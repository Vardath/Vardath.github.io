extends RefCounted
## Pass 36: cultures may VALUE other species' recoverable metabolites.
## Current mixed organic_waste lacks provenance, so bulk buyer quotes are
## keyed to an NPC station's buyer species, NOT a falsely inferred origin.
## Future source-specific premiums remain inactive until resident species and
## physically transported batch origins are conserved individually.

const VERSION := 1
const DATA_PATH := "res://data/waste_cultures.json"
const BUYER_IDS := ["hearth_exchange", "vellum_foundry", "cinder_depot", "verdant_hub"]
const SPECIES_IDS := ["aeralith", "mycoran", "kethric", "lumeni"]


func definitions() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not parsed is Dictionary or parsed.get("schema_version") != VERSION or not parsed.get("species") is Array or not parsed.get("stations") is Array or not parsed.get("future_cross_species_affinities") is Array or not parsed.get("scope") is String:
		return {}
	if parsed.species.size() != SPECIES_IDS.size() or parsed.stations.size() != BUYER_IDS.size() or parsed.future_cross_species_affinities.size() != 4:
		return {}
	var ids: Dictionary = {}
	for i in range(SPECIES_IDS.size()):
		var species: Variant = parsed.species[i]
		if not species is Dictionary or species.get("id") != SPECIES_IDS[i] or not species.get("name") is String or not species.get("notes") is String:
			return {}
		ids[species.id] = true
	for i in range(BUYER_IDS.size()):
		var station: Variant = parsed.stations[i]
		if not station is Dictionary or station.get("station_id") != BUYER_IDS[i] or not ids.has(station.get("buyer_species_id")) or not station.get("reason") is String or not (station.get("organic_waste_buy_price") is int or station.get("organic_waste_buy_price") is float) or int(station.organic_waste_buy_price) < 1 or int(station.organic_waste_buy_price) > 100 or not (station.get("salt_buy_price") is int or station.get("salt_buy_price") is float) or int(station.salt_buy_price) < 1 or int(station.salt_buy_price) > 100:
			return {}
	for affinity in parsed.future_cross_species_affinities:
		if not affinity is Dictionary or not ids.has(affinity.get("recipient_species_id")) or not ids.has(affinity.get("origin_species_id")) or affinity.recipient_species_id == affinity.origin_species_id or not affinity.get("appeal") is String:
			return {}
	return parsed


func catalog(defs: Dictionary) -> Dictionary:
	return {"species":defs.species.duplicate(true), "stations":defs.stations.duplicate(true), "future_cross_species_affinities":defs.future_cross_species_affinities.duplicate(true), "scope":defs.scope}


func prepare(target: Dictionary) -> Error:
	var defs: Dictionary = definitions()
	if defs.is_empty():
		return ERR_INVALID_DATA
	if target.has("waste_cultures_version"):
		return OK if int(target.waste_cultures_version) == VERSION and target.get("waste_cultures_catalog") == catalog(defs) else ERR_UNAVAILABLE
	if target.has("waste_cultures_catalog") or int(target.get("salt_recovery_version", 0)) != 1:
		return ERR_INVALID_DATA
	for binding in defs.stations:
		for station in target.stations:
			if station.id != binding.station_id:
				continue
			if station.has("waste_buyer_species_id"):
				return ERR_ALREADY_IN_USE
	for binding in defs.stations:
		for station in target.stations:
			if station.id != binding.station_id:
				continue
			station["waste_buyer_species_id"] = str(binding.buyer_species_id)
			# Only NPC stations can buy from the player; existing prices (if
			# any) are preserved. Neither buyer credits nor stock are minted.
			if station.owner != target.player_faction_id:
				if not station.buy_prices.has("organic_waste"):
					station.buy_prices["organic_waste"] = int(binding.organic_waste_buy_price)
				if not station.buy_prices.has("salt"):
					station.buy_prices["salt"] = int(binding.salt_buy_price)
	target["waste_cultures_catalog"] = catalog(defs)
	target["waste_cultures_version"] = VERSION
	return OK


func buyer_report(world: RefCounted, station_id: String) -> String:
	var defs: Dictionary = definitions()
	if defs.is_empty():
		return ""
	for binding in defs.stations:
		if str(binding.station_id) != station_id:
			continue
		var station: Dictionary = world._find_station(station_id)
		if station.is_empty():
			return ""
		var species_name := str(binding.buyer_species_id)
		for species in defs.species:
			if species.id == binding.buyer_species_id:
				species_name = str(species.name)
				break
		var offer := int(station.buy_prices.get("organic_waste", 0))
		var salt_offer := int(station.buy_prices.get("salt", 0))
		return "%s bio-market: %s\nUnclassified organic waste: %s\nRecovered mineral salt: %s\n%s\nIndividual species-of-origin premiums require verified species-tagged waste lots and are not yet offered." % [species_name, station.name, "%d CR/unit" % offer if offer > 0 else "No current purchase quote", "%d CR/unit" % salt_offer if salt_offer > 0 else "No current purchase quote", str(binding.reason)]
	return ""
