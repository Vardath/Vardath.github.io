# Compatibility and independent-mod release — 16 November 2026

Installed 32 changed files across 15 extensions after backing up the originals. These comprise stale-patch repairs in ten third-party mods, independent releases of Kopis/Hyperion/Living Factions, and publication metadata for the earlier local Compatibility Fixes and Galactic Occupations repairs.

## Compatibility repairs

| Mod | Change |
|---|---|
| Civilian Economy + Living Factions | Preserve CE hub exclusions and player construction requests in either load order. |
| Pilot Training | Preserve Escape Teleport's player-ship exclusions while adding the training-pair exception. |
| JP Another Explorer / Spiral Explorer | Hook the current assist script; retain order parameters for commander promotion. |
| Trader Seminars | Replace current seminar baskets and old individual entries with exactly ten seminar entries per supported trader. |
| No Ship Limits | Remove Erlking research gates separately from native and Station Build Turbo recipes. |
| Sober's Time Unleashed | Add research strings to one page when multiple matching pages exist. |
| Gramston Ships | Keep additions to existing groups; skip absent optional faction groups. No substitute faction group was invented. |
| Reputations and Professions | Keep the native police hook; make the absent optional KUDA hook non-failing. |
| Rescue Rangers | Skip its native fleet hook when Player Restock deliberately removes that entire native handler. This does not restore the deleted native rebuild system or make these two mods' competing fleet systems equivalent. |

## Independence

All twelve installed Steph/Vardath-authored extensions were checked. No required or optional dependency on another Vardath extension remains in their manifests. A source scan found no cross-mod Vardath symbol or asset-path references after the changes.

Kopis 1.17 removes an unused hard dependency. Hyperion 1.0.4 retires its cross-extension payroll patch. Living Factions 1.79 discovers L/XL builders directly and retains the same genuine-assignment, station-owner, time and payment checks. Its native income adapter and receipt consumer are bundled locally, as are Galactic Occupations' copies; either mod can supply them independently.

This does not remove genuine Egosoft DLC requirements or third-party framework/target requirements. Faction Camouflage still requires Mod Support APIs. The XR no-VRO fix still requires XR ShipPack and is only appropriate with VRO disabled. Optional compatibility targets remain optional. Other authors' mods have not had their framework dependencies stripped.

## Validation and limits

- 23 patch-application scenarios passed, including CE/Living Factions in both orders, each alone, Pilot Training with and without Escape Teleport, repeated seminar application, and the native fleet hook present/removed.
- All changed XML parses; schema comparison found no newly introduced issues. The original files contain some existing schema warnings.
- Active numbered archives were rebuilt and checked; unrelated members were retained. All 32 installed files passed SHA-256 verification.
- All twelve current release ZIPs were checked byte-for-byte against the installed files. GitHub source paths retain existing case where necessary.
- These are static and file-level checks. A fresh X4 session/log is required for runtime confirmation. No save files were edited.

The prior log's mining-station collision mesh warnings, unspecified UI/mission-ID errors and remaining faction-generation errors are outside these stale-selector repairs; they are not claimed fixed here.

## Current releases

| Extension | Content version | Download |
|---|---:|---|
| Terran and Pioneer Short Skirts | 130 | [Current ZIP](../x4-terran-pioneer-short-skirts/terran_pioneer_short_skirts_latest.zip) |
| Vardath Compatibility Fixes | 111 | [Current ZIP](../x4-compatibility-fixes/vardath_compatibility_fixes_latest.zip) |
| Vardath - Faction Camouflage for All Player Ships | 102 | [Current ZIP](../x4-faction-camouflage/vardath_faction_camouflage_latest.zip) |
| Vardath - Player Faction Invincible | 103 | [Current ZIP](../x4-faction-invincible/vardath_faction_invincible_latest.zip) |
| Galactic Occupations | 57 | [Current ZIP](../x4-galactic-occupations/vardath_galactic_occupations_latest.zip) |
| Vardath - Hyperion Ascendant | 104 | [Current ZIP](../x4-hyperion-ascendant/vardath_hyperion_ascendant_latest.zip) |
| Vardath - Kopis Production Cheat | 117 | [Current ZIP](../x4-kopis-production-cheat/vardath_kopis_production_cheat_latest.zip) |
| Vardath - Living Factions and Builders | 179 | [Current ZIP](../x4-living-factions-builders/vardath_living_factions_builders_latest.zip) |
| Vardath - Automatic Station Drones and Managers | 103 | [Current ZIP](../x4-station-auto-drones/vardath_station_auto_drones_latest.zip) |
| Vardath - Universal Cargo Teleportation | 101 | [Current ZIP](../x4-universal-cargo-teleport/vardath_universal_cargo_teleport_latest.zip) |
| Vardath - XR ShipPack without VRO Fix | 100 | [Current ZIP](../x4-xr-no-vro-fix/vardath_xr_no_vro_fix_latest.zip) |
| Vardath - Yaki Terran Habitats | 123 | [Current ZIP](../x4-yaki-terran-habs/vardath_yaki_terran_habs_latest.zip) |

Content versions are the integer values used by X4 (for example 117 denotes Kopis 1.17). Historical ZIPs remain available but are not the current downloads.
