"""JANUS advice is delivered between model passes, not inside an in-flight reply."""
import json
import unittest
from deepthort_local.specification_library import generate_indexed_plan
from deepthort_local.indexed_roadmap_repair import _prompt

class FakeIndex:
    def __init__(self):self.saved=False;self.prompts=[]
    def index(self,*args):pass
    def next_section(self,*args):
        return None if self.saved else {'ordinal':0,'total':1,'attempts':0}
    def model_prompt(self,*args):return 'Review this exact section and propose main.py'
    def save_response(self,*args,**kwargs):self.saved=True
    def status(self,*args):return {'pending':0,'sections':1,'reviewed':1}
    def merged_steps(self,*args):return [{'path':'main.py','description':'Python entrypoint with a hello function'}]

class FakeClient:
    def __init__(self):self.prompts=[]
    def chat(self,session,prompt,max_tokens):self.prompts.append(prompt);return '{"files":[]}'

class CheckpointTests(unittest.TestCase):
    def test_instruction_available_at_next_indexed_section_not_in_source(self):
        index=FakeIndex();client=FakeClient();calls=[]
        def next_advice():
            calls.append(1)
            return 'JANUS TRANSLATION: verify the existing tests before writing more files'
        out,steps=generate_indexed_plan(client,index,1,'plan-1-chat','Build a Python entrypoint',
            '/tmp/demo',max_rounds=2,continuous=True,guidance_getter=next_advice)
        self.assertEqual(len(client.prompts),1)
        self.assertIn('JANUS TRANSLATION',client.prompts[0])
        self.assertEqual(len(steps),1)
        self.assertEqual(len(calls),1)
        self.assertIn('files',out)

    def test_repair_prompt_keeps_exact_original_section(self):
        original='Create a complete PE extension with a correct docking macro.'
        text=_prompt([(0,0,len(original))],original,0,'Docking reference',
            ['Missing macro'],[],new_instruction='Check the existing PE connections before inventing IDs')
        self.assertIn(original,text)
        self.assertIn('JANUS PLANNING CHECKPOINT',text)
        self.assertIn('existing PE connections',text)

if __name__=='__main__':unittest.main()
