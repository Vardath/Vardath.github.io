import unittest
from deepthort_local.application_workflow_probe import exercise
from deepthort_local.video_planning import outline,scene_script
class ApplicationWorkflowTests(unittest.TestCase):
    def test_real_planning_and_acquisition_boundaries(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
    def test_reject_incomplete_scene(self):
        with self.assertRaises(ValueError):scene_script({'narration':'Missing visual'})
    def test_reject_unbounded_outline(self):
        with self.assertRaises(ValueError):outline({'title':'x','audience':'x','language':'x','style':'x','aspect':'16:9','target_seconds':301,'scenes':[{'title':'x','intent':'x'}]})


    def test_android_emulator_exact_runtime_and_fixed_arguments(self):
        import tempfile
        from pathlib import Path
        from deepthort_local.android_emulator import resolve_runtime,command,checked
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp).resolve();root=base/'project';root.mkdir()
            sdk=base/'sdk';exe=sdk/'emulator'/'emulator.exe';exe.parent.mkdir(parents=True);exe.write_bytes(b'fixture')
            avd=base/'avd';cfg=avd/'Test.avd'/'config.ini';cfg.parent.mkdir(parents=True);cfg.write_text('hw.ramSize=2048\n')
            ini=avd/'Test.ini';ini.write_text('path='+str(cfg.parent)+'\n')
            s={'avd':'Test','seconds':30};env={'ANDROID_HOME':str(sdk),'ANDROID_AVD_HOME':str(avd)}
            guards=resolve_runtime(root,s,env)
            self.assertEqual(len(guards),3);argv=command(s,guards)
            self.assertEqual(argv[:3],[str(exe),'-avd','Test'])
            self.assertIn('-read-only',argv);self.assertIn('-no-window',argv);self.assertNotIn('-wipe-data',argv)
            cfg.write_text('hw.ramSize=4096\n')
            self.assertNotEqual(resolve_runtime(root,s,env),guards)
            ini.write_text('path='+str(root)+'\n')
            with self.assertRaises(ValueError):resolve_runtime(root,s,env)
            with self.assertRaises(ValueError):checked({'avd':'../../bad','seconds':30})
    def test_android_emulator_observation_not_boot_proof(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock
        from deepthort_local.android_emulator import monitor,MAX_LOG
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'log';log.write_bytes(b'start')
            alive=Mock(return_value=True);sampler=Mock();sampler.read.return_value=(20,80)
            t=[0.0]
            def sleep(n):t[0]+=n
            r=monitor(alive,log,10,sampler,clock=lambda:t[0],sleep=sleep)
            self.assertEqual(r['status'],'startup_process_observed')
            self.assertFalse(r['android_boot_verified'])
            sampler.read.return_value=(20,5)
            self.assertEqual(monitor(alive,log,10,sampler,clock=lambda:t[0],sleep=sleep)['status'],'resource_reserve_unavailable')
            alive.return_value=False;alive.code.return_value=3
            self.assertEqual(monitor(alive,log,10,sampler,clock=lambda:t[0],sleep=sleep)['process_exit_code'],3)


    def test_grid_game_project_source_and_reachability(self):
        import io,json,zipfile
        from deepthort_local.game_project_generation import generate,checked
        s={'title':'Crystal Maze','width':6,'height':5,'cell_size':32,'start':[0,0],'goal':[5,4],
           'walls':[[2,0],[2,1],[2,2]],'collectibles':[[1,2],[4,3]]}
        data,r=generate(s);self.assertTrue(r['all_objectives_reachable']);self.assertFalse(r['engine_executed'])
        self.assertEqual(data,generate(s)[0])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(set(z.namelist()),{'project.godot','main.tscn','game.gd','README.txt','level.json'})
            self.assertEqual(json.loads(z.read('level.json')),s)
            self.assertIn(b'run/main_scene="res://main.tscn"',z.read('project.godot'))
            self.assertIn(b'path="res://game.gd"',z.read('main.tscn'))
            self.assertIn(b'var next_cell := player + delta',z.read('game.gd'))
            self.assertIn(b'Vector2i(4, 3)',z.read('game.gd'))
        with self.assertRaises(ValueError):checked(dict(s,walls=[[2,i] for i in range(5)]))
        with self.assertRaises(ValueError):checked(dict(s,collectibles=[[0,0]]))
    def test_grid_game_review_and_stale_input(self):
        import tempfile,json
        from pathlib import Path
        from deepthort_local.game_project_generation import review,execute
        s={'title':'Game','width':5,'height':5,'cell_size':24,'start':[0,0],'goal':[4,4],
           'walls':[],'collectibles':[[1,1]]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();path=root/'spec.json';path.write_text(json.dumps(s))
            plan,_=review(root,'spec.json','game.zip')
            path.write_text(json.dumps(dict(s,title='Changed')))
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'game.zip').exists())
            plan,_=review(root,'spec.json','game.zip');r=execute(root,plan)
            self.assertEqual(r['status'],'editable_game_source_generated')
            with self.assertRaises(ValueError):execute(root,plan)


    def test_x4_diff_exact_selector_and_local_replay(self):
        import xml.etree.ElementTree as ET
        from deepthort_local.x4_xml_processing import generate
        raw=b'<macros><macro name="ship_test_macro" class="ship_m"><component ref="test"/><properties><hull max="100"/><storage max="50"/></properties><connections><connection name="weapon" ref="weapon_slot"/></connections></macro></macros>'
        s={'asset':'assets/test.xml','kind':'macro','name':'ship_test_macro','edits':[
            {'path':[{'tag':'properties'},{'tag':'hull'}],'attribute':'max','expected':'100','value':'1000'}]}
        data,r=generate(raw,s);out=ET.fromstring(data)
        self.assertEqual(out.tag,'diff');self.assertEqual(len(out),1)
        self.assertEqual(out[0].get('sel'),"/macros/macro[@name='ship_test_macro']/properties/hull/@max")
        self.assertEqual(out[0].text,'1000');self.assertTrue(r['local_replay_verified']);self.assertFalse(r['gameplay_verified'])
        with self.assertRaises(ValueError):generate(raw.replace(b'max="100"',b'max="200"'),s)
        with self.assertRaises(ValueError):generate(raw.replace(b'<hull max="100"/>',b'<hull max="100"/><hull max="100"/>'),s)
        with self.assertRaises(ValueError):generate(b'<!DOCTYPE macros [<!ENTITY x "bad">]>'+raw,s)
    def test_x4_diff_review_and_stale_source(self):
        import tempfile,json
        from pathlib import Path
        from deepthort_local.x4_xml_processing import review,execute
        s={'asset':'assets/engine.xml','kind':'macro','name':'engine_test_macro','edits':[
            {'path':[{'tag':'properties'},{'tag':'thrust'}],'attribute':'forward','expected':'100','value':'200'}]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'assets').mkdir()
            src=root/'assets'/'engine.xml';raw=b'<macros><macro name="engine_test_macro"><properties><thrust forward="100"/></properties></macro></macros>'
            src.write_bytes(raw);(root/'spec.json').write_text(json.dumps(s))
            plan,_=review(root,'spec.json','patch.xml')
            src.write_bytes(raw+b' ')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'patch.xml').exists())
            src.write_bytes(raw);plan,_=review(root,'spec.json','patch.xml')
            r=execute(root,plan);self.assertEqual(r['status'],'x4_diff_locally_replayed')
            self.assertEqual(src.read_bytes(),raw)
            with self.assertRaises(ValueError):execute(root,plan)


    def test_seeded_connected_level_generation(self):
        import json
        from deepthort_local.level_generation import generate,distances
        from deepthort_local.game_project_generation import checked
        s={'title':'Crystal Grid','width':10,'height':8,'cell_size':24,'seed':17,
           'wall_percent':35,'collectible_count':5,'minimum_goal_distance':16}
        raw,r=generate(s);level=checked(json.loads(raw))
        self.assertEqual(raw,generate(s)[0])
        self.assertNotEqual(raw,generate(dict(s,seed=18))[0])
        self.assertEqual(len(level['walls']),28);self.assertEqual(len(level['collectibles']),5)
        open_cells={(x,y) for x in range(10) for y in range(8)}-set(map(tuple,level['walls']))
        self.assertEqual(len(distances((0,0),open_cells)),len(open_cells))
        self.assertGreaterEqual(r['goal_shortest_path_steps'],16)
        self.assertFalse(r['native_playtest_verified'])
    def test_seeded_level_bounds_and_stale_spec(self):
        import json,tempfile
        from pathlib import Path
        from deepthort_local.level_generation import generate,review,execute
        s={'title':'Level','width':5,'height':5,'cell_size':24,'seed':1,
           'wall_percent':25,'collectible_count':3,'minimum_goal_distance':8}
        with self.assertRaises(ValueError):generate(dict(s,minimum_goal_distance=9))
        with self.assertRaises(ValueError):generate(dict(s,collectible_count=32))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src=root/'spec.json';src.write_text(json.dumps(s))
            plan,_=review(root,'spec.json','level.json')
            src.write_text(json.dumps(dict(s,seed=2)))
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'level.json').exists())
            plan,_=review(root,'spec.json','level.json')
            self.assertEqual(execute(root,plan)['status'],'connected_level_generated')
            with self.assertRaises(ValueError):execute(root,plan)


    def test_procedural_world_connectivity_and_determinism(self):
        import json
        from deepthort_local.world_generation import generate
        from deepthort_local.game_project_generation import checked
        s={'title':'World','columns':3,'rows':2,'seed':17,'region_width':8,'region_height':6,
           'cell_size':24,'wall_percent':25,'collectible_count':3,'extra_links':1}
        raw,receipt=generate(s);world=json.loads(raw)
        self.assertEqual(raw,generate(s)[0])
        self.assertNotEqual(raw,generate(dict(s,seed=18))[0])
        self.assertEqual(len(world['regions']),6)
        self.assertEqual(len(world['links']),6)
        self.assertEqual(len({r['seed'] for r in world['regions']}),6)
        seen={0}
        for _ in world['regions']:
            for a,b in world['links']:
                if a in seen or b in seen:seen.update((a,b))
                self.assertEqual(abs(a%3-b%3)+abs(a//3-b//3),1)
        self.assertEqual(seen,set(range(6)))
        for region in world['regions']:
            level=checked(region['level'])
            self.assertEqual(len(level['walls']),12)
            self.assertEqual(len(level['collectibles']),3)
        self.assertTrue(receipt['all_regions_connected'])
        self.assertFalse(receipt['native_playtest_verified'])

    def test_procedural_world_bounds_and_source_guard(self):
        import json,tempfile
        from pathlib import Path
        from deepthort_local.world_generation import generate,review,execute
        s={'title':'World','columns':2,'rows':2,'seed':1,'region_width':5,'region_height':5,
           'cell_size':24,'wall_percent':20,'collectible_count':2,'extra_links':0}
        with self.assertRaises(ValueError):generate(dict(s,extra_links=2))
        with self.assertRaises(ValueError):generate(dict(s,columns=True))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src=root/'spec.json';src.write_text(json.dumps(s))
            plan,_=review(root,'spec.json','world.json')
            src.write_text(json.dumps(dict(s,seed=2)))
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'world.json').exists())
            plan,_=review(root,'spec.json','world.json')
            self.assertEqual(execute(root,plan)['status'],'connected_world_generated')
            with self.assertRaises(ValueError):execute(root,plan)


    def test_grid_npc_bundle_and_controller(self):
        import io,json,zipfile
        from deepthort_local.npc_behaviour import generate
        level={'title':'NPC','width':5,'height':5,'cell_size':24,'start':[0,0],
               'goal':[4,4],'walls':[[1,1]],'collectibles':[[3,3]]}
        s={'level':level,'patrol':[[0,0],[4,0]],'detection_distance':3,
           'player_trace':[None,[3,0],[3,0],None,None,None]}
        raw,receipt=generate(s)
        self.assertEqual(raw,generate(s)[0])
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            trace=json.loads(z.read('trace.json'))
            ns={};exec(compile(z.read('npc_controller.py'),'npc_controller.py','exec'),ns)
            controller=ns['Controller'](json.loads(z.read('behaviour.json')))
            self.assertEqual(trace,[controller.step(p) for p in s['player_trace']])
        self.assertEqual([row['mode'] for row in trace[:4]],['patrol','pursuit','pursuit','return'])
        self.assertEqual(trace[2]['position'],[2,0])
        self.assertTrue(receipt['movement_verified'])
        self.assertFalse(receipt['native_playtest_verified'])

    def test_grid_npc_review_guards(self):
        import json,tempfile
        from pathlib import Path
        from deepthort_local.npc_behaviour import generate,review,execute
        level={'title':'NPC','width':5,'height':5,'cell_size':24,'start':[0,0],
               'goal':[4,4],'walls':[[1,1]],'collectibles':[[3,3]]}
        s={'level':level,'patrol':[[0,0],[4,0]],'detection_distance':3,'player_trace':[None]}
        with self.assertRaises(ValueError):generate(dict(s,patrol=[[0,0],[1,1]]))
        with self.assertRaises(ValueError):generate(dict(s,player_trace=[[1,1]]))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src=root/'spec.json';src.write_text(json.dumps(s))
            plan,_=review(root,'spec.json','npc.zip')
            src.write_text(json.dumps(dict(s,detection_distance=2)))
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'npc.zip').exists())
            plan,_=review(root,'spec.json','npc.zip')
            self.assertEqual(execute(root,plan)['status'],'npc_behaviour_generated')
            with self.assertRaises(ValueError):execute(root,plan)


    def test_swept_collision_geometry(self):
        from fractions import Fraction
        from deepthort_local.collision_testing import contact
        self.assertEqual(contact([0,0,1,1],[10,0],[5,0,1,4]),Fraction(2,5))
        self.assertEqual(contact([10,0,1,1],[-10,0],[5,0,1,4]),Fraction(2,5))
        self.assertIsNone(contact([0,5,1,1],[10,0],[5,0,1,4]))
        self.assertEqual(contact([0,0,1,1],[4,0],[5,0,1,1]),Fraction(1))
        self.assertEqual(contact([0,0,1,1],[-1,0],[1,0,1,1]),Fraction(0))
        self.assertIsNone(contact([0,0,1,1],[0,0],[2,0,1,1]))
        self.assertEqual(contact([0,0,2,2],[0,0],[1,1,2,2]),Fraction(0))

    def test_swept_collision_expected_results(self):
        import json
        from deepthort_local.collision_testing import generate
        s={'obstacles':[{'id':'a','rect':[5,0,1,1]},{'id':'b','rect':[5,1,1,1]}],
           'cases':[{'id':'fast','rect':[0,0,1,2],'delta':[10,0],'expected_first':['b','a']},
                    {'id':'miss','rect':[0,4,1,1],'delta':[10,0],'expected_first':[]},
                    {'id':'mismatch','rect':[0,0,1,2],'delta':[10,0],'expected_first':['a']}]}
        raw,r=generate(s);rows=json.loads(raw)['cases']
        self.assertEqual(rows[0]['first_contact'],[2,5])
        self.assertEqual(rows[0]['observed_first'],['a','b'])
        self.assertEqual(r['passed'],2);self.assertEqual(r['failed'],1)
        self.assertFalse(r['all_cases_passed'])
        with self.assertRaises(ValueError):generate(dict(s,cases=[dict(s['cases'][0],expected_first=['unknown'])]))

    def test_swept_collision_review_and_cli(self):
        import json,tempfile,subprocess,sys
        from pathlib import Path
        from deepthort_local.collision_testing import review,execute
        s={'obstacles':[{'id':'wall','rect':[5,0,1,1]}],
           'cases':[{'id':'wrong','rect':[0,0,1,1],'delta':[10,0],'expected_first':[]}]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();src=root/'spec.json';src.write_text(json.dumps(s))
            plan,_=review(root,'spec.json','report.json')
            src.write_text(json.dumps(s)+' ')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'report.json').exists())
            plan,_=review(root,'spec.json','report.json')
            p=subprocess.run([sys.executable,'-m','deepthort_local.collision_testing','--root',str(root),'--plan',json.dumps(plan)],capture_output=True,text=True,timeout=30)
            self.assertEqual(p.returncode,1,p.stdout+p.stderr)
            self.assertEqual(json.loads(p.stdout)['failed'],1)
            self.assertTrue((root/'report.json').is_file())
            with self.assertRaises(ValueError):execute(root,plan)


    def test_android_game_archive_and_command(self):
        import io,zipfile
        from deepthort_local.android_game_compilation import archive_files,commands
        preset=b'[preset.0]\nname="Android"\nplatform="Android"\nexport_filter="all_resources"\n[preset.0.options]\ngradle_build/use_gradle_build=false\n'
        def bundle(name='game.gd',cfg=preset):
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:
                z.writestr('project.godot','config_version=5')
                z.writestr('export_presets.cfg',cfg)
                z.writestr(name,'extends Node2D')
            return out.getvalue()
        self.assertIn('game.gd',archive_files(bundle(),'Android'))
        with self.assertRaises(ValueError):archive_files(bundle('../escape.gd'),'Android')
        with self.assertRaises(ValueError):archive_files(bundle(cfg=preset.replace(b'false',b'true')),'Android')
        with self.assertRaises(ValueError):archive_files(bundle(cfg=preset+b'keystore/release_password="secret"\n'),'Android')
        with self.assertRaises(ValueError):archive_files(bundle(),'Other')
        argv=commands('Godot.exe','stage','out.apk','Android')
        self.assertEqual(argv[0],['Godot.exe','--headless','--path','stage','--editor','--import'])
        self.assertEqual(argv[1],['Godot.exe','--headless','--path','stage','--export-debug','Android','out.apk'])

    def test_android_game_apk_structure(self):
        import tempfile,zipfile
        from pathlib import Path
        from deepthort_local.android_game_compilation import inspect_apk
        with tempfile.TemporaryDirectory() as tmp:
            apk=Path(tmp)/'test.apk'
            with zipfile.ZipFile(apk,'w') as z:
                z.writestr('AndroidManifest.xml',b'\x03\x00\x08\x00fixture')
                z.writestr('classes.dex',b'dex\n035\x00fixture')
            r=inspect_apk(apk)
            self.assertTrue(r['apk_structure_verified'])
            self.assertFalse(r['signature_verified'])
            self.assertFalse(r['device_execution_verified'])
            with zipfile.ZipFile(apk,'w') as z:
                z.writestr('AndroidManifest.xml','not binary')
                z.writestr('classes.dex',b'dex\n035\x00fixture')
            with self.assertRaises(ValueError):inspect_apk(apk)


    def test_stopped_container_create_and_inspect(self):
        import tempfile,json
        from pathlib import Path
        from deepthort_local.container_management import perform,project_key,name_for
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);image='sha256:'+'a'*64;ident='b'*64
            s={'operation':'create','name':'test','image':image};calls=[]
            row='|'.join(map(json.dumps,[ident,'/'+name_for(root,s),project_key(root),'created',image]))
            def run(argv):
                calls.append(argv)
                return ['|'.join(map(json.dumps,[image,None])),ident,row][len(calls)-1]
            r=perform(root,s,'docker.exe',run)
            self.assertEqual(r['status'],'stopped_container_created')
            self.assertFalse(r['container_started'])
            self.assertIn('--pull=never',calls[1])
            self.assertIn('--network',calls[1])
            self.assertNotIn('start',calls[1])
            self.assertEqual(calls[0][1:3],['--host','npipe:////./pipe/docker_engine'])
            with self.assertRaises(ValueError):perform(root,s,'docker.exe',lambda argv:'|'.join(map(json.dumps,[image,{'/data':{}}])))

    def test_stopped_container_remove_ownership(self):
        import tempfile,json
        from pathlib import Path
        from deepthort_local.container_management import perform,project_key,name_for
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ident='b'*64;image='sha256:'+'a'*64
            s={'operation':'remove','name':'test','container_id':ident};calls=[]
            def row(label,state):
                return '|'.join(map(json.dumps,[ident,'/'+name_for(root,s),label,state,image]))
            for bad in (row('other','created'),row(project_key(root),'running')):
                calls.clear()
                def reject(argv):
                    calls.append(argv);return bad
                with self.assertRaises(ValueError):perform(root,s,'docker.exe',reject)
                self.assertEqual(len(calls),1)
            calls.clear()
            def run(argv):
                calls.append(argv)
                return row(project_key(root),'exited') if len(calls)==1 else ident
            r=perform(root,s,'docker.exe',run)
            self.assertEqual(r['status'],'stopped_container_removed')
            self.assertEqual(calls[1][-3:],['container','rm',ident])
            with self.assertRaises(ValueError):perform(root,dict(s,container_id='short'),'docker.exe',run)


    def test_integrated_five_model_fixture(self):
        import tempfile,json,hashlib
        from pathlib import Path
        from deepthort_local.five_model_acceptance import exercise,EXPECTED,PLAN,RECALL
        from deepthort_local.triad_profiles import PROFILES,MEMORY_PROFILE
        from deepthort_local.creative_profile import MODEL_NAME,REVISION
        from deepthort_local.creative_core import midi
        health={'pid':10,'ready':True,'offline':True,'backend':'native-openvino-ir-cpu',
                'models':{role:{'name':p[0],'resident':True,'pid':i+11} for i,(role,p) in enumerate(PROFILES.items())},
                'memory_model':{'name':MEMORY_PROFILE[0],'revision':MEMORY_PROFILE[2],'resident':True,'pid':20},
                'serial_memory_mode':True,'memory_retries':0}
        answers=[('memory',RECALL),('janus',PLAN),('implementation',EXPECTED),
                 ('sentinel',{'verdict':'reject','fields':['bpm']}),('sentinel',{'verdict':'accept','fields':[]})]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);calls=[]
            def ask(role,prompt,tokens):
                expected_role,obj=answers[len(calls)];calls.append(role)
                self.assertEqual(role,expected_role);return json.dumps(obj)
            def creative(**kw):
                self.assertTrue(kw['accept'](EXPECTED));raw=midi(EXPECTED)
                (root/'score.mid').write_bytes(raw)
                return root,{'native_inference_verified':True,'assigned_role':'multimedia','model':MODEL_NAME,'revision':REVISION,
                    'pid':30,'sha256':hashlib.sha256(raw).hexdigest(),'scope':'five-model-native',
                    'brief_sha256':hashlib.sha256(kw['brief'].encode()).hexdigest(),'project_publication_authorized':False}
            r=exercise(lambda:health,10,ask,root,creative=creative)
            self.assertEqual(r['status'],'passed',r)
            self.assertEqual(len(r['evidence']['collaboration_stages']),6)
            self.assertEqual(len(calls),5)
            failed=exercise(lambda:health,10,lambda *a:json.dumps({'keep':['N2']}),root,creative=lambda **kw:self.fail('wrong recall must not generate'))
            self.assertEqual(failed['status'],'failed')
            stopped=exercise(lambda:health,10,ask,root,cancelled=lambda:True,creative=creative)
            self.assertEqual(stopped['status'],'cancelled')
            # Scripted receipt tests the host oracle only, not real inference.
            calls.clear()
            def unverified(**kw):
                p,receipt=creative(**kw);receipt['native_inference_verified']=False
                return p,receipt
            r=exercise(lambda:health,10,ask,root,creative=unverified)
            self.assertEqual(r['status'],'failed')
            self.assertEqual(len(calls),4)

    def test_five_model_manifest_registration(self):
        from pathlib import Path
        from deepthort_local.latest_acceptance import load_test
        manifest=load_test(Path(__file__).resolve().parents[1]/'LATEST_TEST.json')
        self.assertEqual(len(manifest['checks']),24)
        self.assertEqual(manifest['checks'][-1],'five_model_acceptance')


    def test_autonomous_self_evaluation_history_and_dedup(self):
        import tempfile,json
        from pathlib import Path
        from deepthort_local.self_evaluation import assess,recommend_once
        from deepthort_local.latest_acceptance import SCHEMA
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);folder=state/'latest-tests';folder.mkdir()
            def report(day,status):
                return {'schema':SCHEMA,'test_id':'fixture','completed_utc':f'2026-11-{day:02d}T00:00:00+00:00',
                    'outcome':'failed' if status=='failed' else 'blocked',
                    'results':[{'check':'five_model_acceptance','status':status,'detail':'ignored'},
                               {'check':'shared_cap','status':'blocked'}]}
            (folder/'LatestTest-20261125-000000-000001.json').write_text(json.dumps(report(25,'passed')))
            (folder/'LatestTest-20261126-000000-000001.json').write_text(json.dumps(report(26,'passed')))
            (folder/'latest.json').write_text(json.dumps(report(27,'failed')))
            r=assess(state)
            self.assertEqual(r['comparable_history'],2)
            self.assertTrue(r['findings'][0]['regression'])
            self.assertEqual(r['findings'][1]['consecutive_observations'],3)
            self.assertFalse(r['execution_authorized'])
            class Store:
                def __init__(self):self.rows={}
                def recommend(self,**kw):
                    key=kw['evidence_key']
                    if key in self.rows:return False
                    self.rows[key]=kw;return True
            store=Store()
            self.assertEqual(recommend_once(state,store),2)
            self.assertEqual(recommend_once(state,store),0)
            self.assertNotIn('ignored',str(store.rows))
            self.assertIn('not classify as a model defect',str(store.rows))

    def test_autonomous_self_evaluation_refuses_inconsistent_evidence(self):
        import tempfile,json
        from pathlib import Path
        from deepthort_local.self_evaluation import assess
        from deepthort_local.latest_acceptance import SCHEMA
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);folder=state/'latest-tests';folder.mkdir()
            data={'schema':SCHEMA,'test_id':'fixture','completed_utc':'2026-11-27T00:00:00+00:00',
                  'outcome':'passed','results':[{'check':'shared_cap','status':'failed'}]}
            (folder/'latest.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):assess(state)
            data['outcome']='failed';data['results'].append(data['results'][0])
            (folder/'latest.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):assess(state)


    def test_procedure_improvement_preserves_checks_and_dependencies(self):
        from deepthort_local.procedure_improvement import propose
        manifest={'id':'fixture','checks':['shared_cap','triad_residency','task_memory','portable_skills','live_memory','memory_core']}
        evaluation={'test_id':'fixture','latest_sha':'a'*64,'findings':[{'check':'memory_core','status':'failed','regression':True,'consecutive_observations':1}]}
        r=propose(manifest,evaluation)
        self.assertEqual(r['candidate_order'],['shared_cap','triad_residency','live_memory','memory_core','task_memory','portable_skills'])
        self.assertEqual(r['historical_checks_before_failure'],5)
        self.assertEqual(r['candidate_checks_before_failure'],3)
        self.assertFalse(r['installation_authorized'])
        self.assertFalse(r['runtime_improvement_verified'])
        self.assertIsNone(propose(dict(manifest,id='different'),evaluation))
        self.assertIsNone(propose(dict(manifest,checks=['shared_cap','task_memory','memory_core']),evaluation))
        self.assertIsNone(propose(manifest,dict(evaluation,findings=[dict(evaluation['findings'][0],status='blocked')])))

    def test_procedure_improvement_staging_is_inert(self):
        import tempfile,json
        from pathlib import Path
        from deepthort_local.procedure_improvement import stage_once
        from deepthort_local.latest_acceptance import SCHEMA
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);state=root/'state';state.mkdir();folder=state/'latest-tests';folder.mkdir()
            manifest={'schema':SCHEMA,'id':'fixture','title':'Fixture','checks':['shared_cap','triad_residency','task_memory','live_memory']}
            src=root/'LATEST_TEST.json';src.write_text(json.dumps(manifest))
            before=src.read_bytes()
            def report(day,status):
                return {'schema':SCHEMA,'test_id':'fixture','completed_utc':f'2026-11-{day:02d}T00:00:00+00:00','outcome':status,
                        'results':[{'check':'live_memory','status':status}]}
            (folder/'LatestTest-20261126-000000-000001.json').write_text(json.dumps(report(26,'passed')))
            (folder/'latest.json').write_text(json.dumps(report(27,'failed')))
            class Store:
                def __init__(self):self.seen=set()
                def recommend(self,**kw):
                    k=kw['evidence_key']
                    if k in self.seen:return False
                    self.seen.add(k);return True
            store=Store()
            self.assertTrue(stage_once(root,state,store))
            self.assertFalse(stage_once(root,state,store))
            staged=list((state/'procedure-improvements').glob('*.json'))
            self.assertEqual(len(staged),1)
            self.assertEqual(src.read_bytes(),before)
            self.assertFalse(json.loads(staged[0].read_text())['execution_authorized'])
