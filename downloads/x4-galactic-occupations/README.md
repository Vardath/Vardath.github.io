# Galactic Occupations 0.4.8 — capital tours and scanner physics

[Download Occupations](Galactic_Occupations_0.4.8_DEV.zip) · [All three updated mods](../x4-updates/) · [Log findings and live checks](vardath_galactic_occupations/LOG_REVIEW_0.4.8.md)

Galactic Sightseeing Tour now accepts **S, M, L and XL ships**. Visible capital services use real ship/station transporter waypoints: the same booked NPC approaches the source, transfers to the receiving room, and must actually be aboard or ashore before the booking advances. Ten passengers maximum, available crew berths, existing fare conditions, ten-stop new bookings and cancellation rules remain.

The scanner now checks visible attention as well as loaded meshes and sector context before surface queries. Inactive geometry uses the existing timed remote survey path where enabled.

Exit X4, overwrite its Occupations folder and load your existing save. Keep Protected UI and Inventory Collector. No new UI, worker restart, passenger reset or changes to the Forge weapon. The separate Hyperion Ascendant and Compatibility 1.0.1 packages address the quest/ship and other logged errors.

459 Python contracts and 91 Lua mocks pass, with native-reference/XML/ZIP checks. **Native capital transporter, physics and save/load execution remain unverified in X4.** The supplied older-version log confirms 623 balance-matched payments totalling 994,060,000 Cr; those are not runtime tests of this release.
