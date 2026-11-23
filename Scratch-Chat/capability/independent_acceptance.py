"""Independent, checkpoint-agnostic JSONL acceptance runner for Scratch Chat.

Run against an already launched DeepThorT-compatible provider:
  python -m capability.independent_acceptance --command python -m capability.deepthort_bridge --checkpoint FILE --tokenizer FILE

This deliberately does not certify quality from random-model transport success.
Fixtures are maintained separately from training and validation data.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

CASES = [
    {"id": "health", "request": {"method": "health"}, "kind": "health"},
    {"id": "context_recall", "request": {"method": "chat", "messages": [
        {"role": "user", "content": "My invented codeword is violet-orbit-73."},
        {"role": "assistant", "content": "I will remember the codeword."},
        {"role": "user", "content": "What was my exact codeword?"}], "max_new_tokens": 64},
     "kind": "contains", "expected": "violet-orbit-73"},
    {"id": "arithmetic", "request": {"method": "chat", "messages": [
        {"role": "user", "content": "What is 17 plus 26? Reply with only the number."}], "max_new_tokens": 32},
     "kind": "equals", "expected": "43"},
    {"id": "invalid_role", "request": {"method": "chat", "messages": [
        {"role": "tool", "content": "not yet supported"}]}, "kind": "error"},
    {"id": "health_recovery", "request": {"method": "health"}, "kind": "health"},
]


def grade(case, response):
    if not isinstance(response, dict):
        return False, "response is not an object"
    kind = case["kind"]
    if kind == "error":
        ok = response.get("ok") is False and isinstance(response.get("error"), str)
        return ok, "expected structured error"
    if kind == "health":
        ok = response.get("ok") is True and response.get("model") == "vardath-scratch-chat"
        return ok, "expected healthy Scratch Chat provider"
    if response.get("ok") is not True or not isinstance(response.get("response"), str):
        return False, "missing successful text response"
    actual = response["response"].strip()
    expected = case["expected"]
    ok = expected in actual if kind == "contains" else actual == expected
    return ok, "expected " + repr(expected) + "; received " + repr(actual[:160])


def evaluate(command, cases=CASES, timeout=120):
    # All requests are sent through an actual process's stdin/stdout, not a
    # mocked serve() call. stderr is captured separately from JSONL protocol.
    payload = "".join(json.dumps(c["request"], ensure_ascii=False) + "\n" for c in cases)
    try:
        completed = subprocess.run(command, input=payload, text=True,
                                   capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"passed": False, "error": str(exc), "results": []}
    lines = completed.stdout.splitlines()
    results = []
    for index, case in enumerate(cases):
        try:
            reply = json.loads(lines[index]) if index < len(lines) else None
        except json.JSONDecodeError:
            reply = None
        passed, detail = grade(case, reply)
        results.append({"id": case["id"], "passed": passed, "detail": detail,
                        "request": case["request"], "response": reply})
    passed = (completed.returncode == 0 and len(lines) == len(cases)
              and all(item["passed"] for item in results))
    return {"passed": passed, "exit_code": completed.returncode,
            "response_lines": len(lines), "expected_lines": len(cases),
            "stderr_tail": completed.stderr[-1000:], "results": results,
            "scope": "bounded transport, context recall and arithmetic; not general conversational readiness",
            "tool_use_evaluated": False,
            "conversation_ready": False,
            "acceptance_scope": "diagnostic only: tool-call execution and real DeepThorT host integration untested"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("Provider command required")
    report = evaluate(command, timeout=args.timeout)
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
