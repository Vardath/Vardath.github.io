# Implementation and compatibility review

Reviewed 7 November 2026 against the repository source and publicly available X4 script/interface references. No X4 runtime was available.

The active changes are Galactic Occupations 0.2.1, Builders 1.74, and Kopis 1.14. The other four extensions were inspected and passed their available checks; they are not unnecessarily changed or included in the update bundle.

| Area | Result and limit |
|---|---|
| Galaxy scope | All twelve orders call the shared worker. Range 99 selects the complete connected/access-granted native sector graph; work rotation prevents local targets pinning a ship in one sector. A ship outside a restricted home range returns into scope before selecting new local work. |
| Passenger authenticity/capacity | Up to ten NPC actors, native non-forced passenger templates, real dock placement, vanilla `npc_move_to`, and per-actor ship-context acknowledgments. The ship remains docked until every accepted NPC boards. No template-only boarding fallback. |
| Taxi/tour persistence | Shared boarding/delivery scripts retain manifests, partial progress and contract IDs. Old single-passenger state is adopted. Saved direct orders retain native priority. Runtime migration and interrupted NPC pathfinding remain unverified. |
| Luxury tour outcome | Ten distinct sites and up to three sectors where available, recorded separately per trip, followed by docking and passenger delivery. Booked ticket price persists. Default maximum: ten passengers × 500,000 Cr = 5,000,000 Cr. |
| Scanner | Removed the normal-AI/player scanner-level mismatch rejection. Enumerates all modules/defence elements without the old eighty-module cut-off, approaches actual surfaces, retries blocked views, requires sustained LOS and checks native scan-data changes before success. Still needs loaded physics and in-game confirmation. |
| Turrets | Existing-ship S/M Loadout/outfitter choices add a virtual Mine Crystals option. Native choices delegate to original callbacks; the virtual ID never enters an engine mode setter or upgrade plan. Independent direct control targets actual deposits; existing equipment/modes/armed settings are not rewritten. Actual arcs, hits, drop handling and Protected UI behavior remain unverified. |
| Vanilla ledger | Removed all custom income UI and renderer/search/paging overrides. Optional published UIX callback changes only the description/label of real native payment IDs; amounts, IDs, graph and totals remain native. No synthetic receipt rows. Ambiguous or condensed history remains vanilla. Lifetime job totals are included as descriptive text. New detailed payment receipts also use the ordinary Logbook. Protected UI remains enabled; actual callback availability still needs verification. |
| Builder billing | Existing 200,000 Cr hire, 100,000 Cr/hour active and 25,000 Cr/hour standby rates, minute settlement, explicit numeric casts and SETA elapsed-time accounting retained. Labels record observed actual credits and stored ship/station names. No retroactive invented receipts. |
| Astrid Tours | Original dedicated clone/equipment retained. Its previous 16 berths plus 90% crew fill left almost no passenger room. The clone now has 32 berths and new spawns use 50% fill. Existing crew are not removed. Other Astrids and the Forge special weapon/recovery files are preserved. |
| Invincibility interaction | The occupation capture transfers existing damaged ships. The separate Invincibility extension intentionally restores player assets on its later sweep; this is its requested behavior, not a permanent hull-preservation guarantee after capture. |
| Inventory Collector | Kept compatible by using actual drop objects/native collection and no timer-generated crystals. External collection may take a drop first; no duplicate payout is inferred from disappearance. Pilot-inventory brokerage only sells actual items present. Test with the installed collector in game. |
| Yaki Habitats | Reviewed its three Terran-derived habitat copies, macro/index links, workforce selection and nonduplicating wharf construction checks. No new change was justified by the available evidence. |
| Station Auto Drones | Reviewed manager eligibility, one-roster Lua bridge, acknowledgment diagnostics and supply-order code. API/XML/archive checks pass. Its engine/Protected UI behavior still requires runtime testing. |
| Universal Cargo Teleport | Both native AI patches and all five available-reference selectors checked. Native trade accounting remains responsible for wares/payment. No new change justified. |
| XPath compatibility | The two Builders economy selectors do not match the older 8.00 snapshot; both match the published 9.00 source at ArtByunex commit e3e8a345e5624db118bff3eb171b60b0993fcc2c. They are retained rather than changed to an older layout. Other resolvable source selectors matched the available snapshot. Effective installed/DLC/mod-merged XPath resolution remains unverified. |

Native reference sources include the [script snapshot](https://github.com/loewenherz-projekt/X4-Scripts/tree/c45e48e77e5e9fe195d24ffe8935dbea7ad864a2), [published 9.00 economy script](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/md/factionlogic_economy.xml), and [schema-derived interface metadata](https://github.com/chemodun/chemodun.github.io/tree/main/src/commands/data). No full reference-game files or third-party mod source are redistributed.

All twelve occupations still require in-game acceptance of menu assignment, target selection, action/effect, completion, repetition, target loss, interruptions and save/load. Full matching installed-game XSD and expression execution were not available. Static/Lua contract success does not establish a playable release.

The published native 9.00 helper and the actual UIX payment-entry callback were inspected directly. The income fix no longer depends on frame, table or column layout. Thirty-one mocked Lua checks cover data-only receipt labeling and the separate turret controls. The supplied debug(2).log proves the earlier failure causes; post-fix in-game verification is still pending.

Runtime repair evidence: direct ship/turret/component blackboards are unsupported; only entity blackboards expose `$variable`. Shared occupation state is now in per-object tables on `player.entity`, so it survives captain changes and uses supported writable values. Crystal drops are captured by the task's exact object event; passenger room events bind to a live group. Recovery edits only the current editable occupation default order's home parameter to its existing value. Direct-order execution takes precedence. The Astrid occupied-ship null guard is the sole Kopis script change in this repair.

## debug(3).log follow-up

The current recovery bundle supersedes the three-mod 0.2.1/1.74/1.14 bundle and adds Yaki Habitats 1.22. It addresses the log's safe-location, presence-expression, optional passenger/police, saved-stack and constructionsequence faults. Explicit default retries and shared-cursor native Logbook receipts address the reported Hold Position/missing-receipt symptoms without simulating successful work or re-paying old records. Crystal harvesting remains UNVERIFIED because the reported session failed at startup. The log does not prove a crash cause. Existing modules are preserved.

## 0.2.3 / debug(4).log

The current bundle updates Occupations and Yaki Habitats; Builders/Kopis are included unchanged. The log's explicit errors are cargo boolean misuse, construction pseudo-entry materialisation and an undefined order icon. Native 9.00 script inspection additionally established the absent undock step and same-faction fleet escort side effects. Full details and per-job evidence gaps are in `JOB_REVIEW_0.2.3.md`. The user has verified real boarding; complete taxi/tour unloading, repaired patrol and physical crystal harvesting still require runtime tests. Existing saved passengers, station modules and Forge weapon files are retained.


## debug(5) and 0.2.4 follow-up

The supplied 0.2.3 log contains 49 direct occupation errors and 222 secondary native movement errors. Shared sector resolution, live-service filtering and post-wait recruitment guards are repaired. New saved per-ship/job diagnostics report status, targets, completed effects and observed positive income in vanilla General Logbook and debug output. No new UI or periodic reward is introduced. Scanner unloaded geometry and physical destruction/collection evidence are handled explicitly. Only Occupations source changed. See its `JOB_REVIEW_0.2.4.md` for exact evidence, all twelve jobs and reproducible runtime tests. No new X4 runtime acceptance test was possible here.
