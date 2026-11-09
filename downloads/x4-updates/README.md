# X4 Hyperion speed and combat update — 10 November 2026

[Download all three changed extensions](X4_Hyperion_Speed_Update_2026-11-10.zip)

| Extension | Version | Change |
|---|---|---|
| [Galactic Occupations](../x4-galactic-occupations/) | 0.4.8 DEV | S/M/L/XL sightseeing tours, same-NPC transporter boarding/departure, station scanner physics guards. |
| [Compatibility Fixes](../x4-compatibility-fixes/) | 1.0.1 | Stable mission cleanup and bounded Inventory Collector, HeadHunter and Emergent Rescue guards. Previous compatibility guards retained. |
| [Hyperion Ascendant](../x4-hyperion-ascendant/) | 1.0.1 | Threefold speed increase; 2,000,000 main damage; 1,600,000 beam hull/shield damage; corrected quest reset scheduling and ware metadata. |

Exit X4 and extract into the **game directory**: the ZIP already contains `extensions/`. Overwrite the two matching existing folders and add `vardath_hyperion_ascendant`. Load your existing save. Hyperion Ascendant requires **Hyperion Pack** and **Cradle of Humanity**. Keep Protected UI and Inventory Collector enabled. Keep the new ship extension installed while its custom ships exist in a save.

Only Hyperion Ascendant changes in this release; Occupations 0.4.8 and Compatibility 1.0.1 are carried forward unchanged. The bundle contains exactly the three extensions above. Forge/Astrid, Builders, Yaki Habitats, Station Drones, Invincibility and Cargo Teleport sources are unchanged. Existing passenger bookings, fares, orders, crew, crystal stock and invoices persist. New tours default to ten stops with up to ten passengers and available berths; accepted older itineraries remain valid.

459 Occupations Python contracts, 91 Lua mocks, 22 Hyperion contracts and 15 Compatibility contracts pass. Current ZIP/source comparisons, pinned native references and the existing seven-extension static audit pass. **No X4 engine, user save or merged installed mod catalog was available:** updated ship combat/drive/quest timing and save/load execution still require live acceptance.

[Current log review and reproducible in-game checks](../x4-hyperion-ascendant/vardath_hyperion_ascendant/LOG_REVIEW_1.0.1.md) · [Remaining third-party errors and compatibility scope](../x4-compatibility-fixes/vardath_compatibility_fixes/REVIEW_1.0.1.md) · [Hyperion tests and limitations](../x4-hyperion-ascendant/vardath_hyperion_ascendant/README.md)

The new 211446 log confirms 50 uniquely keyed, balance-matched payments totalling 113,752,000 Cr. It does not establish a crash cause or prove the new code runs in-game. No UI protection is disabled.

The [previous Hyperion/tours bundle](X4_Hyperion_Tours_Update_2026-11-10.zip) retains Ascendant 1.0.0. The [previous six-mod bundle](X4_Hacker_Survey_Update_2026-11-09.zip) remains available as a historical snapshot; it contains older Occupations and does not include this update.
