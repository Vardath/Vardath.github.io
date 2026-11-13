extends Control
## Shared camera and pointer handling. Camera state is presentation only;
## zooming and panning never change the simulation or a saved game.

const MIN_ZOOM := 0.7
const MAX_ZOOM := 3.5
const DRAG_THRESHOLD := 8.0

var zoom_level := 1.0
var pan_offset := Vector2.ZERO
var _mouse_pressed := false
var _mouse_start := Vector2.ZERO
var _mouse_last := Vector2.ZERO
var _mouse_dragged := false
var _touches: Dictionary = {}
var _touch_start := Vector2.ZERO
var _touch_tap := false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	clip_contents = true
	custom_minimum_size = Vector2(420, 340)


func map_to_screen(point: Vector2) -> Vector2:
	return size * 0.5 + (point - size * 0.5) * zoom_level + pan_offset


func screen_to_map(point: Vector2) -> Vector2:
	return size * 0.5 + (point - size * 0.5 - pan_offset) / zoom_level


func zoom_by(factor: float, anchor: Vector2 = Vector2(-1, -1)) -> void:
	if not is_finite(factor) or factor <= 0.0:
		return
	if anchor == Vector2(-1, -1):
		anchor = size * 0.5
	var before := screen_to_map(anchor)
	zoom_level = clampf(zoom_level * factor, MIN_ZOOM, MAX_ZOOM)
	pan_offset = anchor - size * 0.5 - (before - size * 0.5) * zoom_level
	_limit_pan()
	queue_redraw()


func pan_by(delta: Vector2) -> void:
	pan_offset += delta
	_limit_pan()
	queue_redraw()


func fit_map() -> void:
	zoom_level = 1.0
	pan_offset = Vector2.ZERO
	queue_redraw()


func _limit_pan() -> void:
	# Keep the map recoverable even after a long drag or pinch.
	var limit := size * maxf(0.35, zoom_level * 0.65)
	pan_offset.x = clampf(pan_offset.x, -limit.x, limit.x)
	pan_offset.y = clampf(pan_offset.y, -limit.y, limit.y)


func _activate_at(_point: Vector2) -> void:
	# Implemented by the galaxy and sector views.
	pass


func _gui_input(event: InputEvent) -> void:
	# Godot can also synthesize mouse events for touch. Handle real screen
	# events ourselves so a tap or drag cannot be applied twice.
	if event is InputEventMouse and event.device == InputEvent.DEVICE_ID_EMULATION:
		return
	if event is InputEventScreenTouch:
		if event.pressed:
			_touches[event.index] = event.position
			if _touches.size() == 1:
				_touch_start = event.position
				_touch_tap = true
			else:
				_touch_tap = false
		else:
			if _touches.has(event.index) and _touches.size() == 1 and _touch_tap and not event.is_canceled():
				_activate_at(event.position)
			_touches.erase(event.index)
			_touch_tap = false
		accept_event()
		return
	if event is InputEventScreenDrag and _touches.has(event.index):
		var previous: Vector2 = _touches[event.index]
		var old_center := Vector2.ZERO
		var old_distance := 0.0
		var keys: Array = _touches.keys()
		if keys.size() == 2:
			var first: Vector2 = _touches[keys[0]]
			var second: Vector2 = _touches[keys[1]]
			old_center = (first + second) * 0.5
			old_distance = first.distance_to(second)
		_touches[event.index] = event.position
		if keys.size() == 1:
			if event.position.distance_to(_touch_start) > DRAG_THRESHOLD:
				_touch_tap = false
			if not _touch_tap:
				pan_by(event.position - previous)
		elif keys.size() == 2:
			_touch_tap = false
			var first: Vector2 = _touches[keys[0]]
			var second: Vector2 = _touches[keys[1]]
			var center := (first + second) * 0.5
			var distance := first.distance_to(second)
			if old_distance > 1.0:
				zoom_by(distance / old_distance, old_center)
			pan_by(center - old_center)
		accept_event()
		return
	if event is InputEventMagnifyGesture:
		zoom_by(event.factor, event.position)
		accept_event()
		return
	if event is InputEventMouseButton:
		if event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			zoom_by(1.2 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.2, event.position)
			accept_event()
			return
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				_mouse_pressed = true
				_mouse_start = event.position
				_mouse_last = event.position
				_mouse_dragged = false
			elif _mouse_pressed:
				_mouse_pressed = false
				if not _mouse_dragged and not event.is_canceled():
					_activate_at(event.position)
			accept_event()
			return
	if event is InputEventMouseMotion and _mouse_pressed:
		if event.position.distance_to(_mouse_start) > DRAG_THRESHOLD:
			_mouse_dragged = true
		if _mouse_dragged:
			pan_by(event.position - _mouse_last)
		_mouse_last = event.position
		accept_event()
