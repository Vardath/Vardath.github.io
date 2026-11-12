extends SceneTree

const WorldScript = preload("res://scripts/world.gd")
const MainScene = preload("res://scenes/main.tscn")

var failures: Array[String] = []
var checks := 0


func _initialize() -> void:
	call_deferred("_run")


func _expect(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		printerr("FAIL: " + message)


func _run() -> void:
	var first = WorldScript.new()
	var second = WorldScript.new()
	_expect(first.load_starter() == OK, "starter galaxy loads")
	_expect(second.load_starter() == OK, "a second independent galaxy loads")
	if first.state.is_empty() or second.state.is_empty():
		quit(1)
		return

	_expect(first.state.schema_version == 1, "starter schema is versioned")
	_expect(first.state.sectors.size() == 12, "starter contains 12 sectors")
	_expect(first.state.factions.size() == 5, "starter contains player plus four NPC factions")
	_expect(first.state.ships.size() == 1, "player starts with one ship")
	_expect(first.state.starting_credits > 0, "player starts with credits")

	var faction_ids: Dictionary = {}
	for faction in first.state.factions:
		_expect(not faction_ids.has(faction.id), "faction IDs are unique: " + str(faction.id))
		faction_ids[faction.id] = true
	var sector_ids: Dictionary = {}
	var graph: Dictionary = {}
	for sector in first.state.sectors:
		_expect(not sector_ids.has(sector.id), "sector IDs are unique: " + str(sector.id))
		_expect(faction_ids.has(sector.owner), "sector has a valid owner: " + str(sector.id))
		_expect(float(sector.x) >= 0 and float(sector.x) <= 1 and float(sector.y) >= 0 and float(sector.y) <= 1, "sector coordinates fit map: " + str(sector.id))
		sector_ids[sector.id] = true
		graph[sector.id] = []
	var edges: Dictionary = {}
	for link in first.state.links:
		if link.size() != 2 or not graph.has(link[0]) or not graph.has(link[1]):
			_expect(false, "link must connect two valid sectors")
			continue
		_expect(link[0] != link[1], "links do not loop to the same sector")
		var edge: Array = [link[0], link[1]]
		edge.sort()
		var key := "%s|%s" % edge
		_expect(not edges.has(key), "links are unique: " + key)
		edges[key] = true
		graph[link[0]].append(link[1])
		graph[link[1]].append(link[0])
	var visited: Dictionary = {}
	var queue: Array = [first.state.sectors[0].id]
	while not queue.is_empty():
		var current: String = queue.pop_front()
		if visited.has(current):
			continue
		visited[current] = true
		for neighbor in graph[current]:
			if not visited.has(neighbor):
				queue.append(neighbor)
	_expect(visited.size() == sector_ids.size(), "all starter sectors are reachable")
	for ship in first.state.ships:
		_expect(ship.owner == first.state.player_faction_id, "starter ship belongs to player")
		_expect(sector_ids.has(ship.sector), "starter ship is in a valid sector")
		_expect(not str(ship.captain).is_empty() and int(ship.crew) > 0, "starter ship has a captain and crew")

	first.advance_ticks(12)
	first.advance_ticks(25)
	second.advance_ticks(37)
	_expect(first.snapshot() == second.snapshot(), "same world and tick count give identical state regardless of batching")
	first.advance_ticks(-4)
	first.advance_ticks(0)
	_expect(first.state.tick == 37, "zero and negative tick counts do not change time")
	var copy: Dictionary = first.snapshot()
	copy.ships[0].name = "Changed copy"
	_expect(first.state.ships[0].name == "First Light", "snapshots cannot mutate the live world")

	# Godot 4.4's headless display can default to 64x64 regardless of project
	# window settings. Test the actual intended landscape viewport explicitly.
	root.size = Vector2i(1280, 720)
	var screen = MainScene.instantiate()
	root.add_child(screen)
	await process_frame
	# Container layout can require another frame on older Godot versions.
	await process_frame
	_expect(screen.paused, "game starts paused")
	_expect(screen.find_child("GalaxyMap", true, false) != null, "main scene creates the galaxy map")
	_expect(screen.find_child("ShipButton", true, false) != null, "main scene exposes player property")
	_expect(screen.pause_button.size.y <= 65.0, "top bar stays compact at landscape resolution (button: %s, viewport: %s)" % [screen.pause_button.size, root.size])
	_expect(screen.map_view.size.y >= 250.0, "galaxy map has usable height at landscape resolution")
	screen.map_view.sector_selected.emit("vellum_gate")
	_expect(screen.detail_title.text == "Vellum Gate", "map sector selection updates details")
	_expect(screen.detail_body.text.contains("Vesper Guild"), "sector details show the controlling faction")
	screen.find_child("ShipButton", true, false).pressed.emit()
	_expect(screen.detail_title.text == "First Light", "property selection shows the player's ship")
	_expect(screen.detail_body.text.contains("Mira Vale"), "ship details show the captain")
	_expect(screen.detail_body.text.contains("Crew\n2\n"), "crew count displays as a whole number")
	screen.find_child("PauseButton", true, false).pressed.emit()
	_expect(not screen.paused, "resume control unpauses")
	screen.find_child("PauseButton", true, false).pressed.emit()
	_expect(screen.paused, "pause control pauses")
	screen.queue_free()
	await process_frame
	if failures.is_empty():
		print("PASS: %d foundation checks" % checks)
		quit(0)
	else:
		printerr("FAILED: %d of %d foundation checks" % [failures.size(), checks])
		quit(1)
