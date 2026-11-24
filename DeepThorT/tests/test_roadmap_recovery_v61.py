import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.specification_library import SpecificationIndex
from deepthort_local.x4_variant import VariantSource
from deepthort_local.agent_plan import VanillaSourceCollision, PlanError


class RoadmapRecoveryTests(unittest.TestCase):
    def test_durable_collision_recovery_and_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            project=root/'project'
            project.mkdir()
            db=root/'index.sqlite3'
            request='X4 mod: independent ship from Xenon PE ship_xen_m_corvette_02_a_macro.\nExtension ID: test_pe'
            source='assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml'
            evidence=f'ship_candidates: {source} IDs ship_xen_m_corvette_02_a_macro SHA abcdef123456'
            index=SpecificationIndex(db)
            index.index(1,request)
            index.save_response(1,request,0,json.dumps({'files':[{'path':'content.xml','description':'Extension metadata'}]}),project=project)
            with self.assertRaises(VanillaSourceCollision):
                index.merge_model_revision(1,request,0,json.dumps({'files':[{'path':source,'description':'Independent ship'}]}),project=project,inspected_evidence=evidence)
            variant=VariantSource.inspected(request,evidence,source)
            self.assertIsNotNone(variant)
            index.remember_roadmap_collision(1,request,0,variant)
            index.reserve_revision_attempt(1,request,0,'first correction')
            index=SpecificationIndex(db)
            self.assertEqual(index.revision_cursor(1,request),1)
            self.assertIsNone(index.pending_roadmap_variant(1,request,evidence.replace('abcdef123456','123456abcdef')))
            ordinal, recovered=index.pending_roadmap_variant(1,request,evidence)
            self.assertEqual(ordinal,0)
            self.assertEqual(recovered,variant)
            self.assertTrue(index.reserve_variant_recovery(1))
            self.assertTrue(index.merge_model_revision(1,request,0,'test_pe_ship_macro',project=project,inspected_evidence=evidence,variant=recovered))
            self.assertIsNone(index.pending_roadmap_variant(1,request,evidence))
            steps=index.merged_steps(1,request)
            self.assertIn('index/macros.xml',[s['path'] for s in steps])
            self.assertIn('assets/units/size_m/macros/test_pe_ship_macro.xml',[s['path'] for s in steps])
            with index._db() as conn:
                self.assertEqual(conn.execute('SELECT macro_name FROM variant_bindings').fetchone()[0],'test_pe_ship_macro')
            self.assertFalse(any(project.iterdir()))

    def test_bounded_recovery_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'index.sqlite3'
            request='X4 mod independent ship ship_xen_m_corvette_02_a_macro\nExtension ID: test_pe'
            source='assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml'
            evidence=f'ship_candidates: {source} IDs ship_xen_m_corvette_02_a_macro SHA abcdef123456'
            index=SpecificationIndex(path)
            index.index(1,request)
            variant=VariantSource.inspected(request,evidence,source)
            index.remember_roadmap_collision(1,request,0,variant)
            self.assertTrue(index.reserve_variant_recovery(1))
            index=SpecificationIndex(path)
            self.assertTrue(index.reserve_variant_recovery(1))
            index.remember_roadmap_collision(1,request,0,variant)
            self.assertFalse(index.reserve_variant_recovery(1))
            self.assertIsNone(index.pending_roadmap_variant(1,request,evidence))


if __name__=='__main__':
    unittest.main()
