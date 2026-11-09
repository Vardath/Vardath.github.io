# Vardath Compatibility Fixes 1.0.1

[Download](Vardath_Compatibility_Fixes_1.0.1.zip) · [Current findings and live checks](vardath_compatibility_fixes/REVIEW_1.0.1.md) · [Three-mod update](../x4-updates/X4_Hyperion_Tours_Update_2026-11-10.zip)

Retains the six 1.0.0 fixes and addresses new errors in `debug(20261109-150118).log`:

- Native mission cleanup now iterates a cloned work list with a private counter; immediate callbacks cannot invalidate the next submission index.
- Inventory Collector initializes the conventional common-handler debug variable without changing collection, routing or deposits.
- HeadHunter expires orphaned watchers safely when the pilot or tracking fields are gone, retaining its bounty/death handling.
- Emergent Missions' late rescue update signals its single-use cleanup only while waiting, with the deferred-signal race handled.

The existing incompatible-ammo, captainless academy, HQ conversation, mismatched-trade, stale-invasion-gate and late mission callback guards remain.

Exit X4 and extract into its game directory, overwriting `extensions/vardath_compatibility_fixes`. Enable the extension and load the same save. Keep **Protected UI** and **Inventory Collector** enabled. Third-party dependencies are optional. No UI replacement, free rewards, new game, quest reset or changes to your other mod folders.

Fifteen source/fault contracts pass. All **29 operations in nine diff files** apply uniquely to exact pinned references; XML/diff grammar and ZIP contents are checked. **Runtime testing was unavailable.** HeadHunter's Lua import blocked by Protected UI, missing ship/engine catalogs and unrelated old selectors remain unresolved. The separate Hyperion Ascendant extension supplies the Hyperion story routing repair.

To reproduce: install `lxml>=5,<7`, run `tools/validate.py`, then `tools/package.py`. Exact source URLs/checksums are in `tools/sources.json`; original scripts are downloaded for checking, not redistributed.
