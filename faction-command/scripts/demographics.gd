extends RefCounted
## Pass 32: counted family cohorts, real births and biological maturation.
## An existing pair of settled adults in an operational Family Habitat can
## support a child ONLY after continuous provisioned housing, an available
## real bed, and an extra debit of medical supplies. Children grow into
## school-age youths, then biologically mature into UNSKILLED resident adults.
## No crew, money, factory stock, job skills, ships or NPC workforce is created.

const VERSION := 1
const BIRTH_INTERVAL := 600
const CHILDHOOD_TICKS := 3600
const YOUTH_TICKS := 3600
const SERVICE_INTERVAL := 60
const MAX_GROUP := 1000000


func initialize_record(record: Dictionary) -> void:
	record["family"] = {
		"birth_progress":0,
		"births_total":0,
		"grown_total":0,
		"child_queue":[],
		"youth_queue":[]
	}


func prepare(target: Dictionary) -> Error:
	if target.has("demographics_version"):
		return OK if int(target.demographics_version) == VERSION else ERR_UNAVAILABLE
	if target.has("demographics_catalog") or not target.has("ecology_version") or int(target.get("settlement_version", 0)) != 2 or not target.has("population"):
		return ERR_INVALID_DATA
	for record in target.population.stations.values():
		if record.has("family"):
			return ERR_INVALID_DATA
		initialize_record(record)
	target["demographics_version"] = VERSION
	target["demographics_catalog"] = {
		"birth_interval":BIRTH_INTERVAL,
		"childhood_ticks":CHILDHOOD_TICKS,
		"youth_ticks":YOUTH_TICKS,
		"birth_medical_cost":1
	}
	return OK


func known_households(world: RefCounted, station: Dictionary, adults: int) -> int:
	# Coarse households: two eligible resident adults per household, limited
	# by physical *operational* Family Habitat beds. No species assumptions
	# or individual partner identity is invented at this stage.
	if station.is_empty() or station.owner != world.state.player_faction_id:
		return 0
	var family_beds := 0
	for home in station.get("habitation", []):
		if str(home.id) == "family_habitat" and bool(home.powered):
			family_beds += int(world.state.habitation_catalog.family_habitat.capacity)
	return mini(int(adults / 2), int(family_beds / 2))


func residents(record: Dictionary) -> int:
	if record.is_empty():
		return 0
	var cohort: Dictionary = record.cohorts
	return int(cohort.assigned_workers) + int(cohort.children) + int(cohort.students) + int(cohort.retirees)


func _advance_cohort(record: Dictionary, name: String, target_name: String, next_name: String, duration: int, tick_now: int) -> int:
	var moved := 0
	var queue: Array = record.family[name]
	while not queue.is_empty() and int(queue[0].ready_tick) <= tick_now:
		var batch: Dictionary = queue.pop_front()
		var amount: int = int(batch.quantity)
		record.cohorts[target_name] = int(record.cohorts[target_name]) - amount
		record.cohorts[next_name] = int(record.cohorts[next_name]) + amount
		moved += amount
		if name == "child_queue":
			record.family.youth_queue.append({"quantity":amount, "ready_tick":tick_now + YOUTH_TICKS})
	return moved


func tick(world: RefCounted) -> void:
	if int(world.state.get("demographics_version", 0)) != VERSION or int(world.state.tick) % SERVICE_INTERVAL != 0:
		return
	for station in world.state.stations:
		var record: Dictionary = world.population.station_cohort(world, str(station.id))
		if record.is_empty() or not record.has("family"):
			continue
		var births: int = 0
		var child_to_youth: int = _advance_cohort(record, "child_queue", "children", "students", CHILDHOOD_TICKS, int(world.state.tick))
		var youth_to_adult: int = _advance_cohort(record, "youth_queue", "students", "assigned_workers", YOUTH_TICKS, int(world.state.tick))
		if youth_to_adult > 0:
			if world.state.has("education_version"):
				world.education.on_youth_mature(world, station, youth_to_adult)
			record.family.grown_total = int(record.family.grown_total) + youth_to_adult
			world._record_transaction("resident_maturity", "", str(station.id), "", youth_to_adult, 0, 0)
		if child_to_youth > 0:
			world._record_transaction("resident_youth", "", str(station.id), "", child_to_youth, 0, 0)
		var adults: int = int(record.cohorts.assigned_workers)
		var households: int = known_households(world, station, adults)
		if households == 0 or record.resident_status != "Provisioned" or int(record.resident_alert_cycles) > 0:
			# Continuous family stability is required; drought/power loss
			# resets birth eligibility, but never deletes existing children.
			record.family.birth_progress = 0
			continue
		record.family.birth_progress = mini(BIRTH_INTERVAL, int(record.family.birth_progress) + SERVICE_INTERVAL)
		if int(record.family.birth_progress) < BIRTH_INTERVAL:
			continue
		var powered_beds: int = world.habitation.operational_capacity(station, world.state.habitation_catalog)
		var free_beds: int = maxi(0, powered_beds - residents(record))
		# Each newborn needs a real powered bed and one separately paid
		# medical kit for birth care. No birth occurs if either is absent.
		var dependents: int = int(record.cohorts.children) + int(record.cohorts.students)
		var care_capacity: int = maxi(0, adults * 2 - dependents)
		births = mini(households, mini(free_beds, mini(care_capacity, int(station.stock.get("medical_supplies", 0)))))
		if births <= 0:
			continue
		station.stock.medical_supplies = int(station.stock.medical_supplies) - births
		record.cohorts.children = int(record.cohorts.children) + births
		record.family.child_queue.append({"quantity":births, "ready_tick":int(world.state.tick) + CHILDHOOD_TICKS})
		record.family.births_total = int(record.family.births_total) + births
		record.family.birth_progress = 0
		world._record_transaction("resident_birth", "", str(station.id), "medical_supplies", births, 0, 0)
