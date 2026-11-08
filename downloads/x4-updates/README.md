# Current X4 update — delayed recovery, 8 November 2026

[Occupations 0.4.0](../x4-galactic-occupations/Galactic_Occupations_0.4.0_DEV.zip) · [Six-mod bundle](X4_Recovery_Grace_2026-11-08.zip) · [Policy and live checks](../x4-galactic-occupations/vardath_galactic_occupations/RECOVERY_POLICY_0.4.0.md)

| Extension | Version | This update |
|---|---|---|
| Galactic Occupations | 0.4.0 DEV | Same-crew recall after twenty game minutes away; unpaid cancellation grace; temporary-order protection; new twenty-stop tours. |
| Automatic Station Drones and Managers | 1.02 | Unchanged. |
| Living Factions Builders | 1.75 | Unchanged. |
| Kopis Forge / Astrid Tours | 1.15 | Unchanged, including special weapon and Astrid equipment. |
| Yaki Terran Habitats | 1.23 | Unchanged. |
| Universal Cargo Teleport | 1.01 | Unchanged. |

Exit X4 and extract in the game installation so files land in `extensions/`. Overwrite matching folders and load the existing save. Keep Protected UI and Inventory Collector. Timers use game time, survive save/load and preserve ordinary interruptions. Only actually removed persistent passenger services start unpaid grace; resuming before expiry keeps their party. 299 Python contracts, 78 Lua mocks and package checks pass; new native recalls and evacuations remain runtime-unverified.
