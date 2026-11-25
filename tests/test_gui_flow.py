"""Headless smoke test of real GUI queue -> plan -> approved file writes.
Run under xvfb-run on Linux or directly on Windows.
"""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

class FakeLocalModel:
 def __init__(self):self.calls=[]
 def chat(self,thread,prompt,max_tokens=384):
  self.calls.append(prompt)
  if prompt.startswith('SENTINEL: independently guard'):return 'ACCEPT\nFixture proposal fits the requested Python project.'
  if 'Return ONLY valid JSON' in prompt:
   return json.dumps({'files':[{'path':'main.py','description':'A Python hello world script'},
                              {'path':'test_main.py','description':'A regression test for the script'}]})
  if 'CURRENT FILE: main.py' in prompt:return 'print("hello")\n'
  if 'CURRENT FILE: test_main.py' in prompt:return 'import unittest, io, contextlib, runpy\nclass TestMain(unittest.TestCase):\n    def test_hello(self):\n        output = io.StringIO()\n        with contextlib.redirect_stdout(output):\n            runpy.run_path(\"main.py\")\n        self.assertEqual(output.getvalue(), \"hello\\n\")\n'
  return 'Unexpected model prompt'

class RealGuiQueueTests(unittest.TestCase):
 @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk desktop environment')
 def test_staged_build_flow_no_cloud(self):
  import desktop_app as mod
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);proj=d/'demo';proj.mkdir()
   with patch.object(mod,'STATE',d/'state'),patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
        patch.object(mod.messagebox,'askyesno',return_value=True),\
        patch.object(mod.messagebox,'showinfo'),patch.object(mod.messagebox,'showwarning'),\
        patch.object(mod.messagebox,'showerror'):
    app=mod.DeepThorTDesktop()
    app.disk_gate.gaming = lambda: False  # This fixture exercises an idle gaming PC.
    try:
     app._set_project(proj)
     client=FakeLocalModel();app.client.chat=client.chat
     app.input.insert('1.0','Build a simple Python program plus tests')
     app._queue_input('plan')
     self.assertEqual(app.jobs.items(str(proj)),[])
     conversation=app.conversations.next_pending()
     self.assertEqual(conversation['mode'],'draft_plan')
     app._execute_conversation(conversation)
     deadline=time.monotonic()+8
     while time.monotonic()<deadline:
      app._handle_events()
      if app.conversations.get(conversation['id'])['state']=='responded':break
      time.sleep(.03)
     draft=app.conversations.latest_draft(app.current_chat,str(proj))
     self.assertEqual(len(draft['steps']),2)
     self.assertEqual(app.jobs.items(str(proj)),[])
     app._approve_conversation_plan()
     records=app.jobs.items(str(proj));self.assertEqual(len(records),1)
     job=records[0];ident=job['id']
     self.assertTrue((d/'state'/'project-grants'/f'job-{ident}.json').is_file())
     def tick(timeout=8):
      end=time.monotonic()+timeout
      while time.monotonic()<end:
       app._handle_events();app.update_idletasks();
       if app.events.empty():time.sleep(.04)
       else:time.sleep(.03)
       yield app.jobs.get(ident)['state']
     # Plan was approved before entering the execution queue.
     self.assertEqual(len(app.jobs.steps(ident)),2)
     for _ in range(3):
      app._execute_job(app.jobs.get(ident))
      for state in tick():
       if state in ('queued','waiting_verification','needs_input'):break
     self.assertTrue((proj/'main.py').is_file())
     self.assertEqual((proj/'main.py').read_text(),'print("hello")\n')
     self.assertTrue((proj/'test_main.py').is_file())
     self.assertEqual(app.jobs.get(ident)['state'],'waiting_verification')
     app._project_work_once()
     for state in tick():
      if state in ('complete','needs_input'):break
     self.assertEqual(app.jobs.get(ident)['state'],'complete')
     self.assertEqual(sum(not p.startswith('SENTINEL: independently guard') for p in client.calls),3)
     reviews=[p for p in client.calls if p.startswith('SENTINEL: independently guard')]
     for path in ('main.py','test_main.py'):
      for kind in ('plan','behavior_test' if path=='test_main.py' else 'code'):
       self.assertTrue(any(f'REVIEW KIND: {kind}; intended step: {path}' in p for p in reviews), (path,kind))
    finally:app._quit()

if __name__=='__main__':unittest.main()
