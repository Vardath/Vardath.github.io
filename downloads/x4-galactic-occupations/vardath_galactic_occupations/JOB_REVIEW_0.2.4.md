# Job activity and debug(5) review — 0.2.4

## What the supplied game log establishes

The 7 November 2026 log contains 51,088 lines and identifies Galactic Occupations version 0.23 (extension manifest 23, development release 0.2.3). It contains **49 direct occupation script errors on five captain entities**, plus **222 consequent native move.generic errors** on four of those entities:

| Evidence | Count | Interpretation |
|---|---:|---|
| `vardath.go.approach`: `get_safe_pos sector="$target.sector"` received null | 37 | A still-existing target did not have a sector when approached. The same null destination then reached native movement. These are failed movement attempts, even if the default behaviour remained selected. |
| `move.generic`: six event sources received that null `$destination` | 222 | Six secondary errors for each failed approach. These are consequences of the shared approach defect. |
| `vardath.go.find`: `$candidate.sector.owner` with null sector | 11 | Candidate discovery treated existence as proof of a usable location. |
| `vardath.go.find`: `$candidate.iscapturable` on an XEN F in wreck state | 1 | Recruitment inspected capture-specific data before rejecting the wreck. |

The property documentation and native scripts expose sector context, operational state, wreck state and pilot existence separately. A sector-less reference is not proof an object was destroyed; transit is one possible cause. The log does not identify the target or occupation for each shared approach failure. It is therefore incorrect to assign all four movement-failing captains to particular jobs from this log alone.

The older occupation cargo `.illegalto...count` error and the Yaki construction-plan materialisation errors are absent in this log. This supports that those error paths did not recur during the supplied session; it does not prove every gameplay outcome.

**This debug file is not an export of the player's Logbook or transaction ledger.** It contains no explicit GO completion/payment diagnostics. Optional detailed diagnostics default to zero, and completion debug output was conditional. Consequently the file cannot establish how many other tasks completed, how much they earned, or whether every apparent movement produced its intended effect. User-observed tour Logbook activity is separate evidence. There is no attached save from which to inspect stored receipts or job state.

## Implemented corrections

- The shared approach script undocks, resolves a valid target sector, waits up to approximately one minute for a transient context, and returns an incomplete attempt if none appears. It passes the captured valid sector to both `get_safe_pos` and `move.generic`; no null sector is knowingly passed to native movement. The worker also waits if its own ship has no sector at startup. Normal orders and player piloting retain priority.
- Discovery rejects sector-less candidates before looking at territory ownership. Live services reject non-operational objects before reading capture/pilot data. Recruitment rechecks operational state and pilot existence after its communication delay. Tour sightseeing still permits an actual located derelict; its catalogue excludes sector-less entries and is refreshed on upgrade.
- Every assigned occupation writes an observational activity summary to **vanilla General Logbook**, and the same summary to the debug log. It is first eligible on the next 30-second reporting pass, then is throttled per ship to roughly five minutes plus staggering. It reports ship, job, status, sector, target, destination, task cycles started, completed assignments, actual recorded income, latest completed result and latest unfinished-cycle reason where applicable. It scans only the registered occupation ships.
- Completed tasks receive detailed result text and a separate completion entry. The worker increments completion only after a task returns success, with a persistent per-job assignment-serial guard. A tour stop is route progress, not a completed tour. An incomplete attempt is not a successful assignment. Counters start with 0.2.4 and are not fabricated from old activity.
- The activity and result reporters do not reward, transfer money, scan objects, improve crew, create passengers or transfer ownership. Income counters observe the same already-paid positive amount that enters the existing paid journal. Native ledger/payment receipt integration and Protected UI are unchanged.
- Scanner attempts stop checking the rest of an unloaded station after establishing that module collision geometry is unavailable. They retain that waiting reason instead of reporting a zero-component completion. Actual surface/line-of-sight and before/after scan checks remain mandatory.
- Physical demolition distinguishes a scoped native destruction event or a surviving zero-hull target from mere reference disappearance. Crystal completion still requires a real increase in captain inventory after collecting attributed drop objects. New waiting/failure messages explain no weapon range, no damage, unconfirmed crystal collection, no eligible morale improvement, declined recruitment or absent hostile pursuit.

## All twelve occupations

| Job | Completion evidence now recorded | Remaining runtime verification |
|---|---|---|
| Escort | Real trader arrival plus duration/proximity samples; trader and destination named. | Cross-sector following, transit wait, combat/resumption and one service payment. |
| Taxi | Number of original accepted NPCs actually disembarked at the destination. | Full boarding, departure, drop-off, single fare and partial-unloading reload. |
| Component scanner | Number of components with observed scan changes and station discovery before/after. | Loaded-scene scan effects and visible reporting of unavailable OOS geometry. |
| Connection mapper | Actual anomaly destination-set count, or identified gate/accelerator survey. | Transit safety, destination data and optional traversal. |
| Luxury tour | Delivered passengers, distinct visited sites and sectors; intermediate sights remain separate progress. | Full itinerary, same-actor drop-off and single booked fare. |
| Crystal miner | Captain inventory increase from actual attributed crystal drops; sales recorded separately. | Real deposits, turret hits, drop attribution/collection and broker sale. No OOS harvest is claimed. |
| Hostile lure | Observed pursuit and actual arrival near friendly defences. | Enemy behaviour, survival and useful interception. |
| Asteroid demolition | Scoped destruction event or confirmed zero hull, instead of disappearance alone. | Actual asteroid destruction with suitable weapons/arcs; OOS destruction remains unavailable. |
| Morale booster | Count of crew morale values actually increased. | Native crew changes and eligible faction reputation; maxed crews produce no completion/reputation. |
| Cargo inspection | Target, jurisdiction and true/false contraband result after the inspection checks. | Legal and illegal cargo cases, reporting and real jurisdiction behaviour. |
| Emergency recruitment | Confirmed ownership transfer, named existing hull and remaining hull percentage. | Wreck/bail races, probability, protected exclusions, equipment and crew preservation. |
| Trade route patrol | Trader route arrival and close-range samples; temporary defensive orders remain separate. | Corridor coverage, transit waits, combat/resumption and repeated assignments. |

These are executable observation/reporting changes, not new proof that the listed native effects ran successfully. No X4 executable, matching installed catalogs or save is available in the development environment. The new release has not been run in X4 here.

## Other log findings

There are unrelated third-party errors, including GGSS Emperor using integer literals where native money values are required, missing ship generators/macros, Kuertee object lookups and native UI/widget errors. Auto Drones' seven `[=ERROR=]`-labelled messages in this file are its own diagnostic messages reporting successful scans with `errors=0`, rather than seven failed scans. No other repository-mod script error was identified in this supplied log.

The construction generator also reports a player station with 1,284 functional modules and failed connections. That is concrete evidence of a very large, difficult construction plan; the log does not establish which mod created it or prove a crash cause. No existing station is removed or rewritten to suppress the message. Partial save-header preview parse messages containing `maxsize=0x1000` do not establish save corruption.

Only Galactic Occupations source changes in this repair. Forge/Astrid equipment, builders, Yaki habitats, other repository mods, Inventory Collector and installed third-party extensions are not edited.

## Validation and reproducing gameplay checks

Static XML/API/reference checks, 35 source constraints and all-seven-mod archive/reference checks are run separately from gameplay tests. Lua is unchanged; the existing mocked Lua checks and supported-interpreter syntax checks run in CI. Full installed-game schema and runtime checks remain unavailable. See `TESTING.md` for the complete occupation matrix.

1. Fully exit X4, replace the Occupations extension, restart and load the existing save. Keep Protected UI enabled. Look for `Galactic Occupations 0.2.4 loaded` in General Logbook. Manifests, itinerary progress, crew/equipment, reservations and native default orders are retained; reselect any behaviour already lost to Hold Position in an earlier build.
2. Leave at least one eligible ship assigned to each job. Within the next reporting pass, expect its first `Galactic Occupations: activity - <job>` entry; allow up to a minute for registration. Later reports arrive roughly every five to six game minutes. Clear Logbook search/category filters. Search the debug log for `GO activity:` and `GO completed:` without enabling extra diagnostics.
3. Treat status/target/destination as evidence of activity only. Match an increment in completed assignments with the reported real effect: station scan info, crew skill, ownership, destroyed asteroid, attributed collected crystals, passenger manifest or trader arrival. Jobs without a legitimate cash fee can complete without a payment. Match paid receipts and native transactions separately; reported income is gross received, not profit after expenses.
4. Follow a trader through a super-highway or other transition while escort/patrol is active. A temporary missing target sector must produce waiting/deferred status, no null-destination errors and no artificial completion. Give a direct move order during the wait; it must take priority and the default must resume afterwards.
5. Damage a valid hostile below 25% hull, then have it destroyed or its pilot bail during a recruitment attempt. It must be rejected without a capturable-wreck/pilot property error and without a false ownership/result entry.
6. Compare the scanner with the target scene loaded and unloaded. Loaded work must change real component scan information; unloaded geometry must explain the wait promptly and must not count a scan. Test crystal/demolition weapons near the player separately from their documented OOS limitation.
7. Complete actual taxi and luxury-tour contracts. Check all accepted NPCs leave at the proper station before completed-assignment/fare counts increase. Save/load mid-journey and during partial unloading; there must be no duplicated fare or passenger recreation.
