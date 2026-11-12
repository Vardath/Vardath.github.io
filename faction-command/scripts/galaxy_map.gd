extends Control

signal sector_selected(sector_id: String)

const INK := Color("0a1423")
const MUTED := Color("71879c")
const LINE := Color("36546a")
const HIGHLIGHT := Color("d1f4ec")

var world: Dictionary = {}
var selected_id := "hearthreach"
var _points: Dictionary = {}


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	custom_minimum_size = Vector2(420, 340)


func set_world(value: Dictionary) -> void:
	world = value
	queue_redraw()


func select_sector(sector_id: String) -> void:
	selected_id = sector_id
	queue_redraw()


func _sector_position(sector: Dictionary) -> Vector2:
	var margin := Vector2(60, 50)
	var area := Vector2(maxf(1.0, size.x - margin.x * 2.0), maxf(1.0, size.y - margin.y * 2.0))
	return margin + Vector2(float(sector.x) * area.x, float(sector.y) * area.y)


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
	for sector in world.get("sectors", []):
		var pos: Vector2 = _points[sector.id]
		var color: Color = faction_colors.get(sector.owner, MUTED)
		draw_circle(pos, 17.0 if sector.id == selected_id else 12.0, Color(color, 0.13))
		draw_arc(pos, 13.0 if sector.id == selected_id else 9.0, 0.0, TAU, 32, color, 2.0, true)
		draw_circle(pos, 4.0, color)
		var label_color := HIGHLIGHT if sector.id == selected_id else Color("a9becb")
		draw_string(font, pos + Vector2(15, 5), str(sector.name), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, label_color)
	for ship in world.get("ships", []):
		if _points.has(ship.sector):
			var pos: Vector2 = _points[ship.sector] + Vector2(-15, -17)
			draw_colored_polygon(PackedVector2Array([pos + Vector2(0, -6), pos + Vector2(6, 5), pos + Vector2(-6, 5)]), Color("70e4cf"))


func _gui_input(event: InputEvent) -> void:
	var point := Vector2.ZERO
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		point = event.position
	elif event is InputEventScreenTouch and event.pressed:
		point = event.position
	else:
		return
	var nearest := ""
	var distance := 30.0
	for id in _points:
		var candidate: float = point.distance_to(_points[id])
		if candidate < distance:
			distance = candidate
			nearest = str(id)
	if not nearest.is_empty():
		sector_selected.emit(nearest)
		accept_event()
