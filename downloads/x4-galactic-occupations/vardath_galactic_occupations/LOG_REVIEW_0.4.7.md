# Galactic Occupations 0.4.7 — crash investigation, hacker offices and signal results

## Crash evidence

Reviewed the complete supplied `debug(20261109-083003).log`: **6,659,541 bytes, 38,842 lines**, SHA-256 `bbf6560a418f4f8336770277ea6143cded75d446618c8867d1f6463b585426c5`. It identifies X4 **9.00 (611726)** and Occupations **0.46 / release 0.4.6**.

There are **2,178 error-tag occurrences**, but **no fatal error, exception, access-violation, out-of-memory or crash-stack record**. The final records at game age **27715.33** are a crystal miner resuming at its actual dock. Texture signature diagnostics shortly before that do not prove a corrupt texture or establish a crashing mod. A separate crash dump/stack would be needed to attribute the actual crash; it is not included in this upload.

One error explicitly names this suite: at **23729.18**, `AIDirector::Move()` reports a **possibly infinite wake request loop** in `vardath.go.worker` on entity `0x4c0a7`. It occurs immediately after the same ship's real 51,000 Cr sale, invoice 40, and completion record. The log continues for **3,986.15 game seconds** afterward, including subsequent sales by that worker, so this warning is **not proof of the later crash cause**.

Worker version 21 now yields for one game second at its iteration boundary and between the fast-return commercial/completion/deferred bookkeeping calls. New blocking actions declare `sinceversion="21"` for saved script import. The existing null-local guard remains first after the start label. Runtime 42, contracts, invoices and active passengers remain; no mass worker restart is introduced. These changes bound the fast-return path identified by the warning, without claiming a reproduced native-engine crash.

There are no spacesuit recovery requests in this log; the 0.4.6 recovery protocol is retained and is not runtime-verified by this session.

## Hacker: why only production appeared

Nine catalogue replies appear in the log, but no hacker behaviour startup is recorded. This file therefore does not verify a completed physical hack. The SCA Weapon Component Factory repeatedly reports one actual panel type. Communications Facility replies are unavailable; that alone does not demonstrate a bug because ownerless, player-owned, unlandable or unsupported targets are excluded.

The previous catalogue enumerated **only existing rooms**. Native `NPC_Instantiation.SecurityOffice` and `InfrastructureOffice` create security/engineering offices only at nearby attention. A remote station can therefore have its built-in production room while its other offices do not exist yet. Its partial catalogue was then cached for ten minutes.

The correction:

- Query the **installed native** `tag.security` and `tag.infrastructure` room definitions using the same deterministic seed rules as native NPC instantiation. Test each returned room macro's actual `hascontrolpanel` property. Existing rooms remain the preferred source. No panel type is invented from its name, and no room is created merely by browsing the menu.
- Invalidate older partial caches using catalogue version 47. Both autonomous selection and the existing single-station context command consume the updated catalogue. Eligible faction stations may offer a dynamic office even before a walkable office has been instantiated; actual docking compatibility and ownership checks remain.
- Only **after the hacker has actually docked**, prepare the selected missing compatible office using real native corridor/room definitions. Do not create every possible office at every station. Limit creation to one attempt per visit so missing geometry cannot create an interior loop. Clear output references before each native creation attempt, register only newly created interiors, send the native interior-created notification and refresh the actual room list.
- Actual room geometry, a real selected panel slot, native panel information/cost, physical crew movement, native effect verification and same-NPC return remain mandatory. A macro-supported choice is a preparation plan, not a claim that a live panel already exists or has been hacked. Missing assets, a refused creation, unavailable geometry or a failed panel call cannot count as success.
- Track only extension-created offices. Once no active visit needs one, release persistence. Never force-remove a room containing the player or an NPC; active visits retain their office. Ordinary native rooms are not owned or removed by this system. Offices may remain temporarily if occupied and are checked once per game minute.

The catalogue debug message now distinguishes **available panel types** from **instantiated panel types**. The UI itself is unchanged. The native macro definitions determine which panel choices are supported at each installation; the presence and successful operation of every panel is not asserted without an actual in-game test.

Primary reference: extracted native 9.00 `NPC_Instantiation.SecurityOffice` / `InfrastructureOffice`, `common.xsd` room commands and `scriptproperties.xml` macro/room properties, pinned at ArtByunex/x4-foundation-artbyunex commit `e3e8a345e5624db118bff3eb171b60b0993fcc2c`. These are reference files, not the user's merged installed catalogs.

## Scanner: accepted work, actual offers and contacts

The new log contains **13 scanner completions**, each reporting one signal-leak survey. The AI increments that count only after the Mission Director sets the actual work record's accepted flag. Thus accepted leak work is occurring. However, the previous implementation wrote its detailed survey results to the General logbook without corresponding debug telemetry. Their absence from this debug file is **not proof that no station bonus was applied**, and the old file cannot establish which native offers or markets became available.

The old market lookup used only the currently active `controlentity` at a station. The correction prefers the actual **assignedcontrolentity** and falls back to the visible actor, then the native **md.$ShadyGuyMap** NPC-to-station registry. This can identify an existing assigned market NPC whose visible room/body is absent off screen. It does not create a trader, assign a market to an arbitrary station or assume that every station contains one.

The existing native `GM_BringItems.Start` integration remains: its actual shady-guy `RewardObj` is unlocked by native code only after the required real item delivery. Native source explicitly supports this reward. Scanning does not accept/complete the job or directly set market access.

New observable results:

- `GO signal survey accepted v47`: actual accepted timed work, station, simulation/physical mode, exposed offer count and whether a native generation request was dispatched.
- `GO survey discount confirmed v47`: the actual native discount-added event, its amount and expiry. This is distinct from merely issuing a discount command. Native discount amounts are shares of a ware's price range, not a flat percentage of its entire price.
- Six game seconds after accepted work, `GO signal survey result v47` and the existing **General logbook** report the actual visible native offer count, actual market contact and whether its real delivery offer exists. The follow-up runs only for accepted work.

A generation request is **not** reported as a generated offer. Native faction exclusions, docking relations, tutorial/disabled checks, sector limits and the station's twenty-four-hour coupon/network cooldown remain. An eligible scan can correctly produce zero offers or no market contact. Offers can also subsequently expire under their native rules. Ordinary data/voice leak handling, native scan-publication caps, player orders and the no-fictional-mission-completion policy are unchanged.

Some component scan publications remain queued while `player.maxscanlevel` is -1 in the current player context. That existing native limitation does not prevent the separately accepted signal survey and its supported bonuses.

## Confirmed completed work and payment

| Work in the supplied log | Receipts | Observed credits |
|---|---:|---:|
| Finite-stock crystal sales | 174 | 10,978,000 Cr |
| Completed tours | 14 | 55,000,000 Cr |
| Trade-route patrol services | 4 | 32,000 Cr |
| Total | **192** | **66,010,000 Cr** |

All 192 recorded before/after balance differences match their paid amounts. Crystal ship/invoice pairs are unique. These results verify those particular recorded payments, not all occupation features. The ten-stop new tour default, accepted older itineraries, extra hour, passenger departure gates and all payment code remain unchanged in this release.

## Other errors reviewed

Counts are repeated log occurrences, not distinct root causes.

| Message | Occurrences | Finding |
|---|---:|---|
| Wrong invasion exit sector | 82 | Native FactionGoal_Hold_Space expected Hatikvah's Choice I but the exit led to Rhonkar's Clouds. This is inconsistent gate/path state; its source is not established. No gate rewiring or warning suppression is introduced. |
| Hyperion gate story | 3 | Missing WayHomeTable entry and Investigation_CorrectGate in Story_Hyperion. Native/story context is named, but the file does not establish the originating mod or a safe repair of the saved quest state. |
| Fly-by Looting ammo collection | 32 | md.fbl tries to collect incompatible Ammunition Containers on GRM-Kobayashi Maru. This is separate from essential Inventory Collector. Its installed source is not available for a reliable compatibility patch here. |
| Failed undocked cargo trade probes | 12 | Each correlates with Universal Cargo Teleport's explicit zero-transfer rejection/docking retry. These are handled native trade failures, not evidence of the game crash. No goods or money are fabricated; the existing fallback and source are unchanged. The numeric engine reason is not given an invented meaning. |
| Native trade buy/sell ware mismatch | 2 | order.trade.routine paired different wares; the log does not identify which extension caused the offer state. No unrelated native trade routine is replaced. |
| Missing Koha engines | 20 | No compatible merged loadout candidates. Requires the actual installed ship/faction catalog to repair correctly. |
| Missing ShipGenerator candidates | 81 | Includes loanshark plundererplunderer and fallensplit requests. Missing/invalid catalogs are not replaced with fabricated ships. |
| External patch selectors | 59 | Named patch files include Gramston Ships, Trader Seminars, Pirate Chaos Conflict, No Ship Limits, Pilot Training and NPC Economy Tweaks. Their exact installed targets/versions are required for repairs. |
| Save-header metadata queries | 816 | Truncated maxsize=0x1000 reads; these messages alone do not prove save corruption. |
| Stale mission/component UI queries | 24 / 56 | Missing IDs/objects without originating Lua stacks. Do not replace protected vanilla UI or guess the caller. |
| Native mission thread cleanup | 2 | MC_Management updates an already non-mission cue and signals a listener that no longer exists. No mission/thread state is fabricated or replayed. |
| Missing HQ manager / null pilot | 2 / 2 | ResearchBlueprintsMod and GT_Context_Academy named respectively. Their installed sources are needed for precise guards. |
| Native faction loadout / Yaki supply | 1 / 1 | Original PossibleWares list has no usable candidates; another NPC trade cannot be created. The old invalid explicit-null loadout override remains removed. Correct missing faction equipment data is not present here. |

One HeadHunter module import is explicitly blocked by Protected UI Mode; protection is preserved. The earlier repeated ware, character, text, plan and unsigned-file diagnostics also remain. The 0.4.6 native workforce empty-slot errors do **not** recur in this log. Script names and signature diagnostics alone are not proof of a crash culprit. No third-party mod is disabled, and Protected UI / Inventory Collector remain intact.

## Validation and installation

- **440 Python contracts pass**, including 25 new cases executing the shipped office/contact/scheduling paths with fault-injected native boundaries. They cover the logged production-only setup, absent definitions/corridors, refused creation, versioned cache recovery, real docking, existing-office reuse, player/ownerless stations, active/player/NPC occupancy, cleanup, assigned/visible/registry contacts and versioned positive worker yields.
- **91 unchanged Lua mocks pass**. No UI source changes. GitHub runs its Lua 5.1 syntax/mocks; local shared-library checks use Lua 5.4 with the existing unpack compatibility alias.
- Static XML/declared command signatures, ten native selectors across six diff files, source/archive identity and all seven extension audits pass. Companion source, Forge special weapon, ledger and spacesuit code remain unchanged.
- **Not run:** installed-game XSD validation, actual room rendering/pathing, every panel's native operation, out-of-sector panel APIs, save-load execution and crash reproduction. No X4 executable/save/merged installed catalogs are available here. Source mocks and green repository checks do not establish these native outcomes.

Close X4, replace only `extensions/vardath_galactic_occupations/` from the 0.4.7 archive and load the existing save. Keep Protected UI and Inventory Collector. Current orders, accepted passengers, crew, stock and invoices are preserved; there is no new-game requirement or mass worker restart.

## Existing-save acceptance

1. Reopen the previously production-only SCA factory's Hack Station submenu while unpaused. Confirm the partial catalogue refreshes and offers only actual existing panels or types supported by installed native office macros. Read the new available-versus-instantiated debug counts. Browsing must not create rooms or charge tools.
2. Choose each supported panel on separate visits. Use an AI-owned player ship with actual crew and tools. Confirm actual docking, selected missing office creation only when necessary, real panel probing, the SAME crew member walking to it, correct native tool/cash charge and verified station effect. Require its physical return and actual undocking. Do not equate a macro option or issued native call with successful hacking. Repeat near the player and out of sector; a refused geometry/API call must retain failure/waiting status rather than a claimed completion.
3. Cancel or interrupt a visit, change owners/docking permission, block the path, and remove needed assets in an isolated test copy. Preserve tools, crew, orders and failure recovery. Existing native rooms must not be removed. Complete a visit and wait a game minute: empty extension-created offices should be released. Keep the player or NPC inside and verify no forced removal. Save/load an active office visit and test the existing twenty-minute stranded-crew policy.
4. Assign the scanner to an eligible station outside its twenty-four-hour network cooldown. Verify an accepted fifteen-second physical/off-screen survey, the real native discount event and six-second General/debug result. A generation request with zero actual offers must say zero. Verify real visible offer entries in the vanilla mission interface and a genuine locked market contact's delivery offer where that NPC exists. Complete its actual delivery before expecting market access; ordinary stations without a market must not gain a fabricated NPC.
5. Resume the previously paid ADH-286 crystal miner. Verify the existing invoice is not paid again, another finite resource-backed batch sells, its actual ledger balance changes match, and rapid-wake warnings do not recur. Check direct-order interruption, save/load and all unchanged crew/passenger recovery rules.
6. Continue existing taxi/tour/patrol work, preserve accepted stop counts and confirm the same passenger departure/ledger gates. Newly assigned tours still default to ten stops. Retest all native panel and room states with the installed mod stack; the new paths are implemented and statically/mocked checked, **not yet verified in X4**.

If another crash occurs, retain the full new debug file and the game's accompanying crash dump/stack. This upload alone cannot establish which native module or mod crashed the process.
