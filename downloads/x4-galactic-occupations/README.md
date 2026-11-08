# Galactic Occupations 0.3.9 — paid crystal crew return

[Download Occupations](Galactic_Occupations_0.3.9_DEV.zip) · [Six-mod bundle](../x4-updates/X4_Crystal_Crew_Return_Recovery_2026-11-08.zip) · [Log findings and live tests](vardath_galactic_occupations/LOG_REVIEW_0.3.9.md)

The supplied log confirms seven crystal payments totalling 337,000 Cr, including Astrid Tours' physical seven-item sale for 7,000 Cr. Its representative then remained at the desk. The fix commits a persistent return state with the paid invoice and lets the independent crew controller recover a lost AI handoff, including the already-paid saved visit, without paying twice or replacing crew. Missing parameter lookups and imported result/version handling are also corrected.

Exit X4, overwrite the same extension and load the existing save while the ship remains docked at that station. The same crew member should walk back; a blocked path has the documented two-game-minute native same-actor recovery at that dock. Existing crew/equipment, stock, passengers, bookings, Protected UI and Inventory Collector remain intact.

255 Python contracts, 78 Lua mocks and static/native-patch/package checks pass. New crew-return recovery still needs live confirmation. The log's tour boarding wait remains explicitly unresolved. Only Occupations source changes; companion mods in the bundle are unchanged.
