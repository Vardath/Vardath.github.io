# Scratch Chat milestone — 2026-11-23 finite contamination threshold

## Verified baseline
GitHub Actions source-test run 45160508915: unit-tests completed successfully, including checkpoint-independent dialogue/protocol tests and compilation. This predates the changes below.

GitHub Actions pilot result commit b75018d1aaf076443fbc98f4e30c66d54a8a0cd3 records run 45163287592, validation loss 3.062591 and test loss 3.068315. These are token-prediction measurements, **not** conversational acceptance or proof of dialogue training.

## This pass
The cross-split lexical near-duplicate audit previously allowed a NaN threshold because comparisons with NaN are false. NaN could therefore silently disable the screening gate. The audit now rejects NaN and positive/negative infinity, as well as out-of-range thresholds. Regression tests cover all six invalid values.

Commits: ad75ddf920f91d14ee2bb44c778049d979efd312 and adf18b1ed075d6db1f15f2da882892325bef87a8. Follow-on source CI triggered by pushes; final result not yet established when this milestone was authored.

## Capability and data gate
No new dialogue corpus admitted, no dialogue checkpoint trained, no conversational success claimed. OpenAssistant and other external candidates remain pending independent license, privacy, attribution, and source-revision review. The small self-authored CC0 seed is insufficient for competence. Never substitute pretrained weights into the independent Scratch Chat model.

Next: acquire and review a usable external dialogue corpus, pin exact revisions and hashes, decontaminate conversation-group splits, run bounded original-weight dialogue training, then record independent multi-turn/tool-use and real DeepThorT JSON-line transcripts. Free GPU services require verified access and permission; GitHub Actions CPU is limited to bounded pilot work.
