extends RefCounted
## Pass 37D: additive, physically manufactured animal diets and veterinary
## containment. Existing v30 animals and ordinary emergency rations survive.
## This module does not simulate infections or conjure clinical supplies.

const VERSION := 1
const DATA_PATH := "res://data/animal_feed.json"
const WARE_IDS := ["emberhorn_fodder", "dustwhistle_nectar", "emberhorn_woven_cloth", "dustwhistle_insulation"]
const RECIPE_IDS := ["emberhorn_fodder_mill", "dustwhistle_nectar_blender", "emberhorn_fibre_loom", "dustwhistle_insulation_press", "animal_veterinary_clinic"]
const FEED_BY_SPECIES := {"emberhorn":"emberhorn_fodder", "dustwhistle":"dustwhistle_nectar"}
const EXPECTED_INPUTS := [
	{"mirealgae_biomass":2, "food_rations":1, "energy_cells":1},
	{"sunlace_fruit":2, "potable_water":1, "energy_cells":1},
	{"emberhorn_fur":2, "energy_cells":1},
	{"dustwhistle_feathers":2, "alloy_plates":1, "energy_cells":1},
	{}
]
const EXPECTED_OUTPUTS := [
	{"emberhorn_fodder":5},
	{"dustwhistle_nectar":5},
	{"emberhorn_woven_cloth":1},
	{"dustwhistle_insulation":1},
	{}
]
const EXPECTED_DURATIONS := [28, 24, 30, 32, 60]


func _integer(value: Variant, minimum: int, maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and floor(float(value)) == float(value) and int(value) >= minimum and int(value) <= maximum


func _quantities_match(actual: Variant, needed: Dictionary) -> bool:
	if not actual is Dictionary or actual.size() != needed.size():
		return false
	for id in needed:
		if not _integer(actual.get(id), int(needed[id]), int(needed[id])):
			return false
	return true


func definitions() -> Dictionary:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not data is Dictionary or data.get("schema_version") != VERSION or not data.get("scope") is String or not data.get("wares") is Array or not data.get("recipes") is Array or not data.get("blueprints") is Dictionary:
		return {}
	if data.wares.size() != WARE_IDS.size() or data.recipes.size() != RECIPE_IDS.size() or data.blueprints.size() != RECIPE_IDS.size() or data.get("species_feed") != FEED_BY_SPECIES or data.get("animal_feed_bonus") != {"breeding_step":2, "maturation_step":2} or data.get("veterinary") != {"medical_supplies_per_two_animals":1,"energy_cells_per_treatment":1}:
		return {}
	for i in range(WARE_IDS.size()):
		var ware: Variant = data.wares[i]
		if not ware is Dictionary or ware.get("id") != WARE_IDS[i] or not ware.get("name") is String or not _integer(ware.get("volume"), 1, 100):
			return {}
	for i in range(RECIPE_IDS.size()):
		var recipe: Variant = data.recipes[i]
		if not recipe is Dictionary or recipe.get("id") != RECIPE_IDS[i] or not recipe.get("name") is String or not _integer(recipe.get("cycle_ticks"), EXPECTED_DURATIONS[i], EXPECTED_DURATIONS[i]) or not _quantities_match(recipe.get("inputs"), EXPECTED_INPUTS[i]) or not _quantities_match(recipe.get("outputs"), EXPECTED_OUTPUTS[i]):
			return {}
		if bool(recipe.get("manual_animal_care", false)) != (i == 4):
			return {}
		if i != 4 and recipe.has("manual_animal_care"):
			return {}
		var blueprint: Variant = data.blueprints.get(str(recipe.id))
		if not blueprint is Dictionary or not _integer(blueprint.get("fee"), 1, 1000000) or not _integer(blueprint.get("ticks"), 1, 10000) or not _integer(blueprint.get("storage"), 1, 10000) or not blueprint.get("materials") is Dictionary or blueprint.materials.size() != 2:
			return {}
		if not _integer(blueprint.materials.get("alloy_plates"), 1, 10000) or not _integer(blueprint.materials.get("energy_cells"), 1, 10000):
			return {}
	return data


func prepare(target: Dictionary) -> Error:
	var defs: Dictionary = definitions()
	if defs.is_empty():
		return ERR_INVALID_DATA
	if target.has("animal_feed_version"):
		return OK if target.animal_feed_version == VERSION and target.get("animal_feed_catalog") == defs and target.get("animal_quarantine") is Dictionary else ERR_UNAVAILABLE
	if target.has("animal_feed_catalog") or target.has("animal_quarantine") or target.get("livestock_version") != 1:
		return ERR_INVALID_DATA
	for ware in defs.wares:
		if target.wares.any(func(item): return item.id == ware.id):
			return ERR_ALREADY_IN_USE
		for station in target.stations:
			if station.stock.has(str(ware.id)):
				return ERR_ALREADY_IN_USE
		for ship in target.ships:
			if ship.cargo.has(str(ware.id)):
				return ERR_ALREADY_IN_USE
	for recipe in defs.recipes:
		if target.recipes.any(func(item): return item.id == recipe.id) or target.construction_blueprints.has(str(recipe.id)):
			return ERR_ALREADY_IN_USE
	# An existing v30 saved world receives only new definitions and zero
	# added feed/material stock; captured animals, ages and care ticks persist.
	for ware in defs.wares:
		target.wares.append(ware.duplicate(true))
		for station in target.stations:
			station.stock[str(ware.id)] = 0
	for recipe in defs.recipes:
		target.recipes.append(recipe.duplicate(true))
		target.construction_blueprints[str(recipe.id)] = defs.blueprints[str(recipe.id)].duplicate(true)
	target["animal_feed_version"] = VERSION
	target["animal_feed_catalog"] = defs.duplicate(true)
	target["animal_quarantine"] = {}
	return OK


func feed_for(animal_id: String) -> String:
	return str(FEED_BY_SPECIES.get(animal_id, ""))


func is_quarantined(world: RefCounted, station_id: String, animal_id: String) -> bool:
	return bool(world.state.get("animal_quarantine", {}).get(station_id + "|" + animal_id, false))


func clinic_count(station: Dictionary) -> int:
	var count := 0
	for module in station.get("production", []):
		if str(module.recipe_id) == "animal_veterinary_clinic":
			count += 1
	return count


func set_quarantine(world: RefCounted, station_id: String, animal_id: String) -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var animal: Dictionary = world.livestock.species_by_id(world, animal_id)
	if station.is_empty() or animal.is_empty() or station.owner != world.state.player_faction_id:
		return {"ok":false, "message":"Only existing species in an owned station may be isolated."}
	if world.livestock.pen_count(station, animal) == 0 or world.livestock._headcount(station, animal) < 1:
		return {"ok":false, "message":"A completed habitat containing actual living animals is required."}
	if is_quarantined(world, station_id, animal_id):
		return {"ok":false, "message":"The animal habitat is already quarantined. A veterinary treatment is required to release the restriction."}
	world.state.animal_quarantine[station_id + "|" + animal_id] = true
	return {"ok":true, "message":"The existing %s cohort has been physically isolated from live-animal loading, unloading, breeding and terminal harvesting. Normal sustenance continues." % str(animal.name)}


func treat(world: RefCounted, station_id: String, animal_id: String) -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var animal: Dictionary = world.livestock.species_by_id(world, animal_id)
	if station.is_empty() or animal.is_empty() or station.owner != world.state.player_faction_id:
		return {"ok":false, "message":"Choose an owned station and a registered local animal species."}
	if clinic_count(station) < 1:
		return {"ok":false, "message":"Commission a completed Veterinary Clinic first; there are no free remote treatments."}
	var heads: int = world.livestock._headcount(station, animal)
	if heads < 1:
		return {"ok":false, "message":"There are no living animals to examine."}
	var key: String = station_id + "|" + animal_id
	var status: Dictionary = world.state.livestock_care.get(key, {})
	if status.is_empty() or (not is_quarantined(world, station_id, animal_id) and int(status.get("shortages", 0)) == 0):
		return {"ok":false, "message":"Herd is neither isolated nor exhibiting a current husbandry warning."}
	var meds: int = int(ceil(float(heads) / 2.0))
	if int(station.stock.get("medical_supplies", 0)) < meds or int(station.stock.get("energy_cells", 0)) < 1:
		return {"ok":false, "message":"Clinical intervention requires %d real Medical Supplies and one actual Energy Cell." % meds}
	station.stock.medical_supplies = int(station.stock.medical_supplies) - meds
	station.stock.energy_cells = int(station.stock.energy_cells) - 1
	status.shortages = 0
	status.last_status = "Veterinary recovery; monitor actual animal diet, water and electricity"
	world.state.animal_quarantine.erase(key)
	# Historical and clinical receipts are linked by station, species and tick.
	world._record_transaction("animal_treatment_medical", "", station_id, animal_id, meds, 0, 0)
	world._record_transaction("animal_treatment_energy", "", station_id, animal_id, 1, 0, 0)
	world._record_transaction("animal_treated", "", station_id, animal_id, 1, 0, 0)
	return {"ok":true, "message":"Treated %d living %s with %d Medical Supplies and one Energy Cell. Quarantine released; future food and water still required." % [heads, str(animal.name), meds]}


func report(world: RefCounted, station: Dictionary) -> String:
	var lines: Array[String] = []
	for animal in world.state.livestock_catalog.animals:
		if world.livestock.pen_count(station, animal) == 0:
			continue
		var headcount: int = world.livestock._headcount(station, animal)
		lines.append("%s — tailored food: %s (%d units in store for %d live animals). Emergency Food Rations remain a baseline diet. %s" % [animal.name, str(world._find_ware(feed_for(str(animal.id))).get("name", feed_for(str(animal.id)))), int(station.stock.get(feed_for(str(animal.id)), 0)), headcount, "QUARANTINED: no live movement, reproduction or hide processing" if is_quarantined(world, str(station.id), str(animal.id)) else "Biosecurity: unrestricted"])
	return "No species-specific habitats or diets are established." if lines.is_empty() else "\n".join(lines) + "\nVeterinary clinics: %d completed. Tailored feed accelerates juvenile growth and breeding; ordinary rations sustain life without the bonus. Neither creates water, power or medicine." % clinic_count(station)
