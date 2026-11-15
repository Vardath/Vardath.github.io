extends RefCounted
## Pass 35B: conserved certified adults can travel as identifiable ship passengers.
## While settled they are ALREADY counted in a resident adult cohort and local
## theory/practical licences. While aboard they occupy ONE existing berth, are
## removed from the station cohort, and retain their stable employment history.

const VERSION := 1
const TRANSPORT_VERSION := 1
const SALARY_INTERVAL := 60
const SALARY := 8
const XP_PER_SKILL := 25
const MAX_PROFESSIONALS := 10000
const WORK := {
	"engineering_college": {"role":"Engineer", "recipes":["alloy_smelting", "medical_synthesis", "media_fabrication", "water_recycling"]},
	"agriculture_institute": {"role":"Agricultural steward", "recipes":["hydroponics", "soil_agriculture"]}
}


func initialize_ship(ship: Dictionary) -> void:
	ship["professional_passenger_id"] = ""


func prepare(target: Dictionary) -> Error:
	if target.has("professional_version"):
		if int(target.professional_version) != VERSION or not target.get("professional_registry") is Dictionary or not target.get("professional_next_id") is int:
			return ERR_UNAVAILABLE
	elif target.has("professional_registry") or target.has("professional_next_id") or int(target.get("career_version", 0)) != 1:
		return ERR_INVALID_DATA
	else:
		target["professional_registry"] = {}
		target["professional_next_id"] = 1
		target["professional_version"] = VERSION
	if target.has("professional_transport_version"):
		if int(target.professional_transport_version) != TRANSPORT_VERSION:
			return ERR_UNAVAILABLE
		for ship in target.ships:
			if not ship.get("professional_passenger_id") is String:
				return ERR_INVALID_DATA
		return OK
	for ship in target.ships:
		if ship.has("professional_passenger_id"):
			return ERR_ALREADY_IN_USE
	for ship in target.ships:
		initialize_ship(ship)
	target["professional_transport_version"] = TRANSPORT_VERSION
	return OK


func _local_count(world: RefCounted, station_id: String, track: String) -> int:
	var count := 0
	for worker in world.state.professional_registry.values():
		if worker.station_id == station_id and worker.track == track:
			count += 1
	return count


func available(world: RefCounted, station_id: String, track: String) -> int:
	var station: Dictionary = world._find_station(station_id)
	if station.is_empty() or not station.has("careers") or not WORK.has(track):
		return 0
	return maxi(0, int(station.careers.licensed.get(track, 0)) - _local_count(world, station_id, track))


func _has_workplace(station: Dictionary, track: String) -> bool:
	if not WORK.has(track):
		return false
	for module in station.get("production", []):
		if str(module.recipe_id) in WORK[track].recipes:
			return true
	return false


func appoint(world: RefCounted, station_id: String, track: String) -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var cohort: Dictionary = world.population.station_cohort(world, station_id)
	if station.is_empty() or station.owner != world.state.player_faction_id or cohort.is_empty() or not WORK.has(track):
		return {"ok":false, "message":"Choose an owned station and an implemented professional workplace."}
	if int(world.state.professional_next_id) > MAX_PROFESSIONALS or available(world, station_id, track) < 1:
		return {"ok":false, "message":"No unassigned, real practical graduate is available for that position."}
	if _local_count(world, station_id, track) != 0:
		return {"ok":false, "message":"This initial workplace can employ one identified specialist per profession."}
	if not _has_workplace(station, track) or cohort.resident_status != "Provisioned" or world.habitation.operational_capacity(station, world.state.habitation_catalog) < world.demographics.residents(cohort):
		return {"ok":false, "message":"A built working module and provisioned, powered resident housing are required."}
	var number: int = int(world.state.professional_next_id)
	var id := "professional_%d" % number
	if world.state.professional_registry.has(id):
		return {"ok":false, "message":"The next professional identifier is already occupied."}
	world.state.professional_next_id = number + 1
	world.state.professional_registry[id] = {
		"id":id, "station_id":station_id, "track":track, "role":WORK[track].role,
		"active":true, "experience":0, "skill":0, "work_events":0,
		"salary_due":0, "salary_paid":0, "last_salary_tick":int(world.state.tick),
		"status":"Awaiting completed work"
	}
	world._record_transaction("professional_appoint", str(track), station_id, id, 1, 0, 0)
	return {"ok":true, "message":"Assigned existing certified %s %s to genuine %s production. The adult and qualification were already counted." % [id, WORK[track].role, station.name], "id":id}


func set_active(world: RefCounted, worker_id: String, enabled: bool) -> Dictionary:
	var worker: Dictionary = world.state.professional_registry.get(worker_id, {})
	if worker.is_empty():
		return {"ok":false, "message":"No named professional with that ID."}
	if bool(worker.active) == enabled:
		return {"ok":false, "message":"This professional already has that employment status."}
	var station: Dictionary = world._find_station(str(worker.station_id))
	if station.is_empty() or station.owner != world.state.player_faction_id:
		return {"ok":false, "message":"The employing station is unavailable."}
	if enabled and not _has_workplace(station, str(worker.track)):
		return {"ok":false, "message":"This profession needs its genuine existing workstation."}
	worker.active = enabled
	worker.last_salary_tick = int(world.state.tick)
	worker.status = "Awaiting completed work" if enabled else "Off duty"
	world._record_transaction("professional_assign" if enabled else "professional_unassign", str(worker.track), str(worker.station_id), worker_id, 1, 0, 0)
	return {"ok":true, "message":"%s is now %s; skill, identity and earned wages remain with the same adult." % [worker_id, "on duty" if enabled else "off duty"]}


func record_production(world: RefCounted, station: Dictionary, recipe_id: String) -> void:
	if int(world.state.get("professional_version", 0)) != VERSION or station.owner != world.state.player_faction_id:
		return
	var ids: Array = world.state.professional_registry.keys()
	ids.sort()
	for id in ids:
		var worker: Dictionary = world.state.professional_registry[id]
		if str(worker.station_id) != str(station.id) or not worker.active or recipe_id not in WORK[str(worker.track)].recipes:
			continue
		var cohort: Dictionary = world.population.station_cohort(world, str(station.id))
		if cohort.is_empty() or cohort.resident_status != "Provisioned" or int(worker.salary_due) != int(worker.salary_paid):
			continue
		worker.work_events = int(worker.work_events) + 1
		worker.experience = int(worker.experience) + 1
		worker.skill = mini(5, int(int(worker.experience) / XP_PER_SKILL))
		worker.status = "Working"
		world._record_transaction("professional_work", recipe_id, str(station.id), str(id), 1, 0, 0)
		return


func tick(world: RefCounted) -> void:
	if int(world.state.get("professional_version", 0)) != VERSION:
		return
	var ids: Array = world.state.professional_registry.keys()
	ids.sort()
	for id in ids:
		var worker: Dictionary = world.state.professional_registry[id]
		if not worker.active or int(world.state.tick) - int(worker.last_salary_tick) < SALARY_INTERVAL:
			continue
		var station: Dictionary = world._find_station(str(worker.station_id))
		worker.last_salary_tick = int(worker.last_salary_tick) + SALARY_INTERVAL
		worker.salary_due = int(worker.salary_due) + SALARY
		world._record_transaction("professional_due", str(worker.track), str(worker.station_id), str(id), 1, SALARY, 0)
		var debt: int = int(worker.salary_due) - int(worker.salary_paid)
		if station.is_empty() or int(world.state.starting_credits) < debt:
			worker.status = "Salary in arrears"
			continue
		world.state.starting_credits = int(world.state.starting_credits) - debt
		station.credits = int(station.credits) + debt
		worker.salary_paid = int(worker.salary_paid) + debt
		world._record_transaction("professional_payroll", str(worker.track), str(station.id), str(id), 1, debt, -debt)
		if worker.status == "Salary in arrears":
			worker.status = "Awaiting completed work"



## A professional is OFF the station payroll while in transit. Boarding an
## active employee creates an explicit duty-termination event first.
func board_named(world: RefCounted, ship_id: String, worker_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var origin: Dictionary = world.settlement._docked(world, ship)
	var worker: Dictionary = world.state.professional_registry.get(worker_id, {})
	if origin.is_empty() or origin.owner != world.state.player_faction_id or worker.is_empty() or worker.station_id != origin.id:
		return {"ok":false, "message":"Dock an owned ship at the real professional's current residential station."}
	if int(ship.settler_passengers) != 0 or not ship.get("career_manifest", {}).is_empty() or not str(ship.get("professional_passenger_id", "")).is_empty() or world.settlement.free_berths(world, ship) < 1:
		return {"ok":false, "message":"The ship needs an unused physical passenger berth and no other civilian manifest."}
	var cohort: Dictionary = world.population.station_cohort(world, str(origin.id))
	if cohort.is_empty() or int(cohort.cohorts.assigned_workers) < 1 or int(origin.education.qualified.get(worker.track, 0)) < 1 or int(origin.careers.licensed.get(worker.track, 0)) < 1:
		return {"ok":false, "message":"The source must have that already counted adult and both earned qualifications."}
	var remaining: int = int(cohort.cohorts.assigned_workers) - 1
	if remaining < int(origin.education.teachers) + world.education._active_adults(origin) + world.careers._active_count(origin):
		return {"ok":false, "message":"Current teachers, students and apprentices need their own resident adults."}
	var children: int = int(cohort.cohorts.children) + int(cohort.cohorts.students)
	if remaining * 2 < children:
		return {"ok":false, "message":"Dependent children must retain enough resident adult caregivers."}
	if bool(worker.active):
		worker.active = false
		worker.last_salary_tick = int(world.state.tick)
		world._record_transaction("professional_unassign", str(worker.track), str(origin.id), worker_id, 1, 0, 0)
	origin.education.qualified[worker.track] = int(origin.education.qualified[worker.track]) - 1
	origin.education.certificates_total = int(origin.education.certificates_total) - 1
	origin.careers.licensed[worker.track] = int(origin.careers.licensed[worker.track]) - 1
	cohort.cohorts.assigned_workers = remaining
	if world.demographics.residents(cohort) == 0:
		world.settlement._initialize_welfare(cohort)
	ship.settler_passengers = 1
	ship.settler_source_station_id = str(origin.id)
	ship.professional_passenger_id = worker_id
	worker.station_id = ""
	worker.status = "In transit"
	worker.last_salary_tick = int(world.state.tick)
	world._record_transaction("career_transfer_departure", ship_id, str(origin.id), str(worker.track), 1, 1, 0)
	world._record_transaction("professional_board", ship_id, str(origin.id), worker_id, 1, 0, 0)
	return {"ok":true, "message":"%s boarded %s as one named certified passenger. Existing skills, qualifications and wage debt travel unchanged." % [worker_id, ship.name]}


func disembark_named(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var destination: Dictionary = world.settlement._docked(world, ship)
	var worker_id: String = str(ship.get("professional_passenger_id", ""))
	var worker: Dictionary = world.state.professional_registry.get(worker_id, {})
	if destination.is_empty() or destination.owner != world.state.player_faction_id or quantity != 1 or worker.is_empty() or not str(worker.station_id).is_empty() or int(ship.settler_passengers) != 1:
		return {"ok":false, "message":"Dock the ship with its one documented professional at a supplied owned residence."}
	var cohort: Dictionary = world.population.station_cohort(world, str(destination.id))
	if cohort.is_empty() or _local_count(world, str(destination.id), str(worker.track)) > 0:
		return {"ok":false, "message":"The receiving station has no compatible free professional post or resident ledger."}
	var occupied: int = world.demographics.residents(cohort)
	if world.habitation.operational_capacity(destination, world.state.habitation_catalog) < occupied + 1:
		return {"ok":false, "message":"The professional needs a real available powered residential berth."}
	var missing: String = world.provisions.missing_provision(world, destination, occupied + 1)
	if not missing.is_empty():
		return {"ok":false, "message":"The destination needs physical " + missing + " for the next resident service."}
	if int(cohort.cohorts.assigned_workers) >= 1000000:
		return {"ok":false, "message":"The destination workforce register is full."}
	destination.education.qualified[worker.track] = int(destination.education.qualified[worker.track]) + 1
	destination.education.certificates_total = int(destination.education.certificates_total) + 1
	destination.careers.licensed[worker.track] = int(destination.careers.licensed[worker.track]) + 1
	cohort.cohorts.assigned_workers = int(cohort.cohorts.assigned_workers) + 1
	cohort.resident_status = "Awaiting service"
	cohort.resident_shortage = ""
	cohort.resident_alert_cycles = 0
	worker.station_id = str(destination.id)
	worker.active = false
	worker.status = "Off duty"
	worker.last_salary_tick = int(world.state.tick)
	world._record_transaction("career_transfer_arrival", ship_id, str(destination.id), str(worker.track), 1, 1, 0)
	world._record_transaction("professional_arrive", ship_id, str(destination.id), worker_id, 1, 0, 0)
	world.settlement._clear_manifest(ship, 1)
	ship.professional_passenger_id = ""
	return {"ok":true, "message":"%s settled at %s with exactly the original identity, practicum, work XP and wage history. Start an actual local job separately." % [worker_id, destination.name]}


func passenger_report(world: RefCounted, ship: Dictionary) -> String:
	var id: String = str(ship.get("professional_passenger_id", ""))
	if id.is_empty():
		return ""
	var person: Dictionary = world.state.professional_registry.get(id, {})
	if person.is_empty():
		return ""
	return "NAMED PROFESSIONAL PASSENGER: %s · %s · skill %d/5 · %d genuine work cycles · unpaid salary %d CR. One physical passenger berth; disembark at a powered and stocked player residence." % [id, person.role, int(person.skill), int(person.work_events), int(person.salary_due) - int(person.salary_paid)]


func report(world: RefCounted, station_id: String) -> Array[String]:
	var rows: Array[String] = ["PROFESSIONAL EMPLOYMENT · Live contracts from conserved certified adults"]
	for track in WORK:
		rows.append("%s: %d available practical graduate(s) · built workplace %s" % [WORK[track].role, available(world, station_id, track), "yes" if _has_workplace(world._find_station(station_id), track) else "no"])
	for worker in world.state.professional_registry.values():
		if str(worker.station_id) != station_id:
			continue
		rows.append("%s · %s · %s · skill %d/5 · %d genuine work cycles · salary %d CR/60 ticks · owing %d CR" % [worker.id, worker.role, "On duty" if worker.active else "Off duty", int(worker.skill), int(worker.work_events), SALARY, int(worker.salary_due) - int(worker.salary_paid)])
	return rows
