# Faction Command

An original, offline-first space faction management game for Android landscape,
built with Godot 4. The authoritative design is [Faction Command.md](../Faction%20Command.md).

## Current foundation

The project opens to a selectable 12-sector starter galaxy, four original NPC
factions, and one player-owned ship with a captain and crew. The world starts
paused; Resume and Pause control an integer tick counter. Sector details can be
selected on the map or from the directory; selecting the ship displays its
details. This is a foundation, not yet a playable economy: navigation, orders,
trading, save/load, Android export, and the wider management systems remain to
be implemented.

The scenario data is in `data/starter_galaxy.json` (schema version 1); sector
links are undirected pairs of stable sector IDs. `scripts/world.gd` owns the
starting state and deterministic whole-tick clock, independently from the UI.
The test harness checks scenario integrity, connectivity, deterministic tick
batching, isolation of snapshots, and basic screen interactions.

## Run and test

Open `faction-command/project.godot` in Godot 4.4 or newer and press Run.
The project targets landscape and uses the compatibility renderer. From the
repository root, using a Godot 4 executable:

```sh
godot --headless --path faction-command --editor --quit
godot --headless --path faction-command --script res://tests/run_tests.gd
```

CI uses the official Godot 4.4.1 Linux executable. Android export templates,
SDK setup, an APK and actual device testing are future foundation work; a
passing headless test is not proof of Android gameplay or performance.
