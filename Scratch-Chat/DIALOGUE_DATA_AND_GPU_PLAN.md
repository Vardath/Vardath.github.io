# Scratch Chat: dialogue data and compute acquisition gate

Status: candidate review, **not approved for ingestion**. The original model must remain randomly initialized; external pretrained weights are separate DeepThorT providers only.

## Source admission
For every source record dataset name, exact revision/commit, canonical URL, license identifier and license text URL, attribution requirements, redistribution/training restrictions, upstream provenance, consent/privacy review, SHA-256 digest, retrieval date, and an explicit approved/rejected decision. Dataset-card license labels alone are insufficient when the underlying conversations have different provenance. Do not ingest unknown-license scraped chats or personal conversations.

Candidates for manual license/provenance review:
- OpenAssistant/oasst1: inspect the dataset's Apache-2.0 release and per-message attribution/consent constraints before approving; inspect language and moderation flags.
- allenai/tulu-3-sft-mixture: **do not ingest by default**; mixture sources have differing licenses and must be approved individually.
- Self-authored CC0 dialogue: currently approved seed, but 27 examples are insufficient for capability.

## Split and leakage policy
Normalize Unicode, strip PII and secrets, preserve complete multi-turn conversations, and split by conversation/source document *before* tokenizer fitting or augmentation. Deduplicate normalized exact records and near-duplicates across all splits, including paraphrases and templated variants. Reserve independently authored private acceptance prompts outside the repository training corpus. Keep test records inaccessible to model selection. Emit split manifests with hashes, license/source counts, duplicate-removal counts, and contamination audit results.

## Trainable format
JSONL per conversation: {"id":"...", "source_id":"...", "license":"...", "messages":[{"role":"system|user|assistant|tool","content":"..."}]}. Validate alternating turns and tool call/result identifiers. Mask user/system/tool tokens from supervised assistant-target loss; preserve full conversation context. Distinguish explicit tool-call structures from textual claims of tool use.

## Model and compute milestones
Benchmark a modest from-scratch transformer (e.g. 6 layers, 384 width, 6 heads, ~10-30M parameters depending on vocabulary) for memory/time before scaling; keep the 64-wide 2-layer CPU smoke model only for pipeline validation. Track optimizer/RNG state, tokenizer and dataset digests, exact source revision, training step, evaluation suite version, and reproducible resume.

Free GPU possibilities requiring user-side authorization/availability verification: Kaggle Notebooks GPU quota, Google Colab free tier, and Hugging Face community-sponsored compute. None is allocated or guaranteed; GitHub Actions CPU must remain bounded smoke/CI only.

## Acceptance gate
Require independently held-out multi-turn recall, instruction following, factual uncertainty, tool-call syntax and execution round-trips through the real DeepThorT JSON-lines subprocess. Report per-category scores, raw generations, contamination audit, and failure cases. Protocol pass or falling token loss alone never constitutes conversational readiness.
