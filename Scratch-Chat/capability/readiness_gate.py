"""Fail-closed capability gate for Scratch Chat training reports.

Loss reduction on literary text is not evidence of conversational ability.
"""
import argparse
import json
import math
from pathlib import Path


def assess(report: dict, *, corpus_kind: str = "literary-pilot", probe_scores: dict | None = None) -> dict:
    if not isinstance(report, dict) or "results" not in report:
        raise ValueError("Missing held-out evaluation")
    results = report["results"]
    for split in ("validation", "test"):
        metrics = results.get(split)
        if not isinstance(metrics, dict) or not isinstance(metrics.get("loss"), (int, float)):
            raise ValueError("Missing held-out " + split + " loss")
        if not math.isfinite(metrics["loss"]) or metrics["loss"] < 0:
            raise ValueError("Invalid held-out loss")
        if metrics.get("tokens_evaluated", 0) < 1000:
            raise ValueError("Insufficient held-out tokens")
    if probe_scores is not None:
        if not isinstance(probe_scores, dict):
            raise ValueError("Malformed probe scores")
        checks = probe_scores.get("checks")
        if not isinstance(checks, dict) or not checks or any(type(v) is not bool for v in checks.values()):
            raise ValueError("Missing or invalid boolean probe checks")
        if probe_scores.get("total") != len(checks) or probe_scores.get("passed") != sum(checks.values()):
            raise ValueError("Inconsistent probe totals")
        if probe_scores.get("checkpoint_step") != report.get("checkpoint_step"):
            raise ValueError("Probe scores do not match evaluated checkpoint")
    return {
        "ready_for_conversation": False,
        "training_completed": True,
        "checkpoint_step": report.get("checkpoint_step"),
        "parameters": report.get("parameters"),
        "held_out_validation_loss": results["validation"]["loss"],
        "held_out_test_loss": results["test"]["loss"],
        "development_probes": probe_scores,
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
    p.add_argument("--probe-scores", type=Path)
    a = p.parse_args()
    scores = json.loads(a.probe_scores.read_text(encoding="utf-8")) if a.probe_scores else None
    verdict = assess(json.loads(a.evaluation.read_text(encoding="utf-8")), probe_scores=scores)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()
