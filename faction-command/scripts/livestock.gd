extends RefCounted
## Pass 37C: live, counted animal cargo and finite station husbandry.
## Old player saves have no captured animals. All births, manure, fur,
## feathers and terminal hides require previously acquired life and inputs.
## Exotic pet bonding, disease propagation and alien-specific feed follow later.

const VERSION := 1
const DATA_PATH := "res://data/livestock.json"
const ANIMAL_IDS := ["emberhorn", "dustwhistle"]
const ADULT_WARES := ["emberhorn_grazer", "dustwhistle_moth"]
const YOUNG_WARES := ["emberhorn_calf", "dustwhistle_larva"]
const MATERIAL_WARES := ["emberhorn_fur", "dustwhistle_feathers"]
const ALL_WARES := ["emberhorn_grazer", "emberhorn_calf", "emberhorn_fur", "emberhorn_leather", "dustwhistle_moth", "dustwhistle_larva", "dustwhistle_feathers"]
const RECIPE_IDS := ["emberhorn_paddock", "dustwhistle_aviary"]
const CARE_TICKS := 60
const STASIS_TICKS := 60
const HUNGER_LIMIT := 3


func _whole(value: Variant, minimum: int, maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value)) and int(value) >= minimum and int(value) <= maximum


func _amounts_match(actual: Variant, required: Dictionary) -> bool:
	if not actual is Dictionary or actual.size() != required.size():
		return false
	for id in required:
		if not _whole(actual.get(id), int(required[id]), int(required[id])):
			return false
	return true


func definitions() -> Dictionary:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not data is Dictionary or data.get("schema_version") != VERSION or not data.get("scope") is String or not data.get("animals") is Array or not data.get("wares") is Array or not data.get("recipes") is Array or not data.get("blueprints") is Dictionary:
		return {}
	if data.animals.size() != 2 or data.wares.size() != 7 or data.recipes.size() != 2 or data.blueprints.size() != 2 or not _whole(data.get("care_interval_ticks"), 60, 60) or not _whole(data.get("ship_stasis_interval_ticks"), 60, 60) or not _whole(data.get("shortage_cycles_before_death"), 3, 3):
		return {}
	var biota: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/biota.json"))
	if not biota is Dictionary or not biota.get("organisms") is Array:
		return {}
	var defined_species: Dictionary = {}
	for item in biota.organisms:
		defined_species[str(item.id)] = item
	for i in range(2):
		var animal: Variant = data.animals[i]
		if not animal is Dictionary or animal.get("id") != ANIMAL_IDS[i] or animal.get("species_id") != ADULT_WARES[i] or not defined_species.has(animal.get("species_id")):
			return {}
		if defined_species[animal.species_id].kind != "fauna" or not animal.get("name") is String or not animal.get("site_id") is String or not animal.get("site_name") is String or not animal.get("sector_id") is String or not animal.get("habitat") is String:
			return {}
		if animal.get("adult_ware") != ADULT_WARES[i] or animal.get("young_ware") != YOUNG_WARES[i] or animal.get("material_ware") != MATERIAL_WARES[i] or animal.get("enclosure_recipe") != RECIPE_IDS[i] or not animal.get("enclosure_name") is String:
			return {}
		if animal.get("terminal_ware") != ("emberhorn_leather" if i == 0 else ""):
			return {}
		for number in ["wild_reserve", "capture_ticks", "capacity_per_enclosure", "renewable_interval", "breeding_interval", "maturity_cycles"]:
			if not _whole(animal.get(number), 1, 1000):
				return {}
	for i in range(data.wares.size()):
		var ware: Variant = data.wares[i]
		if not ware is Dictionary or ware.get("id") != ALL_WARES[i] or not ware.get("name") is String or not _whole(ware.get("volume"), 1, 10):
			return {}
	for i in range(2):
		var rec: Variant = data.recipes[i]
		var animal: Dictionary = data.animals[i]
		if not rec is Dictionary or rec.get("id") != RECIPE_IDS[i] or rec.get("name") != animal.enclosure_name or not _whole(rec.get("cycle_ticks"), CARE_TICKS, CARE_TICKS) or rec.get("livestock_service") != true:
			return {}
		if not _amounts_match(rec.get("inputs", {}), {"food_rations":1, "potable_water":1, "energy_cells":1}) or not _amounts_match(rec.get("outputs", {}), {"organic_waste":1}) or not _amounts_match(rec.get("catalysts", {}), {str(animal.adult_ware):1}):
			return {}
		var bp: Variant = data.blueprints.get(str(rec.id))
		if not bp is Dictionary or not bp.get("materials") is Dictionary or not _whole(bp.get("fee"), 1, 1000000) or not _whole(bp.get("ticks"), 1, 10000) or not _whole(bp.get("storage"), 1, 10000) or not _whole(bp.materials.get("alloy_plates"), 1, 10000) or not _whole(bp.materials.get("energy_cells"), 1, 10000):
			return {}
	return data


func _empty_job() -> Dictionary:
	return {"enabled":false, "site_id":"", "phase":"idle", "ticks_remaining":0, "wait_reason":""}


func _empty_care() -> Dictionary:
	return {"ticks":0, "fed_cycles":0, "shortages":0, "birth_progress":0, "juvenile_ages":[], "last_status":"Waiting for animals"}


func _empty_transit() -> Dictionary:
	return {"ticks":0, "shortages":0}


func initialize_ship(ship: Dictionary) -> void:
	ship["wildlife_capture"] = _empty_job()


func prepare(target: Dictionary) -> Error:
	var catalog: Dictionary = definitions()
	if catalog.is_empty():
		return ERR_INVALID_DATA
	if target.has("livestock_version"):
		return OK if target.livestock_version == VERSION and target.get("livestock_catalog") == catalog and target.get("livestock_sites") is Dictionary and target.get("livestock_care") is Dictionary and target.get("livestock_transit") is Dictionary else ERR_UNAVAILABLE
	for key in ["livestock_catalog", "livestock_sites", "livestock_care", "livestock_transit"]:
		if target.has(key):
			return ERR_INVALID_DATA
	if int(target.get("biosurvey_version", 0)) != 1:
		return ERR_INVALID_DATA
	var sectors: Dictionary = {}
	for sector in target.sectors:
		sectors[str(sector.id)] = true
	for animal in catalog.animals:
		if not sectors.has(str(animal.sector_id)):
			return ERR_INVALID_DATA
	for ware in catalog.wares:
		for old_ware in target.wares:
			if old_ware.id == ware.id:
				return ERR_ALREADY_IN_USE
		for station in target.stations:
			if station.stock.has(ware.id):
				return ERR_ALREADY_IN_USE
		for ship in target.ships:
			if ship.cargo.has(ware.id):
				return ERR_ALREADY_IN_USE
	for recipe in catalog.recipes:
		if target.construction_blueprints.has(recipe.id):
			return ERR_ALREADY_IN_USE
		for old_recipe in target.recipes:
			if old_recipe.id == recipe.id:
				return ERR_ALREADY_IN_USE
	for ship in target.ships:
		if ship.has("wildlife_capture"):
			return ERR_ALREADY_IN_USE
	# No existing animals, juvenile births, collected feathers, revenue or
	# backdated capture records are invented during additive save migration.
	for ware in catalog.wares:
		target.wares.append(ware.duplicate(true))
		for station in target.stations:
			station.stock[str(ware.id)] = 0
	for recipe in catalog.recipes:
		target.recipes.append(recipe.duplicate(true))
		target.construction_blueprints[str(recipe.id)] = catalog.blueprints[recipe.id].duplicate(true)
	for ship in target.ships:
		if ship.owner == target.player_faction_id:
			initialize_ship(ship)
	var reserves: Dictionary = {}
	for animal in catalog.animals:
		reserves[str(animal.site_id)] = int(animal.wild_reserve)
	target["livestock_version"] = VERSION
	target["livestock_catalog"] = catalog.duplicate(true)
	target["livestock_sites"] = reserves
	target["livestock_care"] = {}
	target["livestock_transit"] = {}
	return OK


func species_for_sector(world: RefCounted, sector_id: String) -> Dictionary:
	for animal in world.state.get("livestock_catalog", {}).get("animals", []):
		if str(animal.sector_id) == sector_id:
			return animal
	return {}


func species_by_id(world: RefCounted, animal_id: String) -> Dictionary:
	for animal in world.state.get("livestock_catalog", {}).get("animals", []):
		if str(animal.id) == animal_id:
			return animal
	return {}


func _animal_by_adult(world: RefCounted, ware_id: String) -> Dictionary:
	for animal in world.state.get("livestock_catalog", {}).get("animals", []):
		if str(animal.adult_ware) == ware_id:
			return animal
	return {}


func is_live(ware_id: String) -> bool:
	return ware_id in ADULT_WARES or ware_id in YOUNG_WARES


func has_living_animals(ship: Dictionary) -> bool:
	for id in ADULT_WARES:
		if int(ship.get("cargo", {}).get(id, 0)) > 0:
			return true
	return false


func pen_count(station: Dictionary, animal: Dictionary) -> int:
	var result := 0
	for module in station.get("production", []):
		if str(module.recipe_id) == str(animal.enclosure_recipe):
			result += 1
	return result


func capacity(station: Dictionary, animal: Dictionary) -> int:
	return pen_count(station, animal) * int(animal.capacity_per_enclosure)


func _headcount(station: Dictionary, animal: Dictionary) -> int:
	return int(station.stock.get(str(animal.adult_ware), 0)) + int(station.stock.get(str(animal.young_ware), 0))


func can_unload(station: Dictionary, ware_id: String, quantity: int) -> bool:
	if quantity < 1 or ware_id in YOUNG_WARES:
		return false
	for animal in definitions().animals:
		if str(animal.adult_ware) == ware_id:
			return station.get("owner", "") == "player" and pen_count(station, animal) > 0 and _headcount(station, animal) + quantity <= capacity(station, animal)
	return false


func _care_key(station_id: String, animal_id: String) -> String:
	return station_id + "|" + animal_id


func _transit_key(ship_id: String, animal_id: String) -> String:
	return ship_id + "|" + animal_id


func ensure_station(world: RefCounted, station_id: String, adult_ware_id: String) -> void:
	var animal: Dictionary = _animal_by_adult(world, adult_ware_id)
	if animal.is_empty():
		return
	var key := _care_key(station_id, str(animal.id))
	if not world.state.livestock_care.has(key):
		world.state.livestock_care[key] = _empty_care()


func ensure_transit(world: RefCounted, ship_id: String, adult_ware_id: String) -> void:
	var animal: Dictionary = _animal_by_adult(world, adult_ware_id)
	if animal.is_empty():
		return
	var key := _transit_key(ship_id, str(animal.id))
	if not world.state.livestock_transit.has(key):
		world.state.livestock_transit[key] = _empty_transit()


func stop(ship: Dictionary) -> void:
	if not ship.has("wildlife_capture"):
		return
	ship.wildlife_capture = _empty_job()
	if str(ship.get("role", "")) == "Wildlife Collector":
		ship.role = "Unassigned"


func assign(world: RefCounted, ship_id: String, sector_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var animal: Dictionary = species_for_sector(world, sector_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id or not ship.has("wildlife_capture"):
		return {"ok":false, "message":"Choose a player-owned ship with a real captain and crew."}
	if animal.is_empty():
		return {"ok":false, "message":"No lawful wild-animal capture reserve is catalogued in that sector."}
	if int(world.state.livestock_sites.get(str(animal.site_id), 0)) < 1:
		return {"ok":false, "message":"The native wildlife capture quota has been exhausted."}
	if int(ship.crew) < 2 or str(ship.captain).is_empty():
		return {"ok":false, "message":"Capture needs an actual captain and two service crew."}
	if int(ship.get("settler_passengers", 0)) > 0 or not ship.get("career_manifest", {}).is_empty() or not ship.get("professional_passenger_ids", []).is_empty():
		return {"ok":false, "message":"Disembark civilian passengers before transporting living specimens."}
	var sector_owner := ""
	for sector in world.state.sectors:
		if sector.id == sector_id:
			sector_owner = str(sector.owner)
			break
	if sector_owner.is_empty() or (sector_owner != world.state.player_faction_id and int(world.state.relations.get(sector_owner, -100)) < 0):
		return {"ok":false, "message":"Wild-animal capture is not permitted in hostile territory."}
	var volume: int = int(world._find_ware(str(animal.adult_ware)).volume)
	if int(ship.cargo.get("energy_cells", 0)) < 1 or world.cargo_volume(ship_id) + volume - 1 > int(ship.cargo_capacity):
		return {"ok":false, "message":"Capture requires a purchased Energy Cell for the stasis capsule and enough real cargo space."}
	if bool(ship.wildlife_capture.enabled) and str(ship.wildlife_capture.site_id) == str(animal.site_id):
		return {"ok":true, "message":"Existing wildlife capture mission retained; no progress or cargo reset."}
	ship.player_trader.enabled = false
	world.build_supply.stop(ship)
	world.station_supply.stop(ship)
	world.waste_transport.stop(ship)
	world.biosurvey.stop(ship)
	stop(ship)
	ship.wildlife_capture = {"enabled":true, "site_id":str(animal.site_id), "phase":"to_site", "ticks_remaining":int(animal.capture_ticks), "wait_reason":""}
	ship.role = "Wildlife Collector"
	return {"ok":true, "message":"Wildlife collection assigned. Actual travel, %d survey ticks, two crew, cargo stasis and one Energy Cell are required." % int(animal.capture_ticks)}


func tick_capture(world: RefCounted, ship: Dictionary) -> void:
	if not ship.has("wildlife_capture") or not bool(ship.wildlife_capture.enabled):
		return
	var job: Dictionary = ship.wildlife_capture
	var animal: Dictionary = {}
	for item in world.state.livestock_catalog.animals:
		if str(item.site_id) == str(job.site_id):
			animal = item
			break
	if animal.is_empty() or int(world.state.livestock_sites.get(str(job.site_id), 0)) < 1:
		stop(ship)
		ship.status = "Native capture quota depleted"
		return
	if not ship.orders.is_empty() or not ship.travel.is_empty():
		return
	if str(ship.sector) != str(animal.sector_id):
		if not world._queue_ship_route(ship, str(animal.sector_id)):
			job.wait_reason = "No galactic route for livestock collection"
		else:
			job.wait_reason = "Travelling to wildlife preserve"
		ship.status = str(job.wait_reason)
		return
	var animal_volume: int = int(world._find_ware(str(animal.adult_ware)).volume)
	if int(ship.cargo.get("energy_cells", 0)) < 1 or world.cargo_volume(str(ship.id)) + animal_volume - 1 > int(ship.cargo_capacity) or int(ship.crew) < 2:
		ship.status = "Wildlife collection needs power, crew and stasis cargo room"
		return
	ship.docked_at = ""
	job.phase = "capturing"
	job.ticks_remaining = maxi(0, int(job.ticks_remaining) - 1)
	ship.status = "Collecting %s, %d survey ticks remain" % [animal.name, int(job.ticks_remaining)]
	if int(job.ticks_remaining) > 0:
		return
	world.state.livestock_sites[str(animal.site_id)] = int(world.state.livestock_sites[str(animal.site_id)]) - 1
	ship.cargo["energy_cells"] = int(ship.cargo.energy_cells) - 1
	ship.cargo[str(animal.adult_ware)] = int(ship.cargo.get(str(animal.adult_ware), 0)) + 1
	ensure_transit(world, str(ship.id), str(animal.adult_ware))
	world._record_transaction("wildlife_capture_energy", str(ship.id), str(animal.site_id), "energy_cells", 1, 0, 0)
	world._record_transaction("wildlife_captured", str(ship.id), str(animal.site_id), str(animal.adult_ware), 1, 0, 0)
	stop(ship)
	ship.status = "One live %s contained in powered transport stasis" % animal.name


func tick_transit(world: RefCounted, ship: Dictionary) -> void:
	if ship.owner != world.state.player_faction_id:
		return
	for animal in world.state.livestock_catalog.animals:
		var n: int = int(ship.cargo.get(str(animal.adult_ware), 0))
		var key := _transit_key(str(ship.id), str(animal.id))
		if n == 0:
			world.state.livestock_transit.erase(key)
			continue
		if not world.state.livestock_transit.has(key):
			ensure_transit(world, str(ship.id), str(animal.adult_ware))
		var transit: Dictionary = world.state.livestock_transit[key]
		transit.ticks = int(transit.ticks) + 1
		if int(transit.ticks) < STASIS_TICKS:
			continue
		transit.ticks = 0
		if int(ship.cargo.get("energy_cells", 0)) >= n:
			ship.cargo.energy_cells = int(ship.cargo.energy_cells) - n
			transit.shortages = 0
			world._record_transaction("livestock_stasis_energy", str(ship.id), "", "energy_cells", n, 0, 0)
			continue
		transit.shortages = int(transit.shortages) + 1
		ship.status = "Animal stasis needs %d Energy Cells" % n
		if int(transit.shortages) >= HUNGER_LIMIT:
			ship.cargo[str(animal.adult_ware)] = n - 1
			transit.shortages = 0
			world._record_transaction("livestock_death", str(ship.id), "", str(animal.adult_ware), 1, 0, 0)
			if n == 1:
				world.state.livestock_transit.erase(key)


func tick_station(world: RefCounted, station: Dictionary) -> void:
	if station.owner != world.state.player_faction_id:
		return
	for animal in world.state.livestock_catalog.animals:
		var pens: int = pen_count(station, animal)
		if pens == 0:
			continue
		var modules: Array = []
		for module in station.production:
			if str(module.recipe_id) == str(animal.enclosure_recipe):
				modules.append(module)
		var n: int = _headcount(station, animal)
		var key := _care_key(str(station.id), str(animal.id))
		if n == 0:
			for module in modules:
				module.progress = 0
				module.status = "Empty animal habitat"
			if world.state.livestock_care.has(key):
				world.state.livestock_care[key].ticks = 0
				world.state.livestock_care[key].shortages = 0
			continue
		if not world.state.livestock_care.has(key):
			ensure_station(world, str(station.id), str(animal.adult_ware))
		var care: Dictionary = world.state.livestock_care[key]
		care.ticks = int(care.ticks) + 1
		for module in modules:
			module.progress = int(care.ticks) % CARE_TICKS
		if int(care.ticks) < CARE_TICKS:
			continue
		care.ticks = 0
		var food: int = n
		var water: int = n
		var power: int = maxi(1, int(ceil(float(n) / float(animal.capacity_per_enclosure))))
		var current_volume: int = world.station_volume(str(station.id))
		var projected: int = current_volume - food - water - power + n
		var nourished: bool = int(station.stock.get("food_rations", 0)) >= food and int(station.stock.get("potable_water", 0)) >= water and int(station.stock.get("energy_cells", 0)) >= power and projected <= int(station.storage_capacity)
		if not nourished:
			care.shortages = int(care.shortages) + 1
			care.last_status = "Needs live-animal feed, water, power or waste capacity (%d / %d)" % [int(care.shortages), HUNGER_LIMIT]
			for module in modules:
				module.status = str(care.last_status)
			if int(care.shortages) >= HUNGER_LIMIT:
				var victim: String = str(animal.young_ware) if int(station.stock.get(str(animal.young_ware), 0)) > 0 else str(animal.adult_ware)
				station.stock[victim] = int(station.stock[victim]) - 1
				if victim == str(animal.young_ware) and not care.juvenile_ages.is_empty():
					care.juvenile_ages.pop_front()
				care.shortages = 0
				world._record_transaction("livestock_death", "", str(station.id), victim, 1, 0, 0)
			continue
		station.stock.food_rations = int(station.stock.food_rations) - food
		station.stock.potable_water = int(station.stock.potable_water) - water
		station.stock.energy_cells = int(station.stock.energy_cells) - power
		station.stock.organic_waste = int(station.stock.get("organic_waste", 0)) + n
		world._record_transaction("livestock_feed", "", str(station.id), str(animal.adult_ware), food, 0, 0)
		world._record_transaction("livestock_water", "", str(station.id), str(animal.adult_ware), water, 0, 0)
		world._record_transaction("livestock_power", "", str(station.id), str(animal.adult_ware), power, 0, 0)
		world._record_transaction("livestock_manure", "", str(station.id), str(animal.adult_ware), n, 0, 0)
		care.fed_cycles = int(care.fed_cycles) + 1
		care.shortages = 0
		care.last_status = "Fed %d live animals; collected %d organic waste" % [n, n]
		for module in modules:
			module.progress = 0
			module.cycles = int(module.cycles) + 1
			module.status = str(care.last_status)
		# Feed-dependent juveniles grow in real, counted cohorts. Young
		# never move invisibly; adulthood only replaces the same individual.
		var old_ages: Array = care.juvenile_ages.duplicate()
		var updated_ages: Array = []
		for juvenile_age in old_ages:
			var next_age: int = mini(int(animal.maturity_cycles), int(juvenile_age) + 1)
			var adult_volume: int = int(world._find_ware(str(animal.adult_ware)).volume)
			var young_volume: int = int(world._find_ware(str(animal.young_ware)).volume)
			if next_age >= int(animal.maturity_cycles) and world.station_volume(str(station.id)) + adult_volume - young_volume <= int(station.storage_capacity):
				station.stock[str(animal.young_ware)] = int(station.stock[str(animal.young_ware)]) - 1
				station.stock[str(animal.adult_ware)] = int(station.stock.get(str(animal.adult_ware), 0)) + 1
				world._record_transaction("livestock_matured", "", str(station.id), str(animal.adult_ware), 1, 0, 0)
			else:
				updated_ages.append(next_age)
		care.juvenile_ages = updated_ages
		# Shedding/shearing is renewable, never an unaccounted source of
		# adult animal units or a substitute for food.
		var adults: int = int(station.stock.get(str(animal.adult_ware), 0))
		if int(care.fed_cycles) % int(animal.renewable_interval) == 0:
			var volume: int = int(world._find_ware(str(animal.material_ware)).volume)
			var shed: int = mini(adults, maxi(0, int(int(station.storage_capacity) - world.station_volume(str(station.id))) / maxi(1, volume)))
			if shed > 0:
				station.stock[str(animal.material_ware)] = int(station.stock.get(str(animal.material_ware), 0)) + shed
				world._record_transaction("livestock_shed", "", str(station.id), str(animal.material_ware), shed, 0, 0)
		# New juveniles only appear when two real adults have both received
		# enough successful feeding cycles and the habitat can house them.
		if adults >= 2:
			care.birth_progress = mini(int(animal.breeding_interval), int(care.birth_progress) + 1)
			var young_volume: int = int(world._find_ware(str(animal.young_ware)).volume)
			if int(care.birth_progress) >= int(animal.breeding_interval) and _headcount(station, animal) < capacity(station, animal) and world.station_volume(str(station.id)) + young_volume <= int(station.storage_capacity):
				station.stock[str(animal.young_ware)] = int(station.stock.get(str(animal.young_ware), 0)) + 1
				care.juvenile_ages.append(0)
				care.birth_progress = 0
				world._record_transaction("livestock_birth", "", str(station.id), str(animal.young_ware), 1, 0, 0)
		else:
			care.birth_progress = 0


func slaughter(world: RefCounted, station_id: String) -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var animal: Dictionary = species_by_id(world, "emberhorn")
	if station.is_empty() or station.owner != world.state.player_faction_id or pen_count(station, animal) == 0:
		return {"ok":false, "message":"An owned, physically completed Emberhorn paddock is required."}
	if int(station.stock.get(str(animal.adult_ware), 0)) < 1:
		return {"ok":false, "message":"No live adult Emberhorn is available for terminal harvest."}
	if int(station.stock.get("energy_cells", 0)) < 1:
		return {"ok":false, "message":"One real Energy Cell is required for hide processing."}
	var adult_volume: int = int(world._find_ware(str(animal.adult_ware)).volume)
	var hide_volume: int = int(world._find_ware(str(animal.terminal_ware)).volume)
	if world.station_volume(station_id) - adult_volume - 1 + hide_volume + 1 > int(station.storage_capacity):
		return {"ok":false, "message":"There is insufficient physical storage for leather and biowaste."}
	station.stock[str(animal.adult_ware)] = int(station.stock[str(animal.adult_ware)]) - 1
	station.stock.energy_cells = int(station.stock.energy_cells) - 1
	station.stock[str(animal.terminal_ware)] = int(station.stock.get(str(animal.terminal_ware), 0)) + 1
	station.stock.organic_waste = int(station.stock.get("organic_waste", 0)) + 1
	world._record_transaction("livestock_slaughter", "", station_id, str(animal.adult_ware), 1, 0, 0)
	world._record_transaction("livestock_hide", "", station_id, str(animal.terminal_ware), 1, 0, 0)
	world._record_transaction("livestock_slaughter_energy", "", station_id, "energy_cells", 1, 0, 0)
	world._record_transaction("livestock_slaughter_waste", "", station_id, "organic_waste", 1, 0, 0)
	return {"ok":true, "message":"One existing Emberhorn was processed using 1 Energy Cell, yielding 1 hide and 1 organic-waste unit. The live adult count decreased by one."}


func report(world: RefCounted, station: Dictionary) -> String:
	var rows: Array[String] = []
	for animal in world.state.livestock_catalog.animals:
		var adults: int = int(station.stock.get(str(animal.adult_ware), 0))
		var young: int = int(station.stock.get(str(animal.young_ware), 0))
		var pens: int = pen_count(station, animal)
		if adults == 0 and young == 0 and pens == 0:
			continue
		var status: Dictionary = world.state.livestock_care.get(_care_key(str(station.id), str(animal.id)), _empty_care())
		rows.append("%s: %d adults + %d young / %d habitat places. %d completed feeding cycles, %d/%d next care ticks. %s" % [animal.name, adults, young, capacity(station, animal), int(status.fed_cycles), int(status.ticks), CARE_TICKS, str(status.last_status)])
	return "No enclosed animals. Build a species-specific paddock or aviary and transport a genuinely collected animal." if rows.is_empty() else "\n".join(rows)
