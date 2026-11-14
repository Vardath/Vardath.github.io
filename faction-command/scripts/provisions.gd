extends RefCounted
## Versioned civilian supplies. Adds real new wares, recipes, build costs and
## finite water-ice sector deposits to the established conservation economy.
## No NPC market receives stock or credits; goods are obtained only through
## physically paid building, mining/extraction, refining and transport.

const DATA_PATH := "res://data/provisions.json"
const VERSION := 1
const WARE_IDS := ["ice", "potable_water", "food_rations", "medical_supplies"]
const RECIPE_IDS := ["ice_extraction", "water_purification", "hydroponics", "medical_synthesis"]


func definitions() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not parsed is Dictionary or parsed.get("schema_version") != VERSION or not parsed.get("wares") is Array or not parsed.get("recipes") is Array or not parsed.get("blueprints") is Dictionary or not parsed.get("sector_ice_deposits") is Dictionary or not parsed.get("habitat_needs_per_60") is Dictionary:
		return {}
	if parsed.wares.size() != 4 or parsed.recipes.size() != 4 or parsed.blueprints.size() != 4:
		return {}
	for index in range(4):
		if not parsed.wares[index] is Dictionary or str(parsed.wares[index].get("id", "")) != WARE_IDS[index] or not parsed.recipes[index] is Dictionary or str(parsed.recipes[index].get("id", "")) != RECIPE_IDS[index] or not parsed.blueprints.has(RECIPE_IDS[index]):
			return {}
	for ware_id in ["potable_water", "food_rations", "medical_supplies"]:
		if int(parsed.habitat_needs_per_60.get(ware_id, 0)) != 1:
			return {}
	return parsed


func prepare(target: Dictionary) -> Error:
	if target.has("provisions_version"):
		return OK if int(target.provisions_version) == VERSION and target.get("provisions_catalog") is Dictionary else ERR_UNAVAILABLE
	if target.has("provisions_catalog") or not target.has("habitation_version") or not target.has("construction_resources") or not target.get("wares") is Array or not target.get("recipes") is Array:
		return ERR_INVALID_DATA
	var data: Dictionary = definitions()
	if data.is_empty():
		return ERR_INVALID_DATA
	for item in data.wares:
		for known in target.wares:
			if known.id == item.id:
				return ERR_ALREADY_IN_USE
	for recipe in data.recipes:
		for known in target.recipes:
			if known.id == recipe.id:
				return ERR_ALREADY_IN_USE
		if target.construction_blueprints.has(recipe.id):
			return ERR_ALREADY_IN_USE
	# Only sector deposits are seeded. Those are *geological reserves*, not
	# extracted goods in station stock or ship cargo. Existing resources,
	# completed builds and all player finances are left intact.
	for sector_id in data.sector_ice_deposits:
		if not target.construction_resources.has(sector_id) or target.construction_resources[sector_id].deposits.has("ice"):
			return ERR_INVALID_DATA
	for ware in data.wares:
		target.wares.append(ware.duplicate(true))
		for station in target.stations:
			station.stock[ware.id] = 0
	for recipe in data.recipes:
		target.recipes.append(recipe.duplicate(true))
		target.construction_blueprints[recipe.id] = data.blueprints[recipe.id].duplicate(true)
	for sector_id in data.sector_ice_deposits:
		target.construction_resources[sector_id].deposits["ice"] = int(data.sector_ice_deposits[sector_id])
	target["provisions_catalog"] = {
		"wares":WARE_IDS.duplicate(),
		"recipes":RECIPE_IDS.duplicate(),
		"habitat_needs_per_60":data.habitat_needs_per_60.duplicate(true),
		"sector_ice_deposits":data.sector_ice_deposits.duplicate(true)
	}
	target["provisions_version"] = VERSION
	return OK


func needs_per_module(world: RefCounted, module_id: String) -> Dictionary:
	if not world.state.has("provisions_version") or not world.habitation.is_habitat(world, module_id):
		return {}
	return world.state.provisions_catalog.habitat_needs_per_60.duplicate(true)


func facility_needs(world: RefCounted, station: Dictionary, projected_occupants: int = -1) -> Dictionary:
	var totals: Dictionary = {}
	for module in station.get("habitation", []):
		totals["energy_cells"] = int(totals.get("energy_cells", 0)) + int(world.state.habitation_catalog[module.id].energy_per_60)
		for ware_id in needs_per_module(world, str(module.id)):
			totals[ware_id] = int(totals.get(ware_id, 0)) + int(world.state.provisions_catalog.habitat_needs_per_60[ware_id])
	# Settled adults consume *additional* finite supplies over module baseline.
	# Optional projected occupancy checks the full bill BEFORE a new landing.
	if int(world.state.get("settlement_version", 0)) >= 2:
		var occupants: int = projected_occupants
		if occupants < 0:
			var cohort: Dictionary = world.population.station_cohort(world, str(station.get("id", "")))
			occupants = world.demographics.residents(cohort) if world.state.has("demographics_version") else int(cohort.get("cohorts", {}).get("assigned_workers", 0))
		for ware_id in world.settlement.resident_needs(occupants):
			totals[ware_id] = int(totals.get(ware_id, 0)) + int(world.settlement.resident_needs(occupants)[ware_id])
	return totals


func missing_provision(world: RefCounted, station: Dictionary, projected_occupants: int = -1) -> String:
	if not world.state.has("provisions_version") or station.get("habitation", []).is_empty():
		return ""
	# A station stock report is actionable and cannot silently count goods
	# still on a ship or stranded in uncompleted construction storage.
	var needed_wares: Dictionary = facility_needs(world, station, projected_occupants)
	for ware_id in ["energy_cells", "potable_water", "food_rations", "medical_supplies"]:
		var needed: int = int(needed_wares.get(ware_id, 0))
		if int(station.stock.get(ware_id, 0)) < needed:
			return str(world._find_ware(ware_id).get("name", ware_id))
	return ""
