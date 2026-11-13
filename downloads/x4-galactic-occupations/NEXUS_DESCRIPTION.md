# Galactic Occupations — 13 Autonomous Ship Careers for X4: Foundations

**Version:** 0.5.4
**Game:** X4: Foundations 9.00
**Author:** Vardath
**Existing saves:** Supported — no new game required

## Overview

Give your player-owned fleet useful work beyond ordinary trade, mining and combat. Galactic Occupations adds **thirteen persistent autonomous ship roles**, selectable through X4's familiar behaviour controls. Ships can search for suitable tasks over a configurable region, move between sectors and complete paid services or strategic assignments while you manage the wider empire.

Choose a home sector, operating range (including the whole connected galaxy), risk level and available service options. Jobs are designed to use existing ships and crews rather than replacing your fleet.

## The thirteen occupations

1. **Galactic Escort Service:** Escort real commercial traffic to its destination. A verified successful foreign-faction service can earn a fee and modest reputation.
2. **Galactic Taxi Service:** Collect up to ten real NPC passengers, limited by available crew berths, then carry them to booked destinations. Fares are paid only after successful delivery and disembarkation.
3. **Station, Component and Signal Scanner:** Survey station modules and investigate signal leaks. Discover component information, eligible station benefits, offers and contacts through native game mechanisms.
4. **Wormhole and Anomaly Mapper:** Explore gates, accelerators and anomalies and record their actual connections without inventing destinations.
5. **Galactic Sightseeing Tour:** Take up to ten passengers on luxury tours of points of interest, then return and disembark them. Newly assigned tours default to **ten sightseeing stops**, with saved bookings retaining their settings. Where docking and crew capacity allow, S, M, L and XL ships can run tours.
6. **Autonomous Crystal Miner:** Search for and harvest crystals with suitable weapons or turrets. Optional resource-based off-screen mining and finite station sales allow remote crystal work.
7. **Hostile Lure and Interception:** Draw a manageable enemy into pursuit and retreat towards an actual friendly patrol or stronger force.
8. **Asteroid Demolition:** Locate destructible asteroids and shoot them using appropriate weapons. Optional collection of demolition drops is available.
9. **Fleet Morale Booster:** Visit other ships to improve eligible crew morale. Reputation benefits depend on a verified improvement, not simply arriving.
10. **Traffic Control and Cargo Inspection:** Perform cargo inspections using the game's jurisdiction and contraband rules without automatically starting conflicts.
11. **Emergency Ship Recruitment:** Attempt to persuade eligible hostile ships below 25% hull to surrender. Success is probabilistic, and protected or mission ships are excluded.
12. **Trade Route Patrol:** Follow active trader routes, provide protection and move on to other commercial corridors. Verified protection and arrival are required for payment.
13. **Galactic Station Hacker:** Use real hacking tools and an existing crew member to work at an eligible station's native control panel. Hacking depends on docking, available interiors and actual effect verification; it is not an automatic income source.

**Extra command:** Select an eligible player-owned ship and right-click a station to queue **Hack selected station panel** for a specific available panel. This complements the automated hacker role.

## Managing your fleet

- Choose occupation behaviours using the standard ship order/behaviour system.
- Configure home sector, range, risk and task options.
- Assign multiple ships to different services without changing their equipment or crew.
- Follow completed activities and legitimate income through X4's native logbook and transaction ledger.
- Use the optional **Mine Crystals** turret-mode addon to support crystal operations.

These are functional jobs, not free-credit cheats. Some earn money from actual completed services; others provide exploration, morale, security, recruitment or intelligence. Each role has its own suitability requirements for weapons, scanners, cargo, docking, crew or location.

## International language support — new in v0.5.1

English strings are now included in **`t/0001.xml` as a language-neutral fallback**. This should prevent `=ReadText191180-XXX=` placeholders when the game is running in Russian, German, French and other non-English languages.

This is **English fallback text, not a translation**. Separate community translations can be added through matching language-specific files later. The existing English text is preserved.

## Installation and updates

1. Exit X4: Foundations.
2. Extract the complete ZIP into your X4 Foundations game installation directory.
3. Confirm `extensions/vardath_galactic_occupations/content.xml` exists.
4. Enable the extension in the game's Extensions menu and load your existing save.
5. Select an eligible ship and choose a Galactic Occupations role in its behaviour controls.

When upgrading, overwrite the previous Galactic Occupations extension folder. **No new game is necessary.**

## Compatibility and limitations

The mod is developed for X4 9.00, with optional compatibility support for Sector Explorer and Auto Trade Subscriptions. It does not require either optional extension.

Some occupations rely on docking access, spare crew slots, actual station panels, a compatible ship class, discovered targets, loaded physics or native NPC movement. Jobs may wait or skip assignments when these requirements cannot be met.

GitHub Actions checks the extension's XML, source contracts, mocked Lua integration and ZIP integrity. New behaviour and localization still require testing in X4 itself. The v0.5.1 update affects localization and documentation only; it does not reset existing jobs, bookings, wages, orders or saved state.

**Source and downloads:** https://github.com/Vardath/Vardath.github.io/tree/main/downloads/x4-galactic-occupations

## v0.5.4 changelog

- **Station scanning:** verified surveys now immediately publish each scanned module's identity and native map snapshot. High-detail scanner limits still apply; unvisited modules are not revealed.
- **Blueprint recovery:** optionally consume one real Spacesuit EMP from player inventory per researched, eligible missing station module blueprint. Requires close-range NPC survey and completed PHQ research; excluded module types remain unavailable. This uses the native blueprint award after resource consumption but is not an animated or physical bomb/data leak. Toggle **EMP blueprint recovery** in the scanner Behaviour; default OFF.
- **Choose hacking objective:** autonomous hacker Behaviour now offers a numeric choice: 0=random, 1=production, 2=turrets, 3=shields, 4=storage, 5=radar, 6=construction, 7=security. Hacker only uses an available native panel of that type; station context menu still supports specific panel selections and real crew interior work.
- **Mine Crystals:** while active, suspend the selected turret's existing native mining behaviour so it cannot independently aim at whole asteroid bodies. Save and restore its exact previous native turret mode. Search up to 96 nearest asteroids within 15 km for real `class.crystal` deposits. Physical scripted turret fire requires live testing with beam weapons.
- Existing saves supported, no changes to native menu tables or UI scale. Source validation is not an in-game acceptance test.

## v0.5.3 changelog

- Disabled Galactic Occupations' forced spacesuit recovery following ordinary transporter confirmations. An earlier recovery could teleport a player back to a ship and then issue an emergency spacesuit exit while redocking.
- Normal ship/station transporters, X4-native spacesuit use, crew, saved occupations and payments remain unchanged. No new game needed.
- Automated source and mocked UI tests added. In-game floor clipping is not universally solved; try the native Shift+D return-to-ship function if trapped.

## v0.5.2 changelog

- Removed the optional occupation-status row from the game's native ship-information table to preserve dynamic row/column layout.
- Retained all occupation behaviours, Mine Crystals turret controls, saved state and crew. No new game needed.
- Automated source and mocked UI validation; live X4 map behaviour remains to be confirmed.

## v0.5.1 changelog

- Added universal English fallback for non-English game clients.
- Corrected the tour tooltip to the current ten-stop default.
- Added text coverage validation and this detailed role description.
- No game logic or save-state changes.
