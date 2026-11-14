extends SceneTree

const WorldScript = preload("res://scripts/world.gd")
const SaveStoreScript = preload("res://scripts/save_store.gd")
const StationPlannerScript = preload("res://scripts/station_planner.gd")
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
		if station.has("archive"):
			total += int(station.archive.staff_credits)
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
	copy.erase("build_supply")
	copy.erase("station_supply")
	copy.erase("captain_profile")
	copy.erase("crew_profile")
	copy.erase("payroll")
	return copy


func _without_station_supply(ships: Array) -> Array:
	var copy := ships.duplicate(true)
	for ship in copy:
		ship.erase("station_supply")
		ship.erase("captain_profile")
		ship.erase("crew_profile")
		ship.erase("payroll")
	return copy


func _without_progression(ships: Array) -> Array:
	var copy := ships.duplicate(true)
	for ship in copy:
		ship.erase("captain_profile")
		ship.erase("crew_profile")
		ship.erase("payroll")
	return copy


func _strip_habitation(state: Dictionary) -> void:
	state.erase("habitation_version")
	state.erase("habitation_catalog")
	for station in state.get("stations", []):
		station.erase("habitation")
	if state.has("construction_blueprints"):
		for id in ["crew_habitat", "family_habitat", "adaptive_habitat"]:
			state.construction_blueprints.erase(id)
	for cohort in state.get("population", {}).get("stations", {}).values():
		cohort.hab_capacity = 0
		cohort.housing_status = "unimplemented"


func _strip_shipyard(state: Dictionary) -> void:
	_strip_habitation(state)
	state.erase("population_version")
	state.erase("population")
	state.erase("personnel_version")
	state.erase("crew_pools")
	for ship in state.ships:
		ship.erase("captain_profile")
		ship.erase("crew_profile")
		ship.erase("payroll")
	state.erase("shipyard_version")
	state.erase("shipyard")


func _strip_research(state: Dictionary) -> void:
	_strip_shipyard(state)
	state.erase("station_supply_version")
	for ship in state.ships:
		ship.erase("station_supply")
	state.erase("research_version")
	state.erase("research")
	for station in state.stations:
		station.stock.erase("research_notes")
	for index in range(state.wares.size() - 1, -1, -1):
		if state.wares[index].id == "research_notes":
			state.wares.remove_at(index)
	for index in range(state.recipes.size() - 1, -1, -1):
		if state.recipes[index].id == "research_laboratory":
			state.recipes.remove_at(index)
	if state.has("construction_blueprints"):
		state.construction_blueprints.erase("research_laboratory")


func _strip_archives(state: Dictionary) -> void:
	_strip_research(state)
	state.erase("archive_version")
	state.erase("visited_archives")
	for index in range(state.stations.size() - 1, -1, -1):
		if state.stations[index].has("archive"):
			state.stations.remove_at(index)
		else:
			state.stations[index].stock.erase("blank_media")
			state.stations[index].stock.erase("recorded_data")
	for index in range(state.wares.size() - 1, -1, -1):
		if state.wares[index].id in ["blank_media", "recorded_data"]:
			state.wares.remove_at(index)
	for index in range(state.recipes.size() - 1, -1, -1):
		if state.recipes[index].id in ["media_fabrication", "data_reproduction"]:
			state.recipes.remove_at(index)
	if state.has("construction_blueprints"):
		state.construction_blueprints.erase("media_fabrication")
		state.construction_blueprints.erase("data_reproduction")


func _strip_construction(state: Dictionary) -> void:
	_strip_archives(state)
	for key in ["construction_version", "construction_blueprints", "construction_resources", "build_sites", "next_build_site_id", "build_supply_version"]:
		state.erase(key)
	for index in range(state.ships.size() - 1, -1, -1):
		state.ships[index].erase("build_supply")
		if state.ships[index].id == "npc_builder_001":
			state.ships.remove_at(index)


func _map_touch(view, index: int, position: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = index
	event.position = position
	event.pressed = pressed
	view._gui_input(event)


func _map_drag(view, index: int, position: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = index
	event.position = position
	view._gui_input(event)


func _map_item(view, kind: String, id: String) -> Dictionary:
	for item in view._items():
		if item.kind == kind and item.id == id:
			return item
	return {}


func _plan_row(rows: Array, id: String) -> Dictionary:
	for row in rows:
		if row.id == id:
			return row
	return {}


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
	_expect(first.state.ships.size() == 3, "starter galaxy contains one NPC trader and one builder")
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
	_expect(economy.state.stations.size() == 8 and economy.state.wares.size() == 6, "starter economy includes four markets, four archives and six wares")
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
	_strip_construction(old_save)
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
	_expect(upgraded.state.ships[0].cargo.is_empty() and upgraded.state.stations.size() == 8, "upgrade adds empty cargo, starter markets and archives")

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
	_expect(_total_credits(soak.state) == soak_credits and soak.state.ledger.all(func(entry): return entry.kind == "crew_payroll"), "long production run creates neither credits nor trade entries; recurring wages remain internally funded")

	var trading_legacy: Dictionary = economy.snapshot()
	_strip_construction(trading_legacy)
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
	_expect(production_upgrade._find_station("cinder_depot").deposits.ore == 1200 and production_upgrade.state.recipes.size() == 6, "production upgrade adds the finite deposit and current recipes")
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
		if _total_credits(logistics.state) != npc_start_credits or int(logistics.state.starting_credits) + int(logistics.state.ships[0].payroll.total_paid) != 25000:
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
	var served_archives := 0
	for station in logistics_soak.state.stations:
		if station.has("archive") and int(station.archive.cycles) > 0 and int(station.production[1].cycles) > 0:
			served_archives += 1
	_expect(served_archives == 4, "all four faction archives receive supplies, perform upkeep and make copies during the autonomous economy run")
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
	_strip_construction(pre_logistics)
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
		var migrated_stock: Dictionary = new_station.stock.duplicate(true)
		migrated_stock.erase("blank_media")
		migrated_stock.erase("recorded_data")
		migrated_stock.erase("research_notes")
		_expect(new_station.credits == old_station.credits and migrated_stock == old_station.stock and new_station.production == old_station.production, "logistics upgrade preserves station finances and production: " + str(old_station.id))
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
		station.credits = 0 # Sponsors cannot recapitalise an insolvent archive during this scenario.
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
	_strip_construction(old_roles)
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

	# Station planner is a pure preview of real recipes and shared inputs.
	var planner = StationPlannerScript.new()
	var planner_state: Dictionary = concurrent.snapshot()
	var unchanged_planner_state: Dictionary = planner_state.duplicate(true)
	var full_plan: Dictionary = planner.preview(planner_state, {"alloy_smelting":1}, "self", [])
	_expect(full_plan.ok and int(_plan_row(full_plan.modules, "alloy_smelting").get("total", 0)) == 1, "self-sufficient plan preserves the selected smelter")
	_expect(int(_plan_row(full_plan.modules, "ore_extraction").get("added", 0)) == 1 and int(_plan_row(full_plan.modules, "solar_cells").get("added", 0)) == 1, "self-sufficient smelter adds whole ore and power modules")
	_expect(is_equal_approx(float(_plan_row(full_plan.wares, "energy_cells").get("supply", 0)), 40.0) and is_equal_approx(float(_plan_row(full_plan.wares, "energy_cells").get("demand", 0)), 13.5), "plan calculates production and shared input rates per 60 ticks")
	_expect(float(_plan_row(full_plan.wares, "ore").get("imports", -1)) == 0.0 and full_plan.warnings.size() >= 2 and " ".join(full_plan.warnings).contains("finite"), "self-sufficient plan flags unsurveyed sunlight and a finite ore deposit")
	var shared_plan: Dictionary = planner.preview(planner_state, {"alloy_smelting":5, "ore_extraction":1}, "self", [])
	_expect(int(_plan_row(shared_plan.modules, "ore_extraction").get("total", 0)) == 2 and int(_plan_row(shared_plan.modules, "ore_extraction").get("added", 0)) == 1, "shared ore production includes the user's existing module once")
	_expect(int(_plan_row(shared_plan.modules, "solar_cells").get("total", 0)) == 2 and is_equal_approx(float(_plan_row(shared_plan.wares, "energy_cells").get("demand", 0)), 45.0), "shared energy demand is summed before rounding whole solar modules")
	var ore_import: Dictionary = planner.preview(planner_state, {"alloy_smelting":1}, "selected", ["ore"])
	_expect(_plan_row(ore_import.modules, "ore_extraction").is_empty() and int(_plan_row(ore_import.modules, "solar_cells").get("total", 0)) == 1, "selective ore imports remove only the ore production branch")
	_expect(is_equal_approx(float(_plan_row(ore_import.wares, "ore").get("imports", 0)), 12.0), "selective imports report the actual ore shortage")
	var energy_import: Dictionary = planner.preview(planner_state, {"alloy_smelting":1}, "selected", ["energy_cells"])
	_expect(_plan_row(energy_import.modules, "solar_cells").is_empty() and int(_plan_row(energy_import.modules, "ore_extraction").get("total", 0)) == 1 and is_equal_approx(float(_plan_row(energy_import.wares, "energy_cells").get("imports", 0)), 13.5), "selective energy imports leave the ore chain intact")
	var all_import: Dictionary = planner.preview(planner_state, {"alloy_smelting":1}, "all", [])
	_expect(all_import.modules.size() == 1 and is_equal_approx(float(_plan_row(all_import.wares, "ore").get("imports", 0)), 12.0) and is_equal_approx(float(_plan_row(all_import.wares, "energy_cells").get("imports", 0)), 6.0), "import-all adds no upstream modules and reports both inputs")
	var mixed_plan: Dictionary = planner.preview(planner_state, {"alloy_smelting":3, "ore_extraction":1}, "selected", ["ore"])
	_expect(int(_plan_row(mixed_plan.modules, "ore_extraction").get("total", 0)) == 1 and is_equal_approx(float(_plan_row(mixed_plan.wares, "ore").get("imports", 0)), 6.0), "selected imports supplement explicitly chosen local production")
	var missing_recipe: Dictionary = planner_state.duplicate(true)
	for index in range(missing_recipe.recipes.size() - 1, -1, -1):
		if missing_recipe.recipes[index].id == "ore_extraction":
			missing_recipe.recipes.remove_at(index)
	var missing_plan: Dictionary = planner.preview(missing_recipe, {"alloy_smelting":1}, "self", [])
	_expect(float(_plan_row(missing_plan.wares, "ore").get("imports", 0)) > 0.0 and " ".join(missing_plan.warnings).contains("must be imported"), "unavailable production is reported as an import, not fabricated")
	var cyclic_state: Dictionary = {"wares":planner_state.wares.duplicate(true), "recipes":[
		{"id":"loop_energy", "name":"Loop Energy", "cycle_ticks":60, "inputs":{"ore":1}, "outputs":{"energy_cells":1}},
		{"id":"loop_ore", "name":"Loop Ore", "cycle_ticks":60, "inputs":{"energy_cells":1}, "outputs":{"ore":1}}
	]}
	var cycle_plan: Dictionary = planner.preview(cyclic_state, {"loop_energy":1}, "self", [])
	_expect(not cycle_plan.ok and " ".join(cycle_plan.errors).contains("Cyclic dependency"), "cyclic recipes are detected without infinite expansion")
	var resolved_cycle: Dictionary = planner.preview(cyclic_state, {"loop_energy":1}, "selected", ["energy_cells"])
	_expect(resolved_cycle.ok and " ".join(resolved_cycle.warnings).contains("starter stock"), "an import exception breaks a cycle and warns about startup stock")
	_expect(not planner.preview(planner_state, {"alloy_smelting":-1}, "self", []).ok, "invalid module quantities are rejected")
	_expect(planner_state == unchanged_planner_state, "station previews do not mutate the real world")

	# Physical station construction: fee, cargo, builder travel, time and saves.
	var build_world = WorldScript.new()
	_expect(build_world.load_starter() == OK, "construction scenario loads")
	_disable_npc_trading(build_world)
	var build_player: Dictionary = build_world.state.ships[0]
	var builder: Dictionary = build_world._find_ship("npc_builder_001")
	var initial_build_money := _total_credits(build_world.state)
	_expect(builder.owner != build_world.state.player_faction_id and builder.sector == "verdant_trace" and int(builder.credits) == 0, "the independent builder starts at a real sector without invented money")
	_expect(not build_world.queue_fly_to(str(builder.id), "hearthreach"), "the player cannot directly command the NPC builder")
	var build_quote: Dictionary = build_world.construction.quote(build_world, "hearthreach", {"alloy_smelting":1}, "self", [])
	_expect(build_quote.ok and int(build_quote.fee) == 1500 and int(build_quote.materials.alloy_plates) == 28 and int(build_quote.ticks) == 50, "construction quote totals actual modules, builder fee, materials and work time")
	var dry_sector: Dictionary = build_world.construction.quote(build_world, "vellum_gate", {"ore_extraction":1}, "all", [])
	_expect(dry_sector.ok and " ".join(dry_sector.warnings).contains("No usable Ore deposit"), "construction warns when the chosen sector lacks the required deposit")
	var invalid_before: Dictionary = build_world.snapshot()
	_expect(not build_world.construction.place(build_world, "unknown", {"solar_cells":1}, "self", []).ok and build_world.snapshot() == invalid_before, "invalid construction sector has no side effects")
	var poor_build = WorldScript.new()
	poor_build.load_starter()
	poor_build.state.starting_credits = 100
	var poor_before: Dictionary = poor_build.snapshot()
	_expect(not poor_build.construction.place(poor_build, "hearthreach", {"solar_cells":1}, "self", []).ok and poor_build.snapshot() == poor_before, "insufficient builder fee rejects the whole construction transaction")
	var placed: Dictionary = build_world.construction.place(build_world, "hearthreach", {"alloy_smelting":1}, "self", [])
	_expect(placed.ok, "a valid plan creates a build site")
	var site: Dictionary = build_world.construction.find_site(build_world, str(placed.site_id))
	var outpost: Dictionary = build_world._find_station(str(site.station_id))
	_expect(int(build_world.state.starting_credits) == 23500 and int(builder.credits) == 1500 and _total_credits(build_world.state) == initial_build_money, "upfront fee transfers real player credits to the NPC builder")
	_expect(build_world.state.ledger.back().kind == "construction_fee" and outpost.owner == "player" and outpost.production.is_empty() and int(outpost.storage_capacity) == 0, "the ledger records the hire and the empty plot has no free production modules")
	_expect(save_store.save_game(test_root + "/construction-placed.json", build_world.snapshot()) == OK, "an empty build site is saveable immediately after placement")
	build_world.advance_ticks(25)
	_expect(site.status == "Needs materials" and int(site.completed) == 0 and not site.tasks[0].started and builder.sector == "verdant_trace", "the builder does not fabricate materials or start an unfunded module")
	build_world.construction.set_paused(build_world, str(site.id), true)
	build_world.construction.set_paused(build_world, str(site.id), false)
	_expect(site.status == "Needs materials", "resuming an unsupplied site immediately shows that materials are needed")
	_expect(not build_world.construction.deliver(build_world, "ship_001", str(site.id)).ok, "construction cargo cannot be delivered while undocked")
	_expect(build_world.queue_fly_to("ship_001", "vellum_gate"), "player sends the supply ship to the alloy market")
	build_world.advance_ticks(10)
	_expect(build_world.dock_ship("ship_001", "vellum_foundry").ok and build_world.trade("ship_001", "vellum_foundry", "alloy_plates", 28, true).ok, "player buys the actual construction materials")
	_expect(build_world.queue_fly_to("ship_001", "hearthreach"), "player returns the materials to the build sector")
	build_world.advance_ticks(10)
	_expect(build_world.dock_ship("ship_001", str(outpost.id)).ok, "supply ship docks at the actual site")
	_expect(build_world.construction.deliver(build_world, "ship_001", str(site.id)).ok and int(site.build_storage.alloy_plates) == 28 and int(build_player.cargo.alloy_plates) == 0, "physical cargo moves from the ship into separate build storage")
	_expect(save_store.save_game(test_root + "/construction-delivered.json", build_world.snapshot()) == OK, "delivered build storage is saveable before work starts")
	var delivered_once: Dictionary = build_world.snapshot()
	_expect(not build_world.construction.deliver(build_world, "ship_001", str(site.id)).ok and build_world.snapshot() == delivered_once, "repeating a delivery cannot duplicate materials")
	_expect(build_world.construction.set_paused(build_world, str(site.id), true), "construction can be paused")
	build_world.advance_ticks(15)
	_expect(int(site.completed) == 0 and not site.tasks[0].started and int(site.build_storage.alloy_plates) == 28, "paused construction retains materials and performs no work")
	_expect(build_world.construction.set_paused(build_world, str(site.id), false), "construction can resume")
	build_world.advance_ticks(1)
	_expect(site.status == "Builder en route" and builder.sector == "verdant_trace" and not builder.orders.is_empty(), "the hired builder starts a real route to the site")
	for _tick in range(20):
		build_world.advance_ticks(1)
		if site.tasks[0].started:
			break
	_expect(builder.sector == "hearthreach" and site.tasks[0].started and int(site.tasks[0].progress) > 0 and int(site.build_storage.alloy_plates) == 22, "arrival starts the first module and consumes its actual materials exactly once")
	var paused_progress := int(site.tasks[0].progress)
	build_world.construction.set_paused(build_world, str(site.id), true)
	build_world.advance_ticks(8)
	_expect(int(site.tasks[0].progress) == paused_progress and int(site.build_storage.alloy_plates) == 22, "pausing mid-module preserves progress and already committed materials")
	_expect(save_store.save_game(test_root + "/construction-paused.json", build_world.snapshot()) == OK, "paused in-progress work remains saveable")
	build_world.construction.set_paused(build_world, str(site.id), false)
	var mid_build_path := test_root + "/construction-mid.json"
	_expect(save_store.save_game(mid_build_path, build_world.snapshot()) == OK, "an in-progress construction site can be saved")
	var mid_build_read: Dictionary = save_store.load_game(mid_build_path)
	var resumed_build = WorldScript.new()
	_expect(bool(mid_build_read.get("ok", false)) and resumed_build.restore_snapshot(mid_build_read.state) == OK, "an in-progress build restores with its builder and materials")
	build_world.advance_ticks(100)
	resumed_build.advance_ticks(100)
	_expect(build_world.snapshot() == resumed_build.snapshot(), "construction and production continue deterministically after save/load")
	_expect(int(site.completed) == 3 and site.status == "Complete" and outpost.name == site.name and outpost.production.size() == 3 and int(outpost.storage_capacity) == 200, "completed modules become a real player-owned production station")
	_expect(int(site.build_storage.alloy_plates) == 0 and _total_credits(build_world.state) == initial_build_money, "the completed build consumed only its delivered materials and conserved credits")
	_expect(int(outpost.production[0].cycles) > 0 and int(outpost.production[1].cycles) > 0 and int(outpost.production[2].cycles) > 0 and int(build_world.state.construction_resources.hearthreach.deposits.ore) < 240, "the new station produces from sunlight, inputs and its finite sector reserve")
	_expect(save_store.save_game(test_root + "/construction-complete.json", build_world.snapshot()) == OK, "the completed player station remains saveable")
	var completed_read: Dictionary = save_store.load_game(test_root + "/construction-complete.json")
	_expect(bool(completed_read.get("ok", false)) and completed_read.state.construction_resources.hearthreach.deposits.ore == build_world.state.construction_resources.hearthreach.deposits.ore, "remaining finite sector resources survive save/load")
	var cargo_before_transfer: int = int(build_player.cargo.get("alloy_plates", 0))
	var station_before_transfer: int = int(outpost.stock.get("alloy_plates", 0))
	_expect(station_before_transfer > 0 and build_world.transfer_player_station("ship_001", str(outpost.id), "alloy_plates", 1, false).ok, "the player can take real output from their own station")
	_expect(int(build_player.cargo.alloy_plates) == cargo_before_transfer + 1 and int(outpost.stock.alloy_plates) == station_before_transfer - 1 and _total_credits(build_world.state) == initial_build_money, "station cargo transfers preserve goods and do not charge the player")
	var before_invalid_transfer: Dictionary = build_world.snapshot()
	_expect(not build_world.transfer_player_station("ship_001", "vellum_foundry", "alloy_plates", 1, true).ok and build_world.snapshot() == before_invalid_transfer, "free transfers cannot be used on NPC stations")
	var shared_world = WorldScript.new()
	shared_world.restore_snapshot(build_world.snapshot())
	var shared_first: Dictionary = shared_world._find_station(str(outpost.id))
	shared_first.production = [{"recipe_id":"ore_extraction", "progress":7, "cycles":0, "status":"Running"}]
	shared_first.stock = {"energy_cells":10, "ore":0, "alloy_plates":0}
	var shared_second: Dictionary = shared_first.duplicate(true)
	shared_second.id = "shared_resource_test"
	shared_world.state.stations.append(shared_second)
	shared_world.state.construction_resources.hearthreach.deposits.ore = 4
	shared_world.advance_ticks(1)
	_expect(int(shared_world.state.construction_resources.hearthreach.deposits.ore) == 0 and int(shared_first.stock.ore) + int(shared_second.stock.ore) == 4, "two player stations share and cannot overdraw a finite sector deposit")
	var queue_world = WorldScript.new()
	queue_world.load_starter()
	_disable_npc_trading(queue_world)
	var queue_first: Dictionary = queue_world.construction.place(queue_world, "hearthreach", {"solar_cells":1}, "self", [])
	var queue_second: Dictionary = queue_world.construction.place(queue_world, "hearthreach", {"solar_cells":1}, "self", [])
	var queue_site_one: Dictionary = queue_world.construction.find_site(queue_world, str(queue_first.site_id))
	var queue_site_two: Dictionary = queue_world.construction.find_site(queue_world, str(queue_second.site_id))
	queue_world._find_station("vellum_foundry").stock.alloy_plates -= 6
	queue_world.state.ships[0].cargo["alloy_plates"] = 6
	queue_world.dock_ship("ship_001", str(queue_site_two.station_id))
	queue_world.construction.deliver(queue_world, "ship_001", str(queue_site_two.id))
	queue_world.advance_ticks(40)
	_expect(int(queue_site_one.completed) == 0 and queue_site_one.status == "Needs materials" and int(queue_site_two.completed) == 1, "the builder skips an unready site and works on the next supplied site")
	var legacy_construction: Dictionary = saved_trip.duplicate(true)
	_strip_construction(legacy_construction)
	var legacy_construction_path := test_root + "/before-construction.json"
	_expect(save_store.save_game(legacy_construction_path, legacy_construction) == OK, "a pre-construction save remains readable")
	var legacy_construction_read: Dictionary = save_store.load_game(legacy_construction_path)
	var migrated_build = WorldScript.new()
	_expect(bool(legacy_construction_read.get("ok", false)) and migrated_build.restore_snapshot(legacy_construction_read.state) == OK, "a pre-construction save gains the builder and sector resources")
	var migrated_ship: Dictionary = migrated_build.state.ships[0].duplicate(true)
	migrated_ship.erase("build_supply")
	migrated_ship.erase("station_supply")
	migrated_ship.erase("captain_profile")
	migrated_ship.erase("crew_profile")
	migrated_ship.erase("payroll")
	_expect(migrated_ship == legacy_construction.ships[0] and migrated_build.state.ships[1] == legacy_construction.ships[1] and migrated_build.state.ledger == legacy_construction.ledger and migrated_build.state.starting_credits == legacy_construction.starting_credits, "construction migration preserves player property, NPC logistics, orders, credits and ledger")
	_expect(int(migrated_build._find_ship("npc_builder_001").credits) == 0 and migrated_build.state.build_sites.is_empty(), "migration adds no free money, sites or materials")
	var bad_construction: Dictionary = build_world.snapshot()
	bad_construction.build_sites[0].tasks[0].progress = 999
	_expect(save_store.save_game(test_root + "/bad-construction.json", bad_construction) != OK, "invalid completed build progress is rejected")
	bad_construction = build_world.snapshot()
	bad_construction.build_sites[0].build_storage.alloy_plates = 1
	_expect(save_store.save_game(test_root + "/bad-construction.json", bad_construction) != OK, "save validation rejects excess build materials")
	var construction_version_path := test_root + "/construction-version.json"
	_expect(save_store.save_game(construction_version_path, build_world.snapshot()) == OK and save_store.save_game(construction_version_path, build_world.snapshot()) == OK, "construction version test has a backup")
	var future_construction: Dictionary = build_world.snapshot()
	future_construction.construction_version = 3
	var construction_payload := Marshalls.variant_to_base64(future_construction, false)
	var future_construction_file := FileAccess.open(construction_version_path, FileAccess.WRITE)
	future_construction_file.store_string(JSON.stringify({"format_version":1, "payload":construction_payload, "checksum":construction_payload.sha256_text()}))
	future_construction_file.close()
	_expect(save_store.load_game(construction_version_path).get("reason") == "unsupported", "future construction data is not silently replaced by an older backup")

	# The construction queue may be reprioritised only before material consumption.
	var reorder_world = WorldScript.new()
	_expect(reorder_world.load_starter() == OK, "construction reorder scenario loads")
	_disable_npc_trading(reorder_world)
	var reorder_plan: Dictionary = reorder_world.construction.place(reorder_world, "hearthreach", {"alloy_smelting":1}, "self", [])
	var reorder_site: Dictionary = reorder_world.construction.find_site(reorder_world, str(reorder_plan.site_id))
	var initial_reorder_ids: Array[String] = []
	for task in reorder_site.tasks:
		initial_reorder_ids.append(str(task.recipe_id))
	var reorder_funds := _total_credits(reorder_world.state)
	var before_required: Dictionary = reorder_world.construction.remaining_materials(reorder_site).duplicate(true)
	var reorder_ledger: Array = reorder_world.state.ledger.duplicate(true)
	_expect(reorder_site.tasks.size() == 3 and reorder_world.construction.first_editable_index(reorder_site) == 0, "all queued modules are initially editable")
	var reorder_first: Dictionary = reorder_world.construction.move_queued_module(reorder_world, str(reorder_site.id), 2, -1)
	_expect(reorder_first.ok and int(reorder_first.new_index) == 1 and reorder_site.tasks[1].recipe_id == initial_reorder_ids[2] and reorder_site.tasks[2].recipe_id == initial_reorder_ids[1], "moving a pending module up swaps exactly two unstarted tasks")
	_expect(reorder_world.construction.remaining_materials(reorder_site) == before_required and _total_credits(reorder_world.state) == reorder_funds and reorder_world.state.ledger == reorder_ledger, "reordering never fabricates materials or charges or refunds fees")
	var reverse_reorder: Dictionary = reorder_world.construction.move_queued_module(reorder_world, str(reorder_site.id), 1, 1)
	_expect(reverse_reorder.ok and reorder_site.tasks[1].recipe_id == initial_reorder_ids[1] and reorder_site.tasks[2].recipe_id == initial_reorder_ids[2], "moving a queued module down restores original sequence")
	var invalid_move_state: Dictionary = reorder_world.snapshot()
	_expect(not reorder_world.construction.move_queued_module(reorder_world, str(reorder_site.id), 0, -1).ok and not reorder_world.construction.move_queued_module(reorder_world, str(reorder_site.id), 0, 2).ok and reorder_world.snapshot() == invalid_move_state, "out-of-bounds and multi-position queue changes are rejected atomically")
	var reorder_path := test_root + "/construction-reordered.json"
	_expect(save_store.save_game(reorder_path, reorder_world.snapshot()) == OK, "reordered construction queue is saveable")
	var reorder_read: Dictionary = save_store.load_game(reorder_path)
	var reorder_resume = WorldScript.new()
	_expect(bool(reorder_read.get("ok", false)) and reorder_resume.restore_snapshot(reorder_read.state) == OK and reorder_resume.snapshot() == reorder_world.snapshot(), "queued priority persists through save/load")
	reorder_world._find_station("vellum_foundry").stock.alloy_plates -= 28
	reorder_world.state.ships[0].cargo.alloy_plates = 28
	reorder_world.dock_ship("ship_001", str(reorder_site.station_id))
	reorder_world.construction.deliver(reorder_world, "ship_001", str(reorder_site.id))
	for _step in range(35):
		reorder_world.advance_ticks(1)
		if reorder_site.tasks[0].started:
			break
	_expect(reorder_site.tasks[0].started and reorder_world.construction.first_editable_index(reorder_site) == 1, "active construction locks the started module and leaves later modules editable")
	var started_move_state: Dictionary = reorder_world.snapshot()
	_expect(not reorder_world.construction.move_queued_module(reorder_world, str(reorder_site.id), 0, 1).ok and reorder_world.snapshot() == started_move_state, "an already started module cannot be moved while materials are committed")
	_expect(reorder_world.construction.move_queued_module(reorder_world, str(reorder_site.id), 2, -1).ok and reorder_site.tasks[1].recipe_id == initial_reorder_ids[2], "later unstarted modules can still be reordered during active construction")
	_expect(save_store.save_game(test_root + "/construction-reorder-active.json", reorder_world.snapshot()) == OK, "reordering behind an active builder remains saveable")
	reorder_world.advance_ticks(100)
	_expect(int(reorder_site.completed) == 3 and reorder_world._find_station(str(reorder_site.station_id)).production.size() == 3, "builder eventually commissions every module exactly once in revised order")
	var finished_move_state: Dictionary = reorder_world.snapshot()
	_expect(not reorder_world.construction.move_queued_module(reorder_world, str(reorder_site.id), 2, -1).ok and reorder_world.snapshot() == finished_move_state, "completed construction sequence is locked")
	var reorder_cancel = WorldScript.new()
	reorder_cancel.load_starter()
	var cancelled_reorder_id: String = reorder_cancel.construction.place(reorder_cancel, "hearthreach", {"solar_cells":2}, "self", []).site_id
	reorder_cancel.construction.cancel(reorder_cancel, cancelled_reorder_id)
	var cancelled_reorder_state: Dictionary = reorder_cancel.snapshot()
	_expect(not reorder_cancel.construction.move_queued_module(reorder_cancel, cancelled_reorder_id, 1, -1).ok and reorder_cancel.snapshot() == cancelled_reorder_state, "cancelled build sites cannot resume work by reordering their old queue")

	# Cancellation refunds only unstarted work and never materialises cargo.
	var cancel_world = WorldScript.new()
	_expect(cancel_world.load_starter() == OK, "cancellation test world loads")
	_disable_npc_trading(cancel_world)
	var cancel_initial := _total_credits(cancel_world.state)
	var cancel_plan: Dictionary = cancel_world.construction.place(cancel_world, "hearthreach", {"solar_cells":2}, "self", [])
	var cancel_site: Dictionary = cancel_world.construction.find_site(cancel_world, str(cancel_plan.site_id))
	var cancel_station: Dictionary = cancel_world._find_station(str(cancel_site.station_id))
	var cancel_ship: Dictionary = cancel_world.state.ships[0]
	cancel_world._find_station("vellum_foundry").stock.alloy_plates -= 12
	cancel_ship.cargo.alloy_plates = 12
	_expect(cancel_world.dock_ship("ship_001", str(cancel_station.id)).ok and cancel_world.construction.deliver(cancel_world, "ship_001", str(cancel_site.id)).ok, "cancel test delivers real alloy to the plot")
	var original_stored: int = int(cancel_site.build_storage.alloy_plates)
	var fresh_cancel: Dictionary = cancel_world.construction.cancel(cancel_world, str(cancel_site.id))
	_expect(fresh_cancel.ok and int(fresh_cancel.refund) == 600 and int(cancel_world.state.starting_credits) == 25000 and int(cancel_world._find_ship("npc_builder_001").credits) == 0 and _total_credits(cancel_world.state) == cancel_initial, "unstarted cancellation returns the complete fee from the builder without minting credits")
	_expect(cancel_site.cancelled and cancel_site.status == "Cancelled" and cancel_site.tasks.size() == 2 and int(cancel_site.completed) == 0 and int(cancel_site.build_storage.alloy_plates) == original_stored, "cancelled plot preserves every delivered unused unit and its original queue")
	_expect(cancel_world.state.ledger.back().kind == "construction_refund" and int(cancel_world.state.ledger.back().amount) == 600, "fee refund has a positive ledger entry")
	var cancelled_snapshot: Dictionary = cancel_world.snapshot()
	_expect(not cancel_world.construction.cancel(cancel_world, str(cancel_site.id)).ok and cancel_world.snapshot() == cancelled_snapshot, "repeated cancellation cannot pay twice or alter stored materials")
	_expect(not cancel_world.construction.set_paused(cancel_world, str(cancel_site.id), true) and not cancel_world.construction.deliver(cancel_world, "ship_001", str(cancel_site.id)).ok and not cancel_world.build_supply.assign(cancel_world, "ship_001", str(cancel_site.id)).ok, "cancelled construction rejects resuming work and fresh deliveries or suppliers")
	cancel_ship.cargo_capacity = 7
	var first_recovery: Dictionary = cancel_world.construction.recover(cancel_world, "ship_001", str(cancel_site.id))
	_expect(first_recovery.ok and int(first_recovery.quantity) == 7 and int(cancel_ship.cargo.alloy_plates) == 7 and int(cancel_site.build_storage.alloy_plates) == 5, "recovery respects real free cargo volume and retains overflow")
	var recovery_before: Dictionary = cancel_world.snapshot()
	_expect(not cancel_world.construction.recover(cancel_world, "ship_001", str(cancel_site.id)).ok and cancel_world.snapshot() == recovery_before, "recovery cannot duplicate materials with a full ship")
	cancel_ship.cargo_capacity = 20
	_expect(cancel_world.construction.recover(cancel_world, "ship_001", str(cancel_site.id)).ok and int(cancel_ship.cargo.alloy_plates) == 12 and int(cancel_site.build_storage.alloy_plates) == 0, "second physical trip can recover remaining materials without loss")
	_expect(cancel_world.state.ledger.back().kind == "construction_recovery", "dockside recovery is recorded without a fictitious sale")
	var canceled_path := test_root + "/construction-cancelled.json"
	_expect(save_store.save_game(canceled_path, cancel_world.snapshot()) == OK, "cancelled empty plot with recovered cargo remains saveable")
	var canceled_read: Dictionary = save_store.load_game(canceled_path)
	var canceled_resume = WorldScript.new()
	_expect(bool(canceled_read.get("ok", false)) and canceled_resume.restore_snapshot(canceled_read.state) == OK and canceled_resume.snapshot() == cancel_world.snapshot(), "refunds, cancelled queue and recovered cargo persist through save and load")
	cancel_world.advance_ticks(30)
	_expect(cancel_site.status == "Cancelled" and int(cancel_site.completed) == 0 and cancel_station.production.is_empty(), "a cancelled site never restarts work after time advances")

	# A started module has consumed materials; finish it, cancelling only later tasks.
	var partial_cancel = WorldScript.new()
	partial_cancel.load_starter()
	_disable_npc_trading(partial_cancel)
	var partial_plan: Dictionary = partial_cancel.construction.place(partial_cancel, "hearthreach", {"solar_cells":3}, "self", [])
	var partial_site: Dictionary = partial_cancel.construction.find_site(partial_cancel, str(partial_plan.site_id))
	var partial_station: Dictionary = partial_cancel._find_station(str(partial_site.station_id))
	partial_cancel._find_station("vellum_foundry").stock.alloy_plates -= 18
	partial_cancel.state.ships[0].cargo.alloy_plates = 18
	partial_cancel.dock_ship("ship_001", str(partial_station.id))
	partial_cancel.construction.deliver(partial_cancel, "ship_001", str(partial_site.id))
	for _step in range(35):
		partial_cancel.advance_ticks(1)
		if partial_site.tasks[0].started:
			break
	_expect(partial_site.tasks[0].started and int(partial_site.completed) == 0 and int(partial_site.build_storage.alloy_plates) == 12, "builder begins one module and consumes exactly six materials before cancellation")
	var part_cancel_result: Dictionary = partial_cancel.construction.cancel(partial_cancel, str(partial_site.id))
	_expect(part_cancel_result.ok and int(part_cancel_result.refund) == 600 and int(partial_cancel._find_ship("npc_builder_001").credits) == 300 and int(partial_cancel.state.starting_credits) == 24700, "partial cancellation refunds only two unstarted modules, not the active module")
	_expect(partial_site.status == "Finishing current module" and int(partial_site.build_storage.alloy_plates) == 12, "active build can finish while the remaining unused materials stay stored")
	var partial_path := test_root + "/construction-cancel-active.json"
	_expect(save_store.save_game(partial_path, partial_cancel.snapshot()) == OK, "a cancellation during active construction is saveable")
	var partial_read: Dictionary = save_store.load_game(partial_path)
	var partial_resume = WorldScript.new()
	_expect(bool(partial_read.get("ok", false)) and partial_resume.restore_snapshot(partial_read.state) == OK, "active cancellation restores without resetting progress")
	partial_cancel.advance_ticks(80)
	partial_resume.advance_ticks(80)
	_expect(partial_cancel.snapshot() == partial_resume.snapshot(), "a cancelled active build finishes deterministically after saving")
	_expect(partial_site.cancelled and partial_site.status == "Cancelled" and int(partial_site.completed) == 1 and partial_station.production.size() == 1 and int(partial_station.storage_capacity) == 40 and int(partial_site.build_storage.alloy_plates) == 12, "the started module finishes once while both cancelled modules remain unbuilt and recoverable")
	_expect(str(partial_cancel._find_ship("npc_builder_001").build_assignment).is_empty(), "the builder is released after finishing the sole active module")
	_expect(partial_cancel.construction.recover(partial_cancel, "ship_001", str(partial_site.id)).ok and int(partial_cancel.state.ships[0].cargo.alloy_plates) == 12, "physical material recovery still works after a partial station is commissioned")
	var fully_built_snapshot: Dictionary = build_world.snapshot()
	_expect(not build_world.construction.cancel(build_world, str(site.id)).ok and build_world.snapshot() == fully_built_snapshot, "fully completed station cannot be cancelled or refunded")

	# Cancelling a supply run does not erase ship orders or cargo in transit.
	var moving_cancel = WorldScript.new()
	moving_cancel.load_starter()
	_disable_npc_trading(moving_cancel)
	var moving_site_id: String = moving_cancel.construction.place(moving_cancel, "cinder_veil", {"solar_cells":1}, "self", []).site_id
	moving_cancel._find_station("vellum_foundry").stock.alloy_plates -= 6
	moving_cancel.state.ships[0].cargo.alloy_plates = 6
	_expect(moving_cancel.build_supply.assign(moving_cancel, "ship_001", moving_site_id).ok, "build supplier can be assigned before its supply journey")
	moving_cancel.advance_ticks(1)
	var moving_ship: Dictionary = moving_cancel.state.ships[0]
	var original_moving_orders: Array = moving_ship.orders.duplicate(true)
	_expect(not original_moving_orders.is_empty() and moving_ship.build_supply.enabled, "build supplier begins a real sector route")
	_expect(moving_cancel.construction.cancel(moving_cancel, moving_site_id).ok and not moving_ship.build_supply.enabled and moving_ship.role == "Unassigned" and moving_ship.orders == original_moving_orders and int(moving_ship.cargo.alloy_plates) == 6, "cancellation releases an active supplier without discarding queued orders or onboard goods")
	_expect(save_store.save_game(test_root + "/construction-cancel-supplier.json", moving_cancel.snapshot()) == OK, "cancelled construction with an in-flight former supplier remains saveable")
	moving_cancel.advance_ticks(35)
	_expect(moving_ship.orders.is_empty() and int(moving_ship.cargo.alloy_plates) == 6 and int(moving_cancel.construction.find_site(moving_cancel, moving_site_id).build_storage.get("alloy_plates", 0)) == 0, "former supplier completes existing travel but does not deliver into a cancelled plot")

	# Construction schema v1 saves migrate without altering completed work or money.
	var legacy_cancel: Dictionary = build_world.snapshot()
	legacy_cancel.construction_version = 1
	for old_site in legacy_cancel.build_sites:
		old_site.erase("cancelled")
		old_site.erase("refunded_fee")
	var legacy_cancel_path := test_root + "/construction-v1-upgrade.json"
	_expect(save_store.save_game(legacy_cancel_path, legacy_cancel) == OK, "a legacy construction-v1 save remains readable")
	var legacy_cancel_read: Dictionary = save_store.load_game(legacy_cancel_path)
	var legacy_cancel_upgraded = WorldScript.new()
	_expect(bool(legacy_cancel_read.get("ok", false)) and legacy_cancel_upgraded.restore_snapshot(legacy_cancel_read.state) == OK and legacy_cancel_upgraded.state.construction_version == 2, "construction v1 upgrades to v2 without requiring a fresh start")
	_expect(legacy_cancel_upgraded.state.starting_credits == legacy_cancel.starting_credits and legacy_cancel_upgraded.state.ledger == legacy_cancel.ledger and not legacy_cancel_upgraded.state.build_sites[0].cancelled and int(legacy_cancel_upgraded.state.build_sites[0].refunded_fee) == 0, "construction migration preserves credit history and live station state")
	var bad_refund: Dictionary = partial_cancel.snapshot()
	bad_refund.build_sites[0].refunded_fee += 1
	_expect(save_store.save_game(test_root + "/construction-bad-refund.json", bad_refund) != OK, "save validation rejects invented or mismatched cancellation refunds")

	# Automated build supply makes real trips and respects money, cargo and saves.
	var supply_world = WorldScript.new()
	supply_world.load_starter()
	_disable_npc_trading(supply_world)
	var supply_player: Dictionary = supply_world.state.ships[0]
	supply_player.cargo_capacity = 5
	var supply_credits := _total_credits(supply_world.state)
	var supply_foundry: Dictionary = supply_world._find_station("vellum_foundry")
	var original_stock := int(supply_foundry.stock.alloy_plates)
	var supply_placement: Dictionary = supply_world.construction.place(supply_world, "hearthreach", {"solar_cells":3}, "self", [])
	var supply_site: Dictionary = supply_world.construction.find_site(supply_world, str(supply_placement.site_id))
	supply_world.set_player_trader("ship_001", true)
	_expect(supply_world.build_supply.assign(supply_world, "ship_001", str(supply_site.id)).ok and not supply_player.player_trader.enabled and supply_player.role == "Build Supplier", "assigning build supply changes the existing ship role without creating another ship")
	supply_world.advance_ticks(1)
	_expect(supply_player.build_supply.phase == "to_source" and not supply_player.orders.is_empty() and int(supply_foundry.stock.alloy_plates) == original_stock, "supplier physically travels to a real market before buying")
	supply_world.advance_ticks(3)
	var supply_path := test_root + "/supply-travel.json"
	_expect(save_store.save_game(supply_path, supply_world.snapshot()) == OK, "an automatic supplier can be saved while travelling")
	var supply_read: Dictionary = save_store.load_game(supply_path)
	var supply_restored = WorldScript.new()
	_expect(bool(supply_read.get("ok", false)) and supply_restored.restore_snapshot(supply_read.state) == OK, "a supplier restores its destination and current route")
	supply_world.advance_ticks(250)
	supply_restored.advance_ticks(250)
	_expect(supply_world.snapshot() == supply_restored.snapshot(), "automatic supply continues deterministically after save and reload")
	_expect(int(supply_site.completed) == 3 and not supply_player.build_supply.enabled and supply_player.role == "Unassigned", "multiple cargo-sized trips supply the site and the role ends after delivery")
	_expect(original_stock - int(supply_foundry.stock.alloy_plates) == 18 and int(supply_world.state.starting_credits) + int(supply_player.payroll.total_paid) == 25000 - 900 - 18 * 20, "the supplier buys exactly the required real materials at the market price")
	_expect(_total_credits(supply_world.state) == supply_credits and int(supply_player.cargo.get("alloy_plates", 0)) == 0, "repeated supply trips conserve credits and do not fabricate or strand required cargo")

	var poor_supplier = WorldScript.new()
	poor_supplier.load_starter()
	_disable_npc_trading(poor_supplier)
	var poor_site_id: String = poor_supplier.construction.place(poor_supplier, "hearthreach", {"solar_cells":1}, "self", []).site_id
	poor_supplier.state.starting_credits = 0
	poor_supplier.build_supply.assign(poor_supplier, "ship_001", poor_site_id)
	poor_supplier.advance_ticks(1)
	_expect(poor_supplier.state.ships[0].status == "Waiting for credits" and poor_supplier.state.ships[0].build_supply.enabled and poor_supplier.state.ships[0].cargo.is_empty(), "a supplier waits clearly when it cannot afford materials")
	poor_supplier._find_station("hearth_exchange").credits -= 120
	poor_supplier.state.starting_credits = 120
	poor_supplier.advance_ticks(80)
	_expect(int(poor_supplier.construction.find_site(poor_supplier, poor_site_id).completed) == 1, "a supplier automatically resumes when funds become available")
	var onboard_supply = WorldScript.new()
	onboard_supply.load_starter()
	_disable_npc_trading(onboard_supply)
	var onboard_site_id: String = onboard_supply.construction.place(onboard_supply, "hearthreach", {"solar_cells":1}, "self", []).site_id
	onboard_supply._find_station("vellum_foundry").stock.alloy_plates -= 6
	onboard_supply.state.ships[0].cargo.alloy_plates = 6
	onboard_supply.state.starting_credits = 0
	onboard_supply.build_supply.assign(onboard_supply, "ship_001", onboard_site_id)
	onboard_supply.advance_ticks(1)
	_expect(int(onboard_supply.state.ships[0].cargo.alloy_plates) == 0 and int(onboard_supply.construction.find_site(onboard_supply, onboard_site_id).build_storage.alloy_plates) == 6 and int(onboard_supply.state.starting_credits) == 0, "a supplier delivers matching cargo already aboard without buying anything")
	var full_supplier = WorldScript.new()
	full_supplier.load_starter()
	_disable_npc_trading(full_supplier)
	var full_site_id: String = full_supplier.construction.place(full_supplier, "hearthreach", {"solar_cells":1}, "self", []).site_id
	full_supplier.state.ships[0].cargo_capacity = 1
	full_supplier._find_station("hearth_exchange").stock.energy_cells -= 1
	full_supplier.state.ships[0].cargo.energy_cells = 1
	full_supplier.build_supply.assign(full_supplier, "ship_001", full_site_id)
	full_supplier.advance_ticks(1)
	_expect(full_supplier.state.ships[0].status == "Waiting for cargo space" and int(full_supplier.state.ships[0].cargo.energy_cells) == 1, "a full hold causes a visible wait without discarding unrelated cargo")
	var no_stock = WorldScript.new()
	no_stock.load_starter()
	_disable_npc_trading(no_stock)
	var no_stock_site: String = no_stock.construction.place(no_stock, "hearthreach", {"solar_cells":1}, "self", []).site_id
	no_stock._find_station("vellum_foundry").stock.alloy_plates = 0
	no_stock._find_station("cinder_depot").stock.alloy_plates = 0
	no_stock.build_supply.assign(no_stock, "ship_001", no_stock_site)
	no_stock.advance_ticks(1)
	_expect(no_stock.state.ships[0].status == "Waiting for material stock", "a supplier reports a lack of reachable material stock")

	var cancelled_supply = WorldScript.new()
	cancelled_supply.load_starter()
	_disable_npc_trading(cancelled_supply)
	var cancelled_site: String = cancelled_supply.construction.place(cancelled_supply, "hearthreach", {"solar_cells":1}, "self", []).site_id
	cancelled_supply.build_supply.assign(cancelled_supply, "ship_001", cancelled_site)
	for _step in range(30):
		cancelled_supply.advance_ticks(1)
		if cancelled_supply.state.ships[0].build_supply.phase == "to_site" and not cancelled_supply.state.ships[0].orders.is_empty():
			break
	var in_transit: Dictionary = cancelled_supply.state.ships[0]
	var kept_cargo: int = int(in_transit.cargo.get("alloy_plates", 0))
	var kept_orders: Array = in_transit.orders.duplicate(true)
	_expect(kept_cargo == 6 and not kept_orders.is_empty(), "supplier carries purchased materials on its return trip")
	cancelled_supply.set_player_trader("ship_001", false)
	_expect(not in_transit.build_supply.enabled and int(in_transit.cargo.alloy_plates) == kept_cargo and in_transit.orders == kept_orders, "changing role stops supply without cancelling orders or taking cargo")
	cancelled_supply.advance_ticks(15)
	_expect(int(in_transit.cargo.alloy_plates) == kept_cargo and int(cancelled_supply.construction.find_site(cancelled_supply, cancelled_site).build_storage.get("alloy_plates", 0)) == 0, "stopped automation does not later deliver retained cargo")

	var competing_supply = WorldScript.new()
	competing_supply.load_starter()
	_disable_npc_trading(competing_supply)
	var rival_ship: Dictionary = competing_supply.state.ships[0].duplicate(true)
	rival_ship.id = "ship_002"
	rival_ship.name = "Second Light"
	competing_supply.personnel.initialize_ship(rival_ship, int(competing_supply.state.tick), "hearth_exchange")
	competing_supply.state.ships.append(rival_ship)
	var competing_supply_site: String = competing_supply.construction.place(competing_supply, "hearthreach", {"solar_cells":1}, "self", []).site_id
	competing_supply.build_supply.assign(competing_supply, "ship_001", competing_supply_site)
	competing_supply.build_supply.assign(competing_supply, "ship_002", competing_supply_site)
	var compete_stock: int = int(competing_supply._find_station("vellum_foundry").stock.alloy_plates)
	competing_supply.advance_ticks(80)
	_expect(compete_stock - int(competing_supply._find_station("vellum_foundry").stock.alloy_plates) == 6, "suppliers account for each other's purchased in-transit materials and do not buy twice")
	_expect(int(competing_supply.construction.find_site(competing_supply, competing_supply_site).completed) == 1 and save_store.save_game(test_root + "/two-suppliers.json", competing_supply.snapshot()) == OK, "competing_supply suppliers finish with a valid save and a functioning module")

	var owned_supply = WorldScript.new()
	owned_supply.restore_snapshot(build_world.snapshot())
	_disable_npc_trading(owned_supply)
	var owned_station: Dictionary = owned_supply._find_station(str(outpost.id))
	owned_supply.transfer_player_station("ship_001", str(owned_station.id), "alloy_plates", 1, true)
	owned_supply._find_station("vellum_foundry").stock.alloy_plates -= 6
	owned_station.stock.alloy_plates = int(owned_station.stock.alloy_plates) + 6
	for module in owned_station.production:
		module.progress = 0
	var owned_site_id: String = owned_supply.construction.place(owned_supply, "hearthreach", {"solar_cells":1}, "self", []).site_id
	var before_owned_credits: int = int(owned_supply.state.starting_credits)
	var before_owned_payroll: int = int(owned_supply.state.ships[0].payroll.total_paid)
	var before_owned_stock: int = int(owned_station.stock.alloy_plates)
	owned_supply.build_supply.assign(owned_supply, "ship_001", owned_site_id)
	owned_supply.advance_ticks(1)
	_expect(int(owned_station.stock.alloy_plates) == before_owned_stock - 6 and int(owned_supply.state.starting_credits) + int(owned_supply.state.ships[0].payroll.total_paid) - before_owned_payroll == before_owned_credits, "automatic supply prioritizes free physical stock at a player station")
	_expect(int(owned_supply.construction.find_site(owned_supply, owned_site_id).build_storage.get("alloy_plates", 0)) == 6 or owned_supply.construction.find_site(owned_supply, owned_site_id).tasks[0].started, "owned station stock is transferred to the build site before use")

	var old_supply: Dictionary = saved_trip.duplicate(true)
	_strip_archives(old_supply)
	old_supply.erase("build_supply_version")
	for old_ship in old_supply.ships:
		old_ship.erase("build_supply")
	_expect(save_store.save_game(test_root + "/before-supply.json", old_supply) == OK, "a construction-era save without supply automation remains readable")
	var old_supply_load: Dictionary = save_store.load_game(test_root + "/before-supply.json")
	var supply_upgrade = WorldScript.new()
	_expect(bool(old_supply_load.get("ok", false)) and supply_upgrade.restore_snapshot(old_supply_load.state) == OK and not supply_upgrade.state.ships[0].build_supply.enabled, "older saves gain an inactive build supplier")
	var upgraded_ship: Dictionary = supply_upgrade.state.ships[0].duplicate(true)
	upgraded_ship.erase("build_supply")
	upgraded_ship.erase("station_supply")
	upgraded_ship.erase("captain_profile")
	upgraded_ship.erase("crew_profile")
	upgraded_ship.erase("payroll")
	_expect(upgraded_ship == old_supply.ships[0] and supply_upgrade.state.ledger == old_supply.ledger and supply_upgrade.state.starting_credits == old_supply.starting_credits, "supply migration preserves ship orders, cargo, credits and ledger")
	var invalid_supply: Dictionary = supply_world.snapshot()
	invalid_supply.ships[0].build_supply.enabled = true
	invalid_supply.ships[0].build_supply.site_id = "unknown"
	_expect(save_store.save_game(test_root + "/bad-supply.json", invalid_supply) != OK, "save validation rejects supplier assignments to missing sites")
	var future_supply: Dictionary = supply_world.snapshot()
	future_supply.build_supply_version = 2
	var future_supply_payload := Marshalls.variant_to_base64(future_supply, false)
	var future_supply_path := test_root + "/supply-version.json"
	_expect(save_store.save_game(future_supply_path, supply_world.snapshot()) == OK and save_store.save_game(future_supply_path, supply_world.snapshot()) == OK, "supply version test has a valid backup")
	var future_supply_file := FileAccess.open(future_supply_path, FileAccess.WRITE)
	future_supply_file.store_string(JSON.stringify({"format_version":1, "payload":future_supply_payload, "checksum":future_supply_payload.sha256_text()}))
	future_supply_file.close()
	_expect(save_store.load_game(future_supply_path).get("reason") == "unsupported", "future supply data cannot silently fall back to an older save")

	# Historical stations, genuine upkeep and a complete physical copying chain.
	var history_world = WorldScript.new()
	_expect(history_world.load_starter() == OK, "the archive scenario loads")
	_disable_npc_trading(history_world)
	var archive_count := 0
	var archive_owners: Dictionary = {}
	var archive_media: Dictionary = {}
	for station in history_world.state.stations:
		if not station.has("archive"):
			continue
		archive_count += 1
		archive_owners[station.owner] = true
		var catalog: Dictionary = history_world.archives.definition(str(station.id))
		_expect(station.owner != "player" and catalog.owner == station.owner and catalog.sector == station.sector, "archive is a real station belonging to its civilization: " + str(station.id))
		_expect(catalog.records.size() == 5 and not catalog.research_subjects.is_empty(), "archive has a collection and research subjects: " + str(station.id))
		for record in catalog.records:
			archive_media[str(record.medium)] = true
	_expect(archive_count == 4 and archive_owners.size() == 4 and archive_media.size() >= 12, "the four faction archives contain varied physical record formats")
	var archive_station: Dictionary = history_world._find_station("auroran_archive")
	var original_catalog: Dictionary = history_world.archives.definition("auroran_archive").duplicate(true)
	var before_unread: Dictionary = history_world.snapshot()
	_expect(not history_world.archives.read(history_world, "ship_001", "auroran_archive").ok and history_world.snapshot() == before_unread, "reading records requires a visit and cannot unlock them remotely")
	_expect(history_world.dock_ship("ship_001", "auroran_archive").ok, "the player's ship can dock at the faction archive")
	var read_result: Dictionary = history_world.archives.read(history_world, "ship_001", "auroran_archive")
	_expect(read_result.ok and read_result.first_visit and read_result.entry.homeworld == "Kaelith" and archive_station.archive.status == "Needs energy", "a docked visitor can read original records even when the archive needs upkeep")
	_expect(not history_world.archives.read(history_world, "ship_001", "auroran_archive").first_visit and history_world.state.visited_archives.size() == 1, "revisiting cannot duplicate the saved discovery")
	var history_save := test_root + "/history-visited.json"
	_expect(save_store.save_game(history_save, history_world.snapshot()) == OK, "an archive visit saves")
	var history_read: Dictionary = save_store.load_game(history_save)
	var history_restore = WorldScript.new()
	_expect(bool(history_read.get("ok", false)) and history_restore.restore_snapshot(history_read.state) == OK and history_restore.state.visited_archives == ["auroran_archive"], "archive visits survive loading")
	var history_credits := _total_credits(history_world.state)
	var sponsor_balance: int = int(history_world._find_station("hearth_exchange").credits)
	history_world.advance_ticks(30)
	_expect(int(archive_station.credits) == 60 and int(history_world._find_station("hearth_exchange").credits) == sponsor_balance - 60 and _total_credits(history_world.state) == history_credits, "the faction funds its archive by transferring real credits from its own station")
	_expect(int(archive_station.stock.energy_cells) == 0 and archive_station.archive.status == "Needs energy" and int(archive_station.archive.cycles) == 0, "an unfuelled archive reports its shortage without inventing energy or upkeep")
	_expect(history_world.dock_ship("ship_001", "hearth_exchange").ok and history_world.trade("ship_001", "hearth_exchange", "energy_cells", 6, true).ok, "the player buys real energy for the archive")
	_expect(history_world.dock_ship("ship_001", "auroran_archive").ok and history_world.trade("ship_001", "auroran_archive", "energy_cells", 4, false).ok, "the archive buys physical energy using its faction-funded budget")
	_expect(history_world.queue_fly_to("ship_001", "vellum_gate"), "the player travels to purchase archival manufacturing supplies")
	history_world.advance_ticks(10)
	_expect(history_world.dock_ship("ship_001", "vellum_foundry").ok and history_world.trade("ship_001", "vellum_foundry", "alloy_plates", 20, true).ok, "the player purchases real alloy from a market")
	_expect(history_world.queue_fly_to("ship_001", "hearthreach"), "the player carries the alloy back to the archive sector")
	history_world.advance_ticks(10)
	_expect(history_world.dock_ship("ship_001", "auroran_archive").ok, "the player docks at the archive again")
	history_world.advance_ticks(10)
	_expect(int(archive_station.archive.staff_credits) == 2 and int(archive_station.archive.cycles) == 1 and int(archive_station.stock.energy_cells) == 3, "upkeep consumes physical energy and moves wages to the archive staff")
	_expect(history_world.trade("ship_001", "auroran_archive", "alloy_plates", 1, false).ok, "the archive buys an alloy input from the visiting ship")
	history_world.advance_ticks(5)
	var copying_path := test_root + "/archive-copying.json"
	_expect(save_store.save_game(copying_path, history_world.snapshot()) == OK, "archive upkeep and media production save mid-cycle")
	var copying_read: Dictionary = save_store.load_game(copying_path)
	var copying_reload = WorldScript.new()
	_expect(bool(copying_read.get("ok", false)) and copying_reload.restore_snapshot(copying_read.state) == OK, "archive operations restore mid-cycle")
	history_world.advance_ticks(19)
	copying_reload.advance_ticks(19)
	_expect(history_world.snapshot() == copying_reload.snapshot(), "archive funding, upkeep and production continue deterministically after reload")
	_expect(int(archive_station.stock.blank_media) == 3 and int(archive_station.stock.recorded_data) == 1, "the archive turns alloy and energy into blank media and a data copy")
	_expect(history_world.archives.definition("auroran_archive") == original_catalog and int(archive_station.production[1].cycles) == 1, "copying does not consume or alter the historical originals")
	_expect(_total_credits(history_world.state) == history_credits, "archive funding, wages and player trade conserve credits")
	_expect(history_world.trade("ship_001", "auroran_archive", "recorded_data", 1, true).ok, "the player can buy a produced data copy")
	var archive_plan: Dictionary = history_world.construction.quote(history_world, "hearthreach", {"media_fabrication":1, "data_reproduction":1}, "all", [])
	_expect(archive_plan.ok and int(archive_plan.fee) == 1400 and int(archive_plan.materials.alloy_plates) == 18 and " ".join(archive_plan.warnings).contains("Recorded Data"), "the station planner offers a player archive and warns about its reusable source")
	var archive_plot: Dictionary = history_world.construction.place(history_world, "hearthreach", {"media_fabrication":1, "data_reproduction":1}, "all", [])
	var player_archive_site: Dictionary = history_world.construction.find_site(history_world, str(archive_plot.site_id))
	_expect(archive_plot.ok and history_world.dock_ship("ship_001", str(player_archive_site.station_id)).ok and history_world.construction.deliver(history_world, "ship_001", str(player_archive_site.id)).ok, "a player-owned archive is placed and receives its actual construction materials")
	history_world.advance_ticks(70)
	var player_archive_station: Dictionary = history_world._find_station(str(player_archive_site.station_id))
	_expect(int(player_archive_site.completed) == 2 and player_archive_station.owner == "player" and player_archive_station.production.size() == 2, "the builder completes the player's media workshop and scriptorium")
	_expect(history_world.transfer_player_station("ship_001", str(player_archive_station.id), "alloy_plates", 1, true).ok and history_world.transfer_player_station("ship_001", str(player_archive_station.id), "energy_cells", 2, true).ok, "the player's station receives physical inputs from the ship")
	history_world.advance_ticks(22)
	_expect(int(player_archive_station.stock.blank_media) == 4 and int(player_archive_station.stock.get("recorded_data", 0)) == 0 and player_archive_station.production[1].status.contains("Recorded Data source"), "a player scriptorium cannot fabricate a source when only blank media and energy are available")
	_expect(history_world.transfer_player_station("ship_001", str(player_archive_station.id), "recorded_data", 1, true).ok, "the player delivers the purchased source copy")
	history_world.advance_ticks(12)
	_expect(int(player_archive_station.stock.recorded_data) == 2 and int(player_archive_station.stock.blank_media) == 3 and int(player_archive_station.stock.energy_cells) == 0, "the scriptorium retains its source and consumes media and energy to make one copy")
	_expect(_total_credits(history_world.state) == history_credits and save_store.save_game(test_root + "/player-archive.json", history_world.snapshot()) == OK, "the complete archive and copying economy remains funded, conserved and saveable")
	var old_archive_state: Dictionary = saved_trip.duplicate(true)
	_strip_archives(old_archive_state)
	var archive_old_credits := _total_credits(old_archive_state)
	var archive_old_snapshot := old_archive_state.duplicate(true)
	_expect(save_store.save_game(test_root + "/before-archives.json", old_archive_state) == OK, "a pre-archive save remains readable")
	var old_archive_read: Dictionary = save_store.load_game(test_root + "/before-archives.json")
	var archive_upgrade = WorldScript.new()
	_expect(bool(old_archive_read.get("ok", false)) and archive_upgrade.restore_snapshot(old_archive_read.state) == OK, "an old save gains archive stations and data recipes")
	_expect(_total_credits(archive_upgrade.state) == archive_old_credits and _without_station_supply(archive_upgrade.state.ships) == archive_old_snapshot.ships and archive_upgrade.state.ledger == archive_old_snapshot.ledger, "archive migration preserves money, ships, cargo, orders and ledger")
	_expect(int(archive_upgrade._find_station("hearth_exchange").stock.blank_media) == 0 and int(archive_upgrade._find_station("auroran_archive").credits) == 0 and archive_upgrade.state.visited_archives.is_empty(), "archive migration adds no free commodities, funding or visits")
	var invalid_archive: Dictionary = history_world.snapshot()
	for item in invalid_archive.stations:
		if item.id == "auroran_archive":
			item.archive.staff_credits = -1
	_expect(save_store.save_game(test_root + "/invalid-archive.json", invalid_archive) != OK, "save validation rejects negative archive staff balances")
	invalid_archive = history_world.snapshot()
	for recipe in invalid_archive.recipes:
		if recipe.id == "data_reproduction":
			recipe.inputs["recorded_data"] = 1
	_expect(save_store.save_game(test_root + "/invalid-archive.json", invalid_archive) != OK, "a reusable source cannot also be a consumed recipe input")
	var future_archive: Dictionary = history_world.snapshot()
	future_archive.archive_version = 2
	var future_archive_path := test_root + "/archive-version.json"
	_expect(save_store.save_game(future_archive_path, history_world.snapshot()) == OK and save_store.save_game(future_archive_path, history_world.snapshot()) == OK, "archive version test retains a valid backup")
	var future_archive_payload := Marshalls.variant_to_base64(future_archive, false)
	var future_archive_file := FileAccess.open(future_archive_path, FileAccess.WRITE)
	future_archive_file.store_string(JSON.stringify({"format_version":1, "payload":future_archive_payload, "checksum":future_archive_payload.sha256_text()}))
	future_archive_file.close()
	_expect(save_store.load_game(future_archive_path).get("reason") == "unsupported", "future archive data cannot silently fall back to an older save")

	# Research uses physical lab output and distinct, relevant visited archives.
	var research_before_invalid: Dictionary = history_world.snapshot()
	_expect(not history_world.research.start(history_world, "auroran_archive", "archive_indexing").ok and history_world.snapshot() == research_before_invalid, "research cannot be assigned to an NPC archive or spend anything on failure")
	var research_quote: Dictionary = history_world.construction.quote(history_world, "hearthreach", {"research_laboratory":1}, "all", [])
	_expect(research_quote.ok and int(research_quote.fee) == 900 and int(research_quote.materials.alloy_plates) == 14, "the planner prices a buildable research laboratory")
	var research_placement: Dictionary = history_world.construction.place(history_world, "hearthreach", {"research_laboratory":1}, "all", [])
	var research_site: Dictionary = history_world.construction.find_site(history_world, str(research_placement.site_id))
	_expect(research_placement.ok and history_world.build_supply.assign(history_world, "ship_001", str(research_site.id)).ok, "the player places a lab and assigns physical construction supplies")
	history_world.advance_ticks(70)
	var research_lab: Dictionary = history_world._find_station(str(research_site.station_id))
	_expect(int(research_site.completed) == 1 and history_world.research.has_lab(research_lab), "the builder completes an actual player-owned laboratory")
	_expect(history_world.research.progress_per_note(history_world, "archive_indexing") == 3 and history_world.research.progress_per_note(history_world, "media_engineering") == 2, "a visited matching archive helps the relevant project but not an unrelated one")
	var research_invalid: Dictionary = history_world.snapshot()
	_expect(not history_world.research.start(history_world, str(research_lab.id), "unknown_project").ok and history_world.snapshot() == research_invalid, "an unknown project leaves research and property untouched")
	_expect(history_world.dock_ship("ship_001", str(player_archive_station.id)).ok and history_world.transfer_player_station("ship_001", str(player_archive_station.id), "recorded_data", 1, false).ok, "the player physically collects a data copy for laboratory work")
	_expect(history_world.dock_ship("ship_001", "hearth_exchange").ok and history_world.trade("ship_001", "hearth_exchange", "energy_cells", 2, true).ok, "the player buys the lab's energy")
	_expect(history_world.dock_ship("ship_001", str(research_lab.id)).ok and history_world.transfer_player_station("ship_001", str(research_lab.id), "recorded_data", 1, true).ok and history_world.transfer_player_station("ship_001", str(research_lab.id), "energy_cells", 2, true).ok, "the laboratory receives the actual data and energy by ship")
	_expect(history_world.research.start(history_world, str(research_lab.id), "archive_indexing").ok, "a project can be assigned to the completed laboratory")
	history_world.advance_ticks(14)
	_expect(int(history_world.state.research.progress.get("archive_indexing", 0)) == 0 and int(research_lab.stock.recorded_data) == 1, "no research progress or inputs are consumed before the laboratory cycle finishes")
	var research_trip_path := test_root + "/research-mid-cycle.json"
	_expect(save_store.save_game(research_trip_path, history_world.snapshot()) == OK, "active research and the partial lab cycle save")
	var research_trip_read: Dictionary = save_store.load_game(research_trip_path)
	var research_reload = WorldScript.new()
	_expect(bool(research_trip_read.get("ok", false)) and research_reload.restore_snapshot(research_trip_read.state) == OK, "active research reloads with its selected lab")
	history_world.advance_ticks(1)
	research_reload.advance_ticks(1)
	_expect(history_world.snapshot() == research_reload.snapshot(), "lab production and research progress continue deterministically after reload")
	_expect(int(history_world.state.research.progress.archive_indexing) == 3 and int(research_lab.stock.research_notes) == 0 and int(research_lab.stock.recorded_data) == 0 and int(research_lab.stock.energy_cells) == 0, "one real note is consumed for base progress plus one relevant archive bonus")
	_expect(int(player_archive_station.stock.recorded_data) == 1, "laboratory research consumes a copy without consuming the source retained at the archive")

	var research_branch = WorldScript.new()
	research_branch.restore_snapshot(history_world.snapshot())
	var branch_lab: Dictionary = research_branch._find_station(str(research_lab.id))
	branch_lab.stock.research_notes = 3 # Isolated fixture for switching and pausing.
	_expect(research_branch.research.pause(research_branch), "an active research project can be paused")
	research_branch.advance_ticks(2)
	_expect(int(branch_lab.stock.research_notes) == 3 and int(research_branch.state.research.progress.archive_indexing) == 3, "pausing retains notes and prior progress")
	_expect(research_branch.research.start(research_branch, str(branch_lab.id), "media_engineering").ok, "the player can switch to another research project")
	research_branch.advance_ticks(1)
	_expect(int(research_branch.state.research.progress.media_engineering) == 2 and int(research_branch.state.research.progress.archive_indexing) == 3, "switching preserves the first project and gives no unrelated archive bonus")
	research_branch.research.start(research_branch, str(branch_lab.id), "archive_indexing")
	research_branch.advance_ticks(1)
	_expect(int(research_branch.state.research.progress.archive_indexing) == 6 and int(research_branch.state.research.progress.media_engineering) == 2 and int(branch_lab.stock.research_notes) == 1, "resuming retains both project totals and consumes only one note")
	_expect(save_store.save_game(test_root + "/research-switch.json", research_branch.snapshot()) == OK, "switched projects and remaining notes save")

	var research_refs = WorldScript.new()
	research_refs.restore_snapshot(history_world.snapshot())
	_expect(research_refs.queue_fly_to("ship_001", "vellum_gate"), "a researcher can travel to another faction's archive")
	research_refs.advance_ticks(10)
	_expect(research_refs.dock_ship("ship_001", "vesper_archive").ok and research_refs.archives.read(research_refs, "ship_001", "vesper_archive").ok, "the Vesper archive is physically visited")
	_expect(research_refs.research.references(research_refs, "archive_indexing").size() == 2 and research_refs.research.progress_per_note(research_refs, "archive_indexing") == 4, "two independent relevant archives contribute to the project")
	research_refs.archives.read(research_refs, "ship_001", "vesper_archive")
	_expect(research_refs.research.progress_per_note(research_refs, "archive_indexing") == 4, "revisiting an archive never stacks its bonus")
	_expect(research_refs.queue_fly_to("ship_001", "verdant_trace"), "the player can continue to the Frontier archive")
	research_refs.advance_ticks(10)
	_expect(research_refs.dock_ship("ship_001", "frontier_archive").ok and research_refs.archives.read(research_refs, "ship_001", "frontier_archive").ok, "the Frontier collection can be visited")
	_expect(research_refs.research.references(research_refs, "archive_indexing").size() == 3 and research_refs.research.progress_per_note(research_refs, "archive_indexing") == 4, "a third relevant source is shown while its additional bonus is capped")
	_expect(research_refs.queue_fly_to("ship_001", "cinder_veil"), "the player can visit the Ravel archive")
	research_refs.advance_ticks(10)
	_expect(research_refs.dock_ship("ship_001", "ravel_archive").ok and research_refs.archives.read(research_refs, "ship_001", "ravel_archive").ok, "the Ravel collection can be visited")
	_expect(research_refs.research.references(research_refs, "media_engineering").size() == 2 and research_refs.research.progress_per_note(research_refs, "media_engineering") == 4, "an archive matching multiple subjects is counted once, alongside another relevant archive")

	var research_clamp = WorldScript.new()
	research_clamp.restore_snapshot(history_world.snapshot())
	var clamp_archive: Dictionary = research_clamp._find_station(str(player_archive_station.id))
	var clamp_lab: Dictionary = research_clamp._find_station(str(research_lab.id))
	clamp_archive.production[1].progress = 11
	clamp_lab.stock.research_notes = 1
	research_clamp.state.research.progress.archive_indexing = 22
	research_clamp.advance_ticks(1)
	_expect("archive_indexing" in research_clamp.state.research.completed and int(clamp_archive.production[1].progress) == 8, "an upgrade safely adjusts an already-started copying cycle")
	_expect(save_store.save_game(test_root + "/research-upgrade-cycle.json", research_clamp.snapshot()) == OK, "an upgraded in-progress production cycle remains saveable")

	# Manufacture enough copies and notes to finish a real project.
	_expect(history_world.dock_ship("ship_001", "hearth_exchange").ok and history_world.trade("ship_001", "hearth_exchange", "energy_cells", 25, true).ok, "the player buys energy for the research supply chain")
	_expect(history_world.queue_fly_to("ship_001", "vellum_gate"), "the player travels for blank-media material")
	history_world.advance_ticks(10)
	_expect(history_world.dock_ship("ship_001", "vellum_foundry").ok and history_world.trade("ship_001", "vellum_foundry", "alloy_plates", 1, true).ok, "the player buys alloy for blank media")
	_expect(history_world.queue_fly_to("ship_001", "hearthreach"), "the player returns supplies to the archive")
	history_world.advance_ticks(10)
	_expect(history_world.dock_ship("ship_001", str(player_archive_station.id)).ok and history_world.transfer_player_station("ship_001", str(player_archive_station.id), "alloy_plates", 1, true).ok and history_world.transfer_player_station("ship_001", str(player_archive_station.id), "energy_cells", 8, true).ok, "the archive receives real inputs to make further copies")
	history_world.advance_ticks(90)
	_expect(int(player_archive_station.stock.recorded_data) == 8, "the scriptorium produces seven more copies while retaining its source")
	_expect(history_world.transfer_player_station("ship_001", str(player_archive_station.id), "recorded_data", 7, false).ok and history_world.dock_ship("ship_001", str(research_lab.id)).ok and history_world.transfer_player_station("ship_001", str(research_lab.id), "recorded_data", 7, true).ok and history_world.transfer_player_station("ship_001", str(research_lab.id), "energy_cells", 14, true).ok, "seven physical copies and their energy arrive at the lab")
	history_world.advance_ticks(105)
	_expect("archive_indexing" in history_world.state.research.completed and history_world.state.research.active_project_id == "" and int(history_world.state.research.progress.archive_indexing) == 24, "the project completes only after consuming the required laboratory output")
	_expect(int(player_archive_station.stock.recorded_data) == 1 and int(research_lab.stock.recorded_data) == 0 and int(research_lab.stock.energy_cells) == 0, "research preserves the source copy while consuming delivered copies and energy")
	var player_copy_report: Dictionary = history_world.production_report(str(player_archive_station.id))[1]
	var npc_copy_report: Dictionary = history_world.production_report("auroran_archive")[1]
	_expect(int(player_copy_report.duration) == 9 and int(npc_copy_report.duration) == 12, "completed research accelerates the player's scriptorium but not an NPC archive")
	var upgraded_plan: Dictionary = history_world.research.adjusted_recipe(history_world.state, history_world._find_recipe("data_reproduction"), true)
	var upgraded_preview: Dictionary = history_world.construction.planner.preview(history_world.state, {"data_reproduction":1}, "all", [], "hearthreach")
	_expect(int(upgraded_plan.cycle_ticks) == 9 and absf(float(_plan_row(upgraded_preview.wares, "recorded_data").supply) - 60.0 / 9.0) < 0.001, "the planner shows the researched production rate")
	_expect(_total_credits(history_world.state) == history_credits and save_store.save_game(test_root + "/research-complete.json", history_world.snapshot()) == OK, "research and its full supply chain conserve credits and save")
	_expect(not history_world.research.start(history_world, str(research_lab.id), "archive_indexing").ok, "completed research cannot be claimed twice")
	var effects_world = WorldScript.new()
	effects_world.restore_snapshot(history_world.snapshot())
	var effects_lab: Dictionary = effects_world._find_station(str(research_lab.id))
	effects_lab.stock.research_notes = 20 # Isolated fixture for the remaining project rewards.
	_expect(effects_world.research.start(effects_world, str(effects_lab.id), "media_engineering").ok, "the media engineering project can start")
	effects_world.advance_ticks(12)
	_expect("media_engineering" in effects_world.state.research.completed and int(effects_world.production_report(str(player_archive_station.id))[0].duration) == 8 and int(effects_world.production_report("auroran_archive")[0].duration) == 10, "media engineering speeds player workshops without changing NPC workshops")
	var media_preview: Dictionary = effects_world.construction.planner.preview(effects_world.state, {"media_fabrication":1}, "all", [], "hearthreach")
	_expect(absf(float(_plan_row(media_preview.wares, "blank_media").supply) - 30.0) < 0.001, "the planner includes the researched media production rate")
	_expect(effects_world.research.start(effects_world, str(effects_lab.id), "resource_surveying").ok, "the resource surveying project can start")
	effects_world.advance_ticks(8)
	_expect("resource_surveying" in effects_world.state.research.completed and int(effects_world.research.adjusted_recipe(effects_world.state, effects_world._find_recipe("ore_extraction"), true).cycle_ticks) == 6 and int(effects_world.research.adjusted_recipe(effects_world.state, effects_world._find_recipe("ore_extraction"), false).cycle_ticks) == 8, "resource surveying speeds player extractors without changing NPC recipes")
	var ore_fixture: Dictionary = effects_world._find_station("cinder_depot").duplicate(true)
	ore_fixture.id = "player_ore_research_fixture"
	ore_fixture.owner = "player"
	ore_fixture.credits = 0
	ore_fixture.sell_prices = {}
	ore_fixture.buy_prices = {}
	for ware_id in ore_fixture.stock:
		ore_fixture.stock[ware_id] = 0
	ore_fixture.stock.energy_cells = 2
	ore_fixture.deposits.ore = 8
	ore_fixture.production = [{"recipe_id":"ore_extraction", "progress":0, "cycles":0, "status":"Waiting"}]
	effects_world.state.stations.append(ore_fixture)
	effects_world.advance_ticks(5)
	_expect(int(ore_fixture.stock.ore) == 0 and int(ore_fixture.deposits.ore) == 8, "a researched extractor still waits for a complete cycle")
	effects_world.advance_ticks(1)
	_expect(int(ore_fixture.stock.ore) == 4 and int(ore_fixture.stock.energy_cells) == 1 and int(ore_fixture.deposits.ore) == 4, "the faster extractor consumes actual energy and finite ore per cycle")
	_expect(save_store.save_game(test_root + "/all-research-effects.json", effects_world.snapshot()) == OK, "all three completed project effects remain saveable")
	var reserve_world = WorldScript.new()
	reserve_world.restore_snapshot(history_world.snapshot())
	var shared_archive_lab: Dictionary = reserve_world._find_station(str(player_archive_station.id)).duplicate(true)
	shared_archive_lab.id = "player_shared_archive_lab_fixture"
	shared_archive_lab.storage_capacity = 160
	for ware_id in shared_archive_lab.stock:
		shared_archive_lab.stock[ware_id] = 0
	shared_archive_lab.stock.recorded_data = 1
	shared_archive_lab.stock.energy_cells = 2
	shared_archive_lab.production = [{"recipe_id":"data_reproduction", "progress":0, "cycles":0, "status":"Waiting"}, {"recipe_id":"research_laboratory", "progress":14, "cycles":0, "status":"Waiting"}]
	reserve_world.state.stations.append(shared_archive_lab)
	reserve_world.advance_ticks(1)
	_expect(int(shared_archive_lab.stock.recorded_data) == 1 and int(shared_archive_lab.stock.research_notes) == 0 and shared_archive_lab.production[1].status.contains("source"), "a shared laboratory cannot consume the last reusable scriptorium source")
	shared_archive_lab.stock.recorded_data = 2 # Isolated fixture supplies a second copy.
	reserve_world.advance_ticks(1)
	_expect(int(shared_archive_lab.stock.recorded_data) == 1 and int(shared_archive_lab.stock.research_notes) == 1 and int(shared_archive_lab.stock.energy_cells) == 0, "a shared laboratory uses a spare data copy while the source stays reserved")
	_expect(save_store.save_game(test_root + "/reserved-source.json", reserve_world.snapshot()) == OK, "a station with a reserved source remains saveable")

	var old_research_state: Dictionary = saved_trip.duplicate(true)
	_strip_research(old_research_state)
	var old_research_credits := _total_credits(old_research_state)
	_expect(save_store.save_game(test_root + "/before-research.json", old_research_state) == OK, "a pre-research archive save remains readable")
	var old_research_read: Dictionary = save_store.load_game(test_root + "/before-research.json")
	var research_upgrade = WorldScript.new()
	_expect(bool(old_research_read.get("ok", false)) and research_upgrade.restore_snapshot(old_research_read.state) == OK, "old saves gain the inactive research system")
	_expect(_without_station_supply(research_upgrade.state.ships) == old_research_state.ships and research_upgrade.state.ledger == old_research_state.ledger and _total_credits(research_upgrade.state) == old_research_credits and research_upgrade.state.research.completed.is_empty(), "research migration preserves property and money without free progress")
	_expect(int(research_upgrade._find_station("hearth_exchange").stock.research_notes) == 0, "research migration does not add free notes")
	var bad_research: Dictionary = history_world.snapshot()
	bad_research.research.progress.archive_indexing = 25
	_expect(save_store.save_game(test_root + "/bad-research.json", bad_research) != OK, "invalid research progress is rejected")
	var future_research: Dictionary = history_world.snapshot()
	future_research.research_version = 2
	var future_research_path := test_root + "/research-version.json"
	_expect(save_store.save_game(future_research_path, history_world.snapshot()) == OK and save_store.save_game(future_research_path, history_world.snapshot()) == OK, "research version test retains a valid backup")
	var future_research_payload := Marshalls.variant_to_base64(future_research, false)
	var future_research_file := FileAccess.open(future_research_path, FileAccess.WRITE)
	future_research_file.store_string(JSON.stringify({"format_version":1, "payload":future_research_payload, "checksum":future_research_payload.sha256_text()}))
	future_research_file.close()
	_expect(save_store.load_game(future_research_path).get("reason") == "unsupported", "future research data cannot silently fall back to an older save")

	# Standing station supply uses real stock, preserves working reserves and respects a spending cap.
	var station_world = WorldScript.new()
	_expect(station_world.restore_snapshot(history_world.snapshot()) == OK, "station supply scenario restores the working economy")
	_disable_npc_trading(station_world)
	var station_plot: Dictionary = station_world.construction.place(station_world, "hearthreach", {"alloy_smelting":1}, "all", [])
	var station_site: Dictionary = station_world.construction.find_site(station_world, str(station_plot.site_id))
	_expect(station_plot.ok and station_world.build_supply.assign(station_world, "ship_001", str(station_site.id)).ok, "a real production station is placed and its construction supply is assigned")
	station_world.advance_ticks(70)
	var supplied_station: Dictionary = station_world._find_station(str(station_site.station_id))
	var station_ship: Dictionary = station_world.state.ships[0]
	var station_targets: Dictionary = station_world.station_supply.targets(station_world, supplied_station)
	_expect(int(station_site.completed) == 1 and int(station_targets.energy_cells) == 3 and int(station_targets.ore) == 6, "a completed smelter has modest targets for its two actual net inputs")
	var station_setup: Dictionary = station_world.snapshot()
	var station_money := _total_credits(station_world.state)
	var station_wallet: int = int(station_world.state.starting_credits)
	var station_wages_before: int = int(station_world.state.ships[0].payroll.total_paid)
	var station_ore: int = int(station_world._find_station("cinder_depot").stock.ore)
	_expect(station_world.station_supply.assign(station_world, "ship_001", str(supplied_station.id), 18).ok and station_ship.role == "Station Supplier", "the player assigns ongoing input supply with a fixed purchase cap")
	station_world.advance_ticks(1)
	_expect(int(supplied_station.stock.energy_cells) == 3 and int(station_ship.cargo.get("energy_cells", 0)) == 0 and int(station_ship.station_supply.spent) == 0, "the supplier delivers matching cargo already aboard before spending")
	station_world.advance_ticks(3)
	_expect(station_ship.station_supply.phase == "to_source" and not station_ship.orders.is_empty(), "the supplier travels to a real source for the missing input")
	var station_trip_path := test_root + "/station-supply-trip.json"
	_expect(save_store.save_game(station_trip_path, station_world.snapshot()) == OK, "station supply, allowance and the trip save in transit")
	var station_trip_read: Dictionary = save_store.load_game(station_trip_path)
	var station_reload = WorldScript.new()
	_expect(bool(station_trip_read.get("ok", false)) and station_reload.restore_snapshot(station_trip_read.state) == OK, "station supply restores in transit")
	station_world.advance_ticks(40)
	station_reload.advance_ticks(40)
	_expect(station_world.snapshot() == station_reload.snapshot(), "ongoing station logistics continue deterministically after reload")
	_expect(int(station_ship.station_supply.spent) == 18 and int(station_world.state.starting_credits) + int(station_ship.payroll.total_paid) - station_wages_before == station_wallet - 18 and int(station_world._find_station("cinder_depot").stock.ore) == station_ore - 3, "real ore is bought at its market price without exceeding the allowance")
	_expect(station_ship.station_supply.enabled and int(supplied_station.production[0].cycles) > 0 and _total_credits(station_world.state) == station_money, "delivered inputs support real production and all credits remain accounted for")
	var station_bad_update: Dictionary = station_world.snapshot()
	_expect(not station_world.station_supply.assign(station_world, "ship_001", str(supplied_station.id), 17).ok and station_world.snapshot() == station_bad_update, "an updated cap cannot be reduced below the amount already spent")
	_expect(station_world.station_supply.assign(station_world, "ship_001", str(supplied_station.id), 60).ok and int(station_ship.station_supply.spent) == 18, "raising the same assignment's total cap preserves its spending history")
	station_world.advance_ticks(60)
	_expect(int(station_ship.station_supply.spent) > 18 and int(station_ship.station_supply.spent) <= 60 and _total_credits(station_world.state) == station_money, "the standing supplier continues replenishing without exceeding its updated cap")

	var interrupted_station = WorldScript.new()
	interrupted_station.restore_snapshot(station_trip_read.state)
	var interrupted_ship: Dictionary = interrupted_station.state.ships[0]
	for _step in range(30):
		interrupted_station.advance_ticks(1)
		if interrupted_ship.station_supply.phase == "to_station" and not interrupted_ship.orders.is_empty():
			break
	var station_kept_cargo: int = int(interrupted_ship.cargo.get("ore", 0))
	var station_kept_orders: Array = interrupted_ship.orders.duplicate(true)
	_expect(station_kept_cargo == 3 and not station_kept_orders.is_empty(), "purchased station input is physically carried on the return journey")
	interrupted_station.set_player_trader("ship_001", false)
	_expect(not interrupted_ship.station_supply.enabled and int(interrupted_ship.cargo.ore) == station_kept_cargo and interrupted_ship.orders == station_kept_orders, "changing role stops station supply while preserving cargo and queued orders")
	interrupted_station.advance_ticks(20)
	_expect(int(interrupted_ship.cargo.ore) == station_kept_cargo and int(interrupted_station._find_station(str(supplied_station.id)).stock.ore) == 0, "stopped station supply does not later deliver retained cargo")

	var protected_world = WorldScript.new()
	protected_world.restore_snapshot(history_world.snapshot())
	_disable_npc_trading(protected_world)
	var protected_source: Dictionary = protected_world._find_station(str(player_archive_station.id))
	var protected_lab: Dictionary = protected_world._find_station(str(research_lab.id))
	var protected_ship: Dictionary = protected_world.state.ships[0]
	var protected_credits: int = int(protected_world.state.starting_credits)
	_expect(int(protected_source.stock.recorded_data) == 1 and int(protected_world.station_supply.protected_stock(protected_world, protected_source, "recorded_data")) >= 1, "a scriptorium's last data source is protected from automated collection")
	_expect(protected_world.station_supply.assign(protected_world, "ship_001", str(protected_lab.id), 0).ok, "a zero-credit station allowance can use carried cargo and owned surplus")
	protected_world.advance_ticks(8)
	_expect(int(protected_source.stock.recorded_data) == 1 and int(protected_lab.stock.recorded_data) == 0 and int(protected_world.state.starting_credits) == protected_credits, "the supplier neither takes the last source nor purchases with a zero allowance")
	protected_source.stock.recorded_data += 3 # Isolated fixture supplies additional owned copies.
	var protected_total := _total_ware(protected_world.state, "recorded_data")
	protected_world.advance_ticks(8)
	_expect(int(protected_source.stock.recorded_data) == 2 and int(protected_lab.stock.recorded_data) == 2 and _total_ware(protected_world.state, "recorded_data") == protected_total, "owned surplus moves physically and leaves the source intact without creating data")
	_expect(int(protected_world.state.starting_credits) == protected_credits and int(protected_ship.station_supply.spent) == 0, "transfers from owned stations do not spend the allowance")

	var working_world = WorldScript.new()
	working_world.restore_snapshot(history_world.snapshot())
	var working_station: Dictionary = working_world._find_station(str(player_archive_station.id)).duplicate(true)
	working_station.id = "player_working_stock_fixture"
	working_station.production = [{"recipe_id":"media_fabrication", "progress":0, "cycles":0, "status":"Waiting"}]
	for ware_id in working_station.stock:
		working_station.stock[ware_id] = 0
	working_station.stock.alloy_plates = 2
	working_world.state.stations.append(working_station)
	_expect(int(working_world.station_supply._source_stock(working_world, working_station, "alloy_plates")) == 0, "a supplier protects another station's working production inputs")
	working_station.stock.alloy_plates = 5
	_expect(int(working_world.station_supply._source_stock(working_world, working_station, "alloy_plates")) == 2, "only stock above the other station's operating buffer is treated as surplus")
	working_station.stock.alloy_plates = 2
	var safe_build_site: Dictionary = working_world.construction.place(working_world, "hearthreach", {"solar_cells":1}, "all", [])
	_expect(working_world.build_supply.assign(working_world, "ship_001", str(safe_build_site.site_id)).ok, "construction supply can coexist with working-stock protection")
	working_world.advance_ticks(1)
	_expect(working_world.state.ships[0].build_supply.source_id != working_station.id and int(working_station.stock.alloy_plates) == 2, "construction supply also avoids stripping another station's working inputs")

	var full_station_world = WorldScript.new()
	full_station_world.restore_snapshot(station_setup)
	_disable_npc_trading(full_station_world)
	var full_target: Dictionary = full_station_world._find_station(str(supplied_station.id))
	full_target.stock.alloy_plates = int(full_target.storage_capacity)
	full_station_world.station_supply.assign(full_station_world, "ship_001", str(full_target.id), 0)
	full_station_world.advance_ticks(1)
	_expect(full_station_world.state.ships[0].status == "Waiting for station storage" and int(full_station_world.state.ships[0].cargo.energy_cells) == 3, "a full station causes the supplier to wait with cargo intact")
	full_target.stock.alloy_plates = 0 # Isolated fixture frees destination storage.
	full_station_world.advance_ticks(7)
	_expect(int(full_target.stock.energy_cells) == 3 and int(full_station_world.state.ships[0].cargo.energy_cells) == 0, "station supply resumes when storage is freed")

	var self_station_world = WorldScript.new()
	self_station_world.restore_snapshot(build_world.snapshot())
	_disable_npc_trading(self_station_world)
	var self_target: Dictionary = self_station_world._find_station(str(outpost.id))
	_expect(self_station_world.station_supply.targets(self_station_world, self_target).is_empty(), "a self-sufficient station does not request inputs that it can produce itself")
	_expect(self_station_world.station_supply.assign(self_station_world, "ship_001", str(self_target.id), 60).ok, "a supplier may stand by for future shortages at a self-sufficient station")
	self_station_world.advance_ticks(1)
	_expect(self_station_world.state.ships[0].station_supply.enabled and self_station_world.state.ships[0].status == "Station inputs stocked", "the supplier waits rather than buying unnecessary inputs")
	self_station_world.state.construction_resources.hearthreach.deposits.ore = 0
	_expect(int(self_station_world.station_supply.targets(self_station_world, self_target).get("ore", 0)) == 6, "an exhausted deposit creates a new ore import need")

	var competing_stations = WorldScript.new()
	competing_stations.restore_snapshot(station_setup)
	_disable_npc_trading(competing_stations)
	competing_stations.state.ships[0].cargo.clear()
	var second_supplier: Dictionary = competing_stations.state.ships[0].duplicate(true)
	second_supplier.id = "ship_002"
	second_supplier.name = "Second Light"
	competing_stations.personnel.initialize_ship(second_supplier, int(competing_stations.state.tick), "hearth_exchange")
	competing_stations.state.ships.append(second_supplier)
	competing_stations.station_supply.assign(competing_stations, "ship_001", str(supplied_station.id), 36)
	competing_stations.station_supply.assign(competing_stations, "ship_002", str(supplied_station.id), 36)
	var competing_events: int = competing_stations.state.ledger.size()
	competing_stations.advance_ticks(12)
	var competing_ore := 0
	for index in range(competing_events, competing_stations.state.ledger.size()):
		var event: Dictionary = competing_stations.state.ledger[index]
		if event.kind == "buy" and event.ware_id == "ore" and event.ship_id in ["ship_001", "ship_002"]:
			competing_ore += int(event.quantity)
	_expect(competing_ore == 6, "competing suppliers count inbound cargo and do not buy the same shortage twice")
	_expect(save_store.save_game(test_root + "/competing-station-suppliers.json", competing_stations.snapshot()) == OK, "competing station suppliers remain saveable")

	var old_station_supply: Dictionary = saved_trip.duplicate(true)
	_strip_shipyard(old_station_supply)
	old_station_supply.erase("station_supply_version")
	for old_ship in old_station_supply.ships:
		old_ship.erase("station_supply")
	_expect(save_store.save_game(test_root + "/before-station-supply.json", old_station_supply) == OK, "a pre-station-supply save remains readable")
	var old_station_read: Dictionary = save_store.load_game(test_root + "/before-station-supply.json")
	var station_upgrade = WorldScript.new()
	_expect(bool(old_station_read.get("ok", false)) and station_upgrade.restore_snapshot(old_station_read.state) == OK and not station_upgrade.state.ships[0].station_supply.enabled, "old saves gain an inactive station supplier")
	_expect(_without_station_supply(station_upgrade.state.ships) == old_station_supply.ships and station_upgrade.state.ledger == old_station_supply.ledger and _total_credits(station_upgrade.state) == _total_credits(old_station_supply), "station supply migration preserves ship orders, cargo, credits and ledger")
	var bad_station_supply: Dictionary = station_world.snapshot()
	bad_station_supply.ships[0].station_supply.spent = int(bad_station_supply.ships[0].station_supply.budget_limit) + 1
	_expect(save_store.save_game(test_root + "/bad-station-supply.json", bad_station_supply) != OK, "save validation rejects a supplier whose spending exceeds its cap")
	var future_station_supply: Dictionary = station_world.snapshot()
	future_station_supply.station_supply_version = 2
	var future_station_path := test_root + "/station-supply-version.json"
	_expect(save_store.save_game(future_station_path, station_world.snapshot()) == OK and save_store.save_game(future_station_path, station_world.snapshot()) == OK, "station supply version test retains a valid backup")
	var future_station_payload := Marshalls.variant_to_base64(future_station_supply, false)
	var future_station_file := FileAccess.open(future_station_path, FileAccess.WRITE)
	future_station_file.store_string(JSON.stringify({"format_version":1, "payload":future_station_payload, "checksum":future_station_payload.sha256_text()}))
	future_station_file.close()
	_expect(save_store.load_game(future_station_path).get("reason") == "unsupported", "future station supply data cannot silently fall back to an older save")

	# Ship contracts: the NPC wharf must transfer real money, remove physical
	# metal, and commission new owned ships over serialized simulation time.
	var wharf_world = WorldScript.new()
	_expect(wharf_world.load_starter() == OK, "wharf scenario loads without granting another player ship")
	_disable_npc_trading(wharf_world)
	var wharf: Dictionary = wharf_world._find_station("vellum_foundry")
	var initial_wharf_money := _total_credits(wharf_world.state)
	var initial_wharf_stock := int(wharf.stock.alloy_plates)
	_expect(wharf_world.state.shipyard_version == 1 and wharf_world.state.shipyard.orders.is_empty() and wharf_world.state.ships.filter(func(item): return item.owner == "player").size() == 1, "the shipyard is ready with an empty queue and no free player ships")
	var courier_quote: Dictionary = wharf_world.shipyard.quote(wharf_world, "courier_mk1")
	_expect(courier_quote.ok and int(courier_quote.hull.price) == 4000 and int(courier_quote.hull.materials.alloy_plates) == 12 and int(courier_quote.hull.ticks) == 24, "a courier hull has a physical material bill, real price and finite build duration")
	var before_bad_hull: Dictionary = wharf_world.snapshot()
	_expect(not wharf_world.shipyard.place_order(wharf_world, "invalid_hull").ok and before_bad_hull == wharf_world.snapshot(), "unknown hulls cannot spend credits or materials")
	wharf_world.state.relations.vesper = -40
	var before_hostile: Dictionary = wharf_world.snapshot()
	_expect(not wharf_world.shipyard.place_order(wharf_world, "courier_mk1").ok and before_hostile == wharf_world.snapshot(), "hostile faction cannot place a ship contract")
	wharf_world.state.relations.vesper = 0
	wharf_world.state.starting_credits = 200
	var before_poor_wharf: Dictionary = wharf_world.snapshot()
	_expect(not wharf_world.shipyard.place_order(wharf_world, "courier_mk1").ok and before_poor_wharf == wharf_world.snapshot(), "insufficient money rejects the entire hull transaction")
	wharf_world.state.starting_credits = 25000
	wharf.stock.alloy_plates = 0
	var before_short_wharf: Dictionary = wharf_world.snapshot()
	_expect(not wharf_world.shipyard.place_order(wharf_world, "courier_mk1").ok and before_short_wharf == wharf_world.snapshot(), "an empty wharf cannot create ships from missing alloy")
	wharf.stock.alloy_plates = initial_wharf_stock
	var wharf_first: Dictionary = wharf_world.shipyard.place_order(wharf_world, "courier_mk1")
	var wharf_second: Dictionary = wharf_world.shipyard.place_order(wharf_world, "freighter_mk1")
	_expect(wharf_first.ok and wharf_second.ok and wharf_first.ship_id != wharf_second.ship_id and wharf_world.state.shipyard.orders.size() == 2, "two hull contracts reserve stable distinct ship IDs and enter the real queue")
	_expect(int(wharf_world.state.starting_credits) == 12500 and int(wharf.credits) == 32500 and _total_credits(wharf_world.state) == initial_wharf_money, "hull prices transfer existing player credits to the NPC wharf exactly once")
	_expect(int(wharf.stock.alloy_plates) == initial_wharf_stock - 42 and wharf_world.state.ledger[wharf_world.state.ledger.size() - 1].kind == "ship_order", "two hulls consume their exact existing metal immediately and record the payment")
	_expect(wharf_world._find_ship(str(wharf_first.ship_id)).is_empty(), "placing an order does not materialise an instant ship")
	wharf_world.advance_ticks(9)
	_expect(int(wharf_world.state.shipyard.orders[0].progress) == 9 and wharf_world.state.shipyard.orders[0].status == "building" and int(wharf_world.state.shipyard.orders[1].progress) == 0, "only the first paid hull occupies the berth")
	var wharf_save_path := test_root + "/shipyard-in-progress.json"
	_expect(save_store.save_game(wharf_save_path, wharf_world.snapshot()) == OK, "shipbuilding progress and reserved materials are saveable")
	var wharf_loaded: Dictionary = save_store.load_game(wharf_save_path)
	var wharf_restored = WorldScript.new()
	_expect(bool(wharf_loaded.get("ok", false)) and wharf_restored.restore_snapshot(wharf_loaded.state) == OK, "pending paid hull orders restore without duplicate charges")
	wharf_world.advance_ticks(75)
	wharf_restored.advance_ticks(75)
	_expect(wharf_world.snapshot() == wharf_restored.snapshot(), "two serialised hull orders finish deterministically after a mid-build save")
	_expect(wharf_world.state.shipyard.orders[0].status == "complete" and wharf_world.state.shipyard.orders[1].status == "complete" and int(wharf_world.state.shipyard.orders[0].progress) == 24 and int(wharf_world.state.shipyard.orders[1].progress) == 48, "the single berth completes both hulls with their actual build durations")
	var courier_ship: Dictionary = wharf_world._find_ship(str(wharf_first.ship_id))
	var freighter_ship: Dictionary = wharf_world._find_ship(str(wharf_second.ship_id))
	_expect(not courier_ship.is_empty() and not freighter_ship.is_empty() and courier_ship.owner == "player" and freighter_ship.owner == "player" and courier_ship.sector == "vellum_gate" and freighter_ship.sector == "vellum_gate", "completed ships exist as separately owned assets at the actual wharf sector")
	_expect(int(courier_ship.cargo_capacity) == 50 and int(freighter_ship.cargo_capacity) == 180 and courier_ship.has("player_trader") and freighter_ship.has("build_supply") and freighter_ship.has("station_supply"), "new ships have distinct cargo capacities and full existing ship-role compatibility")
	_expect(_total_credits(wharf_world.state) == initial_wharf_money and wharf_world.state.ledger.filter(func(entry): return entry.kind == "ship_delivery").size() == 2, "delivering ships cannot duplicate money and appears in the ledger")
	_expect(save_store.save_game(test_root + "/shipyard-completed.json", wharf_world.snapshot()) == OK, "both completed commissioned ships pass strict save validation")
	_expect(wharf_world.set_player_trader(str(freighter_ship.id), true) and wharf_world.queue_fly_to(str(freighter_ship.id), "cinder_veil") and wharf_world.state.ships[0].orders.is_empty(), "new freighter can take real autonomous and manual orders independently of First Light")

	# The service berth halts, rather than forging a ship or refunding money,
	# if wharf ownership changes during a paid contract.
	var blocked_wharf = WorldScript.new()
	blocked_wharf.load_starter()
	_disable_npc_trading(blocked_wharf)
	var blocked_order: Dictionary = blocked_wharf.shipyard.place_order(blocked_wharf, "courier_mk1")
	blocked_wharf.advance_ticks(5)
	var blocked_progress: int = int(blocked_wharf.state.shipyard.orders[0].progress)
	blocked_wharf._find_station("vellum_foundry").owner = blocked_wharf.state.player_faction_id
	blocked_wharf.advance_ticks(14)
	_expect(blocked_wharf.state.shipyard.orders[0].status == "blocked" and int(blocked_wharf.state.shipyard.orders[0].progress) == blocked_progress and blocked_wharf._find_ship(str(blocked_order.ship_id)).is_empty(), "unavailable wharf suspends paid assembly without fabricating a ship")
	_expect(save_store.save_game(test_root + "/shipyard-blocked.json", blocked_wharf.snapshot()) == OK, "the blocked contract remains a valid persistent state")
	blocked_wharf._find_station("vellum_foundry").owner = "vesper"
	blocked_wharf.advance_ticks(24)
	_expect(blocked_wharf.state.shipyard.orders[0].status == "complete" and not blocked_wharf._find_ship(str(blocked_order.ship_id)).is_empty(), "restoring access to the wharf lets the paid contract finish exactly once")
	var limited_wharf = WorldScript.new()
	limited_wharf.load_starter()
	_disable_npc_trading(limited_wharf)
	for _order in range(5):
		limited_wharf.shipyard.place_order(limited_wharf, "courier_mk1")
	var before_sixth: Dictionary = limited_wharf.snapshot()
	_expect(not limited_wharf.shipyard.place_order(limited_wharf, "courier_mk1").ok and limited_wharf.snapshot() == before_sixth, "a full five-order production queue rejects further purchases atomically")

	# Pre-shipyard saves migrate without resetting existing player property.
	var old_wharf_state: Dictionary = wharf_world.snapshot()
	_strip_shipyard(old_wharf_state)
	var old_wharf_save := test_root + "/before-shipyard.json"
	_expect(save_store.save_game(old_wharf_save, old_wharf_state) == OK, "a pre-shipyard game remains readable")
	var old_wharf_read: Dictionary = save_store.load_game(old_wharf_save)
	var wharf_migrated = WorldScript.new()
	_expect(bool(old_wharf_read.get("ok", false)) and wharf_migrated.restore_snapshot(old_wharf_read.state) == OK and wharf_migrated.state.shipyard_version == 1, "older games gain an empty wharf order catalogue")
	_expect(wharf_migrated.state.shipyard.orders.is_empty() and _without_progression(wharf_migrated.state.ships) == old_wharf_state.ships and wharf_migrated.state.starting_credits == old_wharf_state.starting_credits and wharf_migrated.state.ledger == old_wharf_state.ledger, "migration preserves every existing vessel, order, financial record and cargo unit without granting free ships")
	var bad_shipyard: Dictionary = wharf_world.snapshot()
	bad_shipyard.shipyard.orders[0].progress = 999
	_expect(save_store.save_game(test_root + "/bad-shipyard.json", bad_shipyard) != OK, "save validator rejects impossible shipyard progress")
	bad_shipyard = wharf_world.snapshot()
	bad_shipyard.shipyard.orders[1].ship_id = bad_shipyard.shipyard.orders[0].ship_id
	_expect(save_store.save_game(test_root + "/bad-shipyard.json", bad_shipyard) != OK, "duplicate reserved ship IDs are not saveable")
	var future_wharf_path := test_root + "/future-shipyard.json"
	_expect(save_store.save_game(future_wharf_path, wharf_world.snapshot()) == OK and save_store.save_game(future_wharf_path, wharf_world.snapshot()) == OK, "shipyard version test retains a valid backup")
	var future_wharf: Dictionary = wharf_world.snapshot()
	future_wharf.shipyard_version = 2
	var future_wharf_payload := Marshalls.variant_to_base64(future_wharf, false)
	var future_wharf_file := FileAccess.open(future_wharf_path, FileAccess.WRITE)
	future_wharf_file.store_string(JSON.stringify({"format_version":1, "payload":future_wharf_payload, "checksum":future_wharf_payload.sha256_text()}))
	future_wharf_file.close()
	_expect(save_store.load_game(future_wharf_path).get("reason") == "unsupported", "future shipyard save versions are never silently replaced by an older backup")

	# Personnel are a finite NPC roster. Hiring consumes actual credits;
	# discharge returns a crew member to the same station without a refund,
	# and transfers move existing crew between two physically co-docked ships.
	var crew_world = WorldScript.new()
	_expect(crew_world.load_starter() == OK, "crew-management world loads with finite station rosters")
	_disable_npc_trading(crew_world)
	var crew_first: Dictionary = crew_world._find_ship("ship_001")
	var crew_market: Dictionary = crew_world._find_station("hearth_exchange")
	var crew_total_before: int = _total_credits(crew_world.state)
	var initial_roster: int = int(crew_world.state.crew_pools.hearth_exchange)
	_expect(crew_world.state.personnel_version == 2 and initial_roster == 12 and crew_world.personnel.capacity(crew_first) == 8, "finite recruitment pool and courier crew berth limit are initialized")
	var rename_before: Dictionary = crew_world.snapshot()
	_expect(not crew_world.personnel.rename(crew_world, "npc_builder_001", "Owned Now").ok and crew_world.snapshot() == rename_before, "NPC vessels cannot be renamed")
	_expect(not crew_world.personnel.rename(crew_world, "ship_001", " \t ").ok and crew_world.snapshot() == rename_before, "blank ship names cannot alter world state")
	_expect(not crew_world.personnel.rename(crew_world, "ship_001", "This name exceeds forty letters and must be rejected immediately").ok and crew_world.snapshot() == rename_before, "overlong names are rejected before changing the ship")
	var rename_result: Dictionary = crew_world.personnel.rename(crew_world, "ship_001", "  Aurora One  ")
	_expect(rename_result.ok and crew_first.name == "Aurora One" and crew_first.id == "ship_001" and crew_first.captain == "Mira Vale" and int(crew_first.crew) == 2, "renaming trims whitespace but preserves stable ID, pilot and crew")
	_expect(not crew_world.personnel.rename(crew_world, "ship_001", "Aurora One").ok, "renaming to the current name is rejected without changing state")
	var no_dock: Dictionary = crew_world.snapshot()
	_expect(not crew_world.personnel.hire(crew_world, "ship_001", 1).ok and not crew_world.personnel.discharge(crew_world, "ship_001", 1).ok and crew_world.snapshot() == no_dock, "recruitment and discharge require a real station dock")
	_expect(crew_world.dock_ship("ship_001", "hearth_exchange").ok, "player ship can physically dock at a recruitment market")
	crew_world.state.relations.auroran = -30
	var hostile_crew: Dictionary = crew_world.snapshot()
	_expect(not crew_world.personnel.hire(crew_world, "ship_001", 1).ok and crew_world.snapshot() == hostile_crew, "hostile NPC recruitment fails atomically")
	crew_world.state.relations.auroran = 0
	crew_world.state.starting_credits = 100
	var too_poor_crew: Dictionary = crew_world.snapshot()
	_expect(not crew_world.personnel.hire(crew_world, "ship_001", 1).ok and crew_world.snapshot() == too_poor_crew, "recruitment fails when player cannot afford the crew contract")
	crew_world.state.starting_credits = 25000
	var recruitment_result: Dictionary = crew_world.personnel.hire(crew_world, "ship_001", 3)
	_expect(recruitment_result.ok and int(crew_first.crew) == 5 and int(crew_world.state.crew_pools.hearth_exchange) == initial_roster - 3, "three recruits leave a finite station roster and board the owned ship")
	_expect(int(crew_world.state.starting_credits) == 24250 and int(crew_market.credits) == 20750 and _total_credits(crew_world.state) == crew_total_before, "recruitment transfers exactly 750 existing credits from the player to the NPC station")
	_expect(crew_world.state.ledger.back().kind == "crew_hire" and int(crew_world.state.ledger.back().quantity) == 3 and int(crew_world.state.ledger.back().amount) == -750, "recruitment ledger records the ship, people and actual outlay")
	var crew_cap_before: Dictionary = crew_world.snapshot()
	_expect(not crew_world.personnel.hire(crew_world, "ship_001", 4).ok and crew_world.snapshot() == crew_cap_before, "a courier cannot recruit beyond its physical crew berths")
	crew_world.state.crew_pools.hearth_exchange = 1
	var empty_roster_before: Dictionary = crew_world.snapshot()
	_expect(not crew_world.personnel.hire(crew_world, "ship_001", 2).ok and crew_world.snapshot() == empty_roster_before, "insufficient station personnel cannot manufacture workers")
	crew_world.state.crew_pools.hearth_exchange = initial_roster - 3
	var discharge_result: Dictionary = crew_world.personnel.discharge(crew_world, "ship_001", 1)
	_expect(discharge_result.ok and int(crew_first.crew) == 4 and int(crew_world.state.crew_pools.hearth_exchange) == initial_roster - 2 and int(crew_world.state.starting_credits) == 24250, "discharge returns one worker to the roster without an invented refund")
	_expect(crew_world.state.ledger.back().kind == "crew_discharge" and int(crew_world.state.ledger.back().amount) == 0, "discharged crew get a nonfinancial transaction entry")
	var too_many_discharge: Dictionary = crew_world.snapshot()
	_expect(not crew_world.personnel.discharge(crew_world, "ship_001", 5).ok and crew_world.snapshot() == too_many_discharge, "discharging more crew than aboard does not go negative")
	_expect(save_store.save_game(test_root + "/crew-recruit-and-rename.json", crew_world.snapshot()) == OK, "renamed ship, paid hires and finite station pool survive save validation")
	var crew_save: Dictionary = save_store.load_game(test_root + "/crew-recruit-and-rename.json")
	var restored_crew = WorldScript.new()
	_expect(bool(crew_save.get("ok", false)) and restored_crew.restore_snapshot(crew_save.state) == OK and restored_crew.snapshot() == crew_world.snapshot(), "recruitment and renamed ship round-trip with no duplicated headcount or money")

	var transfer_world = WorldScript.new()
	transfer_world.load_starter()
	_disable_npc_trading(transfer_world)
	var second_contract: Dictionary = transfer_world.shipyard.place_order(transfer_world, "freighter_mk1")
	transfer_world.advance_ticks(48)
	var transfer_source: Dictionary = transfer_world._find_ship("ship_001")
	var transfer_destination: Dictionary = transfer_world._find_ship(str(second_contract.ship_id))
	_expect(second_contract.ok and not transfer_destination.is_empty(), "crew transfers use a real constructed freighter rather than a free test ship")
	var not_colocated: Dictionary = transfer_world.snapshot()
	_expect(not transfer_world.personnel.transfer(transfer_world, "ship_001", str(transfer_destination.id), 1).ok and transfer_world.snapshot() == not_colocated, "different sectors and absent docks prevent remote crew teleportation")
	_expect(transfer_world.queue_fly_to("ship_001", "vellum_gate"), "first player ship can travel to the wharf on a real route")
	transfer_world.advance_ticks(30)
	_expect(transfer_world.dock_ship("ship_001", "vellum_foundry").ok and transfer_source.sector == transfer_destination.sector and transfer_source.docked_at == transfer_destination.docked_at, "both owned ships can be physically co-docked at the NPC wharf")
	var transfer_before_crew: int = int(transfer_source.crew) + int(transfer_destination.crew)
	var transfer_before_money: int = _total_credits(transfer_world.state)
	var transferred: Dictionary = transfer_world.personnel.transfer(transfer_world, "ship_001", str(transfer_destination.id), 1)
	_expect(transferred.ok and int(transfer_source.crew) == 1 and int(transfer_destination.crew) == 5 and int(transfer_source.crew) + int(transfer_destination.crew) == transfer_before_crew, "crew transfer conserves the exact number of personnel between two co-docked ships")
	_expect(_total_credits(transfer_world.state) == transfer_before_money and transfer_world.state.ledger.back().kind == "crew_transfer" and int(transfer_world.state.ledger.back().amount) == 0, "moving crew between owned ships is free but recorded")
	var bad_transfer: Dictionary = transfer_world.snapshot()
	_expect(not transfer_world.personnel.transfer(transfer_world, "ship_001", str(transfer_destination.id), 9).ok and transfer_world.snapshot() == bad_transfer, "insufficient source crew blocks transfers atomically")
	_expect(not transfer_world.personnel.transfer(transfer_world, "ship_001", "ship_001", 1).ok and transfer_world.snapshot() == bad_transfer, "self-transfers are forbidden")
	_expect(not transfer_world.personnel.transfer(transfer_world, "ship_001", "npc_builder_001", 1).ok and transfer_world.snapshot() == bad_transfer, "transfers cannot increase NPC crews")
	_expect(save_store.save_game(test_root + "/crew-transfer.json", transfer_world.snapshot()) == OK, "co-docked crew transfer and ship identities remain saveable")
	var transfer_saved: Dictionary = save_store.load_game(test_root + "/crew-transfer.json")
	var transfer_reloaded = WorldScript.new()
	_expect(bool(transfer_saved.get("ok", false)) and transfer_reloaded.restore_snapshot(transfer_saved.state) == OK and transfer_reloaded.snapshot() == transfer_world.snapshot(), "ship-to-ship transfer remains deterministic after save and load")
	transfer_world.queue_fly_to("ship_001", "cinder_veil")
	var moving_transfer: Dictionary = transfer_world.snapshot()
	_expect(not transfer_world.personnel.transfer(transfer_world, "ship_001", str(transfer_destination.id), 1).ok and transfer_world.snapshot() == moving_transfer, "crew cannot leave a ship while fly orders are pending")

	var old_personnel: Dictionary = transfer_world.snapshot()
	_strip_habitation(old_personnel)
	old_personnel.erase("personnel_version")
	old_personnel.erase("crew_pools")
	old_personnel.erase("population_version")
	old_personnel.erase("population")
	for old_staff_ship in old_personnel.ships:
		old_staff_ship.erase("captain_profile")
		old_staff_ship.erase("crew_profile")
		old_staff_ship.erase("payroll")
	_expect(save_store.save_game(test_root + "/crew-legacy.json", old_personnel) == OK, "old shipyard save without personnel roster remains readable")
	var old_personnel_read: Dictionary = save_store.load_game(test_root + "/crew-legacy.json")
	var migrated_personnel = WorldScript.new()
	_expect(bool(old_personnel_read.get("ok", false)) and migrated_personnel.restore_snapshot(old_personnel_read.state) == OK and migrated_personnel.state.personnel_version == 2, "old save migrates to finite recruitment rosters without a new game")
	_expect(_without_progression(migrated_personnel.state.ships) == old_personnel.ships and migrated_personnel.state.starting_credits == old_personnel.starting_credits and migrated_personnel.state.ledger == old_personnel.ledger, "migration preserves every existing ship, captain, order, crew member and credit")
	var bad_pool: Dictionary = crew_world.snapshot()
	bad_pool.crew_pools.hearth_exchange = -1
	_expect(save_store.save_game(test_root + "/crew-bad-market.json", bad_pool) != OK, "negative roster size is rejected by save validation")
	var future_personnel_path := test_root + "/crew-future.json"
	_expect(save_store.save_game(future_personnel_path, crew_world.snapshot()) == OK and save_store.save_game(future_personnel_path, crew_world.snapshot()) == OK, "future personnel schema test has a valid backup")
	var future_personnel: Dictionary = crew_world.snapshot()
	future_personnel.personnel_version = 3
	var future_personnel_payload := Marshalls.variant_to_base64(future_personnel, false)
	var future_personnel_file := FileAccess.open(future_personnel_path, FileAccess.WRITE)
	future_personnel_file.store_string(JSON.stringify({"format_version":1, "payload":future_personnel_payload, "checksum":future_personnel_payload.sha256_text()}))
	future_personnel_file.close()
	_expect(save_store.load_game(future_personnel_path).get("reason") == "unsupported", "future personnel versions cannot silently revert to previous save backups")

	# Pass 23: real periodic wages, individual captain experience and aggregate
	# crew training. A payroll debit always credits an existing NPC wage agency.
	var payroll_world = WorldScript.new()
	_expect(payroll_world.load_starter() == OK, "captain progression world initializes")
	_disable_npc_trading(payroll_world)
	var payroll_ship: Dictionary = payroll_world._find_ship("ship_001")
	var payroll_station: Dictionary = payroll_world._find_station("hearth_exchange")
	var payroll_initial_money: int = _total_credits(payroll_world.state)
	var payroll_credits: int = int(payroll_world.state.starting_credits)
	var payroll_market_credits: int = int(payroll_station.credits)
	_expect(payroll_world.state.personnel_version == 2 and payroll_ship.captain_profile.id == "captain_ship_001" and payroll_ship.captain == "Mira Vale", "captain has a stable identity separate from the ship name")
	_expect(payroll_ship.captain_profile.skill == 0 and payroll_ship.crew_profile.skill == 0 and payroll_ship.captain_profile.morale == 75 and payroll_ship.crew_profile.morale == 75, "captain and crew start with separate zero skills and normal morale")
	_expect(payroll_ship.payroll.last_tick == 0 and payroll_ship.payroll.arrears == 0 and payroll_world.personnel._ship_wages(payroll_ship) == 18, "initial payroll includes one pilot and two existing service crew")
	payroll_world.advance_ticks(59)
	_expect(int(payroll_world.state.starting_credits) == payroll_credits and int(payroll_ship.payroll.total_paid) == 0 and payroll_ship.payroll.arrears == 0, "simulated salaries do not debit early")
	payroll_world.advance_ticks(1)
	_expect(int(payroll_world.state.starting_credits) == payroll_credits - 18 and int(payroll_ship.payroll.total_paid) == 18, "first crew payroll transfers exactly eighteen existing credits to the agency station")
	_expect(_total_credits(payroll_world.state) == payroll_initial_money and payroll_world.state.ledger.back().kind == "crew_payroll" and int(payroll_world.state.ledger.back().amount) == -18, "wages conserve credits and appear in the main transaction ledger")
	_expect(payroll_ship.captain_profile.morale == 76 and payroll_ship.crew_profile.morale == 76 and payroll_ship.payroll.unpaid_periods == 0, "funded payroll improves captain and crew morale")
	payroll_world.advance_ticks(60)
	_expect(payroll_ship.payroll.total_paid == 36 and payroll_ship.payroll.last_tick == 120 and int(payroll_world.state.starting_credits) == payroll_credits - 36 and _total_credits(payroll_world.state) == payroll_initial_money, "second payroll interval charges exactly once without minting credits")
	var payroll_path := test_root + "/captain-payroll.json"
	_expect(save_store.save_game(payroll_path, payroll_world.snapshot()) == OK, "paid captain and crew wages are saveable")
	var payroll_saved: Dictionary = save_store.load_game(payroll_path)
	var payroll_restored = WorldScript.new()
	_expect(bool(payroll_saved.get("ok", false)) and payroll_restored.restore_snapshot(payroll_saved.state) == OK and payroll_restored.snapshot() == payroll_world.snapshot(), "periodic payroll state restores without paying twice")

	var wage_shortage = WorldScript.new()
	wage_shortage.load_starter()
	_disable_npc_trading(wage_shortage)
	wage_shortage.state.starting_credits = 0
	var unfunded_ship: Dictionary = wage_shortage._find_ship("ship_001")
	wage_shortage.advance_ticks(180)
	_expect(unfunded_ship.payroll.arrears == 54 and unfunded_ship.payroll.unpaid_periods == 3 and unfunded_ship.payroll.total_paid == 0 and wage_shortage.state.starting_credits == 0, "three failed paydays accrue exactly 54 credits of wage debt without overdrawing")
	_expect(unfunded_ship.captain_profile.morale == 60 and unfunded_ship.crew_profile.morale == 60, "three missed payrolls lower actual morale without removing or duplicating crew")
	var unfunded_path := test_root + "/captain-wages-owed.json"
	_expect(save_store.save_game(unfunded_path, wage_shortage.snapshot()) == OK, "wage arrears and morale decline persist in the save format")
	var unpaid_saved: Dictionary = save_store.load_game(unfunded_path)
	var unpaid_restored = WorldScript.new()
	_expect(bool(unpaid_saved.get("ok", false)) and unpaid_restored.restore_snapshot(unpaid_saved.state) == OK and unpaid_restored.snapshot() == wage_shortage.snapshot(), "unpaid payroll round-trips without clearing debt")
	wage_shortage.state.starting_credits = 100
	var shortage_agency_before: int = int(wage_shortage._find_station("hearth_exchange").credits)
	wage_shortage.advance_ticks(60)
	_expect(unfunded_ship.payroll.arrears == 0 and unfunded_ship.payroll.unpaid_periods == 0 and unfunded_ship.payroll.total_paid == 72 and wage_shortage.state.starting_credits == 28, "restored funding pays all accrued wages and the new payroll once")
	_expect(int(wage_shortage._find_station("hearth_exchange").credits) == shortage_agency_before + 72 and unfunded_ship.captain_profile.morale == 61, "arrears repayment conserves station money and morale recovers gradually")
	var no_double_salary: Dictionary = wage_shortage.snapshot()
	wage_shortage.advance_ticks(0)
	_expect(wage_shortage.snapshot() == no_double_salary, "saving or zero-time advancement never pays wages twice")

	# Training is earned from completed movement and actual cargo exchanges,
	# not simply from an idling selected role or uncompleted travel.
	var skill_world = WorldScript.new()
	skill_world.load_starter()
	_disable_npc_trading(skill_world)
	var skill_ship: Dictionary = skill_world._find_ship("ship_001")
	_expect(skill_world.queue_fly_to("ship_001", "opal_crossing"), "training uses a real connected sector crossing")
	skill_world.advance_ticks(4)
	_expect(int(skill_ship.captain_profile.experience) == 0 and int(skill_ship.crew_profile.experience) == 0, "an incomplete sector crossing grants no captain or crew experience")
	skill_world.advance_ticks(1)
	_expect(skill_ship.sector == "opal_crossing" and skill_ship.captain_profile.experience == 2 and skill_ship.crew_profile.experience == 2, "a completed sector crossing trains its assigned captain and aboard crew")
	skill_world.advance_ticks(3)
	_expect(skill_ship.captain_profile.experience == 2 and skill_ship.crew_profile.experience == 2, "idle time after arrival grants no additional experience")
	_expect(skill_world.queue_fly_to("ship_001", "hearthreach"), "pilot can return over the same real route")
	skill_world.advance_ticks(5)
	_expect(skill_ship.captain_profile.experience == 4 and skill_ship.crew_profile.experience == 4, "a second completed crossing grants exactly one additional award")
	_expect(skill_world.dock_ship("ship_001", "hearth_exchange").ok, "crew can use existing market trades for work experience")
	for _purchase in range(25):
		skill_world.trade("ship_001", "hearth_exchange", "energy_cells", 1, true)
	_expect(skill_ship.captain_profile.experience == 29 and skill_ship.captain_profile.skill == 1, "twenty-five physical purchases improve this captain's piloting skill to level one")
	_expect(skill_ship.crew_profile.experience == 54 and skill_ship.crew_profile.skill == 1 and skill_ship.crew == 2, "aboard crew gain aggregate experience from actual purchases without new personnel")
	var trained_xp: int = int(skill_ship.crew_profile.experience)
	skill_world.advance_ticks(2)
	_expect(skill_ship.crew_profile.experience == trained_xp, "docked idle crews do not train themselves")
	var skill_balance_before: int = _total_credits(skill_world.state)
	_expect(skill_world.personnel.hire(skill_world, "ship_001", 2).ok and skill_ship.crew_profile.experience == trained_xp and skill_ship.crew_profile.skill == 0, "inexperienced recruits dilute average crew skill without fabricating prior experience")
	_expect(_total_credits(skill_world.state) == skill_balance_before, "adding trainee crew is still a real money transfer, not a credit source")

	# Captains are distinct people: switching command between co-docked owned
	# hulls keeps a captain's own experience and morale attached to that pilot.
	var captain_world = WorldScript.new()
	captain_world.load_starter()
	_disable_npc_trading(captain_world)
	var captain_contract: Dictionary = captain_world.shipyard.place_order(captain_world, "freighter_mk1")
	captain_world.advance_ticks(48)
	var original_hull: Dictionary = captain_world._find_ship("ship_001")
	var new_hull: Dictionary = captain_world._find_ship(str(captain_contract.ship_id))
	_expect(captain_contract.ok and not new_hull.is_empty() and original_hull.captain_profile.id != new_hull.captain_profile.id, "real new freighter has a distinct named captain profile")
	_expect(captain_world.queue_fly_to("ship_001", "vellum_gate"), "first player pilot travels physically to the wharf for exchange")
	captain_world.advance_ticks(20)
	_expect(captain_world.dock_ship("ship_001", "vellum_foundry").ok, "two player ships physically share the same wharf")
	var original_captain_id: String = str(original_hull.captain_profile.id)
	var original_captain_name: String = str(original_hull.captain)
	var second_captain_id: String = str(new_hull.captain_profile.id)
	var second_captain_name: String = str(new_hull.captain)
	var captain_xp_before: int = int(original_hull.captain_profile.experience)
	var captain_funds_before: int = _total_credits(captain_world.state)
	var changed: Dictionary = captain_world.personnel.swap_captains(captain_world, "ship_001", str(new_hull.id))
	_expect(changed.ok and original_hull.captain_profile.id == second_captain_id and new_hull.captain_profile.id == original_captain_id, "swapping co-docked captains moves their unique identities, never copies them")
	_expect(original_hull.captain == second_captain_name and new_hull.captain == original_captain_name and int(new_hull.captain_profile.experience) == captain_xp_before, "actual captain names and accumulated experience travel together")
	_expect(_total_credits(captain_world.state) == captain_funds_before and captain_world.state.ledger.back().kind == "captain_swap" and int(captain_world.state.ledger.back().amount) == 0, "a same-dock captain swap transfers neither money nor service crew")
	var captain_swap_path := test_root + "/captain-swapped.json"
	_expect(save_store.save_game(captain_swap_path, captain_world.snapshot()) == OK, "reassigned unique captains and payroll are persisted safely")
	var swapped_saved: Dictionary = save_store.load_game(captain_swap_path)
	var swapped_restored = WorldScript.new()
	_expect(bool(swapped_saved.get("ok", false)) and swapped_restored.restore_snapshot(swapped_saved.state) == OK and swapped_restored.snapshot() == captain_world.snapshot(), "captain transfers survive save/load without replacing ship orders")
	var denied_captain: Dictionary = captain_world.snapshot()
	_expect(not captain_world.personnel.swap_captains(captain_world, "ship_001", "npc_builder_001").ok and captain_world.snapshot() == denied_captain, "NPC captains cannot be silently acquired")
	_expect(not captain_world.personnel.swap_captains(captain_world, "ship_001", "ship_001").ok and captain_world.snapshot() == denied_captain, "captains cannot swap with themselves")
	captain_world.queue_fly_to("ship_001", "cinder_veil")
	var captain_moving: Dictionary = captain_world.snapshot()
	_expect(not captain_world.personnel.swap_captains(captain_world, "ship_001", str(new_hull.id)).ok and captain_world.snapshot() == captain_moving, "a captain cannot leave a vessel with active fly orders")

	# Transfer the accumulated training of service crew without duplication.
	var training_transfer = WorldScript.new()
	training_transfer.load_starter()
	_disable_npc_trading(training_transfer)
	var training_order: Dictionary = training_transfer.shipyard.place_order(training_transfer, "freighter_mk1")
	training_transfer.advance_ticks(48)
	var trained_source: Dictionary = training_transfer._find_ship("ship_001")
	var trained_destination: Dictionary = training_transfer._find_ship(str(training_order.ship_id))
	training_transfer.queue_fly_to("ship_001", "vellum_gate")
	training_transfer.advance_ticks(20)
	training_transfer.dock_ship("ship_001", "vellum_foundry")
	var total_training: int = int(trained_source.crew_profile.experience) + int(trained_destination.crew_profile.experience)
	_expect(total_training > 0, "the original ship's real sector journey has already earned experience to transfer")
	_expect(training_transfer.personnel.transfer(training_transfer, "ship_001", str(trained_destination.id), 1).ok, "physical service crew can be transferred after actual route training")
	_expect(int(trained_source.crew_profile.experience) + int(trained_destination.crew_profile.experience) == total_training and int(trained_source.crew) == 1 and int(trained_destination.crew) == 5, "transfer conserves exact aggregate earned experience and personnel headcount")
	_expect(save_store.save_game(test_root + "/crew-progression-transfer.json", training_transfer.snapshot()) == OK, "trained transferred crew remain valid saved property")

	# Pre-progression personnel v1 saves are upgraded without retroactive wage
	# bills, captain replacements, existing crew resets or lost route orders.
	var old_progression: Dictionary = captain_world.snapshot()
	old_progression.personnel_version = 1
	_strip_habitation(old_progression)
	old_progression.erase("population_version")
	old_progression.erase("population")
	for legacy_ship in old_progression.ships:
		legacy_ship.erase("captain_profile")
		legacy_ship.erase("crew_profile")
		legacy_ship.erase("payroll")
	var legacy_progression_path := test_root + "/personnel-v1-upgrade.json"
	_expect(save_store.save_game(legacy_progression_path, old_progression) == OK, "original personnel v1 saves are still readable")
	var legacy_progression_read: Dictionary = save_store.load_game(legacy_progression_path)
	var progressed_restore = WorldScript.new()
	_expect(bool(legacy_progression_read.get("ok", false)) and progressed_restore.restore_snapshot(legacy_progression_read.state) == OK and progressed_restore.state.personnel_version == 2, "personnel v1 migrations create captain and payroll profiles")
	_expect(progressed_restore.state.ships.size() == old_progression.ships.size() and progressed_restore.state.ships[0].captain == old_progression.ships[0].captain and progressed_restore.state.ships[0].orders == old_progression.ships[0].orders and progressed_restore.state.ships[0].crew == old_progression.ships[0].crew, "migration preserves names, existing captains, ship orders and all crew counts")
	_expect(progressed_restore.state.ships[0].payroll.arrears == 0 and progressed_restore.state.ships[0].payroll.last_tick == progressed_restore.state.tick and progressed_restore.state.starting_credits == old_progression.starting_credits, "migration cannot invent back pay or silently debit player funds")
	var corrupt_captain: Dictionary = captain_world.snapshot()
	corrupt_captain.ships.back().captain_profile = corrupt_captain.ships[0].captain_profile.duplicate(true)
	_expect(save_store.save_game(test_root + "/duplicate-captain.json", corrupt_captain) != OK, "save validation blocks duplicating an individual captain identity")
	var corrupt_morale: Dictionary = captain_world.snapshot()
	corrupt_morale.ships[0].captain_profile.morale = 101
	_expect(save_store.save_game(test_root + "/invalid-morale.json", corrupt_morale) != OK, "captain morale cannot exceed 100 in a valid save")
	var corrupt_payroll: Dictionary = captain_world.snapshot()
	corrupt_payroll.ships[0].payroll.arrears = -10
	_expect(save_store.save_game(test_root + "/negative-payroll.json", corrupt_payroll) != OK, "negative crew wage debt is forbidden")
	var future_progression: Dictionary = captain_world.snapshot()
	future_progression.personnel_version = 3
	var future_progression_path := test_root + "/future-personnel-v3.json"
	_expect(save_store.save_game(future_progression_path, captain_world.snapshot()) == OK and save_store.save_game(future_progression_path, captain_world.snapshot()) == OK, "personnel future-version test prepares a valid backup")
	var future_progression_payload := Marshalls.variant_to_base64(future_progression, false)
	var future_progression_file := FileAccess.open(future_progression_path, FileAccess.WRITE)
	future_progression_file.store_string(JSON.stringify({"format_version":1, "payload":future_progression_payload, "checksum":future_progression_payload.sha256_text()}))
	future_progression_file.close()
	_expect(save_store.load_game(future_progression_path).get("reason") == "unsupported", "personnel v3 saves never downgrade through a backup")

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
	var footer_control: Control = screen.find_child("MainFooter", true, false)
	_expect(footer_control.global_position.y + footer_control.size.y <= float(root.size.y), "property and construction controls leave the footer within the viewport")
	_expect(screen.find_child("RolePicker", true, false) != null and screen.role_picker.item_count == 4, "property panel offers manual, trader, build supply and station supply roles")
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

	# Map navigation is presentation only; touch gestures and selection must
	# not change the world, and cards must resolve to actual entities.
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-maps.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	var map_world_before: Dictionary = screen.world.snapshot()
	var galaxy = screen.map_view
	var anchor := Vector2(250, 200)
	var map_anchor: Vector2 = galaxy.screen_to_map(anchor)
	galaxy.zoom_by(1.5, anchor)
	_expect(absf(galaxy.zoom_level - 1.5) < 0.001 and galaxy.screen_to_map(anchor).distance_to(map_anchor) < 0.01, "zoom keeps the point under the user's fingers fixed")
	galaxy.pan_by(Vector2(45, 25))
	var target_sector: Dictionary = {}
	for sector in screen.world.state.sectors:
		if sector.id == "vellum_gate":
			target_sector = sector
	var target_point: Vector2 = galaxy._sector_position(target_sector)
	_map_touch(galaxy, 0, target_point, true)
	_map_touch(galaxy, 0, target_point, false)
	_expect(screen.selected_sector == "vellum_gate", "a touch selects the correct sector after zoom and pan")
	var drag_start := Vector2(200, 220)
	var offset_before: Vector2 = galaxy.pan_offset
	_map_touch(galaxy, 0, drag_start, true)
	_map_drag(galaxy, 0, drag_start + Vector2(50, 30))
	_map_touch(galaxy, 0, drag_start + Vector2(50, 30), false)
	_expect(galaxy.pan_offset != offset_before and screen.selected_sector == "vellum_gate", "one-finger dragging pans without selecting a sector")
	var zoom_before: float = galaxy.zoom_level
	_map_touch(galaxy, 0, Vector2(100, 160), true)
	_map_touch(galaxy, 1, Vector2(200, 160), true)
	_map_drag(galaxy, 1, Vector2(260, 160))
	_map_touch(galaxy, 1, Vector2(260, 160), false)
	_map_touch(galaxy, 0, Vector2(100, 160), false)
	_expect(galaxy.zoom_level > zoom_before and screen.selected_sector == "vellum_gate", "pinching zooms without generating a stray tap")
	galaxy.zoom_by(100.0)
	_expect(is_equal_approx(galaxy.zoom_level, galaxy.MAX_ZOOM), "zoom has an upper bound")
	galaxy.zoom_by(0.00001)
	_expect(is_equal_approx(galaxy.zoom_level, galaxy.MIN_ZOOM), "zoom has a lower bound")
	screen.find_child("MapFit", true, false).pressed.emit()
	_expect(is_equal_approx(galaxy.zoom_level, 1.0) and galaxy.pan_offset == Vector2.ZERO, "Fit restores the galaxy view")
	var fitted_labels_visible := true
	var fitted_labels_clear := true
	var fitted_labels: Dictionary = galaxy._label_layout()
	for sector in screen.world.state.sectors:
		var label_rect: Rect2 = fitted_labels[sector.id]
		if label_rect.position.x < 0 or label_rect.position.y < 0 or label_rect.end.x > galaxy.size.x or label_rect.end.y > galaxy.size.y:
			fitted_labels_visible = false
		for other in screen.world.state.sectors:
			if other.id != sector.id:
				var marker := Rect2(galaxy._sector_position(other) - Vector2(13, 13), Vector2(26, 26))
				if label_rect.intersects(marker) or label_rect.intersects(fitted_labels[other.id]):
					fitted_labels_clear = false
	_expect(fitted_labels_visible, "sector names fit within the map at the default zoom")
	_expect(fitted_labels_clear, "sector names do not overlap other names or markers at the default zoom")
	screen.find_child("MapMode", true, false).pressed.emit()
	await process_frame
	_expect(screen.sector_map.visible and not galaxy.visible and screen.map_title.text == "VELLUM GATE", "sector view opens for the selected sector")
	var sector_view = screen.sector_map
	var foundry_card := _map_item(sector_view, "station", "vellum_foundry")
	_expect(not foundry_card.is_empty() and foundry_card.subtitle == "Needs Energy Cells", "sector view uses the real station and production status")
	if not foundry_card.is_empty():
		var point: Vector2 = foundry_card.rect.get_center()
		_map_touch(sector_view, 0, point, true)
		_map_touch(sector_view, 0, point, false)
	_expect(is_instance_valid(screen.trade_screen) and screen._trade_station_id() == "vellum_foundry", "tapping a station opens its actual market")
	if is_instance_valid(screen.trade_screen):
		screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	var meridian_card := _map_item(sector_view, "sector", "meridian")
	_expect(not meridian_card.is_empty(), "sector overview shows a real adjacent connection")
	if not meridian_card.is_empty():
		var point: Vector2 = meridian_card.rect.get_center()
		_map_touch(sector_view, 0, point, true)
		_map_touch(sector_view, 0, point, false)
	_expect(screen.selected_sector == "meridian" and screen.map_title.text == "MERIDIAN", "tapping a connection opens the adjacent sector")
	_expect(_map_item(sector_view, "station", "vellum_foundry").is_empty(), "sector view does not invent stations in empty sectors")
	_expect(screen.world.snapshot() == map_world_before, "camera and sector browsing do not alter simulation state")
	screen.find_child("MapZoomIn", true, false).pressed.emit()
	_expect(sector_view.zoom_level > 1.0, "zoom buttons also work in the sector overview")
	screen.find_child("MapFit", true, false).pressed.emit()
	_expect(is_equal_approx(sector_view.zoom_level, 1.0), "Fit resets the sector overview")
	screen.find_child("OrderButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].orders.size() == 1 and screen.world.state.ships[0].orders[0].destination == "meridian", "existing ship orders work from the sector view")
	screen._show_sector("verdant_trace")
	var npc_card := _map_item(sector_view, "ship", "npc_logistics_001")
	_expect(not npc_card.is_empty(), "sector overview lists real NPC traffic")
	if not npc_card.is_empty():
		sector_view._activate_at(npc_card.rect.get_center())
	_expect(screen.detail_title.text == "Wayfarer" and screen.detail_body.text.contains("Free Frontier"), "selecting faction traffic shows its actual owner and role")
	sector_view.zoom_by(1.25)
	sector_view.pan_by(Vector2(20, 10))
	var live_offset: Vector2 = sector_view.pan_offset
	screen.world.advance_ticks(12)
	screen._refresh_world_display()
	_expect(_map_item(sector_view, "ship", "npc_logistics_001").is_empty() and screen.detail_body.text.contains("Vellum Gate"), "sector traffic and ship details update when a ship actually travels")
	_expect(is_equal_approx(sector_view.zoom_level, 1.25) and sector_view.pan_offset == live_offset, "simulation updates preserve the current map camera")
	screen.find_child("MapMode", true, false).pressed.emit()
	_expect(galaxy.visible and not sector_view.visible and screen.map_title.text == "GALAXY MAP", "Galaxy returns to the strategic map")
	var map_mode_button: Control = screen.find_child("MapMode", true, false)
	_expect(map_mode_button.global_position.x + map_mode_button.size.x <= float(root.size.x) and map_mode_button.global_position.y + map_mode_button.size.y <= float(root.size.y), "map controls remain inside the landscape viewport")
	var before_station_preview: Dictionary = screen.world.snapshot()
	screen.find_child("PlanStationButton", true, false).pressed.emit()
	await process_frame
	_expect(is_instance_valid(screen.plan_screen) and screen.plan_result.text.contains("Choose a production module"), "station planner opens with a clear starting instruction")
	screen.find_child("PlanAdd_alloy_smelting", true, false).pressed.emit()
	_expect(screen.plan_result.text.contains("Alloy Smelter × 1") and screen.plan_result.text.contains("Ore Extractor × 1") and screen.plan_result.text.contains("Solar Array × 1"), "planner displays chosen and automatically required modules")
	screen.find_child("PlanRemove_alloy_smelting", true, false).pressed.emit()
	_expect(int(screen.plan_module_counts["alloy_smelting"].value) == 0 and screen.plan_result.text.contains("Choose a production module"), "large minus control removes a chosen module")
	screen.find_child("PlanRemove_alloy_smelting", true, false).pressed.emit()
	_expect(int(screen.plan_module_counts["alloy_smelting"].value) == 0, "module quantities cannot become negative")
	screen.find_child("PlanAdd_alloy_smelting", true, false).pressed.emit()
	screen.plan_mode.select(1)
	screen.plan_mode.item_selected.emit(1)
	_expect(screen.plan_import_list.visible and screen.plan_import_options.has("alloy_plates") and screen.plan_import_options.has("blank_media"), "selective sourcing includes inputs for the expanded production recipes")
	screen.plan_import_options["ore"].button_pressed = true
	_expect(not screen.plan_result.text.contains("Ore Extractor") and screen.plan_result.text.contains("Import 12.0"), "selecting an imported ware updates the preview and required rate")
	screen.plan_mode.select(2)
	screen.plan_mode.item_selected.emit(2)
	_expect(not screen.plan_result.text.contains("Solar Array") and not screen.plan_result.text.contains("Ore Extractor"), "import-all removes unnecessary upstream modules in the interface")
	_expect(screen.world.snapshot() == before_station_preview, "station planning spends no credits and builds no modules")
	await process_frame
	var planner_close: Control = screen.find_child("ClosePlannerButton", true, false)
	_expect(planner_close.global_position.y + planner_close.size.y <= float(root.size.y), "station planner close control remains inside the landscape viewport")
	var planner_add: Control = screen.find_child("PlanAdd_alloy_smelting", true, false)
	_expect(planner_add.size.x >= 44.0 and planner_add.size.y >= 44.0, "module add control has a touch-sized target")
	screen.find_child("ClosePlannerButton", true, false).pressed.emit()
	_expect(not is_instance_valid(screen.plan_screen), "station planner closes without changing the world")
	screen.queue_free()
	await process_frame

	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-construction.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	screen.find_child("PlanStationButton", true, false).pressed.emit()
	screen.find_child("PlanAdd_solar_cells", true, false).pressed.emit()
	_expect(screen.plan_result.text.contains("BUILDER FEE: 300 CR") and screen.plan_result.text.contains("Alloy Plates × 6") and not screen.plan_build_button.disabled, "planner shows the actual fee and materials before placement")
	screen.find_child("PlaceBuildSiteButton", true, false).pressed.emit()
	_expect(is_instance_valid(screen.build_screen) and screen.world.state.build_sites.size() == 1 and int(screen.world.state.starting_credits) == 24700, "placing a site opens its build queue and charges the quoted fee")
	screen._place_build_site()
	_expect(screen.world.state.build_sites.size() == 1 and int(screen.world.state.starting_credits) == 24700, "a repeated placement action cannot charge twice after the planner closes")
	var ui_site: Dictionary = screen.world.state.build_sites[0]
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)) and screen.build_info.text.contains("6 still needed"), "the placed site saves immediately and explains missing materials")
	_expect(screen.find_child("BuildTaskPicker", true, false) != null and screen.find_child("MoveBuildTaskUp", true, false) != null and screen.find_child("MoveBuildTaskDown", true, false) != null, "build screen exposes queue selection and clear move controls")
	_expect(screen.build_move_up_button.disabled and screen.build_move_down_button.disabled, "a single pending module has no illegal reorder movement")
	screen.find_child("AutoSupplyBuildButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].build_supply.enabled and screen.role_picker.selected == 2 and screen.build_supply_button.text.contains("Stop supplying"), "build screen assigns the ship and clearly offers a stop control")
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)) and screen.build_feedback.text.contains("credits"), "the supply assignment saves and explains purchases")
	screen.find_child("AutoSupplyBuildButton", true, false).pressed.emit()
	_expect(not screen.world.state.ships[0].build_supply.enabled and screen.role_picker.selected == 0, "build screen can stop supply and return the ship to manual control")
	await process_frame
	var supply_control: Control = screen.find_child("AutoSupplyBuildButton", true, false)
	_expect(supply_control.size.y >= 44.0 and supply_control.global_position.y + supply_control.size.y <= float(root.size.y), "automatic supply remains touch-sized and visible in landscape")
	var build_close_control: Control = screen.find_child("CloseBuildButton", true, false)
	_expect(build_close_control.global_position.y + build_close_control.size.y <= float(root.size.y), "build actions remain inside the landscape viewport after feedback")
	screen.find_child("DockBuildSiteButton", true, false).pressed.emit()
	screen.find_child("DeliverBuildMaterialsButton", true, false).pressed.emit()
	_expect(screen.build_feedback.text.contains("No required construction materials"), "build screen explains when no materials are aboard")
	screen.find_child("CloseBuildButton", true, false).pressed.emit()
	await process_frame
	screen.world.queue_fly_to("ship_001", "vellum_gate")
	screen.world.advance_ticks(10)
	screen.find_child("TradeButton", true, false).pressed.emit()
	for index in screen.trade_station_picker.item_count:
		if screen.trade_station_picker.get_item_metadata(index) == "vellum_foundry":
			screen.trade_station_picker.select(index)
	for index in screen.trade_ware_picker.item_count:
		if screen.trade_ware_picker.get_item_metadata(index) == "alloy_plates":
			screen.trade_ware_picker.select(index)
	screen._update_trade_screen()
	screen.find_child("DockButton", true, false).pressed.emit()
	screen.trade_quantity.value = 6
	screen.find_child("BuyButton", true, false).pressed.emit()
	_expect(int(screen.world.state.ships[0].cargo.alloy_plates) == 6, "build UI scenario purchases real alloy at the NPC market")
	screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	screen.world.queue_fly_to("ship_001", "hearthreach")
	screen.world.advance_ticks(10)
	screen.find_child("BuildsButton", true, false).pressed.emit()
	screen.find_child("DockBuildSiteButton", true, false).pressed.emit()
	screen.find_child("DeliverBuildMaterialsButton", true, false).pressed.emit()
	_expect(int(ui_site.build_storage.alloy_plates) == 6 and screen.build_feedback.text.contains("Delivered"), "build screen delivers the purchased cargo to the site")
	screen.find_child("PauseBuildButton", true, false).pressed.emit()
	screen.world.advance_ticks(12)
	_expect(ui_site.paused and int(ui_site.completed) == 0, "build screen pause prevents construction")
	screen.find_child("PauseBuildButton", true, false).pressed.emit()
	screen.world.advance_ticks(35)
	screen._update_build_screen()
	_expect(not ui_site.paused and int(ui_site.completed) == 1 and screen.build_info.text.contains("Complete"), "build screen resume leads to a completed station")
	screen.find_child("CloseBuildButton", true, false).pressed.emit()
	await process_frame
	screen.world.advance_ticks(8)
	screen.find_child("TradeButton", true, false).pressed.emit()
	for index in screen.trade_station_picker.item_count:
		if screen.trade_station_picker.get_item_metadata(index) == ui_site.station_id:
			screen.trade_station_picker.select(index)
	for index in screen.trade_ware_picker.item_count:
		if screen.trade_ware_picker.get_item_metadata(index) == "energy_cells":
			screen.trade_ware_picker.select(index)
	screen._update_trade_screen()
	_expect(screen.trade_buy_button.text == "Take from station" and screen.trade_info.text.contains("Transfers between your ship and station are free"), "owned stations offer clear free cargo transfers")
	screen.trade_quantity.value = 1
	var ui_credits_before: int = int(screen.world.state.starting_credits)
	screen.find_child("BuyButton", true, false).pressed.emit()
	_expect(int(screen.world.state.ships[0].cargo.energy_cells) == 1 and int(screen.world.state.starting_credits) == ui_credits_before, "owned-station UI takes produced cargo without a fabricated purchase")
	screen.queue_free()
	await process_frame

	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-archive.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	screen._show_sector("hearthreach")
	var archive_map_item := _map_item(screen.sector_map, "station", "auroran_archive")
	_expect(not archive_map_item.is_empty() and str(archive_map_item.subtitle).contains("Archive"), "the sector map identifies the faction archive as a station")
	screen.sector_map.station_selected.emit("auroran_archive")
	_expect(is_instance_valid(screen.trade_screen) and screen._trade_station_id() == "auroran_archive" and screen.trade_archive_button.visible and screen.trade_archive_button.disabled, "choosing the archive shows its records control and asks the visitor to dock")
	screen.find_child("DockButton", true, false).pressed.emit()
	_expect(not screen.trade_archive_button.disabled and screen.trade_production.text.contains("Archive:"), "docking enables records and shows the archive's service status")
	await process_frame
	var archive_trade_close: Control = screen.find_child("CloseTradeButton", true, false)
	_expect(archive_trade_close.global_position.y + archive_trade_close.size.y <= float(root.size.y), "archive market controls remain within the landscape viewport")
	screen.find_child("ReadArchiveButton", true, false).pressed.emit()
	_expect(is_instance_valid(screen.archive_screen) and screen.find_child("ArchiveOverview", true, false).text.contains("Living worlds"), "archive screen displays its world and future research subjects")
	_expect(screen.find_child("ArchiveRecord_0", true, false).text.contains("Illuminated book") and screen.find_child("ArchiveRecord_0", true, false).text.contains("Kaelith"), "archive screen shows the physical medium and original lore")
	_expect(screen.world.state.visited_archives == ["auroran_archive"] and bool(save_store.load_game(screen.save_path).get("ok", false)), "opening the archive saves its visit")
	await process_frame
	var archive_close: Control = screen.find_child("CloseArchiveButton", true, false)
	_expect(archive_close.size.y >= 44.0 and archive_close.global_position.y + archive_close.size.y <= float(root.size.y), "the archive close control is touch-sized and visible")
	screen.find_child("CloseArchiveButton", true, false).pressed.emit()
	_expect(not is_instance_valid(screen.archive_screen) and is_instance_valid(screen.trade_screen), "closing the collection returns to its station")
	screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	screen.find_child("PlanStationButton", true, false).pressed.emit()
	screen.find_child("PlanAdd_data_reproduction", true, false).pressed.emit()
	_expect(screen.plan_result.text.contains("Recorded Data") and screen.plan_result.text.contains("reusable source"), "the planner explains the reusable source needed for a player scriptorium")
	screen.queue_free()
	await process_frame

	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-research.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	_expect(screen.world.restore_snapshot(research_refs.snapshot()) == OK, "research screen scenario restores a built laboratory and visited archives")
	screen._refresh_world_display()
	screen.find_child("TradeButton", true, false).pressed.emit()
	for index in screen.trade_station_picker.item_count:
		if screen.trade_station_picker.get_item_metadata(index) == research_lab.id:
			screen.trade_station_picker.select(index)
	screen._on_trade_selection(0)
	_expect(screen.trade_research_button.visible, "a player laboratory offers research projects from its station screen")
	_expect(screen.trade_station_supply_button.visible, "a player laboratory also offers input supply alongside research")
	screen.find_child("ResearchButton", true, false).pressed.emit()
	_expect(is_instance_valid(screen.research_screen) and screen.research_picker.item_count == 3, "research screen lists the available projects")
	_expect(screen.research_info.text.contains("bonus cap reached") and screen.research_info.text.contains("+1 per note"), "research screen distinguishes contributing archives from sources beyond the cap")
	for index in screen.research_picker.item_count:
		if screen.research_picker.get_item_metadata(index) == "resource_surveying":
			screen.research_picker.select(index)
	screen.research_picker.item_selected.emit(screen.research_picker.selected)
	_expect(screen.research_info.text.contains("Auroran Hall of Memory") and screen.research_info.text.contains("Current progress per note: 4"), "project details name relevant archives and their exact bonus")
	screen.find_child("StartResearchButton", true, false).pressed.emit()
	_expect(screen.world.state.research.active_project_id == "resource_surveying" and bool(save_store.load_game(screen.save_path).get("ok", false)), "starting research through the interface saves the assignment")
	screen.find_child("PauseResearchButton", true, false).pressed.emit()
	_expect(screen.world.state.research.active_project_id == "" and screen.research_feedback.text.contains("retained"), "research screen pauses without discarding progress")
	await process_frame
	var research_close_control: Control = screen.find_child("CloseResearchButton", true, false)
	_expect(research_close_control.size.y >= 44.0 and research_close_control.global_position.y + research_close_control.size.y <= float(root.size.y), "research controls are touch-sized and visible in landscape")
	screen.find_child("CloseResearchButton", true, false).pressed.emit()
	_expect(not is_instance_valid(screen.research_screen) and is_instance_valid(screen.trade_screen), "closing research returns to the station")
	screen.queue_free()
	await process_frame

	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-station-supply.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	_expect(screen.world.restore_snapshot(station_setup) == OK, "station supply screen restores a completed production station")
	screen._refresh_world_display()
	screen.find_child("TradeButton", true, false).pressed.emit()
	for index in screen.trade_station_picker.item_count:
		if screen.trade_station_picker.get_item_metadata(index) == supplied_station.id:
			screen.trade_station_picker.select(index)
	screen._on_trade_selection(0)
	_expect(screen.trade_station_supply_button.visible, "an owned station offers input supply from its station screen")
	screen.find_child("StationSupplyButton", true, false).pressed.emit()
	_expect(is_instance_valid(screen.station_supply_screen) and screen.station_supply_info.text.contains("Energy Cells") and screen.station_supply_info.text.contains("Ore"), "the supply screen names the station's actual needed inputs")
	_expect(screen.station_supply_info.text.contains("zero") and screen.find_child("StopStationSupplyButton", true, false).disabled, "the supply screen explains a zero cap and initially offers no stop action")
	screen.station_supply_budget.value = 18
	screen.find_child("AssignStationSupplyButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].station_supply.enabled and int(screen.world.state.ships[0].station_supply.budget_limit) == 18 and bool(save_store.load_game(screen.save_path).get("ok", false)), "assigning supply through the interface saves the selected allowance")
	_expect(screen.role_picker.selected == 3 and not screen.find_child("StopStationSupplyButton", true, false).disabled, "the station supplier role and stop control reflect the new assignment")
	screen.station_supply_budget.value = 30
	screen.find_child("AssignStationSupplyButton", true, false).pressed.emit()
	_expect(int(screen.world.state.ships[0].station_supply.budget_limit) == 30, "the interface can update the existing purchase cap")
	await process_frame
	var supply_close_control: Control = screen.find_child("CloseStationSupplyButton", true, false)
	_expect(supply_close_control.size.y >= 44.0 and supply_close_control.global_position.y + supply_close_control.size.y <= float(root.size.y), "station supply controls are touch-sized and visible in landscape")
	screen.find_child("StopStationSupplyButton", true, false).pressed.emit()
	_expect(not screen.world.state.ships[0].station_supply.enabled and screen.role_picker.selected == 0 and bool(save_store.load_game(screen.save_path).get("ok", false)), "stopping supply through the interface saves the unassigned role")
	screen.find_child("CloseStationSupplyButton", true, false).pressed.emit()
	_expect(not is_instance_valid(screen.station_supply_screen) and is_instance_valid(screen.trade_screen), "closing station supply returns to the station")
	screen.queue_free()
	await process_frame
	# Property management: two player ships, a completed station and an active
	# build site must remain distinct command targets without creating new data.
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-property-management.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	var property_world = screen.world
	_disable_npc_trading(property_world)
	var property_first: Dictionary = property_world.state.ships[0]
	var built_property: Dictionary = property_world.construction.place(property_world, "hearthreach", {"solar_cells":1}, "self", [])
	_expect(built_property.ok, "property scenario can place a real player station")
	var ready_site: Dictionary = property_world.construction.find_site(property_world, str(built_property.site_id))
	property_world._find_station("vellum_foundry").stock.alloy_plates -= 6
	property_first.cargo.alloy_plates = 6
	property_world.dock_ship(str(property_first.id), str(ready_site.station_id))
	property_world.construction.deliver(property_world, str(property_first.id), str(ready_site.id))
	property_world.advance_ticks(65)
	_expect(int(ready_site.completed) == 1, "property scenario commissions a player-owned working station")
	var waiting_property: Dictionary = property_world.construction.place(property_world, "lantern_deep", {"solar_cells":1}, "self", [])
	_expect(waiting_property.ok, "property scenario also has an unfinished build site")
	var second_ship: Dictionary = property_first.duplicate(true)
	second_ship.id = "player_ship_second"
	second_ship.name = "Second Wind"
	second_ship.captain = "Ilya Tor"
	second_ship.crew = 3
	second_ship.sector = "vellum_gate"
	second_ship.docked_at = ""
	second_ship.orders = []
	second_ship.travel = {}
	second_ship.cargo = {}
	second_ship.role = "Unassigned"
	second_ship.status = "Idle"
	second_ship.player_trader = {"enabled":false, "phase":"idle", "source_id":"", "destination_id":"", "ware_id":"", "quantity":0, "managed_quantity":0, "retry_ticks":0}
	second_ship.build_supply = property_world.build_supply._empty_job()
	second_ship.station_supply = property_world.station_supply._empty_job()
	property_world.personnel.initialize_ship(second_ship, int(property_world.state.tick), "vellum_foundry")
	property_world.state.ships.append(second_ship)
	screen._refresh_world_display()
	_expect(screen.property_count_label.text.contains("2 ships") and screen.property_count_label.text.contains("1 stations") and screen.property_count_label.text.contains("1 sites"), "property directory lists owned ships, working stations and active sites separately")
	_expect(screen.property_picker.item_count == 4 and screen.find_child("PropertySearch", true, false) != null and screen.find_child("OpenPropertyButton", true, false) != null, "searchable property directory exposes four real owned assets")
	var original_selection: String = screen.active_player_ship_id
	_expect(not screen._activate_player_ship("npc_builder_001") and screen.active_player_ship_id == original_selection, "NPC property cannot be selected or controlled as a player ship")
	screen.property_filter.text = "SECOND WIND"
	screen._on_property_filter("SECOND WIND")
	_expect(screen.property_picker.item_count == 1 and str(screen.property_picker.get_item_metadata(0)) == "ship|player_ship_second", "property search finds an owned ship case insensitively")
	screen.property_picker.select(0)
	screen.property_picker.item_selected.emit(0)
	_expect(screen.active_player_ship_id == second_ship.id and screen.detail_title.text == second_ship.name and screen.detail_body.text.contains("Ilya Tor"), "choosing the second ship updates its captain and detail view")
	screen.role_picker.select(1)
	screen.role_picker.item_selected.emit(1)
	_expect(second_ship.player_trader.enabled and not property_first.player_trader.enabled and screen.role_picker.selected == 1, "setting a ship role affects only the selected player ship")
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)), "second ship role and original property save successfully")
	screen.find_child("TradeButton", true, false).pressed.emit()
	for index in range(screen.trade_station_picker.item_count):
		if str(screen.trade_station_picker.get_item_metadata(index)) == "vellum_foundry":
			screen.trade_station_picker.select(index)
			break
	for index in range(screen.trade_ware_picker.item_count):
		if str(screen.trade_ware_picker.get_item_metadata(index)) == "alloy_plates":
			screen.trade_ware_picker.select(index)
			break
	screen._update_trade_screen()
	screen.find_child("DockButton", true, false).pressed.emit()
	screen.trade_quantity.value = 1
	screen.find_child("BuyButton", true, false).pressed.emit()
	_expect(second_ship.docked_at == "vellum_foundry" and int(second_ship.cargo.get("alloy_plates", 0)) == 1 and int(property_first.cargo.get("alloy_plates", 0)) == 0, "docking and buying cargo use the selected ship, not First Light")
	screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	screen.map_view.sector_selected.emit("cinder_veil")
	screen.find_child("OrderButton", true, false).pressed.emit()
	_expect(second_ship.orders.size() == 1 and property_first.orders.is_empty(), "fly orders are queued only on the active player ship")
	screen.property_filter.text = "nomatchingasset"
	screen._on_property_filter("nomatchingasset")
	_expect(screen.property_picker.disabled and screen.property_action_button.disabled and screen.active_player_ship_id == second_ship.id, "an empty search safely disables selection and retains the command ship")
	screen.property_filter.text = "outpost 1"
	screen._on_property_filter("outpost 1")
	_expect(screen.property_picker.item_count == 1 and str(screen.property_picker.get_item_metadata(0)) == "station|" + str(ready_site.station_id), "a commissioned site is listed as a working station, not a duplicate plot")
	screen.property_picker.select(0)
	screen.property_picker.item_selected.emit(0)
	_expect(screen.selected_view == "owned_station" and screen.detail_body.text.contains("Production modules: 1"), "selecting a player station shows its actual production")
	screen.property_action_button.pressed.emit()
	_expect(screen._trade_station_id() == str(ready_site.station_id) and is_instance_valid(screen.trade_screen), "station property action opens the chosen station's trade screen")
	screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	screen.property_filter.text = "outpost 2"
	screen._on_property_filter("outpost 2")
	_expect(screen.property_picker.item_count == 1 and str(screen.property_picker.get_item_metadata(0)) == "site|" + str(waiting_property.site_id), "uncompleted construction is separately accessible as a build site")
	screen.property_picker.select(0)
	screen.property_picker.item_selected.emit(0)
	_expect(screen.selected_view == "owned_site" and screen.detail_body.text.contains("Modules completed: 0 / 1"), "site selection shows the actual construction state")
	screen.property_action_button.pressed.emit()
	_expect(is_instance_valid(screen.build_screen) and str(screen._selected_build_site().id) == str(waiting_property.site_id), "build-site property action manages the selected construction plot")
	screen.find_child("AutoSupplyBuildButton", true, false).pressed.emit()
	_expect(second_ship.build_supply.enabled and second_ship.build_supply.site_id == waiting_property.site_id and not property_first.build_supply.enabled, "build supplies can be assigned to the selected second ship without changing First Light")
	screen.find_child("CloseBuildButton", true, false).pressed.emit()
	await process_frame
	screen._refresh_world_display()
	_expect(screen.active_player_ship_id == second_ship.id and bool(save_store.load_game(screen.save_path).get("ok", false)), "property selection survives refresh and its real ship assignments remain saveable")
	var property_loaded: Dictionary = save_store.load_game(screen.save_path)
	_expect(bool(property_loaded.get("ok", false)) and property_loaded.state.ships.any(func(item): return item.id == second_ship.id and item.build_supply.enabled), "saved world preserves the second player's stable ship ID and assigned role")
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-property-management.json"
	root.add_child(screen)
	await process_frame
	var continue_property_button: Button = screen.find_child("ContinueButton", true, false)
	_expect(continue_property_button != null, "multi-property saved game remains available to continue")
	if continue_property_button != null:
		continue_property_button.pressed.emit()
		await process_frame
		await process_frame
		_expect(screen.property_picker.item_count == 4 and screen.active_player_ship_id == "ship_001", "continuing a multi-property save restores all assets and defaults to a valid owned command ship")
		_expect(screen.world._find_ship(second_ship.id).build_supply.enabled, "saved second-ship automation survives a UI restart")
	screen.queue_free()
	await process_frame
	# The player can really buy and command a new ship from the on-screen
	# wharf interface, rather than inserting a test-only property.
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-ship-orders.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	_disable_npc_trading(screen.world)
	var ui_original_ship: Dictionary = screen.world.state.ships[0]
	screen.find_child("ShipyardButton", true, false).pressed.emit()
	_expect(is_instance_valid(screen.shipyard_screen) and screen.shipyard_info.text.contains("physically at wharf") and screen.find_child("ShipyardHullPicker", true, false) != null, "shipyard menu displays physical wharf inventory and selectable hulls")
	_expect(screen.shipyard_hull_picker.item_count == 2 and not screen.shipyard_buy_button.disabled, "two hull types are available to buy with real starting funds and wharf stock")
	for index in range(screen.shipyard_hull_picker.item_count):
		if str(screen.shipyard_hull_picker.get_item_metadata(index)) == "freighter_mk1":
			screen.shipyard_hull_picker.select(index)
			screen._on_shipyard_hull_selected(index)
			break
	_expect(screen.shipyard_info.text.contains("8500 CR") and screen.shipyard_info.text.contains("Cargo capacity: 180"), "freighter quote shows its real contract cost and cargo capacity")
	screen.find_child("OrderShipButton", true, false).pressed.emit()
	_expect(screen.shipyard_confirm.dialog_text.contains("8500 CR") and screen.world.state.shipyard.orders.is_empty(), "buying a hull requires confirmation before spending")
	screen.shipyard_confirm.confirmed.emit()
	_expect(screen.world.state.shipyard.orders.size() == 1 and int(screen.world.state.starting_credits) == 16500 and int(screen.world._find_station("vellum_foundry").stock.alloy_plates) == 70, "confirmed purchase transfers credits and consumes exactly 30 alloy plates")
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)) and screen.property_count_label.text.contains("1 ships"), "paid pending order saves without granting an instant ship")
	screen.world.advance_ticks(48)
	screen._refresh_world_display()
	screen._update_shipyard_screen()
	var delivered_id: String = str(screen.world.state.shipyard.orders[0].ship_id)
	var delivered_ship: Dictionary = screen.world._find_ship(delivered_id)
	_expect(not delivered_ship.is_empty() and delivered_ship.owner == "player" and delivered_ship["class"] == "Freighter" and int(delivered_ship.cargo_capacity) == 180 and screen.property_count_label.text.contains("2 ships"), "completed paid freighter joins the player's property directory as a real second ship")
	_expect(screen.shipyard_info.text.contains("Complete") and bool(save_store.save_game(screen.save_path, screen.world.snapshot()) == OK), "the shipyard panel reports delivery and the completed new ship is saveable")
	screen.find_child("CloseShipyardButton", true, false).pressed.emit()
	await process_frame
	screen.property_filter.text = "freighter"
	screen._on_property_filter("freighter")
	_expect(screen.property_picker.item_count == 1 and str(screen.property_picker.get_item_metadata(0)) == "ship|" + delivered_id, "newly built freighter is individually searchable")
	screen.property_picker.select(0)
	screen.property_picker.item_selected.emit(0)
	_expect(screen.active_player_ship_id == delivered_id and screen.detail_title.text == delivered_ship.name, "the manufactured ship can be selected as the active command vessel")
	screen.map_view.sector_selected.emit("cinder_veil")
	screen.find_child("OrderButton", true, false).pressed.emit()
	_expect(delivered_ship.orders.size() == 1 and ui_original_ship.orders.is_empty(), "real purchased freighters receive individual orders without changing the starter ship")
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)), "newly purchased vessel orders survive normal autosaving")
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-ship-orders.json"
	root.add_child(screen)
	await process_frame
	var continue_wharf: Button = screen.find_child("ContinueButton", true, false)
	_expect(continue_wharf != null, "save containing a manufactured hull remains available to continue")
	if continue_wharf != null:
		continue_wharf.pressed.emit()
		await process_frame
		await process_frame
		_expect(screen.property_count_label.text.contains("2 ships") and screen.world._find_ship(delivered_id).orders.size() == 1, "reload restores purchased hull and its queued route with no duplication")
	screen.queue_free()
	await process_frame
	# Ship management UI saves real ship names, recruitment, discharge and
	# physical transfers without changing which asset is being commanded.
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-personnel.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	_disable_npc_trading(screen.world)
	var ui_crew_ship: Dictionary = screen.world.state.ships[0]
	screen.find_child("ManageCrewButton", true, false).pressed.emit()
	_expect(is_instance_valid(screen.crew_screen) and screen.find_child("RenameShipButton", true, false) != null and screen.find_child("HireCrewButton", true, false) != null and screen.find_child("DischargeCrewButton", true, false) != null and screen.find_child("TransferCrewButton", true, false) != null, "ship-property panel exposes actual rename, recruitment, discharge and transfer controls")
	_expect(screen.crew_info.text.contains("Mira Vale") and screen.crew_info.text.contains("2 / 8 berths") and screen.crew_transfer_picker.disabled, "crew interface displays the separate captain, real berth capacity and no phantom transfer destinations")
	screen.crew_rename_input.text = "Dawn Voyager"
	screen.find_child("RenameShipButton", true, false).pressed.emit()
	_expect(ui_crew_ship.name == "Dawn Voyager" and screen.ship_button.text.contains("Dawn Voyager") and screen.detail_title.text == "Dawn Voyager", "renaming in UI changes the selected ship everywhere without replacing its ID")
	screen.crew_quantity.value = 2
	var before_ui_hire: int = int(screen.world.state.starting_credits)
	screen.find_child("HireCrewButton", true, false).pressed.emit()
	_expect(int(ui_crew_ship.crew) == 2 and int(screen.world.state.starting_credits) == before_ui_hire and screen.crew_feedback.text.contains("Dock"), "UI refuses undocked recruitment without spending")
	screen.find_child("CloseCrewButton", true, false).pressed.emit()
	await process_frame
	screen.find_child("TradeButton", true, false).pressed.emit()
	for index in range(screen.trade_station_picker.item_count):
		if str(screen.trade_station_picker.get_item_metadata(index)) == "hearth_exchange":
			screen.trade_station_picker.select(index)
			break
	screen.find_child("DockButton", true, false).pressed.emit()
	_expect(ui_crew_ship.docked_at == "hearth_exchange", "UI ship reaches a real NPC crew market using its existing trade/docking controls")
	screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	screen.find_child("ManageCrewButton", true, false).pressed.emit()
	_expect(screen.crew_info.text.contains("Available recruits: 12"), "UI displays the physical recruitment pool at the dock")
	screen.crew_quantity.value = 2
	screen.find_child("HireCrewButton", true, false).pressed.emit()
	_expect(int(ui_crew_ship.crew) == 4 and int(screen.world.state.starting_credits) == before_ui_hire - 500 and int(screen.world.state.crew_pools.hearth_exchange) == 10, "UI hiring transfers real credits and reduces the finite NPC roster")
	screen.crew_quantity.value = 1
	screen.find_child("DischargeCrewButton", true, false).pressed.emit()
	_expect(int(ui_crew_ship.crew) == 3 and int(screen.world.state.crew_pools.hearth_exchange) == 11 and int(screen.world.state.starting_credits) == before_ui_hire - 500, "UI discharge returns one worker without an invented refund")
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)) and save_store.load_game(screen.save_path).state.ships[0].name == "Dawn Voyager", "crew management immediately saves renamed vessel and financial/crew changes")
	screen.find_child("CloseCrewButton", true, false).pressed.emit()
	await process_frame
	var ui_contract: Dictionary = screen.world.shipyard.place_order(screen.world, "courier_mk1")
	screen.world.advance_ticks(24)
	var ui_second: Dictionary = screen.world._find_ship(str(ui_contract.ship_id))
	_expect(ui_contract.ok and not ui_second.is_empty() and screen.world.personnel.capacity(ui_second) == 8, "real wharf-built courier supports the same crew management interface")
	_expect(screen.world.queue_fly_to("ship_001", "vellum_gate"), "player can fly renamed vessel to a dock holding the new courier")
	screen.world.advance_ticks(35)
	_expect(screen.world.dock_ship("ship_001", "vellum_foundry").ok, "both player ships dock at a single real station for transfer")
	screen._refresh_world_display()
	screen.find_child("ManageCrewButton", true, false).pressed.emit()
	_expect(not screen.crew_transfer_picker.disabled and str(screen.crew_transfer_picker.get_item_metadata(screen.crew_transfer_picker.selected)) == ui_second.id, "transfer picker shows only a co-docked owned ship")
	screen.crew_quantity.value = 2
	screen.find_child("TransferCrewButton", true, false).pressed.emit()
	_expect(int(ui_crew_ship.crew) == 1 and int(ui_second.crew) == 4 and screen.crew_feedback.text.contains("Transferred"), "UI moves two existing crew between ships without materializing people")
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)), "UI transfers save the existing real ship IDs and rosters")
	screen.find_child("CloseCrewButton", true, false).pressed.emit()
	await process_frame
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-personnel.json"
	root.add_child(screen)
	await process_frame
	var continue_crew: Button = screen.find_child("ContinueButton", true, false)
	_expect(continue_crew != null, "renamed and staffed fleet has a resumable save")
	if continue_crew != null:
		continue_crew.pressed.emit()
		await process_frame
		await process_frame
		_expect(screen.world._find_ship("ship_001").name == "Dawn Voyager" and int(screen.world._find_ship("ship_001").crew) == 1 and int(screen.world._find_ship(str(ui_contract.ship_id)).crew) == 4, "reloaded fleet retains paid hires, discharge, transfer and original identities")
	screen.queue_free()
	await process_frame

	# Real UI exposes named captain progression and swaps experienced pilots
	# without changing the identities of their commissioned ships.
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-captain-progression.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	_disable_npc_trading(screen.world)
	screen.find_child("ManageCrewButton", true, false).pressed.emit()
	_expect(screen.find_child("SwapCaptainsButton", true, false) != null and screen.crew_captain_swap_button.disabled, "crew menu exposes captain swaps but disables them without a second co-docked ship")
	_expect(screen.crew_info.text.contains("CAPTAIN PROFILE") and screen.crew_info.text.contains("SERVICE CREW PROGRESSION") and screen.crew_info.text.contains("PAYROLL"), "crew menu reports named captain, service skills and explicit wage cost")
	_expect(screen.crew_info.text.contains("18 CR every 60 ticks") and screen.crew_info.text.contains("Next payroll in: 60 ticks"), "initial captain and two service crew display correct live payroll")
	screen.find_child("CloseCrewButton", true, false).pressed.emit()
	await process_frame
	var ui_captain_order: Dictionary = screen.world.shipyard.place_order(screen.world, "courier_mk1")
	screen.world.advance_ticks(24)
	var ui_captain_first: Dictionary = screen.world._find_ship("ship_001")
	var ui_captain_second: Dictionary = screen.world._find_ship(str(ui_captain_order.ship_id))
	var initial_first_pilot: String = str(ui_captain_first.captain)
	var initial_second_pilot: String = str(ui_captain_second.captain)
	_expect(ui_captain_order.ok and not ui_captain_second.is_empty(), "UI captain exchange uses a real paid wharf-built second ship")
	screen.world.queue_fly_to("ship_001", "vellum_gate")
	screen.world.advance_ticks(20)
	_expect(screen.world.dock_ship("ship_001", "vellum_foundry").ok, "both captains physically meet at a valid wharf dock")
	screen._refresh_world_display()
	screen.find_child("ManageCrewButton", true, false).pressed.emit()
	_expect(not screen.crew_captain_swap_button.disabled and screen.crew_transfer_picker.item_count == 1, "captain exchange is enabled for an eligible co-docked player vessel")
	screen.find_child("SwapCaptainsButton", true, false).pressed.emit()
	_expect(ui_captain_first.captain == initial_second_pilot and ui_captain_second.captain == initial_first_pilot, "GUI swaps named pilots without exchanging ships or generating a new captain")
	_expect(screen.crew_info.text.contains(initial_second_pilot) and screen.crew_feedback.text.contains("Captains exchanged"), "pilot management UI updates visible name and action result")
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)), "captain assignment is saved immediately after a UI swap")
	screen.world.advance_ticks(61)
	screen._update_crew_screen()
	_expect(screen.crew_info.text.contains("Total paid:") and screen.crew_info.text.contains("Morale:") and int(ui_captain_first.payroll.total_paid) > 0, "live crew UI updates after a real recurring paid payroll")
	screen.find_child("CloseCrewButton", true, false).pressed.emit()
	await process_frame
	screen.queue_free()
	await process_frame
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-captain-progression.json"
	root.add_child(screen)
	await process_frame
	var continue_pilot: Button = screen.find_child("ContinueButton", true, false)
	_expect(continue_pilot != null, "named-captain management keeps a resumable save")
	if continue_pilot != null:
		continue_pilot.pressed.emit()
		await process_frame
		await process_frame
		_expect(screen.world._find_ship("ship_001").captain == initial_second_pilot and screen.world._find_ship(str(ui_captain_order.ship_id)).captain == initial_first_pilot, "save/load preserves the real exchanged captain assignments")
	screen.queue_free()
	await process_frame

	# Pass 25: one resident population accounting ledger. Existing NPC
	# recruit rosters are mirrored, never summed as a second group of people.
	var resident_world = WorldScript.new()
	_expect(resident_world.load_starter() == OK, "starter galaxy initializes the population accounting ledger")
	_disable_npc_trading(resident_world)
	_expect(resident_world.state.population_version == 1 and resident_world.state.population.stations.size() == resident_world.state.stations.size(), "all existing NPC stations receive one resident cohort")
	var hearth_cohort: Dictionary = resident_world.population.station_cohort(resident_world, "hearth_exchange")
	_expect(int(hearth_cohort.cohorts.available_workers) == 12 and resident_world.state.crew_pools.hearth_exchange == 12 and resident_world.population.station_total(hearth_cohort) == 12, "twelve legacy jobseekers are the same twelve residents, never twenty-four people")
	_expect(int(hearth_cohort.cohorts.children) == 0 and int(hearth_cohort.cohorts.students) == 0 and int(hearth_cohort.cohorts.assigned_workers) == 0 and int(hearth_cohort.cohorts.retirees) == 0 and int(hearth_cohort.hab_capacity) == 0, "first cohort has no fictional births, schools, housing or station employment")
	var known_before: int = resident_world.population.total_people(resident_world)
	var expected_known: int = 0
	for historic_pool in resident_world.state.crew_pools:
		expected_known += int(resident_world.state.crew_pools[historic_pool])
	for counted_ship in resident_world.state.ships:
		expected_known += int(counted_ship.crew) + 1
	_expect(known_before == expected_known, "galaxy population total includes each existing worker once, plus actual ship crews and pilots")
	var residents_report: Array = resident_world.population.report(resident_world)
	_expect(residents_report.size() == resident_world.state.stations.size() and residents_report[0].housing_status == "No habitat", "station roster report accurately labels housing and life support as unimplemented")
	_expect(not resident_world.population.move_workers(resident_world, "not_a_station", -1), "invalid source station cannot give away free residents")
	_expect(not resident_world.population.move_workers(resident_world, "hearth_exchange", -13) and resident_world.population.total_people(resident_world) == known_before, "empty or insufficient cohorts cannot supply more than the available adults")
	_expect(resident_world.dock_ship("ship_001", "hearth_exchange").ok, "starter ship can dock at a station with counted resident workers")
	var adult_recruit: Dictionary = resident_world.personnel.hire(resident_world, "ship_001", 2)
	_expect(adult_recruit.ok and resident_world.population.available_workers(resident_world, "hearth_exchange") == 10 and int(resident_world.state.crew_pools.hearth_exchange) == 10 and int(resident_world.state.ships[0].crew) == 4, "paid hiring removes the exact adults from their origin cohort and boards them on the same real ship")
	_expect(resident_world.population.total_people(resident_world) == known_before, "hiring service crew preserves galaxy-wide accounted headcount")
	var adult_discharge: Dictionary = resident_world.personnel.discharge(resident_world, "ship_001", 1)
	_expect(adult_discharge.ok and resident_world.population.available_workers(resident_world, "hearth_exchange") == 11 and resident_world.state.crew_pools.hearth_exchange == 11 and resident_world.state.ships[0].crew == 3, "discharge returns one actual worker to the station cohort")
	_expect(resident_world.population.total_people(resident_world) == known_before, "discharging service crew cannot duplicate or destroy residents")
	var resident_save_path := test_root + "/resident-labor.json"
	_expect(save_store.save_game(resident_save_path, resident_world.snapshot()) == OK, "cohort-backed real recruitment passes complete save validation")
	var resident_saved: Dictionary = save_store.load_game(resident_save_path)
	var resident_reloaded = WorldScript.new()
	_expect(bool(resident_saved.get("ok", false)) and resident_reloaded.restore_snapshot(resident_saved.state) == OK and resident_reloaded.snapshot() == resident_world.snapshot(), "cohort-backed hiring round-trips without resetting people, funds or crew")
	_expect(resident_reloaded.population.total_people(resident_reloaded) == known_before and resident_reloaded.population.available_workers(resident_reloaded, "hearth_exchange") == 11, "resident cohort counts and onboard personnel remain conserved through save/reload")
	var no_free_people: Dictionary = resident_world.snapshot()
	_expect(save_store.save_game(test_root + "/resident-valid.json", no_free_people) == OK, "well-formed population record saves normally")
	no_free_people.population.stations.hearth_exchange.cohorts.available_workers = 12
	_expect(save_store.save_game(test_root + "/resident-dupe-workers.json", no_free_people) != OK, "save validator rejects duplicated recruits in population-versus-legacy mirror")
	var impossible_child: Dictionary = resident_world.snapshot()
	impossible_child.population.stations.hearth_exchange.cohorts.children = 1
	_expect(save_store.save_game(test_root + "/resident-false-birth.json", impossible_child) != OK, "births cannot be forged before the birth simulation exists")
	var ghost_resident: Dictionary = resident_world.snapshot()
	ghost_resident.population.stations.unknown_site = {"id":"residents_unknown_site", "station_id":"unknown_site", "cohorts":{"children":0,"students":0,"available_workers":1,"assigned_workers":0,"retirees":0}, "hab_capacity":0, "housing_status":"No habitat"}
	_expect(save_store.save_game(test_root + "/resident-ghost-station.json", ghost_resident) != OK, "save validator rejects populated stations that never existed")
	var negative_cohort: Dictionary = resident_world.snapshot()
	negative_cohort.population.stations.hearth_exchange.cohorts.available_workers = -1
	_expect(save_store.save_game(test_root + "/resident-negative.json", negative_cohort) != OK, "negative resident cohorts cannot be saved")
	var duplicate_personnel: Dictionary = resident_world.snapshot()
	duplicate_personnel.crew_pools.hearth_exchange = 13
	_expect(save_store.save_game(test_root + "/resident-divergence.json", duplicate_personnel) != OK, "modded legacy recruitment pools cannot diverge from real counted people")
	var empty_legacy_roster: Dictionary = resident_world.snapshot()
	empty_legacy_roster.crew_pools.hearth_exchange = 0
	empty_legacy_roster.population.stations.hearth_exchange.cohorts.available_workers = 0
	_expect(save_store.save_game(test_root + "/resident-empty-roster.json", empty_legacy_roster) == OK, "a genuinely empty resident-worker pool is a legal save state")
	var future_population: Dictionary = resident_world.snapshot()
	future_population.population_version = 2
	var population_future_path := test_root + "/future-population-v2.json"
	_expect(save_store.save_game(population_future_path, resident_world.snapshot()) == OK and save_store.save_game(population_future_path, resident_world.snapshot()) == OK, "future resident format test retains a valid save backup")
	var future_population_payload := Marshalls.variant_to_base64(future_population, false)
	var future_population_file := FileAccess.open(population_future_path, FileAccess.WRITE)
	future_population_file.store_string(JSON.stringify({"format_version":1, "payload":future_population_payload, "checksum":future_population_payload.sha256_text()}))
	future_population_file.close()
	_expect(save_store.load_game(population_future_path).get("reason") == "unsupported", "a future population schema cannot silently fall back to an older saved game")

	# Construction never populates a station or grants phantom housing.
	var resident_plot = WorldScript.new()
	resident_plot.load_starter()
	_disable_npc_trading(resident_plot)
	var before_station_people: int = resident_plot.population.total_people(resident_plot)
	var resident_site: Dictionary = resident_plot.construction.place(resident_plot, "hearthreach", {"solar_cells":1}, "self", [])
	_expect(resident_site.ok and resident_plot.state.population.stations.has("player_station_1"), "placing a paid station immediately registers a resident cohort without needing to advance time")
	var construction_cohort: Dictionary = resident_plot.population.station_cohort(resident_plot, "player_station_1")
	_expect(resident_plot.population.station_total(construction_cohort) == 0 and construction_cohort.hab_capacity == 0 and resident_plot.population.total_people(resident_plot) == before_station_people, "new station construction gives housing capacity zero and invents no adults")
	_expect(save_store.save_game(test_root + "/resident-empty-player-station.json", resident_plot.snapshot()) == OK, "new empty player-station population saves before its first simulation tick")
	resident_plot.advance_ticks(90)
	_expect(resident_plot.population.station_total(construction_cohort) == 0 and resident_plot.population.total_people(resident_plot) == before_station_people, "waiting alone cannot spontaneously create residents at an unfurnished new station")

	# A paid NPC ship contract must obtain its human pilot and service crew
	# from the wharf's finite counted local adult residents at delivery.
	var new_ship_people = WorldScript.new()
	new_ship_people.load_starter()
	_disable_npc_trading(new_ship_people)
	var before_contract_people: int = new_ship_people.population.total_people(new_ship_people)
	var source_workers: int = new_ship_people.population.available_workers(new_ship_people, "vellum_foundry")
	var commissioned: Dictionary = new_ship_people.shipyard.place_order(new_ship_people, "freighter_mk1")
	_expect(commissioned.ok and new_ship_people.population.total_people(new_ship_people) == before_contract_people, "paying for ship construction creates neither a pilot nor crew prematurely")
	new_ship_people.advance_ticks(48)
	var staffed_freighter: Dictionary = new_ship_people._find_ship(str(commissioned.ship_id))
	_expect(not staffed_freighter.is_empty() and staffed_freighter.crew == 4 and new_ship_people.population.available_workers(new_ship_people, "vellum_foundry") == source_workers - 5, "finishing a freighter moves four real adults plus one pilot from the wharf into the new vessel")
	_expect(new_ship_people.population.total_people(new_ship_people) == before_contract_people and new_ship_people.state.crew_pools.vellum_foundry == source_workers - 5, "new ship contract conserves headcount and keeps the legacy available-worker mirror accurate")
	_expect(save_store.save_game(test_root + "/resident-staffed-freighter.json", new_ship_people.snapshot()) == OK, "ship acquired through finite wharf recruitment is a saveable player-owned asset")

	# If a wharf has no staff, a paid hull is kept blocked until suitable real
	# residents return to its recruitment pool; no free contractor is spawned.
	var shortages = WorldScript.new()
	shortages.load_starter()
	_disable_npc_trading(shortages)
	shortages.state.crew_pools.vellum_foundry = 1
	shortages.state.population.stations.vellum_foundry.cohorts.available_workers = 1
	var before_shortage_people: int = shortages.population.total_people(shortages)
	var waiting_hull: Dictionary = shortages.shipyard.place_order(shortages, "courier_mk1")
	shortages.advance_ticks(24)
	_expect(waiting_hull.ok and shortages.state.shipyard.orders[0].status == "blocked" and shortages._find_ship(str(waiting_hull.ship_id)).is_empty(), "a paid ship cannot manufacture an unfunded pilot and crew from an empty population")
	_expect(shortages.population.total_people(shortages) == before_shortage_people, "blocked ship assembly neither creates nor destroys people")
	_expect(shortages.queue_fly_to("ship_001", "vellum_gate"), "player can transport existing onboard workers to the constrained wharf")
	shortages.advance_ticks(20)
	_expect(shortages.dock_ship("ship_001", "vellum_foundry").ok, "existing workers can physically reach the shipbuilding station before being discharged")
	_expect(shortages.personnel.discharge(shortages, "ship_001", 2).ok and shortages.population.available_workers(shortages, "vellum_foundry") == 3, "returning two real ship workers replenishes an otherwise exhausted wharf population")
	shortages.advance_ticks(1)
	_expect(shortages.state.shipyard.orders[0].status == "complete" and not shortages._find_ship(str(waiting_hull.ship_id)).is_empty(), "previously blocked paid hull completes after legitimate workers become available")
	_expect(shortages.population.total_people(shortages) == before_shortage_people and shortages.population.available_workers(shortages, "vellum_foundry") == 0, "recruited pilot and crew are deducted from that wharf and population is conserved across the full cycle")
	_expect(save_store.save_game(test_root + "/resident-wharf-recovery.json", shortages.snapshot()) == OK, "blocked and restored ship staffing can be saved with exact headcounts")

	# Destruction/removal of a market may retain dormant counted residents
	# from old saves but must never be a usable source for new ship recruits.
	var disappeared = WorldScript.new()
	disappeared.load_starter()
	var disappeared_headcount: int = disappeared.population.total_people(disappeared)
	for station_index in range(disappeared.state.stations.size() - 1, -1, -1):
		if disappeared.state.stations[station_index].id == "hearth_exchange":
			disappeared.state.stations.remove_at(station_index)
	_expect(disappeared.population.station_cohort(disappeared, "hearth_exchange").cohorts.available_workers == 12 and disappeared.population.total_people(disappeared) == disappeared_headcount, "removed NPC station retains dormant residents without magically relocating them")
	_expect(save_store.save_game(test_root + "/resident-dormant.json", disappeared.snapshot()) == OK, "dormant population remains a valid save state until a later evacuation mechanic")
	_expect(disappeared.population.report(disappeared).any(func(row): return row.station_id == "hearth_exchange" and not row.active), "population reporting clearly identifies orphaned but conserved station residents")

	# A Pass-23 saved game has no population key; migration reads its existing
	# exact adult recruitment pool and never duplicates already hired crews.
	var old_population: Dictionary = resident_world.snapshot()
	_strip_habitation(old_population)
	old_population.erase("population_version")
	old_population.erase("population")
	var old_population_path := test_root + "/before-resident-ledger.json"
	_expect(save_store.save_game(old_population_path, old_population) == OK, "Pass-23 personnel game remains readable without the new population schema")
	var old_population_loaded: Dictionary = save_store.load_game(old_population_path)
	var migrated_population = WorldScript.new()
	_expect(bool(old_population_loaded.get("ok", false)) and migrated_population.restore_snapshot(old_population_loaded.state) == OK and migrated_population.state.population_version == 1, "Pass-23 save migrates to the resident-worker ledger without a fresh game")
	_expect(migrated_population.state.ships == old_population.ships and migrated_population.state.crew_pools == old_population.crew_pools and migrated_population.state.starting_credits == old_population.starting_credits and migrated_population.state.ledger == old_population.ledger, "migration leaves existing pilots, crews, salaries, assets, roles, orders and money unchanged")
	_expect(migrated_population.population.total_people(migrated_population) == known_before and migrated_population.population.available_workers(migrated_population, "hearth_exchange") == 11, "old hired workers are not counted again as additional residents on migration")
	_expect(save_store.save_game(test_root + "/migrated-population.json", migrated_population.snapshot()) == OK, "newly migrated population schema is permanently saveable")

	# Headless UI exposes real figures and states that habitat schooling and
	# population births are NOT implemented as playable systems yet.
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-population-ledger.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	screen.find_child("PopulationButton", true, false).pressed.emit()
	_expect(is_instance_valid(screen.population_screen) and screen.find_child("PopulationInfo", true, false) != null, "population overview is reachable from the player's property panel")
	_expect(screen.population_info.text.contains("Known total:") and screen.population_info.text.contains("hearth_exchange") == false and screen.population_info.text.contains("Hearth Exchange"), "population screen displays real counted residents by named station")
	_expect(screen.population_info.text.contains("Available resident workers: 12") and screen.population_info.text.contains("Births, immigration, schools"), "interface distinguishes available real workers from unimplemented residential life simulation")
	var ui_population_total: int = screen.world.population.total_people(screen.world)
	screen.find_child("ClosePopulationButton", true, false).pressed.emit()
	await process_frame
	screen.find_child("TradeButton", true, false).pressed.emit()
	for i in range(screen.trade_station_picker.item_count):
		if str(screen.trade_station_picker.get_item_metadata(i)) == "hearth_exchange":
			screen.trade_station_picker.select(i)
			break
	screen.find_child("DockButton", true, false).pressed.emit()
	screen.find_child("CloseTradeButton", true, false).pressed.emit()
	await process_frame
	screen.find_child("ManageCrewButton", true, false).pressed.emit()
	screen.crew_quantity.value = 1
	screen.find_child("HireCrewButton", true, false).pressed.emit()
	_expect(screen.world.population.available_workers(screen.world, "hearth_exchange") == 11 and screen.world.population.total_people(screen.world) == ui_population_total, "UI crew hire updates the very same station resident cohort without duplication")
	screen.find_child("CloseCrewButton", true, false).pressed.emit()
	await process_frame
	screen.find_child("PopulationButton", true, false).pressed.emit()
	_expect(screen.population_info.text.contains("Available resident workers: 11"), "population overview reflects the actual crew hire immediately")
	screen.find_child("ClosePopulationButton", true, false).pressed.emit()
	await process_frame
	_expect(bool(save_store.load_game(screen.save_path).get("ok", false)), "UI population and individual-ship crew states persist with the normal autosave")
	screen.queue_free()
	await process_frame

	# Pass 26: habitation is physical residential infrastructure rather than
	# an instantly generated population or a fake output-producing factory.
	var residential_world = WorldScript.new()
	_expect(residential_world.load_starter() == OK, "habitation-capable starter loads")
	_disable_npc_trading(residential_world)
	_expect(residential_world.state.habitation_version == 1 and residential_world.state.habitation_catalog.size() == 3, "three original residence module types are available in the actual build catalogue")
	var original_people: int = residential_world.population.total_people(residential_world)
	var original_player_money: int = int(residential_world.state.starting_credits)
	var original_all_money: int = _total_credits(residential_world.state)
	for housing_id in ["crew_habitat", "family_habitat", "adaptive_habitat"]:
		var housing_plan: Dictionary = residential_world.construction.quote(residential_world, "vellum_gate", {housing_id:1}, "all", [])
		var definition: Dictionary = residential_world.state.habitation_catalog[housing_id]
		var blueprint: Dictionary = residential_world.state.construction_blueprints[housing_id]
		var projected: Dictionary = residential_world.construction.planner.preview(residential_world.state, {housing_id:1}, "all", [], "vellum_gate")
		var housing_row: Dictionary = _plan_row(projected.modules, housing_id)
		_expect(housing_plan.ok and int(housing_plan.fee) == int(blueprint.fee) and int(housing_plan.ticks) == int(blueprint.ticks), "residential construction quote uses real blueprint fee and duration: " + housing_id)
		_expect(int(housing_row.housing_capacity) == int(definition.capacity) and int(housing_row.energy_per_60) == int(definition.energy_per_60), "station planner previews housing capacity and funded power needs: " + housing_id)
		_expect(housing_plan.materials.has("alloy_plates") and housing_plan.materials.has("energy_cells"), "all habitats require real construction alloys and energy: " + housing_id)
	var self_sufficient_housing: Dictionary = residential_world.construction.planner.preview(residential_world.state, {"crew_habitat":1}, "self", [], "hearthreach")
	var self_solar: Dictionary = _plan_row(self_sufficient_housing.modules, "solar_cells")
	_expect(self_sufficient_housing.ok and not self_solar.is_empty() and int(self_solar.added) >= 1, "self-sufficient habitat planning adds a real energy-production dependency rather than free life support")
	var imported_housing: Dictionary = residential_world.construction.planner.preview(residential_world.state, {"crew_habitat":1}, "selected", ["energy_cells"], "hearthreach")
	_expect(imported_housing.ok and _plan_row(imported_housing.modules, "solar_cells").is_empty() and imported_housing.warnings.any(func(message): return str(message).contains("not instant residents")), "selected import mode omits solar array and warns housing does not create people")
	_expect(not residential_world.construction.quote(residential_world, "vellum_gate", {"not_real_hab":1}, "all", []).ok, "unknown housing modules cannot be contracted")

	var residential_site: Dictionary = residential_world.construction.place(residential_world, "vellum_gate", {"crew_habitat":1}, "all", [])
	_expect(residential_site.ok and int(residential_world.state.starting_credits) == original_player_money - 500, "buying residential construction transfers real builder fees exactly once")
	var residential_plot: Dictionary = residential_world._find_station("player_station_1")
	var empty_household: Dictionary = residential_world.population.station_cohort(residential_world, "player_station_1")
	_expect(residential_plot.habitation.is_empty() and int(empty_household.hab_capacity) == 0 and residential_world.population.total_people(residential_world) == original_people, "placing construction does not instantly commission homes or create new people")
	_expect(residential_world.dock_ship("ship_001", "hearth_exchange").ok, "ship docks at real source of construction power")
	_expect(residential_world.trade("ship_001", "hearth_exchange", "energy_cells", 2, true).ok, "energy inputs are purchased from a real NPC station")
	_expect(residential_world.queue_fly_to("ship_001", "vellum_gate"), "physical cargo must travel to the housing build sector")
	residential_world.advance_ticks(15)
	_expect(residential_world.dock_ship("ship_001", "vellum_foundry").ok, "construction ship arrives at real NPC alloy vendor")
	_expect(residential_world.trade("ship_001", "vellum_foundry", "alloy_plates", 8, true).ok, "eight physical alloy plates are paid for and loaded")
	_expect(residential_world.dock_ship("ship_001", "player_station_1").ok and residential_world.construction.deliver(residential_world, "ship_001", str(residential_site.site_id)).ok, "player actually docks and delivers both materials into dedicated build storage")
	_expect(int(residential_world._find_ship("ship_001").cargo.get("alloy_plates", 0)) == 0 and int(residential_world._find_ship("ship_001").cargo.get("energy_cells", 0)) == 0, "all physical housing build materials leave ship cargo once")
	residential_world.advance_ticks(80)
	var built_housing_site: Dictionary = residential_world.construction.find_site(residential_world, str(residential_site.site_id))
	_expect(int(built_housing_site.completed) == 1 and residential_plot.habitation.size() == 1 and residential_plot.production.is_empty(), "residential module commissions after real builder work without being misrepresented as a producing factory")
	_expect(int(empty_household.hab_capacity) == 8 and residential_plot.habitation[0].id == "crew_habitat", "completed crew habitat adds exactly eight physical housing places")
	_expect(residential_world.population.station_total(empty_household) == 0 and residential_world.population.total_people(residential_world) == original_people, "housing capacity creates no automatic births, migrants, captains or recruitable adults")
	_expect(residential_plot.habitation[0].status == "Needs Energy Cells" and int(residential_world.habitation.operational_capacity(residential_plot, residential_world.state.habitation_catalog)) == 0, "unpowered housing exists physically but has zero operational life-support capacity")
	_expect(_total_credits(residential_world.state) == original_all_money, "real housing construction and materials trading conserve all credits across the existing economy")
	var built_hab_save := test_root + "/habitat-unpowered.json"
	_expect(save_store.save_game(built_hab_save, residential_world.snapshot()) == OK, "unpowered but completed habitat passes strict save and build-site validation")
	var built_hab_read: Dictionary = save_store.load_game(built_hab_save)
	var built_hab_restored = WorldScript.new()
	_expect(bool(built_hab_read.get("ok", false)) and built_hab_restored.restore_snapshot(built_hab_read.state) == OK and built_hab_restored.snapshot() == residential_world.snapshot(), "constructed housing and population status round-trip without recreating adults or materials")
	_expect(residential_world.queue_fly_to("ship_001", "hearthreach"), "player can return to real NPC energy supplier")
	residential_world.advance_ticks(15)
	_expect(residential_world.dock_ship("ship_001", "hearth_exchange").ok and residential_world.trade("ship_001", "hearth_exchange", "energy_cells", 4, true).ok, "ongoing habitat life-support energy has a physical paid source")
	_expect(residential_world.queue_fly_to("ship_001", "vellum_gate"), "life-support stocks travel through the same galaxy route system")
	residential_world.advance_ticks(15)
	_expect(residential_world.dock_ship("ship_001", "player_station_1").ok and residential_world.transfer_player_station("ship_001", "player_station_1", "energy_cells", 4, true).ok, "real energy stock is delivered to the owned habitat station")
	var before_life_support: int = int(residential_plot.stock.energy_cells)
	var until_service: int = 60 - int(residential_world.state.tick) % 60
	residential_world.advance_ticks(until_service)
	_expect(int(residential_plot.stock.energy_cells) == before_life_support - 1 and residential_plot.habitation[0].powered and residential_plot.habitation[0].status == "Powered", "housing consumes precisely one real Energy Cell on its scheduled life-support cycle")
	_expect(residential_world.habitation.operational_capacity(residential_plot, residential_world.state.habitation_catalog) == 8 and empty_household.housing_status == "Powered", "residence becomes operational only after a real funded power service")
	_expect(residential_world.population.total_people(residential_world) == original_people, "powered housing still does not fabricate workers, residents or children")
	residential_world.advance_ticks(240)
	_expect(residential_plot.stock.energy_cells == 0 and not residential_plot.habitation[0].powered and residential_plot.habitation[0].status == "Needs Energy Cells" and empty_household.housing_status == "Unpowered", "exhausted physical life-support inputs reduce operational housing to zero without negative stock")
	_expect(int(empty_household.hab_capacity) == 8 and residential_world.population.total_people(residential_world) == original_people, "energy shortage preserves constructed physical housing and existing people")
	_expect(save_store.save_game(test_root + "/habitat-after-power-shortage.json", residential_world.snapshot()) == OK, "life-support failures persist as valid station states")
	var forged_housing: Dictionary = residential_world.snapshot()
	forged_housing.population.stations.player_station_1.hab_capacity = 24
	_expect(save_store.save_game(test_root + "/habitat-fake-capacity.json", forged_housing) != OK, "save validation forbids creating housing slots without real built modules")
	var forged_power: Dictionary = residential_world.snapshot()
	forged_power.stations.back().habitation[0].powered = true
	_expect(save_store.save_game(test_root + "/habitat-fake-power.json", forged_power) != OK, "powered residential status must match actual housing service record")
	var fake_module: Dictionary = residential_world.snapshot()
	fake_module.stations.back().habitation.append({"id":"family_habitat","status":"Awaiting power","powered":false,"cycles":0})
	_expect(save_store.save_game(test_root + "/habitat-fake-module.json", fake_module) != OK, "habitat modules cannot be added without matching commissioned build tasks")
	var unborn_child: Dictionary = residential_world.snapshot()
	unborn_child.population.stations.player_station_1.cohorts.children = 1
	_expect(save_store.save_game(test_root + "/habitat-false-birth.json", unborn_child) != OK, "residential modules cannot be used to forge children before the birth lifecycle exists")
	var legacy_housing_world = WorldScript.new()
	legacy_housing_world.load_starter()
	_disable_npc_trading(legacy_housing_world)
	var legacy_housing: Dictionary = legacy_housing_world.snapshot()
	_strip_habitation(legacy_housing)
	_expect(save_store.save_game(test_root + "/before-housing.json", legacy_housing) == OK, "a pre-housing population save remains loadable")
	var legacy_housing_read: Dictionary = save_store.load_game(test_root + "/before-housing.json")
	var housing_migrated = WorldScript.new()
	_expect(bool(legacy_housing_read.get("ok", false)) and housing_migrated.restore_snapshot(legacy_housing_read.state) == OK and housing_migrated.state.habitation_version == 1, "legacy population state gains an empty residential catalogue without resetting the game")
	_expect(housing_migrated.state.starting_credits == legacy_housing.starting_credits and housing_migrated.state.ships == legacy_housing.ships and housing_migrated.state.population.stations.hearth_exchange.cohorts == legacy_housing.population.stations.hearth_exchange.cohorts, "habitation migration preserves people, captain skills, ship orders, crew and credits")
	var invalid_future_housing: Dictionary = residential_world.snapshot()
	invalid_future_housing.habitation_version = 2
	var future_housing_path := test_root + "/future-housing.json"
	_expect(save_store.save_game(future_housing_path, residential_world.snapshot()) == OK and save_store.save_game(future_housing_path, residential_world.snapshot()) == OK, "future housing version check prepares a valid backup")
	var future_housing_payload: String = Marshalls.variant_to_base64(invalid_future_housing, false)
	var future_housing_file := FileAccess.open(future_housing_path, FileAccess.WRITE)
	future_housing_file.store_string(JSON.stringify({"format_version":1, "payload":future_housing_payload, "checksum":future_housing_payload.sha256_text()}))
	future_housing_file.close()
	_expect(save_store.load_game(future_housing_path).get("reason") == "unsupported", "future habitat save versions cannot silently load a previous backup")

	# Android-oriented planner offers real residential controls, not mock UI.
	screen = MainScene.instantiate()
	screen.save_path = test_root + "/ui-habitation.json"
	root.add_child(screen)
	await process_frame
	screen.find_child("StartGameButton", true, false).pressed.emit()
	await process_frame
	await process_frame
	screen.find_child("PlanStationButton", true, false).pressed.emit()
	_expect(screen.plan_module_counts.has("crew_habitat") and screen.plan_module_counts.has("family_habitat") and screen.plan_module_counts.has("adaptive_habitat"), "touch station planner exposes all three actual residential construction choices")
	screen.plan_module_counts.crew_habitat.value = 1
	screen._update_station_plan()
	_expect(screen.plan_result.text.contains("housing places") and screen.plan_result.text.contains("Energy Cells") and screen.plan_build_button.disabled == false, "housing planner displays funded builder cost, real life-support supply and no automatic population")
	screen.find_child("ClosePlannerButton", true, false).pressed.emit()
	await process_frame
	screen.find_child("PopulationButton", true, false).pressed.emit()
	_expect(screen.population_info.text.contains("Housing: 0 slots") and screen.population_info.text.contains("Births, immigration"), "population UI distinguishes empty completed housing from unimplemented immigration and births")
	screen.find_child("ClosePopulationButton", true, false).pressed.emit()
	await process_frame
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
