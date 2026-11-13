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

The galaxy map can be dragged to pan and pinched to zoom; the **+**, **−**
and **Fit** buttons provide an alternative. Select a sector and choose **Open
sector** to see its connections, stations and ships. Tap a connection to open
the neighboring sector, a station to inspect its market and production, or a
ship to see its details. Sector contents are a schematic list for now: the
simulation does not yet track exact positions within a sector. Choose
**Galaxy** to return. The same pan and zoom controls work in both views.

The first manual trading loop has four NPC stations and three wares: Energy
Cells, Ore and Alloy Plates. Open **Trade**, choose a station, travel to its sector and
finish the ship's orders, then dock. Buy goods from station stock and carry them
to a station that buys them. Each transaction changes real cargo, station stock
and both credit balances, and appears in the scrollable transaction ledger. Cargo
space, station storage, stock and budgets are finite. Docking is currently an
immediate sector-level action; prices are fixed.

The first production chain runs on simulation ticks. Solar arrays use the
station's renewable sunlight source to make Energy Cells. An ore extractor
uses Energy Cells and a finite local ore deposit to produce Ore. An alloy
smelter consumes both Ore and Energy Cells to produce Alloy Plates. The Trade
screen shows each station's recipe, progress, shortage or storage blockage, and
remaining deposit. Materials and output move together at cycle completion;
partial progress pauses when inputs or storage are unavailable.

One faction-owned freighter now transports supplies between stations. It is
separate from the player's property: its home station transfers real working
capital, and it buys stock, travels, docks and sells to factories with input
shortages. It checks prices, budgets, storage and routes. If stock disappears
or a buyer cannot pay, it replans or waits with any unsold cargo. Its movements
appear as a diamond on the galaxy map, sector details identify faction traffic,
and the transaction ledger identifies the ship responsible for each entry.

Select **Auto trader** under First Light's ship role to automate its supply
runs. The role spends your faction's credits to buy stock, travels to the
buyer, and returns sale proceeds to your faction. It chooses profitable
factory supply runs using current prices, stock, cargo space, station budgets
and storage. Existing cargo is left alone; the trader sells only the goods it
purchased for its own runs. Both purchases and sales appear in the ledger.
When conditions change it rechecks the deal, finds another buyer or waits
with its cargo. It operates alongside the independent faction freighter.

Manual fly orders join the ship's queue; the trader waits until queued orders
finish, then rechecks its plan. Select **Unassigned** to stop new automated
trades: the current journey still finishes and any purchased cargo stays
aboard. Re-selecting **Auto trader** resumes delivery of that cargo. Manual
sales of the same ware are counted against the trader's cargo first. Role
changes save immediately; in-progress trades and cargo survive save/load.

The game has one local save slot and a manual **Save** button. It also saves
when a game starts, an order is queued, the game is paused or backgrounded,
and every 30 simulation ticks. **Continue saved game** restores the chosen
origin, current relations, credits, crew, tick, and orders, including a crossing
in progress. Games always resume paused. Starting another new game asks before
replacing the slot. A validated previous save is retained as a backup; if the
primary is damaged, Continue offers the backup. A save from an unsupported
version is not silently replaced by an older backup.

Existing trading saves gain production definitions and an empty Ore stock;
existing production saves gain the NPC freighter with an empty wallet. Neither
upgrade resets existing balances, goods, player ships, orders or transaction
history. The NPC receives capital from its home station only after time resumes.

This is an early foundation: there is only one NPC trader; dynamic prices, multiple
save slots, order cancellation, device testing, and the wider management
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
Production tests cover shortages, resumption, finite deposits, capacity, competing
modules, save/load during a cycle and a 2,000-tick run.
NPC logistics tests cover funded travel and deliveries, money conservation,
stock changes, missing or insolvent buyers, lost destinations, migration and
save/load during a trip. Player trader tests also cover manual orders and
intervention, cargo preservation, role changes and save/load in transit.
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

## Android debug builds

The [Faction Command foundation workflow](https://github.com/Vardath/Vardath.github.io/actions/workflows/faction-command.yml)
runs the tests, exports a signed ARM64/ARMv7 debug APK, checks its signature and
package, and uploads `FactionCommand-Android-debug` to the successful run for
30 days. The artifact includes the APK, its SHA-256 checksum and package
information. GitHub may require sign-in to download workflow artifacts.

The APK is a development build using the distinct package ID
`io.github.vardath.factioncommand.debug`. Its debug signing key is deliberately
public and is only for testing; it is not a release key. Keeping that debug key
and package ID stable lets later debug builds install over earlier ones on the
same device. Never use this public key to sign a production release.

To export locally, use Godot 4.4.1 with matching export templates, OpenJDK 17,
and the Android SDK platform tools and build tools 34.0.0. Configure the Java
and Android SDK paths in Godot's Editor Settings. Decode the public test key
to a temporary location, then provide it through Godot's debug-keystore
environment variables and run the Android Debug export preset:

```sh
base64 --decode faction-command/build_support/public-debug.keystore.b64 > /tmp/faction-command-debug.keystore
export GODOT_ANDROID_KEYSTORE_DEBUG_PATH=/tmp/faction-command-debug.keystore
export GODOT_ANDROID_KEYSTORE_DEBUG_USER=factioncommanddebug
export GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD=android
mkdir -p faction-command/build
godot --headless --path faction-command --editor --quit
godot --headless --path faction-command --export-debug "Android Debug" "$PWD/faction-command/build/FactionCommand-debug.apk"
```

The debug key and package ID must stay unchanged for an in-place update. A
passing CI export is not proof of Android gameplay or performance: the APK
still needs installation and playtesting on a physical device.
