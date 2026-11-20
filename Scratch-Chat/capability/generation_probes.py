"""Reproducible generation probes for Scratch Chat; qualitative diagnostics, not a capability score.

The literary pilot has never been trained on instruction following. Record the
actual completions rather than inferring chat competence from next-token loss.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from capability.deepthort_bridge import load_model, respond

PROBES = (
    ("greeting", [{"role": "user", "content": "Hello. What is your name?"}]),
    ("basic_fact", [{"role": "user", "content": "What is two plus two?"}]),
    ("instruction", [{"role": "user", "content": "Reply with exactly the word blue."}]),
    ("short_explanation", [{"role": "user", "content": "Explain why rain falls in one sentence."}]),
    ("multi_turn_memory", [
        {"role": "user", "content": "My favorite color is violet."},
        {"role": "assistant", "content": "I understand."},
        {"role": "user", "content": "What color did I say was my favorite?"},
    ]),
    ("refusal", [{"role": "user", "content": "Can you tell me what you cannot do?"}]),
)


def probe(model, tokenizer, *, max_new_tokens=48):
    return {
        "assessment_type": "unscored_generation_diagnostic",
        "ready_for_conversation": False,
        "warning": "Outputs are inspection samples, not an independently validated conversational benchmark.",
        "probes": [
            {"id": name, "messages": messages,
             "response": respond(model, tokenizer, messages, max_new_tokens=max_new_tokens)}
            for name, messages in PROBES
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model, tokenizer, state = load_model(args.checkpoint, args.tokenizer)
    result = probe(model, tokenizer)
    result["checkpoint_step"] = state["step"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"checkpoint_step": state["step"], "probe_count": len(result["probes"])}))


if __name__ == "__main__":
    main()
