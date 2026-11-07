# Galactic Occupations 0.2.4 — target recovery and visible job results

[Download Occupations](Galactic_Occupations_0.2.4_DEV.zip) · [Current four-mod bundle](../x4-updates/X4_Job_Activity_Fixes_2026-11-07.zip) · [Log findings and all twelve jobs](vardath_galactic_occupations/JOB_REVIEW_0.2.4.md)

The supplied debug(5).log identifies 37 empty-sector approach failures, 222 resulting native navigation errors, 11 unsafe sector-owner lookups and one recruitment lookup on a wreck. This release waits for a usable target context, never knowingly passes an empty sector to navigation, and rejects unavailable live-service targets before capture/pilot lookups.

Every assigned occupation now writes a status summary to the **existing vanilla General Logbook** and debug log about every five minutes: current work, target, destination, started/completed task counts, actual recorded earnings and the last result. Completed work gets a detailed immediate result. Counters start with this update; activity reports create no rewards and do not claim completion. The native transaction ledger and Protected UI integration are unchanged.

The station scanner promptly reports unloaded collision geometry instead of spending twenty seconds on each unavailable module. Other jobs report concrete morale changes, capture results, passenger deliveries, crystal collection and failed prerequisites. Physical harvesting/demolition still require visible simulation; no OOS effects are invented.

Fully exit X4, replace the extension, restart and load the existing save. Keep Protected UI enabled. Reassign occupations already lost to Hold Position. Passenger manifests, tour progress, crew and equipment are retained. Only Occupations source changes in this repair; the four-mod bundle includes current unchanged Builder, Kopis and Yaki versions.

Static checks are separate from in-game acceptance. The game log cannot establish every job's completion or income, and no executable/save is available to run 0.2.4 here. See the installed review and testing instructions for the evidence and remaining checks.
