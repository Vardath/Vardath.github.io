# Faction Command

An original, offline-first space faction management game for Android landscape,
built with Godot 4. The authoritative design is [Faction Command.md](../Faction%20Command.md).

## Current foundation

Choose one of four original faction origins when starting a new game. The
preview shows its starting sector and initial relations; the chosen origin is
friendly (+20) and the other three are neutral (0) in this first prototype.
Your ship and credits still belong to your own independent player faction.

The game has a selectable 12-sector starter galaxy and one player-owned ship
with a captain and crew. The world starts paused; Resume and Pause control the
simulation. Select a sector on the map or
in the directory, then use **Queue fly order** to send First Light there. Queue
additional destinations to visit them in order. Resume time to see the ship
cross connected sectors; each crossing currently takes five ticks. Selecting
the ship shows its captain, crew, location and pending destinations.

The first manual trading loop has four NPC stations and two wares: Energy Cells
and Alloy Plates. Open **Trade**, choose a station, travel to its sector and
finish the ship's orders, then dock. Buy goods from station stock and carry them
to a station that buys them. Each transaction changes real cargo, station stock
and both credit balances, and appears in the scrollable transaction ledger. Cargo
space, station storage, stock and budgets are finite. Docking is currently an
immediate sector-level action; prices and starting inventories are fixed, and
the stations do not yet produce or restock goods.

The game has one local save slot and a manual **Save** button. It also saves
when a game starts, an order is queued, the game is paused or backgrounded,
and every 30 simulation ticks. **Continue saved game** restores the chosen
origin, current relations, credits, crew, tick, and orders, including a crossing
in progress. Games always resume paused. Starting another new game asks before
replacing the slot. A validated previous save is retained as a backup; if the
primary is damaged, Continue offers the backup. A save from an unsupported
version is not silently replaced by an older backup.

This is an early foundation: production, NPC traders, dynamic prices, multiple
save slots, order cancellation, Android export, and the wider management
systems remain to be implemented.

The scenario data is in `data/starter_galaxy.json` (schema version 1), including
data-driven origin sectors and standings; sector links are undirected pairs of
stable sector IDs. `scripts/world.gd` owns the
starting state, whole-tick clock, deterministic route search and queued ship
movement independently from the UI. The test harness checks scenario integrity,
connectivity, travel timing and order queues, deterministic tick batching,
isolation of snapshots, save integrity and backup recovery, and basic screen
interactions. Trading tests cover conservation of credits and goods, failed
transactions, storage limits and upgrading older saves without resetting progress.
The versioned local save wraps an object-free serialized world in a
checksum-protected envelope. Tests use a unique temporary save directory.

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
