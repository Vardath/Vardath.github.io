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
