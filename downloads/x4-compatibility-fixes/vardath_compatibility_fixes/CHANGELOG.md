# Version history

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
