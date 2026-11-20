"""Fail-closed capability gate for Scratch Chat training reports.

Loss reduction on literary text is not evidence of conversational ability.
"""
import argparse
import json
from pathlib import Path


def assess(report: dict, *, corpus_kind: str = "literary-pilot") -> dict:
    if not isinstance(report, dict) or "results" not in report:
        raise ValueError("Missing held-out evaluation")
    results = report["results"]
    for split in ("validation", "test"):
        metrics = results.get(split)
        if not isinstance(metrics, dict) or not isinstance(metrics.get("loss"), (int, float)):
            raise ValueError("Missing held-out " + split + " loss")
        if metrics.get("tokens_evaluated", 0) < 1000:
            raise ValueError("Insufficient held-out tokens")
    return {
        "ready_for_conversation": False,
        "training_completed": True,
        "checkpoint_step": report.get("checkpoint_step"),
        "parameters": report.get("parameters"),
        "held_out_validation_loss": results["validation"]["loss"],
        "held_out_test_loss": results["test"]["loss"],
        "reason": (
            "Only literary next-token prediction has been measured. "
            "A diverse licensed corpus, independent dialogue evaluation, "
            "multi-turn tests and human assessment are required."
            if corpus_kind == "literary-pilot" else
            "Held-out token loss alone cannot establish conversational readiness."
        ),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evaluation", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    verdict = assess(json.loads(a.evaluation.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
