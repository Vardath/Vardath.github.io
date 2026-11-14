extends RefCounted
## A minimal, finite NPC ship-assembly berth. A contract transfers real credits,
## consumes existing alloy at placement, and produces a player-owned hull after
## a serialized, tick-driven queue. No instant or free vessels.

const DATA_PATH := "res://data/ship_hulls.json"
const MAX_PENDING := 5


func _positive_whole(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) >= 1.0 and float(value) == floor(float(value))


func prepare(target: Dictionary) -> Error:
	if target.has("shipyard_version"):
		return OK if target.shipyard_version == 1 and target.get("shipyard") is Dictionary else ERR_UNAVAILABLE
	if target.has("shipyard"):
		return ERR_INVALID_DATA
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not data is Dictionary or data.get("schema_version") != 1 or not data.get("hulls") is Array or not data.get("wharf_station_id") is String:
		return ERR_INVALID_DATA
	var catalog: Dictionary = {}
	var wares: Dictionary = {}
	for ware in target.wares:
		wares[ware.id] = true
	for hull in data.hulls:
		if not hull is Dictionary or not hull.get("id") is String or str(hull.id).is_empty() or catalog.has(hull.id) or not hull.get("name") is String or not hull.get("class") is String:
			return ERR_INVALID_DATA
		for key in ["price", "ticks", "cargo_capacity", "crew"]:
			if not _positive_whole(hull.get(key)):
				return ERR_INVALID_DATA
		if not hull.get("materials") is Dictionary or hull.materials.is_empty():
			return ERR_INVALID_DATA
		for ware_id in hull.materials:
			if not wares.has(ware_id) or not _positive_whole(hull.materials[ware_id]):
				return ERR_INVALID_DATA
		catalog[hull.id] = hull.duplicate(true)
	if catalog.is_empty():
		return ERR_INVALID_DATA
	target["shipyard"] = {"wharf_station_id":str(data.wharf_station_id), "catalog":catalog, "orders":[], "next_order_id":1, "next_ship_serial":2}
	target["shipyard_version"] = 1
	return OK


func _wharf(world: RefCounted) -> Dictionary:
	return world._find_station(str(world.state.shipyard.wharf_station_id))


func _open_orders(world: RefCounted) -> int:
	var result := 0
	for order in world.state.shipyard.orders:
		if str(order.status) != "complete":
			result += 1
	return result


func quote(world: RefCounted, hull_id: String) -> Dictionary:
	var catalog: Dictionary = world.state.get("shipyard", {}).get("catalog", {})
	var hull: Dictionary = catalog.get(hull_id, {})
	if hull.is_empty():
		return {"ok":false, "message":"Unknown ship hull."}
	var wharf: Dictionary = _wharf(world)
	if wharf.is_empty() or wharf.owner == world.state.player_faction_id:
		return {"ok":false, "message":"The NPC wharf is unavailable."}
	if int(world.state.relations.get(str(wharf.owner), 0)) < -25:
		return {"ok":false, "message":"The wharf will not contract with a hostile faction."}
	if _open_orders(world) >= MAX_PENDING:
		return {"ok":false, "message":"Five ship orders are already awaiting delivery."}
	if int(world.state.starting_credits) < int(hull.price):
		return {"ok":false, "message":"Insufficient player credits for the ship contract."}
	for ware_id in hull.materials:
		if int(wharf.stock.get(ware_id, 0)) < int(hull.materials[ware_id]):
			return {"ok":false, "message":"The wharf lacks %s. Physical shipbuilding material must be in its stock." % str(ware_id)}
	return {"ok":true, "message":"Ready to contract with %s." % wharf.name, "hull":hull}


func _ship_id_reserved(world: RefCounted, ship_id: String) -> bool:
	for order in world.state.shipyard.orders:
		if order.ship_id == ship_id:
			return true
	return false


func place_order(world: RefCounted, hull_id: String) -> Dictionary:
	var estimate: Dictionary = quote(world, hull_id)
	if not bool(estimate.get("ok", false)):
		return estimate
	var hull: Dictionary = estimate.hull
	var wharf: Dictionary = _wharf(world)
	var serial: int = int(world.state.shipyard.next_ship_serial)
	var ship_id: String = "player_ship_%04d" % serial
	while not world._find_ship(ship_id).is_empty() or _ship_id_reserved(world, ship_id):
		serial += 1
		ship_id = "player_ship_%04d" % serial
	var order_id: int = int(world.state.shipyard.next_order_id)
	var record: Dictionary = {"id":"ship_order_%d" % order_id, "ship_id":ship_id, "hull_id":hull_id, "wharf_station_id":str(wharf.id), "price":int(hull.price), "materials":hull.materials.duplicate(true), "duration":int(hull.ticks), "progress":0, "status":"queued", "placed_tick":int(world.state.tick), "finished_tick":0}
	# All stock and credit conditions were checked before any mutation.
	world.state.starting_credits = int(world.state.starting_credits) - int(hull.price)
	wharf.credits = int(wharf.credits) + int(hull.price)
	for ware_id in hull.materials:
		wharf.stock[ware_id] = int(wharf.stock[ware_id]) - int(hull.materials[ware_id])
	world.state.shipyard.next_order_id = order_id + 1
	world.state.shipyard.next_ship_serial = serial + 1
	world.state.shipyard.orders.append(record)
	world._record_transaction("ship_order", ship_id, str(wharf.id), "", 1, int(hull.price), -int(hull.price))
	return {"ok":true, "message":"Ship contracted. Its metal is reserved and the wharf will build it over time.", "order_id":record.id, "ship_id":ship_id}


func _assemble_ship(world: RefCounted, order: Dictionary, wharf: Dictionary) -> Dictionary:
	var hull: Dictionary = world.state.shipyard.catalog.get(str(order.hull_id), {})
	if hull.is_empty():
		return {}
	var suffix: String = str(order.ship_id).get_slice("_", 2)
	var vessel: Dictionary = {
		"id":str(order.ship_id), "name":"%s %s" % [hull.name, suffix],
		"class":str(hull["class"]), "owner":world.state.player_faction_id,
		"sector":str(wharf.sector), "captain":"Contract Pilot " + suffix,
		"crew":int(hull.crew), "role":"Unassigned", "status":"Docked",
		"orders":[], "travel":{}, "cargo_capacity":int(hull.cargo_capacity),
		"cargo":{}, "docked_at":str(wharf.id),
		"player_trader":{"enabled":false, "phase":"idle", "source_id":"", "destination_id":"", "ware_id":"", "quantity":0, "managed_quantity":0, "retry_ticks":0},
		"build_supply":world.build_supply._empty_job(),
		"station_supply":world.station_supply._empty_job()
	}
	world.personnel.initialize_ship(vessel, int(world.state.tick), str(wharf.id))
	if world.state.has("settlement_version"):
		world.settlement.initialize_ship(vessel)
	return vessel


func tick(world: RefCounted) -> void:
	for order in world.state.shipyard.orders:
		if str(order.status) == "complete":
			continue
		var wharf: Dictionary = world._find_station(str(order.wharf_station_id))
		if wharf.is_empty() or wharf.owner == world.state.player_faction_id:
			order.status = "blocked"
			return
		if not world._find_ship(str(order.ship_id)).is_empty():
			order.status = "blocked"
			return
		if int(order.progress) < int(order.duration) - 1:
			order.status = "building"
			order.progress = int(order.progress) + 1
			return
		var new_ship: Dictionary = _assemble_ship(world, order, wharf)
		if new_ship.is_empty():
			order.status = "blocked"
			return
		# The contracted pilot and crew now leave the wharf's *existing*
		# resident workforce. If too few people remain, a paid hull waits
		# rather than generating free ship personnel.
		var staff_needed: int = int(new_ship.crew) + 1
		if world.population.available_workers(world, str(wharf.id)) < staff_needed or not world.population.move_workers(world, str(wharf.id), -staff_needed):
			order.status = "blocked"
			return
		world.state.ships.append(new_ship)
		order.progress = int(order.duration)
		order.status = "complete"
		order.finished_tick = int(world.state.tick)
		world._record_transaction("ship_delivery", str(new_ship.id), str(wharf.id), "", 1, 0, 0)
		return
