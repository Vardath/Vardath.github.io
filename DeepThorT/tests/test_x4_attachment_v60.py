import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

from deepthort_local.x4_attachment import contact_checker, make_draft, placements, protected
from deepthort_local.x4_geometry import GeometryError, mesh_positions
from tests.test_x4_geometry_v59 import make_mesh


class AttachmentTests(unittest.TestCase):
    def test_box_overlap_requires_an_actual_triangle_crossing(self):
        check=contact_checker([[(0,0,0),(4,0,0),(0,4,0)]],
                              [[(3,3,-1),(3,3,1),(4,3,1)]],1)
        self.assertIsNone(check((0,0,0)))
        self.assertEqual(check((-2,-2,0)),[0,0])

    def test_reject_missing_protected_connections(self):
        with self.assertRaisesRegex(GeometryError,'Missing protected'):
            protected(ET.fromstring('<component><connections/></component>'))

    def test_exhaust_ray_rejects_a_rock_behind_the_engine(self):
        hull={'min':[-10,-10,-30],'max':[10,10,30],'dimensions':[20,20,60]}
        rock={'min':[-2,-8,-4],'max':[2,8,4]}
        options=placements(hull,[0,0,0],rock,[('cockpit','cockpit',[0,0,29])])
        self.assertTrue(options)
        self.assertFalse(placements(hull,[0,0,0],rock,[('engine','engine',[0,10,0])]))

    def test_independent_bundle_preserves_base_and_binds_scaled_collision_and_lods(self):
        from deepthort_local.x4_sources import PE_MACRO
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ship_path='assets/units/size_m/test_ship.xml'
            ship_dir=ship_path[:-4]+'_data'
            rock_path='assets/rocks/test.xml'
            rock_dir=rock_path[:-4]+'_data'
            part='<parts><part name="part_main"><lods><lod index="0"/><lod index="1"/></lods><size><max x="4" y="4" z="4"/></size></part></parts>'
            con='<connection name="base_main">'+part+'</connection>'
            anchors=''.join(f'<connection name="con_{tag}_01"><offset><position x="100"/></offset></connection>'
                            for tag in ('cockpit','dock','engine','weapon','turret','elevator'))
            def doc(name,folder,cs):
                return f'<components><component name="{name}"><source geometry="{folder}"/><connections>{cs}</connections></component></components>'.encode()
            files={ship_path:doc('test_ship',ship_dir,con+anchors),rock_path:doc('test',rock_dir,con),
                   'assets/units/size_m/macros/'+PE_MACRO+'.xml':f'<macros><macro name="{PE_MACRO}"><component ref="test_ship"/></macro></macros>'.encode(),
                   'index/macros.xml':b'<index/>','index/components.xml':b'<index/>'}
            raw=make_mesh((20,20,60))
            files[ship_dir+'/part_main-lod0.xmf']=raw
            for suffix in ('lod0','lod1','collision'):files[rock_dir+'/part_main-'+suffix+'.xmf']=make_mesh((8,8,8))
            table={p:(None,0,len(b),None) for p,b in files.items()}
            ship=dict(mesh_positions(raw)[0],mesh=ship_dir+'/part_main-lod0.xmf')
            args=(root,ship_path,dict(component=rock_path,mesh=rock_dir+'/part_main-lod0.xmf',scale=.8),ship,'example','example_macro')
            with patch('deepthort_local.x4_attachment.contact_checker',return_value=lambda offset:[0,0]),patch('deepthort_local.x4_attachment._catalog_key',return_value=()),patch('deepthort_local.x4_attachment._entries',return_value=table),patch('deepthort_local.x4_attachment._read',side_effect=lambda _,p:files[p]):
                options=make_draft(*args)
                bundle=make_draft(*args,chosen=options[0])
                with zipfile.ZipFile(io.BytesIO(bundle)) as z:
                    component=ET.fromstring(z.read('example/assets/units/size_m/example.xml')).find('component')
                    self.assertEqual(component.get('name'),'example')
                    self.assertEqual(len(protected(component)),6)
                    metadata=json.loads(z.read('Attachment_measurements.json'))
                    self.assertEqual(len(metadata['fitted_meshes']),3)
                    self.assertEqual(z.read('example/assets/units/size_m/example_data/part_main-lod0.xmf'),raw)
                files['index/components.xml']=b'<index><entry name="example"/></index>'
                with self.assertRaisesRegex(GeometryError,'identity'):make_draft(*args,chosen=options[0])
