extends RefCounted
## Player-ship names and dockside crew services. Every hired service crew
## member comes from a finite NPC station roster; money goes to that station.
## Transfers move existing people between owned, co-docked ships. The captain
## is a separate assigned pilot and is not hired or discharged by this module.

const HIRE_COST := 250
const STARTING_RECRUITS := 12
const MAX_NAME_LENGTH := 40


func prepare(target: Dictionary) -> Error:
	if target.has("personnel_version"):
		return OK if target.personnel_version == 1 and target.get("crew_pools") is Dictionary else ERR_UNAVAILABLE
	if target.has("crew_pools"):
		return ERR_INVALID_DATA
	var pool: Dictionary = {}
	for station in target.get("stations", []):
		if station.owner != target.player_faction_id:
			pool[str(station.id)] = STARTING_RECRUITS
	target["crew_pools"] = pool
	target["personnel_version"] = 1
	return OK


func capacity(ship: Dictionary) -> int:
	match str(ship.get("class", "")):
		"Courier":
			return 8
		"Freighter":
			return 24
		"Builder":
			return 32
		"Carrier":
			return 80
		_:
			return 12


func _owned_ship(world: RefCounted, ship_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id:
		return {}
	return ship


func _valid_name(candidate: String) -> bool:
	if candidate.length() < 1 or candidate.length() > MAX_NAME_LENGTH:
		return false
	for index in range(candidate.length()):
		if candidate.unicode_at(index) < 32 or candidate.unicode_at(index) == 127:
			return false
	return true


func rename(world: RefCounted, ship_id: String, name: String) -> Dictionary:
	var ship := _owned_ship(world, ship_id)
	var candidate: String = name.strip_edges()
	if ship.is_empty():
		return {"ok":false, "message":"Only your own ships can be renamed."}
	if not _valid_name(candidate):
		return {"ok":false, "message":"Use a ship name of 1 to 40 characters without control characters."}
	if str(ship.name) == candidate:
		return {"ok":false, "message":"The ship already has that name."}
	ship.name = candidate
	return {"ok":true, "message":"Ship renamed to %s." % candidate}


func _dock_available(ship: Dictionary, station: Dictionary) -> bool:
	return not ship.is_empty() and not station.is_empty() and str(ship.docked_at) == str(station.id) and ship.sector == station.sector and ship.orders.is_empty() and ship.travel.is_empty()


func hire(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship := _owned_ship(world, ship_id)
	if ship.is_empty() or quantity < 1 or quantity > 100:
		return {"ok":false, "message":"Choose a player ship and a valid crew quantity."}
	var station: Dictionary = world._find_station(str(ship.docked_at))
	if not _dock_available(ship, station) or station.owner == world.state.player_faction_id or not world.state.crew_pools.has(station.id):
		return {"ok":false, "message":"Dock this ship at an NPC recruitment station to hire crew."}
	if int(world.state.relations.get(str(station.owner), 0)) < -25:
		return {"ok":false, "message":"A hostile station will not recruit for your faction."}
	if int(ship.crew) + quantity > capacity(ship):
		return {"ok":false, "message":"This ship has insufficient crew berths."}
	if int(world.state.crew_pools[station.id]) < quantity:
		return {"ok":false, "message":"The station has insufficient available recruits."}
	var total: int = quantity * HIRE_COST
	if int(world.state.starting_credits) < total:
		return {"ok":false, "message":"Insufficient faction credits for recruitment."}
	# Mutate only after all checks, so a failed transaction is atomic.
	world.state.starting_credits = int(world.state.starting_credits) - total
	station.credits = int(station.credits) + total
	ship.crew = int(ship.crew) + quantity
	world.state.crew_pools[station.id] = int(world.state.crew_pools[station.id]) - quantity
	world._record_transaction("crew_hire", ship_id, str(station.id), "", quantity, HIRE_COST, -total)
	return {"ok":true, "message":"Hired %d service crew for %d CR." % [quantity, total]}


func discharge(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship := _owned_ship(world, ship_id)
	if ship.is_empty() or quantity < 1 or quantity > 100 or int(ship.crew) < quantity:
		return {"ok":false, "message":"There are not enough service crew to discharge."}
	var station: Dictionary = world._find_station(str(ship.docked_at))
	if not _dock_available(ship, station) or not world.state.crew_pools.has(station.id) or station.owner == world.state.player_faction_id:
		return {"ok":false, "message":"Dock at an NPC recruitment station to discharge crew."}
	ship.crew = int(ship.crew) - quantity
	world.state.crew_pools[station.id] = int(world.state.crew_pools[station.id]) + quantity
	world._record_transaction("crew_discharge", ship_id, str(station.id), "", quantity, 0, 0)
	return {"ok":true, "message":"Discharged %d service crew to the station roster." % quantity}


func transfer(world: RefCounted, source_id: String, destination_id: String, quantity: int) -> Dictionary:
	var source := _owned_ship(world, source_id)
	var destination := _owned_ship(world, destination_id)
	if source.is_empty() or destination.is_empty() or source_id == destination_id or quantity < 1 or quantity > 100:
		return {"ok":false, "message":"Choose two different owned ships and a valid crew quantity."}
	var station: Dictionary = world._find_station(str(source.docked_at))
	if not _dock_available(source, station) or not _dock_available(destination, station):
		return {"ok":false, "message":"Both ships must finish orders and dock at the same station."}
	if quantity > int(source.crew):
		return {"ok":false, "message":"Not enough crew aboard the source ship."}
	if int(destination.crew) + quantity > capacity(destination):
		return {"ok":false, "message":"Destination ship has insufficient crew berths."}
	source.crew = int(source.crew) - quantity
	destination.crew = int(destination.crew) + quantity
	world._record_transaction("crew_transfer", destination_id, str(station.id), "", quantity, 0, 0)
	return {"ok":true, "message":"Transferred %d service crew to %s." % [quantity, destination.name]}


func eligible_transfers(world: RefCounted, source_id: String) -> Array:
	var result: Array = []
	var source := _owned_ship(world, source_id)
	if source.is_empty():
		return result
	for candidate in world.state.ships:
		if candidate.id != source.id and candidate.owner == world.state.player_faction_id and not str(source.docked_at).is_empty() and candidate.docked_at == source.docked_at and candidate.sector == source.sector:
			result.append(candidate)
	return result
