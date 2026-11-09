# X4 spacesuit control update — 9 November 2026

[Occupations 0.4.6](../x4-galactic-occupations/Galactic_Occupations_0.4.6_DEV.zip) · [Optional six-mod bundle](X4_Spacesuit_Control_Update_2026-11-09.zip) · [Evidence and live checks](../x4-galactic-occupations/vardath_galactic_occupations/LOG_REVIEW_0.4.6.md)

| Extension | Version | Change |
|---|---|---|
| Galactic Occupations | 0.4.6 DEV | Bounded spacesuit context reset, native handoff verification/ship return, station NPC empty-slot guard. |
| Kopis/Astrid | 1.16 | Source unchanged; Forge weapon preserved. |
| Living Factions Builders | 1.75 | Source unchanged. |
| Yaki Habitats | 1.23 | Source unchanged. |
| Station Auto Drones | 1.02 | Source unchanged. |
| Universal Cargo Teleport | 1.01 | Source unchanged. |

Only Occupations needs updating. Exit X4, extract into `extensions/`, overwrite its matching folder and load the existing save. Keep Protected UI and Inventory Collector. Existing orders, bookings, crystal stock and unpaid invoices are preserved. 415 Python contracts, 91 Lua mocks and static/source/archive checks pass; new native recovery/population execution needs live X4 confirmation.
