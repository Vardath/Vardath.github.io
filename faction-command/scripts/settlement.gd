extends RefCounted
## Pass 30: finite resident service, protected shortages and dockside evacuation.
## Live adults are conserved between cohorts and passenger manifests.
## Empty resident pools, free manufactured goods, births, automatic evacuation
## or loss of population on life-support failures are never created.

const VERSION := 2
const RESETTLEMENT_FEE := 100
const MAX_BATCH := 100
const SERVICE_INTERVAL := 60
const WELFARE_STATUSES := ["Unoccupied", "Awaiting service", "Provisioned", "Provision shortage", "Housing offline"]
const RESIDENT_WARES := ["potable_water", "food_rations", "medical_supplies"]


func initialize_ship(ship: Dictionary) -> void:
	ship["settler_passengers"] = 0
	ship["settler_source_station_id"] = ""


func _initialize_welfare(record: Dictionary) -> void:
	# Existing settled adults from v1 are not retroactively charged or reset.
	record["resident_status"] = "Awaiting service" if int(record.cohorts.assigned_workers) > 0 else "Unoccupied"
	record["resident_shortage"] = ""
	record["resident_alert_cycles"] = 0


func prepare(target: Dictionary) -> Error:
	var prior: int = int(target.get("settlement_version", 0))
	if prior == VERSION:
		return OK
	if prior not in [0, 1] or not target.has("provisions_version") or not target.has("population_version"):
		return ERR_UNAVAILABLE
	if prior == 0:
		for ship in target.ships:
			if ship.has("settler_passengers") or ship.has("settler_source_station_id"):
				return ERR_INVALID_DATA
		for ship in target.ships:
			initialize_ship(ship)
	for record in target.population.stations.values():
		_initialize_welfare(record)
	target["settlement_version"] = VERSION
	return OK


func resident_needs(occupied: int) -> Dictionary:
	# One water and ration per four adults, one medical supply per eight.
	# The rounded batches are finite, explicit and small enough for existing
	# early production modules; no requirement when the station is unoccupied.
	if occupied <= 0:
		return {}
	return {
		"potable_water":ceili(float(occupied) / 4.0),
		"food_rations":ceili(float(occupied) / 4.0),
		"medical_supplies":ceili(float(occupied) / 8.0)
	}


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


func _manifest_compatible(ship: Dictionary, source_id: String) -> bool:
	return int(ship.get("settler_passengers", 0)) == 0 or str(ship.get("settler_source_station_id", "")) == source_id


func board(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = _docked(world, ship)
	if station.is_empty() or station.owner == world.state.player_faction_id or not world.state.crew_pools.has(str(station.id)):
		return {"ok":false, "message":"Dock an owned ship at a non-hostile NPC recruitment station."}
	if quantity < 1 or quantity > MAX_BATCH or quantity > free_berths(world, ship):
		return {"ok":false, "message":"Not enough unoccupied ship berths for this group."}
	if int(world.state.relations.get(str(station.owner), 0)) < -25:
		return {"ok":false, "message":"Hostile factions do not authorise civilian resettlement."}
	if not _manifest_compatible(ship, str(station.id)):
		return {"ok":false, "message":"Deliver or return the present group before boarding from another station."}
	if world.population.available_workers(world, str(station.id)) < quantity:
		return {"ok":false, "message":"That station has insufficient existing adult residents."}
	var fee: int = quantity * RESETTLEMENT_FEE
	if int(world.state.starting_credits) < fee:
		return {"ok":false, "message":"Insufficient faction credits for passenger relocation permits."}
	if not world.population.move_workers(world, str(station.id), -quantity):
		return {"ok":false, "message":"Population and recruitment rosters do not reconcile."}
	world.state.starting_credits = int(world.state.starting_credits) - fee
	station.credits = int(station.credits) + fee
	ship.settler_passengers = int(ship.settler_passengers) + quantity
	ship.settler_source_station_id = str(station.id)
	world._record_transaction("settler_boarding", ship_id, str(station.id), "", quantity, RESETTLEMENT_FEE, -fee)
	return {"ok":true, "message":"%d existing adults boarded for a real colony voyage." % quantity}


func evacuate(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = _docked(world, ship)
	if station.is_empty() or station.owner != world.state.player_faction_id:
		return {"ok":false, "message":"Dock your owned ship at an existing player colony to evacuate residents."}
	if quantity < 1 or quantity > MAX_BATCH or quantity > free_berths(world, ship) or not _manifest_compatible(ship, str(station.id)):
		return {"ok":false, "message":"Choose an available transport berth, and do not mix passengers from different sources."}
	var record: Dictionary = world.population.station_cohort(world, str(station.id))
	if record.is_empty() or int(record.cohorts.assigned_workers) < quantity:
		return {"ok":false, "message":"The colony has fewer settled adults than requested."}
	# Evacuation is explicitly legal even when housing is unpowered or stocks
	# are empty. It does not create medical supplies, crew or free credits.
	record.cohorts.assigned_workers = int(record.cohorts.assigned_workers) - quantity
	ship.settler_passengers = int(ship.settler_passengers) + quantity
	ship.settler_source_station_id = str(station.id)
	if int(record.cohorts.assigned_workers) == 0:
		_initialize_welfare(record)
	world._record_transaction("resident_evacuation", ship_id, str(station.id), "", quantity, 0, 0)
	return {"ok":true, "message":"Evacuated %d existing adults aboard %s. Travel to a supplied player colony." % [quantity, ship.name]}


func _clear_manifest(ship: Dictionary, quantity: int) -> void:
	ship.settler_passengers = int(ship.settler_passengers) - quantity
	if int(ship.settler_passengers) == 0:
		ship.settler_source_station_id = ""


func disembark(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = _docked(world, ship)
	if station.is_empty() or quantity < 1 or quantity > MAX_BATCH or quantity > int(ship.get("settler_passengers", 0)):
		return {"ok":false, "message":"Dock your ship and select a valid number of passengers aboard."}
	var source_id: String = str(ship.settler_source_station_id)
	# Only original NPC recruitment sources accept a return without housing.
	if station.owner != world.state.player_faction_id:
		if str(station.id) != source_id or not world.state.crew_pools.has(source_id):
			return {"ok":false, "message":"Return passengers to their original NPC source or settle them in a supplied player colony."}
		if not world.population.move_workers(world, source_id, quantity):
			return {"ok":false, "message":"Original resident roster is not available for returns."}
		_clear_manifest(ship, quantity)
		world._record_transaction("settler_return", ship_id, source_id, "", quantity, 0, 0)
		return {"ok":true, "message":"%d passengers safely returned to their original resident roster." % quantity}
	var record: Dictionary = world.population.station_cohort(world, str(station.id))
	if record.is_empty():
		return {"ok":false, "message":"Station has no registered population ledger."}
	var occupied: int = int(record.cohorts.assigned_workers)
	var usable: int = world.habitation.operational_capacity(station, world.state.habitation_catalog)
	if usable < 1 or occupied + quantity > usable or occupied + quantity > 1000000:
		return {"ok":false, "message":"The station needs enough powered housing for all arriving adults."}
	# Count the incoming adults in the NEXT service-cycle requirement before
	# admission; do not move people to an inadequately supplied habitat.
	var shortage: String = world.provisions.missing_provision(world, station, occupied + quantity)
	if not shortage.is_empty():
		return {"ok":false, "message":"Next residential service cycle lacks " + shortage + "."}
	record.cohorts.assigned_workers = occupied + quantity
	_clear_manifest(ship, quantity)
	record.resident_status = "Awaiting service"
	record.resident_shortage = ""
	record.resident_alert_cycles = 0
	world._record_transaction("settler_arrival", ship_id, str(station.id), "", quantity, 0, 0)
	return {"ok":true, "message":"%d adults settled in %s's real, provisioned housing." % [quantity, station.name]}


func tick(world: RefCounted) -> void:
	if int(world.state.tick) % SERVICE_INTERVAL != 0:
		return
	for station in world.state.stations:
		var record: Dictionary = world.population.station_cohort(world, str(station.id))
		if record.is_empty():
			continue
		var people: int = int(record.cohorts.assigned_workers)
		if people <= 0:
			_initialize_welfare(record)
			continue
		if world.habitation.operational_capacity(station, world.state.habitation_catalog) < people:
			record.resident_status = "Housing offline"
			record.resident_shortage = ""
			record.resident_alert_cycles = int(record.resident_alert_cycles) + 1
			continue
		var necessary: Dictionary = resident_needs(people)
		var missing: String = ""
		for ware_id in RESIDENT_WARES:
			if int(station.stock.get(ware_id, 0)) < int(necessary.get(ware_id, 0)):
				missing = str(ware_id)
				break
		if not missing.is_empty():
			# No partial resident debit, no phantom reserves or silent deaths.
			record.resident_status = "Provision shortage"
			record.resident_shortage = missing
			record.resident_alert_cycles = int(record.resident_alert_cycles) + 1
			continue
		for ware_id in necessary:
			station.stock[ware_id] = int(station.stock.get(ware_id, 0)) - int(necessary[ware_id])
		# Waste comes only from paid water and food, never from vacant
		# habitats, passengers, phantom NPC pools or failed service cycles.
		if world.state.has("ecology_version"):
			world.ecology.record_resident_waste(world, station, necessary)
		record.resident_status = "Provisioned"
		record.resident_shortage = ""
		record.resident_alert_cycles = 0
