extends RefCounted
## Pass 31: circular residential ecology; only physically consumed supplies
## can become waste. Production uses the existing station recipe engine, real
## builder resources, real storage and normal warehouse / ship transfer flows.
## No free settlers, water, food, soil or wastewater are created on migration.

const DATA_PATH := "res://data/ecology.json"
const VERSION := 1
const WARE_IDS := ["organic_waste", "fertile_soil"]
const RECIPE_IDS := ["water_recycling", "soil_agriculture"]
const WASTE_SOURCES := ["potable_water", "food_rations"]


func definitions() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not parsed is Dictionary or parsed.get("schema_version") != VERSION or not parsed.get("wares") is Array or not parsed.get("recipes") is Array or not parsed.get("blueprints") is Dictionary or not parsed.get("waste_sources") is Dictionary:
		return {}
	if parsed.wares.size() != 2 or parsed.recipes.size() != 2 or parsed.blueprints.size() != 2 or parsed.waste_sources != {"potable_water":1, "food_rations":1}:
		return {}
	for i in range(2):
		if not parsed.wares[i] is Dictionary or parsed.wares[i].get("id") != WARE_IDS[i] or parsed.wares[i].get("volume") != 1 or not parsed.wares[i].get("name") is String:
			return {}
		if not parsed.recipes[i] is Dictionary or parsed.recipes[i].get("id") != RECIPE_IDS[i] or not parsed.recipes[i].get("name") is String or not parsed.blueprints.has(RECIPE_IDS[i]):
			return {}
	var recycler: Dictionary = parsed.recipes[0]
	var farmland: Dictionary = parsed.recipes[1]
	if int(recycler.get("cycle_ticks", 0)) != 15 or recycler.get("inputs") != {"organic_waste":2, "energy_cells":1} or recycler.get("outputs") != {"potable_water":1, "fertile_soil":1}:
		return {}
	if int(farmland.get("cycle_ticks", 0)) != 20 or farmland.get("inputs") != {"fertile_soil":1, "potable_water":2, "energy_cells":1} or farmland.get("outputs") != {"food_rations":4}:
		return {}
	for recipe_id in RECIPE_IDS:
		var blueprint: Dictionary = parsed.blueprints[recipe_id]
		if int(blueprint.get("fee", 0)) < 1 or int(blueprint.get("ticks", 0)) < 1 or int(blueprint.get("storage", 0)) < 1 or not blueprint.get("materials") is Dictionary:
			return {}
		if int(blueprint.materials.get("alloy_plates", 0)) < 1 or int(blueprint.materials.get("energy_cells", 0)) < 1:
			return {}
	return parsed


func prepare(target: Dictionary) -> Error:
	if target.has("ecology_version"):
		return OK if int(target.ecology_version) == VERSION and target.get("ecology_catalog") is Dictionary else ERR_UNAVAILABLE
	if target.has("ecology_catalog") or int(target.get("settlement_version", 0)) != 2 or not target.get("wares") is Array or not target.get("recipes") is Array or not target.get("construction_blueprints") is Dictionary:
		return ERR_INVALID_DATA
	var data: Dictionary = definitions()
	if data.is_empty():
		return ERR_INVALID_DATA
	for ware in data.wares:
		for prior in target.wares:
			if prior.id == ware.id:
				return ERR_ALREADY_IN_USE
	for recipe in data.recipes:
		for prior in target.recipes:
			if prior.id == recipe.id:
				return ERR_ALREADY_IN_USE
		if target.construction_blueprints.has(recipe.id):
			return ERR_ALREADY_IN_USE
	# Resource migration only adds empty stock keys; no phantom recovered
	# waste from previous resident service periods is backfilled.
	for ware in data.wares:
		target.wares.append(ware.duplicate(true))
		for station in target.stations:
			station.stock[ware.id] = 0
	for recipe in data.recipes:
		target.recipes.append(recipe.duplicate(true))
		target.construction_blueprints[recipe.id] = data.blueprints[recipe.id].duplicate(true)
	target["ecology_catalog"] = {
		"wares":WARE_IDS.duplicate(),
		"recipes":RECIPE_IDS.duplicate(),
		"waste_sources":data.waste_sources.duplicate(true)
	}
	target["ecology_version"] = VERSION
	return OK


func recovered_waste(paid_resident_needs: Dictionary) -> int:
	# Reclaimed waste is at most the volume of the water and food actually
	# debited, and is generated only after a successful residential service.
	var quantity := 0
	for ware_id in WASTE_SOURCES:
		quantity += maxi(0, int(paid_resident_needs.get(ware_id, 0)))
	return quantity


func record_resident_waste(world: RefCounted, station: Dictionary, paid_needs: Dictionary) -> int:
	if int(world.state.get("ecology_version", 0)) != VERSION:
		return 0
	var generated: int = recovered_waste(paid_needs)
	if generated < 1:
		return 0
	# Existing water/food inputs have just left station storage, so this
	# replacement waste occupies no extra volume. The source is physical,
	# counted residents; never NPC recruitment pools or imaginary people.
	station.stock["organic_waste"] = int(station.stock.get("organic_waste", 0)) + generated
	world._record_transaction("resident_biowaste", "", str(station.id), "organic_waste", generated, 0, 0)
	return generated
