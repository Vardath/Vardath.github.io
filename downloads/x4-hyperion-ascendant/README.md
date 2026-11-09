# Hyperion Ascendant 1.0.1

[Download the updated ship and quest repair](Hyperion_Ascendant_1.0.1.zip) · [Full configuration and tests](vardath_hyperion_ascendant/README.md) · [New log review](vardath_hyperion_ascendant/LOG_REVIEW_1.0.1.md) · [Current three-mod bundle](../x4-updates/X4_Hyperion_Speed_Update_2026-11-10.zip)

The Ascendant’s normal, reverse, boost and travel thrust are **three times its previous settings**. Each main projectile deals **2,000,000** base damage. Each of its eight beam turrets has **1,600,000 damage and 1,600,000 shield damage**, ten times Astrid Tours’ listed beam damage, with matching fast aiming and turret reload settings. These are configured values; effective speed and combat performance require live testing.

The new log exposed an immediate signal after a deferred native cue reset. The repair now waits one second in a separate actions block, rechecks the live quest/sector/listener and can recover the waiting scan left by 1.0.0. Equipment-use metadata and unused blueprint-owner entries are corrected, and localized ship naming no longer uses the warned expression form.

Exit X4, overwrite `extensions/vardath_hyperion_ascendant` and load the existing save. The ZIP includes `extensions/`. Existing ship, macro IDs, equipment modifications, crew and orders are preserved; no new game is required. Keep Hyperion Pack, Cradle of Humanity, Protected UI and Inventory Collector enabled.

22 source/mocked contracts, 15 pinned references, native diff-selector checks and archive/source comparisons pass. **New native timing, speed, combat and save/load execution remain unverified in X4.** Other extension sources are unchanged. The log records 50 balance-matched occupation payments totalling 113,752,000 Cr and no exact fatal/crash marker; remaining external data/UI issues are listed in the review.
