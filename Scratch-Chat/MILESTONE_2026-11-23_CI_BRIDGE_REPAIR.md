# Scratch Chat CI repair — 2026-11-23

## Verified starting state
GitHub Actions source-test run 45065249132 (commit c800b351ec3087541865815e32d747cdea5b4f18) completed **failure**. Job 137339833251 logs show two bridge tests raising AttributeError because direct test-constructed ModernScratchTransformer objects lack chat_format; two assistant-label assertions failed because they still expected assistant text without the newly supervised <|im_end|> termination markers. JSONL transport also errored, consistent with the bridge issue. Original dialogue smoke run 45057667103 also failed on the same bridge attribute issue.

## Changes
- Commit 2a61d06c921b64d6e9605bb7c90301c94a6aa345: bridge defaults absent chat_format to legacy for direct constructed models, retaining explicit SFT tagging for loaded SFT checkpoints.
- Commit 9a5574c8272b96f46f75390926d78ab6e9c1d363: label regression expectations now include the supervised assistant termination markers.

## Limitations and next milestones
Push CI must pass before these repairs are considered verified. Dolly remains quarantined pending source-specific license/privacy admission; no training checkpoint or conversational capability is claimed. Next: validate push CI, admit licensed dialogue, execute bounded from-scratch SFT, verify actual subprocess JSONL exchange and independently held-out multi-turn/tool-use evaluations. CPU Actions cannot replace GPU pretraining.
