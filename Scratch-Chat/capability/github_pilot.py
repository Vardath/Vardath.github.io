"""Prepare a reproducible GitHub-hosted public-domain text pilot.

This is an infrastructure exercise, not a general-language capability dataset.
Never mix validation/test text into tokenizer training.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
MIN_BYTES = 100_000

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=Path("data/github-pilot"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    req = Request(URL, headers={"User-Agent": "Vardath-Scratch-Chat-Research/1.0"})
    with urlopen(req, timeout=90) as response:
        raw = response.read(4_000_001)
    if not MIN_BYTES <= len(raw) <= 4_000_000:
        raise ValueError("Unexpected source size; abort rather than train on partial input")
    text = raw.decode("utf-8")
    # Separate by contiguous character ranges; document the unavoidable
    # adjacent-boundary dependence in this single-source pilot.
    n = len(text)
    splits = {"train": text[:int(n*.90)],
              "validation": text[int(n*.90):int(n*.95)],
              "test": text[int(n*.95):]}
    for name, chunk in splits.items():
        with (args.out / (name+".jsonl")).open("w", encoding="utf-8") as f:
            f.write(json.dumps({"text":chunk}, ensure_ascii=False)+"\n")
    meta = {"url":URL, "sha256":hashlib.sha256(raw).hexdigest(),
            "source_bytes":len(raw), "split_chars":{k:len(v) for k,v in splits.items()},
            "warning":"Tiny Shakespeare is public-domain literary text; not a general assistant corpus. Contiguous splits may share contextual structure."}
    (args.out/"source.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    from capability.bpe import ByteBPE
    tokenizer = ByteBPE.train([splits["train"]],merges=256,max_chars=200_000)
    tokenizer.save(args.out/"tokenizer.json")
    print(json.dumps(meta,indent=2))

if __name__ == "__main__":
    main()
