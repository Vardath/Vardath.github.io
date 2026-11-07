# Galactic Occupations 0.3.5 — passenger departure and fares

[Download Occupations](Galactic_Occupations_0.3.5_DEV.zip) · [Five-mod bundle](../x4-updates/X4_Passenger_Completion_2026-11-08.zip) · [Findings, limits and live tests](vardath_galactic_occupations/PASSENGER_COMPLETION_0.3.5.md)

Repairs the shared taxi/tour departure path: native-style roster release, the same real NPCs walking to station transport points, actual room/full-party verification, preserved retries and bounded blocked-path recovery. Booked fares use observed credits, retain zero/partial unpaid balances and mark paid only after full receipt. Taxi pays 8,000 Cr per delivered passenger; luxury tours retain the booked ticket price (default 500,000 Cr) after the full itinerary and departure.

All 152 Python contracts and 78 Lua mocks pass locally. XML/reference and seven-extension package audits are separate. New X4 execution remains unverified. Existing passengers, tour progress, crew, equipment and other occupations are retained. Protected UI and the vanilla ledger remain; no custom ledger UI is added.

Fully exit X4 before overwriting the matching extension. Load the existing save; reselect only jobs already lost to Hold. Companion sources are unchanged: Builders 1.75, Kopis/Astrid 1.15, Yaki Habitats 1.23, Cargo Teleport 1.01. Earlier unrelated external errors remain described in the debug(8) report.
