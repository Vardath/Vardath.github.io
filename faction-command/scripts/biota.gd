extends RefCounted
## Pass 37A: discoverable biological reference data and deterministic
## consumer-dependent evaluation. No organisms, meals, livestock, drugs,
## fauna, captured specimens or new physical wares are spawned here.
## Existing Food Rations and anonymous residents are deliberately unchanged.

const VERSION := 1
const DATA_PATH := "res://data/biota.json"
const SPECIES_IDS := ["aeralith", "mycoran", "kethric", "lumeni"]
const NUTRIENTS := ["sugar", "protein", "mineral", "spore", "radiance"]
const FLAVORS := ["sweet", "bitter", "earthy", "floral", "briny"]
const TOXINS := ["alkaloid", "mycotoxin", "irritant"]
const KINDS := ["flora", "fauna", "fungus", "microbe", "exotic"]
const ALLOWED_ROLES := ["food", "feed", "luxury", "medicine", "livestock", "material", "pet", "pest", "pollinator", "research", "fermentation", "soil"]
const CULTURE_IDS := ["auroran", "vesper", "ravel", "frontier"]


func _within(value: Variant, low: float, high: float) -> bool:
	return (value is int or value is float) and float(value) >= low and float(value) <= high


func _axis_table(value: Variant, axes: Array, minimum: float, maximum: float) -> bool:
	if not value is Dictionary or value.size() != axes.size():
		return false
	for key in axes:
		if not value.has(key) or not _within(value[key], minimum, maximum):
			return false
	return true


func definitions() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not parsed is Dictionary or parsed.get("schema_version") != VERSION:
		return {}
	if not parsed.get("simulation_scope") is String or not parsed.get("species") is Array or not parsed.get("organisms") is Array or not parsed.get("cultures") is Array:
		return {}
	if parsed.get("nutrient_axes") != NUTRIENTS or parsed.get("flavor_axes") != FLAVORS or parsed.get("toxin_axes") != TOXINS:
		return {}
	if parsed.species.size() != SPECIES_IDS.size() or parsed.cultures.size() != CULTURE_IDS.size() or parsed.organisms.size() < 12:
		return {}
	var registered_species: Dictionary = {}
	for consumer in parsed.species:
		if not consumer is Dictionary or not SPECIES_IDS.has(consumer.get("id")) or registered_species.has(consumer.id) or not consumer.get("name") is String or not consumer.get("notes") is String:
			return {}
		if not _axis_table(consumer.get("digestion"), NUTRIENTS, 0.0, 3.0) or not _axis_table(consumer.get("flavor_weights"), FLAVORS, -3.0, 3.0) or not _axis_table(consumer.get("toxin_tolerance"), TOXINS, 0.0, 5.0):
			return {}
		registered_species[consumer.id] = true
	var registered_organisms: Dictionary = {}
	for organism in parsed.organisms:
		if not organism is Dictionary or not organism.get("id") is String or str(organism.id).is_empty() or registered_organisms.has(organism.id):
			return {}
		if not organism.get("name") is String or not KINDS.has(organism.get("kind")) or not organism.get("origin_world") is String or not organism.get("biome") is String:
			return {}
		if not organism.get("roles") is Array or organism.roles.is_empty() or not organism.get("edible") is bool or not organism.get("harvest_byproducts") is Array:
			return {}
		if not organism.get("stock_origin") is String or organism.stock_origin != "undiscovered" or not organism.get("pharmacology") is String or not organism.get("containment_hazard") is String:
			return {}
		if not _within(organism.get("growth_ticks"), 1, 10000) or not _axis_table(organism.get("nutrients"), NUTRIENTS, 0, 5) or not _axis_table(organism.get("flavors"), FLAVORS, 0, 5) or not _axis_table(organism.get("toxins"), TOXINS, 0, 5):
			return {}
		for role in organism.roles:
			if not ALLOWED_ROLES.has(role):
				return {}
		for material in organism.harvest_byproducts:
			if not material is String or str(material).is_empty():
				return {}
		registered_organisms[organism.id] = true
	var registered_cultures: Dictionary = {}
	for culture in parsed.cultures:
		if not culture is Dictionary or not CULTURE_IDS.has(culture.get("id")) or registered_cultures.has(culture.id) or not culture.get("name") is String or not culture.get("bias") is Dictionary:
			return {}
		for organism_id in culture.bias:
			if not registered_organisms.has(organism_id) or not _within(culture.bias[organism_id], -20, 20):
				return {}
		registered_cultures[culture.id] = true
	return parsed


func prepare(target: Dictionary) -> Error:
	var expected: Dictionary = definitions()
	if expected.is_empty():
		return ERR_INVALID_DATA
	if target.has("biota_version"):
		return OK if target.biota_version == VERSION and target.get("biota_catalog") == expected else ERR_UNAVAILABLE
	if target.has("biota_catalog") or int(target.get("waste_cultures_version", 0)) != 1:
		return ERR_INVALID_DATA
	# A catalogue is knowledge available to the simulation, not collected
	# samples, live individuals, population species tags or paid blueprints.
	target["biota_version"] = VERSION
	target["biota_catalog"] = expected.duplicate(true)
	return OK


func evaluate(consumer_species_id: String, organism_id: String, culture_id: String = "") -> Dictionary:
	var data: Dictionary = definitions()
	if data.is_empty():
		return {}
	var consumer: Dictionary = {}
	var organism: Dictionary = {}
	var culture: Dictionary = {}
	for candidate in data.species:
		if candidate.id == consumer_species_id:
			consumer = candidate
			break
	for candidate in data.organisms:
		if candidate.id == organism_id:
			organism = candidate
			break
	if consumer.is_empty() or organism.is_empty():
		return {}
	if not culture_id.is_empty():
		for candidate in data.cultures:
			if candidate.id == culture_id:
				culture = candidate
				break
		if culture.is_empty():
			return {}
	var accessible: float = 0.0
	var possible: float = 0.0
	for nutrient in NUTRIENTS:
		var assimilation: float = float(consumer.digestion[nutrient])
		accessible += float(organism.nutrients[nutrient]) * assimilation
		possible += 5.0 * assimilation
	var nutrition_score: int = clampi(roundi(100.0 * accessible / maxf(1.0, possible)), 0, 100)
	var taste_score: int = 50
	for flavor in FLAVORS:
		taste_score += roundi(5.0 * float(organism.flavors[flavor]) * float(consumer.flavor_weights[flavor]))
	if not culture.is_empty():
		taste_score += int(culture.bias.get(organism_id, 0))
	taste_score = clampi(taste_score, 0, 100)
	var safe: bool = true
	for toxin in TOXINS:
		if float(organism.toxins[toxin]) > float(consumer.toxin_tolerance[toxin]):
			safe = false
			break
	return {
		"consumer_species_id":consumer_species_id,
		"organism_id":organism_id,
		"culture_id":culture_id,
		"nutrition_score":nutrition_score,
		"taste_score":taste_score,
		"nourishing":nutrition_score >= 50,
		"tasty":taste_score >= 50,
		"safe":safe,
		"edible":bool(organism.edible),
		"bioactive":not str(organism.pharmacology).is_empty(),
		"consume_allowed":safe and bool(organism.edible)
	}
