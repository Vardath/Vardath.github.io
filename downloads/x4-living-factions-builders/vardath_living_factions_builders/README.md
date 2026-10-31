# Vardath - Living Factions and Builders for X4: Foundations

**Status: X4 9.00 experimental release 1.0. Source XML validated, in-game behavior untested.**

This is one standalone extension in two parts:

1. **NPC contracts for player builders (priority):** a player-owned construction ship with **Find Build Tasks** can respond to eligible requests from NPC build storages, if the vanilla script's search range, relations, availability and travel checks permit. After a successful assignment, the mod **attempts** to transfer the normal 50,000-credit hire fee from the requesting faction to the player. Actual payment must be verified in game; do not assume the fee succeeds until tested.
2. **Growing NPC stations:** the vanilla economy manager can request an additional production module during eligible shortage-driven expansions, and request up to three production modules in a newly created factory where formerly it requested one. Common production-module preferred/hard caps are increased to 3/5. Resource supply, builder availability, station designs and faction economy decisions still control whether projects happen.
3. **Player station support:** player-owned stations can broadcast available builder tasks to player builders. NPC builders cannot automatically take a player request outside the normal manual-hire process.

The extension uses **no hard-coded faction IDs**, so it applies to factions that call the vanilla faction economy manager, including supported DLC economies. It does NOT promise that specialized Xenon/Kha'ak or custom faction AI will use standard growth routines; a faction lacking a regular economy manager needs dedicated integration. The extension does not forcibly upgrade every defensive platform or shipyard. The 9.00 staged construction-plan branch remains untouched.

## Installation on Windows

Download the ZIP from the project folder and extract the ONE folder `vardath_living_factions_builders` into:

`C:\Program Files (x86)\Steam\steamapps\common\X4 Foundations\extensions\`

The resulting file must be `...\extensions\vardath_living_factions_builders\content.xml` (no extra nested folder). Enable **Vardath - Living Factions and Builders** in X4's Extensions menu, then restart X4. No DLC is required.

## Use

Give each player builder the **Find Build Tasks** default behavior. Ensure it has construction drones, crew and an unrestricted route to NPC factions with which you can dock. Look for an NPC station already waiting for a builder and with materials in build storage. A contractor ship will respond to the vanilla build request; it will NOT spontaneously select every idle builder or build without materials.

**Important:** take a separate backup save before enabling. Wait for a requesting NPC station, then verify (a) its builder slot is filled by your ship, (b) the ship arrives, (c) construction actually begins, (d) 50,000 credits transfer exactly once. Report any failure with X4 9.00 version and debug log. Station growth can take hours of game time and is triggered by economic conditions.

## Compatibility and limits

- X4 9.00 targeted; untested against later releases.
- The file `aiscripts/order.build.find.task.xml` overlaps other builder dispatch mods such as **Player Builder Autodispatch**. **Disable that mod** while using this extension to avoid duplicated selectors/commands.
- `md/factionlogic_economy.xml`, `libraries/parameters.xml` and `libraries/modules.xml` overlap major economy overhauls such as DeadAir Eco. Avoid combining them until compatibility is validated.
- Does not change construction resources, create builders out of thin air, create unlimited station modules or override all faction build queues.
- The XPath selectors use known 8.x/9.00 modding references but have NOT been checked against an extracted local copy of the latest installed game. If an XPath does not match the exact current game, its feature will not apply. This is a testable initial build, not a claim of completed in-game verification.
- Removing the mod later stops new boosted development; existing physical modules built during play remain in the save.

## Source, credits and licence

Source is in the `vardath_living_factions_builders` folder beside this README. Original adaptation by Vardath, 2026. The player station dispatch and path guard are adapted from **drjele / Player Builder Autodispatch** (MIT). Economic growth hooks are adapted from **DeadAirRT / deadair_eco** and later community adaptations (GPL-3.0). See `ATTRIBUTION.md` and `LICENSE`. Distributed as GPL-3.0-or-later because of the economy hook lineage. X4: Foundations is owned by Egosoft GmbH; no affiliation.
