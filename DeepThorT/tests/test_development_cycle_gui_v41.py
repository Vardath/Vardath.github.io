"""Real GUI + subprocess smoke: failed local test -> Qwen repair -> retest."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class LocalFakeModel:
    def __init__(self):self.calls=[]
    def chat(self,thread,prompt,max_tokens=384):
        self.calls.append(prompt)
        if prompt.startswith('SENTINEL: independently guard'):
            return 'ACCEPT\nFixture proposal fits the addition program; test must determine correctness.'
        if 'You are repairing one file' in prompt:
            return json.dumps({'path':'main.py','code':'def add(a, b):\n    return a + b\n'})
        if 'Return ONLY valid JSON' in prompt:
            return json.dumps({'files':[
                {'path':'main.py','description':'An addition function'},
                {'path':'test_main.py','description':'Unit test of correct addition'}]})
        if 'CURRENT FILE: main.py' in prompt:
            return 'def add(a, b):\n    return a - b\n'
        if 'CURRENT FILE: test_main.py' in prompt:
            return ('import unittest\nfrom main import add\n'
                    'class TestAdd(unittest.TestCase):\n'
                    '    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n')
        raise RuntimeError('Unexpected local model prompt:'+prompt[:220])


class FullGuiDevelopmentCycleTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires a real Tk display')
    def test_local_failure_is_repaired_then_tested_in_same_approved_job(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);project=root/'demo';project.mkdir()
            with patch.object(mod,'STATE',root/'state'),\
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
                 patch.object(mod.messagebox,'askyesno',return_value=True),\
                 patch.object(mod.messagebox,'showinfo'),\
                 patch.object(mod.messagebox,'showwarning'),\
                 patch.object(mod.messagebox,'showerror'):
                app=mod.DeepThorTDesktop()
                app.disk_gate.gaming = lambda: False  # This fixture exercises an idle gaming PC.
                try:
                    app._set_project(project)
                    model=LocalFakeModel()
                    app.client.chat=model.chat
                    app.input.insert('1.0','Build a simple Python addition function and unit tests')
                    app._queue_input('plan')
                    req=app.conversations.next_pending()
                    app._execute_conversation(req)
                    self._wait(app,lambda:app.conversations.get(req['id'])['state']=='responded')
                    app._approve_conversation_plan()
                    rows=app.jobs.items(str(project));self.assertEqual(len(rows),1)
                    jobid=rows[0]['id']
                    for _ in range(3):
                        app._execute_job(app.jobs.get(jobid))
                        self._wait(app,lambda:app.jobs.get(jobid)['state'] in (
                            'queued','waiting_verification','needs_input'))
                    self.assertEqual(app.jobs.get(jobid)['state'],'waiting_verification')
                    self.assertIn('return a - b',(project/'main.py').read_text())
                    # Real subprocess verification, not a mocked positive result.
                    app._project_work_once()
                    self._wait(app,lambda:app.jobs.get(jobid)['state'] in (
                        'waiting_repair','needs_input','complete'),timeout=16)
                    self.assertEqual(app.jobs.get(jobid)['state'],'waiting_repair')
                    cycle=app.cycles.get(jobid)
                    self.assertEqual(cycle['tests'],1)
                    self.assertEqual(cycle['phase'],'repair_ready')
                    # The local ONNX server is mocked at only its API seam.
                    # All project writes and real test process are executed.
                    app.node=MagicMock()
                    app.node.poll.return_value=None
                    app.node_ready=True
                    app._project_work_once()
                    self._wait(app,lambda:app.jobs.get(jobid)['state'] in (
                        'waiting_verification','needs_input'),timeout=12)
                    self.assertEqual(app.jobs.get(jobid)['state'],'waiting_verification')
                    self.assertIn('return a + b',(project/'main.py').read_text())
                    app._project_work_once()
                    self._wait(app,lambda:app.jobs.get(jobid)['state'] in (
                        'complete','needs_input','waiting_repair'),timeout=16)
                    self.assertEqual(app.jobs.get(jobid)['state'],'complete')
                    cycle=app.cycles.get(jobid)
                    self.assertEqual((cycle['tests'],cycle['repairs'],cycle['phase']),
                                     (2,1,'verified'))
                    self.assertTrue(list((root/'state'/'backups').rglob('main.py')))
                    self.assertEqual(sum(not p.startswith('SENTINEL: independently guard') for p in model.calls),4)
                    reviews=[p for p in model.calls if p.startswith('SENTINEL: independently guard')]
                    for path in ('main.py','test_main.py'):
                        for kind in ('plan','code'):
                            self.assertTrue(any(f'REVIEW KIND: {kind}; intended step: {path}' in p for p in reviews),(path,kind))
                    self.assertTrue(any('REVIEW KIND: repair;' in p for p in reviews))
                finally:
                    app._quit()

    @staticmethod
    def _wait(app,done,timeout=10):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            app._handle_events();app.update_idletasks()
            if done():return
            time.sleep(.035)
        raise AssertionError('Cycle GUI test timed out; current pending status='+
                             str(getattr(app,'active_job',None)))


if __name__=='__main__':unittest.main()
