extends Control

const WorldScript = preload("res://scripts/world.gd")
const GalaxyMapScript = preload("res://scripts/galaxy_map.gd")
const BACKGROUND := Color("080f1b")
const PANEL := Color("101e2d")
const BORDER := Color("24394a")
const TEXT := Color("e2f0f0")
const MUTED := Color("8ca4b3")
const ACCENT := Color("71dfcc")

var world = WorldScript.new()
var paused := true
var _elapsed := 0.0
var map_view
var credits_label: Label
var tick_label: Label
var pause_button: Button
var detail_title: Label
var detail_body: Label
var sector_picker: OptionButton


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if world.load_starter() != OK:
		push_error("Unable to load starter galaxy")
		return
	_build_ui()
	_show_sector("hearthreach")
	_update_header()


func _process(delta: float) -> void:
	if paused or world.state.is_empty():
		return
	_elapsed += delta
	var whole_ticks := int(_elapsed)
	if whole_ticks > 0:
		world.advance_ticks(whole_ticks)
		_elapsed -= whole_ticks
		_update_header()


func _style(bg: Color, border: Color = BORDER, radius: int = 8) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(radius)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	return style


func _label(value: String, font_size: int, color: Color = TEXT) -> Label:
	var result := Label.new()
	result.text = value
	result.add_theme_font_size_override("font_size", font_size)
	result.add_theme_color_override("font_color", color)
	return result


func _wrapped_label(value: String, font_size: int, color: Color = TEXT) -> Label:
	var result := _label(value, font_size, color)
	result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return result


func _button(value: String) -> Button:
	var result := Button.new()
	result.text = value
	result.custom_minimum_size.y = 46
	result.add_theme_font_size_override("font_size", 16)
	result.add_theme_color_override("font_color", TEXT)
	result.add_theme_stylebox_override("normal", _style(Color("182d3b")))
	result.add_theme_stylebox_override("hover", _style(Color("254454"), ACCENT))
	result.add_theme_stylebox_override("pressed", _style(Color("1a504b"), ACCENT))
	return result


func _panel() -> PanelContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _style(PANEL))
	return panel


func _build_ui() -> void:
	var background := ColorRect.new()
	background.color = BACKGROUND
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for edge in ["margin_left", "margin_right", "margin_top", "margin_bottom"]:
		margin.add_theme_constant_override(edge, 16)
	add_child(margin)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 12)
	margin.add_child(root)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 18)
	root.add_child(header)
	var brand := VBoxContainer.new()
	brand.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(brand)
	brand.add_child(_label("FACTION COMMAND", 23, TEXT))
	brand.add_child(_label("STRATEGIC OPERATIONS  /  FOUNDATION", 11, ACCENT))
	credits_label = _label("", 17, TEXT)
	credits_label.name = "Credits"
	header.add_child(credits_label)
	tick_label = _label("", 17, MUTED)
	tick_label.name = "Tick"
	header.add_child(tick_label)
	pause_button = _button("Resume")
	pause_button.name = "PauseButton"
	pause_button.custom_minimum_size.x = 100
	pause_button.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pause_button.pressed.connect(_toggle_pause)
	header.add_child(pause_button)

	var content := HBoxContainer.new()
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 12)
	root.add_child(content)

	var property_panel := _panel()
	property_panel.custom_minimum_size.x = 210
	content.add_child(property_panel)
	var property_list := VBoxContainer.new()
	property_list.add_theme_constant_override("separation", 12)
	property_panel.add_child(property_list)
	property_list.add_child(_label("YOUR PROPERTY", 14, ACCENT))
	property_list.add_child(_label("1 SHIP", 12, MUTED))
	var ship_button := _button("◈   First Light")
	ship_button.name = "ShipButton"
	ship_button.pressed.connect(_show_ship)
	property_list.add_child(ship_button)
	property_list.add_child(_label("Courier  ·  Idle\nHearthreach", 13, MUTED))
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	property_list.add_child(spacer)
	property_list.add_child(_label("YOUR FACTION", 12, ACCENT))
	property_list.add_child(_wrapped_label("A small beginning. A whole galaxy ahead.", 13, MUTED))

	var map_panel := _panel()
	map_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(map_panel)
	var map_column := VBoxContainer.new()
	map_column.add_theme_constant_override("separation", 8)
	map_panel.add_child(map_column)
	var map_heading := HBoxContainer.new()
	map_column.add_child(map_heading)
	var title := _label("GALAXY MAP", 16, TEXT)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_heading.add_child(title)
	map_heading.add_child(_label("12 SECTORS   /   4 FACTIONS", 12, MUTED))
	map_view = GalaxyMapScript.new()
	map_view.name = "GalaxyMap"
	map_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map_view.set_world(world.snapshot())
	map_view.sector_selected.connect(_show_sector)
	map_column.add_child(map_view)
	map_column.add_child(_label("Select a sector on the map or use the sector list.", 12, MUTED))

	var detail_panel := _panel()
	detail_panel.custom_minimum_size.x = 230
	content.add_child(detail_panel)
	var detail := VBoxContainer.new()
	detail.add_theme_constant_override("separation", 12)
	detail_panel.add_child(detail)
	detail.add_child(_label("SECTOR DIRECTORY", 13, ACCENT))
	sector_picker = OptionButton.new()
	sector_picker.name = "SectorPicker"
	sector_picker.custom_minimum_size.y = 44
	sector_picker.add_theme_font_size_override("font_size", 15)
	for sector in world.state.sectors:
		sector_picker.add_item(str(sector.name))
		sector_picker.set_item_metadata(sector_picker.item_count - 1, sector.id)
	sector_picker.item_selected.connect(_on_sector_picked)
	detail.add_child(sector_picker)
	detail_title = _label("", 21, TEXT)
	detail_title.name = "DetailTitle"
	detail.add_child(detail_title)
	detail_body = _wrapped_label("", 15, MUTED)
	detail_body.name = "DetailBody"
	detail_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail.add_child(detail_body)
	detail.add_child(_label("FOUNDATION BUILD", 12, ACCENT))
	detail.add_child(_wrapped_label("Travel, trading and orders are being built in future passes.", 13, MUTED))

	root.add_child(_label("OFFLINE  ·  PAUSED AT START  ·  ORIGINAL STARTER GALAXY", 11, MUTED))


func _toggle_pause() -> void:
	paused = not paused
	_update_header()


func _update_header() -> void:
	credits_label.text = "%s CR" % str(int(world.state.starting_credits))
	tick_label.text = "TICK %s" % str(int(world.state.tick))
	pause_button.text = "Resume" if paused else "Pause"


func _on_sector_picked(index: int) -> void:
	_show_sector(str(sector_picker.get_item_metadata(index)))


func _show_sector(sector_id: String) -> void:
	for sector in world.state.sectors:
		if sector.id == sector_id:
			var faction_name := "Independent"
			for faction in world.state.factions:
				if faction.id == sector.owner:
					faction_name = faction.name
			map_view.select_sector(sector_id)
			for index in sector_picker.item_count:
				if sector_picker.get_item_metadata(index) == sector_id:
					sector_picker.select(index)
			detail_title.text = sector.name
			detail_body.text = "Controlled by\n%s\n\n%s" % [faction_name, sector.description]
			return


func _show_ship() -> void:
	var ship: Dictionary = world.state.ships[0]
	var sector_name := str(ship.sector)
	for sector in world.state.sectors:
		if sector.id == ship.sector:
			sector_name = str(sector.name)
			break
	detail_title.text = ship.name
	detail_body.text = "%s  ·  %s\n\nCaptain\n%s\n\nCrew\n%s\n\nRole\n%s\n\nLocation\n%s" % [ship["class"], ship.status, ship.captain, int(ship.crew), ship.role, sector_name]
