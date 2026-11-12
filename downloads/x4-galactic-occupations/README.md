# Galactic Occupations 0.5.0 — safe payments, sightseeing and capital tours

[Download Occupations](Galactic_Occupations_0.5.0.zip) · [All three updated mods](../x4-updates/) · [Log findings and live checks](vardath_galactic_occupations/LOG_REVIEW_0.4.8.md)

**November 12 tour hotfix:** Tour catalogues now prune destroyed/stale points-of-interest from stored lists and force a fresh catalogue search on the next cycle. Tour booking checks validity before accessing a landmark's sector, eliminating the 156 invalid \`$poi.sector\` AI errors recorded in the 2026-11-11 evening log. Existing passengers, tour tickets, destinations, sightseeing progress and paid income are not reset. **0.5.0** also validates restored receipt records and their binding keys before annotating the vanilla transaction log; invalid saved records no longer crash `Vardath.NativeIncome.Payment`. The old `0.4.8_DEV` ZIP remains available as a historical compatibility link.

Galactic Sightseeing Tour accepts **S, M, L and XL ships**. Visible capital services use real ship/station transporter waypoints: the same booked NPC approaches the source, transfers to the receiving room, and must actually be aboard or ashore before the booking advances. Ten passengers maximum, available crew berths, existing fare conditions, ten-stop new bookings and cancellation rules remain.

The scanner now checks visible attention as well as loaded meshes and sector context before surface queries. Inactive geometry uses the existing timed remote survey path where enabled.

Exit X4, overwrite its Occupations folder and load your existing save. Keep Protected UI and Inventory Collector. No new UI, worker restart, passenger reset or changes to the Forge weapon. The separate Hyperion Ascendant and Compatibility 1.0.1 packages address the quest/ship and other logged errors.

459 Python contracts and 91 Lua mocks pass, with native-reference/XML/ZIP checks. **Native capital transporter, physics and save/load execution remain unverified in X4.** The supplied older-version log confirms 623 balance-matched payments totalling 994,060,000 Cr; those are not runtime tests of this release.
