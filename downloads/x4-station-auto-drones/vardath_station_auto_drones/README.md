# Vardath – Automatic Station Drones and Managers (X4: Foundations 9.00)

This is a standalone, always-on X4 extension. It has no toggles, no DLC requirements and does not modify any existing Vardath X4 mod.

**Normal stations:** 90% cargo/transport drones, 5% defence drones, 5% repair drones.  
**Shipyards and wharves:** 60% cargo, 5% defence, 5% repair, 30% build drones.

All percentages are shares of the *shared unit/drone capacity* (not cargo ware storage). Rounding is to whole drones and allocation never deliberately exceeds the station's total capacity. Existing drones are not destroyed to achieve the mix, so the desired numbers can differ temporarily from current inventory. Missing drone types are reallocated to cargo when available. This sets the Logical Overview supply-order targets, not physical drone units; the normal game supply mechanics must buy/build the units.

A Mission Director cue scans the player's old and new stations across the galaxy **every in-game minute**. A Lua event applies/reapplies targets to stations with drone storage. The Lua routine keeps unrelated supply-order entries, including missiles. Manual edits to targets will be reset by the next scan. When station capacity or build-ship capability changes, requirements are recalculated.

Once a player station has a **completed operational dock or pier**, the scan also creates and assigns a manager to its vacant manager post. It checks the actual control-entity list, preserving any existing manager. If you dismiss a manager while a dock remains, the routine creates a replacement on the next scan. It does not automatically hire a ship dealer, create drones or fund station accounts.

## Install

Download `vardath_station_auto_drones_TEST.zip` and extract the single `vardath_station_auto_drones` folder into `X4 Foundations/extensions`. Ensure `extensions/vardath_station_auto_drones/content.xml` exists. Enable in X4's Extensions menu and restart.

**Validation status:** static XML/ZIP and allocation checks passed in development. X4 9.00 runtime has not been run here. Back up a save and confirm manager assignment and drone requirements on an old station, a new dock, and a wharf/shipyard.
