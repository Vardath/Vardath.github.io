# Compatibility review and acceptance — 1.0.0

## Evidence and limits

Input: complete `debug(20261109-083003).log`, 6,659,541 bytes, 38,842 lines, SHA-256 `bbf6560a418f4f8336770277ea6143cded75d446618c8867d1f6463b585426c5`. X4 9.00 (611726), Occupations 0.4.6 in that recording. Occupations 0.4.7 was published separately; this package does not change it.

The file contains 2,178 error-tag occurrences and no fatal/crash stack. It does not establish what crashed the game. No X4 executable, save, crash dump or effective merged installed catalog is available here. Source-level guards do not prove a successful runtime or identify the originating mod for every bad state.

| Source-confirmed issue | Logged occurrences | Implemented boundary |
|---|---:|---|
| `md.fbl.fbl_cue`: incompatible AmmunitionContainer | 32 | The old check tests generic missile storage. The new check requires a valid drop, ship, actual missile ware and free capacity for **that ware**, using documented `ammostorage.{$ware}.free`. The existing native `collect_drop` is retained. No drop destruction, invented ammo or change to ordinary inventory collection. |
| `GT_Context_Academy`: null pilot name | 2 | `$ship.pilot?` tests property presence; it can admit a ship without an NPC captain. Require `$ship.pilot.isclass.npc` before evaluating the entry. Captainless ships remain ineligible and can become eligible when staffed. No fabricated name, captain or course. |
| `ResearchBlueprintsMod.RBM_Start`: null actor | 2 | Remove actor-valued event filters that are evaluated before a manager exists. Both documented conversation events expose the actual actor as `event.object`. A subsequent condition requires that actor to equal the real assigned HQ manager, and retains the original research-unlocked condition. It re-evaluates against the current manager per event; other NPC conversations cannot enable the entry. No research state reset or new UI addon. |
| `order.trade.routine`: different buy/sell wares | 2 | Before the existing assertion and after the existing resume label, reject a pair only when both offers exist and their wares differ. Clear both references, log the rejection and resume `find trade run`. That native path runs `move.idle` for 5–10 seconds on player ships or 10–45 seconds on NPC ships before searching. Matching pairs and buy-only/sell-only runs remain unchanged. No cargo reservation/order creation is allowed from the mismatched pair. |
| `FactionGoal_Hold_Space.EvaluateState`: wrong exit sector | 82 | Rebuild a local list of existing entry points whose existing exits lead to the intended sector. Use this list in the original defence loop. The native assertion, force allocation and station-defence fallback remain. The original saved invasion list and gates are unchanged, so a temporarily rewired gate can become eligible again on a later evaluation. Log filtering at most once per ten game minutes per evaluating cue. This guards stale cached input, not the unknown cause of the map/story inconsistency. |
| `MC_Management`: non-mission update/missing cleanup listener | 2 | Add `hasmission` to the first-failure update gate, keeping failed-mission accounting. Emit cleanup only when its single-use cue is waiting. The signal remains deferred as in native code. `check=false` is restricted to these guarded cleanup signals because the native MD schema specifies delivery after the current actions: another already-queued callback can consume the single-use listener before delivery. No cue reset, instant re-entrant cleanup, reward replay or cleanup action replacement. |

## Reference provenance

- Extracted native 9.00 source: [ArtByunex/x4-foundation-artbyunex](https://github.com/ArtByunex/x4-foundation-artbyunex/tree/e3e8a345e5624db118bff3eb171b60b0993fcc2c), commit `e3e8a345e5624db118bff3eb171b60b0993fcc2c`. The three affected native scripts, `common.xsd`, `md.xsd`, `diff.xsd` and `scriptproperties.xml` were inspected. These are reference files, not the user's merged catalogs.
- [GoAhead-at/galaxy_trader_v9](https://github.com/GoAhead-at/galaxy_trader_v9/tree/b292a80489980771406b6e5498b395b1e5343778), commit `b292a80489980771406b6e5498b395b1e5343778`, academy library. Source content version 1.00.04 dated 2026-11-07 matches the log's version/date. The installed Workshop ID is `ws_3715175855`, folder `galaxy_trader`; the manual release ID is `GalaxyTraderMK3`.
- [YuJin44/researchblueprintsmod](https://github.com/YuJin44/researchblueprintsmod/tree/36c6a0772fda4938e5cf5a67a650c40722ae255e), commit `36c6a0772fda4938e5cf5a67a650c40722ae255e`. Content ID `ws_2961007180`, version 1.06 dated 2024-05-01 matches the log. Folder `researchblueprintsmod`.
- Original author [Fly-by Looting Workshop download](https://steamcommunity.com/sharedfiles/filedetails/?id=1683358279), version 1.11 dated 2020-04-09, folder `fbl`. Retrieved the Workshop's actual XRWS catalog using its public published-file details, extracted `md/fbl.xml`, and verified its embedded MD5 `db4db1d952636d0eb2943e707865ab75`. The logged line 37 matches the actual missile collection call. No secondary snippet was used as a substitute for the source.

`tools/sources.json` records exact URLs and normalized-LF SHA-256 hashes. The package ships only our XML diffs; it does not redistribute entire native or third-party scripts. Exact old-guard matching makes the one-line academy/ammo changes no-ops if an upstream release has already replaced those guards. Other upstream structural changes require source review rather than a claim of universal compatibility.

## Checks performed

- Parsed all extension XML. Validated all six diff documents against the pinned native diff XSD.
- Applied every operation sequentially to the exact full referenced script, requiring **one match for each of 22 operations**. References and resulting XML parse successfully.
- Checked relevant native property metadata, cue-state lookup and documented conversation event fields. Full game MD/AI schema validation is not claimed.
- Executed **nine contracts** with multiple valid/invalid scenarios using the actual shipped guard strings. Checked absent captain/HQ/loot, wrong actor, replaced manager, incompatible/full ammo, valid and one-sided trades, stale/missing/restored gate inputs, late cleanup states, limited diagnostics and upstream guard changes.
- Compared untouched structures to the originals, including native mission cleanup/rewards, the rest of the trade routine and all unrelated academy/research/loot logic. Checked no UI/assets/companion modifications and optional dependencies.
- Built deterministic ZIP with `extensions/vardath_compatibility_fixes/` at its root; compared every archive member byte-for-byte with source and checked CRCs.

These checks validate source application and guard outcomes, **not live X4 execution, actual merged load order, engine event ordering or save/load behavior**.

## Existing-save acceptance

Use a normal backup save and start X4 with `-debug all -logfile debug.log`. Keep Protected UI, Inventory Collector and your existing occupations enabled. Confirm Compatibility Fixes version 1.00 is enabled in Extensions.

1. **Ammo:** on the previously affected ship, approach compatible and incompatible missile drops. Compatible missiles may collect if that ware has capacity; incompatible/full-ware drops must remain and produce no attempted-collection error. Check ordinary personal-inventory loot still collects. Inventory Collector may independently pick up objects, so distinguish its activity from Fly-by Looting.
2. **Academy:** open GalaxyTrader's academy with both staffed and captainless player ships. Only trainable staffed ships should be listed; no null-pilot error. Add a real captain to the excluded ship and refresh. Verify ordinary courses still function.
3. **Research:** load before obtaining/staffing HQ, then when research is unlocked speak to the actual HQ manager. The research option should appear only with that manager. Speak to other station managers, replace the HQ manager, and save/load. No null conversation-actor error and no reset progress.
4. **Trade:** allow the affected trader to continue. If the inconsistent offer pair recurs, expect `VCF: rejected mismatched trade pair` followed by a native delayed new search. Verify actual same-ware buy/sell orders and cargo/credits changes, then interrupt with a direct order and save/load. No mass order cancellation or fast retry loop.
5. **Gate defence:** continue through another faction-logic evaluation with the problematic link. `VCF: deferred stale invasion entry points` may appear at most once per ten game minutes for that cue. Native fallback station defence must continue; inspect the actual galaxy link/story separately. If the native story later restores its exit, it should be accepted at the next evaluation. Do not manually rewire or reset the quest as part of this patch's test.
6. **Mission cleanup:** finish/abandon a multi-part mission chain and test save/load around completion. A late callback must not update a non-mission or restart an already consumed cleanup. Real legitimate native rewards should occur once; an abandoned/failed chain must not acquire a new reward. Check the specific two logged error signatures and ordinary mission progression.
7. **Preservation:** existing taxi/tour passengers, crystal stock/invoices, crews, ship equipment, Kopis weapon and player-issued orders must persist. Check normal occupation payments in the vanilla transaction ledger. No payment code is changed here; the earlier log's 192 balance-matched receipts totalling 66,010,000 Cr remain evidence only for those recorded transactions.

## Errors deliberately left unresolved

| Remaining family | Why this package does not guess a repair |
|---|---|
| Koha engine candidates (20), ShipGenerator candidates (81), native faction loadout and Yaki supply (one each) | Requires actual installed asset/ware/faction catalogs and load order. Placeholder equipment would conceal missing data and can damage spawn behavior. |
| External XPath failures (59) | Gramston Ships, Trader Seminars, Pirate Chaos Conflict, No Ship Limits, Pilot Training and NPC Economy Tweaks are among the named files. Need their installed target scripts/versions and earlier merge results to fix selectors correctly. |
| Hyperion `WayHomeTable` / `Investigation_CorrectGate` (3) | A saved quest-state issue is not resolved by guessing a destination, completing a mission or changing a story gate. Need the relevant save/mission state and installed story source. |
| HeadHunter import blocked by Protected UI (one) | A protection-compatible upstream packaging/code change requires its source. This extension neither disables protection nor whitelists arbitrary imports. |
| Save-header queries (816), stale mission/component UI queries (24/56), repeated texture/text/ware/character/plan diagnostics | Debug log lacks the caller stacks and complete corresponding data. Counts alone do not establish corruption or a crash cause. |
| Universal Cargo Teleport failed undocked trade probes (12) | They already correlate with explicit zero-transfer rejection and docking retry. Do not invent the numeric engine reason, generate cargo or bypass payment. |
| Actual game crash | No fatal error/exception/crash stack exists in the upload. These guards are not a demonstrated crash cure. |

The useful next inputs for the unresolved data/selector families are the named installed extension folders (including their catalogs and `content.xml`), the installed extension list/load order, and a crash dump/stack if X4 produced one. For Hyperion, include the relevant save. No removal of essential mods is requested.
