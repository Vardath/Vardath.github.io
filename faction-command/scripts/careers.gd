extends RefCounted
## Pass 34: practical, paid workplace apprenticeship for EXISTING educated adults.
## It does not mint ship captains, crew skill, adults, equipment or resources.
## Practical certificates travel only with explicitly boarded civilian workers;
## never hide them in anonymous crew recruitment or delete them on evacuation.

const VERSION := 1
const SERVICE_INTERVAL := 60
const PRACTICUM_TICKS := 240
const PAY_PER_CYCLE := 18
const ENERGY_PER_CYCLE := 1
const RECORDS_PER_CYCLE := 1
const TRACKS := [
	"flight_academy", "engineering_college", "management_college",
	"research_academy", "marine_academy", "agriculture_institute"
]


func initialize_station(station: Dictionary) -> void:
	var licenses: Dictionary = {}
	for id in TRACKS:
		licenses[id] = 0
	station["careers"] = {"licensed":licenses, "apprenticeships":{}, "payroll_credits":0}


func initialize_ship(ship: Dictionary) -> void:
	ship["career_manifest"] = {}


func prepare(target: Dictionary) -> Error:
	if target.has("career_version"):
		return OK if int(target.career_version) == VERSION and target.get("career_catalog") is Dictionary else ERR_UNAVAILABLE
	if target.has("career_catalog") or int(target.get("education_version", 0)) != 1:
		return ERR_INVALID_DATA
	for station in target.stations:
		if station.has("careers"):
			return ERR_ALREADY_IN_USE
	for ship in target.ships:
		if ship.has("career_manifest"):
			return ERR_ALREADY_IN_USE
	for station in target.stations:
		initialize_station(station)
	for ship in target.ships:
		initialize_ship(ship)
	var catalog: Dictionary = {}
	for id in TRACKS:
		catalog[id] = {
			"name":str(target.education_catalog[id].name) + " — supervised practicum",
			"duration":PRACTICUM_TICKS,
			"energy_per_60":ENERGY_PER_CYCLE,
			"records_per_60":RECORDS_PER_CYCLE,
			"wages_per_60":PAY_PER_CYCLE,
			"prerequisite":id,
			"workplace":workplace_name(id)
		}
	target["career_catalog"] = catalog
	target["career_version"] = VERSION
	return OK


func workplace_name(track: String) -> String:
	match track:
		"flight_academy":
			return "a docked owned ship with an experienced real captain"
		"engineering_college":
			return "actual industrial production or docked ship maintenance with experienced crew"
		"management_college":
			return "an occupied, provisioned real residential station"
		"research_academy":
			return "a research laboratory operating on physical research records"
		"marine_academy":
			return "a docked owned vessel with experienced crew for noncombat safety drills"
		"agriculture_institute":
			return "actual food farming with completed production cycles"
	return ""


func _experienced_ship(world: RefCounted, station_id: String, captain: bool) -> bool:
	for ship in world.state.ships:
		if ship.owner != world.state.player_faction_id or ship.docked_at != station_id or not ship.orders.is_empty() or not ship.travel.is_empty():
			continue
		var profile: Dictionary = ship.get("captain_profile", {}) if captain else ship.get("crew_profile", {})
		if int(profile.get("skill", 0)) >= 1 and (captain or int(ship.crew) >= 1):
			return true
	return false


func _work_cycles(station: Dictionary, ids: Array) -> int:
	var total := 0
	for module in station.production:
		if module.recipe_id in ids:
			total += int(module.cycles)
	return total


func _workplace(world: RefCounted, station: Dictionary, track: String) -> bool:
	match track:
		"flight_academy":
			return _experienced_ship(world, str(station.id), true)
		"engineering_college":
			return _work_cycles(station, ["alloy_smelting", "medical_synthesis", "media_fabrication", "water_recycling"]) > 0 or _experienced_ship(world, str(station.id), false)
		"management_college":
			return not station.habitation.is_empty() and int(world.population.station_cohort(world, str(station.id)).cohorts.assigned_workers) >= 2
		"research_academy":
			return world.research.has_lab(station) and _work_cycles(station, ["research_laboratory"]) > 0
		"marine_academy":
			return _experienced_ship(world, str(station.id), false)
		"agriculture_institute":
			return _work_cycles(station, ["hydroponics", "soil_agriculture"]) > 0
	return false


func _material(track: String) -> String:
	return "research_notes" if track == "research_academy" else "recorded_data"


func _active_count(station: Dictionary) -> int:
	var total := 0
	for study in station.careers.apprenticeships.values():
		total += int(study.count)
	return total


func candidates(world: RefCounted, station_id: String, track: String) -> int:
	var station: Dictionary = world._find_station(station_id)
	if station.is_empty() or not station.has("careers") or track not in TRACKS:
		return 0
	var holding: int = int(station.education.qualified.get(track, 0))
	var certified: int = int(station.careers.licensed.get(track, 0))
	var assigned: int = int(station.careers.apprenticeships.get(track, {}).get("count", 0))
	return maxi(0, holding - certified - assigned)


func start(world: RefCounted, station_id: String, track: String, quantity: int = 1) -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var record: Dictionary = world.population.station_cohort(world, station_id)
	if station.is_empty() or station.owner != world.state.player_faction_id or record.is_empty() or not station.has("careers") or track not in TRACKS:
		return {"ok":false, "message":"Choose an owned station with an existing qualified adult and real supervised workplace."}
	if quantity < 1 or quantity > 100 or station.careers.apprenticeships.has(track) or candidates(world, station_id, track) < quantity:
		return {"ok":false, "message":"Each practicum needs a distinct existing adult foundation graduate who is not already certified or in this course."}
	if int(station.education.teachers) < 1 or int(record.cohorts.assigned_workers) < 2 or not station.education.courses.is_empty():
		return {"ok":false, "message":"A resident mentor and separate foundation graduate are required; finish concurrent classroom lessons first."}
	if int(record.cohorts.assigned_workers) - int(station.education.teachers) < quantity + _active_count(station):
		return {"ok":false, "message":"Keep working-age trainees separate from actually appointed adult mentors."}
	if record.resident_status != "Provisioned" or world.habitation.operational_capacity(station, world.state.habitation_catalog) < world.demographics.residents(record):
		return {"ok":false, "message":"Both mentor and apprentice need live powered and provisioned residence."}
	if not _workplace(world, station, track):
		return {"ok":false, "message":"Missing practical workplace: " + workplace_name(track)}
	var ware_id: String = _material(track)
	if int(station.stock.get("energy_cells", 0)) < ENERGY_PER_CYCLE or int(station.stock.get(ware_id, 0)) < RECORDS_PER_CYCLE or int(world.state.starting_credits) < PAY_PER_CYCLE:
		return {"ok":false, "message":"An actual on-site work record, energy and first-cycle wages must be available."}
	station.careers.apprenticeships[track] = {"count":quantity, "progress":0, "status":"Enrolled"}
	world._record_transaction("career_apprenticeship_start", "", station_id, track, quantity, 0, 0)
	return {"ok":true, "message":"%d existing foundation graduate(s) assigned to paid supervised %s practice. No ship licence or skill is granted in advance." % [quantity, track]}


func tick(world: RefCounted) -> void:
	if int(world.state.get("career_version", 0)) != VERSION or int(world.state.tick) % SERVICE_INTERVAL != 0:
		return
	for station in world.state.stations:
		if not station.has("careers") or station.careers.apprenticeships.is_empty():
			continue
		var cohort: Dictionary = world.population.station_cohort(world, str(station.id))
		var ordered: Array = station.careers.apprenticeships.keys()
		ordered.sort()
		for track in ordered:
			var stage: Dictionary = station.careers.apprenticeships[track]
			var reason := ""
			if cohort.is_empty() or cohort.resident_status != "Provisioned" or world.habitation.operational_capacity(station, world.state.habitation_catalog) < world.demographics.residents(cohort):
				reason = "Needs provisioned residents"
			elif int(station.education.teachers) < 1 or int(cohort.cohorts.assigned_workers) < int(station.education.teachers) + _active_count(station):
				reason = "Needs real adult mentor"
			elif not _workplace(world, station, str(track)):
				reason = "Needs working practice facility"
			elif int(station.stock.get("energy_cells", 0)) < ENERGY_PER_CYCLE:
				reason = "Needs Energy Cells"
			elif int(station.stock.get(_material(str(track)), 0)) < RECORDS_PER_CYCLE:
				reason = "Needs " + _material(str(track))
			elif int(world.state.starting_credits) < PAY_PER_CYCLE:
				reason = "Needs salaries"
			if not reason.is_empty():
				stage.status = reason
				continue
			var input_id := _material(str(track))
			station.stock.energy_cells = int(station.stock.energy_cells) - ENERGY_PER_CYCLE
			station.stock[input_id] = int(station.stock[input_id]) - RECORDS_PER_CYCLE
			world.state.starting_credits = int(world.state.starting_credits) - PAY_PER_CYCLE
			station.credits = int(station.credits) + PAY_PER_CYCLE
			station.careers.payroll_credits = int(station.careers.payroll_credits) + PAY_PER_CYCLE
			world._record_transaction("career_practicum_payroll", "", str(station.id), input_id, RECORDS_PER_CYCLE, PAY_PER_CYCLE, -PAY_PER_CYCLE)
			stage.progress = int(stage.progress) + SERVICE_INTERVAL
			stage.status = "Supervised work"
			if int(stage.progress) >= PRACTICUM_TICKS:
				var quantity: int = int(stage.count)
				station.careers.licensed[track] = int(station.careers.licensed[track]) + quantity
				station.careers.apprenticeships.erase(track)
				world._record_transaction("career_practicum_complete", "", str(station.id), str(track), quantity, 0, 0)


func board_qualified(world: RefCounted, ship_id: String, track: String, quantity: int, certified: bool) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = world.settlement._docked(world, ship)
	if station.is_empty() or station.owner != world.state.player_faction_id or track not in world.state.education_catalog or not station.has("careers"):
		return {"ok":false, "message":"Dock a player ship at an owned station with genuine foundation graduates."}
	if quantity < 1 or quantity > 100 or not ship.get("career_manifest", {}).is_empty() or int(ship.settler_passengers) != 0 or quantity > world.settlement.free_berths(world, ship):
		return {"ok":false, "message":"Choose vacant real berths; do not mix qualified people with an existing passenger manifest."}
	var record: Dictionary = world.population.station_cohort(world, str(station.id))
	var already: int = int(station.education.qualified.get(track, 0))
	var licensed: int = int(station.careers.licensed.get(track, 0))
	if already < quantity or (certified and licensed < quantity) or (not certified and already - licensed < quantity):
		return {"ok":false, "message":"The departing adults must already hold the selected genuine local theory and practical records."}
	if int(record.cohorts.assigned_workers) - quantity < int(station.education.teachers) + world.education._active_adults(station) + _active_count(station):
		return {"ok":false, "message":"Do not leave enrolled students, mentors or practical trainees without their own remaining adults."}
	var dependent: int = int(record.cohorts.children) + int(record.cohorts.students)
	if (int(record.cohorts.assigned_workers) - quantity) * 2 < dependent:
		return {"ok":false, "message":"Leave enough physical adult caretakers for children and school-age youths."}
	station.education.qualified[track] = already - quantity
	station.education.certificates_total = int(station.education.certificates_total) - quantity
	if certified:
		station.careers.licensed[track] = licensed - quantity
	record.cohorts.assigned_workers = int(record.cohorts.assigned_workers) - quantity
	ship.settler_passengers = quantity
	ship.settler_source_station_id = str(station.id)
	ship.career_manifest = {"track":track, "quantity":quantity, "certified":certified}
	if world.demographics.residents(record) == 0:
		world.settlement._initialize_welfare(record)
	world._record_transaction("career_transfer_departure", ship_id, str(station.id), track, quantity, 1 if certified else 0, 0)
	return {"ok":true, "message":"%d existing %s graduates physically boarded with their %s qualification records. No other source may board until delivery." % [quantity, track, "practical" if certified else "foundation"]}


func settle_qualified(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var destination: Dictionary = world.settlement._docked(world, ship)
	var manifest: Dictionary = ship.get("career_manifest", {})
	if destination.is_empty() or destination.owner != world.state.player_faction_id or manifest.is_empty() or quantity < 1 or quantity > int(manifest.quantity) or int(ship.settler_passengers) != int(manifest.quantity):
		return {"ok":false, "message":"Dock with your existing qualified passengers at a genuinely powered player residence."}
	var rec: Dictionary = world.population.station_cohort(world, str(destination.id))
	var adults: int = int(rec.cohorts.assigned_workers)
	var residents: int = world.demographics.residents(rec)
	var capacity: int = world.habitation.operational_capacity(destination, world.state.habitation_catalog)
	if residents + quantity > capacity or residents + quantity > 1000000:
		return {"ok":false, "message":"All certified passengers need actual vacant powered residential berths."}
	var missing: String = world.provisions.missing_provision(world, destination, residents + quantity)
	if not missing.is_empty():
		return {"ok":false, "message":"New qualified residents need next-cycle " + missing + " before admission."}
	var track: String = str(manifest.track)
	destination.education.qualified[track] = int(destination.education.qualified[track]) + quantity
	destination.education.certificates_total = int(destination.education.certificates_total) + quantity
	if bool(manifest.certified):
		destination.careers.licensed[track] = int(destination.careers.licensed[track]) + quantity
	rec.cohorts.assigned_workers = adults + quantity
	rec.resident_status = "Awaiting service"
	rec.resident_shortage = ""
	rec.resident_alert_cycles = 0
	world._record_transaction("career_transfer_arrival", ship_id, str(destination.id), track, quantity, 1 if bool(manifest.certified) else 0, 0)
	world.settlement._clear_manifest(ship, quantity)
	manifest.quantity = int(manifest.quantity) - quantity
	if int(manifest.quantity) == 0:
		ship.career_manifest = {}
	return {"ok":true, "message":"%d actual %s residents disembarked with their original %s credentials; original course and practical achievements remain recorded." % [quantity, track, "practical" if bool(manifest.certified) else "foundation"]}


func report(world: RefCounted, station_id: String) -> Array[String]:
	var station: Dictionary = world._find_station(station_id)
	if station.is_empty() or not station.has("careers"):
		return []
	var rows: Array[String] = []
	rows.append("PRACTICAL WORK EXPERIENCE · Paid workplace mentoring account: %d CR" % int(station.careers.payroll_credits))
	for track in TRACKS:
		var certs: int = int(station.careers.licensed[track])
		var stage: Dictionary = station.careers.apprenticeships.get(track, {})
		var formatted := "not enrolled" if stage.is_empty() else ("%s · %d actual apprentices · %d/%d ticks" % [stage.status, int(stage.count), int(stage.progress), PRACTICUM_TICKS])
		rows.append("%s: %d local practical attestations, %d available theory-trained candidates\n%s; needs %s, 1 physical study record + 1 energy + %d CR per 60 ticks" % [str(world.state.education_catalog[track].name), certs, candidates(world, station_id, track), formatted, workplace_name(track), PAY_PER_CYCLE])
	return rows
