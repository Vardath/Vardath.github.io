extends RefCounted
## Faction-funded historical stations. Their records are authored data; their
## budgets, consumed energy, wages and visits are persistent world state.

const DATA_PATH := "res://data/archives.json"
const INTERVAL := 30
const TARGET_BUDGET := 120
const FUNDING_PER_INTERVAL := 60
const ENERGY_PER_CYCLE := 1
const STAFF_PAY_PER_CYCLE := 2
const ENERGY_BUFFER := 4
const ENERGY_BUY_PRICE := 11

var definitions: Dictionary = {}
var ware_definitions: Array = []
var recipe_definitions: Array = []
var blueprint_definitions: Dictionary = {}


func _load_definitions() -> Error:
	if not definitions.is_empty():
		return OK
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not data is Dictionary or data.get("schema_version") != 1 or not data.get("archives") is Array or data.archives.is_empty() or not data.get("wares") is Array or not data.get("recipes") is Array or not data.get("blueprints") is Dictionary:
		return ERR_INVALID_DATA
	var loaded: Dictionary = {}
	for entry in data.archives:
		if not entry is Dictionary:
			return ERR_INVALID_DATA
		for key in ["id", "name", "owner", "sector", "sponsor", "civilization", "homeworld", "world_type"]:
			if not entry.get(key) is String or str(entry[key]).is_empty():
				return ERR_INVALID_DATA
		if loaded.has(entry.id) or not entry.get("records") is Array or entry.records.is_empty() or not entry.get("research_subjects") is Array or entry.research_subjects.is_empty():
			return ERR_INVALID_DATA
		for subject in entry.research_subjects:
			if not subject is String or str(subject).is_empty():
				return ERR_INVALID_DATA
		for record in entry.records:
			if not record is Dictionary or not record.get("title") is String or str(record.title).is_empty() or not record.get("text") is String or str(record.text).is_empty() or not record.get("medium") is String or str(record.medium).is_empty():
				return ERR_INVALID_DATA
		loaded[entry.id] = entry.duplicate(true)
	if data.wares.size() != 2 or data.recipes.size() != 2 or not data.blueprints.has("media_fabrication") or not data.blueprints.has("data_reproduction"):
		return ERR_INVALID_DATA
	for ware in data.wares:
		if not ware is Dictionary or ware.get("id") not in ["blank_media", "recorded_data"] or not ware.get("name") is String or int(ware.get("volume", 0)) < 1:
			return ERR_INVALID_DATA
	for recipe in data.recipes:
		if not recipe is Dictionary or recipe.get("id") not in ["media_fabrication", "data_reproduction"] or not recipe.get("name") is String or int(recipe.get("cycle_ticks", 0)) < 1 or not recipe.get("inputs") is Dictionary or not recipe.get("outputs") is Dictionary:
			return ERR_INVALID_DATA
	ware_definitions = data.wares.duplicate(true)
	recipe_definitions = data.recipes.duplicate(true)
	blueprint_definitions = data.blueprints.duplicate(true)
	definitions = loaded
	return OK


func prepare(target: Dictionary) -> Error:
	var loaded := _load_definitions()
	if loaded != OK:
		return loaded
	if target.has("archive_version"):
		return OK if target.archive_version == 1 else ERR_UNAVAILABLE
	var factions: Dictionary = {}
	var sectors: Dictionary = {}
	var station_ids: Dictionary = {}
	var ware_ids: Dictionary = {}
	var recipe_ids: Dictionary = {}
	for faction in target.factions:
		factions[faction.id] = true
	for sector in target.sectors:
		sectors[sector.id] = true
	for station in target.stations:
		station_ids[station.id] = true
	for ware in target.wares:
		ware_ids[ware.id] = true
	for recipe in target.recipes:
		recipe_ids[recipe.id] = true
	for ware in ware_definitions:
		if ware_ids.has(ware.id):
			return ERR_ALREADY_IN_USE
		ware_ids[ware.id] = true
	for recipe in recipe_definitions:
		if recipe_ids.has(recipe.id) or target.construction_blueprints.has(recipe.id):
			return ERR_ALREADY_IN_USE
		recipe_ids[recipe.id] = true
	var additions: Array = []
	for entry in definitions.values():
		if not factions.has(entry.owner) or entry.owner == target.player_faction_id or not sectors.has(entry.sector):
			return ERR_INVALID_DATA
		if station_ids.has(entry.id):
			return ERR_ALREADY_IN_USE
		var stock: Dictionary = {}
		for ware in target.wares:
			stock[ware.id] = 0
		for ware in ware_definitions:
			stock[ware.id] = 0
		if not stock.has("energy_cells"):
			return ERR_INVALID_DATA
		var modules := [{"recipe_id":"media_fabrication", "progress":0, "cycles":0, "status":"Waiting"}, {"recipe_id":"data_reproduction", "progress":0, "cycles":0, "status":"Waiting"}]
		additions.append({"id":entry.id, "name":entry.name, "owner":entry.owner, "sector":entry.sector, "credits":0, "storage_capacity":80, "stock":stock, "sell_prices":{"recorded_data":55}, "buy_prices":{"energy_cells":ENERGY_BUY_PRICE, "alloy_plates":25}, "natural_sources":[], "deposits":{}, "production":modules, "archive":{"sponsor":entry.sponsor, "progress":0, "cycles":0, "staff_credits":0, "status":"Needs energy"}})
	# Existing accounts, cargo and production remain unchanged. New definitions
	# and empty stock slots introduce no money, original records or trade goods.
	target.wares.append_array(ware_definitions.duplicate(true))
	target.recipes.append_array(recipe_definitions.duplicate(true))
	for recipe_id in blueprint_definitions:
		target.construction_blueprints[recipe_id] = blueprint_definitions[recipe_id].duplicate(true)
	for station in target.stations:
		for ware in ware_definitions:
			station.stock[ware.id] = 0
	target.stations.append_array(additions)
	target["visited_archives"] = []
	target["archive_version"] = 1
	return OK


func definition(station_id: String) -> Dictionary:
	return definitions.get(station_id, {})


func read(world: RefCounted, ship_id: String, station_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var station: Dictionary = world._find_station(station_id)
	var entry := definition(station_id)
	if ship.is_empty() or station.is_empty() or entry.is_empty() or not station.has("archive") or ship.owner != world.state.player_faction_id:
		return {"ok":false, "message":"Archive or ship is unavailable."}
	if ship.docked_at != station_id or ship.sector != station.sector or not ship.orders.is_empty() or not ship.travel.is_empty():
		return {"ok":false, "message":"Dock at this archive to read its records."}
	var first_visit: bool = station_id not in world.state.visited_archives
	if first_visit:
		world.state.visited_archives.append(station_id)
	return {"ok":true, "first_visit":first_visit, "entry":entry.duplicate(true)}


func _sponsor(world: RefCounted, station: Dictionary) -> Dictionary:
	var sponsor: Dictionary = world._find_station(str(station.archive.sponsor))
	if not sponsor.is_empty() and sponsor.id != station.id and sponsor.owner == station.owner and not sponsor.has("archive"):
		return sponsor
	for candidate in world.state.stations:
		if candidate.id != station.id and candidate.owner == station.owner and not candidate.has("archive"):
			return candidate
	return {}


func _status(station: Dictionary) -> String:
	if int(station.stock.get("energy_cells", 0)) < ENERGY_PER_CYCLE:
		return "Needs energy"
	if int(station.credits) < STAFF_PAY_PER_CYCLE:
		return "Needs funding"
	return "Operational"


func tick(world: RefCounted) -> void:
	for station in world.state.stations:
		if not station.has("archive"):
			continue
		var archive: Dictionary = station.archive
		if int(world.state.tick) % INTERVAL == 0:
			var sponsor := _sponsor(world, station)
			if not sponsor.is_empty():
				var transfer := mini(FUNDING_PER_INTERVAL, mini(int(sponsor.credits), maxi(0, TARGET_BUDGET - int(station.credits))))
				sponsor.credits = int(sponsor.credits) - transfer
				station.credits = int(station.credits) + transfer
		archive.status = _status(station)
		if archive.status != "Operational":
			continue
		archive.progress = int(archive.progress) + 1
		if int(archive.progress) >= INTERVAL:
			station.stock.energy_cells = int(station.stock.energy_cells) - ENERGY_PER_CYCLE
			station.credits = int(station.credits) - STAFF_PAY_PER_CYCLE
			archive.staff_credits = int(archive.staff_credits) + STAFF_PAY_PER_CYCLE
			archive.progress = 0
			archive.cycles = int(archive.cycles) + 1
			archive.status = _status(station)
