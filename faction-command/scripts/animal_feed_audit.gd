extends RefCounted
## Physical provenance and compatible migration audit for Pass 37D.
## Does not grant raw crops, extra animals, medicine or prebuilt factories.

const FeedScript = preload("res://scripts/animal_feed.gd")

func _whole(value: Variant, minimum: int = 0) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value)) and float(value) >= float(minimum)


func _record(bucket: Dictionary, key: String, amount: int) -> void:
	bucket[key] = int(bucket.get(key, 0)) + amount


func valid(state: Dictionary) -> bool:
	if state.get("animal_feed_version") != FeedScript.VERSION or not state.get("animal_feed_catalog") is Dictionary or not state.get("animal_quarantine") is Dictionary:
		return false
	var feed: Dictionary = FeedScript.new().definitions()
	if feed.is_empty() or state.animal_feed_catalog != feed:
		return false
	for ware in feed.wares:
		if not state.wares.any(func(w): return w.id == ware.id and w == ware):
			return false
	for recipe in feed.recipes:
		if not state.recipes.any(func(r): return r.id == recipe.id and r == recipe):
			return false
		if state.construction_blueprints.get(recipe.id, {}) != feed.blueprints[str(recipe.id)]:
			return false
	var station_map: Dictionary = {}
	var recipe_cycles: Dictionary = {}
	for recipe_id in FeedScript.RECIPE_IDS:
		recipe_cycles[str(recipe_id)] = 0
	for station in state.stations:
		station_map[str(station.id)] = station
		for module in station.production:
			if recipe_cycles.has(str(module.recipe_id)):
				recipe_cycles[str(module.recipe_id)] = int(recipe_cycles[str(module.recipe_id)]) + int(module.cycles)
			if str(module.recipe_id) == "animal_veterinary_clinic" and (int(module.cycles) != 0 or int(module.progress) != 0):
				# A clinic is manual: it never auto-prints care from idle ticks.
				return false
	var species: Dictionary = {}
	for animal in state.livestock_catalog.animals:
		species[str(animal.id)] = animal
	for key in state.animal_quarantine:
		var parts: PackedStringArray = str(key).split("|")
		if parts.size() != 2 or not station_map.has(parts[0]) or not species.has(parts[1]) or state.animal_quarantine[key] != true:
			return false
		var station: Dictionary = station_map[parts[0]]
		var animal: Dictionary = species[parts[1]]
		if station.owner != state.player_faction_id or FeedScript.new().clinic_count(station) < 0:
			return false
		var has_pen := false
		for module in station.production:
			if str(module.recipe_id) == str(animal.enclosure_recipe):
				has_pen = true
		if not has_pen or int(station.stock.get(str(animal.adult_ware), 0)) + int(station.stock.get(str(animal.young_ware), 0)) < 1:
			return false
	var used: Dictionary = {}
	var receipt_special: Dictionary = {}
	var receipt_existing: Dictionary = {}
	var treatment: Dictionary = {}
	var clinical_med: Dictionary = {}
	var clinical_power: Dictionary = {}
	var clinical_waste: Dictionary = {}
	var animal_by_feed: Dictionary = {"emberhorn_fodder":"emberhorn", "dustwhistle_nectar":"dustwhistle"}
	for event in state.ledger:
		var kind: String = str(event.get("kind", ""))
		if kind not in ["animal_feed_used", "animal_treatment_medical", "animal_treatment_energy", "animal_treatment_waste", "animal_treated", "livestock_feed"]:
			continue
		var station_id: String = str(event.get("station_id", ""))
		var ship_id: String = str(event.get("ship_id", ""))
		var ware_id: String = str(event.get("ware_id", ""))
		if not station_map.has(station_id) or station_map[station_id].owner != state.player_faction_id or not ship_id.is_empty() or not _whole(event.get("quantity"), 1) or not _whole(event.get("tick")) or int(event.tick) > int(state.tick) or not _whole(event.get("price")) or not _whole(event.get("amount")) or int(event.price) != 0 or int(event.amount) != 0:
			return false
		var n: int = int(event.quantity)
		var t: String = str(event.tick)
		if kind == "animal_feed_used":
			if not animal_by_feed.has(ware_id):
				return false
			_record(used, ware_id, n)
			_record(receipt_special, station_id + "|" + animal_by_feed[ware_id] + "|" + t, n)
		elif kind == "livestock_feed":
			var owner_species: String = ""
			for animal in species.values():
				if str(animal.adult_ware) == ware_id:
					owner_species = str(animal.id)
			if owner_species.is_empty():
				return false
			_record(receipt_existing, station_id + "|" + owner_species + "|" + t, n)
		else:
			if not species.has(ware_id) or FeedScript.new().clinic_count(station_map[station_id]) == 0:
				return false
			var key: String = station_id + "|" + ware_id + "|" + t
			match kind:
				"animal_treated":
					if n != 1:
						return false
					_record(treatment, key, n)
				"animal_treatment_energy":
					if n != 1:
						return false
					_record(clinical_power, key, n)
				"animal_treatment_waste":
					if n != 1:
						return false
					_record(clinical_waste, key, n)
				"animal_treatment_medical":
					if n > 1000000:
						return false
					_record(clinical_med, key, n)
	for key in receipt_special:
		if int(receipt_special[key]) != int(receipt_existing.get(key, -1)):
			return false
	if treatment != clinical_power or treatment != clinical_waste or treatment.size() != clinical_med.size():
		return false
	for key in clinical_med:
		if not treatment.has(key) or int(clinical_med[key]) < int(treatment[key]):
			return false
	# All manufactured products can only come from actual completed, paid
	# factories. Tailored feed burned in husbandry must also fit that bound.
	for i in range(4):
		var recipe: Dictionary = feed.recipes[i]
		var ware_id: String = str(feed.wares[i].id)
		var manufactured: int = int(recipe_cycles[str(recipe.id)]) * int(recipe.outputs[ware_id])
		var available := 0
		for station in state.stations:
			available += int(station.stock.get(ware_id, 0))
		for ship in state.ships:
			available += int(ship.cargo.get(ware_id, 0))
		if available + int(used.get(ware_id, 0)) > manufactured:
			return false
	return true
