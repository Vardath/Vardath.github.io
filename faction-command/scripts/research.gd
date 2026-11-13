extends RefCounted
## Player research consumes physical laboratory output. Relevant archives
## visited by the player contribute once each, with a fixed diversity cap.

const DATA_PATH := "res://data/research.json"
const BASE_PROGRESS := 2
const MAX_ARCHIVE_BONUS := 2

var projects: Dictionary = {}
var project_order: Array = []
var ware_definition: Dictionary = {}
var recipe_definition: Dictionary = {}
var blueprint_definition: Dictionary = {}


func _load_definitions() -> Error:
	if not projects.is_empty():
		return OK
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not data is Dictionary or data.get("schema_version") != 1 or not data.get("ware") is Dictionary or not data.get("recipe") is Dictionary or not data.get("blueprint") is Dictionary or not data.get("projects") is Array or data.projects.is_empty():
		return ERR_INVALID_DATA
	if data.ware.get("id") != "research_notes" or not data.ware.get("name") is String or int(data.ware.get("volume", 0)) < 1:
		return ERR_INVALID_DATA
	if data.recipe.get("id") != "research_laboratory" or not data.recipe.get("name") is String or int(data.recipe.get("cycle_ticks", 0)) < 1 or not data.recipe.get("inputs") is Dictionary or not data.recipe.get("outputs") is Dictionary or int(data.recipe.outputs.get("research_notes", 0)) < 1:
		return ERR_INVALID_DATA
	if int(data.blueprint.get("fee", 0)) < 1 or int(data.blueprint.get("ticks", 0)) < 1 or int(data.blueprint.get("storage", 0)) < 1 or not data.blueprint.get("materials") is Dictionary or data.blueprint.materials.is_empty():
		return ERR_INVALID_DATA
	var loaded: Dictionary = {}
	var order: Array = []
	for project in data.projects:
		if not project is Dictionary:
			return ERR_INVALID_DATA
		for key in ["id", "name", "description", "reward"]:
			if not project.get(key) is String or str(project[key]).is_empty():
				return ERR_INVALID_DATA
		if loaded.has(project.id) or not project.get("topics") is Array or project.topics.is_empty() or int(project.get("target", 0)) < 1 or not project.get("effect") is Dictionary or not project.effect.get("recipe_id") is String or int(project.effect.get("cycle_ticks", 0)) < 1:
			return ERR_INVALID_DATA
		for topic in project.topics:
			if not topic is String or str(topic).is_empty():
				return ERR_INVALID_DATA
		loaded[project.id] = project.duplicate(true)
		order.append(project.id)
	ware_definition = data.ware.duplicate(true)
	recipe_definition = data.recipe.duplicate(true)
	blueprint_definition = data.blueprint.duplicate(true)
	projects = loaded
	project_order = order
	return OK


func prepare(target: Dictionary) -> Error:
	var loaded := _load_definitions()
	if loaded != OK:
		return loaded
	if target.has("research_version"):
		return OK if target.research_version == 1 else ERR_UNAVAILABLE
	for ware in target.wares:
		if ware.id == ware_definition.id:
			return ERR_ALREADY_IN_USE
	for recipe in target.recipes:
		if recipe.id == recipe_definition.id:
			return ERR_ALREADY_IN_USE
	if target.construction_blueprints.has(recipe_definition.id):
		return ERR_ALREADY_IN_USE
	# Adding an empty stock slot does not change existing goods or balances.
	target.wares.append(ware_definition.duplicate(true))
	target.recipes.append(recipe_definition.duplicate(true))
	target.construction_blueprints[recipe_definition.id] = blueprint_definition.duplicate(true)
	for station in target.stations:
		station.stock[ware_definition.id] = 0
	target["research"] = {"completed":[], "progress":{}, "active_project_id":"", "lab_station_id":""}
	target["research_version"] = 1
	return OK


func definition(project_id: String) -> Dictionary:
	return projects.get(project_id, {})


func has_lab(station: Dictionary) -> bool:
	for module in station.get("production", []):
		if module.get("recipe_id", "") == "research_laboratory":
			return true
	return false


func references(world: RefCounted, project_id: String) -> Array:
	var project := definition(project_id)
	var results: Array = []
	var seen: Dictionary = {}
	if project.is_empty():
		return results
	for archive_id in world.state.get("visited_archives", []):
		if seen.has(archive_id):
			continue
		seen[archive_id] = true
		var archive: Dictionary = world.archives.definition(str(archive_id))
		if archive.is_empty():
			continue
		var matched: Array[String] = []
		for topic in archive.research_subjects:
			if topic in project.topics:
				matched.append(str(topic))
		if not matched.is_empty():
			results.append({"id":archive_id, "name":archive.name, "topics":matched})
	return results


func progress_per_note(world: RefCounted, project_id: String) -> int:
	return BASE_PROGRESS + mini(MAX_ARCHIVE_BONUS, references(world, project_id).size())


func start(world: RefCounted, station_id: String, project_id: String) -> Dictionary:
	var station: Dictionary = world._find_station(station_id)
	var project := definition(project_id)
	if station.is_empty() or station.owner != world.state.player_faction_id or not has_lab(station):
		return {"ok":false, "message":"Choose one of your stations with a completed research laboratory."}
	if project.is_empty():
		return {"ok":false, "message":"Choose a valid research project."}
	if project_id in world.state.research.completed:
		return {"ok":false, "message":"This project is already complete."}
	world.state.research.active_project_id = project_id
	world.state.research.lab_station_id = station_id
	return {"ok":true, "message":"Research assigned. Each note is consumed as work progresses."}


func pause(world: RefCounted) -> bool:
	if str(world.state.research.active_project_id).is_empty():
		return false
	world.state.research.active_project_id = ""
	world.state.research.lab_station_id = ""
	return true


func adjusted_recipe(state: Dictionary, recipe: Dictionary, player_station: bool) -> Dictionary:
	if not player_station or not state.has("research") or state.research.get("completed", []).is_empty():
		return recipe
	if _load_definitions() != OK:
		return recipe
	var adjusted := recipe.duplicate(true)
	for project_id in state.research.completed:
		var project := definition(str(project_id))
		if not project.is_empty() and project.effect.recipe_id == recipe.id:
			adjusted.cycle_ticks = mini(int(adjusted.cycle_ticks), int(project.effect.cycle_ticks))
	return adjusted


func _settle_upgraded_cycles(world: RefCounted, project: Dictionary) -> void:
	for station in world.state.stations:
		if station.owner != world.state.player_faction_id:
			continue
		for module in station.production:
			if module.recipe_id != project.effect.recipe_id:
				continue
			var base: Dictionary = world._find_recipe(str(module.recipe_id))
			if not base.is_empty():
				var duration := int(adjusted_recipe(world.state, base, true).cycle_ticks)
				module.progress = mini(int(module.progress), duration - 1)


func tick(world: RefCounted) -> void:
	var state: Dictionary = world.state.research
	var project_id := str(state.active_project_id)
	if project_id.is_empty():
		return
	var project := definition(project_id)
	var station: Dictionary = world._find_station(str(state.lab_station_id))
	if project.is_empty() or station.is_empty() or station.owner != world.state.player_faction_id or not has_lab(station) or int(station.stock.get("research_notes", 0)) < 1:
		return
	station.stock.research_notes = int(station.stock.research_notes) - 1
	var amount := progress_per_note(world, project_id)
	state.progress[project_id] = mini(int(project.target), int(state.progress.get(project_id, 0)) + amount)
	if int(state.progress[project_id]) >= int(project.target):
		state.completed.append(project_id)
		state.active_project_id = ""
		state.lab_station_id = ""
		_settle_upgraded_cycles(world, project)
