extends RefCounted
## One selected player ship supplies one build site with real cargo and credits.
## Ship orders and carried goods remain the player's property when stopped.

const RETRY_TICKS := 5


func prepare(target: Dictionary) -> Error:
	if target.has("build_supply_version"):
		return OK if target.build_supply_version == 1 else ERR_UNAVAILABLE
	for ship in target.ships:
		if ship.owner == target.player_faction_id:
			ship["build_supply"] = _empty_job()
	target["build_supply_version"] = 1
	return OK


func _empty_job() -> Dictionary:
	return {"enabled":false, "site_id":"", "phase":"idle", "source_id":"", "ware_id":"", "retry_ticks":0, "wait_reason":""}


func assign(world: RefCounted, ship_id: String, site_id: String) -> Dictionary:
	var ship: Dictionary = world._find_ship(ship_id)
	var site: Dictionary = world.construction.find_site(world, site_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id or not ship.has("build_supply") or site.is_empty():
		return {"ok":false, "message":"Ship or build site is unavailable."}
	if not _has_need(world.construction.remaining_materials(site)):
		return {"ok":false, "message":"This site does not need more materials."}
	ship.player_trader.enabled = false
	ship.build_supply = _empty_job()
	ship.build_supply.enabled = true
	ship.build_supply.site_id = site_id
	ship.role = "Build Supplier"
	return {"ok":true, "message":"Supply assigned. Queued orders finish first; purchases use your credits."}


func stop(ship: Dictionary) -> void:
	if not ship.has("build_supply"):
		return
	ship.build_supply = _empty_job()
	if ship.get("role", "") == "Build Supplier":
		ship.role = "Unassigned"


func _has_need(needed: Dictionary) -> bool:
	for amount in needed.values():
		if int(amount) > 0:
			return true
	return false


func _other_inbound(world: RefCounted, ship: Dictionary, site_id: String, ware_id: String) -> int:
	var result := 0
	for other in world.state.ships:
		if other.id == ship.id or not other.has("build_supply"):
			continue
		var job: Dictionary = other.build_supply
		if job.enabled and job.site_id == site_id and job.phase == "to_site":
			result += int(other.cargo.get(ware_id, 0))
	return result


func _reset_trip(job: Dictionary) -> void:
	job.phase = "idle"
	job.source_id = ""
	job.ware_id = ""
	job.retry_ticks = 0
	job.wait_reason = ""


func _wait(job: Dictionary, ship: Dictionary, reason: String) -> void:
	job.retry_ticks = RETRY_TICKS
	job.wait_reason = reason
	ship.status = reason


func _go(world: RefCounted, ship: Dictionary, sector_id: String) -> bool:
	return ship.sector == sector_id or world._queue_ship_route(ship, sector_id)


func _carried_for_site(ship: Dictionary, needed: Dictionary) -> String:
	for ware_id in needed:
		if int(needed[ware_id]) > 0 and int(ship.cargo.get(ware_id, 0)) > 0:
			return str(ware_id)
	return ""


func _candidate(world: RefCounted, ship: Dictionary, site: Dictionary, needed: Dictionary) -> Dictionary:
	var best: Dictionary = {}
	var best_price := 2147483647
	var best_legs := 2147483647
	var has_unreserved_need := false
	var has_space := false
	var has_stock := false
	var has_affordable := false
	var free_volume := maxi(0, int(ship.cargo_capacity) - int(world.cargo_volume(str(ship.id))))
	for ware_id in needed:
		var quantity_needed := maxi(0, int(needed[ware_id]) - _other_inbound(world, ship, str(site.id), str(ware_id)))
		if quantity_needed <= 0:
			continue
		has_unreserved_need = true
		var ware: Dictionary = world._find_ware(str(ware_id))
		if ware.is_empty() or int(ware.volume) > free_volume:
			continue
		has_space = true
		for station in world.state.stations:
			var available := int(station.stock.get(ware_id, 0))
			if available <= 0:
				continue
			var owned: bool = station.owner == world.state.player_faction_id
			var price := 0 if owned else int(station.sell_prices.get(ware_id, 0))
			if not owned and price <= 0:
				continue
			var first_route: Array = world._find_route(str(ship.sector), str(station.sector))
			var second_route: Array = world._find_route(str(station.sector), str(site.sector))
			if first_route.is_empty() or second_route.is_empty():
				continue
			has_stock = true
			var amount := mini(quantity_needed, mini(available, int(free_volume / int(ware.volume))))
			if not owned:
				amount = mini(amount, int(int(world.state.starting_credits) / price))
			if amount <= 0:
				continue
			has_affordable = true
			var legs := first_route.size() + second_route.size() - 2
			if price < best_price or (price == best_price and legs < best_legs):
				best_price = price
				best_legs = legs
				best = {"source_id":station.id, "ware_id":ware_id}
	if not best.is_empty():
		return best
	if not has_unreserved_need:
		return {"waiting":"Waiting for other deliveries"}
	if not has_space:
		return {"waiting":"Waiting for cargo space"}
	if not has_stock:
		return {"waiting":"Waiting for material stock"}
	if not has_affordable:
		return {"waiting":"Waiting for credits"}
	return {"waiting":"Waiting for supplies"}


func tick(world: RefCounted, ship: Dictionary) -> void:
	var job: Dictionary = ship.build_supply
	if not job.enabled or not ship.orders.is_empty() or not ship.travel.is_empty():
		return
	var site: Dictionary = world.construction.find_site(world, str(job.site_id))
	if site.is_empty():
		stop(ship)
		ship.status = "Build site unavailable"
		return
	var needed: Dictionary = world.construction.remaining_materials(site)
	if not _has_need(needed):
		stop(ship)
		ship.status = "Build supplied"
		return
	if int(job.retry_ticks) > 0:
		job.retry_ticks = int(job.retry_ticks) - 1
		ship.status = str(job.wait_reason)
		return
	var carried := _carried_for_site(ship, needed)
	if not carried.is_empty() and job.phase != "to_site":
		job.phase = "to_site"
		job.source_id = ""
		job.ware_id = carried
	if job.phase == "idle":
		var choice := _candidate(world, ship, site, needed)
		if choice.has("waiting"):
			_wait(job, ship, str(choice.waiting))
			return
		job.source_id = choice.source_id
		job.ware_id = choice.ware_id
		job.phase = "to_source"
		job.wait_reason = ""
	if job.phase == "to_source":
		var source: Dictionary = world._find_station(str(job.source_id))
		var ware: Dictionary = world._find_ware(str(job.ware_id))
		if source.is_empty() or ware.is_empty():
			_reset_trip(job)
			return
		if ship.sector != source.sector:
			if not _go(world, ship, str(source.sector)):
				_reset_trip(job)
			return
		var need := maxi(0, int(needed.get(job.ware_id, 0)) - _other_inbound(world, ship, str(site.id), str(job.ware_id)))
		var amount := mini(need, int(source.stock.get(job.ware_id, 0)))
		amount = mini(amount, int(maxi(0, int(ship.cargo_capacity) - int(world.cargo_volume(str(ship.id)))) / int(ware.volume)))
		var owned: bool = source.owner == world.state.player_faction_id
		var price := 0 if owned else int(source.sell_prices.get(job.ware_id, 0))
		if not owned and price > 0:
			amount = mini(amount, int(int(world.state.starting_credits) / price))
		elif not owned:
			amount = 0
		if amount <= 0:
			_reset_trip(job)
			return
		ship.docked_at = source.id
		ship.status = "Docked"
		var result: Dictionary = world.transfer_player_station(str(ship.id), str(source.id), str(ware.id), amount, false) if owned else world._trade_for_ship(ship, str(source.id), str(ware.id), amount, true)
		if not result.ok:
			_reset_trip(job)
			return
		job.phase = "to_site"
		job.source_id = ""
	if job.phase == "to_site":
		if ship.sector != site.sector:
			if not _go(world, ship, str(site.sector)):
				_wait(job, ship, "Waiting for route to site")
			return
		ship.docked_at = site.station_id
		ship.status = "Docked"
		world.construction.deliver(world, str(ship.id), str(site.id))
		_reset_trip(job)
		if not _has_need(world.construction.remaining_materials(site)):
			stop(ship)
			ship.status = "Build supplied"
