# Vardath - Faction Camouflage 1.02

## Installation

Requires X4: Foundations 8.00+, SirNukes Mod Support APIs (`ws_2042901274`) for the right-click and selection menu. Extract this archive to the **X4 Foundations game directory**, merging `extensions/vardath_faction_camouflage`. Existing save compatible; no new game or ship refit.

## Operation

Right-click **any operational player-owned ship** on the map and choose **Select faction camouflage...**. Pick a native faction from the list. To disable, use **Drop faction camouflage** on the same ship's map menu or **Use my real faction** in the picker. The selected ship stays player-owned. Original ship selection, orders, crews, equipment and storage are unchanged.

Uses the native X4 `md.Cover.TriggerCover` cue for setting and dropping a ship's cover, so combat exposure, scans, story missions and reputation consequences continue to be handled by the game. Cover can be lost during combat; the mod does not restore it automatically or manipulate faction reputation. Vanilla player-controlled-ship cover may be removed on changing controlled ship.

## Diagnostics

The 2026-11-12 07:26 log confirms V1.01 loaded without any explicitly named camouflage script errors. The new generic V1.02 selector has only static verification, not a live X4 test. The game remains responsible for whether a particular ship/faction combination can actually maintain cover.
