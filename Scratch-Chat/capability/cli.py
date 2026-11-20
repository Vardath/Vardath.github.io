"""Run with python -m capability.cli prepare|tokenizer|baseline."""
import argparse
import json
from pathlib import Path
from .corpus import prepare
from .bpe import ByteBPE


def _lines(path):
    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)['text']


def main():
    p = argparse.ArgumentParser(description='From-scratch capability foundation')
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('prepare', help='Prepare licensed corpus with held-out splits')
    c.add_argument('--manifest', type=Path, required=True)
    c.add_argument('--out', type=Path, required=True)
    c.add_argument('--seed', type=int, default=2026)
    t = sub.add_parser('tokenizer', help='Train original byte-BPE tokenizer on train only')
    t.add_argument('--corpus', type=Path, required=True)
    t.add_argument('--out', type=Path, required=True)
    t.add_argument('--merges', type=int, default=384)
    t.add_argument('--max-chars', type=int, default=1_000_000)
    s = sub.add_parser('stats', help='Evaluate held-out tokenizer compression')
    s.add_argument('--corpus', type=Path, required=True)
    s.add_argument('--tokenizer', type=Path, required=True)
    args = p.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(args.manifest, args.out, seed=args.seed), indent=2))
    elif args.command == 'tokenizer':
        tokenizer = ByteBPE.train(_lines(args.corpus / 'train.jsonl'),
                                  merges=args.merges, max_chars=args.max_chars)
        tokenizer.save(args.out)
        print(json.dumps({'tokenizer':str(args.out), 'vocab_size':tokenizer.vocab_size,
                          'learned_merges':len(tokenizer.merges)}, indent=2))
    else:
        t = ByteBPE.load(args.tokenizer)
        report = {}
        for split in ('train','validation','test'):
            sample = list(_lines(args.corpus / f'{split}.jsonl'))
            chars = sum(len(s) for s in sample)
            bytes_count = sum(len(s.encode('utf-8')) for s in sample)
            token_count = sum(len(t.encode(s)) for s in sample)
            if any(t.decode(t.encode(s)) != s for s in sample):
                raise AssertionError(f'{split} has tokenizer roundtrip failure')
            report[split] = {'records': len(sample), 'chars': chars,
                             'utf8_bytes': bytes_count, 'tokens': token_count,
                             'bytes_per_token': round(bytes_count/token_count, 3) if token_count else None}
        out = args.corpus / 'tokenizer_report.json'
        out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
