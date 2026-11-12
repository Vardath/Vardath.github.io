# Faction Command — Master Game Design and Development Plan

Version: 0.2 | Status: approved concept, implementation pending | Target: Android landscape, offline-first

## Vision
Faction Command is an ORIGINAL 2D, map-driven space economy and faction management simulation inspired by the depth of space trading/empire games. It must not copy X4: Foundations code, art, text, faction/sector/ship names, maps, or distinctive UI assets. The player commands a faction rather than manually pilots ships. Gameplay centers on strategic map navigation, property management, individual ship orders, automation, production, diplomacy, policing and autonomous battles.

## Non-negotiable gameplay
- Start with one owned ship, modest credits and crew; grow through trade, mining, missions and production into stations, shipyards, fleets and territory.
- All player-owned property appears in a searchable, filterable tree: ships, stations, fleets, construction, and subordinate groups. Select any asset to inspect orders, inventory, equipment, crew, finances and behavior.
- No manual piloting. Player directs ships by map click/tap and context menus. Ships travel and fight autonomously. Pause and issue orders; adjustable simulation speed.
- Individual orders include fly to, dock, buy/sell, transfer cargo, mine, salvage, explore, scan, escort, attack, defend, patrol, police, repair, refit, recruit, board (where permitted), construct, and retreat. Persistent order queues; interrupt/resume; repeat and conditional orders.
- Selectable ship roles/standing behaviors: sector/local/galaxy trader, miner, salvager, explorer, surveyor, mapper, taxi, tour operator, courier, builder, supply ship, patrol, police/inspector, escort, bounty hunter, rescue, hacker/intelligence, fleet support, military roles. Each uses real targets, travel, cargo, costs and payouts, not passive income fabrication.
- Hire/fire/transfer/promote/train captains, pilots, engineers, marines, station managers and service crews; track skills, wages, morale and availability.
- Autonomous combat shown on zoomed sector map: real positions, movement, target selection, weapon ranges/cooldowns, shields/hull, missiles, repair, retreat, boarding, casualties and salvage. Police scan cargo, enforce faction laws, respond to crime and affect reputation.
- Build stations and production chains, logistics networks, shipyards and fleets. NPC factions have budgets, inventories, production, consumption, shipbuilding and territorial objectives; destruction and shortages matter.
- Unified transaction ledger for every asset: purchases, sales, wages, repairs, construction, missions, taxes and profits. Save/load full simulation.

## Galaxy and map
- Target initial authored/procedural hybrid galaxy: ~300 sectors, 20–30 distinct original factions; scalable to more only after performance validation. Start MVP at 12–20 sectors and 4 factions.
- Original sector names, topology, regions, environmental hazards, resources, ownership, laws, infrastructure, gates and contested borders.
- Continuous zoom from galaxy graph to sector 2D tactical view. Galaxy level displays nodes, trade routes, faction territory, filters, mission markers and moving asset indicators. Sector level shows ships, stations, gates, asteroid fields, resource zones, combat and traffic.
- Same underlying simulation for both views; distant objects need not be rendered. Fog of war, sensor range, discovered routes, searchable assets and map overlays.
- Touch gestures: pinch zoom, pan, tap select, long-press context order, multi-select and accessible list alternatives. Keep UI readable on a phone in landscape.

## Economy — authoritative simulation
- Every ware has unit volume, production inputs, outputs, cycle duration, workforce/energy requirements, storage and legal status.
- Mines and energy facilities supply refineries; refineries supply component factories; components and advanced goods feed station construction, shipyards, weapons and equipment; civilian demand and upkeep create sinks.
- Stations maintain finite inventories and credits. Ships transport physical cargo and pay/receive credits; docking, travel time, storage and throughput constrain logistics.
- Pricing responds to stock coverage, demand and regional risk within bounded rules; no arbitrary infinite-money loops.
- NPC traders seek profitable feasible routes; NPC factions invest and expand from actual economic capability. Shortages halt production and slow shipbuilding. Piracy and war disrupt supply.
- Define deterministic production ticks and transaction atomicity; prevent duplicate sales, negative inventories, ghost cargo and save/load exploits.
- Track ware-level stock flow, credit flow, faction solvency, factory utilization and logistics bottlenecks. Include debug economic inspector and repeatable seed scenarios.

## Ship and station model
- Ship classes: scout, courier, fighter, corvette, freighter, miner, salvage, transport, destroyer, carrier, construction vessel. Original hull designs and names; modular engine, shields, weapons, sensors, cargo and drones.
- Ships have position, velocity abstraction, orders, role, captain, crew, fuel/energy if used, cargo, hull/shields, equipment, faction ownership, operating costs and history.
- Stations have modules, production recipes, dock capacity, storage, managers, workers, buy/sell rules, build queues and defense systems.
- Fleet hierarchy supports commanders, subordinates, formation/doctrine, resupply and automatic replacement.
- Shipyards consume components and time to produce real hulls; production slots and equipment stocks matter.

## Factions, law and diplomacy
- 20–30 original factions at full target: governments, corporations, guilds, frontier coalitions, pirates and independents, with distinct doctrines, home sectors, economic strengths and diplomatic relations.
- Reputation, trade permissions, embargoes, patrol jurisdictions, smuggling, contraband, scans, fines, criminal evidence, piracy, escorts, war, peace and territorial claims.
- Policing operates via patrol routes, sensors, scan decisions, legal rules, interception and reputation consequences; avoid omniscient enforcement.
- AI strategic planners make bounded decisions from economic and military state, with tunable difficulty but no mandatory resource cheating.

## Missions and narrative
- Original procedural contracts: deliveries, mining, taxi, tours, construction, escorts, defense, policing, surveys, salvage, humanitarian relief, piracy suppression and faction campaigns.
- Mission generation checks actual demand, reachable locations, stock availability and payer budget; payment on verified completion. Narrative quests must be original.
- Contracts include prerequisites, deadlines, cancellation rules, faction reputation and failure consequences.

## Android architecture
- Recommended: Godot 4, GDScript for UI/prototype; evaluate C# or native modules only if profiling proves necessary. Android landscape, offline-first, no mandatory server.
- Strict separation: deterministic simulation core; command/order engine; presentation/UI; persistence. Avoid tying simulation state to visible nodes.
- Fixed simulation ticks; event-driven jobs and sparse scheduling. Near/active sector receives detailed tactical updates; distant sectors receive coarser economic/strategic updates while preserving aggregate outcomes and consistent arrival times.
- Spatial indexing for nearby interactions; object pooling for visible markers/projectiles; cull offscreen visuals. Do not simulate thousands of rendered ships every frame.
- Battery/performance presets; cap render FPS independently of simulation; pause when backgrounded; autosave safely.
- Save versioning and migration; stable entity IDs; transactional persistence with integrity checks. Offline saves, manual save slots and crash recovery.
- Accessibility: scalable text, color-independent faction identification, readable icons, large touch targets and list-based command alternatives.

## Interface screens
1. Galaxy map and sector zoom.
2. Property tree and asset detail with contextual command queue.
3. Crew hiring, firing, training and transfer.
4. Ship roles/behavior configuration, blacklists, risk and profit thresholds.
5. Cargo, ware trading, station logistics and price history.
6. Station builder and production overview.
7. Fleet doctrine and tactical command.
8. Diplomacy, laws, crime and faction standing.
9. Missions and contract tracking.
10. Ledger, profit/loss, asset history and economy diagnostics.
11. Save/load, speed and graphics/battery settings.

## Implementation phases and acceptance criteria
### Phase 0 — Foundation
Create Godot project, repository game directory, data schemas, original naming conventions, Android export pipeline, automated lint/tests and deterministic headless simulation harness. Confirm a signed development APK can install and launch on a real Android device.

### Phase 1 — Vertical slice
12–20 sectors, 4 factions, 6–10 wares, 4–6 ship classes, 3 production chains. One player ship; property list; map pan/zoom; ship selection and order queue; docking, buy/sell, mining, production, autonomous traders, credits, ledger and save/load.
**Pass:** player can order a ship to buy and deliver ware; actual inventory and credits change exactly once; simulation survives save/reload.

### Phase 2 — Economic depth
Expand wares, factories, station construction, player-owned stations, workforce, logistics AI and NPC budgets; shipyards consume real materials and build ships.
**Pass:** deliberate disruption creates observable shortage, price response and production slowdown; restoring supply recovers output.

### Phase 3 — Security and combat
Sector tactical view, autonomous combat, equipment, fleet orders, police, contraband, reputation, escort and pirate AI.
**Pass:** orders and combat outcomes remain consistent offscreen; law enforcement uses actual detection and jurisdiction.

### Phase 4 — Occupations, quests, diplomacy
Ship role framework, civilian occupations, contract generation, campaigns, faction diplomacy and territorial expansion.
**Pass:** automated roles complete real journeys/contracts, transfer passengers/cargo where applicable and receive ledger payments only on verified completion.

### Phase 5 — Scale and release
Expand toward ~300 sectors and 20–30 factions with procedural variety and authored landmarks; optimize for Android; balance economy; original art/audio; accessibility; APK release.
**Pass:** defined representative Android device runs a sustained simulated campaign without major tick backlog, save corruption or unacceptable battery drain. Establish measured FPS, memory, CPU and battery targets after device profiling.

## Test and CI requirements
- Unit tests: recipes, cargo conservation, credit conservation (except explicit sources/sinks), prices, legality, role transitions, crew transfers, order interruption, save migrations.
- Integration tests: mine → refine → manufacture → shipyard, trader routes, combat destruction, policing, missions, faction shortages.
- Deterministic long-run soak tests with fixed seeds; detect deadlocks, runaway inflation, negative stock, orphaned orders, impossible routes, duplicate payouts and entity leaks.
- GitHub Actions: validate project/assets, run headless tests, export Android debug APK, publish CI artifacts; release signing secrets must never be committed.
- A green CI build is not proof of gameplay correctness; require on-device playtesting and scenario tests.

## Repository workflow
- This document is the authoritative design baseline at repository root: `Faction Command.md`.
- Put game source under `faction-command/` so website files remain unaffected.
- Maintain milestones/issues, small reviewable commits, tests, versioned changelog and reproducible Android build instructions.
- Do not silently replace features or claim completion without passing relevant tests. Update this document when scope decisions are approved.
- GitHub stores code and build artifacts; Godot and Android export tools perform compilation, while CI automates checks and builds.


## List-based station construction and self-sufficiency planner
- The station builder is a mobile-friendly list of module types with quantity controls, rather than a manual 3D assembly puzzle. The player chooses production modules, storage, docks, housing, defenses, shipbuilding and support modules and enters quantities. New stations and existing station expansions use the same planner.
- Three resource-sourcing modes per station: **Fully self-sufficient**, **Import selected inputs**, and **Import all inputs**. The partial-import mode exposes each required ware as a toggle and permits per-ware import quotas, supplier restrictions and maximum purchase price.
- Player chooses target final output wares and desired production modules or output rate. The planner recursively expands the recipe dependency graph, calculates required intermediate production, mines/extractors, power, workforce, storage and docks, then rounds to whole modules. It must handle shared intermediates across multiple outputs, production cycle rates, alternative recipes, recycling and cyclic dependencies; cycles require explicit resolution or a warning, never infinite recursion.
- Self-sufficient means all *manufacturable* recurring inputs are produced locally at sufficient throughput; natural resources still require accessible local deposits/collectors. Warn if the sector lacks a resource or if workforce/energy is insufficient; offer import exceptions or alternative sites.
- For imported wares, omit their upstream production modules and calculate expected import throughput, transport capacity, running cost and exposure to shortages. Mixed sourcing must permit local production plus imports for a single ware.
- Planner previews module bill of materials, credit cost, estimated build time, required construction deliveries, per-minute inputs/outputs, workforce, power balance, storage days, expected profit and bottlenecks. Estimates must clearly distinguish current market prices from guaranteed prices.
- Construction is a persistent queued process: reserve budget/resources, obtain a builder, deliver physical materials, complete modules in sequence, and update station production when commissioned. No instant free modules. Allow pause, reorder, cancel with defined refund/salvage rules, and save/load mid-build.
- The player can assign station managers and subordinate traders/miners, define trade rules and budgets, enable auto-purchase of build materials, and expand stations later. NPC factions use the same module economics and construction constraints.
- MVP implementation: module selection and quantities, dependency calculation for three production chains, preview, construction queue and persistence. Later: full mixed sourcing, shared inputs, workforce, advanced station logic and shipyards.
- Acceptance tests: (1) self-sufficient plan covers all required recurring inputs at target rate; (2) import-all adds no unnecessary upstream factories; (3) selective imports remove only the correct dependency branches; (4) shared inputs are not double-counted; (5) missing resources and recipe cycles yield actionable warnings; (6) construction consumes materials/credits exactly once and survives save/load.

## Development progress and mandatory green-commit gate
- Maintain a separate repository-root file **`Faction Command Progress.md`** as the durable, chronological implementation journal. Each development pass records scope, files changed, commits, tests run, results, known defects, remaining work and the next permitted task.
- Before moving from one implementation task to the next: push/commit the task, inspect the corresponding GitHub Actions check runs for the actual commit SHA, wait for required workflows to finish, and verify **green/success**. A created commit alone is not verification.
- If checks are red, pending, missing or cannot be inspected, **do not proceed to the next implementation task**. Record the exact blocker in the progress file and fix the current task or request the necessary access. Never report green without observing the check results.
- Keep CI checks scoped to the game directory so existing website functionality is not inadvertently broken. Do not equate a green CI result with verified Android gameplay; retain real-device acceptance tests.

## Immediate next tasks
1. Establish original lore, faction list and sector-generation schema.
2. Implement Godot project skeleton and mobile navigation/property UI.
3. Implement deterministic economy simulation and test harness.
4. Implement order queues, autonomous ship navigation and cargo trading.
5. Configure GitHub Actions for Android debug builds and test on a physical device.

## Current design decisions
- Strategic management, **no manual piloting**.
- Galaxy map with zoomable 2D sectors and visible autonomous battles.
- Individual property commands, crew management and selectable autonomous ship occupations.
- Real shared economy for player and NPC factions.
- Bigger galaxy and more factions than a typical initial prototype, contingent on performance.
