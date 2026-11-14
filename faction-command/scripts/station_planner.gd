extends RefCounted
## A read-only production planner. Rates are per 60 simulation ticks.
## Construction and sector resource surveys are intentionally separate.

const MAX_MODULES := 10000
const EPSILON := 0.000001
const ResearchScript = preload("res://scripts/research.gd")

var research = ResearchScript.new()


func preview(state: Dictionary, requested: Dictionary, mode: String, selected_imports: Array, sector_id: String = "") -> Dictionary:
	var errors: Array[String] = []
	var warnings: Array[String] = []
	var recipes: Dictionary = {}
	var producers: Dictionary = {}
	var wares: Dictionary = {}
	for ware in state.get("wares", []):
		wares[str(ware.id)] = str(ware.name)
	for original in state.get("recipes", []):
		var recipe: Dictionary = research.adjusted_recipe(state, original, true)
		var id := str(recipe.id)
		if recipes.has(id) or int(recipe.cycle_ticks) <= 0:
			errors.append("Invalid or duplicate production recipe: " + id)
			continue
		recipes[id] = recipe
		for ware_id in recipe.outputs:
			if float(recipe.outputs[ware_id]) <= 0.0:
				continue
			if not producers.has(ware_id):
				producers[ware_id] = recipe
			elif not warnings.has("Several recipes produce %s; using %s." % [wares.get(ware_id, ware_id), producers[ware_id].name]):
				warnings.append("Several recipes produce %s; using %s." % [wares.get(ware_id, ware_id), producers[ware_id].name])
	# Habitats are services, not factories. Include their recurring station
	# Energy Cells consumption in the same dependency graph so self-sufficient
	# construction can add solar generation, or explicitly import it.
	for habitat_id in state.get("habitation_catalog", {}):
		var home: Dictionary = state.habitation_catalog[habitat_id]
		if recipes.has(habitat_id):
			errors.append("Habitat ID collides with a production recipe: " + str(habitat_id))
			continue
		var requirements: Dictionary = {"energy_cells":int(home.energy_per_60)}
		for ware_id in state.get("provisions_catalog", {}).get("habitat_needs_per_60", {}):
			requirements[ware_id] = int(state.provisions_catalog.habitat_needs_per_60[ware_id])
		recipes[habitat_id] = {"id":str(habitat_id), "name":str(home.name), "inputs":requirements, "outputs":{}, "cycle_ticks":60}
	for school_id in state.get("education_catalog", {}):
		var school: Dictionary = state.education_catalog[school_id]
		if recipes.has(school_id):
			errors.append("School ID collides with a production recipe: " + str(school_id))
			continue
		# School and teaching records are REAL ongoing demands, not
		# manufacturing outputs or free graduation tokens.
		recipes[school_id] = {"id":str(school_id), "name":str(school.name), "inputs":{"energy_cells":int(school.energy_per_60), str(school.material):int(school.material_per_60)}, "outputs":{}, "cycle_ticks":60}
	if mode not in ["self", "selected", "all"]:
		errors.append("Choose a valid sourcing mode.")
	var imported: Dictionary = {}
	if mode == "all":
		for ware_id in wares:
			imported[ware_id] = true
	elif mode == "selected":
		for ware_id in selected_imports:
			if not wares.has(ware_id):
				errors.append("Unknown import: " + str(ware_id))
			else:
				imported[ware_id] = true
	var counts: Dictionary = {}
	for id in recipes:
		counts[id] = 0
	for id in requested:
		var value: Variant = requested[id]
		if not recipes.has(id) or not value is int or int(value) < 0 or int(value) > 1000:
			errors.append("Invalid requested module quantity: " + str(id))
		else:
			counts[id] = int(value)
	var visited: Dictionary = {}
	var visiting: Dictionary = {}
	for id in counts:
		if int(counts[id]) > 0:
			for ware_id in recipes[id].inputs:
				_check_cycle(str(ware_id), producers, imported, visiting, visited, errors, wares)
	if int(requested.get("water_recycling", 0)) > 0 or int(requested.get("soil_agriculture", 0)) > 0:
		warnings.append("Recycling recovers potable water and fertile soil ONLY from physical organic waste generated when real settled adults consume food and water. Empty habitats and ship crews supply none; import organic waste or house/provision residents before expecting output. Soil farms consume real reclaimed soil, water and power.")
	# An import exception can break a cyclic recipe graph, but the loop may
	# still need a delivery or starter stock before it can begin operating.
	if errors.is_empty() and not imported.is_empty():
		var cyclic_without_imports: Array[String] = []
		var full_visited: Dictionary = {}
		for id in counts:
			if int(counts[id]) > 0:
				for ware_id in recipes[id].inputs:
					_check_cycle(str(ware_id), producers, {}, {}, full_visited, cyclic_without_imports, wares)
		if not cyclic_without_imports.is_empty():
			warnings.append("A cyclic production chain may need imported starter stock before it can run.")
	if errors.is_empty():
		# Each pass adds enough whole modules for a currently unmet input.
		# Recompute rates as dependencies are added so shared inputs are counted
		# once across the entire station, including already chosen modules.
		var stable := false
		for _pass in range(MAX_MODULES):
			var rates := _rates(recipes, counts)
			var changed := false
			var ware_ids: Array = rates.demand.keys()
			ware_ids.sort()
			for ware_id in ware_ids:
				if imported.has(ware_id) or not producers.has(ware_id):
					continue
				var deficit := float(rates.demand[ware_id]) - float(rates.supply.get(ware_id, 0.0))
				if deficit <= EPSILON:
					continue
				var recipe: Dictionary = producers[ware_id]
				var per_module := 60.0 * float(recipe.outputs[ware_id]) / float(recipe.cycle_ticks)
				var add_count := maxi(1, int(ceil(deficit / per_module - EPSILON)))
				var id := str(recipe.id)
				if int(counts[id]) + add_count > MAX_MODULES:
					errors.append("The plan exceeds the current module limit.")
					break
				counts[id] = int(counts[id]) + add_count
				changed = true
				# Recalculate after every addition; one recipe can make multiple wares.
				break
			if not errors.is_empty():
				break
			if not changed:
				stable = true
				break
		if not stable and errors.is_empty():
			errors.append("Could not resolve the module dependencies.")
	var rates := _rates(recipes, counts)
	var module_rows: Array[Dictionary] = []
	var known_resources: Dictionary = state.get("construction_resources", {}).get(sector_id, {})
	for original in state.get("recipes", []):
		var id := str(original.id)
		if not counts.has(id) or int(counts[id]) <= 0:
			continue
		var recipe: Dictionary = recipes[id]
		var chosen := int(requested.get(id, 0))
		module_rows.append({"id":id, "name":str(recipe.name), "chosen":chosen, "added":int(counts[id]) - chosen, "total":int(counts[id])})
		for ware_id in recipe.get("catalysts", {}):
			var message := "Requires %d %s as a reusable source; obtain it before copying begins." % [int(recipe.catalysts[ware_id]), str(wares.get(ware_id, ware_id))]
			if not warnings.has(message):
				warnings.append(message)
		if not str(recipe.get("source", "")).is_empty():
			var message := "Requires %s; local availability is not yet surveyed." % str(recipe.source).capitalize()
			if not known_resources.is_empty():
				message = "" if recipe.source in known_resources.natural_sources else "No %s is available in this sector." % str(recipe.source)
			if not message.is_empty() and not warnings.has(message):
				warnings.append(message)
		if not recipe.get("deposit", {}).is_empty():
			var resource := str(recipe.deposit.resource)
			var message := "Requires a finite %s deposit; local availability is not yet surveyed." % str(wares.get(resource, resource))
			if not known_resources.is_empty():
				var remaining := int(known_resources.deposits.get(resource, 0))
				message = "Finite %s reserve in this sector: %d units, shared by your stations." % [str(wares.get(resource, resource)), remaining] if remaining >= int(recipe.deposit.quantity) else "No usable %s deposit remains in this sector." % str(wares.get(resource, resource))
			if not warnings.has(message):
				warnings.append(message)
	for habitat_id in state.get("habitation_catalog", {}):
		if int(counts.get(habitat_id, 0)) < 1:
			continue
		var home: Dictionary = state.habitation_catalog[habitat_id]
		var chosen: int = int(requested.get(habitat_id, 0))
		module_rows.append({"id":str(habitat_id), "name":str(home.name), "chosen":chosen, "added":int(counts[habitat_id]) - chosen, "total":int(counts[habitat_id]), "housing_capacity":int(home.capacity) * int(counts[habitat_id]), "energy_per_60":int(home.energy_per_60) * int(counts[habitat_id]), "provisions_per_60":state.get("provisions_catalog", {}).get("habitat_needs_per_60", {}).duplicate(true)})
	for school_id in state.get("education_catalog", {}):
		if int(counts.get(school_id, 0)) <= 0:
			continue
		var school: Dictionary = state.education_catalog[school_id]
		var chosen: int = int(requested.get(school_id, 0))
		module_rows.append({"id":str(school_id), "name":str(school.name), "chosen":chosen, "added":int(counts[school_id]) - chosen, "total":int(counts[school_id]), "school_seats":int(school.seats) * int(counts[school_id]), "school_target":str(school.target), "education_energy_per_60":int(school.energy_per_60) * int(counts[school_id]), "education_material":str(school.material)})
	if not state.get("education_catalog", {}).is_empty() and module_rows.any(func(row): return row.has("school_seats")):
		warnings.append("Education facilities create classrooms, NOT free students, teachers, skills or research. Enrol real housed residents, appoint existing adults as instructors and physically supply archival records, power and salary credits. College certificates are foundational theory only, not licensed pilots or marines.")
	if not state.get("habitation_catalog", {}).is_empty() and module_rows.any(func(row): return row.has("housing_capacity")):
		warnings.append("Habitats provide housing capacity, not instant residents, crew or births. Every service cycle requires real Energy Cells, Potable Water, Food Rations and Medical Supplies; household growth, ageing and species compatibility are future systems.")
	var ware_rows: Array[Dictionary] = []
	for ware in state.get("wares", []):
		var ware_id := str(ware.id)
		var supply := float(rates.supply.get(ware_id, 0.0))
		var demand := float(rates.demand.get(ware_id, 0.0))
		if supply <= EPSILON and demand <= EPSILON:
			continue
		var required_import := maxf(0.0, demand - supply)
		if required_import > EPSILON and not imported.has(ware_id):
			var message := "No available local recipe covers %s; it must be imported." % str(ware.name)
			if not warnings.has(message) and errors.is_empty():
				warnings.append(message)
		ware_rows.append({"id":ware_id, "name":str(ware.name), "supply":supply, "demand":demand, "imports":required_import, "surplus":maxf(0.0, supply - demand)})
	return {"ok":errors.is_empty(), "modules":module_rows, "wares":ware_rows, "errors":errors, "warnings":warnings}


func _rates(recipes: Dictionary, counts: Dictionary) -> Dictionary:
	var supply: Dictionary = {}
	var demand: Dictionary = {}
	for id in counts:
		var count := int(counts[id])
		if count <= 0:
			continue
		var recipe: Dictionary = recipes[id]
		var cycles := 60.0 * count / float(recipe.cycle_ticks)
		for ware_id in recipe.inputs:
			demand[ware_id] = float(demand.get(ware_id, 0.0)) + cycles * float(recipe.inputs[ware_id])
		for ware_id in recipe.outputs:
			supply[ware_id] = float(supply.get(ware_id, 0.0)) + cycles * float(recipe.outputs[ware_id])
	return {"supply":supply, "demand":demand}


func _check_cycle(ware_id: String, producers: Dictionary, imported: Dictionary, visiting: Dictionary, visited: Dictionary, errors: Array[String], wares: Dictionary) -> void:
	if imported.has(ware_id) or visited.has(ware_id) or not producers.has(ware_id):
		return
	if visiting.has(ware_id):
		var message := "Cyclic dependency involving %s. Select an input to import." % str(wares.get(ware_id, ware_id))
		if not errors.has(message):
			errors.append(message)
		return
	visiting[ware_id] = true
	var recipe: Dictionary = producers[ware_id]
	for input_id in recipe.inputs:
		_check_cycle(str(input_id), producers, imported, visiting, visited, errors, wares)
	visiting.erase(ware_id)
	visited[ware_id] = true
