# Galactic Occupations 0.4.4 — cold-start and compatibility fixes

[Download Occupations](Galactic_Occupations_0.4.4_DEV.zip) · [Optional six-mod bundle](../x4-updates/X4_Startup_Loadout_Fixes_2026-11-09.zip) · [Full findings and live checks](vardath_galactic_occupations/LOG_REVIEW_0.4.4.md)

The new manifest43 log confirms **13,353,000 Cr** from 137 balance-matched payments: a complete twenty-stop luxury tour across fifteen sectors pays 5,000,000 Cr after all ten destination departures, and 136 stock-backed crystal sales pay 8,353,000 Cr. Thirteen scanner visits complete; the prior mission-reference, CHC and character-model floods are absent.

0.4.4 guards one startup registry read, removes two erroneous explicit-null station loadout overrides and extends optional Auto Trade Subscriptions compatibility to eighteen additional logged faction conditions. Job AI/navigation, payments, passengers, crew-return actions, turrets, UI and companion sources are unchanged. The third-party subscription initializer is not forcibly replayed.

Exit X4, overwrite the matching Occupations extension folder and load the existing save. Keep Protected UI and Inventory Collector. 387 Python contracts, 91 Lua mocks and static/native-reference/package checks pass; the new corrections still require live X4 confirmation. Missing faction equipment/ship candidates and stale UI callback errors remain documented separately.
