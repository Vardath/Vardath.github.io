extends RefCounted
## One local save slot. A verified temporary file replaces the primary only
## after the previous valid primary has been retained as a backup.

const FORMAT_VERSION := 1
const MAX_SAVE_BYTES := 64 * 1024 * 1024
const ArchivesScript = preload("res://scripts/archives.gd")
const ResearchScript = preload("res://scripts/research.gd")
const ProvisionsScript = preload("res://scripts/provisions.gd")
const EcologyScript = preload("res://scripts/ecology.gd")
const DemographicsScript = preload("res://scripts/demographics.gd")
const EducationScript = preload("res://scripts/education.gd")
const CareersScript = preload("res://scripts/careers.gd")
const PersonnelScript = preload("res://scripts/personnel.gd")


func has_any_save(path: String) -> bool:
	return FileAccess.file_exists(path) or FileAccess.file_exists(path + ".bak")


func save_game(path: String, state: Dictionary) -> Error:
	if not _valid_world(state):
		return ERR_INVALID_DATA
	# Preserve exact numeric types and values. Objects are never serialized.
	var payload := Marshalls.variant_to_base64(state, false)
	var envelope := {"format_version": FORMAT_VERSION, "checksum": payload.sha256_text(), "payload": payload}
	var temporary := path + ".tmp"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(envelope))
	file.flush()
	var write_error := file.get_error()
	file.close()
	if write_error != OK:
		return write_error
	if not bool(_read_one(temporary).get("ok", false)):
		return ERR_FILE_CORRUPT
	if FileAccess.file_exists(path) and bool(_read_one(path).get("ok", false)):
		var backup_error := DirAccess.rename_absolute(ProjectSettings.globalize_path(path), ProjectSettings.globalize_path(path + ".bak"))
		if backup_error != OK:
			return backup_error
	# If the primary is damaged, retain any usable backup instead of replacing it.
	return DirAccess.rename_absolute(ProjectSettings.globalize_path(temporary), ProjectSettings.globalize_path(path))


func load_game(path: String) -> Dictionary:
	var primary := _read_one(path)
	if bool(primary.get("ok", false)):
		primary["recovered"] = false
		return primary
	# Do not silently replace a save from a newer version with an older backup.
	if primary.get("reason", "") == "unsupported":
		return primary
	var backup := _read_one(path + ".bak")
	if bool(backup.get("ok", false)):
		backup["recovered"] = true
		return backup
	if primary.get("reason", "") == "missing" and backup.get("reason", "") == "missing":
		return {"ok": false, "reason": "missing"}
	return {"ok": false, "reason": "unreadable"}


func _read_one(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"ok": false, "reason": "missing"}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"ok": false, "reason": "unreadable"}
	if file.get_length() > MAX_SAVE_BYTES:
		file.close()
		return {"ok": false, "reason": "unreadable"}
	var text := file.get_as_text()
	file.close()
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return {"ok": false, "reason": "unreadable"}
	var envelope: Variant = parser.data
	if not envelope is Dictionary:
		return {"ok": false, "reason": "unreadable"}
	if not _is_nonnegative_integer(envelope.get("format_version")):
		return {"ok": false, "reason": "unreadable"}
	if envelope.get("format_version", -1) != FORMAT_VERSION:
		return {"ok": false, "reason": "unsupported"}
	if not envelope.get("payload") is String or not envelope.get("checksum") is String:
		return {"ok": false, "reason": "unreadable"}
	var payload: String = envelope.payload
	if payload.sha256_text() != envelope.checksum:
		return {"ok": false, "reason": "unreadable"}
	# Objects remain disabled: saves contain data only, never executable objects.
	var decoded: Variant = Marshalls.base64_to_variant(payload, false)
	if not decoded is Dictionary:
		return {"ok": false, "reason": "unreadable"}
	if _is_nonnegative_integer(decoded.get("schema_version")) and decoded.schema_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("economy_version") and _is_nonnegative_integer(decoded.economy_version) and decoded.economy_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("production_version") and _is_nonnegative_integer(decoded.production_version) and decoded.production_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("logistics_version") and _is_nonnegative_integer(decoded.logistics_version) and decoded.logistics_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("player_roles_version") and _is_nonnegative_integer(decoded.player_roles_version) and decoded.player_roles_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("construction_version") and _is_nonnegative_integer(decoded.construction_version) and decoded.construction_version not in [1, 2]:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("build_supply_version") and _is_nonnegative_integer(decoded.build_supply_version) and decoded.build_supply_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("archive_version") and _is_nonnegative_integer(decoded.archive_version) and decoded.archive_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("research_version") and _is_nonnegative_integer(decoded.research_version) and decoded.research_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("station_supply_version") and _is_nonnegative_integer(decoded.station_supply_version) and decoded.station_supply_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("shipyard_version") and _is_nonnegative_integer(decoded.shipyard_version) and decoded.shipyard_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("personnel_version") and _is_nonnegative_integer(decoded.personnel_version) and decoded.personnel_version not in [1, 2]:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("population_version") and _is_nonnegative_integer(decoded.population_version) and decoded.population_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("habitation_version") and _is_nonnegative_integer(decoded.habitation_version) and decoded.habitation_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("provisions_version") and _is_nonnegative_integer(decoded.provisions_version) and decoded.provisions_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("career_version") and _is_nonnegative_integer(decoded.career_version) and decoded.career_version != 1:
		return {"ok":false, "reason":"unsupported"}
	if decoded.has("education_version") and _is_nonnegative_integer(decoded.education_version) and decoded.education_version != 1:
		return {"ok":false, "reason":"unsupported"}
	if decoded.has("demographics_version") and _is_nonnegative_integer(decoded.demographics_version) and decoded.demographics_version != 1:
		return {"ok":false, "reason":"unsupported"}
	if decoded.has("ecology_version") and _is_nonnegative_integer(decoded.ecology_version) and decoded.ecology_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("settlement_version") and _is_nonnegative_integer(decoded.settlement_version) and decoded.settlement_version not in [1, 2]:
		return {"ok": false, "reason": "unsupported"}
	if not _valid_world(decoded):
		return {"ok": false, "reason": "unreadable"}
	return {"ok": true, "state": decoded}


func _is_number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))


func _is_nonnegative_integer(value: Variant) -> bool:
	return _is_number(value) and float(value) >= 0.0 and float(value) == floor(float(value))


func _valid_world(state: Dictionary) -> bool:
	if state.has("station_supply_version") and not state.has("research_version"):
		return false
	if state.has("shipyard_version") != state.has("shipyard") or (state.has("shipyard_version") and not state.has("station_supply_version")):
		return false
	if state.has("personnel_version") != state.has("crew_pools") or (state.has("personnel_version") and not state.has("shipyard_version")):
		return false
	if state.has("population_version") != state.has("population") or (state.has("population_version") and state.get("personnel_version") != 2):
		return false
	if state.has("habitation_version") != state.has("habitation_catalog") or (state.has("habitation_version") and not state.has("population_version")):
		return false
	if state.has("provisions_version") != state.has("provisions_catalog") or (state.has("provisions_version") and not state.has("habitation_version")):
		return false
	if state.has("settlement_version") and not state.has("provisions_version"):
		return false
	if state.has("ecology_version") != state.has("ecology_catalog") or (state.has("ecology_version") and state.get("settlement_version") != 2):
		return false
	if state.has("demographics_version") != state.has("demographics_catalog") or (state.has("demographics_version") and state.get("ecology_version") != 1):
		return false
	if state.has("education_version") != state.has("education_catalog") or (state.has("education_version") and state.get("demographics_version") != 1):
		return false
	if state.has("career_version") != state.has("career_catalog") or (state.has("career_version") and state.get("education_version") != 1):
		return false
	if state.get("schema_version", 0) != 1 or not _is_nonnegative_integer(state.get("tick")) or not _is_nonnegative_integer(state.get("starting_credits")):
		return false
	for key in ["factions", "sectors", "links", "ships", "starting_profiles"]:
		if not state.get(key) is Array:
			return false
	if not state.get("relations") is Dictionary or not state.get("player_faction_id") is String or not state.get("player_origin_faction_id") is String:
		return false
	var factions: Dictionary = {}
	for faction in state.factions:
		if not faction is Dictionary or not faction.get("id") is String or str(faction.id).is_empty() or not faction.get("name") is String or not faction.get("color") is String or not str(faction.color).is_valid_html_color() or factions.has(faction.id):
			return false
		factions[faction.id] = true
	if not factions.has(state.player_faction_id) or not factions.has(state.player_origin_faction_id) or state.player_origin_faction_id == state.player_faction_id:
		return false
	for id in factions:
		if id != state.player_faction_id and not _is_number(state.relations.get(id)):
			return false
	var sectors: Dictionary = {}
	for sector in state.sectors:
		if not sector is Dictionary or not sector.get("id") is String or str(sector.id).is_empty() or sectors.has(sector.id) or not sector.get("name") is String or not sector.get("description") is String or not factions.has(sector.get("owner")):
			return false
		if not _is_number(sector.get("x")) or not _is_number(sector.get("y")) or float(sector.x) < 0.0 or float(sector.x) > 1.0 or float(sector.y) < 0.0 or float(sector.y) > 1.0:
			return false
		sectors[sector.id] = true
	var links: Dictionary = {}
	for link in state.links:
		if not link is Array or link.size() != 2 or not sectors.has(link[0]) or not sectors.has(link[1]) or link[0] == link[1]:
			return false
		links["%s|%s" % [link[0], link[1]]] = true
		links["%s|%s" % [link[1], link[0]]] = true
	if state.ships.is_empty():
		return false
	var ships: Dictionary = {}
	for ship in state.ships:
		if not ship is Dictionary:
			return false
		for key in ["id", "name", "class", "owner", "sector", "captain", "role", "status"]:
			if not ship.get(key) is String:
				return false
		if str(ship.id).is_empty() or ships.has(ship.id) or not factions.has(ship.owner) or not sectors.has(ship.sector) or not _is_nonnegative_integer(ship.get("crew")) or not ship.get("orders") is Array or not ship.get("travel") is Dictionary:
			return false
		ships[ship.id] = true
		for order in ship.orders:
			if not order is Dictionary or order.get("type") != "fly_to" or not sectors.has(order.get("destination")):
				return false
		if not ship.travel.is_empty():
			var trip: Dictionary = ship.travel
			if ship.orders.is_empty() or trip.get("from") != ship.sector or not sectors.has(trip.get("to")) or not links.has("%s|%s" % [trip.get("from"), trip.get("to")]):
				return false
			if not _is_nonnegative_integer(trip.get("total")) or not _is_nonnegative_integer(trip.get("remaining")) or int(trip.total) < 1 or int(trip.remaining) < 1 or int(trip.remaining) > int(trip.total):
				return false
	if state.ships[0].owner != state.player_faction_id:
		return false
	# Saves made before the first economy pass are migrated when opened.
	if not state.has("economy_version"):
		return not state.has("production_version") and not state.has("logistics_version") and not state.has("player_roles_version") and not state.has("construction_version") and not state.has("build_supply_version") and not state.has("archive_version") and not state.has("research_version")
	if not _valid_economy(state, factions, sectors):
		return false
	# Saves from the manual-trading pass are migrated when opened.
	if not state.has("production_version"):
		return not state.has("logistics_version") and not state.has("player_roles_version") and not state.has("construction_version") and not state.has("build_supply_version") and not state.has("archive_version") and not state.has("research_version")
	if not _valid_production(state):
		return false
	if not state.has("logistics_version"):
		return not state.has("player_roles_version") and not state.has("construction_version") and not state.has("build_supply_version") and not state.has("archive_version") and not state.has("research_version")
	if not _valid_logistics(state):
		return false
	if not state.has("player_roles_version"):
		return not state.has("construction_version") and not state.has("build_supply_version") and not state.has("archive_version") and not state.has("research_version")
	if not _valid_player_roles(state):
		return false
	if not state.has("construction_version"):
		return not state.has("build_supply_version") and not state.has("archive_version") and not state.has("research_version")
	if not _valid_construction(state, factions, sectors):
		return false
	if not state.has("build_supply_version"):
		return not state.has("archive_version") and not state.has("research_version")
	if not _valid_build_supply(state):
		return false
	if not state.has("archive_version"):
		return not state.has("research_version")
	if not _valid_archives(state):
		return false
	if not state.has("research_version"):
		return not state.has("station_supply_version")
	if not _valid_research(state):
		return false
	if not state.has("station_supply_version"):
		return not state.has("shipyard_version")
	if not _valid_station_supply(state):
		return false
	if state.has("shipyard_version") and not _valid_shipyard(state):
		return false
	if not state.has("personnel_version"):
		return not state.has("population_version")
	if not _valid_personnel(state):
		return false
	if not state.has("population_version"):
		return not state.has("habitation_version")
	if not _valid_population(state):
		return false
	if not state.has("habitation_version"):
		return not state.has("provisions_version")
	if not _valid_habitation(state):
		return false
	if not state.has("provisions_version"):
		return not state.has("settlement_version")
	if not _valid_provisions(state):
		return false
	if state.has("settlement_version") and not _valid_settlement(state):
		return false
	if state.has("ecology_version") and not _valid_ecology(state):
		return false
	if state.has("demographics_version") and not _valid_demographics(state):
		return false
	if state.has("education_version") and not _valid_education(state):
		return false
	return not state.has("career_version") or _valid_careers(state)


func _valid_settlement(state: Dictionary) -> bool:
	if state.settlement_version not in [1, 2]:
		return false
	var personnel = PersonnelScript.new()
	var player_stations: Dictionary = {}
	for station in state.stations:
		if station.owner == state.player_faction_id:
			player_stations[str(station.id)] = true
	for ship in state.ships:
		if not _is_nonnegative_integer(ship.get("settler_passengers")) or not ship.get("settler_source_station_id") is String:
			return false
		var n: int = int(ship.settler_passengers)
		var source: String = str(ship.settler_source_station_id)
		if n > 1000000 or source.length() > 128 or (n == 0) != source.is_empty():
			return false
		if n > 0:
			if ship.owner != state.player_faction_id or int(ship.crew) + n > personnel.capacity(ship):
				return false
			# Pass 29 sources are existing NPC roster stations only. Pass 30
			# also permits physical evacuation from a valid owned colony.
			if not state.crew_pools.has(source) and (state.settlement_version != 2 or not player_stations.has(source)):
				return false
	if state.settlement_version == 1:
		return true
	for record in state.population.stations.values():
		if not record is Dictionary or record.get("resident_status") not in ["Unoccupied", "Awaiting service", "Provisioned", "Provision shortage", "Housing offline"]:
			return false
		if not record.get("resident_shortage") is String or str(record.resident_shortage) not in ["", "potable_water", "food_rations", "medical_supplies"]:
			return false
		if not _is_nonnegative_integer(record.get("resident_alert_cycles")) or int(record.resident_alert_cycles) > 1000000:
			return false
		var occupied: int = int(record.cohorts.assigned_workers)
		var mode: String = str(record.resident_status)
		var alert: int = int(record.resident_alert_cycles)
		if (occupied == 0) != (mode == "Unoccupied"):
			return false
		if (mode == "Provision shortage") != (str(record.resident_shortage) != ""):
			return false
		if mode in ["Provision shortage", "Housing offline"]:
			if alert < 1:
				return false
		elif alert != 0:
			return false
	return true




func _valid_demographics(state: Dictionary) -> bool:
	if state.demographics_version != 1 or state.get("demographics_catalog") != {
		"birth_interval":DemographicsScript.BIRTH_INTERVAL,
		"childhood_ticks":DemographicsScript.CHILDHOOD_TICKS,
		"youth_ticks":DemographicsScript.YOUTH_TICKS,
		"birth_medical_cost":1
	}:
		return false
	var registered: Dictionary = {}
	for station in state.stations:
		registered[str(station.id)] = station
	for station_id in state.population.stations:
		var record: Dictionary = state.population.stations[station_id]
		if not record.get("family") is Dictionary:
			return false
		var family: Dictionary = record.family
		if family.size() != 5 or not _is_nonnegative_integer(family.get("birth_progress")) or int(family.birth_progress) > DemographicsScript.BIRTH_INTERVAL or int(family.birth_progress) % DemographicsScript.SERVICE_INTERVAL != 0:
			return false
		for key in ["births_total", "grown_total"]:
			if not _is_nonnegative_integer(family.get(key)) or int(family[key]) > 1000000:
				return false
		if int(family.grown_total) > int(family.births_total) or not family.get("child_queue") is Array or not family.get("youth_queue") is Array:
			return false
		if not registered.has(station_id) and (int(family.births_total) != 0 or int(family.birth_progress) != 0):
			return false
		var child_count: int = 0
		var youth_count: int = 0
		for queue_id in ["child_queue", "youth_queue"]:
			var cohort_queue: Array = family[queue_id]
			if cohort_queue.size() > 10000:
				return false
			var earliest := -1
			for entry in cohort_queue:
				if not entry is Dictionary or entry.size() != 2 or not _is_nonnegative_integer(entry.get("quantity")) or int(entry.quantity) < 1 or not _is_nonnegative_integer(entry.get("ready_tick")):
					return false
				var due: int = int(entry.ready_tick)
				var duration: int = DemographicsScript.CHILDHOOD_TICKS if queue_id == "child_queue" else DemographicsScript.YOUTH_TICKS
				if due <= int(state.tick) or due > int(state.tick) + duration or (earliest >= 0 and due < earliest):
					return false
				earliest = due
				if queue_id == "child_queue":
					child_count += int(entry.quantity)
				else:
					youth_count += int(entry.quantity)
		if child_count != int(record.cohorts.children) or youth_count != int(record.cohorts.students) or int(family.births_total) != child_count + youth_count + int(family.grown_total):
			return false
		if (child_count + youth_count) > int(record.hab_capacity) or (child_count + youth_count) > 0 and int(record.cohorts.assigned_workers) * 2 < child_count + youth_count:
			return false
	return true



func _valid_education(state: Dictionary) -> bool:
	if state.education_version != 1 or not state.get("education_catalog") is Dictionary:
		return false
	var source: Dictionary = EducationScript.new().definitions()
	if source.is_empty() or state.education_catalog != source.catalog:
		return false
	for program_id in EducationScript.PROGRAM_IDS:
		if state.construction_blueprints.get(program_id, {}) != source.blueprints[program_id]:
			return false
	for station in state.stations:
		if not station.get("education") is Dictionary:
			return false
		var record: Dictionary = station.education
		if record.size() != 7 or not record.get("modules") is Array or not record.get("courses") is Dictionary or not record.get("qualified") is Dictionary or record.qualified.size() != EducationScript.PROGRAM_IDS.size():
			return false
		for key in ["teachers", "youth_completed", "certificates_total", "payroll_credits"]:
			if not _is_nonnegative_integer(record.get(key)) or int(record[key]) > 1000000:
				return false
		if int(record.teachers) > 1000000 or record.modules.size() > 300 or record.courses.size() > EducationScript.PROGRAM_IDS.size():
			return false
		var module_counts: Dictionary = {}
		for id in record.modules:
			if not id is String or id not in EducationScript.PROGRAM_IDS:
				return false
			module_counts[id] = int(module_counts.get(id, 0)) + 1
		var cohort: Dictionary = state.population.stations.get(str(station.id), {})
		if cohort.is_empty():
			return false
		var adults: int = int(cohort.cohorts.assigned_workers)
		var youths: int = int(cohort.cohorts.students)
		var trained_adults := 0
		for program_id in EducationScript.PROGRAM_IDS:
			if not _is_nonnegative_integer(record.qualified.get(program_id)) or int(record.qualified[program_id]) > 1000000:
				return false
			trained_adults += int(record.qualified[program_id])
		if trained_adults > adults or int(record.teachers) > adults or int(record.youth_completed) > youths or int(record.certificates_total) != trained_adults + int(record.youth_completed):
			return false
		var adult_studying := 0
		var youth_studying := 0
		var teachers_busy := 0
		for program_id in record.courses:
			var classroom: Variant = record.courses[program_id]
			if not record.qualified.has(program_id) or not classroom is Dictionary or classroom.size() != 4 or int(module_counts.get(program_id, 0)) == 0:
				return false
			if not _is_nonnegative_integer(classroom.get("count")) or int(classroom.count) < 1 or not _is_nonnegative_integer(classroom.get("progress")) or classroom.get("target") not in ["adult", "youth"] or not classroom.get("status") is String or str(classroom.status).length() > 96:
				return false
			var program: Dictionary = state.education_catalog[program_id]
			if int(classroom.count) > int(module_counts[program_id]) * int(program.seats) or int(classroom.progress) >= int(program.course_ticks) or int(classroom.progress) % EducationScript.INTERVAL != 0 or int(classroom.progress) > int(state.tick):
				return false
			if classroom.target == "youth":
				if program_id != "community_school":
					return false
				youth_studying += int(classroom.count)
			else:
				adult_studying += int(classroom.count)
			teachers_busy += ceili(float(int(classroom.count)) / float(EducationScript.STUDENTS_PER_TEACHER))
		if teachers_busy > int(record.teachers) or adult_studying + maxi(int(record.teachers), trained_adults) > adults or youth_studying + int(record.youth_completed) > youths:
			return false
		# A save cannot mint a certificate by changing a counter. Validate
		# its immutable education enrollment/completion and wage evidence.
		var last_appointment: int = 0
		var enrolled_by_program: Dictionary = {}
		var completed_by_program: Dictionary = {}
		var exited_by_program: Dictionary = {}
		var transferred_out: Dictionary = {}
		var transferred_in: Dictionary = {}
		var payroll_evidence := 0
		for event in state.ledger:
			if str(event.get("station_id", "")) != str(station.id):
				continue
			var kind: String = str(event.get("kind", ""))
			if kind not in ["education_appointment", "education_enrollment", "education_completed", "education_age_exit", "education_payroll", "career_transfer_departure", "career_transfer_arrival"]:
				continue
			if not _is_nonnegative_integer(event.get("quantity")) or not _is_nonnegative_integer(event.get("price")) or not _is_number(event.get("amount")) or not _is_nonnegative_integer(event.get("tick")) or int(event.tick) > int(state.tick):
				return false
			if kind == "education_appointment":
				if int(event.price) != 0 or int(event.amount) != 0:
					return false
				last_appointment = int(event.quantity)
			elif kind == "education_payroll":
				if int(event.amount) >= 0 or int(event.price) < 1 or int(event.quantity) < 1:
					return false
				payroll_evidence += -int(event.amount)
			else:
				var program_id: String = str(event.get("ware_id", ""))
				if program_id not in EducationScript.PROGRAM_IDS or int(event.quantity) < 1 or int(event.price) != 0 or int(event.amount) != 0:
					return false
				if kind == "education_enrollment":
					enrolled_by_program[program_id] = int(enrolled_by_program.get(program_id, 0)) + int(event.quantity)
				elif kind == "education_completed":
					completed_by_program[program_id] = int(completed_by_program.get(program_id, 0)) + int(event.quantity)
				elif kind == "education_age_exit":
					if program_id != "community_school":
						return false
					exited_by_program[program_id] = int(exited_by_program.get(program_id, 0)) + int(event.quantity)
				elif kind == "career_transfer_departure":
					if not state.has("career_version") or int(event.price) not in [0, 1]:
						return false
					transferred_out[program_id] = int(transferred_out.get(program_id, 0)) + int(event.quantity)
				elif kind == "career_transfer_arrival":
					if not state.has("career_version") or int(event.price) not in [0, 1]:
						return false
					transferred_in[program_id] = int(transferred_in.get(program_id, 0)) + int(event.quantity)
		if last_appointment != int(record.teachers) or payroll_evidence != int(record.payroll_credits):
			return false
		for program_id in EducationScript.PROGRAM_IDS:
			var expected_completed: int = int(record.qualified[program_id]) + (int(record.youth_completed) if program_id == "community_school" else 0) + int(transferred_out.get(program_id, 0)) - int(transferred_in.get(program_id, 0))
			if int(completed_by_program.get(program_id, 0)) != expected_completed:
				return false
			var active_count: int = int(record.courses.get(program_id, {}).get("count", 0))
			if int(enrolled_by_program.get(program_id, 0)) != expected_completed + int(exited_by_program.get(program_id, 0)) + active_count:
				return false
		if (not record.courses.is_empty() or trained_adults > 0 or int(record.youth_completed) > 0 or int(record.teachers) > 0) and station.owner != state.player_faction_id:
			return false
		if not record.courses.is_empty() and (station.get("habitation", []).is_empty() or int(cohort.hab_capacity) < adults + youths + int(cohort.cohorts.children)):
			return false
	return true


func _valid_careers(state: Dictionary) -> bool:
	if state.career_version != CareersScript.VERSION or not state.get("career_catalog") is Dictionary:
		return false
	var source := CareersScript.new()
	var expected: Dictionary = {}
	for track in CareersScript.TRACKS:
		expected[track] = {
			"name":str(state.education_catalog[track].name) + " — supervised practicum",
			"duration":CareersScript.PRACTICUM_TICKS,
			"energy_per_60":CareersScript.ENERGY_PER_CYCLE,
			"records_per_60":CareersScript.RECORDS_PER_CYCLE,
			"wages_per_60":CareersScript.PAY_PER_CYCLE,
			"prerequisite":track,
			"workplace":source.workplace_name(track)
		}
	if expected != state.career_catalog:
		return false
	var departures: Dictionary = {}
	var arrivals: Dictionary = {}
	for station in state.stations:
		if not station.get("careers") is Dictionary:
			return false
		var careers: Dictionary = station.careers
		if careers.size() != 3 or not careers.get("licensed") is Dictionary or not careers.get("apprenticeships") is Dictionary or careers.licensed.size() != CareersScript.TRACKS.size() or careers.apprenticeships.size() > CareersScript.TRACKS.size() or not _is_nonnegative_integer(careers.get("payroll_credits")):
			return false
		var rec: Dictionary = state.population.stations.get(str(station.id), {})
		if rec.is_empty():
			return false
		var trainees := 0
		for track in CareersScript.TRACKS:
			var certified: Variant = careers.licensed.get(track)
			if not _is_nonnegative_integer(certified) or int(certified) > int(station.education.qualified[track]):
				return false
			var study: Variant = careers.apprenticeships.get(track, {})
			if not study is Dictionary or not study.is_empty():
				if not study is Dictionary or study.size() != 3 or not _is_nonnegative_integer(study.get("count")) or int(study.count) < 1 or not _is_nonnegative_integer(study.get("progress")) or int(study.progress) >= CareersScript.PRACTICUM_TICKS or int(study.progress) % CareersScript.SERVICE_INTERVAL != 0 or study.get("status") not in ["Enrolled", "Supervised work", "Needs provisioned residents", "Needs real adult mentor", "Needs working practice facility", "Needs Energy Cells", "Needs recorded_data", "Needs research_notes", "Needs salaries"]:
					return false
				if int(study.count) + int(certified) > int(station.education.qualified[track]):
					return false
				trainees += int(study.count)
		if int(station.education.teachers) + trainees > int(rec.cohorts.assigned_workers):
			return false
		if not careers.apprenticeships.is_empty() and (station.owner != state.player_faction_id or int(station.education.teachers) < 1 or station.habitation.is_empty()):
			return false
		var paid := 0
		var by_program: Dictionary = {}
		var practice_complete: Dictionary = {}
		var local_departures: Dictionary = {}
		var local_arrivals: Dictionary = {}
		for event in state.ledger:
			if str(event.get("station_id", "")) != str(station.id):
				continue
			var kind: String = str(event.get("kind", ""))
			if kind not in ["career_apprenticeship_start", "career_practicum_payroll", "career_practicum_complete", "career_transfer_departure", "career_transfer_arrival"]:
				continue
			if not _is_nonnegative_integer(event.get("quantity")) or not _is_number(event.get("amount")) or not _is_nonnegative_integer(event.get("price")) or not _is_nonnegative_integer(event.get("tick")) or int(event.tick) > int(state.tick):
				return false
			if kind == "career_practicum_payroll":
				if event.ware_id not in ["recorded_data", "research_notes"] or int(event.quantity) != CareersScript.RECORDS_PER_CYCLE or int(event.price) != CareersScript.PAY_PER_CYCLE or int(event.amount) != -CareersScript.PAY_PER_CYCLE:
					return false
				paid += -int(event.amount)
				continue
			var track: String = str(event.get("ware_id", ""))
			if kind == "career_apprenticeship_start":
				if track not in CareersScript.TRACKS or int(event.quantity) < 1 or int(event.amount) != 0 or int(event.price) != 0:
					return false
				by_program[track] = int(by_program.get(track, 0)) + int(event.quantity)
			elif kind == "career_practicum_complete":
				if track not in CareersScript.TRACKS or int(event.quantity) < 1 or int(event.amount) != 0 or int(event.price) != 0:
					return false
				practice_complete[track] = int(practice_complete.get(track, 0)) + int(event.quantity)
			elif kind in ["career_transfer_departure", "career_transfer_arrival"]:
				if track not in EducationScript.PROGRAM_IDS or int(event.quantity) < 1 or int(event.amount) != 0 or int(event.price) not in [0, 1] or not event.get("ship_id") is String:
					return false
				var key := str(event.ship_id) + "|" + track + "|" + str(event.price)
				if kind == "career_transfer_departure":
					departures[key] = int(departures.get(key, 0)) + int(event.quantity)
					if int(event.price) == 1:
						local_departures[track] = int(local_departures.get(track, 0)) + int(event.quantity)
				else:
					arrivals[key] = int(arrivals.get(key, 0)) + int(event.quantity)
					if int(event.price) == 1:
						local_arrivals[track] = int(local_arrivals.get(track, 0)) + int(event.quantity)
		if paid != int(careers.payroll_credits):
			return false
		for track in CareersScript.TRACKS:
			var enrolled: int = int(by_program.get(track, 0))
			var completed: int = int(practice_complete.get(track, 0))
			var working: int = int(careers.apprenticeships.get(track, {}).get("count", 0))
			if enrolled != completed + working:
				return false
			if completed + int(local_arrivals.get(track, 0)) - int(local_departures.get(track, 0)) != int(careers.licensed[track]):
				return false
	for ship in state.ships:
		if not ship.get("career_manifest") is Dictionary:
			return false
		var manifest: Dictionary = ship.career_manifest
		if manifest.is_empty():
			continue
		if manifest.size() != 3 or manifest.get("track") not in EducationScript.PROGRAM_IDS or not _is_nonnegative_integer(manifest.get("quantity")) or int(manifest.quantity) < 1 or manifest.get("certified") not is bool:
			return false
		if ship.owner != state.player_faction_id or int(ship.get("settler_passengers", 0)) != int(manifest.quantity):
			return false
		var origin: Dictionary = {}
		for station in state.stations:
			if str(station.id) == str(ship.settler_source_station_id):
				origin = station
				break
		if origin.is_empty() or origin.owner != state.player_faction_id:
			return false
		var key := str(ship.id) + "|" + str(manifest.track) + "|" + ("1" if bool(manifest.certified) else "0")
		if int(departures.get(key, 0)) - int(arrivals.get(key, 0)) < int(manifest.quantity):
			return false
	for key in departures:
		var on_ship := 0
		for ship in state.ships:
			var manifest: Dictionary = ship.career_manifest
			if not manifest.is_empty() and key == str(ship.id) + "|" + str(manifest.track) + "|" + ("1" if bool(manifest.certified) else "0"):
				on_ship += int(manifest.quantity)
		if int(departures[key]) - int(arrivals.get(key, 0)) != on_ship:
			return false
	for key in arrivals:
		if not departures.has(key):
			return false
	return true


func _valid_ecology(state: Dictionary) -> bool:
	if state.ecology_version != 1 or not state.get("ecology_catalog") is Dictionary:
		return false
	var expected: Dictionary = EcologyScript.new().definitions()
	if expected.is_empty() or state.ecology_catalog != {
		"wares":EcologyScript.WARE_IDS,
		"recipes":EcologyScript.RECIPE_IDS,
		"waste_sources":expected.waste_sources
	}:
		return false
	for ware in expected.wares:
		var found := false
		for present in state.wares:
			if present.id == ware.id:
				if present != ware:
					return false
				found = true
				break
		if not found:
			return false
	for recipe in expected.recipes:
		var found := false
		for present in state.recipes:
			if present.id == recipe.id:
				if present != recipe:
					return false
				found = true
				break
		if not found or state.construction_blueprints.get(recipe.id, {}) != expected.blueprints[recipe.id]:
			return false
	return true


func _valid_provisions(state: Dictionary) -> bool:
	if state.provisions_version != 1 or not state.get("provisions_catalog") is Dictionary:
		return false
	var data: Dictionary = ProvisionsScript.new().definitions()
	if data.is_empty():
		return false
	var expected: Dictionary = {
		"wares":ProvisionsScript.WARE_IDS,
		"recipes":ProvisionsScript.RECIPE_IDS,
		"habitat_needs_per_60":data.habitat_needs_per_60,
		"sector_ice_deposits":data.sector_ice_deposits
	}
	if state.provisions_catalog != expected:
		return false
	for ware in data.wares:
		var found := false
		for existing in state.wares:
			if existing.id == ware.id:
				if existing != ware:
					return false
				found = true
				break
		if not found:
			return false
	for recipe in data.recipes:
		var found := false
		for existing in state.recipes:
			if existing.id == recipe.id:
				if existing != recipe:
					return false
				found = true
				break
		if not found or state.construction_blueprints.get(recipe.id, {}) != data.blueprints[recipe.id]:
			return false
	for sector_id in data.sector_ice_deposits:
		if not state.construction_resources.has(sector_id):
			return false
		var deposits: Dictionary = state.construction_resources[sector_id].deposits
		if not _is_nonnegative_integer(deposits.get("ice")) or int(deposits.ice) > int(data.sector_ice_deposits[sector_id]):
			return false
	return true


func _valid_habitation(state: Dictionary) -> bool:
	if state.habitation_version != 1 or not state.get("habitation_catalog") is Dictionary or state.habitation_catalog.size() != 3:
		return false
	var expected_ids := ["crew_habitat", "family_habitat", "adaptive_habitat"]
	for module_id in state.habitation_catalog:
		if not module_id in expected_ids:
			return false
		var definition: Variant = state.habitation_catalog[module_id]
		if not definition is Dictionary or definition.get("id") != module_id or not definition.get("name") is String or not definition.get("environment") is String or not _is_nonnegative_integer(definition.get("capacity")) or int(definition.capacity) < 1 or int(definition.capacity) > 1000000 or not _is_nonnegative_integer(definition.get("energy_per_60")) or int(definition.energy_per_60) < 1 or int(definition.energy_per_60) > 1000:
			return false
		if not state.construction_blueprints.has(module_id):
			return false
	for station in state.stations:
		if not station.get("habitation") is Array or not state.population.stations.has(str(station.id)):
			return false
		var total := 0
		var powered := 0
		for housing in station.habitation:
			if not housing is Dictionary or not state.habitation_catalog.has(housing.get("id")) or not housing.get("powered") is bool or housing.get("status") not in ["Awaiting power", "Powered", "Needs Energy Cells", "Needs Potable Water", "Needs Food Rations", "Needs Medical Supplies"] or not _is_nonnegative_integer(housing.get("cycles")) or int(housing.cycles) > int(state.tick / 60):
				return false
			if bool(housing.powered) != (housing.status == "Powered"):
				return false
			var definition: Dictionary = state.habitation_catalog[housing.id]
			total += int(definition.capacity)
			if housing.powered:
				powered += int(definition.capacity)
		if total > 1000000:
			return false
		var residents: Dictionary = state.population.stations[str(station.id)]
		var expected_status := "No habitat" if total == 0 else ("Powered" if powered == total else ("Partially powered" if powered > 0 else "Unpowered"))
		if int(residents.hab_capacity) != total or residents.housing_status != expected_status:
			return false
	return true


func _valid_population(state: Dictionary) -> bool:
	if state.population_version != 1 or not state.get("population") is Dictionary:
		return false
	var population: Dictionary = state.population
	if not population.get("stations") is Dictionary or population.stations.size() > 10000:
		return false
	if population.stations.is_empty():
		return false
	var registered: Dictionary = {}
	for station in state.stations:
		registered[str(station.id)] = true
	# The legacy pool and the new cohort are two views of the SAME people:
	# a difference would duplicate, lose or fabricate recruits.
	for station_id in state.crew_pools:
		if not population.stations.has(station_id):
			return false
	for station_id in population.stations:
		if not station_id is String or str(station_id).is_empty() or str(station_id).length() > 128:
			return false
		if not registered.has(station_id) and not state.crew_pools.has(station_id):
			return false
		var entry: Variant = population.stations[station_id]
		if not entry is Dictionary:
			return false
		if entry.get("id") != "residents_" + str(station_id) or entry.get("station_id") != station_id or not entry.get("cohorts") is Dictionary:
			return false
		if not _is_nonnegative_integer(entry.get("hab_capacity")) or int(entry.hab_capacity) > 1000000 or not entry.get("housing_status") is String:
			return false
		if not state.has("habitation_version") and (int(entry.hab_capacity) != 0 or entry.housing_status != "unimplemented"):
			return false
		if state.has("habitation_version") and entry.housing_status not in ["No habitat", "Powered", "Partially powered", "Unpowered"]:
			return false
		var counts: Dictionary = entry.cohorts
		if counts.size() != 5:
			return false
		for group in ["children", "students", "available_workers", "assigned_workers", "retirees"]:
			if not _is_nonnegative_integer(counts.get(group)) or int(counts[group]) > 1000000:
				return false
		if not state.has("demographics_version") and (int(counts.children) != 0 or int(counts.students) != 0 or int(counts.retirees) != 0):
			return false
		if state.has("demographics_version") and int(counts.retirees) != 0:
			return false
		if int(counts.assigned_workers) + int(counts.children) + int(counts.students) + int(counts.retirees) > 0:
			if not state.has("settlement_version") or not registered.has(station_id):
				return false
			var owned: Dictionary = {}
			for location in state.stations:
				if str(location.id) == str(station_id):
					owned = location
					break
			if owned.is_empty() or owned.owner != state.player_faction_id or int(counts.assigned_workers) + int(counts.children) + int(counts.students) + int(counts.retirees) > int(entry.hab_capacity):
				return false
		var available: int = int(counts.available_workers)
		if available != int(state.crew_pools.get(station_id, 0)):
			return false
	return true


func _valid_personnel(state: Dictionary) -> bool:
	if state.personnel_version not in [1, 2] or not state.get("crew_pools") is Dictionary or state.crew_pools.is_empty():
		return false
	# A station may legitimately be destroyed or removed while NPC ships are
	# travelling. Keep its dormant roster for save compatibility.
	for station_id in state.crew_pools:
		if not station_id is String or str(station_id).is_empty() or str(station_id).length() > 128 or not _is_nonnegative_integer(state.crew_pools[station_id]) or int(state.crew_pools[station_id]) > 1000000:
			return false
	if state.personnel_version == 1:
		return true
	var captain_ids: Dictionary = {}
	for ship in state.ships:
		if ship.owner != state.player_faction_id:
			if ship.has("captain_profile") or ship.has("crew_profile") or ship.has("payroll"):
				return false
			continue
		if not ship.get("captain_profile") is Dictionary or not ship.get("crew_profile") is Dictionary or not ship.get("payroll") is Dictionary:
			return false
		var captain: Dictionary = ship.captain_profile
		var crew: Dictionary = ship.crew_profile
		var pay: Dictionary = ship.payroll
		if not captain.get("id") is String or str(captain.id).is_empty() or str(captain.id).length() > 128 or captain_ids.has(captain.id):
			return false
		captain_ids[captain.id] = true
		for profile in [captain, crew]:
			if not _is_nonnegative_integer(profile.get("experience")) or int(profile.experience) > 1000000000 or not _is_nonnegative_integer(profile.get("skill")) or int(profile.skill) > 5 or not _is_nonnegative_integer(profile.get("morale")) or int(profile.morale) > 100:
				return false
		if int(captain.skill) != mini(5, int(int(captain.experience) / 25)) or int(crew.skill) != mini(5, int(int(crew.experience) / maxi(1, int(ship.crew)) / 25)):
			return false
		for field in ["last_tick", "arrears", "total_paid", "unpaid_periods"]:
			if not _is_nonnegative_integer(pay.get(field)) or int(pay[field]) > 1000000000:
				return false
		if int(pay.last_tick) > int(state.tick) or not pay.get("station_id") is String or str(pay.station_id).length() > 128:
			return false
	return true


func _valid_shipyard(state: Dictionary) -> bool:
	if state.shipyard_version != 1 or not state.get("shipyard") is Dictionary:
		return false
	var yard: Dictionary = state.shipyard
	if not yard.get("wharf_station_id") is String or str(yard.wharf_station_id).is_empty() or not yard.get("catalog") is Dictionary or yard.catalog.is_empty() or not yard.get("orders") is Array or not _is_nonnegative_integer(yard.get("next_order_id")) or int(yard.next_order_id) < 1 or not _is_nonnegative_integer(yard.get("next_ship_serial")) or int(yard.next_ship_serial) < 2:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	for hull_id in yard.catalog:
		var hull: Variant = yard.catalog[hull_id]
		if not hull is Dictionary or hull.get("id") != hull_id or not hull.get("name") is String or str(hull.name).is_empty() or not hull.get("class") is String or str(hull["class"]).is_empty() or not hull.get("materials") is Dictionary or hull.materials.is_empty():
			return false
		for key in ["price", "ticks", "cargo_capacity", "crew"]:
			if not _is_nonnegative_integer(hull.get(key)) or int(hull[key]) < 1 or int(hull[key]) > 100000000:
				return false
		for ware_id in hull.materials:
			if not wares.has(ware_id) or not _is_nonnegative_integer(hull.materials[ware_id]) or int(hull.materials[ware_id]) < 1:
				return false
	var order_ids: Dictionary = {}
	var reserved_ids: Dictionary = {}
	var pending := 0
	for order in yard.orders:
		if not order is Dictionary or not order.get("id") is String or str(order.id).is_empty() or order_ids.has(order.id) or not order.get("ship_id") is String or str(order.ship_id).is_empty() or reserved_ids.has(order.ship_id) or not yard.catalog.has(order.get("hull_id")) or order.get("wharf_station_id") != yard.wharf_station_id:
			return false
		for key in ["price", "duration", "progress", "placed_tick", "finished_tick"]:
			if not _is_nonnegative_integer(order.get(key)):
				return false
		if int(order.price) < 1 or int(order.duration) < 1 or int(order.duration) > 1000000 or int(order.progress) > int(order.duration) or int(order.placed_tick) > int(state.tick) or int(order.finished_tick) > int(state.tick):
			return false
		if not order.get("materials") is Dictionary or order.materials.is_empty() or order.get("status") not in ["queued", "building", "blocked", "complete"]:
			return false
		for ware_id in order.materials:
			if not wares.has(ware_id) or not _is_nonnegative_integer(order.materials[ware_id]) or int(order.materials[ware_id]) < 1:
				return false
		if order.status == "complete":
			if int(order.progress) != int(order.duration) or int(order.finished_tick) < int(order.placed_tick):
				return false
		else:
			pending += 1
			if int(order.progress) >= int(order.duration) or int(order.finished_tick) != 0:
				return false
		order_ids[order.id] = true
		reserved_ids[order.ship_id] = true
	if pending > 5 or int(yard.next_order_id) <= yard.orders.size():
		return false
	return true


func _valid_station_supply(state: Dictionary) -> bool:
	if state.station_supply_version != 1:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	for ship in state.ships:
		if ship.owner != state.player_faction_id:
			if ship.has("station_supply"):
				return false
			continue
		if not ship.get("station_supply") is Dictionary:
			return false
		var job: Dictionary = ship.station_supply
		if not job.get("enabled") is bool or job.get("phase") not in ["idle", "to_source", "to_station"]:
			return false
		for key in ["station_id", "source_id", "ware_id", "wait_reason"]:
			if not job.get(key) is String:
				return false
		for key in ["retry_ticks", "budget_limit", "spent"]:
			if not _is_nonnegative_integer(job.get(key)):
				return false
		if int(job.budget_limit) > 1000000000 or int(job.spent) > int(job.budget_limit):
			return false
		if not job.enabled:
			if not job.station_id.is_empty() or job.phase != "idle" or not job.source_id.is_empty() or not job.ware_id.is_empty() or not job.wait_reason.is_empty() or int(job.retry_ticks) != 0 or int(job.budget_limit) != 0 or int(job.spent) != 0:
				return false
			continue
		if job.station_id.is_empty() or ship.role != "Station Supplier" or ship.player_trader.enabled or ship.build_supply.enabled:
			return false
		if job.phase == "idle" and (not job.source_id.is_empty() or not job.ware_id.is_empty()):
			return false
		if job.phase == "to_source" and (job.source_id.is_empty() or not wares.has(job.ware_id)):
			return false
		if job.phase == "to_station" and (not job.source_id.is_empty() or not wares.has(job.ware_id)):
			return false
	return true


func _valid_research(state: Dictionary) -> bool:
	if state.research_version != 1 or not state.get("research") is Dictionary:
		return false
	var data = ResearchScript.new()
	if data._load_definitions() != OK:
		return false
	var found_ware := false
	var found_recipe := false
	for ware in state.wares:
		if ware.id == "research_notes":
			found_ware = true
	for recipe in state.recipes:
		if recipe.id == "research_laboratory":
			found_recipe = true
	if not found_ware or not found_recipe or not state.construction_blueprints.has("research_laboratory"):
		return false
	var research: Dictionary = state.research
	if not research.get("completed") is Array or not research.get("progress") is Dictionary or not research.get("active_project_id") is String or not research.get("lab_station_id") is String:
		return false
	var completed: Dictionary = {}
	for id in research.completed:
		if not id is String or not data.projects.has(id) or completed.has(id):
			return false
		completed[id] = true
	for id in research.progress:
		if not data.projects.has(id) or not _is_nonnegative_integer(research.progress[id]) or int(research.progress[id]) > int(data.projects[id].target):
			return false
		if (int(research.progress[id]) == int(data.projects[id].target)) != completed.has(id):
			return false
	for id in completed:
		if not research.progress.has(id) or int(research.progress[id]) != int(data.projects[id].target):
			return false
	if research.active_project_id.is_empty():
		return research.lab_station_id.is_empty()
	return data.projects.has(research.active_project_id) and not completed.has(research.active_project_id) and not research.lab_station_id.is_empty()


func _valid_archives(state: Dictionary) -> bool:
	if state.archive_version != 1 or not state.get("visited_archives") is Array:
		return false
	var archive_data = ArchivesScript.new()
	if archive_data._load_definitions() != OK:
		return false
	var visited: Dictionary = {}
	for id in state.visited_archives:
		if not id is String or not archive_data.definitions.has(id) or visited.has(id):
			return false
		visited[id] = true
	for station in state.stations:
		if archive_data.definitions.has(station.id) and not station.has("archive"):
			return false
		if not station.has("archive"):
			continue
		var definition: Dictionary = archive_data.definition(str(station.id))
		var archive: Variant = station.archive
		if definition.is_empty() or not archive is Dictionary or station.sector != definition.sector:
			return false
		if not archive.get("sponsor") is String or str(archive.sponsor).is_empty() or archive.get("status") not in ["Operational", "Needs energy", "Needs funding"]:
			return false
		for key in ["progress", "cycles", "staff_credits"]:
			if not _is_nonnegative_integer(archive.get(key)):
				return false
		if int(archive.progress) >= archive_data.INTERVAL:
			return false
	return true


func _valid_build_supply(state: Dictionary) -> bool:
	if state.build_supply_version != 1:
		return false
	var sites: Dictionary = {}
	for site in state.build_sites:
		sites[site.id] = true
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	for ship in state.ships:
		if ship.owner != state.player_faction_id:
			if ship.has("build_supply"):
				return false
			continue
		if not ship.get("build_supply") is Dictionary:
			return false
		var job: Dictionary = ship.build_supply
		if not job.get("enabled") is bool or job.get("phase") not in ["idle", "to_source", "to_site"] or not _is_nonnegative_integer(job.get("retry_ticks")):
			return false
		for key in ["site_id", "source_id", "ware_id", "wait_reason"]:
			if not job.get(key) is String:
				return false
		if not job.enabled:
			if not job.site_id.is_empty() or job.phase != "idle" or not job.source_id.is_empty() or not job.ware_id.is_empty() or int(job.retry_ticks) != 0 or not job.wait_reason.is_empty():
				return false
			continue
		if not sites.has(job.site_id) or ship.player_trader.enabled or ship.role != "Build Supplier":
			return false
		if job.phase == "idle" and (not job.source_id.is_empty() or not job.ware_id.is_empty()):
			return false
		if job.phase == "to_source" and (job.source_id.is_empty() or not wares.has(job.ware_id)):
			return false
		if job.phase == "to_site" and (not job.source_id.is_empty() or not wares.has(job.ware_id)):
			return false
	return true


func _valid_economy(state: Dictionary, factions: Dictionary, sectors: Dictionary) -> bool:
	if state.economy_version != 1 or not state.get("wares") is Array or not state.get("stations") is Array or not state.get("ledger") is Array or not _is_nonnegative_integer(state.get("next_transaction_id")):
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		if not ware is Dictionary or not ware.get("id") is String or str(ware.id).is_empty() or wares.has(ware.id) or not ware.get("name") is String or not _is_nonnegative_integer(ware.get("volume")) or int(ware.volume) < 1:
			return false
		wares[ware.id] = int(ware.volume)
	var stations: Dictionary = {}
	for station in state.stations:
		if not station is Dictionary or not station.get("id") is String or str(station.id).is_empty() or stations.has(station.id) or not station.get("name") is String or not factions.has(station.get("owner")) or not sectors.has(station.get("sector")) or not _is_nonnegative_integer(station.get("credits")) or not _is_nonnegative_integer(station.get("storage_capacity")):
			return false
		var station_used := 0
		for key in ["stock", "sell_prices", "buy_prices"]:
			if not station.get(key) is Dictionary:
				return false
			for ware_id in station[key]:
				if not wares.has(ware_id) or not _is_nonnegative_integer(station[key][ware_id]):
					return false
				if key != "stock" and (int(station[key][ware_id]) < 1 or int(station[key][ware_id]) > 1000000000):
					return false
				if key == "stock":
					station_used += int(station[key][ware_id]) * int(wares[ware_id])
		if station_used > int(station.storage_capacity):
			return false
		stations[station.id] = station
	if wares.is_empty() or stations.is_empty():
		return false
	for ship in state.ships:
		if not ship.get("cargo") is Dictionary or not ship.get("docked_at") is String or not _is_nonnegative_integer(ship.get("cargo_capacity")):
			return false
		var volume := 0
		for ware_id in ship.cargo:
			if not wares.has(ware_id) or not _is_nonnegative_integer(ship.cargo[ware_id]):
				return false
			volume += int(ship.cargo[ware_id]) * int(wares[ware_id])
		if volume > int(ship.cargo_capacity):
			return false
		if not str(ship.docked_at).is_empty():
			if not stations.has(ship.docked_at) or stations[ship.docked_at].sector != ship.sector or not ship.orders.is_empty() or not ship.travel.is_empty():
				return false
	var last_id := 0
	for entry in state.ledger:
		if not entry is Dictionary or not _is_nonnegative_integer(entry.get("id")) or int(entry.id) <= last_id:
			return false
		last_id = int(entry.id)
	if int(state.next_transaction_id) <= last_id:
		return false
	return true


func _valid_production(state: Dictionary) -> bool:
	if state.production_version != 1 or not state.get("recipes") is Array:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	var recipes: Dictionary = {}
	for recipe in state.recipes:
		if not recipe is Dictionary or not recipe.get("id") is String or str(recipe.id).is_empty() or recipes.has(recipe.id) or not recipe.get("name") is String or not _is_nonnegative_integer(recipe.get("cycle_ticks")) or int(recipe.cycle_ticks) < 1 or int(recipe.cycle_ticks) > 1000000:
			return false
		if not recipe.get("inputs") is Dictionary or not recipe.get("outputs") is Dictionary or recipe.outputs.is_empty():
			return false
		for key in ["inputs", "outputs"]:
			for ware_id in recipe[key]:
				if not wares.has(ware_id) or not _is_nonnegative_integer(recipe[key][ware_id]) or int(recipe[key][ware_id]) < 1 or int(recipe[key][ware_id]) > 1000000:
					return false
		var catalysts: Variant = recipe.get("catalysts", {})
		if not catalysts is Dictionary or not recipe.get("catalog_source", false) is bool:
			return false
		for ware_id in catalysts:
			if not wares.has(ware_id) or recipe.inputs.has(ware_id) or not _is_nonnegative_integer(catalysts[ware_id]) or int(catalysts[ware_id]) < 1 or int(catalysts[ware_id]) > 1000000:
				return false
		if recipe.get("catalog_source", false) and not catalysts.has("recorded_data"):
			return false
		var source: Variant = recipe.get("source", "")
		if not source is String or (source != "" and source != "sunlight"):
			return false
		var deposit: Variant = recipe.get("deposit", {})
		if not deposit is Dictionary:
			return false
		if not deposit.is_empty():
			if not wares.has(deposit.get("resource")) or not _is_nonnegative_integer(deposit.get("quantity")) or int(deposit.quantity) < 1 or int(deposit.quantity) > 1000000:
				return false
		if recipe.inputs.is_empty() and source == "" and deposit.is_empty():
			return false
		recipes[recipe.id] = recipe
	if recipes.is_empty():
		return false
	for station in state.stations:
		if not station.get("natural_sources") is Array or not station.get("deposits") is Dictionary or not station.get("production") is Array:
			return false
		for source in station.natural_sources:
			if source != "sunlight":
				return false
		for resource_id in station.deposits:
			if not wares.has(resource_id) or not _is_nonnegative_integer(station.deposits[resource_id]):
				return false
		for module in station.production:
			if not module is Dictionary or not recipes.has(module.get("recipe_id")) or not _is_nonnegative_integer(module.get("progress")) or not _is_nonnegative_integer(module.get("cycles")) or not module.get("status") is String:
				return false
			if int(module.progress) >= int(recipes[module.recipe_id].cycle_ticks):
				return false
	return true


func _valid_logistics(state: Dictionary) -> bool:
	if state.logistics_version != 1:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	for ship in state.ships:
		if not ship.has("autotrader"):
			continue
		if ship.owner == state.player_faction_id or not _is_nonnegative_integer(ship.get("credits")) or not ship.autotrader is Dictionary:
			return false
		var job: Dictionary = ship.autotrader
		if not job.get("enabled") is bool or not job.get("funded") is bool or not job.get("phase") is String or job.phase not in ["idle", "to_source", "to_destination"]:
			return false
		for key in ["home_station_id", "source_id", "destination_id", "ware_id"]:
			if not job.get(key) is String:
				return false
		if not _is_nonnegative_integer(job.get("quantity")) or not _is_nonnegative_integer(job.get("retry_ticks")) or job.home_station_id.is_empty():
			return false
		# A station can disappear while a ship is en route. The trader will
		# replan on arrival; that ordinary world change must not corrupt a save.
		if job.phase == "to_source" and (job.source_id.is_empty() or job.destination_id.is_empty() or not wares.has(job.ware_id) or int(job.quantity) < 1):
			return false
		if job.phase == "to_destination" and (not wares.has(job.ware_id) or int(job.quantity) < 1):
			return false
	return true


func _valid_player_roles(state: Dictionary) -> bool:
	if state.player_roles_version != 1:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	for ship in state.ships:
		if ship.owner != state.player_faction_id:
			if ship.has("player_trader"):
				return false
			continue
		if not ship.get("player_trader") is Dictionary:
			return false
		var job: Dictionary = ship.player_trader
		if not job.get("enabled") is bool or job.get("phase") not in ["idle", "to_source", "to_destination"]:
			return false
		for key in ["source_id", "destination_id", "ware_id"]:
			if not job.get(key) is String:
				return false
		for key in ["quantity", "managed_quantity", "retry_ticks"]:
			if not _is_nonnegative_integer(job.get(key)):
				return false
		if job.phase == "to_source" and (job.source_id.is_empty() or job.destination_id.is_empty() or not wares.has(job.ware_id) or int(job.quantity) < 1):
			return false
		if job.phase == "to_destination" and (not wares.has(job.ware_id) or int(job.quantity) < 1):
			return false
		if job.phase != "to_destination" and int(job.managed_quantity) != 0:
			return false
		if int(job.managed_quantity) > int(job.quantity) or int(job.managed_quantity) > int(ship.cargo.get(job.ware_id, 0)):
			return false
	return true


func _valid_construction(state: Dictionary, factions: Dictionary, sectors: Dictionary) -> bool:
	if state.construction_version not in [1, 2] or not state.get("construction_blueprints") is Dictionary or not state.get("construction_resources") is Dictionary or not state.get("build_sites") is Array or not _is_nonnegative_integer(state.get("next_build_site_id")) or int(state.next_build_site_id) < 1:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	var recipes: Dictionary = {}
	for recipe in state.recipes:
		recipes[recipe.id] = true
	for recipe_id in state.construction_blueprints:
		var blueprint: Variant = state.construction_blueprints[recipe_id]
		if not recipes.has(recipe_id) and not state.get("habitation_catalog", {}).has(recipe_id) and not state.get("education_catalog", {}).has(recipe_id) or not blueprint is Dictionary or not _is_nonnegative_integer(blueprint.get("fee")) or int(blueprint.fee) < 1 or not _is_nonnegative_integer(blueprint.get("ticks")) or int(blueprint.ticks) < 1 or int(blueprint.ticks) > 1000000 or not _is_nonnegative_integer(blueprint.get("storage")) or int(blueprint.storage) < 1 or not blueprint.get("materials") is Dictionary or blueprint.materials.is_empty():
			return false
		for ware_id in blueprint.materials:
			if not wares.has(ware_id) or not _is_nonnegative_integer(blueprint.materials[ware_id]) or int(blueprint.materials[ware_id]) < 1:
				return false
	for sector_id in sectors:
		if not state.construction_resources.has(sector_id):
			return false
	for sector_id in state.construction_resources:
		var pool: Variant = state.construction_resources[sector_id]
		if not sectors.has(sector_id) or not pool is Dictionary or not pool.get("natural_sources") is Array or not pool.get("deposits") is Dictionary:
			return false
		for source in pool.natural_sources:
			if source != "sunlight":
				return false
		for ware_id in pool.deposits:
			if not wares.has(ware_id) or not _is_nonnegative_integer(pool.deposits[ware_id]):
				return false
	var builder: Dictionary = {}
	for ship in state.ships:
		if ship.id == "npc_builder_001":
			builder = ship
	if builder.is_empty() or builder.owner == state.player_faction_id or not factions.has(builder.owner) or not _is_nonnegative_integer(builder.get("credits")) or not builder.get("build_assignment") is String or builder.has("autotrader"):
		return false
	var stations: Dictionary = {}
	for station in state.stations:
		stations[station.id] = station
		if station.has("resource_sector") and (station.owner != state.player_faction_id or station.resource_sector != station.sector or not state.construction_resources.has(station.resource_sector)):
			return false
	var sites: Dictionary = {}
	var station_sites: Dictionary = {}
	for site in state.build_sites:
		if not site is Dictionary or not site.get("id") is String or str(site.id).is_empty() or sites.has(site.id) or not site.get("station_id") is String or station_sites.has(site.station_id) or not stations.has(site.station_id) or not site.get("name") is String or not sectors.has(site.get("sector")) or not _is_nonnegative_integer(site.get("fee")) or int(site.fee) < 1 or not site.get("paused") is bool or not _is_nonnegative_integer(site.get("completed")) or not site.get("builder_id") is String or not site.get("status") is String or not site.get("build_storage") is Dictionary or not site.get("tasks") is Array or site.tasks.is_empty() or site.tasks.size() > 300 or int(site.completed) > site.tasks.size():
			return false
		var cancelled := false
		var refunded_fee := 0
		if state.construction_version == 2:
			if not site.get("cancelled") is bool or not _is_nonnegative_integer(site.get("refunded_fee")):
				return false
			cancelled = bool(site.cancelled)
			refunded_fee = int(site.refunded_fee)
			if (not cancelled and refunded_fee != 0) or (cancelled and site.paused):
				return false
		var station: Dictionary = stations[site.station_id]
		if station.owner != state.player_faction_id or station.sector != site.sector or station.get("resource_sector", "") != site.sector:
			return false
		var production_index := 0
		var habitat_index := 0
		var education_index := 0
		var required: Dictionary = {}
		var unstarted_fee := 0
		var storage_total := 0
		for index in range(site.tasks.size()):
			var task: Variant = site.tasks[index]
			if not task is Dictionary or (not recipes.has(task.get("recipe_id")) and not state.get("habitation_catalog", {}).has(task.get("recipe_id")) and not state.get("education_catalog", {}).has(task.get("recipe_id"))) or not _is_nonnegative_integer(task.get("duration")) or int(task.duration) < 1 or int(task.duration) > 1000000 or not _is_nonnegative_integer(task.get("storage")) or int(task.storage) < 1 or not task.get("materials") is Dictionary or task.materials.is_empty() or not task.get("started") is bool or not _is_nonnegative_integer(task.get("progress")):
				return false
			for ware_id in task.materials:
				if not wares.has(ware_id) or not _is_nonnegative_integer(task.materials[ware_id]) or int(task.materials[ware_id]) < 1:
					return false
				if not task.started:
					required[ware_id] = int(required.get(ware_id, 0)) + int(task.materials[ware_id])
			if not task.started:
				if not state.construction_blueprints.has(task.recipe_id):
					return false
				unstarted_fee += int(state.construction_blueprints[task.recipe_id].fee)
			if index < int(site.completed):
				if not task.started or int(task.progress) != int(task.duration):
					return false
				if state.get("habitation_catalog", {}).has(task.recipe_id):
					if not station.has("habitation") or habitat_index >= station.habitation.size() or station.habitation[habitat_index].id != task.recipe_id:
						return false
					habitat_index += 1
				elif state.get("education_catalog", {}).has(task.recipe_id):
					if not station.has("education") or education_index >= station.education.modules.size() or station.education.modules[education_index] != task.recipe_id:
						return false
					education_index += 1
				else:
					if production_index >= station.production.size() or station.production[production_index].recipe_id != task.recipe_id:
						return false
					production_index += 1
				storage_total += int(task.storage)
			elif index == int(site.completed):
				if int(task.progress) >= int(task.duration) or (not task.started and int(task.progress) != 0):
					return false
			elif task.started or int(task.progress) != 0:
				return false
		if int(station.storage_capacity) != storage_total or station.production.size() != production_index or (state.has("habitation_version") and station.habitation.size() != habitat_index) or (state.has("education_version") and station.education.modules.size() != education_index):
			return false
		if state.construction_version == 2 and cancelled and (refunded_fee != unstarted_fee or refunded_fee > int(site.fee)):
			return false
		if cancelled and not str(site.builder_id).is_empty():
			if int(site.completed) >= site.tasks.size() or not bool(site.tasks[int(site.completed)].started):
				return false
		for ware_id in site.build_storage:
			if not wares.has(ware_id) or not _is_nonnegative_integer(site.build_storage[ware_id]) or int(site.build_storage[ware_id]) > int(required.get(ware_id, 0)):
				return false
		if not str(site.builder_id).is_empty() and (site.builder_id != builder.id or builder.build_assignment != site.id or int(site.completed) == site.tasks.size()):
			return false
		sites[site.id] = site
		station_sites[site.station_id] = true
	if not str(builder.build_assignment).is_empty() and (not sites.has(builder.build_assignment) or sites[builder.build_assignment].builder_id != builder.id):
		return false
	if sites.has("buildsite_%d" % int(state.next_build_site_id)) or stations.has("player_station_%d" % int(state.next_build_site_id)):
		return false
	return true
