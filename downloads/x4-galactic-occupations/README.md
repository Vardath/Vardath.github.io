# Galactic Occupations 0.3.1 — station menu and crystal recovery

[Download Occupations](Galactic_Occupations_0.3.1_DEV.zip) · [Four-mod bundle](../x4-updates/X4_Hacker_Menu_Crystal_Fix_2026-11-07.zip) · [Repair report](vardath_galactic_occupations/MENU_CRYSTAL_REVIEW_0.3.1.md) · [Install and use](vardath_galactic_occupations/README.md)

Repairs the native station submenu's stale Checking row: rebuild only the custom actions when the reply arrives, poll for missed replies, and offer a real-time timeout/retry. Unpause for Mission Director lookups; missing/unloaded panels produce an explicit empty result.

Adds a configurable active-simulation fallback for crystal miners, actual loose-crystal-drop recovery, bounded native pickup retries and a native player-ship route to player inventory if NPC pickup is refused. No invented crystals, cash, crate deletion or out-of-sector damage. The new log separates search, real damage, pickup and observed item delivery. Thirteen galaxy-wide behaviours, crew hacking, 8,000 Cr verified foreign-trader patrol fees and the original vanilla ledger are retained.

Close X4, overwrite this extension and load the existing save with Protected UI and Inventory Collector enabled. Re-select Crystal Miner if its new Follow active crystal simulation setting is missing. The fallback must work in active simulation; enter an actual asteroid field to verify harvesting. Other mod sources are unchanged; the bundle includes their current versions.

Source/XML, inventory/UI mocks and archive audits are distinct from in-game testing. Actual new crystal delivery and remote crew hacking remain runtime-unverified here.
