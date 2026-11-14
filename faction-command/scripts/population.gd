extends RefCounted
## First resident-population ledger: a counted source for NPC-station recruits.
## At this stage stations have NO buildable living quarters, birth cycles,
## immigration or adult graduation. Migrating an existing recruitment pool
## labels the *same* people as available residents; it does not seed a second
## population or manufacture a recruit. Legacy crew_pools is a checked mirror
## until all callers have migrated onto this API.

const VERSION := 1
const GROUPS := ["children", "students", "available_workers", "assigned_workers", "retirees"]
const MAX_STATIONS := 10000


func _cohort(station_id: String, existing_recruits: int) -> Dictionary:
	return {
		"id":"residents_" + station_id,
		"station_id":station_id,
		"cohorts":{
			"children":0,
			"students":0,
			"available_workers":existing_recruits,
			"assigned_workers":0,
			"retirees":0
		},
		"hab_capacity":0,
		"housing_status":"unimplemented"
	}


func prepare(target: Dictionary) -> Error:
	if target.has("population_version"):
		return OK if int(target.population_version) == VERSION and target.get("population") is Dictionary else ERR_UNAVAILABLE
	if target.has("population") or not target.get("crew_pools") is Dictionary:
		return ERR_INVALID_DATA
	var stations: Dictionary = {}
	# The original finite recruiters are explicitly the same residents, not
	# a second source of free people or a reset of an emptied roster.
	for station_id in target.crew_pools:
		if not station_id is String or str(station_id).is_empty() or stations.size() >= MAX_STATIONS:
			return ERR_INVALID_DATA
		stations[station_id] = _cohort(str(station_id), int(target.crew_pools[station_id]))
	# A newly constructed player station starts with zero residents. There is
	# no implied home habitat or unexplained population from construction.
	for station in target.get("stations", []):
		if not stations.has(station.id):
			if stations.size() >= MAX_STATIONS:
				return ERR_INVALID_DATA
			stations[station.id] = _cohort(str(station.id), 0)
	target["population"] = {"stations":stations}
	target["population_version"] = VERSION
	return OK


func register_station(world: RefCounted, station_id: String) -> void:
	if not world.state.has("population"):
		return
	if not world.state.population.stations.has(station_id):
		var record: Dictionary = _cohort(station_id, int(world.state.crew_pools.get(station_id, 0)))
		if world.state.has("habitation_version"):
			record.housing_status = "No habitat"
		world.state.population.stations[station_id] = record


func station_cohort(world: RefCounted, station_id: String) -> Dictionary:
	if not world.state.has("population"):
		return {}
	return world.state.population.stations.get(station_id, {})


func available_workers(world: RefCounted, station_id: String) -> int:
	var record: Dictionary = station_cohort(world, station_id)
	if record.is_empty():
		return 0
	return int(record.cohorts.available_workers)


func move_workers(world: RefCounted, station_id: String, delta: int) -> bool:
	# Positive delta returns staff to the source; negative delta places
	# real residents aboard a ship. No credit or demographic generation.
	var record: Dictionary = station_cohort(world, station_id)
	if record.is_empty() or not world.state.crew_pools.has(station_id):
		return false
	var present: int = int(record.cohorts.available_workers)
	if present != int(world.state.crew_pools[station_id]):
		return false
	if present + delta < 0 or present + delta > 1000000:
		return false
	record.cohorts.available_workers = present + delta
	world.state.crew_pools[station_id] = present + delta
	return true


func station_total(record: Dictionary) -> int:
	if record.is_empty():
		return 0
	var total := 0
	for group in GROUPS:
		total += int(record.cohorts.get(group, 0))
	return total


func total_people(world: RefCounted) -> int:
	if not world.state.has("population"):
		return 0
	var total := 0
	# crew_pools is a backwards-compatible mirror of available_workers; do
	# not sum it independently or count these people twice.
	for cohort in world.state.population.stations.values():
		total += station_total(cohort)
	for ship in world.state.ships:
		total += int(ship.crew) + 1 # Each existing ship has a named pilot.
		total += int(ship.get("settler_passengers", 0)) # In transit, no longer at their source.
	return total


func report(world: RefCounted) -> Array:
	var result: Array = []
	if not world.state.has("population"):
		return result
	for station_id in world.state.population.stations:
		var rec: Dictionary = world.state.population.stations[station_id]
		var station: Dictionary = world._find_station(str(station_id))
		result.append({
			"station_id":str(station_id),
			"name":str(station.get("name", station_id)),
			"owner":str(station.get("owner", "unavailable")),
			"sector":str(station.get("sector", "")),
			"known_residents":station_total(rec),
			"available":int(rec.cohorts.available_workers),
			"children":int(rec.cohorts.children),
			"students":int(rec.cohorts.students),
			"assigned":int(rec.cohorts.assigned_workers),
			"occupied_housing":int(rec.cohorts.assigned_workers),
			"available_beds":maxi(0, world.habitation.operational_capacity(station, world.state.habitation_catalog) - int(rec.cohorts.assigned_workers)) if not station.is_empty() else 0,
			"housing_deficit":maxi(0, int(rec.cohorts.assigned_workers) - world.habitation.operational_capacity(station, world.state.habitation_catalog)) if not station.is_empty() else int(rec.cohorts.assigned_workers),
			"resident_status":str(rec.get("resident_status", "Unoccupied")),
			"resident_shortage":str(rec.get("resident_shortage", "")),
			"resident_alert_cycles":int(rec.get("resident_alert_cycles", 0)),
			"retirees":int(rec.cohorts.retirees),
			"hab_capacity":int(rec.hab_capacity),
			"operational_capacity":world.habitation.operational_capacity(station, world.state.habitation_catalog) if not station.is_empty() else 0,
			"energy_per_60":world.habitation.maintenance_per_60(station, world.state.habitation_catalog) if not station.is_empty() else 0,
			"housing_status":str(rec.housing_status),
			"provisions_per_60":world.provisions.facility_needs(world, station) if not station.is_empty() else {},
			"provision_shortage":world.provisions.missing_provision(world, station) if not station.is_empty() else "",
			"active":not station.is_empty()
		})
	return result


func tick(world: RefCounted) -> void:
	# Register new facilities without seeding adults. Boarded adults may
	# relocate into existing housing; births and schooling are future passes.
	for station in world.state.stations:
		register_station(world, str(station.id))
