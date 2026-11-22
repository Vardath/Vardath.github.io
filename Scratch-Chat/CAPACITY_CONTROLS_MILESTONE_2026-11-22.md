# Original-weight dialogue pilot capacity controls — 2026-11-22

Latest inspected Actions run: [44976935600](https://github.com/Vardath/Vardath.github.io/actions/runs/44976935600). Connected GitHub jobs API reported the unit-tests job **completed successfully**, including the test and Python compilation steps. This predates this milestone's changes.

The dialogue pilot CLI now accepts `--width`, `--layers`, `--heads`, `--context-size`, and `--seed`, validates head divisibility before creating output files, and writes chosen controls into its pilot report. This enables explicitly configured, original-weight model-capacity comparisons, not a claim that a larger model has been trained. A regression test covers invalid head divisibility. Commit execution status for these changes must be checked independently; push-triggered Actions runs are not reliably discoverable through the connector's PR-only commit-run lookup.

Example (requires an independently reviewed, approved and hashed manifest and three decontaminated JSONL splits):
```sh
python -m capability.run_dialogue_pilot --manifest approved.json --splits reviewed-splits --output pilot-128 --steps 20 --width 128 --layers 4 --heads 4 --context-size 256 --seed 2026
```

No external dataset was acquired, approved, downloaded or trained during this pass. No conversational acceptance or real DeepThorT integration pass has been demonstrated. CPU Actions runs remain suitable only for bounded smoke tests. GPU availability and dataset rights require independent verification. The source register remains pending review; never treat its candidate list as approval.
