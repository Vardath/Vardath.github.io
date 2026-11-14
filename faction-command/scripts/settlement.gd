extends RefCounted
## Pass 29: population-conserving, physically docked civilian relocation.
## Passengers are NOT service crew; they occupy otherwise unfilled berths.
## No births, automatic immigration or free housing are created by this module.

const VERSION := 1
const RESETTLEMENT_FEE := 100
const MAX_BATCH := 100


func initialize_ship(ship: Dictionary) -> void:
	ship["settler_passengers"] = 0
	ship["settler_source_station_id"] = ""


func prepare(target: Dictionary) -> Error:
	if target.has("settlement_version"):
		return OK if int(target.settlement_version) == VERSION else ERR_UNAVAILABLE
	if not target.has("provisions_version"):
		return ERR_INVALID_DATA
	for ship in target.ships:
		if ship.has("settler_passengers") or ship.has("settler_source_station_id"):
			return ERR_INVALID_DATA
	for ship in target.ships:
		initialize_ship(ship)
	target["settlement_version"] = VERSION
	return OK


func free_berths(world: RefCounted, ship: Dictionary) -> int:
	if ship.is_empty():
		return 0
	return maxi(0, world.personnel.capacity(ship) - int(ship.crew) - int(ship.get("settler_passengers", 0)))


func _docked(world: RefCounted, ship: Dictionary) -> Dictionary:
	if ship.is_empty() or ship.owner != world.state.player_faction_id or not ship.orders.is_empty() or not ship.travel.is_empty():
		return {}
	var station: Dictionary = world._find_station(str(ship.get("docked_at", "")))
	if station.is_empty() or str(station.sector) != str(ship.sector):
		return {}
	return station


func board(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = _docked(world, ship)
	if station.is_empty() or station.owner == world.state.player_faction_id or not world.state.crew_pools.has(str(station.id)):
		return {"ok":false, "message":"Dock your ship at a non-hostile NPC recruitment station to board settlers."}
	if quantity < 1 or quantity > MAX_BATCH or quantity > free_berths(world, ship):
		return {"ok":false, "message":"Not enough unoccupied ship berths for this group."}
	if int(world.state.relations.get(str(station.owner), 0)) < -25:
		return {"ok":false, "message":"Hostile factions do not authorise civilian resettlement."}
	if int(ship.settler_passengers) > 0 and str(ship.settler_source_station_id) != str(station.id):
		return {"ok":false, "message":"Deliver or return the present group before boarding from another station."}
	if world.population.available_workers(world, str(station.id)) < quantity:
		return {"ok":false, "message":"That station has insufficient existing adult residents."}
	var fee: int = quantity * RESETTLEMENT_FEE
	if int(world.state.starting_credits) < fee:
		return {"ok":false, "message":"Insufficient faction credits for passenger relocation permits."}
	# The NPC's resident ledger and recruitment mirror are the SAME people.
	# Debiting both views is handled in the population module, once.
	if not world.population.move_workers(world, str(station.id), -quantity):
		return {"ok":false, "message":"Population and recruitment rosters do not reconcile."}
	world.state.starting_credits = int(world.state.starting_credits) - fee
	station.credits = int(station.credits) + fee
	ship.settler_passengers = int(ship.settler_passengers) + quantity
	ship.settler_source_station_id = str(station.id)
	world._record_transaction("settler_boarding", ship_id, str(station.id), "", quantity, RESETTLEMENT_FEE, -fee)
	return {"ok":true, "message":"%d existing adults boarded. Transport them to a supplied, operational player habitat." % quantity}


func disembark(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = _docked(world, ship)
	if station.is_empty() or quantity < 1 or quantity > MAX_BATCH or quantity > int(ship.get("settler_passengers", 0)):
		return {"ok":false, "message":"Dock your ship and select a valid number of passengers aboard."}
	var source_id: String = str(ship.settler_source_station_id)
	if str(station.id) == source_id:
		if not world.population.move_workers(world, source_id, quantity):
			return {"ok":false, "message":"Original resident roster is not available for returns."}
		ship.settler_passengers = int(ship.settler_passengers) - quantity
		if int(ship.settler_passengers) == 0:
			ship.settler_source_station_id = ""
		world._record_transaction("settler_return", ship_id, source_id, "", quantity, 0, 0)
		return {"ok":true, "message":"%d passengers safely returned to their original resident roster." % quantity}
	if station.owner != world.state.player_faction_id:
		return {"ok":false, "message":"Passengers may settle only at your own operational station, or return to their original station."}
	var record: Dictionary = world.population.station_cohort(world, str(station.id))
	if record.is_empty():
		return {"ok":false, "message":"Station has no registered population ledger."}
	var occupied: int = int(record.cohorts.assigned_workers)
	var usable: int = world.habitation.operational_capacity(station, world.state.habitation_catalog)
	if usable < 1 or occupied + quantity > usable:
		return {"ok":false, "message":"The station needs enough actively powered, provisioned housing for all arriving adults."}
	var shortage: String = world.provisions.missing_provision(world, station)
	if not shortage.is_empty():
		return {"ok":false, "message":"Settlers cannot disembark: next service cycle lacks " + shortage + "."}
	if occupied + quantity > 1000000:
		return {"ok":false, "message":"Population capacity exceeded."}
	record.cohorts.assigned_workers = occupied + quantity
	ship.settler_passengers = int(ship.settler_passengers) - quantity
	if int(ship.settler_passengers) == 0:
		ship.settler_source_station_id = ""
	world._record_transaction("settler_arrival", ship_id, str(station.id), "", quantity, 0, 0)
	return {"ok":true, "message":"%d adults settled in %s's existing powered housing." % [quantity, station.name]}
