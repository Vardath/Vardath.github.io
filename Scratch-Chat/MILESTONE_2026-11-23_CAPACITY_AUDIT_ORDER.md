# Scratch Chat CI repair — 2026-11-23 (16:06 Brisbane)

Verified push run [45119069826](https://github.com/Vardath/Vardath.github.io/actions/runs/45119069826) **failed**. Retrieved actual job logs: `test_dialogue_capacity_cli.CapacityControlsTest.test_rejects_incompatible_heads_before_creating_outputs` expected `ValueError`, but the lexical audit opened absent `train.jsonl` and raised `FileNotFoundError` first. Other selected suites passed; the dialogue wildcard suite failed.

Commit `74bd12e315aac7daa58ec961ce680441b7e9bbe1` restores validation of width/layers/heads/context/steps/merges before reading split contents, preserving mandatory lexical screening before tokenizer fitting, output creation or training. The previously fixed overwrite guard remains in place.

Follow-on push workflow must be checked for a green result; no local or CI success is claimed here. No new model training or quality metrics were produced. Dolly remains quarantined. Outstanding: approve licensed dialogue corpus and privacy review; immutable train/validation/test admission; bounded original-weight training and reproducible checkpoint; held-out multi-turn/tool-use scoring; actual DeepThorT JSONL acceptance. No Shakespeare-only training.
