extends RefCounted
## Pass 36: autonomous hazardous-waste logistics between REAL owned stations.
## Each run collects physically produced organic waste, occupies ship cargo
## capacity, respects the source's own working recipe buffer, travels real
## sector gates, docks and delivers without creating credits or cargo.

const VERSION := 1
const WARE := "organic_waste"
const TARGET_STOCK := 12
const RETRY_TICKS := 5


func _empty_job() -> Dictionary:
	return {"enabled":false, "destination_id":"", "source_id":"", "phase":"idle", "managed_quantity":0, "retry_ticks":0, "wait_reason":"", "trips":0, "delivered_total":0}


func initialize_ship(ship: Dictionary) -> void:
	if ship.owner != "":
		ship["waste_transport"] = _empty_job()


func prepare(target: Dictionary) -> Error:
	if target.has("waste_transport_version"):
		if int(target.waste_transport_version) != VERSION:
			return ERR_UNAVAILABLE
		for ship in target.ships:
			if ship.owner == target.player_faction_id and not ship.get("waste_transport") is Dictionary:
				return ERR_INVALID_DATA
			if ship.owner != target.player_faction_id and ship.has("waste_transport"):
				return ERR_INVALID_DATA
		return OK
	for ship in target.ships:
		if ship.has("waste_transport"):
			return ERR_ALREADY_IN_USE
	for ship in target.ships:
		if ship.owner == target.player_faction_id:
			ship["waste_transport"] = _empty_job()
	target["waste_transport_version"] = VERSION
	return OK


func _recycles(station: Dictionary) -> bool:
	for module in station.get("production", []):
		if str(module.recipe_id) == "water_recycling":
			return true
	return false


func assign(world: RefCounted, ship_id: String, destination_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var destination: Dictionary = world._find_station(destination_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id or not ship.has("waste_transport"):
		return {"ok":false, "message":"Choose one existing player-owned ship."}
	if destination.is_empty() or destination.owner != world.state.player_faction_id or not _recycles(destination):
		return {"ok":false, "message":"Choose an actual owned station with a completed wastewater recycling module."}
	if int(ship.cargo_capacity) < 1:
		return {"ok":false, "message":"This ship has no physical cargo bay for waste."}
	if int(ship.get("settler_passengers", 0)) != 0 or not ship.get("career_manifest", {}).is_empty() or not ship.get("professional_passenger_ids", []).is_empty():
		return {"ok":false, "message":"Complete civilian transport before assigning a bio-waste hauler."}
	if bool(ship.waste_transport.enabled) and str(ship.waste_transport.destination_id) == destination_id:
		ship.waste_transport.retry_ticks = 0
		return {"ok":true, "message":"Existing waste collection refreshed. Cargo, trips and scheduled orders remain unchanged."}
	# Role changes leave the ship's *already queued* movement orders alone.
	ship.player_trader.enabled = false
	world.build_supply.stop(ship)
	world.station_supply.stop(ship)
	stop(ship)
	ship.waste_transport.enabled = true
	ship.waste_transport.destination_id = destination_id
	ship.role = "Waste Hauler"
	return {"ok":true, "message":"Waste-hauling assigned. Ship will collect surplus real organic waste from owned stations and deliver it to the recycler using normal cargo, docking and star routes."}


func stop(ship: Dictionary) -> void:
	if not ship.has("waste_transport"):
		return
	ship.waste_transport = _empty_job()
	if ship.get("role", "") == "Waste Hauler":
		ship.role = "Unassigned"


func _wait(ship: Dictionary, job: Dictionary, message: String) -> void:
	job.retry_ticks = RETRY_TICKS
	job.wait_reason = message
	ship.status = message


func _finish_trip(job: Dictionary) -> void:
	job.phase = "idle"
	job.source_id = ""
	job.managed_quantity = 0
	job.retry_ticks = 0
	job.wait_reason = ""


func _incoming(world: RefCounted, destination_id: String, own_ship_id: String) -> int:
	var inbound := 0
	for other in world.state.ships:
		if str(other.id) == own_ship_id or not other.has("waste_transport"):
			continue
		var trip: Dictionary = other.waste_transport
		if bool(trip.enabled) and str(trip.destination_id) == destination_id and trip.phase == "to_destination":
			inbound += int(trip.managed_quantity)
	return inbound


func _desired(world: RefCounted, target: Dictionary, ship: Dictionary) -> int:
	var reserved_space: int = maxi(0, int(target.storage_capacity) - int(world.station_volume(str(target.id))))
	# Do not let waste input occupy every last warehouse slot needed for
	# the recycler's *three* physical outputs (water, soil, salt).
	var ware: Dictionary = world._find_ware(WARE)
	if ware.is_empty():
		return 0
	var allowance := mini(TARGET_STOCK, maxi(0, int(target.storage_capacity) / 3))
	var needed: int = maxi(0, allowance - int(target.stock.get(WARE, 0)) - _incoming(world, str(target.id), str(ship.id)))
	return mini(needed, maxi(0, reserved_space - 3))


func _source(world: RefCounted, ship: Dictionary, destination: Dictionary) -> Dictionary:
	var selected: Dictionary = {}
	var best_path := 2147483647
	var best_stock := -1
	for candidate in world.state.stations:
		if candidate.owner != world.state.player_faction_id or candidate.id == destination.id:
			continue
		var protected: int = world.station_supply.protected_stock(world, candidate, WARE)
		var usable: int = maxi(0, int(candidate.stock.get(WARE, 0)) - protected)
		if usable < 1:
			continue
		var path: Array = world._find_route(str(ship.sector), str(candidate.sector))
		var back: Array = world._find_route(str(candidate.sector), str(destination.sector))
		if path.is_empty() or back.is_empty():
			continue
		var distance: int = path.size() + back.size() - 2
		if distance < best_path or (distance == best_path and usable > best_stock):
			best_path = distance
			best_stock = usable
			selected = candidate
	return selected


func tick(world: RefCounted, ship: Dictionary) -> void:
	var job: Dictionary = ship.waste_transport
	if not bool(job.enabled) or not ship.orders.is_empty() or not ship.travel.is_empty():
		return
	var destination: Dictionary = world._find_station(str(job.destination_id))
	if destination.is_empty() or destination.owner != world.state.player_faction_id or not _recycles(destination):
		stop(ship)
		ship.status = "Waste treatment station unavailable"
		return
	if int(job.retry_ticks) > 0:
		job.retry_ticks = int(job.retry_ticks) - 1
		ship.status = str(job.wait_reason)
		return
	if job.phase == "idle":
		if _desired(world, destination, ship) < 1:
			_wait(ship, job, "Waste recycler already stocked or lacks storage")
			return
		var source: Dictionary = _source(world, ship, destination)
		if source.is_empty():
			_wait(ship, job, "Waiting for physically collected waste")
			return
		job.phase = "to_source"
		job.source_id = str(source.id)
		job.wait_reason = ""
	if job.phase == "to_source":
		var source: Dictionary = world._find_station(str(job.source_id))
		if source.is_empty() or source.owner != world.state.player_faction_id or source.id == destination.id:
			_finish_trip(job)
			return
		if str(ship.sector) != str(source.sector):
			if not world._queue_ship_route(ship, str(source.sector)):
				_wait(ship, job, "Waiting for route to waste collection")
			return
		var ware: Dictionary = world._find_ware(WARE)
		var available: int = maxi(0, int(source.stock.get(WARE, 0)) - world.station_supply.protected_stock(world, source, WARE))
		var cargo_room: int = int(maxi(0, int(ship.cargo_capacity) - int(world.cargo_volume(str(ship.id)))) / int(ware.volume))
		var quantity: int = mini(_desired(world, destination, ship), mini(available, cargo_room))
		if quantity <= 0:
			_finish_trip(job)
			_wait(ship, job, "Waste source or cargo capacity unavailable")
			return
		ship.docked_at = str(source.id)
		ship.status = "Docked"
		var pickup: Dictionary = world.transfer_player_station(str(ship.id), str(source.id), WARE, quantity, false)
		if not pickup.ok:
			_finish_trip(job)
			_wait(ship, job, "Waste collection blocked: " + str(pickup.message))
			return
		job.managed_quantity = quantity
		job.phase = "to_destination"
		world._record_transaction("waste_collected", str(ship.id), str(source.id), WARE, quantity, 0, 0)
	if job.phase == "to_destination":
		var ware: Dictionary = world._find_ware(WARE)
		if str(ship.sector) != str(destination.sector):
			if not world._queue_ship_route(ship, str(destination.sector)):
				_wait(ship, job, "Waiting for route to waste recycler")
			return
		var room: int = int(maxi(0, int(destination.storage_capacity) - int(world.station_volume(str(destination.id))) - 3) / int(ware.volume))
		var quantity: int = mini(int(job.managed_quantity), mini(room, int(ship.cargo.get(WARE, 0))))
		if quantity <= 0:
			_wait(ship, job, "Waiting for recycling storage or carried waste")
			return
		ship.docked_at = str(destination.id)
		ship.status = "Docked"
		var delivery: Dictionary = world.transfer_player_station(str(ship.id), str(destination.id), WARE, quantity, true)
		if not delivery.ok:
			_wait(ship, job, "Waste delivery blocked: " + str(delivery.message))
			return
		job.managed_quantity = int(job.managed_quantity) - quantity
		job.delivered_total = int(job.delivered_total) + quantity
		world._record_transaction("waste_delivered", str(ship.id), str(destination.id), WARE, quantity, 0, 0)
		if int(job.managed_quantity) == 0:
			job.trips = int(job.trips) + 1
			_finish_trip(job)
