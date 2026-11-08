# Galactic Occupations 0.3.6 — docked services and galaxy movement

[Download Occupations](Galactic_Occupations_0.3.6_DEV.zip) · [Five-mod bundle](../x4-updates/X4_Docking_Travel_Recovery_2026-11-08.zip) · [Log evidence, all-role review and live tests](vardath_galactic_occupations/LOG_REVIEW_0.3.6.md)

Repairs the native automatic-undock boundary that interrupted taxis, tours and crystal sellers after landing. The exact owned service resumes at its recorded dock; explicit departure clears the bounded handoff. Passengers leave only at the booked taxi destination or original tour pickup station. No alternate/safety station is selected after boarding.

Scoped native jump discovery now honours shared VGO galaxy routing, including Morale, while keeping native blacklists and other orders intact. Crystal field search no longer performs invalid arithmetic on time. Existing real passengers, routes, crew, equipment, finite stock and unpaid balances are retained. Crystal sales now require an existing crew member at a real inventory-trader counter, finite merchant stock acceptance and the same actor back aboard before occupation departure. Escort/patrol partial payments retain their unpaid balance. [Crew sales and live limits](vardath_galactic_occupations/CREW_CRYSTAL_SALES_0.3.6.md).

203 Python contracts, 78 Lua mocks, native diff grammar/selectors and seven package audits are separate from X4 runtime verification, which is unavailable here. The report identifies demonstrated log9 failures, new repairs, actual recorded work/payments and remaining limits for every role. Keep Protected UI and Inventory Collector; no vanilla UI renderer is replaced.

Fully exit X4, overwrite the extension and load the same save. Already-inserted launch orders may finish once; the next planned docking must resume the service. Reselect only jobs already lost to Hold. Companion source mods remain Builders 1.75, Kopis/Astrid 1.15, Yaki Habitats 1.23 and Cargo Teleport 1.01.
