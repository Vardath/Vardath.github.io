# Tour, taxi and patrol fixes — 7 November 2026

[Download the current four-mod bundle](X4_Tour_Patrol_Fixes_2026-11-07.zip).

Fully exit X4, replace the included extension folders, restart and load the existing save. Keep Protected UI enabled. Reassign jobs already lost to Hold Position. Already boarded passengers, tour progress, crew, equipment and ownership remain saved.

| Extension | Version | This delivery |
|---|---|---|
| Galactic Occupations | 0.2.3 DEV | Explicit departures; real full-batch taxi/tour drop-off; persistent neutral-trader escort/patrol with separate temporary combat orders; boolean cargo check and namespaced map icons. |
| Yaki Terran Habitats | 1.23 | Direct native plan macro access; skip expansion on failed inspection; no removal of existing modules. |
| Living Factions & Builders | 1.75 | Included current version, unchanged in this repair. Native payment receipts retained. |
| Kopis Production Cheat | 1.15 | Included current version, unchanged in this repair. Forge special weapon and Astrid equipment retained. |

Taxi: board → undock → direct destination → dock → all accepted passengers leave → fare. Tour: board → undock → booked sightseeing itinerary → dock → all accepted passengers leave → luxury fare. Visible passengers walk off; off-screen unloading requires an actual connection of the same cue actor into a real destination room, or remains unpaid. No timer-only completion. NPC room/path availability still requires in-game confirmation.

The native fleet escort subroutine was unsuitable for neutral traders and could replace the occupation's orders. The replacement follows actual commercial routes and isolates defensive combat in separate temporary native orders. This update does not overwrite unrelated player orders or intentionally selected Hold.

All twelve occupations were source-reviewed; [the included report](../x4-galactic-occupations/vardath_galactic_occupations/JOB_REVIEW_0.2.3.md) distinguishes fixes and remaining runtime tests. User-observed successful boarding in 0.2.2 does not prove the complete trip or crystal harvest. XML/API, 28 source constraints, 31 mocked Lua contracts and seven-mod packaging audits are separate from in-game execution.
