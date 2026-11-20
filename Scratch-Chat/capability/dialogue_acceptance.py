"""Independent deterministic capability probes for a randomly initialized dialogue checkpoint.

These prompts are not part of the 18-example seed. Exact scoring is deliberately
strict and is not a claim of general conversational competence.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

CASES = [
    {"id":"arithmetic_unseen","category":"reasoning","messages":[{"role":"user","content":"What is 8 plus 5? Answer with digits only."}],"expected":"13"},
    {"id":"instruction_unseen","category":"instruction","messages":[{"role":"user","content":"Respond with exactly: violet"}],"expected":"violet"},
    {"id":"multi_turn_recall","category":"multi_turn","messages":[{"role":"user","content":"Remember the code word is lantern."},{"role":"assistant","content":"Understood."},{"role":"user","content":"What was the code word? Reply with the word only."}],"expected":"lantern"},
    {"id":"tool_boundary","category":"tool_use","messages":[{"role":"user","content":"Use a calculator tool to compute 19 * 7. If no tools are available, say exactly NO_TOOL."}],"expected":"NO_TOOL"},
]
def evaluate(checkpoint, tokenizer, output):
    requests = [{"method":"health"}] + [
        {"method":"chat","messages":case["messages"],"max_new_tokens":32}
        for case in CASES
    ]
    proc = subprocess.run(
        [sys.executable,"-m","capability.deepthort_bridge",
         "--checkpoint",str(checkpoint),"--tokenizer",str(tokenizer)],
        input="".join(json.dumps(req)+"\n" for req in requests),
        capture_output=True,text=True,timeout=120,check=True)
    rows = [json.loads(line) for line in proc.stdout.splitlines()]
    if len(rows) != len(requests):
        raise RuntimeError("Bridge returned wrong number of JSON-line responses")
    if not rows[0].get("ok") or rows[0].get("ready_for_conversation") is not False:
        raise RuntimeError("Bridge readiness health contract failed")
    results=[]
    for case,row in zip(CASES,rows[1:]):
        if not row.get("ok") or not isinstance(row.get("response"),str):
            raise RuntimeError("Bridge chat contract failed for "+case["id"])
        response=row["response"].strip()
        results.append({"id":case["id"],"category":case["category"],
                        "expected":case["expected"],"response":response,
                        "passed":response==case["expected"]})
    report={"benchmark":"independent-dialogue-development-v1",
            "seed_examples_in_benchmark":0,
            "checkpoint":str(checkpoint),
            "protocol_pass":True,"ready_for_conversation":False,
            "passed":sum(x["passed"] for x in results),
            "total":len(results),"cases":results,
            "limitations":"Four development checks; not a validated conversational benchmark. No actual tool invocation API is implemented."}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--checkpoint",type=Path,required=True)
    parser.add_argument("--tokenizer",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(evaluate(args.checkpoint,args.tokenizer,args.output)))
if __name__=="__main__":
    main()
