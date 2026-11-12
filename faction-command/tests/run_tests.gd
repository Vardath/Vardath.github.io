extends SceneTree

const WorldScript = preload("res://scripts/world.gd")
const SaveStoreScript = preload("res://scripts/save_store.gd")
const MainScene = preload("res://scenes/main.tscn")

var failures: Array[String] = []
var checks := 0


func _initialize() -> void:
	call_deferred("_run")


func _expect(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		printerr("FAIL: " + message)


func _total_credits(state: Dictionary) -> int:
	var total := int(state.starting_credits)
	for station in state.stations:
		total += int(station.credits)
	for ship in state.ships:
		if ship.owner != state.player_faction_id:
			total += int(ship.get("credits", 0))
	return total


func _disable_npc_trading(world: RefCounted) -> void:
	for ship in world.state.ships:
		if ship.has("autotrader"):
			ship.autotrader.enabled = false


func _without_player_role(ship: Dictionary) -> Dictionary:
	var copy := ship.duplicate(true)
	copy.erase("player_trader")
	return copy


func _total_ware(state: Dictionary, ware_id: String) -> int:
	var total := 0
	for station in state.stations:
		total += int(station.stock.get(ware_id, 0))
	for ship in state.ships:
		total += int(ship.cargo.get(ware_id, 0))
	return total


func _run() -> void:
	# A unique isolated directory prevents tests from ever touching a player's save.
	var test_root := "user://fc-test-%s-%s" % [OS.get_process_id(), Time.get_ticks_usec()]
	_expect(DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(test_root)) == OK, "isolated test save directory is created")
	var first = WorldScript.new()
	var second = WorldScript.new()
	_expect(first.load_starter() == OK, "starter galaxy loads")
	_expect(second.load_starter() == OK, "a second independent galaxy loads")
	if first.state.is_empty() or second.state.is_empty():
		quit(1)
		return

	_expect(first.state.schema_version == 1, "starter schema is versioned")
	_expect(first.state.sectors.size() == 12, "starter contains 12 sectors")
	_expect(first.state.factions.size() == 5, "starter contains player plus four NPC factions")
	var player_ship_count := 0
	for ship in first.state.ships:
		if ship.owner == first.state.player_faction_id:
			player_ship_count += 1
	_expect(player_ship_count == 1, "player starts with one independently owned ship")
	_expect(first.state.ships.size() == 2, "starter galaxy also contains one NPC trader")
	_expect(first.state.starting_credits > 0, "player starts with credits")

	var faction_ids: Dictionary = {}
	for faction in first.state.factions:
		_expect(not faction_ids.has(faction.id), "faction IDs are unique: " + str(faction.id))
		faction_ids[faction.id] = true
	var sector_ids: Dictionary = {}
	var graph: Dictionary = {}
	for sector in first.state.sectors:
		_expect(not sector_ids.has(sector.id), "sector IDs are unique: " + str(sector.id))
		_expect(faction_ids.has(sector.owner), "sector has a valid owner: " + str(sector.id))
		_expect(float(sector.x) >= 0 and float(sector.x) <= 1 and float(sector.y) >= 0 and float(sector.y) <= 1, "sector coordinates fit map: " + str(sector.id))
		sector_ids[sector.id] = true
		graph[sector.id] = []
	var edges: Dictionary = {}
	for link in first.state.links:
		if link.size() != 2 or not graph.has(link[0]) or not graph.has(link[1]):
			_expect(false, "link must connect two valid sectors")
			continue
		_expect(link[0] != link[1], "links do not loop to the same sector")
		var edge: Array = [link[0], link[1]]
		edge.sort()
		var key := "%s|%s" % edge
		_expect(not edges.has(key), "links are unique: " + key)
		edges[key] = true
		graph[link[0]].append(link[1])
		graph[link[1]].append(link[0])
	var visited: Dictionary = {}
	var queue: Array = [first.state.sectors[0].id]
	while not queue.is_empty():
		var current: String = queue.pop_front()
		if visited.has(current):
			continue
		visited[current] = true
		for neighbor in graph[current]:
			if not visited.has(neighbor):
				queue.append(neighbor)
	_expect(visited.size() == sector_ids.size(), "all starter sectors are reachable")
	for ship in first.state.ships:
		_expect(faction_ids.has(ship.owner), "starter ship belongs to a valid faction")
		_expect(sector_ids.has(ship.sector), "starter ship is in a valid sector")
		_expect(not str(ship.captain).is_empty() and int(ship.crew) > 0, "starter ship has a captain and crew")

	_expect(first.state.starting_profiles.size() == 4, "four faction origins are available")
	var seen_origins: Dictionary = {}
	for profile in first.state.starting_profiles:
		var origin: String = profile.faction_id
		_expect(not seen_origins.has(origin), "starting origin is unique: " + origin)
		seen_origins[origin] = true
		_expect(faction_ids.has(origin) and origin != first.state.player_faction_id, "starting origin is an NPC faction: " + origin)
		_expect(sector_ids.has(profile.sector_id), "origin has a valid sector: " + origin)
		for faction in first.state.factions:
			if faction.id != first.state.player_faction_id:
				_expect(profile.relations.has(faction.id), "origin defines relations with " + str(faction.id))
		var origin_world = WorldScript.new()
		_expect(origin_world.load_starter(origin) == OK, "new game starts with " + origin)
		_expect(origin_world.state.player_origin_faction_id == origin, "chosen origin is recorded: " + origin)
		_expect(origin_world.state.ships[0].sector == profile.sector_id, "starting ship is placed in chosen origin sector: " + origin)
		_expect(origin_world.state.ships[0].owner == "player", "ship remains independently owned for " + origin)
		_expect(origin_world.state.relations == profile.relations, "chosen origin's initial relations are applied: " + origin)
		_expect(origin_world.state.sectors == first.state.sectors, "choosing an origin does not change sector ownership: " + origin)
		origin_world.state.relations[origin] = 99
		_expect(profile.relations[origin] != 99, "live relations are independent of profile defaults")
	var unchanged: Dictionary = first.snapshot()
	_expect(first.load_starter("invalid_origin") == ERR_INVALID_PARAMETER, "invalid origin is rejected")
	_expect(first.snapshot() == unchanged, "invalid origin does not overwrite the existing world")

	first.advance_ticks(12)
	first.advance_ticks(25)
	second.advance_ticks(37)
	_expect(first.snapshot() == second.snapshot(), "same world and tick count give identical state regardless of batching")
	first.advance_ticks(-4)
	first.advance_ticks(0)
	_expect(first.state.tick == 37, "zero and negative tick counts do not change time")
	var copy: Dictionary = first.snapshot()
	copy.ships[0].name = "Changed copy"
	_expect(first.state.ships[0].name == "First Light", "snapshots cannot mutate the live world")

	var journey = WorldScript.new()
	var batched = WorldScript.new()
	_expect(journey.load_starter() == OK and batched.load_starter() == OK, "travel test worlds load")
	_expect(not journey.queue_fly_to("ship_001", "hearthreach"), "cannot queue a trip to the current sector")
	_expect(not journey.queue_fly_to("ship_001", "unknown"), "cannot queue an unknown destination")
	_expect(not journey.queue_fly_to("missing", "opal_crossing"), "cannot order an unknown ship")
	for sim in [journey, batched]:
		_expect(sim.queue_fly_to("ship_001", "opal_crossing"), "valid first destination queues")
		_expect(sim.queue_fly_to("ship_001", "lantern_deep"), "a second destination queues in order")
		_expect(not sim.queue_fly_to("ship_001", "lantern_deep"), "duplicate final destination is rejected")
	journey.advance_ticks(4)
	_expect(journey.state.ships[0].sector == "hearthreach", "ship remains in origin until a crossing finishes")
	_expect(journey.state.ships[0].travel.remaining == 1, "crossing consumes one unit per tick")
	journey.advance_ticks(1)
	_expect(journey.state.ships[0].sector == "opal_crossing", "ship reaches first destination after five ticks")
	_expect(journey.state.ships[0].orders.size() == 1, "completed order is removed exactly once")
	journey.advance_ticks(5)
	batched.advance_ticks(10)
	_expect(journey.state.ships[0].sector == "lantern_deep", "queued second destination completes")
	_expect(journey.state.ships[0].orders.is_empty() and journey.state.ships[0].status == "Idle", "ship returns to idle when queue is empty")
	_expect(journey.state.starting_credits == 25000, "travel does not create or spend credits")
	_expect(journey.snapshot() == batched.snapshot(), "batched and individually advanced travel reach identical state")
	var disconnected = WorldScript.new()
	disconnected.load_starter()
	disconnected.state.links.clear()
	_expect(not disconnected.queue_fly_to("ship_001", "opal_crossing"), "unreachable destinations are rejected")
	disconnected.state.links.append(["hearthreach", "opal_crossing"])
	disconnected.state.ships[0].owner = "vesper"
	_expect(not disconnected.queue_fly_to("ship_001", "opal_crossing"), "player cannot order a foreign ship")

	var save_store = SaveStoreScript.new()
	var save_path := test_root + "/travel.json"
	var to_save = WorldScript.new()
	_expect(to_save.load_starter("vesper") == OK, "saved journey starts with a selected origin")
	_expect(to_save.queue_fly_to("ship_001", "cinder_veil"), "first saved journey order queues")
	_expect(to_save.queue_fly_to("ship_001", "copper_wake"), "second saved journey order queues")
	to_save.state.relations.ravel = 7
	to_save.state.starting_credits = 23800
	to_save.advance_ticks(2)
	var original: Dictionary = to_save.snapshot()
	_expect(save_store.save_game(save_path, original) == OK, "mid-crossing game saves successfully")
	var loaded: Dictionary = save_store.load_game(save_path)
	_expect(bool(loaded.get("ok", false)) and not bool(loaded.get("recovered", true)), "primary save loads")
	if bool(loaded.get("ok", false)):
		_expect(loaded.state == original, "save restores the whole world, including origin, relations, credits, crew, travel and orders")
		var resumed = WorldScript.new()
		resumed.state = loaded.state.duplicate(true)
		to_save.advance_ticks(13)
		resumed.advance_ticks(13)
		_expect(resumed.snapshot() == to_save.snapshot(), "travel continues identically after save/load")
		_expect(resumed.state.ships[0].orders.is_empty(), "restored queued orders complete once")
	var previous_text := FileAccess.get_file_as_string(save_path)
	var invalid_world: Dictionary = original.duplicate(true)
	invalid_world.tick = -1
	_expect(save_store.save_game(save_path, invalid_world) != OK, "invalid world is rejected before writing")
	_expect(FileAccess.get_file_as_string(save_path) == previous_text, "failed validation leaves the existing save intact")
	_expect(save_store.save_game(save_path, to_save.snapshot()) == OK, "subsequent save succeeds")
	_expect(FileAccess.file_exists(save_path + ".bak"), "a previous valid save is kept as a backup")
	var corrupt := FileAccess.open(save_path, FileAccess.WRITE)
	corrupt.store_string("{broken")
	corrupt.close()
	var recovered: Dictionary = save_store.load_game(save_path)
	_expect(bool(recovered.get("ok", false)) and bool(recovered.get("recovered", false)), "damaged primary recovers the backup")
	if bool(recovered.get("ok", false)):
		_expect(recovered.state == original, "recovery restores the previous complete world")
	_expect(save_store.save_game(save_path, to_save.snapshot()) == OK, "a recovered game can write a new primary")
	_expect(bool(save_store.load_game(save_path + ".bak").get("ok", false)), "replacing a damaged primary preserves the valid backup")
	var corrupt_path := test_root + "/invalid.json"
	var malformed: Dictionary = original.duplicate(true)
	malformed.ships[0].travel.remaining = -1
	var malformed_payload := Marshalls.variant_to_base64(malformed, false)
	var corrupt_file := FileAccess.open(corrupt_path, FileAccess.WRITE)
	corrupt_file.store_string(JSON.stringify({"format_version": 1, "payload": malformed_payload, "checksum": malformed_payload.sha256_text()}))
	corrupt_file.close()
	_expect(not bool(save_store.load_game(corrupt_path).get("ok", false)), "structurally invalid data is rejected even with a matching checksum")
	var tampered_path := test_root + "/tampered.json"
	var tampered := FileAccess.open(tampered_path, FileAccess.WRITE)
	tampered.store_string(JSON.stringify({"format_version": 1, "payload": malformed_payload, "checksum": "incorrect"}))
	tampered.close()
	_expect(not bool(save_store.load_game(tampered_path).get("ok", false)), "checksum mismatch is rejected")
	var newer := FileAccess.open(save_path, FileAccess.WRITE)
	newer.store_string(JSON.stringify({"format_version": 99, "payload": "{}", "checksum": ""}))
	newer.close()
	_expect(save_store.load_game(save_path).get("reason") == "unsupported", "newer save versions are not silently replaced by an older backup")

	var economy = WorldScript.new()
	_expect(economy.load_starter() == OK, "starter economy loads")
	_disable_npc_trading(economy)
	_expect(economy.state.stations.size() == 4 and economy.state.wares.size() == 3, "starter economy has four stations and three wares")
	# Isolate the conservation check to trading; production has explicit
	# resource sources and sinks that are tested separately below.
	for station in economy.state.stations:
		station.production.clear()
	var credits_before := _total_credits(economy.state)
	var energy_before := _total_ware(economy.state, "energy_cells")
	var alloy_before := _total_ware(economy.state, "alloy_plates")
	var no_trade: Dictionary = economy.snapshot()
	_expect(not economy.trade("ship_001", "hearth_exchange", "energy_cells", 1, true).ok, "buying requires docking")
	_expect(not economy.dock_ship("ship_001", "vellum_foundry").ok, "cannot dock at a distant station")
	_expect(economy.snapshot() == no_trade, "rejected distant and undocked actions change nothing")
	_expect(economy.dock_ship("ship_001", "hearth_exchange").ok, "ship docks at a station in its sector")
	no_trade = economy.snapshot()
	_expect(not economy.trade("ship_001", "hearth_exchange", "energy_cells", 0, true).ok, "zero-quantity trade is rejected")
	_expect(not economy.trade("ship_001", "hearth_exchange", "energy_cells", -2, true).ok, "negative-quantity trade is rejected")
	_expect(not economy.trade("ship_001", "hearth_exchange", "alloy_plates", 1, true).ok, "unavailable station offer is rejected")
	_expect(not economy.trade("ship_001", "hearth_exchange", "alloy_plates", 1, false).ok, "cannot sell cargo the ship does not carry")
	_expect(not economy.trade("missing", "hearth_exchange", "energy_cells", 1, true).ok, "unknown ship cannot trade")
	_expect(economy.snapshot() == no_trade, "invalid trades leave cargo, stock, credits and ledger untouched")
	_expect(economy.trade("ship_001", "hearth_exchange", "energy_cells", 10, true).ok, "docked ship buys available energy")
	_expect(economy.state.starting_credits == 24900 and economy.state.ships[0].cargo.energy_cells == 10, "purchase debits credits and adds physical cargo")
	_expect(economy._find_station("hearth_exchange").stock.energy_cells == 110, "purchase removes stock from the selling station")
	_expect(economy.state.ledger.size() == 1 and economy.state.ledger[0].amount == -100, "purchase is recorded once in the ledger")
	no_trade = economy.snapshot()
	_expect(not economy.trade("ship_001", "hearth_exchange", "energy_cells", 41, true).ok, "purchase cannot exceed ship cargo space")
	_expect(not economy.trade("ship_001", "hearth_exchange", "energy_cells", 1000, true).ok, "purchase cannot exceed station stock")
	_expect(economy.snapshot() == no_trade, "capacity and stock failures are atomic")
	var funds: int = int(economy.state.starting_credits)
	economy.state.starting_credits = 0
	no_trade = economy.snapshot()
	_expect(not economy.trade("ship_001", "hearth_exchange", "energy_cells", 1, true).ok and economy.snapshot() == no_trade, "purchase requires sufficient player credits")
	economy.state.starting_credits = funds
	_expect(economy.queue_fly_to("ship_001", "vellum_gate"), "a docked ship can be ordered to another sector")
	_expect(economy.state.ships[0].docked_at == "", "travel order undocks the ship")
	_expect(not economy.trade("ship_001", "hearth_exchange", "energy_cells", 1, true).ok, "ship cannot trade while travelling")
	economy.advance_ticks(10)
	_expect(economy.state.ships[0].sector == "vellum_gate", "ship physically reaches the next market")
	_expect(economy.dock_ship("ship_001", "vellum_foundry").ok, "ship docks at destination")
	var foundry: Dictionary = economy._find_station("vellum_foundry")
	var foundry_funds: int = int(foundry.credits)
	foundry.credits = 0
	no_trade = economy.snapshot()
	_expect(not economy.trade("ship_001", "vellum_foundry", "energy_cells", 1, false).ok and economy.snapshot() == no_trade, "sale requires the station to have credits")
	foundry.credits = foundry_funds
	var foundry_capacity: int = int(foundry.storage_capacity)
	foundry.storage_capacity = economy.station_volume("vellum_foundry")
	no_trade = economy.snapshot()
	_expect(not economy.trade("ship_001", "vellum_foundry", "energy_cells", 1, false).ok and economy.snapshot() == no_trade, "sale requires station storage space")
	foundry.storage_capacity = foundry_capacity
	_expect(economy.trade("ship_001", "vellum_foundry", "energy_cells", 10, false).ok, "cargo is sold to the destination station")
	_expect(economy.state.starting_credits == 25060 and economy.state.ships[0].cargo.energy_cells == 0 and foundry.stock.energy_cells == 10, "sale moves cargo and pays the player")
	_expect(economy.trade("ship_001", "vellum_foundry", "alloy_plates", 10, true).ok, "return cargo can be purchased")
	_expect(economy.queue_fly_to("ship_001", "hearthreach"), "return route is queued")
	economy.advance_ticks(10)
	_expect(economy.dock_ship("ship_001", "hearth_exchange").ok, "returning ship docks")
	_expect(economy.trade("ship_001", "hearth_exchange", "alloy_plates", 10, false).ok, "return cargo can be sold")
	_expect(economy.state.starting_credits == 25160 and economy.state.ledger.size() == 4, "round trip profit and four ledger entries are correct")
	_expect(_total_credits(economy.state) == credits_before, "trading conserves credits between player and stations")
	_expect(_total_ware(economy.state, "energy_cells") == energy_before and _total_ware(economy.state, "alloy_plates") == alloy_before, "trading conserves physical wares")
	var economy_path := test_root + "/economy.json"
	_expect(save_store.save_game(economy_path, economy.snapshot()) == OK, "economy and ledger can be saved")
	var economy_load: Dictionary = save_store.load_game(economy_path)
	_expect(bool(economy_load.get("ok", false)) and economy_load.state == economy.snapshot(), "economy, docked ship and ledger survive save/load")
	var invalid_economy: Dictionary = economy.snapshot()
	invalid_economy.stations[0].storage_capacity = 0
	_expect(save_store.save_game(economy_path, invalid_economy) != OK, "save validation rejects station stock beyond storage capacity")
	_expect(save_store.load_game(economy_path).state == economy.snapshot(), "rejecting invalid economy leaves the last save intact")
	_expect(save_store.save_game(economy_path, economy.snapshot()) == OK, "economy save retains a compatible backup")
	var future_economy: Dictionary = economy.snapshot()
	future_economy.economy_version = 2
	var future_payload := Marshalls.variant_to_base64(future_economy, false)
	var future_file := FileAccess.open(economy_path, FileAccess.WRITE)
	future_file.store_string(JSON.stringify({"format_version": 1, "payload": future_payload, "checksum": future_payload.sha256_text()}))
	future_file.close()
	_expect(save_store.load_game(economy_path).get("reason") == "unsupported", "future economy schema is not silently replaced with an older backup")
	var old_save: Dictionary = original.duplicate(true)
	for key in ["economy_version", "production_version", "logistics_version", "player_roles_version", "recipes", "wares", "stations", "ledger", "next_transaction_id"]:
		old_save.erase(key)
	for index in range(old_save.ships.size() - 1, -1, -1):
		if old_save.ships[index].id == "npc_logistics_001":
			old_save.ships.remove_at(index)
	for ship in old_save.ships:
		ship.erase("player_trader")
		ship.erase("cargo")
		ship.erase("cargo_capacity")
		ship.erase("docked_at")
	var legacy_path := test_root + "/legacy.json"
	_expect(save_store.save_game(legacy_path, old_save) == OK, "pre-economy save remains readable")
	var legacy_load: Dictionary = save_store.load_game(legacy_path)
	var upgraded = WorldScript.new()
	_expect(bool(legacy_load.get("ok", false)) and upgraded.restore_snapshot(legacy_load.state) == OK, "pre-economy save is upgraded")
	_expect(upgraded.state.player_origin_faction_id == old_save.player_origin_faction_id and upgraded.state.relations == old_save.relations and upgraded.state.tick == old_save.tick, "upgrade preserves origin, relations and time")
	_expect(upgraded.state.ships[0].orders == old_save.ships[0].orders and upgraded.state.ships[0].travel == old_save.ships[0].travel, "upgrade preserves a journey in progress")
	_expect(upgraded.state.ships[0].cargo.is_empty() and upgraded.state.stations.size() == 4, "upgrade adds empty cargo and starter markets")

	var production_world = WorldScript.new()
	_expect(production_world.load_starter() == OK, "production scenario loads")
	_disable_npc_trading(production_world)
	var solar: Dictionary = production_world._find_station("hearth_exchange")
	var smelter: Dictionary = production_world._find_station("vellum_foundry")
	var mine: Dictionary = production_world._find_station("cinder_depot")
	var credits_at_start := _total_credits(production_world.state)
	production_world.advance_ticks(5)
	_expect(int(solar.stock.energy_cells) == 120 and int(solar.production[0].progress) == 5, "solar output waits for the full production cycle")
	_expect(int(smelter.production[0].cycles) == 0 and smelter.production[0].status == "Needs Energy Cells", "smelter halts when an input is missing")
	production_world.advance_ticks(1)
	_expect(int(solar.stock.energy_cells) == 124 and int(solar.production[0].cycles) == 1, "sunlight produces energy after six ticks")
	production_world.advance_ticks(2)
	_expect(int(mine.stock.ore) == 4 and int(mine.stock.energy_cells) == 2 and int(mine.deposits.ore) == 1196, "ore extraction consumes energy and the finite deposit")
	_expect(_total_credits(production_world.state) == credits_at_start, "production alone does not create credits")
	_expect(production_world.dock_ship("ship_001", "hearth_exchange").ok, "production test ship docks at the solar station")
	_expect(production_world.trade("ship_001", "hearth_exchange", "energy_cells", 5, true).ok, "production test ship buys real energy cargo")
	_expect(production_world.queue_fly_to("ship_001", "vellum_gate"), "energy delivery route is queued")
	production_world.advance_ticks(10)
	_expect(int(smelter.production[0].cycles) == 0, "smelter remains idle until the delivery arrives")
	_expect(production_world.dock_ship("ship_001", "vellum_foundry").ok, "energy delivery docks at the smelter")
	_expect(production_world.trade("ship_001", "vellum_foundry", "energy_cells", 5, false).ok, "energy is physically delivered to the smelter")
	production_world.advance_ticks(5)
	_expect(int(smelter.production[0].progress) == 5 and int(smelter.stock.ore) == 12 and int(smelter.stock.alloy_plates) == 100, "partial cycle preserves inputs and output until completion")
	var halfway_path := test_root + "/production-halfway.json"
	_expect(save_store.save_game(halfway_path, production_world.snapshot()) == OK, "a production cycle can be saved partway through")
	var halfway_load: Dictionary = save_store.load_game(halfway_path)
	var continued = WorldScript.new()
	_expect(bool(halfway_load.get("ok", false)) and continued.restore_snapshot(halfway_load.state) == OK, "partial production cycle reloads")
	var unbroken = WorldScript.new()
	_expect(unbroken.restore_snapshot(production_world.snapshot()) == OK, "comparison world starts from the same snapshot")
	continued.advance_ticks(5)
	for _tick in range(5):
		unbroken.advance_ticks(1)
	_expect(continued.snapshot() == unbroken.snapshot(), "production after reload matches uninterrupted single-tick execution")
	var completed_smelter: Dictionary = continued._find_station("vellum_foundry")
	_expect(int(completed_smelter.stock.ore) == 10 and int(completed_smelter.stock.energy_cells) == 4 and int(completed_smelter.stock.alloy_plates) == 102 and int(completed_smelter.production[0].cycles) == 1, "completed cycle consumes exactly two ore and one energy for two alloy")
	smelter.stock.energy_cells = 0
	production_world.advance_ticks(10)
	_expect(int(smelter.production[0].progress) == 5 and int(smelter.production[0].cycles) == 0 and smelter.production[0].status == "Needs Energy Cells", "shortage freezes partial progress without producing goods")
	smelter.stock.energy_cells = 5
	production_world.advance_ticks(5)
	_expect(int(smelter.production[0].cycles) == 1 and int(smelter.stock.alloy_plates) == 102, "production resumes from its preserved progress when supplies return")

	var finite = WorldScript.new()
	finite.load_starter()
	_disable_npc_trading(finite)
	var finite_mine: Dictionary = finite._find_station("cinder_depot")
	finite_mine.deposits.ore = 4
	finite.advance_ticks(8)
	_expect(int(finite_mine.stock.ore) == 4 and int(finite_mine.deposits.ore) == 0, "extractor consumes the last available deposit")
	finite.advance_ticks(16)
	_expect(int(finite_mine.stock.ore) == 4 and int(finite_mine.production[0].cycles) == 1 and finite_mine.production[0].status == "Deposit exhausted", "exhausted deposits cannot generate more ore")
	var full = WorldScript.new()
	full.load_starter()
	_disable_npc_trading(full)
	var full_solar: Dictionary = full._find_station("hearth_exchange")
	full_solar.stock.energy_cells = 300
	full.advance_ticks(12)
	_expect(int(full_solar.stock.energy_cells) == 300 and int(full_solar.production[0].progress) == 0 and full_solar.production[0].status == "Storage full", "full storage stops solar production without overfilling")
	full_solar.natural_sources.clear()
	_expect(full.production_report("hearth_exchange")[0].status == "Needs sunlight", "renewable source is required explicitly")
	full_solar.natural_sources.append("sunlight")
	_expect(full.dock_ship("ship_001", "hearth_exchange").ok and full.trade("ship_001", "hearth_exchange", "energy_cells", 4, true).ok, "player can clear full storage by buying real stock")
	full.advance_ticks(6)
	_expect(int(full_solar.stock.energy_cells) == 300 and int(full_solar.production[0].cycles) == 1, "solar production resumes when storage has room")
	var partial_capacity = WorldScript.new()
	partial_capacity.load_starter()
	_disable_npc_trading(partial_capacity)
	var partial_solar: Dictionary = partial_capacity._find_station("hearth_exchange")
	partial_capacity.advance_ticks(3)
	partial_solar.storage_capacity = partial_capacity.station_volume("hearth_exchange")
	partial_capacity.advance_ticks(8)
	_expect(int(partial_solar.production[0].progress) == 3 and partial_solar.production[0].status == "Storage full", "storage shortage freezes an unfinished cycle")
	partial_solar.storage_capacity = partial_capacity.station_volume("hearth_exchange") + 4
	partial_capacity.advance_ticks(3)
	_expect(int(partial_solar.production[0].cycles) == 1 and int(partial_solar.stock.energy_cells) == 124, "unfinished production resumes without duplicating output")
	var competing = WorldScript.new()
	competing.load_starter()
	_disable_npc_trading(competing)
	var shared_smelter: Dictionary = competing._find_station("vellum_foundry")
	shared_smelter.stock.ore = 2
	shared_smelter.stock.energy_cells = 1
	shared_smelter.storage_capacity = competing.station_volume("vellum_foundry")
	shared_smelter.production.append({"recipe_id":"alloy_smelting", "progress":0, "cycles":0, "status":"Running"})
	competing.advance_ticks(10)
	_expect(int(shared_smelter.stock.ore) == 0 and int(shared_smelter.stock.energy_cells) == 0 and int(shared_smelter.stock.alloy_plates) == 102, "a full station can convert inputs when the finished output uses less space")
	_expect(int(shared_smelter.production[0].cycles) == 1 and int(shared_smelter.production[1].cycles) == 0 and int(shared_smelter.production[1].progress) == 9, "competing modules cannot consume the same inputs twice")
	var soak = WorldScript.new()
	soak.load_starter()
	_disable_npc_trading(soak)
	var soak_credits := _total_credits(soak.state)
	soak.advance_ticks(2000)
	for station in soak.state.stations:
		_expect(soak.station_volume(str(station.id)) <= int(station.storage_capacity), "long run respects station storage: " + str(station.id))
		for ware_id in station.stock:
			_expect(int(station.stock[ware_id]) >= 0, "long run never creates negative stock: " + str(station.id) + "/" + str(ware_id))
	_expect(int(soak._find_station("hearth_exchange").stock.energy_cells) == 300 and int(soak._find_station("hearth_exchange").production[0].cycles) == 45, "solar output stops exactly at capacity in a long run")
	_expect(int(soak._find_station("cinder_depot").stock.ore) == 12 and int(soak._find_station("cinder_depot").deposits.ore) == 1188 and soak._find_station("cinder_depot").production[0].status == "Needs Energy Cells", "extractor stops after consuming its finite starting energy")
	_expect(_total_credits(soak.state) == soak_credits and soak.state.ledger.is_empty(), "long production run creates neither credits nor trade entries")

	var trading_legacy: Dictionary = economy.snapshot()
	trading_legacy.erase("production_version")
	trading_legacy.erase("logistics_version")
	trading_legacy.erase("player_roles_version")
	trading_legacy.ships[0].erase("player_trader")
	trading_legacy.erase("recipes")
	for index in range(trading_legacy.ships.size() - 1, -1, -1):
		if trading_legacy.ships[index].id == "npc_logistics_001":
			trading_legacy.ships.remove_at(index)
	for index in range(trading_legacy.wares.size() - 1, -1, -1):
		if trading_legacy.wares[index].id == "ore":
			trading_legacy.wares.remove_at(index)
	for station in trading_legacy.stations:
		for key in ["stock", "buy_prices", "sell_prices"]:
			station[key].erase("ore")
		station.erase("production")
		station.erase("natural_sources")
		station.erase("deposits")
	# A pre-existing market rule may have deliberately been removed.
	trading_legacy.stations[0].sell_prices.erase("energy_cells")
	var trading_legacy_path := test_root + "/trading-legacy.json"
	_expect(save_store.save_game(trading_legacy_path, trading_legacy) == OK, "pre-production trading save remains readable")
	var trading_legacy_read: Dictionary = save_store.load_game(trading_legacy_path)
	var production_upgrade = WorldScript.new()
	_expect(bool(trading_legacy_read.get("ok", false)) and production_upgrade.restore_snapshot(trading_legacy_read.state) == OK, "pre-production trading save upgrades")
	_expect(production_upgrade.state.starting_credits == trading_legacy.starting_credits and production_upgrade.state.ledger == trading_legacy.ledger and _without_player_role(production_upgrade.state.ships[0]) == trading_legacy.ships[0], "production upgrade preserves credits, transaction history and the player's ship")
	for old_station in trading_legacy.stations:
		var new_station: Dictionary = production_upgrade._find_station(str(old_station.id))
		_expect(new_station.credits == old_station.credits and new_station.stock.energy_cells == old_station.stock.energy_cells and new_station.stock.alloy_plates == old_station.stock.alloy_plates, "production upgrade preserves existing stock and station credits: " + str(old_station.id))
		_expect(int(new_station.stock.ore) == 0, "production upgrade does not add free ware stock: " + str(old_station.id))
	_expect(production_upgrade._find_station("cinder_depot").deposits.ore == 1200 and production_upgrade.state.recipes.size() == 3, "production upgrade adds the new finite deposit and recipes")
	_expect(not production_upgrade._find_station("hearth_exchange").sell_prices.has("energy_cells"), "production upgrade preserves existing market rules")
	_expect(save_store.save_game(trading_legacy_path, production_upgrade.snapshot()) == OK, "upgraded production state saves successfully")
	var invalid_production: Dictionary = production_world.snapshot()
	invalid_production.stations[0].production[0].progress = 6
	_expect(save_store.save_game(trading_legacy_path, invalid_production) != OK, "invalid production progress is rejected")
	invalid_production = production_world.snapshot()
	invalid_production.recipes[0].erase("source")
	_expect(save_store.save_game(trading_legacy_path, invalid_production) != OK, "input-free recipes require an explicit natural source")
	var future_production: Dictionary = production_world.snapshot()
	future_production.production_version = 2
	var production_payload := Marshalls.variant_to_base64(future_production, false)
	var future_production_file := FileAccess.open(trading_legacy_path, FileAccess.WRITE)
	future_production_file.store_string(JSON.stringify({"format_version": 1, "payload": production_payload, "checksum": production_payload.sha256_text()}))
	future_production_file.close()
	_expect(save_store.load_game(trading_legacy_path).get("reason") == "unsupported", "future production schema is not silently replaced by an older backup")

	var logistics = WorldScript.new()
	_expect(logistics.load_starter() == OK, "autonomous logistics scenario loads")
	var npc: Dictionary = logistics._find_ship("npc_logistics_001")
	var npc_start_credits := _total_credits(logistics.state)
	var home_market: Dictionary = logistics._find_station("verdant_hub")
	var home_before: int = int(home_market.credits)
	_expect(npc.owner == "frontier" and int(npc.credits) == 0, "NPC trader starts independently with no fabricated credits")
	_expect(not logistics.queue_fly_to("npc_logistics_001", "hearthreach"), "player cannot command an NPC trader")
	logistics.advance_ticks(1)
	_expect(int(npc.credits) == 1000 and int(home_market.credits) == home_before - 1000 and logistics.state.ledger[0].kind == "funding", "home station transfers and records real working capital")
	_expect(_total_credits(logistics.state) == npc_start_credits and int(logistics.state.starting_credits) == 25000, "funding conserves credits and does not use player money")
	_expect(npc.sector == "verdant_trace" and npc.cargo.is_empty(), "planned cargo is not teleported into the ship")
	logistics.advance_ticks(1)
	_expect(int(npc.cargo.get("energy_cells", 0)) == 8 and logistics.state.ledger[1].kind == "buy", "NPC buys physical energy from station stock")
	_expect(int(logistics._find_station("vellum_foundry").stock.energy_cells) == 0, "destination receives nothing before the journey")
	logistics.advance_ticks(9)
	_expect(int(logistics._find_station("vellum_foundry").stock.energy_cells) == 0, "NPC delivery takes actual sector travel time")
	logistics.advance_ticks(1)
	_expect(logistics.state.ledger[2].kind == "sell" and logistics.state.ledger[2].station_id == "vellum_foundry" and int(logistics._find_station("vellum_foundry").stock.energy_cells) == 8, "NPC sells cargo only on arrival at the destination")
	var logistics_valid := true
	var prior_events: int = logistics.state.ledger.size()
	for _step in range(220):
		var previous_cargo: Dictionary = npc.cargo.duplicate(true)
		logistics.advance_ticks(1)
		if _total_credits(logistics.state) != npc_start_credits or int(logistics.state.starting_credits) != 25000:
			logistics_valid = false
		if logistics.cargo_volume(str(npc.id)) > int(npc.cargo_capacity):
			logistics_valid = false
		for station in logistics.state.stations:
			if int(station.credits) < 0 or logistics.station_volume(str(station.id)) > int(station.storage_capacity):
				logistics_valid = false
			for ware_id in station.stock:
				if int(station.stock[ware_id]) < 0:
					logistics_valid = false
		for index in range(prior_events, logistics.state.ledger.size()):
			var event: Dictionary = logistics.state.ledger[index]
			if event.kind in ["buy", "sell"]:
				var market: Dictionary = logistics._find_station(str(event.station_id))
				var delta := int(npc.cargo.get(event.ware_id, 0)) - int(previous_cargo.get(event.ware_id, 0))
				var expected_delta := int(event.quantity) if event.kind == "buy" else -int(event.quantity)
				if npc.sector != market.sector or delta != expected_delta:
					logistics_valid = false
		prior_events = logistics.state.ledger.size()
	_expect(logistics_valid, "autonomous trades conserve credits, obey capacity and move cargo only at the visited market")
	_expect(int(logistics._find_station("vellum_foundry").production[0].cycles) > 0, "NPC energy deliveries enable real alloy production")
	_expect(int(logistics._find_station("cinder_depot").production[0].cycles) > 3, "NPC energy deliveries replenish the ore extractor")
	var ore_delivered := false
	for event in logistics.state.ledger:
		if event.kind == "sell" and event.ware_id == "ore" and event.station_id == "vellum_foundry":
			ore_delivered = true
	_expect(ore_delivered, "NPC physically transports ore to the smelter")
	var logistics_soak = WorldScript.new()
	logistics_soak.load_starter()
	var logistics_soak_credits := _total_credits(logistics_soak.state)
	logistics_soak.advance_ticks(2000)
	var soak_npc: Dictionary = logistics_soak.state.ships[1]
	var soak_valid := int(soak_npc.credits) >= 0 and logistics_soak.cargo_volume(str(soak_npc.id)) <= int(soak_npc.cargo_capacity)
	for station in logistics_soak.state.stations:
		if int(station.credits) < 0 or logistics_soak.station_volume(str(station.id)) > int(station.storage_capacity):
			soak_valid = false
		for ware_id in station.stock:
			if int(station.stock[ware_id]) < 0:
				soak_valid = false
	_expect(soak_valid and _total_credits(logistics_soak.state) == logistics_soak_credits, "2,000-tick NPC run preserves credit, stock and capacity invariants")
	_expect(save_store.save_game(test_root + "/npc-soak.json", logistics_soak.snapshot()) == OK, "long-running NPC world remains saveable")

	var trip = WorldScript.new()
	trip.load_starter()
	trip.advance_ticks(2)
	_expect(trip.state.ships[1].autotrader.phase == "to_destination" and int(trip.state.ships[1].cargo.energy_cells) > 0, "NPC test captures a purchased cargo in transit")
	var trip_path := test_root + "/npc-trip.json"
	_expect(save_store.save_game(trip_path, trip.snapshot()) == OK, "NPC trade in progress can be saved")
	var trip_read: Dictionary = save_store.load_game(trip_path)
	var trip_loaded = WorldScript.new()
	_expect(bool(trip_read.get("ok", false)) and trip_loaded.restore_snapshot(trip_read.state) == OK, "NPC route and cargo reload")
	trip.advance_ticks(120)
	for _step in range(120):
		trip_loaded.advance_ticks(1)
	_expect(trip.snapshot() == trip_loaded.snapshot(), "NPC trading remains deterministic across save/load and tick batching")

	var vanished_stock = WorldScript.new()
	vanished_stock.load_starter()
	vanished_stock.advance_ticks(1)
	var waiting_npc: Dictionary = vanished_stock.state.ships[1]
	var chosen_source: Dictionary = vanished_stock._find_station(str(waiting_npc.autotrader.source_id))
	_expect(not chosen_source.is_empty() and chosen_source.sector == waiting_npc.sector, "NPC selected a local supplier for the stock-race scenario")
	chosen_source.production.clear()
	chosen_source.stock[waiting_npc.autotrader.ware_id] = 0
	vanished_stock.advance_ticks(1)
	_expect(waiting_npc.cargo.is_empty() and vanished_stock.state.ledger.size() == 1, "stock disappearing before purchase cannot create cargo or a payment")

	var no_buyer = WorldScript.new()
	no_buyer.load_starter()
	no_buyer.advance_ticks(2)
	var waiting_cargo: Dictionary = no_buyer.state.ships[1]
	for station in no_buyer.state.stations:
		if station.buy_prices.has("energy_cells"):
			station.credits = 0
	no_buyer.advance_ticks(20)
	var sales_before := 0
	for event in no_buyer.state.ledger:
		if event.kind == "sell" and event.ware_id == "energy_cells":
			sales_before += 1
	_expect(int(waiting_cargo.cargo.energy_cells) == 8 and sales_before == 0 and waiting_cargo.autotrader.phase == "to_destination", "NPC retains cargo when no station can pay")
	var funds_source: Dictionary = no_buyer._find_station("hearth_exchange")
	var funds_target: Dictionary = no_buyer._find_station("vellum_foundry")
	funds_source.credits = int(funds_source.credits) - 200
	funds_target.credits = int(funds_target.credits) + 200
	no_buyer.advance_ticks(20)
	var sales_after := 0
	for event in no_buyer.state.ledger:
		if event.kind == "sell" and event.ware_id == "energy_cells":
			sales_after += 1
	_expect(int(waiting_cargo.cargo.energy_cells) == 0 and sales_after == 1, "NPC sells retained cargo once a real buyer can pay")
	var lost_market = WorldScript.new()
	lost_market.load_starter()
	lost_market.advance_ticks(2)
	var missing_id: String = lost_market.state.ships[1].autotrader.destination_id
	for index in range(lost_market.state.stations.size() - 1, -1, -1):
		if lost_market.state.stations[index].id == missing_id:
			lost_market.state.stations.remove_at(index)
	var lost_market_path := test_root + "/lost-market.json"
	_expect(save_store.save_game(lost_market_path, lost_market.snapshot()) == OK, "a station disappearing en route does not corrupt the save")
	var lost_read: Dictionary = save_store.load_game(lost_market_path)
	var resumed_market = WorldScript.new()
	_expect(bool(lost_read.get("ok", false)) and resumed_market.restore_snapshot(lost_read.state) == OK, "NPC cargo reloads after its destination disappears")
	resumed_market.advance_ticks(40)
	_expect(int(resumed_market.state.ships[1].cargo.get("energy_cells", 0)) == 0, "NPC finds another available buyer after its destination disappears")

	var pre_logistics: Dictionary = production_world.snapshot()
	pre_logistics.erase("logistics_version")
	pre_logistics.erase("player_roles_version")
	pre_logistics.ships[0].erase("player_trader")
	for index in range(pre_logistics.ships.size() - 1, -1, -1):
		if pre_logistics.ships[index].id == "npc_logistics_001":
			pre_logistics.ships.remove_at(index)
	var old_production_path := test_root + "/production-legacy.json"
	_expect(save_store.save_game(old_production_path, pre_logistics) == OK, "pre-logistics production save remains readable")
	var old_production: Dictionary = save_store.load_game(old_production_path)
	var logistics_upgrade = WorldScript.new()
	_expect(bool(old_production.get("ok", false)) and logistics_upgrade.restore_snapshot(old_production.state) == OK, "production save gains autonomous logistics")
	_expect(_without_player_role(logistics_upgrade.state.ships[0]) == pre_logistics.ships[0] and logistics_upgrade.state.ledger == pre_logistics.ledger and logistics_upgrade.state.starting_credits == pre_logistics.starting_credits, "logistics upgrade preserves the player's ship, credits and ledger")
	for old_station in pre_logistics.stations:
		var new_station: Dictionary = logistics_upgrade._find_station(str(old_station.id))
		_expect(new_station.credits == old_station.credits and new_station.stock == old_station.stock and new_station.production == old_station.production, "logistics upgrade preserves station finances and production: " + str(old_station.id))
	_expect(int(logistics_upgrade.state.ships[1].credits) == 0, "logistics upgrade does not create NPC funds")
	var altered_home: Dictionary = pre_logistics.duplicate(true)
	for station in altered_home.stations:
		if station.id == "verdant_hub":
			station.owner = altered_home.player_faction_id
	var alternate = WorldScript.new()
	_expect(alternate.restore_snapshot(altered_home) == OK and alternate.state.ships[1].owner != altered_home.player_faction_id, "logistics upgrade selects an available NPC home if the original is player-owned")
	var captured_home = WorldScript.new()
	captured_home.load_starter()
	var captured_station: Dictionary = captured_home._find_station("verdant_hub")
	captured_station.owner = captured_home.state.player_faction_id
	var captured_balance: int = int(captured_station.credits)
	captured_home.advance_ticks(8)
	_expect(int(captured_station.credits) == captured_balance and int(captured_home.state.ships[1].credits) == 0, "an NPC cannot take working capital from a station captured by the player")
	_expect(save_store.save_game(test_root + "/captured-home.json", captured_home.snapshot()) == OK, "a changed station owner does not invalidate the save")
	var invalid_logistics: Dictionary = logistics.snapshot()
	invalid_logistics.ships[1].credits = -1
	_expect(save_store.save_game(test_root + "/bad-npc.json", invalid_logistics) != OK, "a negative NPC wallet is rejected")
	invalid_logistics = logistics.snapshot()
	invalid_logistics.ships[1].autotrader.phase = "invalid"
	_expect(save_store.save_game(test_root + "/bad-npc.json", invalid_logistics) != OK, "an invalid NPC order phase is rejected")
	var npc_version_path := test_root + "/npc-version.json"
	_expect(save_store.save_game(npc_version_path, logistics.snapshot()) == OK and save_store.save_game(npc_version_path, logistics.snapshot()) == OK, "NPC version check has a valid backup")
	var future_logistics: Dictionary = logistics.snapshot()
	future_logistics.logistics_version = 2
	var logistics_payload := Marshalls.variant_to_base64(future_logistics, false)
	var future_logistics_file := FileAccess.open(npc_version_path, FileAccess.WRITE)
	future_logistics_file.store_string(JSON.stringify({"format_version": 1, "payload": logistics_payload, "checksum": logistics_payload.sha256_text()}))
	future_logistics_file.close()
	_expect(save_store.load_game(npc_version_path).get("reason") == "unsupported", "future logistics schema is not silently replaced by an older backup")

	# Player role: physical trades, manual intervention and save safety.
	var trader = WorldScript.new()
	_expect(trader.load_starter() == OK, "player trader scenario loads")
	_disable_npc_trading(trader)
	var player: Dictionary = trader.state.ships[0]
	var total_money := _total_credits(trader.state)
	_expect(not player.player_trader.enabled and player.role == "Unassigned", "player trader is opt-in")
	_expect(not trader.set_player_trader("npc_logistics_001", true) and not trader.set_player_trader("unknown", true), "roles cannot be assigned to NPC or unknown ships")
	_expect(trader.dock_ship("ship_001", "hearth_exchange").ok and trader.trade("ship_001", "hearth_exchange", "energy_cells", 3, true).ok, "player acquires cargo before enabling automation")
	_expect(trader.set_player_trader("ship_001", true), "player enables autonomous trading")
	for _tick in range(40):
		trader.advance_ticks(1)
		if player.player_trader.phase == "to_destination":
			break
	var player_job: Dictionary = player.player_trader
	_expect(player_job.phase == "to_destination" and player_job.ware_id == "energy_cells" and int(player_job.managed_quantity) > 2, "role buys physical cargo for a profitable supply run")
	_expect(int(player.cargo.energy_cells) == int(player_job.managed_quantity) + 3 and trader.state.ledger.size() == 2, "purchased cargo is tracked separately from existing cargo")
	_expect(int(trader.state.starting_credits) < 25000 and _total_credits(trader.state) == total_money, "player buys with faction credits without creating money")
	var saved_trip: Dictionary = trader.snapshot()
	var player_trip_path := test_root + "/player-trip.json"
	_expect(save_store.save_game(player_trip_path, saved_trip) == OK, "player trade can be saved while carrying goods")
	var player_trip_read: Dictionary = save_store.load_game(player_trip_path)
	var player_resumed = WorldScript.new()
	_expect(bool(player_trip_read.get("ok", false)) and player_resumed.restore_snapshot(player_trip_read.state) == OK, "player trade resumes from a saved journey")
	trader.advance_ticks(60)
	player_resumed.advance_ticks(60)
	_expect(trader.snapshot() == player_resumed.snapshot(), "saved player trade continues deterministically")
	var player_sale_seen := false
	for entry in trader.state.ledger:
		if entry.ship_id == "ship_001" and entry.kind == "sell":
			player_sale_seen = true
	_expect(player_sale_seen and int(player.cargo.energy_cells) >= 3 and _total_credits(trader.state) == total_money, "player trader delivers real cargo while preserving pre-existing goods and credits")

	# Disable during a run, then manually sell part of the managed cargo.
	var intervention = WorldScript.new()
	_expect(intervention.restore_snapshot(saved_trip) == OK, "intervention scenario restores in-flight cargo")
	var held: Dictionary = intervention.state.ships[0]
	var managed_before := int(held.player_trader.managed_quantity)
	_expect(intervention.set_player_trader("ship_001", false), "player can turn automation off in transit")
	var events_before: int = intervention.state.ledger.size()
	intervention.advance_ticks(40)
	_expect(intervention.state.ledger.size() == events_before and int(held.player_trader.managed_quantity) == managed_before, "disabling lets the existing trip finish without trading or losing cargo")
	var buyer_id := str(held.player_trader.destination_id)
	_expect(intervention.dock_ship("ship_001", buyer_id).ok and intervention.trade("ship_001", buyer_id, "energy_cells", 2, false).ok, "player can manually sell some role-managed cargo")
	_expect(int(held.player_trader.managed_quantity) == managed_before - 2, "manual sale reduces the amount the role may later sell")
	intervention.set_player_trader("ship_001", true)
	intervention.advance_ticks(1)
	_expect(int(held.cargo.energy_cells) == 3 and held.player_trader.phase == "idle", "resuming delivers only remaining managed cargo, leaving original goods aboard")

	var ordered = WorldScript.new()
	ordered.load_starter()
	_disable_npc_trading(ordered)
	_expect(ordered.queue_fly_to("ship_001", "vellum_gate") and ordered.set_player_trader("ship_001", true), "a role can be enabled with a manual route already queued")
	ordered.advance_ticks(9)
	_expect(ordered.state.ledger.is_empty() and ordered.state.ships[0].sector != "vellum_gate", "automation waits while the manual journey is in progress")
	ordered.advance_ticks(1)
	_expect(ordered.state.ships[0].sector == "vellum_gate", "manual destination is reached before automation continues")

	var override_world = WorldScript.new()
	override_world.restore_snapshot(saved_trip)
	var override_ship: Dictionary = override_world.state.ships[0]
	_expect(override_world.queue_fly_to("ship_001", "hearthreach"), "a manual route can be queued behind an automated journey")
	var has_left := false
	var completed_manual := false
	var no_early_sale := true
	var original_events: int = override_world.state.ledger.size()
	for _tick in range(80):
		override_world.advance_ticks(1)
		if override_ship.sector != "hearthreach":
			has_left = true
		if override_world.state.ledger.size() != original_events:
			no_early_sale = false
		if has_left and override_ship.sector == "hearthreach":
			completed_manual = true
			break
	_expect(completed_manual and no_early_sale, "queued manual destination completes before the trader resumes its sale")
	override_world.advance_ticks(40)
	_expect(override_world.state.ledger.size() > original_events and int(override_ship.cargo.energy_cells) >= 3, "trader replans its delivery after the manual route without losing original cargo")

	var waiting_player = WorldScript.new()
	waiting_player.restore_snapshot(saved_trip)
	var waiting_ship: Dictionary = waiting_player.state.ships[0]
	for station in waiting_player.state.stations:
		if station.buy_prices.has("energy_cells"):
			station.credits = 0
	waiting_player.advance_ticks(80)
	_expect(int(waiting_ship.player_trader.managed_quantity) > 0 and int(waiting_ship.cargo.energy_cells) >= int(waiting_ship.player_trader.managed_quantity) + 3, "insolvent buyers make the player trader wait with its cargo")
	_expect(save_store.save_game(test_root + "/waiting-player.json", waiting_player.snapshot()) == OK, "waiting cargo and an unavailable buyer remain saveable")
	waiting_player._find_station("vellum_foundry").credits = 1000
	waiting_player.advance_ticks(60)
	_expect(int(waiting_ship.cargo.energy_cells) >= 3 and waiting_player.state.ledger.size() > 2, "trader resumes when a buyer can pay")
	var no_funds = WorldScript.new()
	no_funds.load_starter()
	_disable_npc_trading(no_funds)
	no_funds.state.starting_credits = 0
	no_funds.set_player_trader("ship_001", true)
	no_funds.advance_ticks(40)
	_expect(no_funds.state.ledger.is_empty() and no_funds.state.ships[0].cargo.is_empty(), "trader cannot buy without player funds")

	var old_roles: Dictionary = saved_trip.duplicate(true)
	old_roles.erase("player_roles_version")
	old_roles.ships[0].erase("player_trader")
	old_roles.ships[0].role = "Unassigned"
	_expect(save_store.save_game(test_root + "/old-roles.json", old_roles) == OK, "older logistics save remains readable")
	var old_roles_load: Dictionary = save_store.load_game(test_root + "/old-roles.json")
	var roles_upgrade = WorldScript.new()
	_expect(bool(old_roles_load.get("ok", false)) and roles_upgrade.restore_snapshot(old_roles_load.state) == OK, "older logistics save gains the new role")
	_expect(not roles_upgrade.state.ships[0].player_trader.enabled and _without_player_role(roles_upgrade.state.ships[0]) == old_roles.ships[0] and roles_upgrade.state.ledger == old_roles.ledger and roles_upgrade.state.ships[1] == old_roles.ships[1], "role migration preserves existing ship, journey, NPC and ledger without enabling automation")
	var bad_role: Dictionary = saved_trip.duplicate(true)
	bad_role.ships[0].player_trader.managed_quantity = 999
	_expect(save_store.save_game(test_root + "/bad-role.json", bad_role) != OK, "save validation rejects managed cargo beyond the actual hold")
	bad_role = saved_trip.duplicate(true)
	bad_role.ships[0].player_trader.phase = "invalid"
	_expect(save_store.save_game(test_root + "/bad-role.json", bad_role) != OK, "save validation rejects invalid player trader phases")
	var roles_version_path := test_root + "/role-version.json"
	_expect(save_store.save_game(roles_version_path, saved_trip) == OK and save_store.save_game(roles_version_path, saved_trip) == OK, "player-role version test has a valid backup")
	var future_roles: Dictionary = saved_trip.duplicate(true)
	future_roles.player_roles_version = 2
	var roles_payload := Marshalls.variant_to_base64(future_roles, false)
	var future_roles_file := FileAccess.open(roles_version_path, FileAccess.WRITE)
	future_roles_file.store_string(JSON.stringify({"format_version": 1, "payload": roles_payload, "checksum": roles_payload.sha256_text()}))
	future_roles_file.close()
	_expect(save_store.load_game(roles_version_path).get("reason") == "unsupported", "future player-role data is not silently replaced by an older backup")

	var concurrent = WorldScript.new()
	concurrent.load_starter()
	var concurrent_credits := _total_credits(concurrent.state)
	concurrent.set_player_trader("ship_001", true)
	concurrent.advance_ticks(500)
	var concurrent_ok := _total_credits(concurrent.state) == concurrent_credits
	for ship in concurrent.state.ships:
		if concurrent.cargo_volume(str(ship.id)) > int(ship.cargo_capacity):
			concurrent_ok = false
	for station in concurrent.state.stations:
		if int(station.credits) < 0 or concurrent.station_volume(str(station.id)) > int(station.storage_capacity):
			concurrent_ok = false
	_expect(concurrent_ok and concurrent.state.ledger.size() > 3, "player and NPC traders operate together without creating credits or exceeding capacity")
	_expect(save_store.save_game(test_root + "/concurrent.json", concurrent.snapshot()) == OK, "concurrent trading world remains saveable")

	# Godot 4.4's headless display can default to 64x64 regardless of project
	# window settings. Test the actual intended landscape viewport explicitly.
	root.size = Vector2i(1280, 720)
	var screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-vesper.json"
	root.add_child(screen)
	await process_frame
	# Container layout can require another frame on older Godot versions.
	await process_frame
	_expect(screen.find_child("NewGameScreen", true, false) != null, "new game presents faction origins")
	_expect(screen.start_buttons.size() == 4, "new game offers all four origins")
	screen.find_child("Origin_vesper", true, false).pressed.emit()
	_expect(screen.origin_title.text == "Vesper Guild", "choosing an origin updates its preview")
	_expect(screen.origin_summary.text.contains("Vellum Gate") and screen.origin_summary.text.contains("Vesper Guild: +20"), "origin preview shows starting sector and relations")
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	_expect(screen.world.state.player_origin_faction_id == "vesper", "new game applies selected origin")
	_expect(screen.world.state.ships[0].sector == "vellum_gate", "new game starts in selected faction sector")
	_expect(screen.world.state.ships[0].owner == "player", "new game keeps the player faction independent")
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-travel.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	_expect(screen.paused, "game starts paused")
	_expect(screen.find_child("GalaxyMap", true, false) != null, "main scene creates the galaxy map")
	_expect(screen.find_child("ShipButton", true, false) != null, "main scene exposes player property")
	_expect(screen.pause_button.size.y <= 65.0, "top bar stays compact at landscape resolution (button: %s, viewport: %s)" % [screen.pause_button.size, root.size])
	_expect(screen.map_view.size.y >= 250.0, "galaxy map has usable height at landscape resolution")
	_expect(screen.find_child("RolePicker", true, false) != null and screen.role_picker.item_count == 2, "property panel offers manual and autonomous trader roles")
	screen.role_picker.select(1)
	screen.role_picker.item_selected.emit(1)
	_expect(screen.world.state.ships[0].player_trader.enabled and screen.role_hint.text.contains("credits"), "selecting trader enables it and explains its use of player funds")
	_expect(save_store.load_game(screen.save_path).state.ships[0].player_trader.enabled, "changing the ship role saves immediately")
	screen.find_child("ShipButton", true, false).pressed.emit()
	_expect(screen.detail_body.text.contains("Autonomous Trader") and screen.detail_body.text.contains("Trader plan"), "ship details show its role and current plan")
	screen.role_picker.select(0)
	screen.role_picker.item_selected.emit(0)
	_expect(not screen.world.state.ships[0].player_trader.enabled and screen.role_hint.text.contains("cargo"), "unassigning explains the treatment of the current journey and cargo")
	screen.find_child("TradeButton", true, false).pressed.emit()
	_expect(screen.find_child("TradeScreen", true, false) != null, "trade screen opens")
	_expect(screen.trade_production.text.contains("Solar Array") and screen.trade_production.text.contains("Sunlight"), "market screen shows production and its natural input")
	screen.trade_station_picker.select(1)
	screen.trade_station_picker.item_selected.emit(1)
	_expect(screen.trade_production.text.contains("Needs Energy Cells") and screen.trade_production.text.contains("Ore"), "market screen explains a smelter shortage and its recipe")
	screen.trade_station_picker.select(0)
	screen.trade_station_picker.item_selected.emit(0)
	screen.find_child("DockButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].docked_at == "hearth_exchange", "trade screen docks at the local station")
	screen.trade_quantity.value = 5
	screen.find_child("BuyButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].cargo.energy_cells == 5 and screen.world.state.ledger.size() == 1, "trade screen purchases stock and records it")
	_expect(save_store.load_game(screen.save_path).state.ships[0].cargo.energy_cells == 5, "successful trade is saved immediately")
	screen.trade_quantity.value = 1
	for _count in range(4):
		screen.find_child("BuyButton", true, false).pressed.emit()
	_expect(screen.world.state.ledger.size() == 5 and screen.trade_ledger.text.contains("#1") and screen.trade_ledger.text.contains("#5"), "scrollable ledger includes both old and new transactions")
	screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	screen.map_view.sector_selected.emit("vellum_gate")
	_expect(screen.detail_title.text == "Vellum Gate", "map sector selection updates details")
	_expect(screen.detail_body.text.contains("Vesper Guild"), "sector details show the controlling faction")
	screen.find_child("OrderButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].orders.size() == 1, "fly-order button queues selected destination")
	_expect(screen.order_feedback.text.contains("Resume"), "paused player is told to resume for travel")
	_expect(screen.world.state.ships[0].sector == "hearthreach", "issuing an order while paused does not move the ship")
	screen.find_child("ShipButton", true, false).pressed.emit()
	_expect(screen.detail_title.text == "First Light", "property selection shows the player's ship")
	_expect(screen.detail_body.text.contains("Mira Vale"), "ship details show the captain")
	_expect(screen.detail_body.text.contains("Crew\n2\n"), "crew count displays as a whole number")
	_expect(screen.detail_body.text.contains("Energy Cells: 9"), "ship details display carried cargo")
	_expect(screen.detail_body.text.contains("Vellum Gate"), "ship details show queued destination")
	await process_frame
	await process_frame
	var order_control: Control = screen.find_child("OrderButton", true, false)
	_expect(order_control.global_position.y + order_control.size.y <= float(root.size.y), "long ship details keep order controls inside the viewport")
	screen.find_child("PauseButton", true, false).pressed.emit()
	_expect(not screen.paused, "resume control unpauses")
	_expect(screen.order_feedback.text.is_empty(), "resume clears the paused-order prompt")
	screen.find_child("PauseButton", true, false).pressed.emit()
	_expect(screen.paused, "pause control pauses")
	_expect(screen.find_child("SaveButton", true, false) != null, "manual save control is available")
	_expect(FileAccess.file_exists(screen.save_path), "starting and ordering a ship creates a save")
	screen.world.state.relations.vesper = 12
	screen.find_child("PauseButton", true, false).pressed.emit()
	screen._process(1.0)
	_expect(screen.save_status.text == "Unsaved", "advanced simulation is marked unsaved until the next save")
	screen._process(29.0)
	var timed_save: Dictionary = save_store.load_game(screen.save_path)
	_expect(bool(timed_save.get("ok", false)) and timed_save.state.tick == screen.world.state.tick and timed_save.state.relations.vesper == 12, "autosave records elapsed time and changed relations")
	screen.world.advance_ticks(1)
	screen.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	var background_save: Dictionary = save_store.load_game(screen.save_path)
	_expect(screen.paused and bool(background_save.get("ok", false)) and background_save.state.tick == screen.world.state.tick, "backgrounding pauses and saves the game")
	var saved_ui_state: Dictionary = screen.world.snapshot()
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-travel.json"
	root.add_child(screen)
	await process_frame
	_expect(screen.find_child("ContinueButton", true, false) != null, "continue is offered when a save exists")
	screen.find_child("ContinueButton", true, false).pressed.emit()
	await process_frame
	_expect(screen.world.snapshot() == saved_ui_state, "continue restores the exact saved ship orders and world")
	_expect(screen.paused, "continued game starts paused")
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-travel.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	_expect(not screen.game_started, "starting a new game does not immediately overwrite an existing save")
	_expect(screen.overwrite_confirmation.visible, "replacing an existing save requires confirmation")
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-npc.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	screen.world.advance_ticks(12)
	screen._show_sector("vellum_gate")
	_expect(screen.detail_body.text.contains("Wayfarer") and screen.detail_body.text.contains("Faction traffic"), "sector details identify NPC traffic separately from player property")
	screen.find_child("TradeButton", true, false).pressed.emit()
	_expect(screen.trade_ledger.text.contains("Wayfarer") and screen.trade_ledger.text.contains("funded"), "ledger identifies NPC trade and working-capital transfers")
	screen.queue_free()
	await process_frame
	var directory := DirAccess.open(test_root)
	if directory != null:
		for file_name in directory.get_files():
			directory.remove(file_name)
		DirAccess.remove_absolute(ProjectSettings.globalize_path(test_root))
	if failures.is_empty():
		print("PASS: %d foundation checks" % checks)
		quit(0)
	else:
		printerr("FAILED: %d of %d foundation checks" % [failures.size(), checks])
		quit(1)
