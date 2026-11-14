# Faction Command

An original, offline-first space faction management game for Android landscape,
built with Godot 4. The authoritative design is [Faction Command.md](../Faction%20Command.md).

## Station population accounting and future habitation

**The first population ledger is implemented; residential habitation and
education remain designs, not playable mechanics.** Open **Population** in
Your Property to see counted available resident workers at each NPC station,
known population across stations, and actual ship crew plus named captains.
The original finite NPC recruitment pools have been converted into matching
station-resident cohorts. Each recruit is one person, not a second population
on top of the old roster. Paid hiring removes workers from their NPC-station
cohort when they board a ship, and discharge returns those same people.
New construction sites start with zero residents; building modules alone
does not add people, housing capacity or free crew.

New ships from the NPC wharf must also source their bundled captain and crew
from its available **resident workforce** at the time of delivery. If the
wharf has insufficient personnel, the fully paid hull waits instead of
creating fictional people. The player may bring existing ship staff to the
wharf and discharge them, or later use immigration and schools when those
mechanics exist. Existing Pass-23 saves migrate in place without credit,
captain, ship-order or personnel resets.

In later passes, station habitats will provide actual housing and capacity
for households, children, growing adults, trained workers, immigrants and
retirees, with species-compatible life support, upkeep, jobs and morale.
Births will create children rather than instant adult workers; immigration
and staffing transfers will deduct from known populations and require travel.
Housing, teachers and schools will have finite capacity and operating costs.

Future buildable modules include family, urban and adaptive habitats;
community schools, flight academies, navigation colleges, industrial trade
schools, shipyard and engineering institutes, station management and logistics
colleges, research universities, medical and cultural academies, marine and
boarding schools; and clinics, recreation, parks and civic spaces to improve
wellbeing. Training requires actual students, instructors, time, materials,
equipment and funding. Skills include piloting, navigation, research,
engineering, mining, station administration, trade, security, boarding,
medicine, diplomacy, archiving, teaching and civilian services.

See the **Population, habitation, education and professional skills** section
of [Faction Command.md](../Faction%20Command.md) for the full skills matrix,
module catalogue, staffing economics, migration safeguards and ordered
implementation/testing plan. The first resident-worker ledger already reuses the original finite NPC
recruitment pools and preserves the captain/crew careers from Passes 22–23.
The next implementation priority is buildable habitats and supported life
support, not another isolated crew counter. No school, habitat, birth,
immigration or population-growth recipes are playable yet.

## Current foundation

Choose one of four original faction origins when starting a new game. The
preview shows its starting sector and initial relations; the chosen origin is
friendly (+20) and the other three are neutral (0) in this first prototype.
Your ship and credits still belong to your own independent player faction.

The game has a selectable 12-sector starter galaxy and starts with one
player-owned ship, First Light, with a captain and crew. The world starts
paused; Resume and Pause control the simulation. Use the **Your Property**
search field to find owned ships, commissioned stations and active or cancelled
construction sites. Selecting a ship makes it the active command ship for
role changes, queued fly orders, docking, manual trading, archive visits and
station/build supply. All orders and physical cargo belong to that selected
ship; selecting a different ship does not transfer ownership or cancel the
previous ship's orders. Select a station for its production details and
**Open station trade**, or choose a build site and **Manage build site**.
The directory shows property counts and supports case-insensitive matching by
asset name, category, stable ID and sector. It handles additional player-owned
ships already present in a save. The first NPC wharf contracts below can
also produce additional owned ships in normal play.

Select a sector on the map or in the directory, then use **Queue fly order**
for the active ship. Queue additional destinations to visit in sequence.
Resume time to see ships cross connected sectors, currently five ticks
per crossing. Ship details show captain, crew, role, cargo and orders.
Your selection is a UI preference; underlying ship IDs, orders, roles,
stations, credits and save data are unchanged by browsing the directory.

### Ship orders at the NPC wharf

Choose **Order ships** from Your Property. Vellum Foundry in Vellum Gate
currently provides a small, remotely accessible NPC assembly berth. The first
catalogue has a **Courier** (4,000 CR, 12 Alloy Plates, 24 build ticks and 50
cargo capacity) and a **Freighter** (8,500 CR, 30 Alloy Plates, 48 ticks and 180
cargo capacity). The quoted fee includes contract crew and an initial pilot.
Placing an order is confirmed before credits move. The wharf must already have
the required physical alloy in stock; payment transfers directly to its
operating budget and consumes that stock exactly once. A lack of money or metal
prevents the whole transaction. This prototype uses an alloy-only hull bill;
later shipyards will require more complete components, equipment and workforce.

The wharf handles one ship at a time, with up to five incomplete orders.
Pending contracts, ordered stable ship IDs and construction progress survive
saving, restoring and game pauses. If the NPC wharf becomes unavailable,
production blocks without creating a free vessel or refunding an unfinished
paid order. Once finished, the ship exists at the wharf with the owner's
player-faction identity, its own crew and cargo capacity, full ship automation
controls, and an entry in the property directory and transaction ledger.
Select the new ship there to command or trade with it. Ship contracts cannot
yet be cancelled, and new shipyard construction, modular hull equipment and
player-owned wharf operation are later goals.

### Ship renaming and crew management

Select a player-owned ship in **Your Property**, then choose **Rename / manage
crew**. Rename the selected vessel (1–40 visible characters) without changing
its stable ship ID, captain, orders, cargo or automation. The service crew
are counted separately from the ship's named captain. This first pass sets
capacity by ship class: Couriers have 8 service-crew berths, Freighters 24,
Builders 32, Carriers 80 and other ships 12.

To **Hire** service crew, fly the selected ship to an NPC station and dock
using the normal Trade screen. NPC stations have a finite initial pool of
12 available recruits, retained in the save. Recruitment costs 250 CR per
person and transfers the money directly to the hiring station; it does not
create additional station personnel or silently replace existing crew.
Hiring fails if there are insufficient credits, berths or recruits, or the
station's faction is hostile. **Discharge** returns people to that NPC
station's roster without refunding their hiring fees. **Transfer crew**
moves existing people for free only between two player-owned ships both docked
at the same station with their travel orders finished. Transfer eligibility,
crew quantities and berth capacity are checked before a change is committed.

Hiring, discharge and transfers are recorded in the financial ledger and
save immediately. A ship can have zero service crew while its separately
assigned captain remains aboard.

### Individual captains, training and payroll

Every player-owned ship now keeps a **named captain identity** with its own
piloting experience, skill (level 0–5) and morale (0–100), independently from
the ship ID. Captains earn experience from completed sector crossings and
actual cargo/trade or construction-delivery events; idle time does not produce
free training. The crew has a separate aggregate service-skill and morale
record, with total earned experience conserved when people transfer between
ships. New recruits have no previous earned experience. **Swap captains**
lets two owned ships exchange their named pilots when both are docked at the
same station with no outstanding orders. Each captain retains their personal
experience and morale, without changing either ship's crew, cargo or orders.

Every 60 simulation ticks the player's faction owes **12 CR for the captain,
plus 2 CR per captain skill level, plus 3 CR for each service crew member**.
The prototype sends paid wages to the nominated NPC recruitment agency's
existing station balance; it does not yet create personal NPC credit wallets.
Payments appear in the ordinary financial ledger and preserve total credits
across the simulated economy. With insufficient credits, wages accumulate as
an explicit debt rather than allowing a negative player balance, and unpaid
crew morale decreases five points per payroll cycle. Paying accumulated
arrears plus the current payroll restores the account, with morale recovering
gradually one point per funded payday. Wage records and their precise
simulation clock survive save/reload. If the primary agency station vanishes,
a surviving NPC station can clear the debt; if none exists, wages remain owed.

This pass **records** skill and morale, but they do not yet affect movement
speed, trade results, production, recruitment or job efficiency. Crew remain
aggregate counts rather than individually named NPCs; captain hiring/firing,
training facilities, individual wages, officer ranks, operational crew minimums
and a larger personnel market remain future work.

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
**Automatically supply** to assign the selected player ship. It delivers matching cargo
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
**Trade** and choose **Supply inputs**. Assign the selected player ship and set a maximum
purchase spend for that assignment. The ship uses matching cargo already
aboard, collects surplus from your other stations, or buys from reachable NPC
markets within the allowance. The allowance is a cap, not an upfront payment;
zero permits only carried cargo and your own surplus. The supplier stays on
the job and replenishes inputs as they are used. Targets are based on net
production needs and required reusable sources, so locally produced inputs
are not routinely purchased. Exhausted deposits can create new import needs.
The supplier preserves source stations' working inputs and reusable originals,
respects station storage, and reports why it is waiting. Stop it or change its
role to retain cargo and let queued orders finish. The interface assigns the ship currently selected in Your Property; station output sales are not automated here.

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

Select **Auto trader** under the selected ship's role to automate its supply
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
Shipyard tests cover verified money/ware transfers, full or hostile facilities,
serial construction, per-hull ship roles, a blocked wharf, stable ship identities,
save/load mid-contract, old-save migration, future-version protection and the
end-to-end purchase and command UI.
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
