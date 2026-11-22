# Scratch Chat — prompt/family leakage hardening (2026-11-23)

Verified GitHub Actions source-test run [45035111424](https://github.com/Vardath/Vardath.github.io/actions/runs/45035111424): unit-tests completed successfully after the preceding tokenization and fixture repairs. Earlier run [45035102647](https://github.com/Vardath/Vardath.github.io/actions/runs/45035102647) failed.

This pass extends the final `capability/dialogue_admission.py` file-level gate: identical normalized sequences of user prompts cannot appear in different splits even with different assistant answers; upstream `conversation_id`, `source_conversation_id`, and `template_family_id` are isolated across splits when supplied. Added tests for these leaks and distinct valid families. Generic repeated prompts may now be rejected conservatively. This check does not detect paraphrases or authenticate source claims, and cannot reconstruct missing family identifiers.

Commits: f419420a, 7e11049f, 5ac0abd. New push-triggered CI remains to be verified. No external Dolly examples are approved or trained on; no checkpoint or DeepThorT application acceptance is claimed. Next: independently review source licensing/privacy, admit only defensible records, run original-weight dialogue pilot and independent multi-turn/tool-use evaluation. Do not use Shakespeare-only experiments as conversation evidence.
