# Vardath Compatibility Fixes 1.0.3

[Download](Vardath_Compatibility_Fixes_1.0.3.zip) · [Current findings and live checks](vardath_compatibility_fixes/REVIEW_1.0.1.md) · [Three-mod update](../x4-updates/X4_Hyperion_Tours_Update_2026-11-10.zip)

**1.0.3 (log 2026-11-12, 22:20):** The Fly-by Looting compatibility guard now excludes ammunition pickups from L/XL ships. The latest log shows 129 `collect_drop` rejections, only for the large Hyperion Ascendant and Warlord-class mothership. The native command is not called for those large-ship ammo drops, but S/M missile pickups with capacity and all other existing Fly-by Looting behaviour remain unchanged. This does not modify either ship's storage or destroy the floating ammunition containers. Static patched-source tests confirm the guard; only a new X4 run can confirm the runtime result.

**1.0.2:** GalaxyTrader MK3's destroyed-ship event now checks for a valid sector name before logging. This prevents repeated destroyed-ship sector property-lookup errors without changing trader assignments, pilot rescue, orders or balances. A separate Vardath Invincibility 1.02 update guards non-defensible player gate construction sites; this compatibility mod does not modify the gates extension itself.

Retains the six 1.0.0 fixes and addresses new errors in `debug(20261109-150118).log`:

- Native mission cleanup now iterates a cloned work list with a private counter; immediate callbacks cannot invalidate the next submission index.
- Inventory Collector initializes the conventional common-handler debug variable without changing collection, routing or deposits.
- HeadHunter expires orphaned watchers safely when the pilot or tracking fields are gone, retaining its bounty/death handling.
- Emergent Missions' late rescue update signals its single-use cleanup only while waiting, with the deferred-signal race handled.

The existing incompatible-ammo, captainless academy, HQ conversation, mismatched-trade, stale-invasion-gate and late mission callback guards remain.

Exit X4 and extract into its game directory, overwriting `extensions/vardath_compatibility_fixes`. Enable the extension and load the same save. Keep **Protected UI** and **Inventory Collector** enabled. Third-party dependencies are optional. No UI replacement, free rewards, new game, quest reset or changes to your other mod folders.

Static source/fault contracts cover **ten targeted diff files**, including the GalaxyTrader destroyed-ship guard. All native diffs apply uniquely to exact pinned references; XML/diff grammar and ZIP contents are checked. **Runtime testing was unavailable.** HeadHunter's Lua import blocked by Protected UI, missing ship/engine catalogs and unrelated old selectors remain unresolved. The separate Hyperion Ascendant extension supplies the Hyperion story routing repair.

To reproduce: install `lxml>=5,<7`, run `tools/validate.py`, then `tools/package.py`. Exact source URLs/checksums are in `tools/sources.json`; original scripts are downloaded for checking, not redistributed.
