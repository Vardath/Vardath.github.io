extends "res://scripts/map_interaction.gd"
## Sector contents are arranged as a schematic because the simulation does
## not yet track positions inside a sector. All listed objects are real.

signal sector_selected(sector_id: String)
signal station_selected(station_id: String)
signal ship_selected(ship_id: String)

const INK := Color("0a1423")
const ACCENT := Color("71dfcc")
const TEXT := Color("d8ebee")
const MUTED := Color("91aab8")
const EDGE := Color("355367")

var world: Dictionary = {}
var selected_id := ""


func set_world(value: Dictionary) -> void:
	world = value
	queue_redraw()


func select_sector(sector_id: String) -> void:
	if selected_id != sector_id:
		selected_id = sector_id
		fit_map()
	queue_redraw()


func _sector_name(sector_id: String) -> String:
	for sector in world.get("sectors", []):
		if sector.id == sector_id:
			return str(sector.name)
	return sector_id


func _items() -> Array[Dictionary]:
	var items: Array[Dictionary] = []
	if world.is_empty() or selected_id.is_empty():
		return items
	var margin := 18.0
	var gap := 12.0
	var column_width := maxf(90.0, (size.x - margin * 2.0 - gap * 2.0) / 3.0)
	var counts := [0, 0, 0]
	for link in world.get("links", []):
		if link.size() != 2 or selected_id not in link:
			continue
		var other: String = str(link[1]) if link[0] == selected_id else str(link[0])
		items.append(_item(0, counts[0], column_width, margin, gap, "sector", other, _sector_name(other), "Open sector"))
		counts[0] += 1
	for station in world.get("stations", []):
		if station.sector != selected_id:
			continue
		var status := "No production"
		if station.has("archive"):
			status = "Archive · " + str(station.archive.status)
		elif not station.get("production", []).is_empty():
			status = str(station.production[0].status)
		items.append(_item(1, counts[1], column_width, margin, gap, "station", str(station.id), str(station.name), status))
		counts[1] += 1
	for ship in world.get("ships", []):
		if ship.sector != selected_id:
			continue
		var status := str(ship.status)
		if not ship.get("travel", {}).is_empty():
			status = "Crossing to " + _sector_name(str(ship.travel.to))
		elif ship.owner == world.get("player_faction_id", ""):
			status = "Your ship · " + status
		items.append(_item(2, counts[2], column_width, margin, gap, "ship", str(ship.id), str(ship.name), status))
		counts[2] += 1
	return items


func _item(column: int, row: int, width: float, margin: float, gap: float, kind: String, id: String, title: String, subtitle: String) -> Dictionary:
	var base := Vector2(margin + column * (width + gap), 82.0 + row * 64.0)
	return {"kind":kind, "id":id, "title":title, "subtitle":subtitle, "rect":Rect2(map_to_screen(base), Vector2(width, 55.0) * zoom_level)}


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), INK)
	if world.is_empty() or selected_id.is_empty():
		return
	var font := ThemeDB.fallback_font
	var title_size := clampi(int(14.0 * zoom_level), 10, 20)
	var small_size := clampi(int(12.0 * zoom_level), 9, 17)
	var margin := 18.0
	var gap := 12.0
	var width := maxf(90.0, (size.x - margin * 2.0 - gap * 2.0) / 3.0)
	draw_string(font, map_to_screen(Vector2(margin, 25)), "SECTOR OVERVIEW", HORIZONTAL_ALIGNMENT_LEFT, -1, title_size, ACCENT)
	draw_string(font, map_to_screen(Vector2(margin, 45)), "Schematic layout · positions within a sector are not simulated yet", HORIZONTAL_ALIGNMENT_LEFT, -1, small_size, MUTED)
	for column in range(3):
		var heading: String = ["CONNECTIONS", "STATIONS", "SHIPS"][column]
		var base := Vector2(margin + column * (width + gap), 72.0)
		draw_string(font, map_to_screen(base), heading, HORIZONTAL_ALIGNMENT_LEFT, -1, small_size, ACCENT)
	var viewport := Rect2(Vector2.ZERO, size)
	var counts := {"sector":0, "station":0, "ship":0}
	for item in _items():
		counts[item.kind] += 1
		var rect: Rect2 = item.rect
		if not viewport.intersects(rect):
			continue
		draw_rect(rect, Color("152a39"))
		draw_rect(rect, EDGE, false, 1.0)
		var inset := 9.0 * zoom_level
		draw_string(font, rect.position + Vector2(inset, 21.0 * zoom_level), str(item.title), HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - inset * 2.0, title_size, TEXT)
		draw_string(font, rect.position + Vector2(inset, 41.0 * zoom_level), str(item.subtitle), HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - inset * 2.0, small_size, MUTED)
	var kinds := ["sector", "station", "ship"]
	for column in range(3):
		if counts[kinds[column]] == 0:
			var base := Vector2(margin + column * (width + gap), 106.0)
			draw_string(font, map_to_screen(base), "None here", HORIZONTAL_ALIGNMENT_LEFT, -1, small_size, MUTED)


func _activate_at(point: Vector2) -> void:
	for item in _items():
		if item.rect.has_point(point):
			match item.kind:
				"sector": sector_selected.emit(str(item.id))
				"station": station_selected.emit(str(item.id))
				"ship": ship_selected.emit(str(item.id))
			return
