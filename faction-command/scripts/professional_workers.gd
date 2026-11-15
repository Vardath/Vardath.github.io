extends RefCounted
## Pass 35A: named, station-local professionals reserved from existing adults.
## Every professional is ALREADY counted in assigned_workers and licensed.
## Do not add these records to population totals or teleport them as ship crew.
## Named professional travel and other workplaces follow in later increments.

const VERSION := 1
const SALARY_INTERVAL := 60
const SALARY := 8
const XP_PER_SKILL := 25
const MAX_PROFESSIONALS := 10000
const WORK := {
	"engineering_college": {"role":"Engineer", "recipes":["alloy_smelting", "medical_synthesis", "media_fabrication", "water_recycling"]},
	"agriculture_institute": {"role":"Agricultural steward", "recipes":["hydroponics", "soil_agriculture"]}
}


func prepare(target: Dictionary) -> Error:
	if target.has("professional_version"):
		if int(target.professional_version) != VERSION or not target.get("professional_registry") is Dictionary or not target.get("professional_next_id") is int:
			return ERR_UNAVAILABLE
		return OK
	if target.has("professional_registry") or target.has("professional_next_id") or int(target.get("career_version", 0)) != 1:
		return ERR_INVALID_DATA
	target["professional_registry"] = {}
	target["professional_next_id"] = 1
	target["professional_version"] = VERSION
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
	if enabled and (not _has_workplace(station, str(worker.track))):
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


func report(world: RefCounted, station_id: String) -> Array[String]:
	var rows: Array[String] = ["PROFESSIONAL EMPLOYMENT · Live contracts from conserved certified adults"]
	for track in WORK:
		rows.append("%s: %d available practical graduate(s) · built workplace %s" % [WORK[track].role, available(world, station_id, track), "yes" if _has_workplace(world._find_station(station_id), track) else "no"])
	for worker in world.state.professional_registry.values():
		if str(worker.station_id) != station_id:
			continue
		rows.append("%s · %s · %s · skill %d/5 · %d genuine work cycles · salary %d CR/60 ticks · owing %d CR" % [worker.id, worker.role, "On duty" if worker.active else "Off duty", int(worker.skill), int(worker.work_events), SALARY, int(worker.salary_due) - int(worker.salary_paid)])
	return rows
