extends RefCounted
## Deterministic logistics shared by faction freighters and player traders.
## Both pay for stock, use sector routes and sell only after docking.

const WORKING_CAPITAL := 1000
const TARGET_CYCLES := 8
const RETRY_TICKS := 5


func tick(world: RefCounted, ship: Dictionary) -> void:
	var is_player: bool = ship.owner == world.state.player_faction_id
	var job: Dictionary = ship.player_trader if is_player else ship.autotrader
	if not job.enabled or not ship.orders.is_empty() or not ship.travel.is_empty():
		return
	if int(job.retry_ticks) > 0:
		job.retry_ticks = int(job.retry_ticks) - 1
		ship.status = "Waiting for buyer" if job.phase == "to_destination" else "Waiting for trade"
		return
	if job.phase == "idle":
		if not is_player and not bool(job.funded):
			var home: Dictionary = world._find_station(str(job.home_station_id))
			if home.is_empty() or home.owner != ship.owner:
				home = {}
				for station in world.state.stations:
					if station.owner == ship.owner:
						home = station
						job.home_station_id = station.id
						break
			if home.is_empty():
				job.retry_ticks = RETRY_TICKS
				ship.status = "Waiting for funds"
				return
			if ship.sector != home.sector:
				_go(world, ship, str(home.sector))
				return
			var amount := mini(WORKING_CAPITAL, int(home.credits))
			if amount <= 0:
				job.retry_ticks = RETRY_TICKS
				ship.status = "Waiting for funds"
				return
			home.credits = int(home.credits) - amount
			ship.credits = int(ship.credits) + amount
			job.funded = true
			world._record_transaction("funding", str(ship.id), str(home.id), "", 0, 0, amount)
		var candidate := _plan_trade(world, ship)
		if candidate.is_empty():
			job.retry_ticks = RETRY_TICKS
			ship.status = "Waiting for trade"
			return
		job.source_id = candidate.source_id
		job.destination_id = candidate.destination_id
		job.ware_id = candidate.ware_id
		job.quantity = candidate.quantity
		job.phase = "to_source"
		var source: Dictionary = world._find_station(str(job.source_id))
		if not _go(world, ship, str(source.sector)):
			_reset(job)
		return
	if job.phase == "to_source":
		var source: Dictionary = world._find_station(str(job.source_id))
		var destination: Dictionary = world._find_station(str(job.destination_id))
		var ware: Dictionary = world._find_ware(str(job.ware_id))
		if source.is_empty() or destination.is_empty() or ware.is_empty():
			_reset(job)
			return
		if ship.sector != source.sector:
			if not _go(world, ship, str(source.sector)):
				_reset(job)
			return
		var amount := _available_quantity(world, ship, source, destination, ware, int(job.quantity), true)
		if amount <= 0:
			_reset(job)
			return
		ship.docked_at = source.id
		ship.status = "Docked"
		var purchase: Dictionary = world._trade_for_ship(ship, str(source.id), str(ware.id), amount, true)
		if not purchase.ok:
			_reset(job)
			return
		job.quantity = amount
		if is_player:
			job.managed_quantity = amount
		job.phase = "to_destination"
		_go(world, ship, str(destination.sector))
		return
	if job.phase == "to_destination":
		var ware: Dictionary = world._find_ware(str(job.ware_id))
		if ware.is_empty() or _managed_cargo(ship, job) <= 0:
			_reset(job)
			return
		var destination: Dictionary = world._find_station(str(job.destination_id))
		if destination.is_empty() or _sale_capacity(world, destination, ware) <= 0:
			_redirect(world, ship, ware)
			return
		if ship.sector != destination.sector:
			if not _go(world, ship, str(destination.sector)):
				_redirect(world, ship, ware)
			return
		var amount := mini(_managed_cargo(ship, job), _sale_capacity(world, destination, ware))
		ship.docked_at = destination.id
		ship.status = "Docked"
		var sale: Dictionary = world._trade_for_ship(ship, str(destination.id), str(ware.id), amount, false)
		if not sale.ok:
			_redirect(world, ship, ware)
			return
		if is_player:
			job.managed_quantity = int(job.managed_quantity) - amount
		if _managed_cargo(ship, job) == 0:
			_reset(job)
		else:
			_redirect(world, ship, ware)


func _go(world: RefCounted, ship: Dictionary, destination: String) -> bool:
	if ship.sector == destination:
		return true
	return world._queue_ship_route(ship, destination)


func _reset(job: Dictionary) -> void:
	job.phase = "idle"
	job.source_id = ""
	job.destination_id = ""
	job.ware_id = ""
	job.quantity = 0
	job.retry_ticks = 0
	if job.has("managed_quantity"):
		job.managed_quantity = 0


func _managed_cargo(ship: Dictionary, job: Dictionary) -> int:
	var carried := int(ship.cargo.get(job.ware_id, 0))
	if job.has("managed_quantity"):
		return mini(carried, int(job.managed_quantity))
	return carried


func _demand(world: RefCounted, station: Dictionary, ware_id: String) -> int:
	var target := 0
	for module in station.production:
		var recipe: Dictionary = world._find_recipe(str(module.recipe_id))
		if not recipe.is_empty():
			target += int(recipe.inputs.get(ware_id, 0)) * TARGET_CYCLES
	return maxi(0, target - int(station.stock.get(ware_id, 0)))


func _sale_capacity(world: RefCounted, station: Dictionary, ware: Dictionary) -> int:
	if not station.buy_prices.has(ware.id):
		return 0
	var price := int(station.buy_prices[ware.id])
	if price <= 0:
		return 0
	var free_space := maxi(0, int(station.storage_capacity) - int(world.station_volume(str(station.id))))
	return mini(int(int(station.credits) / price), int(free_space / int(ware.volume)))


func _available_quantity(world: RefCounted, ship: Dictionary, source: Dictionary, destination: Dictionary, ware: Dictionary, requested: int, require_demand: bool) -> int:
	if not source.sell_prices.has(ware.id) or not destination.buy_prices.has(ware.id):
		return 0
	var purchase_price := int(source.sell_prices[ware.id])
	var sale_price := int(destination.buy_prices[ware.id])
	if purchase_price <= 0 or sale_price <= purchase_price:
		return 0
	var capacity := maxi(0, int(ship.cargo_capacity) - int(world.cargo_volume(str(ship.id))))
	var quantity := mini(requested, int(source.stock.get(ware.id, 0)))
	quantity = mini(quantity, int(capacity / int(ware.volume)))
	var wallet := int(world.state.starting_credits) if ship.owner == world.state.player_faction_id else int(ship.credits)
	quantity = mini(quantity, int(wallet / purchase_price))
	quantity = mini(quantity, _sale_capacity(world, destination, ware))
	if require_demand:
		quantity = mini(quantity, _demand(world, destination, str(ware.id)))
	return maxi(0, quantity)


func _plan_trade(world: RefCounted, ship: Dictionary) -> Dictionary:
	var best: Dictionary = {}
	var best_score := -1
	for source in world.state.stations:
		var to_source: Array = world._find_route(str(ship.sector), str(source.sector))
		if to_source.is_empty():
			continue
		for destination in world.state.stations:
			if source.id == destination.id:
				continue
			var to_destination: Array = world._find_route(str(source.sector), str(destination.sector))
			if to_destination.is_empty():
				continue
			for ware in world.state.wares:
				var quantity := _available_quantity(world, ship, source, destination, ware, int(ship.cargo_capacity), true)
				if quantity <= 0:
					continue
				var profit := (int(destination.buy_prices[ware.id]) - int(source.sell_prices[ware.id])) * quantity
				var legs := to_source.size() + to_destination.size() - 2
				var score := int(profit * 1000 / (legs + 1))
				if score > best_score:
					best_score = score
					best = {"source_id": source.id, "destination_id": destination.id, "ware_id": ware.id, "quantity": quantity}
	return best


func _redirect(world: RefCounted, ship: Dictionary, ware: Dictionary) -> void:
	var job: Dictionary = ship.player_trader if ship.owner == world.state.player_faction_id else ship.autotrader
	var best: Dictionary = {}
	var best_score := -1
	for station in world.state.stations:
		var quantity := mini(_managed_cargo(ship, job), _sale_capacity(world, station, ware))
		if quantity <= 0:
			continue
		var route: Array = world._find_route(str(ship.sector), str(station.sector))
		if route.is_empty():
			continue
		var score := int(int(station.buy_prices[ware.id]) * quantity * 1000 / maxi(1, route.size()))
		if score > best_score:
			best_score = score
			best = station
	if best.is_empty():
		job.destination_id = ""
		job.retry_ticks = RETRY_TICKS
		ship.status = "Waiting for buyer"
		return
	job.destination_id = best.id
	if not _go(world, ship, str(best.sector)):
		job.destination_id = ""
		job.retry_ticks = RETRY_TICKS
