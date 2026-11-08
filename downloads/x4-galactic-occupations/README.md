# Galactic Occupations 0.3.7 — crystal counter recovery

[Download Occupations](Galactic_Occupations_0.3.7_DEV.zip) · [Six-mod bundle](../x4-updates/X4_Crystal_Counter_Recovery_2026-11-08.zip) · [Current log report and live tests](vardath_galactic_occupations/LOG_REVIEW_0.3.7.md)

The supplied debug(10) proves actual docking/worker resumption, 23 successful sector-travel attempts, a five-crew morale improvement, one 8,000 Cr patrol payment and seven real crystal pickups. It does not show a crystal sale: miners waited for merchants or a usable customer position, then retried.

This build fixes missing first-use population/payment clocks, targets the actual merchant for interaction, uses nearby free NPC positions, retains cooldowns for every failed buyer, and adds stage diagnostics. Stock, existing crew, passenger bookings, earned claims, normal turret settings, Protected UI and Inventory Collector are preserved. Source/mocked tests pass; native NPC paths and sales still require in-game confirmation.

Close X4, overwrite the extension, then load the same save. Existing batches are retained. The bundle includes Occupations 0.3.7, Auto Drones 1.02 (one missing-statistics guard), Builders 1.75, Kopis/Astrid 1.15, Yaki Habitats 1.23 and Cargo Teleport 1.01. The last four sources are unchanged.
