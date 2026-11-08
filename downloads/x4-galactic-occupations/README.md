# Galactic Occupations 0.3.8 — galaxy service recovery

[Download Occupations](Galactic_Occupations_0.3.8_DEV.zip) · [Six-mod bundle](../x4-updates/X4_Galaxy_Service_Recovery_2026-11-08.zip) · [Log findings and live tests](vardath_galactic_occupations/LOG_REVIEW_0.3.8.md)

The new log exposes a 0.3.7 regression: a merchant NPC was passed to an object-only interaction API. That call is removed. Physical counter visits use native room/floor queries and actual crew arrival. Off-screen crystal sales use the requested finite-stock broker simulation at a real permitted dock, so unloaded trading corners no longer block galaxy-wide sales. Cash goes to the player; existing stock and unpaid balances survive.

Taxi/tour keep real named NPCs and native passenger rosters. Away from the player, native-style roster/actor handoffs avoid waiting forever for uninstantiated rooms. Visible NPCs use actual ship/station points. Only whole-party departure at the booked station completes a fare; tours still require their full itinerary. No alternative drop-off, duplicate payment or synthetic passenger cargo.

Only Occupations changes this time. The log verifies two 8,000 Cr patrol payments; it does not verify a new crystal sale or passenger fare. 242 Python contracts and 78 Lua mocks pass, plus XML/reference/native-patch/package checks. These are not in-game tests. Close X4, overwrite the same extension and load the existing save. Protected UI, Inventory Collector, Forge/Astrid and companion mod sources are preserved. Full limits and reproducible tests are in the linked review.
