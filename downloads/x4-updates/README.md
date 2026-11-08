# Current X4 update — crew and order recovery, 8 November 2026

[Occupations 0.4.2](../x4-galactic-occupations/Galactic_Occupations_0.4.2_DEV.zip) · [Six-mod bundle](X4_Crew_Order_Recovery_2026-11-08.zip) · [Findings and live checks](../x4-galactic-occupations/vardath_galactic_occupations/CREW_ORDER_RECOVERY_0.4.2.md)

| Extension | Version | This update |
|---|---|---|
| Galactic Occupations | 0.4.2 DEV | Fixes the ashore-crew movement lock across roles, background status/timeout ownership and the missed scanner worker gate; queues real samples for native scan publication. |
| Kopis Forge / Astrid Tours | 1.16 | Source unchanged. |
| Automatic Station Drones and Managers | 1.02 | Source unchanged. |
| Living Factions Builders | 1.75 | Source unchanged. |
| Yaki Terran Habitats | 1.23 | Source unchanged. |
| Universal Cargo Teleport | 1.01 | Source unchanged. |

Exit X4, extract so files land in `extensions/`, overwrite matching folders and load the existing save. Keep Protected UI and Inventory Collector. No new game. Only Occupations needs updating for this fix. All earlier recovery changes remain included. 370 Python contracts, 91 Lua mocks and source/archive audits pass; native movement, NPC walking, scan publication and save/load require live testing. The new log shows the prior shared hold persisting after Scanner/Patrol role changes; it does not supply a runtime result for this repair.
