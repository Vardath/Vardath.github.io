extends RefCounted
## Player-ship names and dockside crew services. Every hired service crew
## member comes from a finite NPC station roster; money goes to that station.
## Transfers move existing people between owned, co-docked ships. The captain
## is a separate assigned pilot and is not hired or discharged by this module.

const HIRE_COST := 250
const STARTING_RECRUITS := 12
const MAX_NAME_LENGTH := 40
const PAYROLL_TICKS := 60
const CAPTAIN_WAGE := 12
const SERVICE_WAGE := 3
const XP_PER_LEVEL := 25
const MAX_SKILL := 5


func prepare(target: Dictionary) -> Error:
	if not target.has("personnel_version"):
		if target.has("crew_pools"):
			return ERR_INVALID_DATA
		var pool: Dictionary = {}
		for station in target.get("stations", []):
			if station.owner != target.player_faction_id:
				pool[str(station.id)] = STARTING_RECRUITS
		target["crew_pools"] = pool
		target["personnel_version"] = 1
	if int(target.personnel_version) == 1:
		if not target.get("crew_pools") is Dictionary:
			return ERR_INVALID_DATA
		# In-place migration: existing names, crew, ship orders, credits and
		# captain assignments are untouched. Do not charge retroactive salaries.
		for ship in target.get("ships", []):
			if ship.owner == target.player_faction_id:
				initialize_ship(ship, int(target.get("tick", 0)), _default_pay_station(target, ship))
		target["personnel_version"] = 2
		return OK
	if int(target.personnel_version) != 2 or not target.get("crew_pools") is Dictionary:
		return ERR_UNAVAILABLE
	return OK


func _default_pay_station(target: Dictionary, ship: Dictionary) -> String:
	for station in target.get("stations", []):
		if station.owner != target.player_faction_id and str(station.id) == str(ship.get("docked_at", "")):
			return str(station.id)
	for station in target.get("stations", []):
		if station.owner != target.player_faction_id:
			return str(station.id)
	return ""


func initialize_ship(ship: Dictionary, tick: int, station_id: String) -> void:
	# A unique captain identity belongs to the captain, not the hull.
	ship["captain_profile"] = {"id":"captain_" + str(ship.id), "experience":0, "skill":0, "morale":75}
	ship["crew_profile"] = {"experience":0, "skill":0, "morale":75}
	ship["payroll"] = {"last_tick":tick, "arrears":0, "total_paid":0, "unpaid_periods":0, "station_id":station_id}


func skill_from_experience(experience: int) -> int:
	return mini(MAX_SKILL, maxi(0, int(experience / XP_PER_LEVEL)))


func _update_skills(ship: Dictionary) -> void:
	ship.captain_profile.skill = skill_from_experience(int(ship.captain_profile.experience))
	var count := maxi(1, int(ship.crew))
	ship.crew_profile.skill = skill_from_experience(int(int(ship.crew_profile.experience) / count))


func _ship_wages(ship: Dictionary) -> int:
	return CAPTAIN_WAGE + int(ship.captain_profile.skill) * 2 + int(ship.crew) * SERVICE_WAGE


func _payroll_station(world: RefCounted, ship: Dictionary) -> Dictionary:
	var preferred: Dictionary = world._find_station(str(ship.payroll.station_id))
	if not preferred.is_empty() and preferred.owner != world.state.player_faction_id:
		return preferred
	for station in world.state.stations:
		if station.owner != world.state.player_faction_id:
			return station
	return {}


func tick(world: RefCounted) -> void:
	for ship in world.state.ships:
		if ship.owner != world.state.player_faction_id:
			continue
		# Newly delivered ships are initialized by shipyard before insertion.
		# This also protects externally added owned ships in modded games.
		if not ship.has("captain_profile"):
			initialize_ship(ship, int(world.state.tick), _default_pay_station(world.state, ship))
		var elapsed := int(world.state.tick) - int(ship.payroll.last_tick)
		if elapsed < PAYROLL_TICKS:
			continue
		ship.payroll.last_tick = int(ship.payroll.last_tick) + PAYROLL_TICKS
		var current_due: int = _ship_wages(ship)
		var total_due: int = int(ship.payroll.arrears) + current_due
		var station: Dictionary = _payroll_station(world, ship)
		if not station.is_empty() and int(world.state.starting_credits) >= total_due:
			world.state.starting_credits = int(world.state.starting_credits) - total_due
			station.credits = int(station.credits) + total_due
			ship.payroll.station_id = str(station.id)
			ship.payroll.total_paid = int(ship.payroll.total_paid) + total_due
			ship.payroll.arrears = 0
			ship.payroll.unpaid_periods = 0
			ship.captain_profile.morale = mini(100, int(ship.captain_profile.morale) + 1)
			if int(ship.crew) > 0:
				ship.crew_profile.morale = mini(100, int(ship.crew_profile.morale) + 1)
			world._record_transaction("crew_payroll", str(ship.id), str(station.id), "", int(ship.crew) + 1, 0, -total_due)
		else:
			ship.payroll.arrears = total_due
			ship.payroll.unpaid_periods = int(ship.payroll.unpaid_periods) + 1
			ship.captain_profile.morale = maxi(0, int(ship.captain_profile.morale) - 5)
			if int(ship.crew) > 0:
				ship.crew_profile.morale = maxi(0, int(ship.crew_profile.morale) - 5)


func record_activity(world: RefCounted, ship_id: String, kind: String) -> void:
	var ship := _owned_ship(world, ship_id)
	if ship.is_empty() or not ship.has("captain_profile"):
		return
	if kind not in ["sector_crossing", "buy", "sell", "transfer_in", "transfer_out", "build_delivery", "construction_recovery", "station_supply_delivery", "station_supply_purchase"]:
		return
	ship.captain_profile.experience = int(ship.captain_profile.experience) + (2 if kind == "sector_crossing" else 1)
	ship.crew_profile.experience = int(ship.crew_profile.experience) + int(ship.crew)
	_update_skills(ship)


func swap_captains(world: RefCounted, source_id: String, destination_id: String) -> Dictionary:
	var source := _owned_ship(world, source_id)
	var destination := _owned_ship(world, destination_id)
	if source.is_empty() or destination.is_empty() or source_id == destination_id:
		return {"ok":false, "message":"Choose two different player-owned ships."}
	var station: Dictionary = world._find_station(str(source.docked_at))
	if not _dock_available(source, station) or not _dock_available(destination, station):
		return {"ok":false, "message":"Both ships must be docked at the same station with no active orders."}
	var original_name: String = str(source.captain)
	var original_profile: Dictionary = source.captain_profile
	source.captain = destination.captain
	source.captain_profile = destination.captain_profile
	destination.captain = original_name
	destination.captain_profile = original_profile
	world._record_transaction("captain_swap", source_id, str(station.id), "", 2, 0, 0)
	return {"ok":true, "message":"Captains exchanged ships. Both pilots keep their own skills and morale."}





func capacity(ship: Dictionary) -> int:
	match str(ship.get("class", "")):
		"Courier":
			return 8
		"Freighter":
			return 24
		"Builder":
			return 32
		"Carrier":
			return 80
		_:
			return 12


func _owned_ship(world: RefCounted, ship_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id:
		return {}
	return ship


func _valid_name(candidate: String) -> bool:
	if candidate.length() < 1 or candidate.length() > MAX_NAME_LENGTH:
		return false
	for index in range(candidate.length()):
		if candidate.unicode_at(index) < 32 or candidate.unicode_at(index) == 127:
			return false
	return true


func rename(world: RefCounted, ship_id: String, name: String) -> Dictionary:
	var ship := _owned_ship(world, ship_id)
	var candidate: String = name.strip_edges()
	if ship.is_empty():
		return {"ok":false, "message":"Only your own ships can be renamed."}
	if not _valid_name(candidate):
		return {"ok":false, "message":"Use a ship name of 1 to 40 characters without control characters."}
	if str(ship.name) == candidate:
		return {"ok":false, "message":"The ship already has that name."}
	ship.name = candidate
	return {"ok":true, "message":"Ship renamed to %s." % candidate}


func _dock_available(ship: Dictionary, station: Dictionary) -> bool:
	return not ship.is_empty() and not station.is_empty() and str(ship.docked_at) == str(station.id) and ship.sector == station.sector and ship.orders.is_empty() and ship.travel.is_empty()


func hire(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship := _owned_ship(world, ship_id)
	if ship.is_empty() or quantity < 1 or quantity > 100:
		return {"ok":false, "message":"Choose a player ship and a valid crew quantity."}
	var station: Dictionary = world._find_station(str(ship.docked_at))
	if not _dock_available(ship, station) or station.owner == world.state.player_faction_id or not world.state.crew_pools.has(station.id):
		return {"ok":false, "message":"Dock this ship at an NPC recruitment station to hire crew."}
	if int(world.state.relations.get(str(station.owner), 0)) < -25:
		return {"ok":false, "message":"A hostile station will not recruit for your faction."}
	if int(ship.crew) + quantity > capacity(ship):
		return {"ok":false, "message":"This ship has insufficient crew berths."}
	if int(world.state.crew_pools[station.id]) < quantity or world.population.available_workers(world, str(station.id)) < quantity:
		return {"ok":false, "message":"The station has insufficient available resident recruits."}
	var total: int = quantity * HIRE_COST
	if int(world.state.starting_credits) < total:
		return {"ok":false, "message":"Insufficient faction credits for recruitment."}
	# Mutate only after all checks, so a failed transaction is atomic.
	world.state.starting_credits = int(world.state.starting_credits) - total
	station.credits = int(station.credits) + total
	var old_count: int = int(ship.crew)
	ship.crew = old_count + quantity
	ship.crew_profile.morale = int((int(ship.crew_profile.morale) * old_count + 75 * quantity) / (old_count + quantity))
	_update_skills(ship)
	if not world.population.move_workers(world, str(station.id), -quantity):
		# Population and legacy crew pools must agree before hiring.
		push_error("Population reconciliation failed during crew hiring")
		return {"ok":false, "message":"Population roster is inconsistent."}
	world._record_transaction("crew_hire", ship_id, str(station.id), "", quantity, HIRE_COST, -total)
	return {"ok":true, "message":"Hired %d service crew for %d CR." % [quantity, total]}


func discharge(world: RefCounted, ship_id: String, quantity: int) -> Dictionary:
	var ship := _owned_ship(world, ship_id)
	if ship.is_empty() or quantity < 1 or quantity > 100 or int(ship.crew) < quantity:
		return {"ok":false, "message":"There are not enough service crew to discharge."}
	var station: Dictionary = world._find_station(str(ship.docked_at))
	if not _dock_available(ship, station) or not world.state.crew_pools.has(station.id) or station.owner == world.state.player_faction_id:
		return {"ok":false, "message":"Dock at an NPC recruitment station to discharge crew."}
	var old_count: int = int(ship.crew)
	var lost_experience: int = int(int(ship.crew_profile.experience) * quantity / old_count)
	ship.crew = old_count - quantity
	ship.crew_profile.experience = int(ship.crew_profile.experience) - lost_experience
	_update_skills(ship)
	if not world.population.move_workers(world, str(station.id), quantity):
		push_error("Population reconciliation failed during crew discharge")
		return {"ok":false, "message":"Population roster is inconsistent."}
	world._record_transaction("crew_discharge", ship_id, str(station.id), "", quantity, 0, 0)
	return {"ok":true, "message":"Discharged %d service crew to the station roster." % quantity}


func transfer(world: RefCounted, source_id: String, destination_id: String, quantity: int) -> Dictionary:
	var source := _owned_ship(world, source_id)
	var destination := _owned_ship(world, destination_id)
	if source.is_empty() or destination.is_empty() or source_id == destination_id or quantity < 1 or quantity > 100:
		return {"ok":false, "message":"Choose two different owned ships and a valid crew quantity."}
	var station: Dictionary = world._find_station(str(source.docked_at))
	if not _dock_available(source, station) or not _dock_available(destination, station):
		return {"ok":false, "message":"Both ships must finish orders and dock at the same station."}
	if quantity > int(source.crew):
		return {"ok":false, "message":"Not enough crew aboard the source ship."}
	if int(destination.crew) + quantity > capacity(destination):
		return {"ok":false, "message":"Destination ship has insufficient crew berths."}
	var old_source: int = int(source.crew)
	var old_destination: int = int(destination.crew)
	var moved_experience: int = int(int(source.crew_profile.experience) * quantity / old_source)
	var source_morale: int = int(source.crew_profile.morale)
	var destination_morale: int = int(destination.crew_profile.morale)
	source.crew = old_source - quantity
	destination.crew = old_destination + quantity
	source.crew_profile.experience = int(source.crew_profile.experience) - moved_experience
	destination.crew_profile.experience = int(destination.crew_profile.experience) + moved_experience
	destination.crew_profile.morale = int((destination_morale * old_destination + source_morale * quantity) / (old_destination + quantity))
	_update_skills(source)
	_update_skills(destination)
	world._record_transaction("crew_transfer", destination_id, str(station.id), "", quantity, 0, 0)
	return {"ok":true, "message":"Transferred %d service crew to %s." % [quantity, destination.name]}


func eligible_transfers(world: RefCounted, source_id: String) -> Array:
	var result: Array = []
	var source := _owned_ship(world, source_id)
	if source.is_empty():
		return result
	for candidate in world.state.ships:
		if candidate.id != source.id and candidate.owner == world.state.player_faction_id and not str(source.docked_at).is_empty() and candidate.docked_at == source.docked_at and candidate.sector == source.sector:
			result.append(candidate)
	return result
