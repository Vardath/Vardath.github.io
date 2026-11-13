extends "res://scripts/map_interaction.gd"

signal sector_selected(sector_id: String)

const INK := Color("0a1423")
const MUTED := Color("71879c")
const LINE := Color("36546a")
const HIGHLIGHT := Color("d1f4ec")

var world: Dictionary = {}
var selected_id := "hearthreach"
var _points: Dictionary = {}
var _label_cache: Dictionary = {}
var _label_camera: Array = []
var _label_sectors: Array = []


func set_world(value: Dictionary) -> void:
	world = value
	queue_redraw()


func select_sector(sector_id: String) -> void:
	selected_id = sector_id
	queue_redraw()


func _sector_position(sector: Dictionary) -> Vector2:
	# Leave room for the longest sector names on the right at the fitted zoom.
	var left := 48.0
	var right := minf(150.0, size.x * 0.23)
	var area := Vector2(maxf(1.0, size.x - left - right), maxf(1.0, size.y - 100.0))
	return map_to_screen(Vector2(left, 50.0) + Vector2(float(sector.x) * area.x, float(sector.y) * area.y))


func _label_layout() -> Dictionary:
	var font := ThemeDB.fallback_font
	var sectors: Array = world.get("sectors", [])
	var camera := [size, zoom_level, pan_offset]
	if camera == _label_camera and sectors == _label_sectors:
		return _label_cache
	var labels: Dictionary = {}
	var occupied: Array[Rect2] = []
	for sector in sectors:
		var pos := _sector_position(sector)
		var text_size := font.get_string_size(str(sector.name), HORIZONTAL_ALIGNMENT_LEFT, -1, 14)
		var candidates: Array[Rect2] = [
			Rect2(pos + Vector2(15, -text_size.y / 2.0), text_size),
			Rect2(pos + Vector2(-text_size.x / 2.0, 16), text_size),
			Rect2(pos + Vector2(-text_size.x / 2.0, -16 - text_size.y), text_size),
			Rect2(pos + Vector2(-15 - text_size.x, -text_size.y / 2.0), text_size)
		]
		var best: Rect2 = candidates[0]
		var best_score := INF
		for candidate in candidates:
			var score := 0.0
			score += maxf(0.0, -candidate.position.x) + maxf(0.0, -candidate.position.y)
			score += maxf(0.0, candidate.end.x - size.x) + maxf(0.0, candidate.end.y - size.y)
			score *= 10.0
			for other in sectors:
				if other.id == sector.id:
					continue
				var marker := Rect2(_sector_position(other) - Vector2(13, 13), Vector2(26, 26))
				if candidate.intersects(marker):
					score += 1000.0 + candidate.intersection(marker).get_area()
			for previous in occupied:
				if candidate.intersects(previous):
					score += 1000.0 + candidate.intersection(previous).get_area()
			if score < best_score:
				best_score = score
				best = candidate
		labels[sector.id] = best
		occupied.append(best)
	_label_cache = labels
	_label_camera = camera
	_label_sectors = sectors.duplicate(true)
	return labels


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), INK)
	# Fixed decorative points make the backdrop reproducible and inexpensive.
	for i in range(85):
		var x := fmod(float(i * 83 + 29), maxf(1.0, size.x))
		var y := fmod(float(i * 137 + 51), maxf(1.0, size.y))
		draw_circle(Vector2(x, y), 1.0 if i % 7 else 1.6, Color(0.38, 0.52, 0.62, 0.28))
	if world.is_empty():
		return
	_points.clear()
	var faction_colors: Dictionary = {}
	for faction in world.get("factions", []):
		faction_colors[faction.id] = Color.html(faction.color)
	for sector in world.get("sectors", []):
		_points[sector.id] = _sector_position(sector)
	for link in world.get("links", []):
		if link.size() == 2 and _points.has(link[0]) and _points.has(link[1]):
			draw_line(_points[link[0]], _points[link[1]], LINE, 2.0, true)
	var font := ThemeDB.fallback_font
	var labels := _label_layout()
	for sector in world.get("sectors", []):
		var pos: Vector2 = _points[sector.id]
		var color: Color = faction_colors.get(sector.owner, MUTED)
		draw_circle(pos, 17.0 if sector.id == selected_id else 12.0, Color(color, 0.13))
		draw_arc(pos, 13.0 if sector.id == selected_id else 9.0, 0.0, TAU, 32, color, 2.0, true)
		draw_circle(pos, 4.0, color)
		var label_color := HIGHLIGHT if sector.id == selected_id else Color("a9becb")
		var label_rect: Rect2 = labels[sector.id]
		draw_string(font, label_rect.position + Vector2(0, font.get_ascent(14)), str(sector.name), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, label_color)
	for ship in world.get("ships", []):
		if _points.has(ship.sector):
			var pos: Vector2 = _points[ship.sector]
			var travel: Dictionary = ship.get("travel", {})
			if not travel.is_empty() and _points.has(travel.get("to", "")):
				var progress := 1.0 - float(travel.remaining) / float(travel.total)
				pos = pos.lerp(_points[travel.to], progress)
			if ship.owner == world.get("player_faction_id", ""):
				pos += Vector2(-15, -17)
				draw_colored_polygon(PackedVector2Array([pos + Vector2(0, -6), pos + Vector2(6, 5), pos + Vector2(-6, 5)]), Color("70e4cf"))
			else:
				pos += Vector2(15, -17)
				var ship_color: Color = faction_colors.get(ship.owner, MUTED)
				draw_colored_polygon(PackedVector2Array([pos + Vector2(0, -6), pos + Vector2(6, 0), pos + Vector2(0, 6), pos + Vector2(-6, 0)]), ship_color)


func _activate_at(point: Vector2) -> void:
	var nearest := ""
	var distance := 30.0
	for sector in world.get("sectors", []):
		var candidate: float = point.distance_to(_sector_position(sector))
		if candidate < distance:
			distance = candidate
			nearest = str(sector.id)
	if not nearest.is_empty():
		sector_selected.emit(nearest)
