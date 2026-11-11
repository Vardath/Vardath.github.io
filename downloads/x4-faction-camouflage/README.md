# Vardath Faction Camouflage 1.01

Installable, standalone X4: Foundations extension for **Hyperion Ascendant** and **Astrid Tours**, with no changes to either original ship mod.

[Download the extension](Vardath_Faction_Camouflage_1.01.zip)

## Requirements

* X4 Foundations 8.00 or later
* Hyperion Ascendant or Astrid Tours, as published in this repository
* SirNukes **Mod Support APIs** (`sn_mod_support_apis`, Workshop identifier `ws_2042901274`). The user's last debug log showed this installed.

## Use

Exit the game and extract the ZIP into the X4 Foundations directory. Its paths begin with `extensions/vardath_faction_camouflage/`; enable the new extension. Right-click an owned Hyperion Ascendant or Astrid Tours ship on the map, choose **Select faction camouflage...**, then select a faction. Use **Drop faction camouflage** on the same right-click menu to switch straight back, or select **Use my real faction** in the chooser.

The action calls the genuine X4 `md.Cover.TriggerCover` mission-director cue. All normal attack, scan, mission and exposure rules apply. The mod does **not** alter real ownership, force camouflage to persist through combat, restore reputation, create orders, or change weapons, equipment, crew, ship loadouts, or orders. Saving an active cover uses the game's native cover state.

## Release verification

Archive blob SHA-1: `95e5561cc687b7f7a29766a01fd7bebf8ac0ac7e`. Static XML/ZIP tests passed; live in-game selection and combat behaviour need testing. The archive itself contains the full editable MD script and README.

For an initial game test, try the faction chooser and drop-cover action in a disposable save before using the ships in combat.
