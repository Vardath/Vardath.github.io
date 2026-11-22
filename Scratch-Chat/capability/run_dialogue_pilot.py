"""Fail-closed, original-weight dialogue SFT pipeline.

Requires a reviewed source manifest and three immutable split files.
Never fits tokenizer on validation/test; never trains on test; never downloads
or substitutes pretrained weights. This is a bounded CPU pilot, not acceptance.
Run from Scratch-Chat root: python -m capability.run_dialogue_pilot ...
"""
import argparse
import json
from pathlib import Path

from capability.dialogue_source_manifest import verify_split_files
from capability.dialogue_format import export as serialize
from capability.dialogue_tokenizer import build as fit_tokenizer
from capability.dialogue_labels import export as label
from capability.dialogue_sft_train import run as train


def run_pipeline(manifest_path, splits, output, *, steps=10, merges=128,
                 context_size=256, width=64, layers=2, heads=4, seed=2026):
    manifest_path, splits, output = map(Path, (manifest_path, splits, output))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_split_files(manifest, splits)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Output directory must be new/empty; do not overwrite checkpoints")
    if steps < 1 or merges < 0:
        raise ValueError("Invalid training controls")
    output.mkdir(parents=True, exist_ok=True)
    serialized = output / "serialized"
    serialized.mkdir()
    serialized_provenance = {}
    for split in ("train", "validation", "test"):
        serialized_provenance[split] = serialize(splits / (split + ".jsonl"),
                                                serialized / (split + ".jsonl"))
    tokenizer_path = output / "tokenizer.json"
    tokenizer_info = fit_tokenizer(serialized, tokenizer_path, merges=merges)
    labeled = output / "labeled"
    labeled.mkdir()
    labeled_info = {}
    for split in ("train", "validation", "test"):
        labeled_info[split] = label(serialized / (split + ".jsonl"), tokenizer_path,
                                    labeled / (split + ".jsonl"))
    # The test split is deliberately excluded from optimization and checkpoint selection.
    checkpoint = output / "original_sft.pt"
    from capability.bpe import ByteBPE
    vocab_size = ByteBPE.load(tokenizer_path).vocab_size
    metrics = train(labeled / "train.jsonl", labeled / "validation.jsonl",
                    checkpoint, vocab_size=vocab_size, steps=steps,
                    width=width, layers=layers, heads=heads,
                    context_size=context_size, seed=seed)
    report = {"manifest": str(manifest_path), "source_id": manifest["source_id"],
              "source_revision": manifest["revision"],
              "serialized": serialized_provenance, "tokenizer": tokenizer_info,
              "labels": labeled_info, "training": metrics,
              "checkpoint": str(checkpoint),
              "test_used_for_training_or_selection": False,
              "acceptance_passed": False,
              "limitations": "CPU pilot only; independent multi-turn and real DeepThorT JSONL acceptance required"}
    (output / "pilot_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--splits", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--merges", type=int, default=128)
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.manifest, args.splits, args.output,
                                  steps=args.steps, merges=args.merges), indent=2))


if __name__ == "__main__":
    main()
