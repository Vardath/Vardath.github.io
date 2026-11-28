import json
import unittest
from deepthort_local.creative_core import parse_score, generate_score_reply
from deepthort_local.memory_governor import specialist_prompt
from deepthort_local.win_cpu_cap import MAX_CPU_PERCENT,MAX_RAM_PERCENT,calculate_ram_limit

SCORE={'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]}
RAW=json.dumps(SCORE)

class NativeRepairTests(unittest.TestCase):
    def test_complete_wrappers_only(self):
        fence=chr(96)*3
        for value in (RAW,fence+'json\n'+RAW+'\n'+fence,
                      '<|channel>thought\nDrafting.<channel|>'+RAW+'<turn|>',
                      '<think>Drafting.</think>'+RAW):
            self.assertEqual(parse_score(value),SCORE)
        for value in ('<|channel>thought\n'+RAW,'<think>'+RAW,
                      'text '+RAW,RAW+' trailing text',RAW+RAW,
                      fence+'json\n'+RAW, '{"bpm":100,"bpm":100,"notes":[]}'):
            with self.assertRaises(ValueError):parse_score(value)

    def test_retry_only_once_and_preserves_original(self):
        prompts=[];answers=iter(['not JSON',RAW])
        def generate(prompt):
            prompts.append(prompt)
            return next(answers)
        original='Compose an ascending short score at 100 BPM.'
        self.assertEqual(parse_score(generate_score_reply(generate,original)),SCORE)
        self.assertEqual(len(prompts),2)
        self.assertEqual(prompts[0],original)
        self.assertTrue(prompts[1].startswith(original+'\n'))
        prompts.clear()
        def invalid(prompt):
            prompts.append(prompt)
            return 'invalid'
        with self.assertRaises(ValueError):generate_score_reply(invalid,original)
        self.assertEqual(len(prompts),2)

    def test_already_valid_does_not_retry(self):
        prompts=[]
        def generate(prompt):
            prompts.append(prompt)
            return RAW
        self.assertEqual(generate_score_reply(generate,'Brief'),RAW)
        self.assertEqual(prompts,['Brief'])

    def test_memory_prompt_does_not_change_candidate_identity(self):
        rows=[{'id':'N42','kind':'historical_verification','focus':'Export','observation':'Icon red','evidence':'f'*64}]
        prompt=specialist_prompt('Fix export.','Repair export truncation','implementation','',rows)
        self.assertIn('Default to keep=[]',prompt)
        self.assertIn('NOT exercised',prompt)
        expected=[{k:v for k,v in row.items() if k!='evidence'} for row in rows]
        self.assertEqual(json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1]),expected)
        self.assertNotIn('f'*64,prompt)

    def test_caps_and_reserve(self):
        g=1024**3
        self.assertEqual((MAX_CPU_PERCENT,MAX_RAM_PERCENT),(85,80))
        self.assertEqual(calculate_ram_limit(40*g,40*g),26*g)
        self.assertEqual(calculate_ram_limit(40*g,20*g),16*g)
        self.assertEqual(calculate_ram_limit(40*g,40*g,80),32*g)
        self.assertEqual(calculate_ram_limit(40*g,20*g,65,15),14*g)
        with self.assertRaises(ValueError):calculate_ram_limit(40*g,40*g,81)

if __name__=='__main__':
    unittest.main()
