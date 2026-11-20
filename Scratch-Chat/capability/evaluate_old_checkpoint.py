"""Record, but do not exaggerate, the v0.1 model's capability on new prompts.

Keyword presence is a crude diagnostic, *not* verified factual correctness.
These prompts were written after the 51-example starter model was trained.
"""
from __future__ import annotations
import json
from pathlib import Path
import torch
from vardath_chat.engine import LocalChatEngine

ROOT = Path(__file__).resolve().parent.parent

def main():
    torch.set_num_threads(2)
    engine = LocalChatEngine(ROOT / 'checkpoints' / 'starter.pt')
    items = []
    for line in (ROOT / 'evaluation' / 'unseen_questions.jsonl').read_text(encoding='utf-8').splitlines():
        obj = json.loads(line)
        answer = engine.reply([{'role':'user','content':obj['prompt']}], max_tokens=72, temperature=0)
        found = any(s.casefold() in answer.casefold() for s in obj['expected_terms'])
        items.append({**obj, 'model_response': answer, 'keyword_found': found})
    out = {'evaluation':'Unseen-prompt smoke test only; keywords do NOT prove correctness',
           'checkpoint':'starter.pt: trained on all 51 previous starter conversations',
           'n_prompts': len(items), 'keyword_found_count':sum(r['keyword_found'] for r in items),
           'results': items}
    target = ROOT / 'reports' / 'v01_unseen_baseline.json'
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'n_prompts':out['n_prompts'], 'keyword_found_count':out['keyword_found_count'],
                      'report':str(target)},indent=2))

if __name__ == '__main__':
    main()
