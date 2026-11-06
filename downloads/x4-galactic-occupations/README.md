# Galactic Occupations 0.2.1 — native transaction screen repair

[Download the extension](Galactic_Occupations_0.2.1_DEV.zip) · [All three changed mods](../x4-updates/X4_Updated_Mods_2026-11-07.zip) · [Features and installation](vardath_galactic_occupations/README.md) · [Testing](vardath_galactic_occupations/TESTING.md)

Removed the custom income panel and all transaction rendering/search/paging overrides after the supplied log confirmed they broke the native transaction screen. Real Occupations and Builder payment rows receive descriptive text only through the optional published UI Extensions callback. No synthetic entries, duplicate money or forced changes to Protected UI Mode. Without that callback, native labels remain generic and detailed paid receipts remain in the ordinary Logbook.

The log's ship/component state-write failures, invalid listeners, firing attention contexts and Astrid null lookup are addressed too. Range 99 still covers the connected accessible galaxy; taxi and ten-stop luxury tours still require actual NPC boarding and crew capacity. All physical gameplay acceptance remains pending in the actual game.

Fully exit X4 before updating the existing extension folders, restart and load the existing save. See the included reproducible acceptance tests and factual static report. This is a development build, not a claim of successful in-game testing.
