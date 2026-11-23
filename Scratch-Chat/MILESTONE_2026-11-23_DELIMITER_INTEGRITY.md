# Scratch Chat milestone — 2026-11-23: delimiter integrity

Verified [GitHub Actions source-test run 45093092918](https://github.com/Vardath/Vardath.github.io/actions/runs/45093092918): unit-tests job completed successfully, including checkpoint-independent dialogue/protocol tests. This run predates the changes below.

Commits:
- 6e5b32edd15f8661d16cb65d478ee8bc7a400bcd: admission rejects reserved chat serialization delimiters embedded in external message content.
- 654daed138572cf4a67d8fb5c813a5b857f8967f: regression checks user/assistant delimiter injection.

Why: embedded role or end-of-turn tokens can corrupt supervised chat boundaries and enable fabricated assistant turns in untrusted imported data. This is a narrow input-integrity repair, not a substitute for source licensing, consent, semantic decontamination, or training.

No Shakespeare-only training, new conversational checkpoint, or quality improvement in this pass. Dolly remains quarantined. Push-triggered CI for these new commits must be checked independently; no green claim until a completed job is inspected.

Next: obtain independently reviewed, revision-pinned, privacy-screened conversational data; record per-source obligations and content hashes; decontaminate all three splits; run bounded original-weight SFT; evaluate independent multi-turn/tool probes against actual checkpoint predictions through the JSONL subprocess and installed DeepThorT. CPU Actions is only pilot infrastructure. Free GPU availability is not established; candidate platforms require explicit access and terms verification.
