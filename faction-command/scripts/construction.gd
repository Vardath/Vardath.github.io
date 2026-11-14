extends RefCounted
## Persistent construction contracts, physical build storage and one NPC
## builder. Fees move to the builder; materials are consumed at module start.

const DATA_PATH := "res://data/construction.json"
const BUILDER_ID := "npc_builder_001"
const MAX_TASKS := 300
const PlannerScript = preload("res://scripts/station_planner.gd")

var planner = PlannerScript.new()


func prepare(target: Dictionary) -> Error:
	if target.has("construction_version"):
		if int(target.construction_version) == 2:
			return OK
		if int(target.construction_version) != 1:
			return ERR_UNAVAILABLE
		# Preserve legacy site queues, materials, progress and builder assignments.
		for site in target.get("build_sites", []):
			site["cancelled"] = false
			site["refunded_fee"] = 0
		target["construction_version"] = 2
		return OK
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not data is Dictionary or not data.get("blueprints") is Dictionary or not data.get("sector_deposits") is Dictionary or not data.get("default_natural_sources") is Array:
		return ERR_INVALID_DATA
	for ship in target.ships:
		if ship.id == BUILDER_ID:
			return ERR_ALREADY_IN_USE
	var home: Dictionary = {}
	for station in target.stations:
		if station.id == "verdant_hub" and station.owner != target.player_faction_id:
			home = station
			break
	if home.is_empty():
		for station in target.stations:
			if station.owner != target.player_faction_id:
				home = station
				break
	if home.is_empty():
		return ERR_INVALID_DATA
	var resources: Dictionary = {}
	for sector in target.sectors:
		resources[sector.id] = {"natural_sources":data.default_natural_sources.duplicate(true), "deposits":data.sector_deposits.get(sector.id, {}).duplicate(true)}
	target["construction_blueprints"] = data.blueprints.duplicate(true)
	target["construction_resources"] = resources
	target["build_sites"] = []
	target["next_build_site_id"] = 1
	target.ships.append({"id":BUILDER_ID, "name":"Keystone", "class":"Builder", "owner":home.owner, "sector":home.sector, "captain":"Sera Nahl", "crew":5, "role":"Builder", "status":"Idle", "orders":[], "travel":{}, "cargo_capacity":0, "cargo":{}, "docked_at":"", "credits":0, "build_assignment":""})
	target["construction_version"] = 2
	return OK


func quote(world: RefCounted, sector_id: String, requested: Dictionary, mode: String, imports: Array) -> Dictionary:
	if not world.state.construction_resources.has(sector_id):
		return {"ok":false, "message":"Choose a valid sector."}
	var plan: Dictionary = planner.preview(world.state, requested, mode, imports, sector_id)
	if not plan.ok:
		return {"ok":false, "message":" ".join(plan.errors)}
	if plan.modules.is_empty():
		return {"ok":false, "message":"Choose at least one production module."}
	var total := 0
	var fee := 0
	var ticks := 0
	var materials: Dictionary = {}
	for row in plan.modules:
		if not world.state.construction_blueprints.has(row.id):
			return {"ok":false, "message":"No construction blueprint for " + str(row.name) + "."}
		var blueprint: Dictionary = world.state.construction_blueprints[row.id]
		var amount := int(row.total)
		total += amount
		fee += int(blueprint.fee) * amount
		ticks += int(blueprint.ticks) * amount
		for ware_id in blueprint.materials:
			materials[ware_id] = int(materials.get(ware_id, 0)) + int(blueprint.materials[ware_id]) * amount
	if total > MAX_TASKS:
		return {"ok":false, "message":"A build can contain at most %d modules." % MAX_TASKS}
	return {"ok":true, "modules":plan.modules, "warnings":plan.warnings, "fee":fee, "ticks":ticks, "materials":materials}


func place(world: RefCounted, sector_id: String, requested: Dictionary, mode: String, imports: Array) -> Dictionary:
	var estimate := quote(world, sector_id, requested, mode, imports)
	if not estimate.ok:
		return estimate
	var builder: Dictionary = world._find_ship(BUILDER_ID)
	if builder.is_empty() or builder.owner == world.state.player_faction_id:
		return {"ok":false, "message":"No builder is available."}
	if int(world.state.starting_credits) < int(estimate.fee):
		return {"ok":false, "message":"Not enough credits for the builder fee."}
	if world._find_route(str(builder.sector), sector_id).is_empty():
		return {"ok":false, "message":"The builder cannot reach that sector."}
	var number := int(world.state.next_build_site_id)
	var site_id := "buildsite_%d" % number
	var station_id := "player_station_%d" % number
	if not find_site(world, site_id).is_empty() or not world._find_station(station_id).is_empty():
		return {"ok":false, "message":"The next build-site ID is already in use."}
	var name := "Outpost %d" % number
	var stock: Dictionary = {}
	for ware in world.state.wares:
		stock[ware.id] = 0
	var resources: Dictionary = world.state.construction_resources[sector_id]
	var station := {"id":station_id, "name":name + " (building)", "owner":world.state.player_faction_id, "sector":sector_id, "credits":0, "storage_capacity":0, "stock":stock, "sell_prices":{}, "buy_prices":{}, "natural_sources":resources.natural_sources.duplicate(true), "deposits":{}, "resource_sector":sector_id, "production":[]}
	var tasks: Array = []
	for row in estimate.modules:
		var blueprint: Dictionary = world.state.construction_blueprints[row.id]
		for _count in range(int(row.total)):
			tasks.append({"recipe_id":row.id, "duration":int(blueprint.ticks), "materials":blueprint.materials.duplicate(true), "storage":int(blueprint.storage), "started":false, "progress":0})
	var site := {"id":site_id, "station_id":station_id, "name":name, "sector":sector_id, "fee":int(estimate.fee), "paused":false, "cancelled":false, "refunded_fee":0, "completed":0, "builder_id":"", "status":"Needs materials", "build_storage":{}, "tasks":tasks}
	# The upfront fee is transferred to the actual NPC builder once, and all
	# validation is complete before balances or world objects are changed.
	world.state.starting_credits = int(world.state.starting_credits) - int(estimate.fee)
	builder.credits = int(builder.credits) + int(estimate.fee)
	world.state.next_build_site_id = number + 1
	world.state.stations.append(station)
	world.population.register_station(world, station_id)
	world.state.build_sites.append(site)
	world._record_transaction("construction_fee", BUILDER_ID, station_id, "", 0, 0, -int(estimate.fee))
	return {"ok":true, "message":"Build site placed. Deliver the listed materials.", "site_id":site_id}


func find_site(world: RefCounted, site_id: String) -> Dictionary:
	for site in world.state.get("build_sites", []):
		if site.id == site_id:
			return site
	return {}


func remaining_materials(site: Dictionary) -> Dictionary:
	var needed: Dictionary = {}
	if bool(site.get("cancelled", false)):
		return needed
	for index in range(int(site.completed), site.tasks.size()):
		var task: Dictionary = site.tasks[index]
		if task.started:
			continue
		for ware_id in task.materials:
			needed[ware_id] = int(needed.get(ware_id, 0)) + int(task.materials[ware_id])
	for ware_id in needed:
		needed[ware_id] = maxi(0, int(needed[ware_id]) - int(site.build_storage.get(ware_id, 0)))
	return needed


func deliver(world: RefCounted, ship_id: String, site_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var site := find_site(world, site_id)
	if ship.is_empty() or site.is_empty() or ship.owner != world.state.player_faction_id:
		return {"ok":false, "message":"Ship or build site is unavailable."}
	if bool(site.get("cancelled", false)):
		return {"ok":false, "message":"Construction was cancelled. Recover its materials instead."}
	if ship.sector != site.sector or ship.docked_at != site.station_id or not ship.orders.is_empty() or not ship.travel.is_empty():
		return {"ok":false, "message":"Dock the ship at this build site first."}
	var needed := remaining_materials(site)
	var transferred := 0
	for ware_id in needed:
		var amount := mini(int(needed[ware_id]), int(ship.cargo.get(ware_id, 0)))
		if amount <= 0:
			continue
		ship.cargo[ware_id] = int(ship.cargo[ware_id]) - amount
		site.build_storage[ware_id] = int(site.build_storage.get(ware_id, 0)) + amount
		if ship.has("player_trader") and ship.player_trader.phase == "to_destination" and ship.player_trader.ware_id == ware_id:
			ship.player_trader.managed_quantity = maxi(0, int(ship.player_trader.managed_quantity) - amount)
		transferred += amount
		world._record_transaction("build_delivery", ship_id, str(site.station_id), str(ware_id), amount, 0, 0)
	if transferred == 0:
		return {"ok":false, "message":"No required construction materials are aboard."}
	if not site.paused and str(site.builder_id).is_empty() and _ready_for_work(site):
		site.status = "Awaiting builder"
	return {"ok":true, "message":"Delivered %d units to build storage." % transferred}


func set_paused(world: RefCounted, site_id: String, paused: bool) -> bool:
	var site := find_site(world, site_id)
	if site.is_empty() or bool(site.get("cancelled", false)) or int(site.completed) >= site.tasks.size():
		return false
	site.paused = paused
	site.status = "Paused" if paused else ("Awaiting builder" if _ready_for_work(site) else "Needs materials")
	return true


## Completed modules and an in-progress module cannot be moved. Entries
## that have not consumed materials are safe to swap without changing stock,
## budgets, production or the builder's existing travel orders.
func first_editable_index(site: Dictionary) -> int:
	var index := int(site.completed)
	if index < site.tasks.size() and bool(site.tasks[index].started):
		index += 1
	return index


func move_queued_module(world: RefCounted, site_id: String, index: int, direction: int) -> Dictionary:
	var site := find_site(world, site_id)
	if site.is_empty() or bool(site.get("cancelled", false)):
		return {"ok":false, "message":"Choose an active construction site with queued modules."}
	if direction != -1 and direction != 1:
		return {"ok":false, "message":"Move one position up or down."}
	var other_index := index + direction
	var first := first_editable_index(site)
	if index < first or other_index < first or index >= site.tasks.size() or other_index >= site.tasks.size():
		return {"ok":false, "message":"Completed or active modules cannot move, and a queued module cannot move beyond the queue."}
	if bool(site.tasks[index].started) or bool(site.tasks[other_index].started):
		return {"ok":false, "message":"Only unstarted modules can be reordered."}
	var displaced: Dictionary = site.tasks[other_index]
	site.tasks[other_index] = site.tasks[index]
	site.tasks[index] = displaced
	if str(site.builder_id).is_empty():
		site.status = "Awaiting builder" if _ready_for_work(site) else "Needs materials"
	return {"ok":true, "message":"Queued module moved; material requirements and paid fees are unchanged.", "new_index":other_index}


func _ready_for_work(site: Dictionary) -> bool:
	if bool(site.get("cancelled", false)) or int(site.completed) >= site.tasks.size():
		return false
	var task: Dictionary = site.tasks[int(site.completed)]
	if task.started:
		return true
	for ware_id in task.materials:
		if int(site.build_storage.get(ware_id, 0)) < int(task.materials[ware_id]):
			return false
	return true


## Cancel only unfinished work. A module which already consumed its inputs is
## allowed to finish, avoiding a phantom loss of goods or completed production.
## Fees for never-started modules return from the NPC builder's actual wallet.
## Construction storage remains physical stock until recovered by a docked ship.
func cancel(world: RefCounted, site_id: String) -> Dictionary:
	var site := find_site(world, site_id)
	var builder: Dictionary = world._find_ship(BUILDER_ID)
	if site.is_empty() or builder.is_empty() or bool(site.get("cancelled", false)) or int(site.completed) >= site.tasks.size():
		return {"ok":false, "message":"No unfinished active construction is available to cancel."}
	var refund := 0
	for index in range(int(site.completed), site.tasks.size()):
		var task: Dictionary = site.tasks[index]
		if task.started:
			continue
		var blueprint: Dictionary = world.state.construction_blueprints.get(str(task.recipe_id), {})
		if blueprint.is_empty():
			return {"ok":false, "message":"The builder fee schedule is unavailable."}
		refund += int(blueprint.fee)
	if refund > int(site.fee) or refund > int(builder.credits):
		return {"ok":false, "message":"The builder cannot fund the outstanding fee refund."}
	var active: bool = int(site.completed) < site.tasks.size() and bool(site.tasks[int(site.completed)].started)
	site.cancelled = true
	site.paused = false
	site.refunded_fee = refund
	if refund > 0:
		builder.credits = int(builder.credits) - refund
		world.state.starting_credits = int(world.state.starting_credits) + refund
		world._record_transaction("construction_refund", BUILDER_ID, str(site.station_id), "", 0, 0, refund)
	for ship in world.state.ships:
		if ship.has("build_supply") and ship.build_supply.enabled and ship.build_supply.site_id == site.id:
			world.build_supply.stop(ship)
	if not active:
		# An NPC builder already travelling completes its route, without starting
		# anything at the cancelled site or losing its queued movement.
		if builder.build_assignment == site.id:
			builder.build_assignment = ""
		site.builder_id = ""
	var station: Dictionary = world._find_station(str(site.station_id))
	if not station.is_empty():
		station.name = str(site.name) if int(site.completed) > 0 else str(site.name) + " (cancelled plot)"
	site.status = "Finishing current module" if active else "Cancelled"
	return {"ok":true, "message":"Cancelled unstarted modules; refunded %d CR. Unused material remains at the site for recovery." % refund, "refund":refund}


func recover(world: RefCounted, ship_id: String, site_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var site := find_site(world, site_id)
	if ship.is_empty() or site.is_empty() or ship.owner != world.state.player_faction_id or not bool(site.get("cancelled", false)):
		return {"ok":false, "message":"Select one of your cancelled construction sites."}
	if ship.sector != site.sector or ship.docked_at != site.station_id or not ship.orders.is_empty() or not ship.travel.is_empty():
		return {"ok":false, "message":"Dock the recovery ship at the cancelled site first."}
	var free_volume := maxi(0, int(ship.cargo_capacity) - int(world.cargo_volume(ship_id)))
	var recovered := 0
	var ware_ids: Array = site.build_storage.keys()
	ware_ids.sort()
	for ware_id in ware_ids:
		var ware: Dictionary = world._find_ware(str(ware_id))
		if ware.is_empty() or int(ware.volume) <= 0:
			continue
		var amount := mini(int(site.build_storage[ware_id]), int(free_volume / int(ware.volume)))
		if amount <= 0:
			continue
		site.build_storage[ware_id] = int(site.build_storage[ware_id]) - amount
		ship.cargo[ware_id] = int(ship.cargo.get(ware_id, 0)) + amount
		free_volume -= amount * int(ware.volume)
		recovered += amount
		world._record_transaction("construction_recovery", ship_id, str(site.station_id), str(ware_id), amount, 0, 0)
	if recovered == 0:
		return {"ok":false, "message":"No construction material fits in this ship's remaining cargo space."}
	return {"ok":true, "message":"Recovered %d physical construction material units." % recovered, "quantity":recovered}


func tick(world: RefCounted) -> void:
	var builder: Dictionary = world._find_ship(BUILDER_ID)
	if builder.is_empty():
		return
	for site in world.state.build_sites:
		if bool(site.get("cancelled", false)):
			var still_building: bool = not str(site.builder_id).is_empty() and int(site.completed) < site.tasks.size() and bool(site.tasks[int(site.completed)].started)
			site.status = "Finishing current module" if still_building else "Cancelled"
		elif int(site.completed) >= site.tasks.size():
			site.status = "Complete"
		elif site.paused:
			site.status = "Paused"
		elif str(site.builder_id).is_empty():
			site.status = "Awaiting builder" if _ready_for_work(site) else "Needs materials"
	var current := find_site(world, str(builder.build_assignment))
	if not current.is_empty() and bool(current.get("cancelled", false)) and (int(current.completed) >= current.tasks.size() or not bool(current.tasks[int(current.completed)].started)):
		current.builder_id = ""
		builder.build_assignment = ""
		current = {}
	if not current.is_empty() and (current.paused or int(current.completed) >= current.tasks.size()):
		if not builder.orders.is_empty() or not builder.travel.is_empty():
			return
		current.builder_id = ""
		builder.build_assignment = ""
		current = {}
	if current.is_empty():
		builder.build_assignment = ""
		if not builder.orders.is_empty() or not builder.travel.is_empty():
			return
		for site in world.state.build_sites:
			if bool(site.get("cancelled", false)) or site.paused or not _ready_for_work(site) or world._find_route(str(builder.sector), str(site.sector)).is_empty():
				continue
			current = site
			builder.build_assignment = site.id
			site.builder_id = builder.id
			break
	if current.is_empty():
		return
	if not builder.orders.is_empty() or not builder.travel.is_empty():
		current.status = "Builder en route"
		return
	if builder.sector != current.sector:
		if world._queue_ship_route(builder, str(current.sector)):
			current.status = "Builder en route"
		else:
			current.status = "Builder cannot reach site"
		return
	var task: Dictionary = current.tasks[int(current.completed)]
	if not task.started:
		if not _ready_for_work(current):
			current.builder_id = ""
			builder.build_assignment = ""
			current.status = "Needs materials"
			return
		for ware_id in task.materials:
			current.build_storage[ware_id] = int(current.build_storage[ware_id]) - int(task.materials[ware_id])
		task.started = true
	task.progress = int(task.progress) + 1
	current.status = "Building"
	builder.status = "Building"
	if int(task.progress) < int(task.duration):
		return
	var station: Dictionary = world._find_station(str(current.station_id))
	if station.is_empty():
		current.status = "Station unavailable"
		return
	# A residence is a real service module, not a fictitious production
	# recipe. It creates living space only after physical materials and all
	# builder work are completed; it never creates adults, children or crew.
	if world.habitation.is_habitat(world, str(task.recipe_id)):
		if not world.habitation.on_commission(world, str(station.id), str(task.recipe_id)):
			current.status = "Cannot commission habitat"
			return
	else:
		station.production.append({"recipe_id":task.recipe_id, "progress":0, "cycles":0, "status":"Waiting"})
	station.storage_capacity = int(station.storage_capacity) + int(task.storage)
	current.completed = int(current.completed) + 1
	if bool(current.get("cancelled", false)):
		station.name = current.name
		current.status = "Cancelled"
		current.builder_id = ""
		builder.build_assignment = ""
	elif int(current.completed) >= current.tasks.size():
		station.name = current.name
		current.status = "Complete"
		current.builder_id = ""
		builder.build_assignment = ""
