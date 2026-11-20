"""Direct generation probes: never confuse decreasing loss with usable chat.

Prompt list must be unseen during training. A useful assistant requires human review
and substantially broader evaluations, not merely these mechanical flags.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import time

from capability.modern_chat import load_chat, generate

DEFAULT_PROMPTS = [
    {'category':'greeting', 'prompt':'Hi there, can we talk about something new?'},
    {'category':'factual', 'prompt':'Explain what causes a rainbow.'},
    {'category':'reasoning', 'prompt':'If I have four apples and give away two, how many remain?'},
    {'category':'instructions', 'prompt':'Write exactly three short sentences about forests.'},
    {'category':'explanation', 'prompt':'What is the difference between a planet and a star?'},
    {'category':'uncertainty', 'prompt':'Tell me a fact that you are unsure about.'},
]


def flags(answer: str) -> list[str]:
    issues=[]
    stripped=answer.strip()
    if not stripped:
        issues.append('blank_or_whitespace_only')
        return issues
    if len(stripped)<4:
        issues.append('extremely_short')
    if len(stripped)>20 and len(set(stripped)) <= 3:
        issues.append('low_character_diversity')
    if re.search(r'(.{1,7})\1{4,}', stripped):
        issues.append('repeated_sequence')
    if '\ufffd' in stripped:
        issues.append('utf8_replacement_characters')
    return issues


def probe(model, tok, questions=None, *, max_tokens=56, temperature=0):
    questions=questions if questions is not None else DEFAULT_PROMPTS
    output=[]
    for item in questions:
        prompt=item['prompt']
        start=time.monotonic()
        try:
            answer=generate(model,tok,[{'role':'user','content':prompt}],
                            max_new_tokens=max_tokens,temperature=temperature)
            output.append({'category': item.get('category','other'),'prompt':prompt,
                           'answer':answer, 'flags':flags(answer),
                           'elapsed_seconds':round(time.monotonic()-start,3)})
        except ValueError as exc:
            output.append({'category': item.get('category','other'), 'prompt':prompt,
                           'error':str(exc), 'flags':['generation_error']})
    return {'purpose':'direct standalone conversation probes; not an intelligence score',
            'questions':len(output), 'flagged_answers':sum(bool(x['flags']) for x in output),
            'human_review_required':True, 'results':output}


def main(argv=None):
    p=argparse.ArgumentParser(description='Check actual Vardath Scratch Chat replies')
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--tokenizer',type=Path,required=True)
    p.add_argument('--questions',type=Path)
    p.add_argument('--output',type=Path,default=Path('reports/chat_quality_v07.json'))
    p.add_argument('--max-tokens',type=int,default=56)
    a=p.parse_args(argv)
    qs=json.loads(a.questions.read_text(encoding='utf8')) if a.questions else None
    model,tok=load_chat(a.checkpoint,a.tokenizer)
    result=probe(model,tok,qs,max_tokens=a.max_tokens)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
