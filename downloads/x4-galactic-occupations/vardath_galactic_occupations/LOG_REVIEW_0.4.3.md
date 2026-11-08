# Supplied-log review and native mission-offer correction — 0.4.3

## Reviewed evidence

`debug(20261108-122227).log`, uploaded 8 November 2026: 7,373,974 bytes, 47,137 lines, SHA-256 `54cefc4d84252ae6489f09d307cd78fd346d59be7924a490fd19da3905ec068c`. Loaded Occupations **0.42**, Kopis/Astrid **1.16**, Builders **1.75**. Script events span game times 6918.00–17365.57 (about 2 hours 54 minutes of recorded game time). New completions below are counted from explicit events, not repeatedly summed lifetime activity snapshots.

| Occupation | New events recorded in this log | Observed payment |
|---|---|---:|
| Autonomous Crystal Miner | 57 completed stock-backed off-screen sales | 3,901,000 Cr |
| Galactic Taxi Service | 2 completed deliveries, each reported as ten delivered passengers | 160,000 Cr |
| Galactic Escort Service | 1 completed escort | 12,000 Cr |
| Trade Route Patrol | 8 completed protection assignments | 64,000 Cr |
| Fleet Morale Booster | 9 completed services; 40 individual crew morale values improved | No wage expected |
| Station, Component and Signal Scanner | 10 completed station visits; 80 component samples queued; each completion reports a signal-leak survey | No wage expected |
| Galactic Sightseeing Tour | LMF-454 reaches 17/20 sights with 2 passengers; PAF-887 reaches 16/20 with 10; IOS-561 reaches 6/20 with 10 | No completed-tour fare in this log |
| Hostile Lure and Interception | Travel/search active; zero completed lures; visible-attention weapon limitation is reported | Not verified |
| Wormhole and Anomaly Mapper | No new completion event here | Not verified |
| Asteroid Demolition | No new completion event here | Not verified |
| Traffic Control and Cargo Inspection | No new completion event here | Not verified |
| Emergency Ship Recruitment | No new completion event here | Not verified |
| Galactic Station Hacker | 3 real panel-catalogue replies return ready with one actual panel type | No completed crew hack here |

**68 recorded payments total 4,137,000 Cr.** Each logged `balance_after - balance_before` matches the actual paid amount. There are no repeated recorded ship/invoice, ship/contract or ship/job/serial payment IDs. Values are converted from native hundredths of a credit. This demonstrates the logged cash changes; a text log cannot show the contents of an open vanilla transaction-ledger window or prove other unlogged payments. No new payment implementation is introduced.

Taxi has nineteen explicit per-person departure messages across the two completed contracts; the first lacks a separate passenger-9 departure message, while both full-party completion/payment gates report ten. The log verifies the two fares and many physical departures, not twenty separately observed walking animations. Do not treat that missing diagnostic line alone as proof of either a stranded or a duplicated passenger.

AKD-700 now travels under Scanner, completes two Taxi jobs, changes to Escort and then Crystal Miner, and reaches multiple sectors. Its former global ashore-crew movement lock is not reproduced. There is no explicit twenty-minute recall event in this session, so the recall itself remains unverified by this log.

Visible crystal work also selects six turrets and destroys two actual Bandannite deposits (hull 500 to 0, destruction events confirmed). Another Menelaene attempt deals no logged hull damage. AKD-700's harvest/sale counters remain at the earlier seven items: **new physical drop collection and a subsequent physical counter sale are not established here**. The 57 new paid sales are the explicitly labelled off-screen resource/stock-backed system, not proof of visible turret/drop collection.

The scanner now physically travels and retains real close-range samples while the current player scan cap is -1. Eighty queue registrations are recorded; native publication must still wait for an available native scanner context. This is not a claim that all eighty native scan levels were already applied. A native-publication logbook notice is separate from debug output.

## The suite error found and corrected

Ten error-tagged entries belong explicitly to this suite: five scanner mission-generation requests each produce a failed `md.GenericMissions.Manager.SelectMission` property lookup and a null-cue error. Times: 10666.25, 11287.34, 14515.15, 16143.22 and 17315.59. Station coupons and the rest of the survey are separate actions; this failure concerns the request for a new native mission offer.

Native 9.00 `GenericMissions` declares `SelectMission` as an event-signalled cue taking a table with `$Sector` and `$OfferObject`. It is nested under Manager in XML, but MD cue identifiers are script-wide: the external reference is **`md.GenericMissions.SelectMission`**. Manager variable access, such as `md.GenericMissions.Manager.$MissionCues`, remains valid. References: [pinned native GenericMissions](https://github.com/ArtByunex/x4-foundation-artbyunex/blob/e3e8a345e5624db118bff3eb171b60b0993fcc2c/md/genericmissions.xml), [Egosoft Mission Director Guide](https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/).

0.4.3 resolves the correct cue with an optional lookup, checks that it exists and signals the real station/sector payload only if the existing native exclusions, docking permissions, sector limit and station cooldown also permit it. An unavailable native cue does not block the other earned station benefits, and the request flag stays false. It does not auto-accept missions or invent a mission completion/reward.

Only `VGO_Survey.xml` gameplay logic changes, plus extension version metadata. AI/navigation, bookings, payments, crew recovery, turrets and UI sources are byte-identical to 0.4.2. The native MD action refresh applies on loading the same save. There is no worker-version bump or mass order restart.

The validator now checks literal GenericMissions cue names against 44 identifiers from that pinned source, distinguishing cue identifiers from Manager blackboard variables. Eight new tests execute correct request dispatch, payload, missing cue, disabled generation and cooldown boundaries, and reject the exact previously failing identifier. **378 Python contracts pass.** Retained UI tests cover 91 mocked checks; actual native mission creation after this fix is not yet run in X4 here.

## Other log messages

The 3,371 error-tagged entries include normal mod startup diagnostics as well as real faults. They should not all be interpreted as crashes or Occupations failures. Notable groups:

| Group | Entries | Attribution/limit |
|---|---:|---|
| Missing character model | 819 | New versus the preceding two supplied logs. Model name is blank, so the responsible character asset/mod cannot be established here. |
| Missing character mesh | 39 | Native rendering errors; no suite script is named. |
| CHC null-object lookups | 400 | `md.kuertee_chc.ResolveObjectToShipStation`, reading `trueowner` and `toplevelcommander` on null. |
| Stale mission UI IDs | 320 | Native UI queries an unavailable mission/offer. The log does not identify the owner of every stale ID. |
| UI widget capacity | 148 | Native fifty-slider limit reached. No Occupations UI layout changes are made. |
| Save-header XML parsing at a 4 KiB read limit | 170 | `maxsize=0x1000` metadata reads; not evidence by itself that a complete save is corrupt. |
| Terran frigate job generation | 60 | Invalid/missing military-frigate generation for `terran_frigate_patrol_l`. |
| Patch selector failures | 67 | Includes VRO/other installed patches. No new suite patch failure is identified. |
| Undefined sound IDs | 74 | Mostly the Argon small launch-tube sound reference. |
| Ammunition-container collection | 2 | `md.fbl.fbl_cue` tries a container Astrid Tours cannot collect. This is not a crystal deposit or our crystal-sale script. |

These external/unattributed errors are recorded rather than patched speculatively into the working suite. No explicit crash/access-violation or out-of-memory trace is present; the file ends with save-header parsing messages. No Builders/Kopis/Yaki/Drones/Cargo Teleport script error is explicitly named by the new error blocks. That does not establish complete runtime coverage of those mods.

## Install and live check

1. Exit X4 and overwrite `extensions/vardath_galactic_occupations` from the 0.4.3 ZIP. Load the existing save. Keep Protected UI and Inventory Collector; companion mods need no update.
2. Let a scanner complete a signal survey at an eligible non-player station whose existing twenty-four-game-hour station cooldown has expired. Earlier surveys keep their earned coupon/cooldown; they are not replayed for extra benefits by this patch.
3. Confirm the new log contains no `Manager.SelectMission` lookup or null-cue error. The native request must use the actual station/sector and respect the sector mission cap. Native mission generation remains probabilistic and may legitimately offer nothing; neither an instant mission nor acceptance/payment is guaranteed.
4. Existing taxi/tour bookings, crystal invoices/stock, direct orders and crew-return clocks must continue. New tours still require twenty actual booked stops and destination departure before their luxury fare; the ongoing 17/20 tour is not already a completed fare.

Static checks, mock execution, native reference comparison, source/archive audits and GitHub CI are distinct from running this correction inside the installed X4 game. The reviewed log predates 0.4.3.
