# GalaxyTrader MK3 Fleet UI Table Hotfix — X4 9.00

**Opt-in drop-in for GalaxyTrader MK3 v1.0.4 (November 7, 2026).** Does not modify Vardath's other mods, underlying trade AI, crew, ships or saved orders. This release updates only the GalaxyTrader Fleet View UI code.

## Source-confirmed fault addressed

The Fleet View reserves seven fixed-width widget columns (six action icons and a selection checkbox), even when X4's Map information panel supplies only 438 layout units. The supplied debug log states `reserveScrollBar: width available=438, required=444`, then reports negative font widths, and an absent content element at row 12, column 8, causing the Map info frame to abort.

The Fleet View source also leaves the action cells of non-selected rows empty and, when vanilla XP disables the Academy action, can leave an unfilled action slot on the selected row.

## Patch behaviour

- Computes whether the information panel has sufficient space for its icons and four minimum text columns.
- **Narrow panels:** show a compact five-column fleet list (ship, role, pilot, home, selection). The six shortcut action buttons and wide 8-column filtering toolbar are hidden in this compact presentation; the normal GalaxyTrader/ship context menu actions remain available. Details and ship selection remain.
- **Wide panels:** retain the existing buttons, controls, filters, and detail panels.
- In wide mode, explicitly create blank text spanning unused action columns, preventing nil cells in the native X4 table renderer.
- No core trading scripts, orders, reputation, payouts, UI Extensions framework, or Egosoft UI files are changed.

## Installation

1. **Exit X4 and back up your saves.** This modifies a third-party UI file, not your saves.
2. Locate the installed GalaxyTrader folder, which the game log calls `extensions/galaxy_trader`. For your Windows installation it should be under the X4 game directory. Workshop installations sometimes use another physical location; use the actual folder supplying that extension.
3. Back up `ui/gt_fleet_view.lua` if it exists as a loose file.
4. Extract `GT_Fleet_UI_Hotfix_1.0.zip` into the same X4 game directory **only if the installed GalaxyTrader extension really is at** `extensions/galaxy_trader`. The ZIP contains `extensions/galaxy_trader/ui/gt_fleet_view.lua`.
5. Start X4 and open the GalaxyTrader fleet overview and ordinary Map information panels. Check whether the malformed-cell/width error recurs.

**Steam Workshop may overwrite the loose file during updates.** If the game loads a packed catalog before the loose override, the patch may not take effect; verify using a new debug log. The patch assumes the public upstream Fleet View source is equivalent to the v1.0.4 Steam build.

**Rollback:** close X4 and restore the backup of `gt_fleet_view.lua`, or delete the newly added file if there was no loose original.

## Provenance and scope

Based on upstream GoAhead-at/galaxy_trader_v9 commit `c6d3c9a36b6dea974babb79ef66f3903e978bc83`, file blob SHA `35299b8a1ede08db848f739ccbd927a35006cd8c`. Source is MIT licensed; original LICENSE is included with attribution.

Automated CI validates Lua 5.1 syntax, exact package members and the responsive/blank-cell source contracts. **There is no runtime X4 test here and the log does not prove GalaxyTrader caused every interface problem.** Other Map UI mods, especially UI Extensions callbacks, can still cause errors. For too-narrow standard Map panels, adjusting **UI Scale** down or using the third-party **Info Panel Width** mod to enlarge panels may also help; do not add further UI mods until first testing this narrow repair.
