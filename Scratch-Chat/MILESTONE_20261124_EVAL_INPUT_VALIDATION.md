# Scratch Chat — held-out evaluation input validation (2026-11-24)

Baseline: GitHub Actions original dialogue smoke run 45257993758 failed at DeepThorT JSON-line transport after successful bounded 80-step original-weight training and held-out loss evaluation. Its source-test companion 45258019585 passed. Subsequent newline-framing repair was committed, but this milestone does not claim its follow-on workflow passed: push-triggered runs are not returned by the connector's commit-run lookup.

Commits 65ecfb35 and 6e9f21a add fail-closed handling and regression coverage for malformed final evaluation messages. Previously a non-object final message could raise AttributeError rather than a controlled ValueError. This is evaluation infrastructure, not a conversational quality improvement. Source test CI and smoke execution on these commits remain to be checked. No Shakespeare-only run, external dataset admission, GPU training, or checkpoint quality claim in this pass.

Next: inspect latest smoke jobs and artifacts for the newline repair, independently license-review larger conversational data, prepare immutable decontaminated splits, run bounded original-weight pilot, and test held-out multi-turn/tool-use semantics through the actual DeepThorT JSON-line interface. GitHub CPU must not be represented as large-scale GPU pretraining.
