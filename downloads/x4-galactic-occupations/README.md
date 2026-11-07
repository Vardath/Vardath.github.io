# Galactic Occupations 0.2.5 — crystal weapons and direct player inventory

[Download Occupations](Galactic_Occupations_0.2.5_DEV.zip) · [Four-mod bundle](../x4-updates/X4_Crystal_Inventory_Fix_2026-11-07.zip) · [Crystal repair and test report](vardath_galactic_occupations/CRYSTAL_REVIEW_0.2.5.md)

The supplied debug(6).log confirms twenty crystal reports blocked by beam-only preflight and no attempted harvest. This release accepts S/M/L/XL ships, forward guns, ordinary turrets and missile turrets. It adds native aiming/arc attempts and per-asteroid deposit detection, and prevents competing occupation/standalone turret controllers.

Actual attributed crystal drops are collected at short range with the native pickup action, then existing captain-held crystals are immediately and accountably forwarded to **player inventory**. No cargo hold, cargo drones, beam-only setting, captain holding limit or automatic sale is required. There is no free item or cash grant. Real weapons, ammunition, collision-safe access and physical simulation are still necessary; no off-screen harvest is fabricated.

Fully exit X4, overwrite this extension, restart and load your existing save with Protected UI enabled. Reassign any job already lost to Hold Position. Existing passengers, itineraries, equipment, crew and history remain saved. All other mod sources, including Forge/Astrid equipment and Inventory Collector, are untouched.

XML/reference, source/accounting and Lua mock checks are separate from in-game verification. This development environment cannot run X4; the newly enabled firing, pickup and player-inventory effects remain runtime-unverified. The report includes reproducible tests and the supplied log's actual evidence.
