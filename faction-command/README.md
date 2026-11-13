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

The starter economy has four markets and four historical archives. Its wares
include Energy Cells, Ore, Alloy Plates, Blank Media, Recorded Data and Research
Notes. Open **Trade**, choose a station, travel to its sector and
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

**Plan station** designs a station in the selected sector. Choose production
modules and quantities, then choose **Self-sufficient**, **Import selected
inputs**, or **Import all inputs**. The planner calculates supporting modules,
shared input rates, the builder fee, construction materials and work time.
It warns if an ore deposit is absent or finite. The estimate does not include
the purchase price of materials or builder travel time.

Choose **Place build site** to pay the quoted fee to the independent builder
Keystone and create an empty player-owned plot. Buy Alloy Plates from an NPC
market, fly them to the plot's sector, open **Stations & builds**, dock at the
site and choose **Deliver materials**. Alternatively, select the site and use
**Automatically supply** to assign First Light. It delivers matching cargo
already aboard, then collects from your own station stock or buys from a
reachable NPC market with your faction's credits. It physically travels and
makes multiple trips if needed, showing when it waits for stock, credits or
cargo space. When the materials are delivered, the ship returns to an
unassigned role. Stop supply from the build screen or change the ship's role;
its current orders finish and any cargo stays aboard. Queued orders also finish
before a new supply assignment starts. The builder travels to supplied sites
and consumes physical build storage as each module starts. Modules finish over
time and immediately become working production with their own storage. Pause
or resume a build from the same screen. The builder fee is initially paid upfront. **Cancel unfinished construction**
on the Stations & builds screen to refund the exact fees for never-started
modules from the builder's actual wallet. A module that already began keeps
its committed materials and finishes before the builder leaves; previously
completed modules remain operational. The cancellation stops build suppliers
without cancelling their queued travel or taking their cargo. No more modules
start on that plot. Delivered but unused construction materials stay in
separate physical build storage. Dock one of your ships at the cancelled
plot and choose **Recover unused materials** to transfer as much as its cargo
capacity permits; repeat with available space until the stock is empty.
Fees and physical recoveries are recorded in the transaction ledger.
A cancelled empty plot remains on the property list as a recovery location;
plot demolition is not yet implemented. To change construction priority, open
**Stations & builds**, select a module in the queue and choose **Move up** or
**Move down**. Only modules which have not begun consuming materials can move;
completed modules and the currently building module are locked. Reordering
does not alter fees, stock, cargo, builder travel or the module bill of
materials. The revised sequence is saved immediately and survives loading.
Build storage cannot be consumed by production. The ship uses only surplus
from your stations, preserving their working inputs and reusable sources.

At your own station, **Trade** offers free cargo transfers instead of buying
from yourself. Player stations in the same sector share a finite ore reserve:
Hearthreach starts with 240 units, Lantern Deep 400, Cinder Veil 600 and Copper
Wake 1,000. These are separate from existing NPC station deposits. All starter
sectors have sunlight. Plans that have not been placed are not saved.

For ongoing production inputs, open one of your completed stations through
**Trade** and choose **Supply inputs**. Assign First Light and set a maximum
purchase spend for that assignment. The ship uses matching cargo already
aboard, collects surplus from your other stations, or buys from reachable NPC
markets within the allowance. The allowance is a cap, not an upfront payment;
zero permits only carried cargo and your own surplus. The supplier stays on
the job and replenishes inputs as they are used. Targets are based on net
production needs and required reusable sources, so locally produced inputs
are not routinely purchased. Exhausted deposits can create new import needs.
The supplier preserves source stations' working inputs and reusable originals,
respects station storage, and reports why it is waiting. Stop it or change its
role to retain cargo and let queued orders finish. The interface currently
assigns the single starter ship; station output sales are not automated here.

Each NPC faction maintains a historical archive station in its starter sector.
Select its sector, choose **Open sector**, tap the archive, dock and choose
**Read historical records**. The starter collection has five entries per
faction, with books, tablets, tapes, crystals, discs and light drives among the
catalogued formats. Archive subjects can contribute to matching research
projects. A visit is saved, and the records remain readable on site even when
upkeep is short.

Faction sponsors transfer existing funds into archive operating budgets.
Archives buy physical energy and alloy, pay staff from their budgets, consume
energy for upkeep and report shortages. Their media workshop uses alloy and
energy to make Blank Media, and their scriptorium uses blank media and energy
to produce Recorded Data copies from the retained historical collection.
Sources are never consumed when copied. Traders and the player can supply
archives and buy recorded copies when stock is available.

Players can build their own **Media Workshop** and **Archive Scriptorium**
using the station planner. A player scriptorium needs at least one Recorded
Data unit in its station storage as a reusable source, plus blank media and
energy for each copy. The current two wares aggregate formats and source
civilizations; they do not yet represent individual books, provenance or a
player-managed catalogue.

Build a **Research Laboratory** through the station planner and supply it with
Recorded Data and Energy Cells. It produces one Research Note per cycle. Open
your station in **Trade**, choose **Research projects**, and assign a project
to that laboratory. Each note consumed adds two progress, plus one for each
distinct relevant archive you have visited, up to two extra. The project screen
names the relevant archives and shows the current contribution. Visits are
references learned by the player; the aggregate data ware does not yet track
which archive a particular copy came from. You can pause or switch projects
without losing their progress. Completing the first projects makes your own
scriptoria, media workshops or ore extractors work faster; NPC stations retain
their existing rates. The station planner and production reports show the new
rates, and the normal inputs and finite deposits are still required.
If a laboratory and a scriptorium share a station, the last data copy needed
as the scriptorium's reusable source is reserved automatically.

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
Older saves also gain the NPC builder and sector resources, without a fee or a
new build site. Existing construction saves gain the inactive supply role;
in-progress construction, cargo, builder travel and supply trips are saved.
Older saves gain the archive stations and data recipes with empty new stocks;
they also gain an inactive research system. No existing credits, cargo or
production are reset. Existing saves also gain an inactive station-supplier
role without changing their current orders or cargo.

This is an early foundation: there is one NPC trader and one NPC builder;
automated station output sales and cancelled-plot removal,
dynamic prices, source-specific collections, expanded research and prerequisites,
multiple save slots, device testing and wider management systems remain to be
implemented.

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
Construction tests cover paid builder travel, physical deliveries, resource
sharing, paused and resumed builds, completed production, cancellation of
unstarted and actively building modules, exact fee refunds, dockside material
recovery, interrupted suppliers, safe reordering of unstarted modules,
construction save schema migration and saving mid-construction. Supply tests cover real purchases, limited cargo, waiting and
resuming, role changes, competing ships and saving during supply trips.
Archive tests cover funding, maintenance, visits, media manufacture, retained
copy sources, player-built data production, migration and save/load.
Research tests cover lab construction and inputs, relevant archive references,
project progress and pausing, real upgrade effects, migration and save/load.
Station supply tests cover purchase limits, physical deliveries, working-stock
protection, changing shortages, competing ships, role changes and save/load.
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
