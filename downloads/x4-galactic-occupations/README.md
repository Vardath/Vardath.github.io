# Galactic Occupations 0.4.6 — spacesuit handoff recovery

[Download Occupations](Galactic_Occupations_0.4.6_DEV.zip) · [Optional six-mod bundle](../x4-updates/X4_Spacesuit_Control_Update_2026-11-09.zip) · [Evidence and live checks](vardath_galactic_occupations/LOG_REVIEW_0.4.6.md)

After a confirmed Use Spacesuit stalls, recovery resets the original ship context, requires a real native teleport acknowledgement, attempts one suit exit and verifies actual suit/control/room/transit state. A failed exit has one bounded original-ship return. No unrequested/repeated ejections, crew/order changes or UI replacement. The station NPC empty-service-slot branch is also guarded before actor creation.

The supplied 035808 log confirms the earlier recovery fired but ends before verification. It also confirms 26 crystal sales and two completed tours paid 10,700,000 Cr with matching balance changes. Other data/UI errors are documented with uncertain callers left unattributed.

Exit X4, overwrite the matching Occupations extension folder and load the same save. Keep Protected UI and Inventory Collector. Tours retain the ten-stop new default and extra hour from 0.4.5; existing bookings/settings are preserved. 415 Python contracts, 91 Lua mocks and static/native-reference/package checks pass. New native recovery and station population execution need live X4 confirmation. Companion sources are unchanged.
