# Log review and compatibility corrections — 0.4.4

Reviewed on 9 November 2026 (Australia/Brisbane).

## Evidence from the supplied session

`debug(20261108-154336).log`: 5,106,581 bytes, 32,155 lines; SHA-256 `95f6b0b9975a7f879a3df1aec3b9942897df71fc18e68f657cabd8f3cfe5c4cf`. Loaded Occupations 0.43, Kopis/Astrid 1.16, Builders 1.75 and the other current companion versions. The last script event is at game time 9161.21. This session has different ship IDs and starts at game clock zero, so it is not a controlled replay of the preceding session.

| Recorded work | Events | Confirmed credits |
|---|---:|---:|
| Stock-backed off-screen crystal sales | 136 | 8,353,000 Cr |
| Full luxury tour | 1 | 5,000,000 Cr |
| **Total** | **137** | **13,353,000 Cr** |

Every recorded payment matches its own before/after balance difference. No repeated ship/invoice or ship/contract payment IDs were found. These figures are newly recorded payments, not repeated cumulative activity snapshots.

The full tour is **Astrid Tours ZBI-439**. It visits **20 distinct sites across 15 sectors**, then all **ten** passenger departure entries name the booked destination, **HOP Shield Component Factory I AVY-857**, at game time 7850.54. The full-party completion and 5,000,000 Cr payment follow at 7850.85. That is direct evidence for a completed cross-galaxy luxury itinerary, destination departure and payment. These particular departures are labelled `native_offscreen=1`: the same native actor/roster handoff is confirmed, while ten visible walking animations are not recorded. A subsequent ten-passenger tour is already 3/20 stops underway. The ordinary Astrid reaches 18/20 with two passengers; several other tours are progressing.

The scanner records **13 completed station visits and 104 queued component samples**, with a signal-leak survey reported on each completion. The old `Manager.SelectMission` lookup error is absent. Queue registration is not proof that native module scan levels have already been published. There is no new visible crystal harvesting/counter-return demonstration here: the paid crystal cycles are explicitly off-screen resource/stock-backed operations.

Neither VRO nor Crime Has Consequences appears in the new 147-extension list; both were in the preceding 149-extension list. The earlier CHC null-object flood, missing-character model/mesh flood and Terran frigate job error are absent. Gender Spawn-Ratio and Character Adjustments remains loaded, so its presence alone does not substantiate the earlier character-error suspicion.

## Corrected in 0.4.4

### 1. Cold-start registry check

One error at game time zero comes from `VGO_CrystalShop.RecoverVisitsV39` checking `md.VGO_State.Init.$Ships.count` before the registry exists. A separate first `check_value` now checks presence before the original count condition. MD conditions run in sequence and stop after a failed check. No registry is invented, no crew is recreated, and the saved-visit recovery actions are unchanged. The existing controller still retries every five seconds and can recover the same saved actor/visit once the registry is ready.

### 2. Invalid station loadout fallback in our compatibility patch

There are **55** errors from the exact expression `if $PossibleWares.count then $PossibleWares else null`: 52 in initial `FinaliseStations` construction and three in its new-station library under faction logic. This expression was introduced by our compatibility patch. The native action requires a list or table; explicitly supplying null does not mean omitting the argument to request native defaults. The earlier static test incorrectly accepted that assumption.

Both custom `wares` overrides are removed. Native `generate_loadout` receives its original `$PossibleWares` list, including an empty list where appropriate. The two existing guards against an absent faction equipment-table entry are retained. Native construction/loadout sequencing and nonempty equipment lists stay intact. The validator now permits this station compatibility file to change only those equipment-table guards, preventing reintroduction of a ware-argument replacement.

This corrects our invalid type argument. It does not create a missing Yaki/Fallen Families equipment catalogue or retroactively re-equip stations. The underlying 52 native "no sensible wares" diagnostics may remain when the installed faction setup supplies no equipment. It does not change the Forge main weapon, ship equipment or player stations by a retrofit script.

### 3. Optional Auto Trade Subscriptions compatibility

The log records **36** `ramautosubs_Init` errors from 18 conditions whose eligibility side uses `faction.argon` (and the other real faction identifiers), but whose ownership side uses an undefined bare name such as `{argon}`. The prior optional patch fixed only the separate alliance check.

The same narrowly matched, silent attribute correction now covers those 18 logged conditions too: both sides refer to the same `faction.<id>`. The existing alliance correction is retained. No subscription action, price, eligibility rule or UI is replaced. Absent mod files and already-corrected checks are optional no-ops. The third-party initialization cue is not forcibly reset: this fixes its conditions when its own cue executes, rather than replaying purchases or grants on an existing save.

All job AI, navigation, payment, passenger lifecycle, crew-return actions, turret and UI files remain byte-identical to 0.4.3. Only the cold-start MD condition, station compatibility guards/removal, optional subscription conditions and extension metadata change. Runtime 42 is retained; no bulk worker restart, order clearing or new game is required. All companion extension sources remain unchanged.

## Remaining messages

There are 2,917 error-tagged entries in total, including informational startup diagnostics. They are not 2,917 confirmed gameplay failures. Notable remaining groups:

| Message group | Entries | Interpretation |
|---|---:|---|
| Destroyed/invalid UI table | 696 | `helper.xpl GetCellContent` receives table ID 104 after it has been destroyed. The callback's originating addon is not identified. |
| Stale mission UI ID | 336 | Mission/offer details queried after an ID is unavailable; owner of the stale UI request is not established. |
| Missing Yaki fighter generation | 49 failed jobs | No ship matches military/plunder S-ship selection for `yaki_fighter_escort_mixed`. The missing-candidate complaint is separate from Occupations jobs. |
| Missing scavenger escort generation | 11 failed jobs | No S fighter matches `scavenger_escort_common`. |
| Native faction equipment warnings | 52 | Empty equipment catalogues for Yaki/Fallen Families; distinct from our corrected null argument. |
| Auto Trade Subscriptions | 36 | The exact bare-faction conditions covered by this update. |
| Third-party patch failures | 59 | Includes GramstonShips, Trader Seminars, NPC Economy Tweaks, Pilot Training and other installed patches. A failed patch identifies its authoring mod, not necessarily the other side of a conflict. |
| Save-header metadata XML | 126 | Reads capped at `maxsize=0x1000`; not proof that a complete save is corrupt. |

Other named contexts include Emergent Missions rescue callbacks, JP explorer scripts, native trade/escort AI, Research Blueprints and two Fly-by Looting ammunition-container complaints. One `[VAD] First scan: found 0 player stations` entry is an intentional Station Auto Drones diagnostic at game time 60.04, not an exception. No worker/navigation/payment failure from our jobs or explicit crash/access-violation/out-of-memory trace is identified. The file ends in save-header metadata parsing messages.

## Validation and existing-save acceptance

**387 Python contracts** pass, including nine new boundary cases. They execute the real registry conditions, recover an existing paid visit only after initialization, apply both station patch paths and reproduce the old 0.4.3 null-argument failure at a type-checked native-action boundary. Optional subscription tests cover all 19 expressions, existing subscriptions, eligibility and absent/already-fixed external code. Retained UI coverage is **91 Lua mocks**. Nine remaining XPath selectors across five native diff files match the pinned 9.00 reference and pass its diff grammar. Static source/archive audits and bundle checks are separate from X4 runtime execution.

The native contract comes from pinned 9.00 `common.xsd`/`finalisestations.xml`; condition ordering and same-save MD refresh are documented in the [Egosoft Mission Director Guide](https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/). No X4 executable, current save or merged installed catalogues are available here, so these new corrections remain runtime-unverified.

1. Exit X4, overwrite `extensions/vardath_galactic_occupations` from 0.4.4 and load the existing save. Keep Protected UI and Inventory Collector; companion mods need no update.
2. Verify no `RecoverVisitsV39 ... $Ships` initialization lookup. Leave any actual crew visit, paid/unpaid invoice, passenger booking and direct order in place; initialization must not recreate or clear them.
3. Let actual faction station construction/finalisation occur. Verify no null `wares` argument error; nonempty faction equipment still uses the same native list. Native missing-faction-equipment warnings are a separate limitation and may persist. Do not use a new-game requirement to work around an existing-save bug.
4. Where Auto Trade Subscriptions naturally executes, verify the 18 bare-faction lookup failures disappear and its own eligibility/existing-subscription checks remain effective. Already-complete third-party initialization is not reset for a second grant.
5. Continue an existing tour/crystal sale and compare real destination departure, balance increase, one vanilla ledger receipt and General notice. The new fix must not alter those already-working paths. Protected UI, existing orders, crew and Forge equipment should be retained.
