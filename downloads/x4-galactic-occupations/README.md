# Galactic Occupations 0.4.1 — spacesuit recovery and log fixes

[Download Occupations](Galactic_Occupations_0.4.1_DEV.zip) · [Six-mod bundle](../x4-updates/X4_Spacesuit_Recovery_2026-11-08.zip) · [Findings and live checks](vardath_galactic_occupations/SPACESUIT_RECOVERY_0.4.1.md)

[Scanner and passenger changes](vardath_galactic_occupations/SURVEY_BOARDING_0.4.1.md): timed off-screen module/signal-leak surveys, real station bonuses and native job/black-market discovery. Boarding/departure now accept valid disconnected NPC identities; visible blocked walking has same-actor recovery. New gameplay paths require live checking.

Adds one delayed native recovery for a confirmed Use Spacesuit exit that leaves inconsistent suit/control/room state. Normal exits remain vanilla. Fixes the invalid pilot role check in cancelled-passenger cleanup; retains twenty-minute crew recalls, interruption-safe unpaid cancellation grace and twenty-stop tour defaults.

The companion Kopis/Astrid 1.16 fixes 11,240 logged ship-blackboard braking errors and excludes native/suit transitions from the yacht's braking assist. Forge weapon assets and recovery scripts are unchanged.

Exit X4, overwrite the matching extension folders and load the same save. Keep Protected UI and Inventory Collector. The new log confirms 581,000 Cr in crystal/escort/patrol payments, but tour boarding remains unresolved. 348 Python contracts, 91 Lua mocks and static/package checks pass; new native recovery is not live verified.
