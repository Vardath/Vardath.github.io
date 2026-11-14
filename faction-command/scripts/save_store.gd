extends RefCounted
## One local save slot. A verified temporary file replaces the primary only
## after the previous valid primary has been retained as a backup.

const FORMAT_VERSION := 1
const MAX_SAVE_BYTES := 64 * 1024 * 1024
const ArchivesScript = preload("res://scripts/archives.gd")
const ResearchScript = preload("res://scripts/research.gd")


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
	return not state.has("population_version") or _valid_population(state)


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
		if not _is_nonnegative_integer(entry.get("hab_capacity")) or int(entry.hab_capacity) != 0 or entry.get("housing_status") != "unimplemented":
			return false
		var counts: Dictionary = entry.cohorts
		if counts.size() != 5:
			return false
		for group in ["children", "students", "available_workers", "assigned_workers", "retirees"]:
			if not _is_nonnegative_integer(counts.get(group)) or int(counts[group]) > 1000000:
				return false
		if int(counts.children) != 0 or int(counts.students) != 0 or int(counts.assigned_workers) != 0 or int(counts.retirees) != 0:
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
		if not recipes.has(recipe_id) or not blueprint is Dictionary or not _is_nonnegative_integer(blueprint.get("fee")) or int(blueprint.fee) < 1 or not _is_nonnegative_integer(blueprint.get("ticks")) or int(blueprint.ticks) < 1 or int(blueprint.ticks) > 1000000 or not _is_nonnegative_integer(blueprint.get("storage")) or int(blueprint.storage) < 1 or not blueprint.get("materials") is Dictionary or blueprint.materials.is_empty():
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
		if station.owner != state.player_faction_id or station.sector != site.sector or station.get("resource_sector", "") != site.sector or station.production.size() != int(site.completed):
			return false
		var required: Dictionary = {}
		var unstarted_fee := 0
		var storage_total := 0
		for index in range(site.tasks.size()):
			var task: Variant = site.tasks[index]
			if not task is Dictionary or not recipes.has(task.get("recipe_id")) or not _is_nonnegative_integer(task.get("duration")) or int(task.duration) < 1 or int(task.duration) > 1000000 or not _is_nonnegative_integer(task.get("storage")) or int(task.storage) < 1 or not task.get("materials") is Dictionary or task.materials.is_empty() or not task.get("started") is bool or not _is_nonnegative_integer(task.get("progress")):
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
				if not task.started or int(task.progress) != int(task.duration) or station.production[index].recipe_id != task.recipe_id:
					return false
				storage_total += int(task.storage)
			elif index == int(site.completed):
				if int(task.progress) >= int(task.duration) or (not task.started and int(task.progress) != 0):
					return false
			elif task.started or int(task.progress) != 0:
				return false
		if int(station.storage_capacity) != storage_total:
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
