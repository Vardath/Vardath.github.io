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
