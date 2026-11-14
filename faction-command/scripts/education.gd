extends RefCounted
## Pass 33: staffed, physically built educational service modules.
## Residents do not multiply when appointed as instructors or students.
## Completion is an introductory civilian credential at the original station,
## NOT a free captain, military specialist or usable ship skill point.
## Each completed study period consumes real energy, archival data and money.

const DATA_PATH := "res://data/education.json"
const VERSION := 1
const INTERVAL := 60
const STUDENTS_PER_TEACHER := 4
const PROGRAM_IDS := [
	"community_school", "flight_academy", "engineering_college",
	"management_college", "research_academy", "marine_academy",
	"agriculture_institute"
]


func definitions() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not parsed is Dictionary or int(parsed.get("schema_version", -1)) != VERSION or int(parsed.get("service_interval", 0)) != INTERVAL or int(parsed.get("students_per_instructor", 0)) != STUDENTS_PER_TEACHER or not parsed.get("modules") is Array or parsed.modules.size() != PROGRAM_IDS.size():
		return {}
	var catalog: Dictionary = {}
	var blueprints: Dictionary = {}
	for entry in parsed.modules:
		if not entry is Dictionary or entry.get("id") not in PROGRAM_IDS or catalog.has(entry.id) or not entry.get("name") is String or entry.get("target") not in ["any", "adult"] or entry.get("material") not in ["recorded_data", "research_notes"]:
			return {}
		for key in ["seats", "course_ticks", "energy_per_60", "wage_per_60", "material_per_60"]:
			if int(entry.get(key, 0)) < 1:
				return {}
		if int(entry.course_ticks) % INTERVAL != 0 or int(entry.seats) > 32 or int(entry.material_per_60) > 4 or int(entry.wage_per_60) > 200:
			return {}
		if not entry.get("blueprint") is Dictionary:
			return {}
		var bill: Dictionary = entry.blueprint
		if int(bill.get("fee", 0)) < 1 or int(bill.get("ticks", 0)) < 1 or int(bill.get("storage", 0)) < 1 or not bill.get("materials") is Dictionary or int(bill.materials.get("alloy_plates", 0)) < 1 or int(bill.materials.get("energy_cells", 0)) < 1:
			return {}
		catalog[str(entry.id)] = {
			"id":str(entry.id), "name":str(entry.name), "target":str(entry.target),
			"seats":int(entry.seats), "course_ticks":int(entry.course_ticks),
			"energy_per_60":int(entry.energy_per_60), "wage_per_60":int(entry.wage_per_60),
			"material":str(entry.material), "material_per_60":int(entry.material_per_60)
		}
		blueprints[str(entry.id)] = {
			"fee":int(bill.fee), "ticks":int(bill.ticks), "storage":int(bill.storage),
			"materials":{"alloy_plates":int(bill.materials.alloy_plates), "energy_cells":int(bill.materials.energy_cells)}
		}
	if catalog.size() != PROGRAM_IDS.size() or catalog.community_school.target != "any":
		return {}
	for program_id in PROGRAM_IDS:
		if program_id != "community_school" and catalog[program_id].target != "adult":
			return {}
	return {"catalog":catalog, "blueprints":blueprints}


func initialize_station(station: Dictionary) -> void:
	var qualified: Dictionary = {}
	for program_id in PROGRAM_IDS:
		qualified[program_id] = 0
	station["education"] = {
		"modules":[], "teachers":0, "courses":{},
		"qualified":qualified, "youth_completed":0,
		"certificates_total":0, "payroll_credits":0
	}


func prepare(target: Dictionary) -> Error:
	if target.has("education_version"):
		return OK if int(target.education_version) == VERSION and target.get("education_catalog") is Dictionary else ERR_UNAVAILABLE
	if target.has("education_catalog") or target.get("demographics_version", 0) != 1 or not target.get("construction_blueprints") is Dictionary:
		return ERR_INVALID_DATA
	var source: Dictionary = definitions()
	if source.is_empty():
		return ERR_INVALID_DATA
	for program_id in PROGRAM_IDS:
		if target.construction_blueprints.has(program_id):
			return ERR_ALREADY_IN_USE
	for station in target.stations:
		if station.has("education"):
			return ERR_ALREADY_IN_USE
	for program_id in PROGRAM_IDS:
		target.construction_blueprints[program_id] = source.blueprints[program_id].duplicate(true)
	for station in target.stations:
		initialize_station(station)
	target["education_catalog"] = source.catalog.duplicate(true)
	target["education_version"] = VERSION
	return OK


func modules_at(station: Dictionary, program_id: String) -> int:
	if not station.has("education"):
		return 0
	return station.education.modules.count(program_id)


func on_commission(world: RefCounted, station_id: String, program_id: String) -> bool:
	var station: Dictionary = world._find_station(station_id)
	if station.is_empty() or station.owner != world.state.player_faction_id or not world.state.education_catalog.has(program_id) or not station.has("education"):
		return false
	station.education.modules.append(program_id)
	return true


func _active_adults(station: Dictionary) -> int:
	var total := 0
	for course in station.education.courses.values():
		if course.target == "adult":
			total += int(course.count)
	return total


func _active_youths(station: Dictionary) -> int:
	var total := 0
	for course in station.education.courses.values():
		if course.target == "youth":
			total += int(course.count)
	return total


func _teacher_load(station: Dictionary) -> int:
	var total := 0
	for course in station.education.courses.values():
		total += ceili(float(int(course.count)) / float(STUDENTS_PER_TEACHER))
	return total


func qualified_adults(station: Dictionary) -> int:
	var total := 0
	if not station.has("education"):
		return 0
	for quantity in station.education.qualified.values():
		total += int(quantity)
	return total


func available_for_relocation(world: RefCounted, station_id: String) -> int:
	var station: Dictionary = world._find_station(station_id)
	var rec: Dictionary = world.population.station_cohort(world, station_id)
	if station.is_empty() or rec.is_empty() or not station.has("education"):
		return 0
	var adults: int = int(rec.cohorts.assigned_workers)
	return maxi(0, adults - maxi(int(station.education.teachers), qualified_adults(station)) - _active_adults(station))


func appoint(world: RefCounted, station_id: String, count: int) -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var rec: Dictionary = world.population.station_cohort(world, station_id)
	if station.is_empty() or station.owner != world.state.player_faction_id or rec.is_empty() or not station.has("education"):
		return {"ok":false, "message":"Select a physically staffed player-owned residential school."}
	if count < 0 or count > int(rec.cohorts.assigned_workers) - _active_adults(station) or _teacher_load(station) > count:
		return {"ok":false, "message":"Appointed instructors must be real resident adults, not enrolled students or imaginary workers."}
	station.education.teachers = count
	return {"ok":true, "message":"%d existing resident adults are now appointed as teaching staff. Active classes pay real wages." % count}


func enroll(world: RefCounted, station_id: String, program_id: String, count: int, target: String = "adult") -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var rec: Dictionary = world.population.station_cohort(world, station_id)
	if station.is_empty() or station.owner != world.state.player_faction_id or rec.is_empty() or not station.has("education") or not world.state.education_catalog.has(program_id):
		return {"ok":false, "message":"Choose an owned, completed education facility."}
	var definition: Dictionary = world.state.education_catalog[program_id]
	if count < 1 or count > 1000 or modules_at(station, program_id) < 1 or station.education.courses.has(program_id):
		return {"ok":false, "message":"A physical classroom must have free places, and may run only one class per course at once."}
	if target not in ["adult", "youth"] or (target == "youth" and program_id != "community_school"):
		return {"ok":false, "message":"Only the community-school curriculum accepts school-age youths. Other tracks teach introductory adult theory."}
	var available: int = 0
	if target == "youth":
		available = int(rec.cohorts.students) - int(station.education.youth_completed) - _active_youths(station)
	else:
		available = available_for_relocation(world, station_id)
	if count > available or count > modules_at(station, program_id) * int(definition.seats):
		return {"ok":false, "message":"Not enough real unenrolled learners or built classroom seats."}
	var required_teachers: int = _teacher_load(station) + ceili(float(count) / float(STUDENTS_PER_TEACHER))
	if required_teachers > int(station.education.teachers):
		return {"ok":false, "message":"Appoint one resident adult instructor for every four learners in concurrent classes."}
	if world.demographics.residents(rec) > world.habitation.operational_capacity(station, world.state.habitation_catalog) or rec.resident_status != "Provisioned":
		return {"ok":false, "message":"Learners and instructors need powered, provisioned real housing before classes begin."}
	if program_id != "community_school" and int(station.education.qualified.get("community_school", 0)) < 1:
		return {"ok":false, "message":"Advanced theory needs a resident who first completed documented foundational education."}
	var min_material: int = ceili(float(count) / float(STUDENTS_PER_TEACHER)) * int(definition.material_per_60)
	var min_cost: int = ceili(float(count) / float(STUDENTS_PER_TEACHER)) * int(definition.wage_per_60)
	if int(station.stock.get(str(definition.material), 0)) < min_material or int(station.stock.get("energy_cells", 0)) < int(definition.energy_per_60) or int(world.state.starting_credits) < min_cost:
		return {"ok":false, "message":"Fund a first teaching cycle with physically stocked learning records, energy and actual instructor wages."}
	station.education.courses[program_id] = {"count":count, "target":target, "progress":0, "status":"Enrolled"}
	world._record_transaction("education_enrollment", "", station_id, "", count, 0, 0)
	return {"ok":true, "message":"Enrolled %d existing %s residents in %s. Their class requires physical records, power, teachers, wages and time." % [count, target, definition.name]}


func on_youth_mature(world: RefCounted, station: Dictionary, quantity: int) -> void:
	if not station.has("education") or quantity <= 0:
		return
	var class_state: Dictionary = station.education.courses.get("community_school", {})
	if not class_state.is_empty() and class_state.target == "youth":
		var remaining_youth: int = int(world.population.station_cohort(world, str(station.id)).cohorts.students)
		var eligible: int = maxi(0, remaining_youth - int(station.education.youth_completed))
		if int(class_state.count) > eligible:
			var removed: int = int(class_state.count) - eligible
			class_state.count = eligible
			if eligible == 0:
				station.education.courses.erase("community_school")
			world._record_transaction("education_age_exit", "", str(station.id), "", removed, 0, 0)
	var accredited: int = mini(quantity, int(station.education.youth_completed))
	if accredited > 0:
		station.education.youth_completed = int(station.education.youth_completed) - accredited
		station.education.qualified.community_school = int(station.education.qualified.community_school) + accredited


func tick(world: RefCounted) -> void:
	if int(world.state.get("education_version", 0)) != VERSION or int(world.state.tick) % INTERVAL != 0:
		return
	for station in world.state.stations:
		if not station.has("education") or station.education.courses.is_empty():
			continue
		var rec: Dictionary = world.population.station_cohort(world, str(station.id))
		var course_ids: Array = station.education.courses.keys()
		course_ids.sort()
		for program_id in course_ids:
			var course: Dictionary = station.education.courses[program_id]
			var definition: Dictionary = world.state.education_catalog[program_id]
			var teachers: int = ceili(float(int(course.count)) / float(STUDENTS_PER_TEACHER))
			var energy: int = int(definition.energy_per_60)
			var records: int = teachers * int(definition.material_per_60)
			var wages: int = teachers * int(definition.wage_per_60)
			var stop_reason := ""
			if rec.is_empty() or rec.resident_status != "Provisioned" or world.habitation.operational_capacity(station, world.state.habitation_catalog) < world.demographics.residents(rec):
				stop_reason = "Needs provisioned housing"
			elif _teacher_load(station) > int(station.education.teachers):
				stop_reason = "Needs resident instructors"
			elif int(station.stock.get("energy_cells", 0)) < energy:
				stop_reason = "Needs Energy Cells"
			elif int(station.stock.get(str(definition.material), 0)) < records:
				stop_reason = "Needs " + str(definition.material)
			elif int(world.state.starting_credits) < wages:
				stop_reason = "Needs salary credits"
			if not stop_reason.is_empty():
				course.status = stop_reason
				continue
			station.stock.energy_cells = int(station.stock.energy_cells) - energy
			station.stock[definition.material] = int(station.stock[definition.material]) - records
			world.state.starting_credits = int(world.state.starting_credits) - wages
			# No individual wallets exist yet: station credits are the resident
			# instructor payroll account. The faction loses exactly the same
			# funds the school account gains; there is no money creation.
			station.credits = int(station.credits) + wages
			station.education.payroll_credits = int(station.education.payroll_credits) + wages
			world._record_transaction("education_payroll", "", str(station.id), str(definition.material), records, wages, -wages)
			course.progress = int(course.progress) + INTERVAL
			course.status = "Studying"
			if int(course.progress) >= int(definition.course_ticks):
				var grads: int = int(course.count)
				if course.target == "youth":
					station.education.youth_completed = int(station.education.youth_completed) + grads
				else:
					station.education.qualified[program_id] = int(station.education.qualified[program_id]) + grads
				station.education.certificates_total = int(station.education.certificates_total) + grads
				station.education.courses.erase(program_id)
				world._record_transaction("education_completed", "", str(station.id), program_id, grads, 0, 0)


func report(world: RefCounted, station_id: String) -> Array[String]:
	var station: Dictionary = world._find_station(station_id)
	if station.is_empty() or not station.has("education"):
		return []
	var rows: Array[String] = []
	rows.append("Physically appointed resident instructors: %d · Total issued foundational certificates: %d · School payroll account: %d CR" % [int(station.education.teachers), int(station.education.certificates_total), int(station.education.payroll_credits)])
	rows.append("School-age youths with completed general education: %d" % int(station.education.youth_completed))
	for program_id in PROGRAM_IDS:
		var installed: int = modules_at(station, program_id)
		if installed == 0:
			continue
		var definition: Dictionary = world.state.education_catalog[program_id]
		var active: Dictionary = station.education.courses.get(program_id, {})
		var status: String = "Idle" if active.is_empty() else "%s · %d %s learners · %d/%d ticks" % [active.status, int(active.count), active.target, int(active.progress), int(definition.course_ticks)]
		rows.append("%s · %d classroom(s) · %d places each\n%s\nAdult foundation certificates: %d · Study cost / 60 ticks: %d energy, %d %s and %d CR per instructor-group" % [definition.name, installed, int(definition.seats), status, int(station.education.qualified[program_id]), int(definition.energy_per_60), int(definition.material_per_60), str(definition.material), int(definition.wage_per_60)])
	return rows
