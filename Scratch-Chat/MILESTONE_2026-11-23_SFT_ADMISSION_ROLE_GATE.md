# Scratch Chat admission boundary milestone — 2026-11-23

Verified previous push-triggered source-test run [45085855009](https://github.com/Vardath/Vardath.github.io/actions/runs/45085855009) succeeded on commit d9160b106313907171d2462bfd1b10a8ab198b68. This was source-test success, not conversation acceptance.

## Change

The manifest verifier used by `capability.run_dialogue_pilot` previously validated role/content types and cross-split hashes but admitted incomplete and malformed message ordering, including orphan tool messages and conversations ending in a user turn. The separate external-data auditor had stronger role validation, but the actual SFT pipeline did not call it. The training boundary now rejects malformed role order and requires a final assistant answer. Added regression tests for valid multi-turn and tool-response histories and six malformed histories. Updated older test fixtures to contain complete conversations.

## Limitations and next gate

This does not authenticate external licenses, approve Dolly, perform semantic near-duplicate removal, train new dialogue weights, or demonstrate independent DeepThorT integration. The project still needs reviewed data and substantial GPU training. A green source-test run will verify code invariants only. Avoid Shakespeare-only runs as conversational evidence.
