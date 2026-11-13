extends RefCounted
## A player ship keeps a station's net production inputs stocked. Goods move
## physically; external purchases are limited by a player-set allowance.

const BUFFER_TICKS := 30
const RETRY_TICKS := 5
const EPSILON := 0.000001


func prepare(target: Dictionary) -> Error:
	if target.has("station_supply_version"):
		return OK if target.station_supply_version == 1 else ERR_UNAVAILABLE
	for ship in target.ships:
		if ship.owner == target.player_faction_id:
			ship["station_supply"] = _empty_job()
	target["station_supply_version"] = 1
	return OK


func _empty_job() -> Dictionary:
	return {"enabled":false, "station_id":"", "phase":"idle", "source_id":"", "ware_id":"", "retry_ticks":0, "wait_reason":"", "budget_limit":0, "spent":0}


func targets(world: RefCounted, station: Dictionary) -> Dictionary:
	var demand: Dictionary = {}
	var production: Dictionary = {}
	var catalysts: Dictionary = {}
	for module in station.get("production", []):
		var base: Dictionary = world._find_recipe(str(module.recipe_id))
		if base.is_empty():
			continue
		var recipe: Dictionary = world.research.adjusted_recipe(world.state, base, station.owner == world.state.player_faction_id)
		var source := str(recipe.get("source", ""))
		var deposit: Dictionary = recipe.get("deposit", {})
		if (not source.is_empty() and source not in station.natural_sources) or (not deposit.is_empty() and int(world._station_deposits(station).get(deposit.resource, 0)) < int(deposit.quantity)):
			continue
		var duration := float(recipe.cycle_ticks)
		for ware_id in recipe.inputs:
			demand[ware_id] = float(demand.get(ware_id, 0.0)) + float(recipe.inputs[ware_id]) / duration
		for ware_id in recipe.outputs:
			production[ware_id] = float(production.get(ware_id, 0.0)) + float(recipe.outputs[ware_id]) / duration
		for ware_id in recipe.get("catalysts", {}):
			if bool(recipe.get("catalog_source", false)) and station.has("archive") and ware_id == "recorded_data":
				continue
			catalysts[ware_id] = maxi(int(catalysts.get(ware_id, 0)), int(recipe.catalysts[ware_id]))
	var needed_ids: Array = demand.keys()
	for ware_id in catalysts:
		if ware_id not in needed_ids:
			needed_ids.append(ware_id)
	needed_ids.sort()
	var desired: Dictionary = {}
	for ware_id in needed_ids:
		var net := maxf(0.0, float(demand.get(ware_id, 0.0)) - float(production.get(ware_id, 0.0)))
		var quantity := int(ceil(net * BUFFER_TICKS - EPSILON)) + int(catalysts.get(ware_id, 0))
		if quantity > 0:
			desired[ware_id] = quantity
	if desired.is_empty():
		return desired
	# Reserve at least half the station capacity for output and other stock.
	var fair_volume := maxi(1, int(int(station.storage_capacity) / 2 / desired.size()))
	for ware_id in desired:
		var ware: Dictionary = world._find_ware(str(ware_id))
		if ware.is_empty() or int(ware.volume) > int(station.storage_capacity):
			desired[ware_id] = 0
		else:
			var fair_units := maxi(1, int(fair_volume / int(ware.volume)))
			desired[ware_id] = mini(int(desired[ware_id]), fair_units)
	return desired


func protected_stock(world: RefCounted, station: Dictionary, ware_id: String) -> int:
	var needed := targets(world, station)
	var catalysts: Dictionary = world._station_reservations(station)
	var working_inputs := 0
	for module in station.get("production", []):
		var recipe: Dictionary = world._find_recipe(str(module.recipe_id))
		if not recipe.is_empty():
			working_inputs += int(recipe.inputs.get(ware_id, 0)) * 2
	return maxi(int(needed.get(ware_id, 0)), working_inputs + int(catalysts.get(ware_id, 0)))


func has_inputs(world: RefCounted, station: Dictionary) -> bool:
	for module in station.get("production", []):
		var recipe: Dictionary = world._find_recipe(str(module.recipe_id))
		if not recipe.is_empty() and (not recipe.inputs.is_empty() or not recipe.get("catalysts", {}).is_empty()):
			return true
	return false


func assign(world: RefCounted, ship_id: String, station_id: String, budget_limit: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = world._find_station(station_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id or not ship.has("station_supply") or station.is_empty() or station.owner != world.state.player_faction_id:
		return {"ok":false, "message":"Choose your ship and one of your stations."}
	if budget_limit < 0 or budget_limit > 1000000000:
		return {"ok":false, "message":"Choose a valid purchase allowance."}
	if not has_inputs(world, station):
		return {"ok":false, "message":"This station has no production inputs to supply."}
	if ship.station_supply.enabled and ship.station_supply.station_id == station_id:
		if budget_limit < int(ship.station_supply.spent):
			return {"ok":false, "message":"The limit cannot be lower than the amount already spent."}
		ship.station_supply.budget_limit = budget_limit
		ship.station_supply.retry_ticks = 0
		return {"ok":true, "message":"Purchase limit updated. Existing cargo and orders are retained."}
	ship.player_trader.enabled = false
	world.build_supply.stop(ship)
	ship.station_supply = _empty_job()
	ship.station_supply.enabled = true
	ship.station_supply.station_id = station_id
	ship.station_supply.budget_limit = budget_limit
	ship.role = "Station Supplier"
	return {"ok":true, "message":"Station supply assigned. Queued orders finish first."}


func stop(ship: Dictionary) -> void:
	if not ship.has("station_supply"):
		return
	ship.station_supply = _empty_job()
	if ship.get("role", "") == "Station Supplier":
		ship.role = "Unassigned"


func _reset_trip(job: Dictionary) -> void:
	job.phase = "idle"
	job.source_id = ""
	job.ware_id = ""
	job.retry_ticks = 0
	job.wait_reason = ""


func _wait(job: Dictionary, ship: Dictionary, reason: String) -> void:
	job.retry_ticks = RETRY_TICKS
	job.wait_reason = reason
	ship.status = reason


func _go(world: RefCounted, ship: Dictionary, sector_id: String) -> bool:
	return ship.sector == sector_id or world._queue_ship_route(ship, sector_id)


func _other_inbound(world: RefCounted, ship: Dictionary, station_id: String, ware_id: String) -> int:
	var total := 0
	for other in world.state.ships:
		if other.id == ship.id or not other.has("station_supply"):
			continue
		var job: Dictionary = other.station_supply
		if job.enabled and job.station_id == station_id and job.phase == "to_station" and job.ware_id == ware_id:
			total += int(other.cargo.get(ware_id, 0))
	return total


func _incoming_volume(world: RefCounted, ship: Dictionary, station_id: String) -> int:
	var total := 0
	for other in world.state.ships:
		if other.id == ship.id or not other.has("station_supply"):
			continue
		var job: Dictionary = other.station_supply
		if not job.enabled or job.station_id != station_id or job.phase != "to_station":
			continue
		var ware: Dictionary = world._find_ware(str(job.ware_id))
		if not ware.is_empty():
			total += int(other.cargo.get(job.ware_id, 0)) * int(ware.volume)
	return total


func _source_stock(world: RefCounted, station: Dictionary, ware_id: String) -> int:
	var amount := int(station.stock.get(ware_id, 0))
	if station.owner == world.state.player_faction_id:
		amount -= protected_stock(world, station, ware_id)
	return maxi(0, amount)


func _candidate(world: RefCounted, ship: Dictionary, station: Dictionary, desired: Dictionary) -> Dictionary:
	var best: Dictionary = {}
	var best_urgency := -1.0
	var best_price := 2147483647
	var best_legs := 2147483647
	var any_shortfall := false
	var any_need := false
	var any_room := false
	var any_cargo_space := false
	var any_stock := false
	var any_allowance := false
	var free_ship := maxi(0, int(ship.cargo_capacity) - int(world.cargo_volume(str(ship.id))))
	var free_station := maxi(0, int(station.storage_capacity) - int(world.station_volume(str(station.id))) - _incoming_volume(world, ship, str(station.id)))
	var allowance := maxi(0, int(ship.station_supply.budget_limit) - int(ship.station_supply.spent))
	for ware_id in desired:
		var shortfall := maxi(0, int(desired[ware_id]) - int(station.stock.get(ware_id, 0)))
		any_shortfall = any_shortfall or shortfall > 0
		var remaining := maxi(0, shortfall - _other_inbound(world, ship, str(station.id), str(ware_id)))
		if remaining <= 0:
			continue
		var urgency := float(remaining) / float(desired[ware_id])
		any_need = true
		var ware: Dictionary = world._find_ware(str(ware_id))
		if ware.is_empty() or int(ware.volume) > free_station:
			continue
		any_room = true
		if int(ware.volume) > free_ship:
			continue
		any_cargo_space = true
		for source in world.state.stations:
			if source.id == station.id:
				continue
			var available := _source_stock(world, source, str(ware_id))
			if available <= 0:
				continue
			var owned: bool = source.owner == world.state.player_faction_id
			var price := 0 if owned else int(source.sell_prices.get(ware_id, 0))
			if not owned and price <= 0:
				continue
			var first: Array = world._find_route(str(ship.sector), str(source.sector))
			var second: Array = world._find_route(str(source.sector), str(station.sector))
			if first.is_empty() or second.is_empty():
				continue
			any_stock = true
			if not owned and allowance < price:
				continue
			any_allowance = true
			if not owned and int(world.state.starting_credits) < price:
				continue
			var legs := first.size() + second.size() - 2
			if urgency > best_urgency + EPSILON or (absf(urgency - best_urgency) <= EPSILON and (price < best_price or (price == best_price and legs < best_legs))):
				best_urgency = urgency
				best_price = price
				best_legs = legs
				best = {"source_id":source.id, "ware_id":ware_id}
	if not best.is_empty():
		return best
	if not any_need:
		return {"waiting":"Waiting for other deliveries" if any_shortfall else "Station inputs stocked"}
	if not any_room:
		return {"waiting":"Waiting for station storage"}
	if not any_cargo_space:
		return {"waiting":"Waiting for cargo space"}
	if not any_stock:
		return {"waiting":"Waiting for supply stock"}
	if not any_allowance:
		return {"waiting":"Waiting for purchase allowance"}
	return {"waiting":"Waiting for credits"}


func tick(world: RefCounted, ship: Dictionary) -> void:
	var job: Dictionary = ship.station_supply
	if not job.enabled or not ship.orders.is_empty() or not ship.travel.is_empty():
		return
	var station: Dictionary = world._find_station(str(job.station_id))
	if station.is_empty() or station.owner != world.state.player_faction_id:
		stop(ship)
		ship.status = "Supply station unavailable"
		return
	var desired := targets(world, station)
	if int(job.retry_ticks) > 0:
		job.retry_ticks = int(job.retry_ticks) - 1
		ship.status = str(job.wait_reason)
		return
	if job.phase != "to_station":
		for ware_id in desired:
			var remaining := maxi(0, int(desired[ware_id]) - int(station.stock.get(ware_id, 0)) - _other_inbound(world, ship, str(station.id), str(ware_id)))
			if remaining > 0 and int(ship.cargo.get(ware_id, 0)) > 0:
				job.phase = "to_station"
				job.source_id = ""
				job.ware_id = ware_id
				break
	if job.phase == "idle":
		var choice := _candidate(world, ship, station, desired)
		if choice.has("waiting"):
			_wait(job, ship, str(choice.waiting))
			return
		job.phase = "to_source"
		job.source_id = choice.source_id
		job.ware_id = choice.ware_id
		job.wait_reason = ""
	if job.phase == "to_source":
		var source: Dictionary = world._find_station(str(job.source_id))
		var ware: Dictionary = world._find_ware(str(job.ware_id))
		if source.is_empty() or ware.is_empty() or source.id == station.id:
			_reset_trip(job)
			return
		if ship.sector != source.sector:
			if not _go(world, ship, str(source.sector)):
				_reset_trip(job)
			return
		var need := maxi(0, int(desired.get(job.ware_id, 0)) - int(station.stock.get(job.ware_id, 0)) - _other_inbound(world, ship, str(station.id), str(job.ware_id)))
		var amount := mini(need, _source_stock(world, source, str(job.ware_id)))
		amount = mini(amount, int(maxi(0, int(ship.cargo_capacity) - int(world.cargo_volume(str(ship.id)))) / int(ware.volume)))
		amount = mini(amount, int(maxi(0, int(station.storage_capacity) - int(world.station_volume(str(station.id))) - _incoming_volume(world, ship, str(station.id))) / int(ware.volume)))
		var owned: bool = source.owner == world.state.player_faction_id
		var price := 0 if owned else int(source.sell_prices.get(job.ware_id, 0))
		if not owned and price > 0:
			amount = mini(amount, int(mini(int(world.state.starting_credits), int(job.budget_limit) - int(job.spent)) / price))
		elif not owned:
			amount = 0
		if amount <= 0:
			_reset_trip(job)
			return
		ship.docked_at = source.id
		ship.status = "Docked"
		var result: Dictionary = world.transfer_player_station(str(ship.id), str(source.id), str(ware.id), amount, false) if owned else world._trade_for_ship(ship, str(source.id), str(ware.id), amount, true)
		if not result.ok:
			_reset_trip(job)
			return
		job.spent = int(job.spent) + amount * price
		job.phase = "to_station"
		job.source_id = ""
	if job.phase == "to_station":
		var ware: Dictionary = world._find_ware(str(job.ware_id))
		if ware.is_empty() or int(ship.cargo.get(job.ware_id, 0)) <= 0:
			_reset_trip(job)
			return
		if ship.sector != station.sector:
			if not _go(world, ship, str(station.sector)):
				_wait(job, ship, "Waiting for route to station")
			return
		var need := maxi(0, int(desired.get(job.ware_id, 0)) - int(station.stock.get(job.ware_id, 0)))
		if need == 0:
			_reset_trip(job)
			return
		var room := int(maxi(0, int(station.storage_capacity) - int(world.station_volume(str(station.id)))) / int(ware.volume))
		var amount := mini(need, mini(room, int(ship.cargo.get(job.ware_id, 0))))
		if amount <= 0:
			_wait(job, ship, "Waiting for station storage")
			return
		ship.docked_at = station.id
		ship.status = "Docked"
		world.transfer_player_station(str(ship.id), str(station.id), str(ware.id), amount, true)
		_reset_trip(job)
