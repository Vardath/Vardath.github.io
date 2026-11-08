# Galactic Occupations 0.4.5 — shorter tours and longer timeouts

[Download Occupations](Galactic_Occupations_0.4.5_DEV.zip) · [Optional six-mod bundle](../x4-updates/X4_Tour_Timeout_Update_2026-11-09.zip) · [Full findings and live checks](vardath_galactic_occupations/LOG_REVIEW_0.4.5.md)

Newly assigned Tours default to **ten stops**. Accepted bookings and valid saved settings keep their promised route/fare. Active booked-tour task/docking deadlines receive **one extra game hour**, tracked so repeated polling does not extend the same deadline again. Cancelled-tour grace gains an hour above the previous measured estimate, with a **three-hour minimum**; pending saved deadlines extend once. Taxi and crew-return timers, passenger actions, payments and UI are unchanged.

The supplied manifest44 log confirms 28,993,000 Cr from 193 crystal sales and four completed full tours. It contains no error block explicitly naming this suite; the documented remaining messages concern external scripts, missing equipment/ship candidates and UI/save-header queries.

Exit X4, overwrite the matching Occupations extension folder and load the same save. Keep Protected UI and Inventory Collector. Existing orders still configured for twenty stops can be changed to ten for their next booking; current accepted tours retain their stop count. 400 Python contracts, 91 Lua mocks and static/native-reference/package checks pass. New native timeout integration needs in-game confirmation; all companion sources are unchanged.
