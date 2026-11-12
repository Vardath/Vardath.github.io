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
	return total


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
	_expect(first.state.ships.size() == 1, "player starts with one ship")
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
		_expect(ship.owner == first.state.player_faction_id, "starter ship belongs to player")
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
	_expect(economy.state.stations.size() == 4 and economy.state.wares.size() == 2, "starter economy has four stations and two wares")
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
	for key in ["economy_version", "wares", "stations", "ledger", "next_transaction_id"]:
		old_save.erase(key)
	for ship in old_save.ships:
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
	screen.find_child("TradeButton", true, false).pressed.emit()
	_expect(screen.find_child("TradeScreen", true, false) != null, "trade screen opens")
	screen.find_child("DockButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].docked_at == "hearth_exchange", "trade screen docks at the local station")
	screen.trade_quantity.value = 5
	screen.find_child("BuyButton", true, false).pressed.emit()
	_expect(screen.world.state.ships[0].cargo.energy_cells == 5 and screen.world.state.ledger.size() == 1, "trade screen purchases stock and records it")
	_expect(save_store.load_game(screen.save_path).state.ships[0].cargo.energy_cells == 5, "successful trade is saved immediately")
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
	_expect(screen.detail_body.text.contains("Energy Cells: 5"), "ship details display carried cargo")
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
