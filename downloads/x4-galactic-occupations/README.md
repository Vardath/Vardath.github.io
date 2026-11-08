# Galactic Occupations 0.4.2 — crew and order recovery

[Download Occupations](Galactic_Occupations_0.4.2_DEV.zip) · [Optional six-mod bundle](../x4-updates/X4_Crew_Order_Recovery_2026-11-08.zip) · [Log findings, fixes and live checks](vardath_galactic_occupations/CREW_ORDER_RECOVERY_0.4.2.md)

Fixes the movement lock after taking off with a crystal representative ashore and changing roles. All occupations can travel while old crew recovery runs independently; the original twenty-minute same-NPC recall and payment accounting remain. Background crystal/hacker activity no longer replaces another role's status or timeout recovery.

Scanners now use their own installed equipment, including capital ships, rather than the player's current scan context. Real completed samples queue for actual native publication when available while the ship and signal-leak benefits keep working. Pending information is explicitly labelled pending.

Exit X4, overwrite the matching Occupations extension folder and load the same save. Keep Protected UI and Inventory Collector. Only Occupations source changes; all five other bundle sources are unchanged. 370 Python contracts, 91 Lua mocks and static/package checks pass; new native movement, walking, publication and save/load remain unverified in X4 here.
