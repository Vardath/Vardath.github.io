extends RefCounted
## Pass 37B — finite orbital biome sampling, real ship cargo and first
## cultivated organisms. No free collection, instant gene cloning, invented
## citizens, animal farming, meals or species origin labels for old residents.

const VERSION := 1
const DATA_PATH := "res://data/biosurvey.json"
const SAMPLES := ["sunlace_seed_capsule", "mirealgae_culture_capsule"]
const PRODUCTS := ["sunlace_fruit", "mirealgae_biomass", "biogene_record"]
const RECIPE_IDS := ["bio_gene_bank", "sunlace_hydroponics", "mirealgae_bioreactor"]
const REQUIRED_ENERGY := "energy_cells"


func _quantities_match(actual: Variant, wanted: Dictionary) -> bool:
	if not actual is Dictionary or actual.size() != wanted.size():
		return false
	for id in wanted:
		var value: Variant = actual.get(id, null)
		if not (value is int or value is float) or not is_finite(float(value)) or float(value) != float(wanted[id]):
			return false
	return true


func definitions() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not parsed is Dictionary or parsed.get("schema_version") != VERSION or not parsed.get("sites") is Array or not parsed.get("wares") is Array or not parsed.get("recipes") is Array or not parsed.get("blueprints") is Dictionary or not parsed.get("scope") is String or not parsed.get("biohazard_policy") is String:
		return {}
	if parsed.sites.size() != 2 or parsed.wares.size() != 5 or parsed.recipes.size() != RECIPE_IDS.size() or parsed.blueprints.size() != RECIPE_IDS.size():
		return {}
	var biota: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/biota.json"))
	if not biota is Dictionary or not biota.get("organisms") is Array:
		return {}
	var organisms: Dictionary = {}
	for organism in biota.organisms:
		organisms[str(organism.id)] = organism
	var ids: Dictionary = {}
	for i in range(parsed.wares.size()):
		var w: Variant = parsed.wares[i]
		var valid_id: String = (SAMPLES + PRODUCTS)[i]
		if not w is Dictionary or w.get("id") != valid_id or not w.get("name") is String or w.get("volume") != 1:
			return {}
	for site in parsed.sites:
		if not site is Dictionary or not site.get("id") is String or ids.has(site.id) or not site.get("name") is String or not site.get("sector_id") is String or not organisms.has(site.get("organism_id")) or not SAMPLES.has(site.get("sample_ware_id")):
			return {}
		if not site.get("safety") is String or site.safety not in ["clean_botanical", "contained_microbe"]:
			return {}
		for key in ["initial_reserve", "collection_ticks", "energy_cost", "min_crew"]:
			var value: Variant = site.get(key, null)
			if not (value is int or value is float) or not is_finite(float(value)) or float(value) != floor(float(value)):
				return {}
		if int(site.initial_reserve) < 1 or int(site.initial_reserve) > 1000 or int(site.collection_ticks) < 2 or int(site.collection_ticks) > 1000 or int(site.energy_cost) != 1 or int(site.min_crew) != 2:
			return {}
		if site.sample_ware_id == "sunlace_seed_capsule" and site.organism_id != "sunlace_fruit":
			return {}
		if site.sample_ware_id == "mirealgae_culture_capsule" and site.organism_id != "mirealgae":
			return {}
		ids[site.id] = true
	for i in range(parsed.recipes.size()):
		var recipe: Variant = parsed.recipes[i]
		if not recipe is Dictionary or recipe.get("id") != RECIPE_IDS[i] or not recipe.get("name") is String or not (recipe.get("cycle_ticks") is int or recipe.get("cycle_ticks") is float) or int(recipe.cycle_ticks) < 1:
			return {}
		if not recipe.get("inputs") is Dictionary or not recipe.get("outputs") is Dictionary or not recipe.get("catalysts", {}) is Dictionary:
			return {}
		if not parsed.blueprints.has(recipe.id):
			return {}
		var blueprint: Dictionary = parsed.blueprints[recipe.id]
		if not blueprint.get("materials") is Dictionary or int(blueprint.get("fee", 0)) < 1 or int(blueprint.get("ticks", 0)) < 1 or int(blueprint.get("storage", 0)) < 1 or int(blueprint.materials.get("alloy_plates", 0)) < 1 or int(blueprint.materials.get("energy_cells", 0)) < 1:
			return {}
	# Keep biological accounting fixed and independently auditable.
	if not _quantities_match(parsed.recipes[0].inputs, {"sunlace_seed_capsule":1, "energy_cells":1}) or not _quantities_match(parsed.recipes[0].outputs, {"biogene_record":1}):
		return {}
	if not _quantities_match(parsed.recipes[1].inputs, {"potable_water":2, "fertile_soil":1, "energy_cells":1}) or not _quantities_match(parsed.recipes[1].get("catalysts", {}), {"sunlace_seed_capsule":1}) or not _quantities_match(parsed.recipes[1].outputs, {"sunlace_fruit":3}):
		return {}
	if not _quantities_match(parsed.recipes[2].inputs, {"potable_water":2, "energy_cells":1}) or not _quantities_match(parsed.recipes[2].get("catalysts", {}), {"mirealgae_culture_capsule":1}) or not _quantities_match(parsed.recipes[2].outputs, {"mirealgae_biomass":3}):
		return {}
	return parsed


func _empty_job() -> Dictionary:
	return {"enabled":false, "site_id":"", "phase":"idle", "ticks_remaining":0, "wait_reason":""}


func initialize_ship(ship: Dictionary) -> void:
	ship["bio_survey"] = _empty_job()


func prepare(target: Dictionary) -> Error:
	var defs: Dictionary = definitions()
	if defs.is_empty():
		return ERR_INVALID_DATA
	if target.has("biosurvey_version"):
		return OK if int(target.biosurvey_version) == VERSION and target.get("biosurvey_catalog") == defs and target.get("biosurvey_sites") is Dictionary else ERR_UNAVAILABLE
	if target.has("biosurvey_catalog") or target.has("biosurvey_sites") or int(target.get("biota_version", 0)) != 1 or not target.get("wares") is Array or not target.get("recipes") is Array or not target.get("construction_blueprints") is Dictionary:
		return ERR_INVALID_DATA
	for ware in defs.wares:
		for original in target.wares:
			if original.id == ware.id:
				return ERR_ALREADY_IN_USE
		for station in target.stations:
			if station.stock.has(ware.id):
				return ERR_ALREADY_IN_USE
		for ship in target.ships:
			if ship.cargo.has(ware.id):
				return ERR_ALREADY_IN_USE
	for recipe in defs.recipes:
		if target.construction_blueprints.has(recipe.id):
			return ERR_ALREADY_IN_USE
		for original in target.recipes:
			if original.id == recipe.id:
				return ERR_ALREADY_IN_USE
	for ship in target.ships:
		if ship.has("bio_survey"):
			return ERR_ALREADY_IN_USE
	var sector_ids: Dictionary = {}
	for sector in target.sectors:
		sector_ids[str(sector.id)] = true
	for site in defs.sites:
		if not sector_ids.has(site.sector_id):
			return ERR_INVALID_DATA
	# Only *finite wild reserves* are established by the newly discovered
	# environmental system; historical inventory stays exactly as it was.
	for ware in defs.wares:
		target.wares.append(ware.duplicate(true))
		for station in target.stations:
			station.stock[ware.id] = 0
	for recipe in defs.recipes:
		target.recipes.append(recipe.duplicate(true))
		target.construction_blueprints[recipe.id] = defs.blueprints[recipe.id].duplicate(true)
	var sites: Dictionary = {}
	for site in defs.sites:
		sites[str(site.id)] = int(site.initial_reserve)
	target["biosurvey_sites"] = sites
	for ship in target.ships:
		if ship.owner == target.player_faction_id:
			initialize_ship(ship)
	target["biosurvey_catalog"] = defs.duplicate(true)
	target["biosurvey_version"] = VERSION
	return OK


func site_for_sector(world: RefCounted, sector_id: String) -> Dictionary:
	for site in world.state.get("biosurvey_catalog", {}).get("sites", []):
		if str(site.sector_id) == sector_id:
			return site
	return {}


func has_gene_bank(station: Dictionary) -> bool:
	for module in station.get("production", []):
		if str(module.get("recipe_id", "")) == "bio_gene_bank":
			return true
	return false


func stop(ship: Dictionary) -> void:
	if not ship.has("bio_survey"):
		return
	ship.bio_survey = _empty_job()
	if str(ship.get("role", "")) == "Bio Survey":
		ship.role = "Unassigned"


func assign(world: RefCounted, ship_id: String, sector_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var site: Dictionary = site_for_sector(world, sector_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id or not ship.has("bio_survey"):
		return {"ok":false, "message":"Select a player-owned vessel with a real captain and crew."}
	if site.is_empty():
		return {"ok":false, "message":"No licensed orbital biological sampling site is catalogued for this sector."}
	if int(world.state.biosurvey_sites.get(str(site.id), 0)) < 1:
		return {"ok":false, "message":"This planetary sampling reserve has been exhausted."}
	if int(ship.crew) < int(site.min_crew) or str(ship.captain).is_empty():
		return {"ok":false, "message":"Sampling requires a captain and at least two existing service crew."}
	var sector: Dictionary = {}
	for candidate in world.state.sectors:
		if candidate.id == sector_id:
			sector = candidate
			break
	if sector.is_empty() or (str(sector.owner) != world.state.player_faction_id and int(world.state.relations.get(str(sector.owner), -100)) < 0):
		return {"ok":false, "message":"Planetary collection is not authorised in hostile territory."}
	var sample: Dictionary = world._find_ware(str(site.sample_ware_id))
	if sample.is_empty() or int(ship.cargo.get(REQUIRED_ENERGY, 0)) < int(site.energy_cost) or world.cargo_volume(ship_id) + int(sample.volume) - int(site.energy_cost) > int(ship.cargo_capacity):
		return {"ok":false, "message":"Buy and load a real Energy Cell and keep a free cargo slot before collecting."}
	if int(ship.get("settler_passengers", 0)) != 0 or not ship.get("career_manifest", {}).is_empty() or not ship.get("professional_passenger_ids", []).is_empty():
		return {"ok":false, "message":"Disembark civilian passengers before handling biological specimens."}
	if bool(ship.bio_survey.enabled) and str(ship.bio_survey.site_id) == str(site.id):
		return {"ok":true, "message":"Existing biological survey remains assigned; no progress or cargo has been reset."}
	# Genuine role exclusivity: do not erase any cargo or already queued travel.
	ship.player_trader.enabled = false
	world.build_supply.stop(ship)
	world.station_supply.stop(ship)
	world.waste_transport.stop(ship)
	world.livestock.stop(ship)
	stop(ship)
	ship.bio_survey = {"enabled":true, "site_id":str(site.id), "phase":"to_site", "ticks_remaining":int(site.collection_ticks), "wait_reason":""}
	ship.role = "Bio Survey"
	return {"ok":true, "message":"Bio survey ordered for %s. This voyage needs real travel, crew, survey time, an Energy Cell and finite native specimens." % site.name}


func tick(world: RefCounted, ship: Dictionary) -> void:
	if not ship.has("bio_survey") or not bool(ship.bio_survey.enabled):
		return
	var job: Dictionary = ship.bio_survey
	var site: Dictionary = {}
	for row in world.state.biosurvey_catalog.sites:
		if str(row.id) == str(job.site_id):
			site = row
			break
	if site.is_empty() or int(world.state.biosurvey_sites.get(str(job.site_id), 0)) < 1:
		stop(ship)
		ship.status = "No remaining authorised planetary samples"
		return
	if not ship.orders.is_empty() or not ship.travel.is_empty():
		ship.status = "Bio survey waiting for existing ship orders"
		return
	if str(ship.sector) != str(site.sector_id):
		if not world._queue_ship_route(ship, str(site.sector_id)):
			job.wait_reason = "No physical sector route to survey site"
		else:
			job.wait_reason = "Travelling to biological survey site"
		ship.status = job.wait_reason
		return
	var cargo_room: int = int(ship.cargo_capacity) - world.cargo_volume(str(ship.id))
	var energy: int = int(ship.cargo.get(REQUIRED_ENERGY, 0))
	if int(ship.crew) < int(site.min_crew) or energy < int(site.energy_cost) or cargo_room + int(site.energy_cost) < 1:
		job.wait_reason = "Survey needs crew, survey energy and physical cargo space"
		ship.status = job.wait_reason
		return
	ship.docked_at = ""
	job.phase = "collecting"
	job.wait_reason = ""
	job.ticks_remaining = maxi(0, int(job.ticks_remaining) - 1)
	ship.status = "Collecting %s (%d ticks)" % [site.name, int(job.ticks_remaining)]
	if int(job.ticks_remaining) > 0:
		return
	# One atomic movement: an existing native specimen leaves its finite
	# planetary reserve and occupies real ship storage, paying real energy.
	world.state.biosurvey_sites[str(site.id)] = int(world.state.biosurvey_sites[str(site.id)]) - 1
	ship.cargo[REQUIRED_ENERGY] = energy - int(site.energy_cost)
	ship.cargo[str(site.sample_ware_id)] = int(ship.cargo.get(str(site.sample_ware_id), 0)) + 1
	world._record_transaction("bio_survey_energy", str(ship.id), str(site.id), REQUIRED_ENERGY, int(site.energy_cost), 0, 0)
	world._record_transaction("bio_collected", str(ship.id), str(site.id), str(site.sample_ware_id), 1, 0, 0)
	stop(ship)
	ship.status = "Contained specimen collected; deliver to an owned gene bank"
