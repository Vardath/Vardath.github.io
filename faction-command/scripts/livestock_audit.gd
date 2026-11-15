extends RefCounted
## Audits native wildlife sources, ship/station animal inventories and all
## provenance-bearing manufacturing receipts. Older saves lack this version,
## and are assessed by the existing validators before additive migration.

const LivestockScript = preload("res://scripts/livestock.gd")

func _whole(v: Variant, lower: int = 0) -> bool:
	return (v is int or v is float) and is_finite(float(v)) and float(v) == floor(float(v)) and float(v) >= float(lower)


func _receipt(counter: Dictionary, key: String, qty: int) -> void:
	counter[key] = int(counter.get(key, 0)) + qty


func _total(state: Dictionary, ware_id: String) -> int:
	var n := 0
	for ship in state.ships:
		n += int(ship.cargo.get(ware_id, 0))
	for station in state.stations:
		n += int(station.stock.get(ware_id, 0))
	return n


func valid(state: Dictionary) -> bool:
	if state.get("livestock_version") != LivestockScript.VERSION or not state.get("livestock_catalog") is Dictionary or not state.get("livestock_sites") is Dictionary or not state.get("livestock_care") is Dictionary or not state.get("livestock_transit") is Dictionary:
		return false
	var livestock = LivestockScript.new()
	var data: Dictionary = livestock.definitions()
	if data.is_empty() or state.livestock_catalog != data or state.livestock_sites.size() != data.animals.size():
		return false
	for item in data.wares:
		if not state.wares.any(func(w): return w.id == item.id and w == item):
			return false
	for recipe in data.recipes:
		if not state.recipes.any(func(r): return r.id == recipe.id and r == recipe):
			return false
		if state.construction_blueprints.get(recipe.id, {}) != data.blueprints[recipe.id]:
			return false
	var species: Dictionary = {}
	var sites: Dictionary = {}
	var live_from_captures: Dictionary = {}
	var births: Dictionary = {}
	var lost: Dictionary = {}
	var hides: Dictionary = {}
	var molt: Dictionary = {}
	var captured_receipts: Dictionary = {}
	var capture_energy: Dictionary = {}
	var slaughter_receipts: Dictionary = {}
	var hide_receipts: Dictionary = {}
	var slaughter_power: Dictionary = {}
	var slaughter_waste: Dictionary = {}
	var care_feed: Dictionary = {}
	var care_water: Dictionary = {}
	var care_energy: Dictionary = {}
	var care_manure: Dictionary = {}
	for animal in data.animals:
		species[str(animal.id)] = animal
		sites[str(animal.site_id)] = animal
		live_from_captures[str(animal.id)] = 0
		births[str(animal.id)] = 0
		lost[str(animal.id)] = 0
		hides[str(animal.id)] = 0
		molt[str(animal.id)] = 0
		if not _whole(state.livestock_sites.get(str(animal.site_id), null)) or int(state.livestock_sites[animal.site_id]) > int(animal.wild_reserve):
			return false
	var ships: Dictionary = {}
	var stations: Dictionary = {}
	for ship in state.ships:
		ships[str(ship.id)] = ship
	for station in state.stations:
		stations[str(station.id)] = station
	var care_event_counts: Dictionary = {}
	for event in state.ledger:
		var kind: String = str(event.get("kind", ""))
		if not (kind.begins_with("livestock_") or kind.begins_with("wildlife_")):
			continue
		if not _whole(event.get("tick")) or int(event.tick) > int(state.tick) or not _whole(event.get("quantity"), 1) or not _whole(event.get("price")) or int(event.price) != 0 or not _whole(event.get("amount")) or int(event.amount) != 0:
			return false
		var ship_id: String = str(event.get("ship_id", ""))
		var station_id: String = str(event.get("station_id", ""))
		var ware_id: String = str(event.get("ware_id", ""))
		var n: int = int(event.quantity)
		var key: String = "%s|%s|%d" % [ship_id, station_id, int(event.tick)]
		if kind in ["wildlife_capture_energy", "wildlife_captured"]:
			if not sites.has(station_id) or not ships.has(ship_id) or ships[ship_id].owner != state.player_faction_id or n != 1:
				return false
			var a: Dictionary = sites[station_id]
			if kind == "wildlife_capture_energy":
				if ware_id != "energy_cells":
					return false
				_receipt(capture_energy, key, 1)
			else:
				if ware_id != str(a.adult_ware):
					return false
				_receipt(captured_receipts, key, 1)
				_receipt(live_from_captures, str(a.id), 1)
			continue
		if kind == "livestock_stasis_energy":
			if not ships.has(ship_id) or ships[ship_id].owner != state.player_faction_id or not station_id.is_empty() or ware_id != "energy_cells":
				return false
			continue
		if kind == "livestock_death":
			if not (ships.has(ship_id) and ships[ship_id].owner == state.player_faction_id and station_id.is_empty() or ship_id.is_empty() and stations.has(station_id) and stations[station_id].owner == state.player_faction_id):
				return false
			var matched_death := false
			for a in data.animals:
				if ware_id in [str(a.adult_ware), str(a.young_ware)]:
					_receipt(lost, str(a.id), n)
					matched_death = true
			if not matched_death:
				return false
			continue
		if not ship_id.is_empty() or not stations.has(station_id) or stations[station_id].owner != state.player_faction_id:
			return false
		var a: Dictionary = {}
		for candidate in data.animals:
			if ware_id in [str(candidate.adult_ware), str(candidate.young_ware), str(candidate.material_ware), str(candidate.terminal_ware)]:
				a = candidate
				break
		if a.is_empty():
			if kind not in ["livestock_slaughter_energy", "livestock_slaughter_waste"] or ware_id not in ["energy_cells", "organic_waste"]:
				return false
			var s_key: String = station_id + "|" + str(event.tick)
			if kind == "livestock_slaughter_energy" and ware_id == "energy_cells":
				_receipt(slaughter_power, s_key, n)
			elif kind == "livestock_slaughter_waste" and ware_id == "organic_waste":
				_receipt(slaughter_waste, s_key, n)
			else:
				return false
			continue
		var care_key := station_id + "|" + str(a.id) + "|" + str(event.tick)
		if kind in ["livestock_feed", "livestock_water", "livestock_power", "livestock_manure"]:
			if ware_id != str(a.adult_ware):
				return false
			var group: Dictionary = care_feed if kind == "livestock_feed" else (care_water if kind == "livestock_water" else (care_energy if kind == "livestock_power" else care_manure))
			_receipt(group, care_key, n)
			if kind == "livestock_feed":
				_receipt(care_event_counts, station_id + "|" + str(a.id), 1)
		elif kind == "livestock_birth":
			if ware_id != str(a.young_ware) or n != 1:
				return false
			_receipt(births, str(a.id), n)
		elif kind == "livestock_matured":
			if ware_id != str(a.adult_ware) or n != 1:
				return false
		elif kind == "livestock_shed":
			if ware_id != str(a.material_ware):
				return false
			_receipt(molt, str(a.id), n)
		elif kind == "livestock_slaughter":
			if str(a.id) != "emberhorn" or ware_id != str(a.adult_ware):
				return false
			_receipt(lost, str(a.id), n)
			_receipt(slaughter_receipts, station_id + "|" + str(event.tick), n)
		elif kind == "livestock_hide":
			if str(a.id) != "emberhorn" or ware_id != str(a.terminal_ware):
				return false
			_receipt(hides, str(a.id), n)
			_receipt(hide_receipts, station_id + "|" + str(event.tick), n)
		else:
			return false
	if capture_energy != captured_receipts or slaughter_receipts != hide_receipts or slaughter_receipts != slaughter_power or slaughter_receipts != slaughter_waste:
		return false
	if care_feed != care_water or care_feed != care_manure:
		return false
	for key in care_feed:
		if not care_energy.has(key) or int(care_energy[key]) < 1 or int(care_energy[key]) > int(care_feed[key]):
			return false
	if care_feed.size() != care_energy.size():
		return false
	for a in data.animals:
		var taken: int = int(live_from_captures[str(a.id)])
		if int(state.livestock_sites[a.site_id]) + taken != int(a.wild_reserve):
			return false
		var living: int = _total(state, str(a.adult_ware)) + _total(state, str(a.young_ware))
		if living + int(lost[str(a.id)]) != taken + int(births[str(a.id)]):
			return false
		if _total(state, str(a.material_ware)) > int(molt[str(a.id)]):
			return false
		if not str(a.terminal_ware).is_empty() and _total(state, str(a.terminal_ware)) > int(hides[str(a.id)]):
			return false
	for key in state.livestock_care:
		if not key is String or not state.livestock_care[key] is Dictionary:
			return false
		var fragments: PackedStringArray = str(key).split("|")
		if fragments.size() != 2 or not stations.has(fragments[0]) or not species.has(fragments[1]):
			return false
		var station: Dictionary = stations[fragments[0]]
		var a: Dictionary = species[fragments[1]]
		var care: Dictionary = state.livestock_care[key]
		if station.owner != state.player_faction_id or livestock.pen_count(station, a) == 0 or care.size() != livestock._empty_care().size():
			return false
		if not _whole(care.get("ticks")) or int(care.ticks) >= LivestockScript.CARE_TICKS or not _whole(care.get("shortages")) or int(care.shortages) >= LivestockScript.HUNGER_LIMIT or not _whole(care.get("fed_cycles")) or int(care.fed_cycles) > int(state.tick / LivestockScript.CARE_TICKS) or not _whole(care.get("birth_progress")) or int(care.birth_progress) > int(a.breeding_interval) or not care.get("juvenile_ages") is Array or not care.get("last_status") is String:
			return false
		if int(care.fed_cycles) != int(care_event_counts.get(key, 0)):
			return false
		if care.juvenile_ages.size() != int(station.stock.get(str(a.young_ware), 0)):
			return false
		for age in care.juvenile_ages:
			if not _whole(age) or int(age) > int(a.maturity_cycles):
				return false
	for station in state.stations:
		for a in data.animals:
			var n: int = int(station.stock.get(str(a.adult_ware), 0)) + int(station.stock.get(str(a.young_ware), 0))
			if n > livestock.capacity(station, a):
				return false
			if n > 0 and (station.owner != state.player_faction_id or not state.livestock_care.has(str(station.id) + "|" + str(a.id))):
				return false
	for ship in state.ships:
		if ship.owner == state.player_faction_id:
			if not ship.get("wildlife_capture") is Dictionary:
				return false
			var job: Dictionary = ship.wildlife_capture
			if job.size() != livestock._empty_job().size() or not job.get("enabled") is bool or not job.get("site_id") is String or not job.get("phase") is String or not job.get("wait_reason") is String or not _whole(job.get("ticks_remaining")):
				return false
			if bool(job.enabled):
				var matched_job := false
				for animal in data.animals:
					if animal.site_id == job.site_id and int(job.ticks_remaining) <= int(animal.capture_ticks):
						matched_job = true
				if not matched_job or str(job.phase) not in ["to_site", "capturing"] or str(ship.role) != "Wildlife Collector" or ship.player_trader.enabled or ship.bio_survey.enabled or ship.waste_transport.enabled or ship.build_supply.enabled or ship.station_supply.enabled:
					return false
			elif job != livestock._empty_job() or ship.role == "Wildlife Collector":
				return false
			for a in data.animals:
				var transit_key := str(ship.id) + "|" + str(a.id)
				var n: int = int(ship.cargo.get(str(a.adult_ware), 0))
				if int(ship.cargo.get(str(a.young_ware), 0)) > 0:
					return false
				if n > 0:
					if not state.livestock_transit.has(transit_key):
						return false
				elif state.livestock_transit.has(transit_key):
					return false
		elif ship.has("wildlife_capture"):
			return false
	for key in state.livestock_transit:
		var chunks: PackedStringArray = str(key).split("|")
		if chunks.size() != 2 or not ships.has(chunks[0]) or not species.has(chunks[1]) or ships[chunks[0]].owner != state.player_faction_id:
			return false
		var transit: Variant = state.livestock_transit[key]
		if not transit is Dictionary or transit.size() != livestock._empty_transit().size() or not _whole(transit.get("ticks")) or int(transit.ticks) >= LivestockScript.STASIS_TICKS or not _whole(transit.get("shortages")) or int(transit.shortages) >= LivestockScript.HUNGER_LIMIT:
			return false
		if int(ships[chunks[0]].cargo.get(str(species[chunks[1]].adult_ware), 0)) <= 0:
			return false
	return true
