# Galactic Occupations 0.2.3 — tour departure, passenger drop-off and patrol repair

[Download Occupations](Galactic_Occupations_0.2.3_DEV.zip) · [Current four-mod bundle](../x4-updates/X4_Tour_Patrol_Fixes_2026-11-07.zip) · [All twelve jobs reviewed](vardath_galactic_occupations/JOB_REVIEW_0.2.3.md)

Actual boarding is reported working in 0.2.2. This update adds explicit native undocking to movement paths, selects a tour's first sight immediately after boarding, and requires the same passengers to leave at the final station before a taxi/tour can finish and receive its fare. Visible passengers walk off; off-screen unloading attempts a verified actual actor-room transfer, never timer-only success.

Escort and Trade Route Patrol no longer borrow the vanilla same-faction fleet escort order, which can replace/cancel their orders. Real trader contracts persist across separately queued defensive attacks. Cargo inspection's boolean lookup and Yaki Habitats' direct plan macro lookup are fixed too. Protected UI, existing passenger batches and the Forge weapon are preserved.

Fully exit X4, replace the included extension folders, restart and load the existing save. Reassign occupations already lost to Hold Position. Current tour passengers and itinerary progress remain saved. The repaired departure/unloading/patrol flow still needs in-game confirmation; crystal harvesting remains unverified. Static success is not a claim of a completed gameplay test.
