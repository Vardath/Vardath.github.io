extends RefCounted
## Small, presentation-independent world state. Time advances only through
## explicit whole ticks; no wall clock or frame rate enters the simulation.

const STARTER_DATA := "res://data/starter_galaxy.json"

var state: Dictionary = {}


func load_starter() -> Error:
	if not FileAccess.file_exists(STARTER_DATA):
		return ERR_FILE_NOT_FOUND
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(STARTER_DATA))
	if not parsed is Dictionary or parsed.get("schema_version", 0) != 1:
		return ERR_PARSE_ERROR
	state = parsed.duplicate(true)
	state["tick"] = 0
	return OK


func advance_ticks(count: int) -> void:
	if count <= 0 or state.is_empty():
		return
	state["tick"] = int(state["tick"]) + count


func snapshot() -> Dictionary:
	return state.duplicate(true)
