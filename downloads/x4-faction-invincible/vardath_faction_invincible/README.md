# Vardath - Player Faction Invincible 1.03 (X4: Foundations 9.00)

**1.03:** Gate and highway-entry-gate components are explicitly excluded *before* checking defensibility or applying health/minimum commands. Previously saved gate entries are removed from this mod’s tracking table without attempting to modify their hull or shields. This is a conservative guard for the 100 non-defensible gate construction-site errors still appearing every in-game minute in the 12 November 22:20 log. It leaves player ships, genuine stations, and other eligible deployables protected; requires live X4 verification.

Independent, **always-on** invincibility for the entire player faction. No menu, toggle, required DLC, or changes to the other Vardath X4 mods.

## Function

Every in-game minute, the Mission Director searches the galaxy for player-owned ships, stations and deployables (satellites, mines, laser towers and beacons). It repairs hull and shields to **100%** and sets their minimum hull and shield limits to **100%**. The minimum limits protect against destruction between scans: periodic regeneration alone cannot prevent a lethal hit.

The same protection is re-applied to engines, shields, weapons, turrets and individual station modules, including newly fitted/built components. Newly purchased, built or captured assets receive protection on the next scan (up to roughly one in-game minute). The first scan runs when the MD cue is first checked; exact timing depends on X4.

When an asset stops being player-owned, the next scan removes this mod's minimum protection from that asset and surviving components. Previously restored health stays restored. State is stored in the save.

## Install

Download and extract the `vardath_faction_invincible_TEST.zip` archive. Put its single `vardath_faction_invincible` folder inside your `X4 Foundations/extensions` directory, so that `extensions/vardath_faction_invincible/content.xml` exists. Enable it in the game's Extensions menu and restart. Back up a save before testing.

This is a standalone unpacked XML extension; there is nothing to compile. No DLC dependency.

## Limitations

**Static XML checks passed; X4 9.00 game testing is still required.** Confirm that hull and shield minima work on ships, station modules and deployables, and that shieldless objects produce no script errors. Forced mission despawns, script deletions and some environmental or story mechanics can bypass ordinary combat damage. A newly built asset can be destroyed before its first scan. On very large empires the per-minute component search may cost some performance.

If you intend to uninstall, keep a pre-mod save; simply removing an MD script may not reset minimum-hull/shield properties already serialized into a save.
