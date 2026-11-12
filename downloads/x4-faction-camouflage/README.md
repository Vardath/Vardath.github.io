# Vardath Faction Camouflage 1.02 — all player-owned ships

[Download the installable extension](Vardath_Faction_Camouflage_1.02.zip)

**Version 1.02** expands the original Hyperion Ascendant / Astrid Tours camouflage selector to **every operational player-owned ship** (including modded ships). It does not alter ship macros, pilot assignments, crew, orders, equipment, trade/storage, reputation or combat behaviours.

## Installation and use

Requires X4: Foundations 8.00+ and SirNukes **Mod Support APIs** (`sn_mod_support_apis`, Workshop `ws_2042901274`). The uploaded 12 November log confirms those APIs and Camouflage 1.01 loaded. Exit X4, extract this ZIP to the **game directory**, merging `extensions/vardath_faction_camouflage/`. Load your existing save; no new start, refit or equipment installation is necessary.

Right-click **any operational player-owned ship** on the map. Choose **Select faction camouflage...** to see available factions. Choose a faction, or choose **Use my real faction (disable camouflage)** to reveal the real player identity. While under cover, **Drop faction camouflage** appears on the same map context menu.

The commands call the **native X4** `md.Cover.TriggerCover` cue, which manages normal scans, exposure, combat and reputation outcomes. The extension does *not* maintain cover during attacks, reverse any player-reputation loss, suppress story or mission checks, or restore camouflage automatically after exposure. Native player-cover rules may drop cover when control is transferred between ships.

## Verification and scope

Git blob for V1.02 installable ZIP: `8f387eebf9035425066056b12def0d67bac63d5f`. The ZIP includes complete editable MD XML. Source/ZIP/XML/static-API checks can pass in GitHub CI; **actual in-game right-click visibility, selector behaviour, and reputation effects require in-game testing**.

Separate issue from the attached November 12 log: Builders 1.75 raises 40 fractional-cent conversion warnings, and the installed 1.02 Auto-Drones code logs 97 zero-error scans under ERROR. The latest Builders and Drone packages should be checked independently; this camouflage extension does not patch them.
