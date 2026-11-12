extends RefCounted
## Small, presentation-independent world state. Time advances only through
## explicit whole ticks; no wall clock or frame rate enters the simulation.

const STARTER_DATA := "res://data/starter_galaxy.json"
const TICKS_PER_CROSSING := 5

var state: Dictionary = {}


func load_starter(origin_faction_id: String = "auroran") -> Error:
	if not FileAccess.file_exists(STARTER_DATA):
		return ERR_FILE_NOT_FOUND
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(STARTER_DATA))
	if not parsed is Dictionary or parsed.get("schema_version", 0) != 1:
		return ERR_PARSE_ERROR
	var chosen: Dictionary = {}
	for profile in parsed.get("starting_profiles", []):
		if profile.get("faction_id", "") == origin_faction_id:
			chosen = profile
			break
	if chosen.is_empty():
		return ERR_INVALID_PARAMETER
	var new_state: Dictionary = parsed.duplicate(true)
	new_state["tick"] = 0
	new_state["player_origin_faction_id"] = origin_faction_id
	new_state["relations"] = chosen.relations.duplicate(true)
	for ship in new_state.get("ships", []):
		if ship.owner == new_state.player_faction_id:
			ship.sector = chosen.sector_id
		ship["orders"] = []
		ship["travel"] = {}
	state = new_state
	return OK


func advance_ticks(count: int) -> void:
	if count <= 0 or state.is_empty():
		return
	for _step in range(count):
		state["tick"] = int(state["tick"]) + 1
		for ship in state.get("ships", []):
			_tick_ship(ship)


func snapshot() -> Dictionary:
	return state.duplicate(true)


func queue_fly_to(ship_id: String, destination: String) -> bool:
	var ship := _find_ship(ship_id)
	if ship.is_empty() or ship.owner != state.get("player_faction_id", ""):
		return false
	var origin: String = str(ship.sector)
	if not ship.orders.is_empty():
		origin = str(ship.orders.back().destination)
	if origin == destination or _find_route(origin, destination).is_empty():
		return false
	ship.orders.append({"type": "fly_to", "destination": destination})
	if ship.travel.is_empty():
		ship.status = "Queued"
	return true


func _find_ship(ship_id: String) -> Dictionary:
	for ship in state.get("ships", []):
		if ship.id == ship_id:
			return ship
	return {}


func _find_route(origin: String, destination: String) -> Array:
	var neighbors: Dictionary = {}
	for sector in state.get("sectors", []):
		neighbors[sector.id] = []
	if not neighbors.has(origin) or not neighbors.has(destination):
		return []
	# The data's fixed link order is the tie breaker between equal routes.
	for link in state.get("links", []):
		if link.size() == 2 and neighbors.has(link[0]) and neighbors.has(link[1]):
			neighbors[link[0]].append(link[1])
			neighbors[link[1]].append(link[0])
	var previous: Dictionary = {origin: ""}
	var waiting: Array = [origin]
	while not waiting.is_empty() and not previous.has(destination):
		var current: String = waiting.pop_front()
		for neighbor in neighbors[current]:
			if not previous.has(neighbor):
				previous[neighbor] = current
				waiting.append(neighbor)
	if not previous.has(destination):
		return []
	var route: Array = []
	var current: String = destination
	while not current.is_empty():
		route.push_front(current)
		current = str(previous[current])
	return route


func _tick_ship(ship: Dictionary) -> void:
	if ship.orders.is_empty():
		ship.status = "Idle"
		return
	if ship.travel.is_empty():
		var route := _find_route(str(ship.sector), str(ship.orders[0].destination))
		if route.size() < 2:
			ship.status = "Blocked"
			return
		ship.travel = {"from": route[0], "to": route[1], "total": TICKS_PER_CROSSING, "remaining": TICKS_PER_CROSSING}
	ship.status = "Travelling"
	ship.travel.remaining = int(ship.travel.remaining) - 1
	if int(ship.travel.remaining) <= 0:
		ship.sector = ship.travel.to
		ship.travel = {}
		if ship.sector == ship.orders[0].destination:
			ship.orders.pop_front()
		if ship.orders.is_empty():
			ship.status = "Idle"
