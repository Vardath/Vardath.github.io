extends RefCounted
## Pass 36: independently versioned salt byproduct from the existing physical
## organic-waste recycler. No historical water, salt or credits are backfilled.
## Old v1 ecology saves retain their original recipe until this one-time upgrade.

const VERSION := 1
const SALT_WARE := {"id":"salt", "name":"Recovered Mineral Salt", "volume":1}
const SALT_CATALOG := {"ware_id":"salt", "recipe_id":"water_recycling", "cycle_interval":4, "quantity":1}
const SALT_CYCLES := 4
const RECOVERY_EVENT := "salt_recovered"


func prepare(target: Dictionary) -> Error:
	if target.has("salt_recovery_version"):
		return OK if int(target.salt_recovery_version) == VERSION and target.get("salt_recovery_catalog") == SALT_CATALOG else ERR_UNAVAILABLE
	if target.has("salt_recovery_catalog") or int(target.get("ecology_version", 0)) != 1:
		return ERR_INVALID_DATA
	for ware in target.wares:
		if ware.id == SALT_WARE.id:
			return ERR_ALREADY_IN_USE
	var recycler: Dictionary = {}
	for recipe in target.recipes:
		if recipe.id == "water_recycling":
			recycler = recipe
			break
	if recycler.is_empty() or not recycler.get("outputs") is Dictionary or recycler.outputs.size() != 2 or float(recycler.outputs.get("potable_water", 0)) != 1.0 or float(recycler.outputs.get("fertile_soil", 0)) != 1.0:
		return ERR_INVALID_DATA
	for station in target.stations:
		if station.stock.has("salt"):
			printerr("Salt migration encountered pre-existing station salt: ", station.id)
			return ERR_ALREADY_IN_USE
	for ship in target.ships:
		if ship.cargo.has("salt"):
			return ERR_ALREADY_IN_USE
	# Atomic additive migration, performed only once after source checks.
	target.wares.append(SALT_WARE.duplicate(true))
	for station in target.stations:
		station.stock["salt"] = 0
	target["salt_recovery_version"] = VERSION
	target["salt_recovery_catalog"] = SALT_CATALOG.duplicate(true)
	return OK


func record_cycle(world: RefCounted, station: Dictionary, module: Dictionary) -> void:
	if str(module.get("recipe_id", "")) != "water_recycling" or int(world.state.get("salt_recovery_version", 0)) != VERSION:
		return
	# One real concentrated mineral-salt unit per FOUR successful
	# wastewater cycles: eight physical waste units and four paid energy
	# cells are consumed before a unit can be recovered. The ordinary
	# water and soil outputs remain unmodified and finite.
	if int(module.get("cycles", 0)) < 1 or int(module.cycles) % SALT_CYCLES != 0:
		return
	if int(world.station_volume(str(station.id))) + 1 > int(station.storage_capacity):
		# Preserve output/storage conservation. With the vanilla recycler's
		# 3 input / 2 output volumes, each physical cycle frees at least
		# one slot for this occasional salt byproduct.
		return
	station.stock["salt"] = int(station.stock.get("salt", 0)) + 1
	world._record_transaction(RECOVERY_EVENT, "", str(station.id), "salt", 1, 0, 0)
