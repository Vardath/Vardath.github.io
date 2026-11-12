extends RefCounted
## One local save slot. A verified temporary file replaces the primary only
## after the previous valid primary has been retained as a backup.

const FORMAT_VERSION := 1
const MAX_SAVE_BYTES := 64 * 1024 * 1024


func has_any_save(path: String) -> bool:
	return FileAccess.file_exists(path) or FileAccess.file_exists(path + ".bak")


func save_game(path: String, state: Dictionary) -> Error:
	if not _valid_world(state):
		return ERR_INVALID_DATA
	# Preserve exact numeric types and values. Objects are never serialized.
	var payload := Marshalls.variant_to_base64(state, false)
	var envelope := {"format_version": FORMAT_VERSION, "checksum": payload.sha256_text(), "payload": payload}
	var temporary := path + ".tmp"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(envelope))
	file.flush()
	var write_error := file.get_error()
	file.close()
	if write_error != OK:
		return write_error
	if not bool(_read_one(temporary).get("ok", false)):
		return ERR_FILE_CORRUPT
	if FileAccess.file_exists(path) and bool(_read_one(path).get("ok", false)):
		var backup_error := DirAccess.rename_absolute(ProjectSettings.globalize_path(path), ProjectSettings.globalize_path(path + ".bak"))
		if backup_error != OK:
			return backup_error
	# If the primary is damaged, retain any usable backup instead of replacing it.
	return DirAccess.rename_absolute(ProjectSettings.globalize_path(temporary), ProjectSettings.globalize_path(path))


func load_game(path: String) -> Dictionary:
	var primary := _read_one(path)
	if bool(primary.get("ok", false)):
		primary["recovered"] = false
		return primary
	# Do not silently replace a save from a newer version with an older backup.
	if primary.get("reason", "") == "unsupported":
		return primary
	var backup := _read_one(path + ".bak")
	if bool(backup.get("ok", false)):
		backup["recovered"] = true
		return backup
	if primary.get("reason", "") == "missing" and backup.get("reason", "") == "missing":
		return {"ok": false, "reason": "missing"}
	return {"ok": false, "reason": "unreadable"}


func _read_one(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"ok": false, "reason": "missing"}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"ok": false, "reason": "unreadable"}
	if file.get_length() > MAX_SAVE_BYTES:
		file.close()
		return {"ok": false, "reason": "unreadable"}
	var text := file.get_as_text()
	file.close()
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return {"ok": false, "reason": "unreadable"}
	var envelope: Variant = parser.data
	if not envelope is Dictionary:
		return {"ok": false, "reason": "unreadable"}
	if not _is_nonnegative_integer(envelope.get("format_version")):
		return {"ok": false, "reason": "unreadable"}
	if envelope.get("format_version", -1) != FORMAT_VERSION:
		return {"ok": false, "reason": "unsupported"}
	if not envelope.get("payload") is String or not envelope.get("checksum") is String:
		return {"ok": false, "reason": "unreadable"}
	var payload: String = envelope.payload
	if payload.sha256_text() != envelope.checksum:
		return {"ok": false, "reason": "unreadable"}
	# Objects remain disabled: saves contain data only, never executable objects.
	var decoded: Variant = Marshalls.base64_to_variant(payload, false)
	if not decoded is Dictionary:
		return {"ok": false, "reason": "unreadable"}
	if _is_nonnegative_integer(decoded.get("schema_version")) and decoded.schema_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("economy_version") and _is_nonnegative_integer(decoded.economy_version) and decoded.economy_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("production_version") and _is_nonnegative_integer(decoded.production_version) and decoded.production_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if decoded.has("logistics_version") and _is_nonnegative_integer(decoded.logistics_version) and decoded.logistics_version != 1:
		return {"ok": false, "reason": "unsupported"}
	if not _valid_world(decoded):
		return {"ok": false, "reason": "unreadable"}
	return {"ok": true, "state": decoded}


func _is_number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))


func _is_nonnegative_integer(value: Variant) -> bool:
	return _is_number(value) and float(value) >= 0.0 and float(value) == floor(float(value))


func _valid_world(state: Dictionary) -> bool:
	if state.get("schema_version", 0) != 1 or not _is_nonnegative_integer(state.get("tick")) or not _is_nonnegative_integer(state.get("starting_credits")):
		return false
	for key in ["factions", "sectors", "links", "ships", "starting_profiles"]:
		if not state.get(key) is Array:
			return false
	if not state.get("relations") is Dictionary or not state.get("player_faction_id") is String or not state.get("player_origin_faction_id") is String:
		return false
	var factions: Dictionary = {}
	for faction in state.factions:
		if not faction is Dictionary or not faction.get("id") is String or str(faction.id).is_empty() or not faction.get("name") is String or not faction.get("color") is String or not str(faction.color).is_valid_html_color() or factions.has(faction.id):
			return false
		factions[faction.id] = true
	if not factions.has(state.player_faction_id) or not factions.has(state.player_origin_faction_id) or state.player_origin_faction_id == state.player_faction_id:
		return false
	for id in factions:
		if id != state.player_faction_id and not _is_number(state.relations.get(id)):
			return false
	var sectors: Dictionary = {}
	for sector in state.sectors:
		if not sector is Dictionary or not sector.get("id") is String or str(sector.id).is_empty() or sectors.has(sector.id) or not sector.get("name") is String or not sector.get("description") is String or not factions.has(sector.get("owner")):
			return false
		if not _is_number(sector.get("x")) or not _is_number(sector.get("y")) or float(sector.x) < 0.0 or float(sector.x) > 1.0 or float(sector.y) < 0.0 or float(sector.y) > 1.0:
			return false
		sectors[sector.id] = true
	var links: Dictionary = {}
	for link in state.links:
		if not link is Array or link.size() != 2 or not sectors.has(link[0]) or not sectors.has(link[1]) or link[0] == link[1]:
			return false
		links["%s|%s" % [link[0], link[1]]] = true
		links["%s|%s" % [link[1], link[0]]] = true
	if state.ships.is_empty():
		return false
	var ships: Dictionary = {}
	for ship in state.ships:
		if not ship is Dictionary:
			return false
		for key in ["id", "name", "class", "owner", "sector", "captain", "role", "status"]:
			if not ship.get(key) is String:
				return false
		if str(ship.id).is_empty() or ships.has(ship.id) or not factions.has(ship.owner) or not sectors.has(ship.sector) or not _is_nonnegative_integer(ship.get("crew")) or not ship.get("orders") is Array or not ship.get("travel") is Dictionary:
			return false
		ships[ship.id] = true
		for order in ship.orders:
			if not order is Dictionary or order.get("type") != "fly_to" or not sectors.has(order.get("destination")):
				return false
		if not ship.travel.is_empty():
			var trip: Dictionary = ship.travel
			if ship.orders.is_empty() or trip.get("from") != ship.sector or not sectors.has(trip.get("to")) or not links.has("%s|%s" % [trip.get("from"), trip.get("to")]):
				return false
			if not _is_nonnegative_integer(trip.get("total")) or not _is_nonnegative_integer(trip.get("remaining")) or int(trip.total) < 1 or int(trip.remaining) < 1 or int(trip.remaining) > int(trip.total):
				return false
	if state.ships[0].owner != state.player_faction_id:
		return false
	# Saves made before the first economy pass are migrated when opened.
	if not state.has("economy_version"):
		return not state.has("production_version") and not state.has("logistics_version")
	if not _valid_economy(state, factions, sectors):
		return false
	# Saves from the manual-trading pass are migrated when opened.
	if not state.has("production_version"):
		return not state.has("logistics_version")
	if not _valid_production(state):
		return false
	return not state.has("logistics_version") or _valid_logistics(state)


func _valid_economy(state: Dictionary, factions: Dictionary, sectors: Dictionary) -> bool:
	if state.economy_version != 1 or not state.get("wares") is Array or not state.get("stations") is Array or not state.get("ledger") is Array or not _is_nonnegative_integer(state.get("next_transaction_id")):
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		if not ware is Dictionary or not ware.get("id") is String or str(ware.id).is_empty() or wares.has(ware.id) or not ware.get("name") is String or not _is_nonnegative_integer(ware.get("volume")) or int(ware.volume) < 1:
			return false
		wares[ware.id] = int(ware.volume)
	var stations: Dictionary = {}
	for station in state.stations:
		if not station is Dictionary or not station.get("id") is String or str(station.id).is_empty() or stations.has(station.id) or not station.get("name") is String or not factions.has(station.get("owner")) or not sectors.has(station.get("sector")) or not _is_nonnegative_integer(station.get("credits")) or not _is_nonnegative_integer(station.get("storage_capacity")):
			return false
		var station_used := 0
		for key in ["stock", "sell_prices", "buy_prices"]:
			if not station.get(key) is Dictionary:
				return false
			for ware_id in station[key]:
				if not wares.has(ware_id) or not _is_nonnegative_integer(station[key][ware_id]):
					return false
				if key != "stock" and (int(station[key][ware_id]) < 1 or int(station[key][ware_id]) > 1000000000):
					return false
				if key == "stock":
					station_used += int(station[key][ware_id]) * int(wares[ware_id])
		if station_used > int(station.storage_capacity):
			return false
		stations[station.id] = station
	if wares.is_empty() or stations.is_empty():
		return false
	for ship in state.ships:
		if not ship.get("cargo") is Dictionary or not ship.get("docked_at") is String or not _is_nonnegative_integer(ship.get("cargo_capacity")):
			return false
		var volume := 0
		for ware_id in ship.cargo:
			if not wares.has(ware_id) or not _is_nonnegative_integer(ship.cargo[ware_id]):
				return false
			volume += int(ship.cargo[ware_id]) * int(wares[ware_id])
		if volume > int(ship.cargo_capacity):
			return false
		if not str(ship.docked_at).is_empty():
			if not stations.has(ship.docked_at) or stations[ship.docked_at].sector != ship.sector or not ship.orders.is_empty() or not ship.travel.is_empty():
				return false
	var last_id := 0
	for entry in state.ledger:
		if not entry is Dictionary or not _is_nonnegative_integer(entry.get("id")) or int(entry.id) <= last_id:
			return false
		last_id = int(entry.id)
	if int(state.next_transaction_id) <= last_id:
		return false
	return true


func _valid_production(state: Dictionary) -> bool:
	if state.production_version != 1 or not state.get("recipes") is Array:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	var recipes: Dictionary = {}
	for recipe in state.recipes:
		if not recipe is Dictionary or not recipe.get("id") is String or str(recipe.id).is_empty() or recipes.has(recipe.id) or not recipe.get("name") is String or not _is_nonnegative_integer(recipe.get("cycle_ticks")) or int(recipe.cycle_ticks) < 1 or int(recipe.cycle_ticks) > 1000000:
			return false
		if not recipe.get("inputs") is Dictionary or not recipe.get("outputs") is Dictionary or recipe.outputs.is_empty():
			return false
		for key in ["inputs", "outputs"]:
			for ware_id in recipe[key]:
				if not wares.has(ware_id) or not _is_nonnegative_integer(recipe[key][ware_id]) or int(recipe[key][ware_id]) < 1 or int(recipe[key][ware_id]) > 1000000:
					return false
		var source: Variant = recipe.get("source", "")
		if not source is String or (source != "" and source != "sunlight"):
			return false
		var deposit: Variant = recipe.get("deposit", {})
		if not deposit is Dictionary:
			return false
		if not deposit.is_empty():
			if not wares.has(deposit.get("resource")) or not _is_nonnegative_integer(deposit.get("quantity")) or int(deposit.quantity) < 1 or int(deposit.quantity) > 1000000:
				return false
		if recipe.inputs.is_empty() and source == "" and deposit.is_empty():
			return false
		recipes[recipe.id] = recipe
	if recipes.is_empty():
		return false
	for station in state.stations:
		if not station.get("natural_sources") is Array or not station.get("deposits") is Dictionary or not station.get("production") is Array:
			return false
		for source in station.natural_sources:
			if source != "sunlight":
				return false
		for resource_id in station.deposits:
			if not wares.has(resource_id) or not _is_nonnegative_integer(station.deposits[resource_id]):
				return false
		for module in station.production:
			if not module is Dictionary or not recipes.has(module.get("recipe_id")) or not _is_nonnegative_integer(module.get("progress")) or not _is_nonnegative_integer(module.get("cycles")) or not module.get("status") is String:
				return false
			if int(module.progress) >= int(recipes[module.recipe_id].cycle_ticks):
				return false
	return true


func _valid_logistics(state: Dictionary) -> bool:
	if state.logistics_version != 1:
		return false
	var wares: Dictionary = {}
	for ware in state.wares:
		wares[ware.id] = true
	for ship in state.ships:
		if not ship.has("autotrader"):
			continue
		if ship.owner == state.player_faction_id or not _is_nonnegative_integer(ship.get("credits")) or not ship.autotrader is Dictionary:
			return false
		var job: Dictionary = ship.autotrader
		if not job.get("enabled") is bool or not job.get("funded") is bool or not job.get("phase") is String or job.phase not in ["idle", "to_source", "to_destination"]:
			return false
		for key in ["home_station_id", "source_id", "destination_id", "ware_id"]:
			if not job.get(key) is String:
				return false
		if not _is_nonnegative_integer(job.get("quantity")) or not _is_nonnegative_integer(job.get("retry_ticks")) or job.home_station_id.is_empty():
			return false
		# A station can disappear while a ship is en route. The trader will
		# replan on arrival; that ordinary world change must not corrupt a save.
		if job.phase == "to_source" and (job.source_id.is_empty() or job.destination_id.is_empty() or not wares.has(job.ware_id) or int(job.quantity) < 1):
			return false
		if job.phase == "to_destination" and (not wares.has(job.ware_id) or int(job.quantity) < 1):
			return false
	return true
