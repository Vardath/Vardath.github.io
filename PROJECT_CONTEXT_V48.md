# DeepThorT v48 — indexed X4 roadmap repair and truthful diagnostics

Date: 23 November 2026. Baseline: verified v47 `d693150e7c972c23b647f1b3581dc4c1ec3d8d4e`.

## User report and grounded diagnosis

`DeepThorT-Diagnostics-20261123-120446.zip`, generated 02:04:49 UTC, shows a `draft_plan` request #25 (7,422 original characters) that failed at 01:00:49 UTC after indexed source review, then failed again at 02:04:36 UTC approximately **two seconds after retry**. The second attempt produced **no new ONNX inference request**: `HierarchicalPlanStore.prepare` rejected model-proposed plans missing X4 extension metadata, MD XML, assets/libraries XML and PE behaviours. The diagnostics show normal ONNX startup and three successful local model responses in the earlier session; they do not demonstrate an ONNX connection reset on the final retry.

The release v47 `desktop_app.py` inadvertently logged startup `version='46'`; this field was stale and does NOT alone establish whether a v47 overlay was installed. v48 records `48`.

## Change

- New `deepthort_local/indexed_roadmap_repair.py`: when indexed X4 sections are complete but combined plan validation fails with missing X4 criteria, use up to the remaining 40-call planning allowance to ask local Qwen for targeted corrections to model-proposed files. A correction prompt contains one complete verbatim indexed source section, its original index and bounded advisory metadata, rather than truncating the specification. Full original specification remains indexed and validated in aggregate.
- `SpecificationIndex.merge_model_revision`: parse corrections using the same safe target and structural parser; refuse Python application stages in X4 mods, cross-section conflicts, loss of already satisfied criteria and 24-file-per-section overflow. Store only genuinely changed model-authored fragments atomically. An independent monotonic per-request attempt ID avoids repeatedly replaying the same cached malformed answer when retried.
- Existing hierarchy and required X4 validator stay authoritative; no automatic approval, source editing, prewritten file intentions or remote inference.
- `desktop_app.py`: recoverable indexed planning exhaustion now says PLAN STILL INCOMPLETE, not a generic model reply failure; startup version marker corrected.

## Test limits

Linux scripted models and Xvfb can reproduce/fix the logical dead-end, but only the user's physical Windows installation and real ONNX inference will prove whether the actual Qwen model supplies sufficient content. The user has not been asked to reduce their 40-pass budget. Installation, gameplay and reliable UI simulation are not inferred from a valid plan.
