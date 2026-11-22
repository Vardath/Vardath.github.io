"""Held-out, deterministic behavioural evaluation for Scratch Chat.

This is a scorer, not a claim that the model passes. Never evaluate on training
prompts. Predictions are produced separately by the actual model/JSONL bridge.
Each JSONL case contains id, messages, expected and optional checks.
"""
import argparse
import json
import re
from pathlib import Path

def normalize(value):
    return " ".join(value.casefold().split())

def score_case(case, prediction):
    if not isinstance(prediction, str):
        return {"passed": False, "reason": "non-string response"}
    checks = case.get("checks", {})
    if not isinstance(checks, dict):
        raise ValueError("checks must be an object")
    expected = case.get("expected")
    results = {}
    if expected is not None:
        if not isinstance(expected, str):
            raise ValueError("expected must be a string")
        results["exact"] = normalize(prediction) == normalize(expected)
    for key in ("contains", "excludes"):
        values = checks.get(key, [])
        if not isinstance(values, list) or any(not isinstance(x, str) or not x for x in values):
            raise ValueError(f"{key} must be a list of nonempty strings")
        for i, value in enumerate(values):
            found = normalize(value) in normalize(prediction)
            results[f"{key}:{i}"] = found if key == "contains" else not found
    if checks.get("json_object"):
        try:
            parsed = json.loads(prediction)
            results["json_object"] = isinstance(parsed, dict)
        except (ValueError, TypeError):
            results["json_object"] = False
    if not results:
        raise ValueError("Case needs expected or checks")
    return {"passed": all(results.values()), "checks": results}

def evaluate(cases_path, predictions_path):
    def read(path):
        records = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            identifier = obj.get("id")
            if not isinstance(identifier, str) or not identifier or identifier in records:
                raise ValueError(f"missing or duplicate id in {path}")
            records[identifier] = obj
        return records
    cases, predictions = read(cases_path), read(predictions_path)
    if not cases or set(cases) != set(predictions):
        raise ValueError("Cases and predictions must have identical nonempty id sets")
    details = {}
    for identifier, case in cases.items():
        messages = case.get("messages")
        if not isinstance(messages, list) or len(messages) < 1 or messages[-1].get("role") != "user":
            raise ValueError(f"{identifier}: evaluation prompt must end in user turn")
        if not all(isinstance(m, dict) and m.get("role") in ("system", "user", "assistant", "tool")
                   and isinstance(m.get("content"), str) for m in messages):
            raise ValueError(f"{identifier}: invalid messages")
        details[identifier] = score_case(case, predictions[identifier].get("response"))
    passed = sum(int(x["passed"]) for x in details.values())
    return {"passed": passed, "total": len(details), "pass_rate": passed / len(details),
            "results": details, "limitations": "Deterministic lexical checks only; no semantic or human quality judgment. Predictions must come from a real model run."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    report = evaluate(args.cases, args.predictions)
    output = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    raise SystemExit(0 if report["passed"] == report["total"] else 1)

if __name__ == "__main__":
    main()
