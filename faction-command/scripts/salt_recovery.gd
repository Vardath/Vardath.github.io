extends RefCounted
## Pass 36: independently versioned salt byproduct from the existing physical
## organic-waste recycler. No historical water, salt or credits are backfilled.
## Old v1 ecology saves retain their original recipe until this one-time upgrade.

const VERSION := 1
const SALT_WARE := {"id":"salt", "name":"Recovered Mineral Salt", "volume":1}
const SALT_CATALOG := {"ware_id":"salt", "recipe_id":"water_recycling", "quantity_per_cycle":1}
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
	if recycler.is_empty() or recycler.outputs != {"potable_water":1, "fertile_soil":1}:
		return ERR_INVALID_DATA
	for station in target.stations:
		if station.stock.has("salt"):
			return ERR_ALREADY_IN_USE
	for ship in target.ships:
		if ship.cargo.has("salt"):
			return ERR_ALREADY_IN_USE
	# Atomic additive migration, performed only once after source checks.
	target.wares.append(SALT_WARE.duplicate(true))
	for station in target.stations:
		station.stock["salt"] = 0
	recycler.outputs["salt"] = 1
	target["salt_recovery_version"] = VERSION
	target["salt_recovery_catalog"] = SALT_CATALOG.duplicate(true)
	return OK


func record_cycle(world: RefCounted, station: Dictionary, recipe_id: String) -> void:
	if recipe_id != "water_recycling" or int(world.state.get("salt_recovery_version", 0)) != VERSION:
		return
	# Called only AFTER the ordinary production recipe has actually
	# consumed waste and energy, and placed all three outputs into stock.
	world._record_transaction(RECOVERY_EVENT, "", str(station.id), "salt", 1, 0, 0)
