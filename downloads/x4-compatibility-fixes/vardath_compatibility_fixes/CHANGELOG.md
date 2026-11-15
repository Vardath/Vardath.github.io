# Version history

## 1.0.9 — 2026-11-15 — HeadHunter and CHC source-aware guards

- **HeadHunter (Workshop 2992233767):** Source-pinned `Speaky` cue at `start_script object="$FactionRep"` (error line 342) is called 158 times with a null representative in the supplied log. Wrap only that native `start_script` in `do_if value="@$FactionRep.isclass.npc"`; preserve its original script, line pool, delay, interactive flag and the bounty payout and tracking cues. Validator checks the patched file against the exact pinned Workshop source, and verifies the entire original `start_script` is unchanged inside the guard.
- **Crime Has Consequences (Workshop 3627879558):** 1.0.8's broad `set_value` XPath matches multiple identical expressions, causing X4 to skip the patch; 988 property-lookup errors remain. Select a safe optional lookup only within a named `ResolveObjectToShipStation` cue or library rather than all exact expressions in the script. Both variants are marked `silent` so unknown upstream structures are left unchanged rather than raising a startup error. The existing `do_if` optional commander lookup is retained. This patch cannot be proved against original source, only synthetic cue/library-context fixtures; the next X4 run must confirm the patch actually applied and the missing-object errors decreased.
- **Personal Envoy Auto (Workshop 3744204222):** All `$PilotActor` errors are gone in the new 195,038-line recording, consistent with the 1.0.8 exact-expression guard. No further Envoy changes.
- **Spectrum Super Ship (Workshop 3576089734):** 9,542 missing-macro records for `extensions/ccmod/assets/units/size_xl/macros/ccsupership_macro`. Its Steam Workshop page warns of incompatibility and broken blueprints in X4 8.0; user game uses 9.0. Do **not** substitute a dummy ship or delete serialized vessels in the player's live save. The user-supplied 35760889734 has one extra 8.
- **Other high-impact outside-source issues:** 19,654 missing empty character-model references, 677 `fs_destroyer` invalid meshsources, 213 insufficient UI table height warnings, 185 missing ShipGenerators, 267 stale mission-ID queries, and 13 research-menu onUpdate script exceptions. No ungrounded asset overrides.
- Archive contains all prior compatibility diffs. CI validation remains `partial` (native X4 runtime unavailable; 2 pinned GalaxyTrader source URLs missing; Envoy and CHC original XML unverified).



## 1.0.8 — 2026-11-14 — exact log-targeted guards

- **Personal Envoy Auto (Workshop 3744204222, v1.21):** X4 explicitly logs that Compatibility Fixes 1.0.7's absolute cue selector matched no node. Its original `EnsurePermanentCrew` still emits 5,319 missing `$PilotActor` errors in the new session, with the exact failing action `<do_if>` at line 409, expression `$CrewKept and $PilotActor and $PilotActor.exists`. The replacement diff targets the **exact original expression** anywhere in the MD script, with `$CrewKept and @$PilotActor.exists` so only an existing actor satisfies the branch. It no longer prepends a null actor or assumes a cue tree structure. It does not spawn, delete or reassign crew.
- **Kuertee Crime Has Consequences (Workshop 3627879558, v9.02):** `ResolveObjectToShipStation` dereferences `$kCHC_object == null` at line 515 and 522. Two precise attribute replacements use optional property lookups for the existing headquarters/commander expressions. Other crime, police, bounty, ship and faction logic is unchanged.
- **Significant unrelated problems in new log:** 25,483 missing empty character-model records, 835 missing `ccmod/assets/units/size_xl/macros/ccsupership_macro` references (3,338 related errors), 205 missing trade-ware-list selections, 406 invalid mission-ID query pairs. The `ccmod_spectrum_steamgg` Workshop mod needs its actual missing asset or correct original installation; creating a dummy capital ship is unsafe. No hidden fixes to these non-sourced issues.
- **Validation:** Exact expressions are taken from the attached 14 November debug log; the upstream original XML of Personal Envoy and Crime Has Consequences is unavailable. Synthetic fixture tests ensure exact-selector unique application, original action bodies preserved, and failure when the upstream target changes. The new overlays **cannot** be asserted to match the real Workshop XML until X4 run or original sources are available. CI records partial validation; earlier 11 source-covered diffs remain intact and two older GalaxyTrader pins remain unavailable.
- Existing save, ship orders, original crew, Protected UI, inventory-collector integration, and every other mod are unmodified.



## 1.0.7 — 2026-11-14 — provisional Personal Envoy Auto 1.21 guard

- **Personal Envoy Auto (Shpeck, Workshop 3744204222):** the supplied 14 November X4 log contains exactly 2,795 `md.Personal_Envoy_Full_Crew.EnsurePermanentCrew` missing-`$PilotActor` property errors. The extension is recorded as version 1.21. A cross-extension diff, under `extensions/personal_envoy_auto/md/personal_envoy_full_crew.xml`, prepends a single `do_if value="not $PilotActor?"` and initialises a missing `$PilotActor` to `null`. It does not override a pre-existing actor, replace the cue, spawn or destroy crew, move the ship, or change assignments. Optional dependency uses exact Workshop ID `ws_3744204222`.
- **Validation limitation:** the original Workshop `personal_envoy_full_crew.xml` could not be retrieved. This is an *experimental missing-variable guard*, tested against the X4 diff schema and a synthetic matching cue only; it is **NOT** verified against the actual upstream source or game. If the original script relies on a valid actor in following actions, additional errors may remain; no claim of fixed crew respawning.
- All previously source-confirmed compatibility diffs remain unchanged. Two older GalaxyTrader sources are also unavailable (HTTP 404), reported explicitly in CI as partial validation.
- Save-compatible metadata (`save="0"`); no UI/Lua replacement and no changes to Protected UI or Inventory Collector.



## 1.0.6 — 2026-11-14

- **Kuertee Emergent Missions:** prevent the repeat `Bounties_UpdateLastKnown` error flood caused by computer-class pilot objects and bounty history tables absent in older saved records. The original location-update calculation now runs only for operational NPC pilots with a valid ship/sector and faction. Initialise only missing per-pilot and per-faction location containers; never overwrite existing entries.
- Source-grounded in the pinned v9.02 Workshop cue structure; static validation must confirm every XPath uniquely and the unchanged remainder of the Kuertee bounty logic. No extra bounties, reward replay, UI changes, forced orders or new game.
- This does not repair broken ship generators, Koha engines, XR models, malformed third-party wares, or oversized UI tables.


## 1.0.5 — 2026-11-13

- **Fly-by Looting:** stop calling `collect_drop` for ammunition containers on M, L and XL ships. The November 13 log shows hundreds of native rejections by the M-class Verdandi despite its reported missile-storage capacity. S-class ammo collection and all ordinary loot are retained.
- **Kuertee Emergent Missions — bounties:** guard the two native bounty registration calls when the attacker has no valid NPC pilot. Normal pilot kills and bounty statistics use the untouched original libraries.
- **Kuertee Emergent Missions — patrol/raid/rescue:** fix a target scorer referencing `$nearestTo` outside its scope by measuring distance from the current NPC defender. Guard target debug, player target selection, target notification and NPC attack calls when the filtered enemy list is empty.
- Exact installed v9.02 Workshop XML files pinned by SHA256 and catalog checksum; modified XML is validated against those references. All unrelated mission rewards, crew, ship ownership, trading logic and player controls are unchanged.
- **Not addressed:** XR ShipPack corrupt collision mesh, third-party invalid crafting resources, absent ship generator/loadouts, stale external mission IDs, and save-preview header truncation. Those cannot be safely fixed without the relevant source assets or a confirmed offending caller.
- No new game required. Protected UI remains enabled. All source/CI results are static; live X4 testing remains necessary.


## 1.0.1 — 2026-11-10

- Stable native cleanup work list/private counter for immediate callback mutation.
- Guarded Inventory Collector debug default, HeadHunter absent-pilot expiry and late Emergent Missions rescue cleanup.
- Nine diffs, 29 unique operations, thirteen pinned references and fifteen source/fault contracts; no reward replay or UI protection changes.

## 1.0.0 — 2026-11-09

- Added six narrowly scoped XML compatibility patches for errors in the 083003 debug log.
- Preserved native trade retry delays, mission cleanup/rewards, saved invasion descriptors and incompatible loot drops.
- Added optional dependencies for the observed Fly-by Looting, GalaxyTrader MK3 and Research Blueprints versions.
- Added checksum-pinned source application, native diff grammar checks, nine failure-boundary contracts, deterministic packaging and a dedicated GitHub workflow.
- No new game, UI replacement or changes to existing suite extension files. Runtime validation remains outstanding.
