# Dialogue acquisition and acceptance gate — 2026-11-22

## Verified status
GitHub Actions run 44986884318 completed its unit-tests job successfully (including Python compilation and dialogue/protocol tests). This predates the new deterministic resume regression test in commit c163e69b06d9f19fbf791f096bb7132eef4dbf46. No new green result is claimed yet.

## Data admission requirements
Do not label a dataset "approved" on the basis of its name alone. For each exact downloadable snapshot, record canonical source URL, immutable revision/commit, license text URL, redistribution and derivative/training permissions, attribution requirements, download SHA-256, total rows, rejected rows, and train/validation/test counts. Reject unknown, conflicting, noncommercial-incompatible (for a commercial target), or unverifiable licenses pending review. Do not mix third-party datasets into the independently initialized Scratch Chat checkpoint without this record.

Candidate investigations (not acquired or approved): OpenAssistant/oasst1 (inspect Apache-2.0 dataset license, contributor provenance and safety); HuggingFaceH4/ultrachat_200k (inspect source-generation provenance and licensing); databricks/databricks-dolly-15k (inspect dataset-specific licensing and permitted uses). Dataset-card labels alone do not establish rights to every underlying utterance. Avoid contaminated benchmark conversations and private data.

Before training, normalize conversation role turns, remove PII/secrets and unsupported tool transcripts, deduplicate normalized prompts and entire conversation groups, group related conversations before deterministic splitting, and freeze split SHA-256 hashes. Reserve test data for independent final acceptance; never tune to the held-out test. Tokenize using train split only and mask user/system tokens from assistant loss. Record any exclusion of examples exceeding context.

## Training and evaluation gates
Start with a bounded CPU smoke pilot to verify gradients, checkpoint creation, resume equivalence and masked loss. For meaningful pretraining, investigate free GPU resources (Kaggle notebooks, Google Colab free tier) subject to actual current quotas, terms and availability; no access or quota is asserted. Preserve a randomly initialized model with a documented parameter budget, dataset version, seed, optimizer state, tokenizer and code revision. Do not overwrite it with pretrained weights.

A separate evaluation harness must measure multi-turn instruction adherence, conversational coherence, held-out paraphrases, refusal calibration, tool-call JSON schema validity and end-to-end DeepThorT newline-delimited JSON subprocess requests (multiple messages per process, clean shutdown, timeout, malformed input, and output isolation). Distinguish format correctness from conversational quality. Do not claim passing acceptance from unit tests or Shakespeare next-token losses.

## This pass
Added a regression comparing every final model tensor, RNG state and held-out assistant loss between uninterrupted five-step training and two-step-plus-resume training. This is a reproducibility test, not evidence of useful conversation. No external corpus acquired or trained, no new checkpoint artifact published, and no DeepThorT application acceptance demonstrated.
