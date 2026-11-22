"""Fail-closed admission checks for external Scratch Chat JSONL dialogue.

No network downloads or implicit license approval. This gate must run before
external data is mixed with the original CC0 seed.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROLES = {"system", "user", "assistant", "tool"}
LICENSES = {"CC0-1.0", "CC-BY-4.0", "Apache-2.0"}

def canonical(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

def audit(manifest_path, train_path, validation_path, test_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    required = ("source_id", "source_url", "revision", "license", "license_url",
                "approval", "approved_by", "retrieved_utc", "sha256")
    if any(not manifest.get(k) for k in required):
        raise ValueError("Incomplete source provenance/approval manifest")
    if manifest["approval"] != "approved" or manifest["license"] not in LICENSES:
        raise ValueError("Source is not explicitly approved under an admitted license")
    results = {}
    seen_ids, seen_dialogues = set(), set()
    split_signatures = []
    token_index = defaultdict(set)
    for split, path in (("train", train_path), ("validation", validation_path), ("test", test_path)):
        raw = Path(path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != manifest["sha256"].get(split):
            raise ValueError(f"{split}: SHA-256 mismatch")
        count = 0
        for line in raw.decode("utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("source_id") != manifest["source_id"] or record.get("license") != manifest["license"]:
                raise ValueError(f"{split}: source/license mismatch")
            identifier = record.get("id")
            if not isinstance(identifier, str) or not identifier or identifier in seen_ids:
                raise ValueError(f"{split}: duplicate/missing conversation id")
            seen_ids.add(identifier)
            messages = record.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                raise ValueError(f"{split}: incomplete conversation")
            for msg in messages:
                if not isinstance(msg, dict) or msg.get("role") not in ROLES or not isinstance(msg.get("content"), str) or not msg["content"].strip():
                    raise ValueError(f"{split}: invalid message")
            if not any(m["role"] == "user" for m in messages) or not any(m["role"] == "assistant" for m in messages):
                raise ValueError(f"{split}: missing user/assistant turns")
            normalized = json.dumps([(m["role"], canonical(m["content"])) for m in messages], ensure_ascii=False)
            if normalized in seen_dialogues:
                raise ValueError(f"{split}: cross-split or within-split duplicate dialogue")
            seen_dialogues.add(normalized)
            # Exact indexed candidate retrieval: any positive multiset Jaccard
            # pair shares at least one token. Avoid comparing unrelated records.
            tokens = Counter(re.findall(r"\\w+", canonical(" ".join(m["content"] for m in messages))))
            token_count = sum(tokens.values())
            candidates = set()
            for token in tokens:
                candidates.update(token_index[token])
            for prior_index in sorted(candidates):
                prior_split, prior_tokens, prior_count = split_signatures[prior_index]
                if prior_split == split or min(token_count, prior_count) < 12:
                    continue
                overlap = sum((tokens & prior_tokens).values())
                union = token_count + prior_count - overlap
                if union and overlap / union >= 0.85:
                    raise ValueError(f"{split}: near-duplicate dialogue across {prior_split} split")
            index = len(split_signatures)
            split_signatures.append((split, tokens, token_count))
            for token in tokens:
                token_index[token].add(index)
            count += 1
        if not count:
            raise ValueError(f"{split}: empty split")
        results[split] = {"count": count, "sha256": digest}
    return {"approved_source": manifest["source_id"], "license": manifest["license"], "splits": results, "status": "exact-duplicate-and-provenance-check-passed", "limitations": "Lexical similarity is not semantic deduplication; PII, consent and source-license audits still require independent review"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--train", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--test", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.manifest, args.train, args.validation, args.test), indent=2))

if __name__ == "__main__":
    main()
