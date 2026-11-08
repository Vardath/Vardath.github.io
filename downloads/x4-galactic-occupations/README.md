# Galactic Occupations 0.4.0 — interruption-safe recovery

[Download Occupations](Galactic_Occupations_0.4.0_DEV.zip) · [Six-mod bundle](../x4-updates/X4_Recovery_Grace_2026-11-08.zip) · [Recovery rules and live checks](vardath_galactic_occupations/RECOVERY_POLICY_0.4.0.md)

Stranded crystal/hacker crew are recalled to the same ship after twenty game minutes away, preserving the same NPC, role, post and native roster. Cancelling the persistent taxi service gives passengers thirty game minutes before unpaid evacuation. Cancelled tours get at least two game hours, extended by observed cruise duration. Resuming before expiry keeps the same party. Combat, lockboxes, other orders and player control retain passengers whenever the original default or queued service remains.

New tours default to twenty stops; accepted bookings keep their existing route. Cancellation cleanup removes only that booking's passenger entries and preserves anyone recruited into ordinary crew. No cancellation fare, duplicate payment, extra actor or invented ledger transaction. Timers and progress persist across saves.

Exit X4 and overwrite the existing extension, then load the same save. Keep Protected UI and Inventory Collector. Only Occupations source changes. 299 Python contracts, 78 Lua mocks and static/native-patch/package checks pass; new native recalls and evacuations remain unverified in X4. The prior tour boarding wait remains a separate reported limitation.
