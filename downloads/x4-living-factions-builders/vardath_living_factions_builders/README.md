# Vardath - Living Factions and Builders for X4: Foundations

**v1.1 experimental — X4 9.00. Automated ZIP/XML checks pass when the associated GitHub Actions workflow is green; no in-game verification has been performed.**

## What the mod does

### NPC faction build requests to YOUR construction ships

Every **five in-game minutes**, `md/vardath_faction_build_requests.xml` scans stations across the galaxy, including those owned by installed DLC factions, and looks for a genuine construction project that is **already waiting for a construction vessel**. It then reissues X4's own `request construction vessel` signal to suitable player-owned XL construction ships whose current order is **Find Build Tasks**.

This supplements the vanilla construction site's short-range request search, so a player builder does not have to be within the native five-gate scan at the precise time a request first occurs. On receipt, the **unchanged vanilla handler's normal range, permitted-route, relation, and availability checks** still apply, so the builder may decline distant or restricted work. The mod does not forcibly take control of idle/manual-command ships.

The NPC station must have a real queued construction job and be ready to construct. A project lacking necessary resources will not recruit a builder prematurely. The first builder that accepts receives the existing assignment, preventing duplicate bookings. The AI-script patch attempts to transfer **50,000 Cr** from the requesting NPC faction to the player after successful assignment; this payment still needs confirmation in game.

### Station growth

Vanilla shortage-driven faction economy logic requests additional production expansion and creates larger initial factories, within module compatibility limits. This covers factions using the standard economy manager, including DLC factions added to the same system. Xenon, Kha'ak, scripted/custom construction systems, plot-only stations and factions not using that manager are not guaranteed to grow.

### Player stations

A player station can also broadcast a construction request to player builders. NPC builders cannot automatically take those player requests without the normal hiring flow.

## Installation

Download **[v1.1 ZIP](../vardath_living_factions_builders_v1.1.zip)** and extract the **`vardath_living_factions_builders`** directory to your game's extension directory, usually:

`C:\Program Files (x86)\Steam\steamapps\common\X4 Foundations\extensions\vardath_living_factions_builders\`

Check that `content.xml` is immediately inside this directory (not doubly nested). Restart X4; enable the extension under Extensions. No DLC is required, but the mod's minimum game version is 9.00.

## In-game check

1. Back up your save; start the game with at least one player-owned XL construction ship with a pilot, construction drones and **Find Build Tasks** as its active default order.
2. Check that its travel blacklist and maximum gate range allow routes to friendly NPC faction stations.
3. Find a non-player station with a queued build, adequate build resources and no construction vessel assigned. The extra broker checks the galaxy every five in-game minutes.
4. Verify that your builder receives a real deployment order, attaches to that NPC project, travels and begins building. Verify the transfer of 50,000 Cr **once**, not every periodic scan.
5. If it does not work, capture the X4 debug log (`-debug scripts`) and the source station/ship details. Structural validation alone does not test X4's live Mission Director event or AI handler.

**Status:** The request broker and the existing AI changes have not yet been run against an installed X4 game, so any schema-runtime errors, unreachable jobs, and the payment need in-game verification. The mod is source-complete as an initial implementation, not a proven stable release.

## Compatibility, performance, known limits

- Target: X4 9.00. Source uses vanilla-derived 9.00 patterns and contemporary X4 community examples. The 9.00 game's exact installed files and XSDs were unavailable for direct replay validation.
- NPC jobs are **requested**; the normal order's range, sector blacklist, docking relations and pilot availability still decide whether they are accepted. No new jobs are invented when faction stations have no build queued.
- Every five minutes, a single galactic station query runs **only if the player owns a functioning XL builder**. The inner dispatch loop is restricted to NPC stations actually waiting for a CV and to player builders with the proper FindBuildTasks order.
- Disable **Player Builder Autodispatch** while testing: it also patches `aiscripts/order.build.find.task.xml` and `aiscripts/build.buildstorage.xml`.
- Avoid other faction economy overhauls such as DeadAir Eco during the first test because of overlapping XML patches.
- No free station modules, no creation of additional construction ships, no bypass of building materials, and no changes to manual builder orders. Any construction already completed remains part of a save after uninstalling.

## Credits / licensing

Made for Vardath in 2026; GPL-3.0-or-later. Dispatch guard and player build-storage request based on drjele/Player Builder Autodispatch (MIT); economy hook patterns based on DeadAir Eco (GPL-3.0) and later 8.x migration. See LICENSE and ATTRIBUTION.md. X4 is owned by Egosoft GmbH.
