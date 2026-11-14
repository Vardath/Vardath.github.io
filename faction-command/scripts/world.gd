extends RefCounted
## Small, presentation-independent world state. Time advances only through
## explicit whole ticks; no wall clock or frame rate enters the simulation.

const STARTER_DATA := "res://data/starter_galaxy.json"
const TICKS_PER_CROSSING := 5
const NPCTradeScript = preload("res://scripts/npc_trade.gd")
const ConstructionScript = preload("res://scripts/construction.gd")
const BuildSupplyScript = preload("res://scripts/build_supply.gd")
const ArchivesScript = preload("res://scripts/archives.gd")
const ResearchScript = preload("res://scripts/research.gd")
const StationSupplyScript = preload("res://scripts/station_supply.gd")
const ShipyardScript = preload("res://scripts/shipyard.gd")
const PersonnelScript = preload("res://scripts/personnel.gd")
const PopulationScript = preload("res://scripts/population.gd")
const HabitationScript = preload("res://scripts/habitation.gd")

var state: Dictionary = {}
var npc_trade = NPCTradeScript.new()
var construction = ConstructionScript.new()
var build_supply = BuildSupplyScript.new()
var archives = ArchivesScript.new()
var research = ResearchScript.new()
var station_supply = StationSupplyScript.new()
var shipyard = ShipyardScript.new()
var personnel = PersonnelScript.new()
var population = PopulationScript.new()
var habitation = HabitationScript.new()


func load_starter(origin_faction_id: String = "auroran") -> Error:
	if not FileAccess.file_exists(STARTER_DATA):
		return ERR_FILE_NOT_FOUND
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(STARTER_DATA))
	if not parsed is Dictionary or parsed.get("schema_version", 0) != 1:
		return ERR_PARSE_ERROR
	var chosen: Dictionary = {}
	for profile in parsed.get("starting_profiles", []):
		if profile.get("faction_id", "") == origin_faction_id:
			chosen = profile
			break
	if chosen.is_empty():
		return ERR_INVALID_PARAMETER
	var new_state: Dictionary = parsed.duplicate(true)
	new_state["tick"] = 0
	new_state["player_origin_faction_id"] = origin_faction_id
	new_state["relations"] = chosen.relations.duplicate(true)
	for ship in new_state.get("ships", []):
		if ship.owner == new_state.player_faction_id:
			ship.sector = chosen.sector_id
		ship["orders"] = []
		ship["travel"] = {}
	if _prepare_economy(new_state) != OK:
		return ERR_INVALID_DATA
	if _prepare_production(new_state) != OK:
		return ERR_INVALID_DATA
	if _prepare_logistics(new_state) != OK:
		return ERR_INVALID_DATA
	if _prepare_player_roles(new_state) != OK:
		return ERR_INVALID_DATA
	if construction.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if build_supply.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if archives.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if research.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if station_supply.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if shipyard.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if personnel.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if population.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	if habitation.prepare(new_state) != OK:
		return ERR_INVALID_DATA
	state = new_state
	return OK


func restore_snapshot(snapshot: Dictionary) -> Error:
	var restored := snapshot.duplicate(true)
	var result := _prepare_economy(restored)
	if result != OK:
		return result
	result = _prepare_production(restored)
	if result != OK:
		return result
	result = _prepare_logistics(restored)
	if result != OK:
		return result
	result = _prepare_player_roles(restored)
	if result != OK:
		return result
	result = construction.prepare(restored)
	if result != OK:
		return result
	result = build_supply.prepare(restored)
	if result != OK:
		return result
	result = archives.prepare(restored)
	if result != OK:
		return result
	result = research.prepare(restored)
	if result != OK:
		return result
	result = station_supply.prepare(restored)
	if result != OK:
		return result
	result = shipyard.prepare(restored)
	if result != OK:
		return result
	result = personnel.prepare(restored)
	if result != OK:
		return result
	result = population.prepare(restored)
	if result != OK:
		return result
	result = habitation.prepare(restored)
	if result != OK:
		return result
	state = restored
	return OK


func _prepare_economy(target: Dictionary) -> Error:
	if target.has("economy_version"):
		return OK if target.economy_version == 1 else ERR_UNAVAILABLE
	# Older saves predate the economy. Add the initial NPC economy and empty
	# player cargo without resetting the saved world, ship, orders or relations.
	var defaults: Variant = JSON.parse_string(FileAccess.get_file_as_string(STARTER_DATA))
	if not defaults is Dictionary or not defaults.get("wares") is Array or not defaults.get("stations") is Array:
		return ERR_INVALID_DATA
	target["wares"] = defaults.wares.duplicate(true)
	target["stations"] = defaults.stations.duplicate(true)
	target["economy_version"] = 1
	target["ledger"] = []
	target["next_transaction_id"] = 1
	for ship in target.get("ships", []):
		ship["cargo_capacity"] = 50
		ship["cargo"] = {}
		ship["docked_at"] = ""
	return OK


func _prepare_production(target: Dictionary) -> Error:
	if target.has("production_version"):
		return OK if target.production_version == 1 else ERR_UNAVAILABLE
	var defaults: Variant = JSON.parse_string(FileAccess.get_file_as_string(STARTER_DATA))
	if not defaults is Dictionary or not defaults.get("recipes") is Array or not defaults.get("wares") is Array or not defaults.get("stations") is Array:
		return ERR_INVALID_DATA
	# Preserve all old balances, inventories, orders and ships. New resource and
	# module definitions are added without replenishing an existing station.
	var newly_added_wares: Dictionary = {}
	for default_ware in defaults.wares:
		var found := false
		for ware in target.wares:
			if ware.id == default_ware.id:
				found = true
				break
		if not found:
			target.wares.append(default_ware.duplicate(true))
			newly_added_wares[default_ware.id] = true
	target["recipes"] = defaults.recipes.duplicate(true)
	for station in target.stations:
		var template: Dictionary = {}
		for candidate in defaults.stations:
			if candidate.id == station.id:
				template = candidate
				break
		station["natural_sources"] = template.get("natural_sources", []).duplicate(true)
		station["deposits"] = template.get("deposits", {}).duplicate(true)
		station["production"] = template.get("production", []).duplicate(true)
		for ware in target.wares:
			if not station.stock.has(ware.id):
				station.stock[ware.id] = 0
		for price_type in ["buy_prices", "sell_prices"]:
			for ware_id in template.get(price_type, {}):
				if newly_added_wares.has(ware_id) and not station[price_type].has(ware_id):
					station[price_type][ware_id] = template[price_type][ware_id]
	target["production_version"] = 1
	return OK


func _prepare_logistics(target: Dictionary) -> Error:
	if target.has("logistics_version"):
		return OK if target.logistics_version == 1 else ERR_UNAVAILABLE
	for ship in target.ships:
		if ship.id == "npc_logistics_001":
			return ERR_ALREADY_IN_USE
	var home: Dictionary = {}
	for station in target.stations:
		if station.id == "verdant_hub" and station.owner != target.player_faction_id:
			home = station
			break
	if home.is_empty():
		for station in target.stations:
			if station.owner != target.player_faction_id:
				home = station
				break
	if home.is_empty():
		target["logistics_version"] = 1
		return OK
	# The freighter starts with no money. Its home station transfers working
	# capital on the first simulation tick; migration creates no credits.
	target.ships.append({"id":"npc_logistics_001", "name":"Wayfarer", "class":"Freighter", "owner":home.owner, "sector":home.sector, "captain":"Talin Rho", "crew":3, "role":"Autonomous Trader", "status":"Idle", "orders":[], "travel":{}, "cargo_capacity":50, "cargo":{}, "docked_at":"", "credits":0, "autotrader":{"enabled":true, "phase":"idle", "home_station_id":home.id, "source_id":"", "destination_id":"", "ware_id":"", "quantity":0, "retry_ticks":0, "funded":false}})
	target["logistics_version"] = 1
	return OK


func _prepare_player_roles(target: Dictionary) -> Error:
	if target.has("player_roles_version"):
		return OK if target.player_roles_version == 1 else ERR_UNAVAILABLE
	# Add an inactive role to old player ships without touching their orders,
	# cargo, crew, balances or existing NPC traders.
	for ship in target.ships:
		if ship.owner == target.player_faction_id:
			ship["player_trader"] = {"enabled":false, "phase":"idle", "source_id":"", "destination_id":"", "ware_id":"", "quantity":0, "managed_quantity":0, "retry_ticks":0}
	target["player_roles_version"] = 1
	return OK


func advance_ticks(count: int) -> void:
	if count <= 0 or state.is_empty():
		return
	for _step in range(count):
		state["tick"] = int(state["tick"]) + 1
		for ship in state.get("ships", []):
			_tick_ship(ship)
		for station in state.get("stations", []):
			_tick_production(station)
		for ship in state.get("ships", []):
			if ship.has("autotrader") or ship.has("player_trader"):
				npc_trade.tick(self, ship)
			if ship.has("build_supply"):
				build_supply.tick(self, ship)
			if ship.has("station_supply"):
				station_supply.tick(self, ship)
		construction.tick(self)
		habitation.tick(self)
		archives.tick(self)
		research.tick(self)
		shipyard.tick(self)
		personnel.tick(self)
		population.tick(self)


func snapshot() -> Dictionary:
	return state.duplicate(true)


func queue_fly_to(ship_id: String, destination: String) -> bool:
	var ship := _find_ship(ship_id)
	if ship.is_empty() or ship.owner != state.get("player_faction_id", ""):
		return false
	return _queue_ship_route(ship, destination)


func set_player_trader(ship_id: String, enabled: bool) -> bool:
	var ship := _find_ship(ship_id)
	if ship.is_empty() or ship.owner != state.get("player_faction_id", "") or not ship.has("player_trader"):
		return false
	build_supply.stop(ship)
	station_supply.stop(ship)
	ship.player_trader.enabled = enabled
	ship.role = "Autonomous Trader" if enabled else "Unassigned"
	return true


func _queue_ship_route(ship: Dictionary, destination: String) -> bool:
	var origin: String = str(ship.sector)
	if not ship.orders.is_empty():
		origin = str(ship.orders.back().destination)
	if origin == destination or _find_route(origin, destination).is_empty():
		return false
	ship.orders.append({"type": "fly_to", "destination": destination})
	ship.docked_at = ""
	if ship.travel.is_empty():
		ship.status = "Queued"
	return true


func _find_ship(ship_id: String) -> Dictionary:
	for ship in state.get("ships", []):
		if ship.id == ship_id:
			return ship
	return {}


func _find_station(station_id: String) -> Dictionary:
	for station in state.get("stations", []):
		if station.id == station_id:
			return station
	return {}


func _find_ware(ware_id: String) -> Dictionary:
	for ware in state.get("wares", []):
		if ware.id == ware_id:
			return ware
	return {}


func _find_recipe(recipe_id: String) -> Dictionary:
	for recipe in state.get("recipes", []):
		if recipe.id == recipe_id:
			return recipe
	return {}


func _station_deposits(station: Dictionary) -> Dictionary:
	var sector_id := str(station.get("resource_sector", ""))
	if not sector_id.is_empty():
		return state.get("construction_resources", {}).get(sector_id, {}).get("deposits", {})
	return station.deposits


func _station_reservations(station: Dictionary) -> Dictionary:
	var reserved: Dictionary = {}
	for module in station.production:
		var recipe := _find_recipe(str(module.recipe_id))
		if recipe.is_empty():
			continue
		for ware_id in recipe.get("catalysts", {}):
			if bool(recipe.get("catalog_source", false)) and station.has("archive") and ware_id == "recorded_data":
				continue
			reserved[ware_id] = maxi(int(reserved.get(ware_id, 0)), int(recipe.catalysts[ware_id]))
	return reserved


func _production_block_reason(station: Dictionary, recipe: Dictionary, reservations: Variant = null) -> String:
	var reserved: Dictionary = _station_reservations(station) if reservations == null else reservations
	if bool(recipe.get("catalog_source", false)) and station.has("archive") and station.archive.status != "Operational":
		return "Archive needs upkeep"
	for ware_id in recipe.inputs:
		if int(station.stock.get(ware_id, 0)) < int(recipe.inputs[ware_id]):
			var ware := _find_ware(str(ware_id))
			return "Needs " + str(ware.get("name", ware_id))
		if int(station.stock.get(ware_id, 0)) - int(recipe.inputs[ware_id]) < int(reserved.get(ware_id, 0)):
			var ware := _find_ware(str(ware_id))
			return "Keep " + str(ware.get("name", ware_id)) + " source"
	for ware_id in recipe.get("catalysts", {}):
		if bool(recipe.get("catalog_source", false)) and station.has("archive") and ware_id == "recorded_data":
			continue
		if int(station.stock.get(ware_id, 0)) < int(recipe.catalysts[ware_id]):
			var ware := _find_ware(str(ware_id))
			return "Needs " + str(ware.get("name", ware_id)) + " source"
	var source := str(recipe.get("source", ""))
	if not source.is_empty() and source not in station.natural_sources:
		return "Needs " + source
	var deposit: Dictionary = recipe.get("deposit", {})
	if not deposit.is_empty() and int(_station_deposits(station).get(deposit.resource, 0)) < int(deposit.quantity):
		return "Deposit exhausted"
	var projected := station_volume(str(station.id))
	for ware_id in recipe.inputs:
		projected -= int(recipe.inputs[ware_id]) * int(_find_ware(str(ware_id)).volume)
	for ware_id in recipe.outputs:
		projected += int(recipe.outputs[ware_id]) * int(_find_ware(str(ware_id)).volume)
	if projected > int(station.storage_capacity):
		return "Storage full"
	return ""


func _tick_production(station: Dictionary) -> void:
	var reservations := _station_reservations(station)
	for module in station.production:
		var recipe := _find_recipe(str(module.recipe_id))
		if recipe.is_empty():
			module.status = "Invalid recipe"
			continue
		recipe = research.adjusted_recipe(state, recipe, station.owner == state.player_faction_id)
		var blocked := _production_block_reason(station, recipe, reservations)
		if not blocked.is_empty():
			module.status = blocked
			continue
		module.status = "Running"
		module.progress = int(module.progress) + 1
		if int(module.progress) < int(recipe.cycle_ticks):
			continue
		# Input removal, output addition and resource depletion occur together.
		for ware_id in recipe.inputs:
			station.stock[ware_id] = int(station.stock.get(ware_id, 0)) - int(recipe.inputs[ware_id])
		for ware_id in recipe.outputs:
			station.stock[ware_id] = int(station.stock.get(ware_id, 0)) + int(recipe.outputs[ware_id])
		var deposit: Dictionary = recipe.get("deposit", {})
		if not deposit.is_empty():
			var deposits := _station_deposits(station)
			deposits[deposit.resource] = int(deposits[deposit.resource]) - int(deposit.quantity)
		module.progress = 0
		module.cycles = int(module.cycles) + 1
		blocked = _production_block_reason(station, recipe, reservations)
		if not blocked.is_empty():
			module.status = blocked


func production_report(station_id: String) -> Array:
	var station := _find_station(station_id)
	var reports: Array = []
	if station.is_empty():
		return reports
	var reservations := _station_reservations(station)
	for module in station.production:
		var recipe := _find_recipe(str(module.recipe_id))
		if recipe.is_empty():
			continue
		recipe = research.adjusted_recipe(state, recipe, station.owner == state.player_faction_id)
		var reason := _production_block_reason(station, recipe, reservations)
		reports.append({"name": recipe.name, "status": "Running" if reason.is_empty() else reason, "progress": int(module.progress), "duration": int(recipe.cycle_ticks), "cycles": int(module.cycles), "inputs": recipe.inputs.duplicate(true), "outputs": recipe.outputs.duplicate(true), "catalysts":recipe.get("catalysts", {}).duplicate(true), "catalog_source":bool(recipe.get("catalog_source", false)), "source": str(recipe.get("source", "")), "deposit": recipe.get("deposit", {}).duplicate(true)})
	return reports


func cargo_volume(ship_id: String) -> int:
	var ship := _find_ship(ship_id)
	if ship.is_empty():
		return 0
	var used := 0
	for ware_id in ship.cargo:
		var ware := _find_ware(str(ware_id))
		if not ware.is_empty():
			used += int(ship.cargo[ware_id]) * int(ware.volume)
	return used


func station_volume(station_id: String) -> int:
	var station := _find_station(station_id)
	if station.is_empty():
		return 0
	var used := 0
	for ware_id in station.stock:
		var ware := _find_ware(str(ware_id))
		if not ware.is_empty():
			used += int(station.stock[ware_id]) * int(ware.volume)
	return used


func dock_ship(ship_id: String, station_id: String) -> Dictionary:
	var ship := _find_ship(ship_id)
	var station := _find_station(station_id)
	if ship.is_empty() or station.is_empty() or ship.owner != state.player_faction_id:
		return {"ok": false, "message": "Ship or station is unavailable."}
	if not ship.orders.is_empty() or not ship.travel.is_empty():
		return {"ok": false, "message": "Wait until the ship finishes its orders."}
	if ship.sector != station.sector:
		return {"ok": false, "message": "The ship must travel to the station's sector first."}
	ship.docked_at = station.id
	ship.status = "Docked"
	return {"ok": true, "message": "Docked at " + str(station.name) + "."}


func transfer_player_station(ship_id: String, station_id: String, ware_id: String, quantity: int, to_station: bool) -> Dictionary:
	var ship := _find_ship(ship_id)
	var station := _find_station(station_id)
	var ware := _find_ware(ware_id)
	if ship.is_empty() or station.is_empty() or ware.is_empty() or ship.owner != state.player_faction_id or station.owner != state.player_faction_id:
		return {"ok":false, "message":"Your ship and station are required."}
	if quantity <= 0 or quantity > 1000000000:
		return {"ok":false, "message":"Choose a positive quantity."}
	if ship.sector != station.sector or ship.docked_at != station_id or not ship.orders.is_empty() or not ship.travel.is_empty():
		return {"ok":false, "message":"Dock the ship at your station first."}
	var cargo := int(ship.cargo.get(ware_id, 0))
	var stock := int(station.stock.get(ware_id, 0))
	if to_station:
		if cargo < quantity or station_volume(station_id) + quantity * int(ware.volume) > int(station.storage_capacity):
			return {"ok":false, "message":"Not enough cargo or station storage."}
		ship.cargo[ware_id] = cargo - quantity
		station.stock[ware_id] = stock + quantity
		if ship.has("player_trader") and ship.player_trader.phase == "to_destination" and ship.player_trader.ware_id == ware_id:
			ship.player_trader.managed_quantity = maxi(0, int(ship.player_trader.managed_quantity) - quantity)
	else:
		if stock < quantity or cargo_volume(ship_id) + quantity * int(ware.volume) > int(ship.cargo_capacity):
			return {"ok":false, "message":"Not enough station stock or ship cargo space."}
		station.stock[ware_id] = stock - quantity
		ship.cargo[ware_id] = cargo + quantity
	_record_transaction("transfer_in" if to_station else "transfer_out", ship_id, station_id, ware_id, quantity, 0, 0)
	return {"ok":true, "message":"Transferred %d %s." % [quantity, ware.name]}


func trade(ship_id: String, station_id: String, ware_id: String, quantity: int, buy: bool) -> Dictionary:
	var ship := _find_ship(ship_id)
	if ship.is_empty() or ship.owner != state.player_faction_id:
		return {"ok": false, "message": "Ship is unavailable."}
	var result := _trade_for_ship(ship, station_id, ware_id, quantity, buy)
	# A manual sale consumes role-managed goods first, so resuming the role
	# cannot later sell the player's unrelated pre-existing cargo by mistake.
	if result.ok and not buy and ship.has("player_trader"):
		var job: Dictionary = ship.player_trader
		if job.phase == "to_destination" and job.ware_id == ware_id:
			job.managed_quantity = maxi(0, int(job.managed_quantity) - quantity)
	return result


func _trade_for_ship(ship: Dictionary, station_id: String, ware_id: String, quantity: int, buy: bool) -> Dictionary:
	var station := _find_station(station_id)
	var ware := _find_ware(ware_id)
	if ship.is_empty() or station.is_empty() or ware.is_empty():
		return {"ok": false, "message": "Ship, station or ware is unavailable."}
	if quantity <= 0 or quantity > 1000000000:
		return {"ok": false, "message": "Choose a positive quantity."}
	if ship.sector != station.sector or ship.docked_at != station_id or not ship.travel.is_empty() or not ship.orders.is_empty():
		return {"ok": false, "message": "The ship must be docked at this station."}
	var prices: Dictionary = station.sell_prices if buy else station.buy_prices
	if not prices.has(ware_id):
		return {"ok": false, "message": "This station does not offer that trade."}
	var price := int(prices[ware_id])
	if price <= 0 or price > 1000000000:
		return {"ok": false, "message": "This station has an invalid price."}
	var total := price * quantity
	var stock := int(station.stock.get(ware_id, 0))
	var cargo := int(ship.cargo.get(ware_id, 0))
	if buy:
		if stock < quantity:
			return {"ok": false, "message": "The station does not have enough stock."}
		if cargo_volume(str(ship.id)) + quantity * int(ware.volume) > int(ship.cargo_capacity):
			return {"ok": false, "message": "The ship does not have enough cargo space."}
		var available_credits := int(state.starting_credits) if ship.owner == state.player_faction_id else int(ship.get("credits", 0))
		if available_credits < total:
			return {"ok": false, "message": "Your faction does not have enough credits."}
		if ship.owner == state.player_faction_id:
			state.starting_credits = available_credits - total
		else:
			ship.credits = available_credits - total
		station.credits = int(station.credits) + total
		station.stock[ware_id] = stock - quantity
		ship.cargo[ware_id] = cargo + quantity
	else:
		if cargo < quantity:
			return {"ok": false, "message": "The ship does not carry enough of this ware."}
		if int(station.credits) < total:
			return {"ok": false, "message": "The station does not have enough credits."}
		if station_volume(station_id) + quantity * int(ware.volume) > int(station.storage_capacity):
			return {"ok": false, "message": "The station does not have enough storage space."}
		if ship.owner == state.player_faction_id:
			state.starting_credits = int(state.starting_credits) + total
		else:
			ship.credits = int(ship.get("credits", 0)) + total
		station.credits = int(station.credits) - total
		station.stock[ware_id] = stock + quantity
		ship.cargo[ware_id] = cargo - quantity
	_record_transaction("buy" if buy else "sell", str(ship.id), station_id, ware_id, quantity, price, -total if buy else total)
	return {"ok": true, "message": "%s %d %s for %d credits." % ["Bought" if buy else "Sold", quantity, ware.name, total]}


func _record_transaction(kind: String, ship_id: String, station_id: String, ware_id: String, quantity: int, price: int, amount: int) -> void:
	state.ledger.append({"id": int(state.next_transaction_id), "tick": int(state.tick), "kind": kind, "ship_id": ship_id, "station_id": station_id, "ware_id": ware_id, "quantity": quantity, "price": price, "amount": amount})
	state.next_transaction_id = int(state.next_transaction_id) + 1
	personnel.record_activity(self, ship_id, kind)


func _find_route(origin: String, destination: String) -> Array:
	var neighbors: Dictionary = {}
	for sector in state.get("sectors", []):
		neighbors[sector.id] = []
	if not neighbors.has(origin) or not neighbors.has(destination):
		return []
	# The data's fixed link order is the tie breaker between equal routes.
	for link in state.get("links", []):
		if link.size() == 2 and neighbors.has(link[0]) and neighbors.has(link[1]):
			neighbors[link[0]].append(link[1])
			neighbors[link[1]].append(link[0])
	var previous: Dictionary = {origin: ""}
	var waiting: Array = [origin]
	while not waiting.is_empty() and not previous.has(destination):
		var current: String = waiting.pop_front()
		for neighbor in neighbors[current]:
			if not previous.has(neighbor):
				previous[neighbor] = current
				waiting.append(neighbor)
	if not previous.has(destination):
		return []
	var route: Array = []
	var current: String = destination
	while not current.is_empty():
		route.push_front(current)
		current = str(previous[current])
	return route


func _tick_ship(ship: Dictionary) -> void:
	if ship.orders.is_empty():
		ship.status = "Docked" if not str(ship.docked_at).is_empty() else "Idle"
		return
	if ship.travel.is_empty():
		var route := _find_route(str(ship.sector), str(ship.orders[0].destination))
		if route.size() < 2:
			ship.status = "Blocked"
			return
		ship.travel = {"from": route[0], "to": route[1], "total": TICKS_PER_CROSSING, "remaining": TICKS_PER_CROSSING}
	ship.status = "Travelling"
	ship.travel.remaining = int(ship.travel.remaining) - 1
	if int(ship.travel.remaining) <= 0:
		ship.sector = ship.travel.to
		ship.travel = {}
		personnel.record_activity(self, str(ship.id), "sector_crossing")
		if ship.sector == ship.orders[0].destination:
			ship.orders.pop_front()
		if ship.orders.is_empty():
			ship.status = "Idle"
