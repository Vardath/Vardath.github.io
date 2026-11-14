extends Control

const WorldScript = preload("res://scripts/world.gd")
const GalaxyMapScript = preload("res://scripts/galaxy_map.gd")
const SectorMapScript = preload("res://scripts/sector_map.gd")
const SaveStoreScript = preload("res://scripts/save_store.gd")
const StationPlannerScript = preload("res://scripts/station_planner.gd")
const BACKGROUND := Color("080f1b")
const PANEL := Color("101e2d")
const BORDER := Color("24394a")
const TEXT := Color("e2f0f0")
const MUTED := Color("8ca4b3")
const ACCENT := Color("71dfcc")

var world = WorldScript.new()
var save_store = SaveStoreScript.new()
var station_planner = StationPlannerScript.new()
var save_path := "user://faction_command_save.json"
var _last_saved_tick := 0
var paused := true
var _elapsed := 0.0
var map_view
var sector_map
var showing_sector_map := false
var map_title: Label
var map_caption: Label
var map_mode_button: Button
var credits_label: Label
var tick_label: Label
var pause_button: Button
var detail_title: Label
var detail_body: Label
var sector_picker: OptionButton
var ship_brief: Label
var ship_button: Button
var property_count_label: Label
var property_filter: LineEdit
var property_picker: OptionButton
var property_action_button: Button
var property_picker_signature := ""
var selected_property_key := ""
var active_player_ship_id := ""
var role_picker: OptionButton
var role_hint: Label
var order_target: Label
var order_feedback: Label
var selected_sector := "hearthreach"
var selected_view := "sector"
var selected_ship_id := ""
var chosen_origin := "auroran"
var start_screen: Control
var start_buttons: Dictionary = {}
var origin_title: Label
var origin_summary: Label
var game_started := false
var save_status: Label
var save_notice: Label
var overwrite_confirmation: ConfirmationDialog
var trade_screen: Control
var trade_station_picker: OptionButton
var trade_ware_picker: OptionButton
var trade_quantity: SpinBox
var trade_info: Label
var trade_production: Label
var trade_ledger: Label
var trade_feedback: Label
var trade_buy_button: Button
var trade_sell_button: Button
var trade_archive_button: Button
var trade_production_heading: Label
var archive_screen: Control
var trade_research_button: Button
var research_screen: Control
var research_picker: OptionButton
var research_info: Label
var research_feedback: Label
var research_start_button: Button
var research_pause_button: Button
var trade_station_actions: HBoxContainer
var trade_station_supply_button: Button
var station_supply_screen: Control
var station_supply_budget: SpinBox
var station_supply_info: Label
var station_supply_feedback: Label
var station_supply_stop_button: Button
var plan_screen: Control
var plan_mode: OptionButton
var plan_module_counts: Dictionary = {}
var plan_import_options: Dictionary = {}
var plan_import_list: VBoxContainer
var plan_result: Label
var plan_build_button: Button
var plan_feedback: Label
var build_screen: Control
var build_picker: OptionButton
var build_info: Label
var build_feedback: Label
var build_pause_button: Button
var build_dock_button: Button
var build_deliver_button: Button
var build_supply_button: Button
var build_cancel_button: Button
var build_recover_button: Button
var build_cancel_confirm: ConfirmationDialog
var build_cancel_site_id := ""
var build_task_picker: OptionButton
var build_move_up_button: Button
var build_move_down_button: Button
var build_task_list_signature := ""
var build_task_picker_site_id := ""
var shipyard_screen: Control
var shipyard_hull_picker: OptionButton
var shipyard_info: Label
var shipyard_feedback: Label
var shipyard_buy_button: Button
var shipyard_confirm: ConfirmationDialog
var crew_screen: Control
var crew_screen_ship_id := ""
var crew_info: Label
var crew_feedback: Label
var crew_rename_input: LineEdit
var crew_quantity: SpinBox
var crew_transfer_picker: OptionButton
var crew_captain_swap_button: Button


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if world.load_starter() != OK:
		push_error("Unable to load starter galaxy")
		return
	_build_new_game_screen()


func _process(delta: float) -> void:
	if paused or world.state.is_empty():
		return
	_elapsed += delta
	var whole_ticks := int(_elapsed)
	if whole_ticks > 0:
		world.advance_ticks(whole_ticks)
		_elapsed -= whole_ticks
		_update_header()
		_refresh_world_display()
		if is_instance_valid(trade_screen):
			_update_trade_screen()
		if is_instance_valid(build_screen):
			_update_build_screen()
		if is_instance_valid(research_screen):
			_update_research_screen()
		if is_instance_valid(station_supply_screen):
			_update_station_supply_screen()
		if is_instance_valid(shipyard_screen):
			_update_shipyard_screen()
		if is_instance_valid(crew_screen):
			_update_crew_screen()
		if save_status.text != "Save failed":
			save_status.text = "Unsaved"
		if int(world.state.tick) - _last_saved_tick >= 30:
			_save_current_game()


func _notification(what: int) -> void:
	if (what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST) and game_started:
		paused = true
		if is_instance_valid(pause_button):
			_update_header()
		_save_current_game()


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


func _build_new_game_screen() -> void:
	start_screen = Control.new()
	start_screen.name = "NewGameScreen"
	start_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(start_screen)
	var background := ColorRect.new()
	background.color = BACKGROUND
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	start_screen.add_child(background)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	start_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(900, 550)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	panel.add_child(column)
	column.add_child(_label("FACTION COMMAND", 25, TEXT))
	column.add_child(_label("NEW GAME  /  CHOOSE YOUR ORIGIN", 13, ACCENT))
	column.add_child(_wrapped_label("Your origin sets your starting sector and relations. Your faction and property remain your own.", 15, MUTED))
	var content := HBoxContainer.new()
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 22)
	column.add_child(content)
	var choices := VBoxContainer.new()
	choices.custom_minimum_size.x = 335
	choices.add_theme_constant_override("separation", 8)
	content.add_child(choices)
	choices.add_child(_label("STARTING FACTION", 12, ACCENT))
	for profile in world.state.starting_profiles:
		var faction_id: String = profile.faction_id
		var button := _button("%s\n%s" % [_faction_name(faction_id), _sector_name(str(profile.sector_id))])
		button.name = "Origin_" + faction_id
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.custom_minimum_size.y = 62
		button.pressed.connect(_select_origin.bind(faction_id))
		choices.add_child(button)
		start_buttons[faction_id] = button
	var info := VBoxContainer.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.add_theme_constant_override("separation", 10)
	content.add_child(info)
	info.add_child(_label("ORIGIN PREVIEW", 12, ACCENT))
	origin_title = _label("", 22, TEXT)
	origin_title.name = "OriginTitle"
	info.add_child(origin_title)
	origin_summary = _wrapped_label("", 15, MUTED)
	origin_summary.name = "OriginSummary"
	origin_summary.size_flags_vertical = Control.SIZE_EXPAND_FILL
	info.add_child(origin_summary)
	save_notice = _wrapped_label("", 12, MUTED)
	save_notice.name = "SaveNotice"
	info.add_child(save_notice)
	if save_store.has_any_save(save_path):
		var saved: Dictionary = save_store.load_game(save_path)
		if bool(saved.get("ok", false)):
			var continue_button := _button("Continue saved game")
			continue_button.name = "ContinueButton"
			continue_button.pressed.connect(_continue_game)
			info.add_child(continue_button)
			if bool(saved.get("recovered", false)):
				save_notice.text = "The latest save is damaged. Continue will use the previous backup."
		else:
			save_notice.text = "Saved game is unreadable or uses an unsupported version."
	var start_button := _button("Start new game")
	start_button.name = "StartGameButton"
	start_button.pressed.connect(_start_game)
	info.add_child(start_button)
	overwrite_confirmation = ConfirmationDialog.new()
	overwrite_confirmation.name = "OverwriteConfirmation"
	overwrite_confirmation.title = "Start a new game?"
	overwrite_confirmation.dialog_text = "Starting a new game replaces the current save slot. A compatible previous save is kept as a backup when possible."
	overwrite_confirmation.ok_button_text = "Start new game"
	overwrite_confirmation.confirmed.connect(_begin_new_game)
	start_screen.add_child(overwrite_confirmation)
	_select_origin(chosen_origin)


func _select_origin(faction_id: String) -> void:
	for profile in world.state.starting_profiles:
		if profile.faction_id != faction_id:
			continue
		chosen_origin = faction_id
		origin_title.text = _faction_name(faction_id)
		var lines: Array[String] = []
		lines.append(str(profile.description))
		lines.append("\nStarting sector: " + _sector_name(str(profile.sector_id)))
		lines.append("\nStarting relations")
		for faction in world.state.factions:
			if faction.id == world.state.player_faction_id:
				continue
			var value := int(profile.relations.get(faction.id, 0))
			lines.append("%s: %s%d" % [faction.name, "+" if value > 0 else "", value])
		origin_summary.text = "\n".join(lines)
		for id in start_buttons:
			var border := ACCENT if id == faction_id else BORDER
			var fill := Color("1b3a41") if id == faction_id else Color("182d3b")
			start_buttons[id].add_theme_stylebox_override("normal", _style(fill, border))
		return


func _start_game() -> void:
	if game_started:
		return
	if save_store.has_any_save(save_path):
		overwrite_confirmation.popup_centered()
		return
	_begin_new_game()


func _begin_new_game() -> void:
	if game_started:
		return
	if world.load_starter(chosen_origin) != OK:
		push_error("Unable to create the selected starting origin")
		return
	_enter_world()
	_save_current_game()


func _continue_game() -> void:
	if game_started:
		return
	var saved: Dictionary = save_store.load_game(save_path)
	if not bool(saved.get("ok", false)):
		save_notice.text = "Saved game could not be loaded."
		return
	if world.restore_snapshot(saved.state) != OK:
		save_notice.text = "Saved game could not be upgraded."
		return
	_enter_world()
	save_status.text = "Backup loaded" if bool(saved.get("recovered", false)) else "Game loaded"


func _enter_world() -> void:
	game_started = true
	paused = true
	_elapsed = 0.0
	_last_saved_tick = int(world.state.tick)
	active_player_ship_id = str(world.state.ships[0].id)
	selected_property_key = "ship|" + active_player_ship_id
	property_picker_signature = ""
	selected_sector = str(world.state.ships[0].sector)
	selected_view = "sector"
	start_screen.queue_free()
	_build_ui()
	_show_sector(selected_sector)
	_update_header()


func _save_current_game() -> bool:
	var error: Error = save_store.save_game(save_path, world.snapshot())
	if error != OK:
		if is_instance_valid(save_status):
			save_status.text = "Save failed"
		push_warning("Could not save the game: " + error_string(error))
		return false
	_last_saved_tick = int(world.state.tick)
	if is_instance_valid(save_status):
		save_status.text = "Saved"
	return true


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
	save_status = _label("", 13, MUTED)
	save_status.name = "SaveStatus"
	header.add_child(save_status)
	var save_button := _button("Save")
	save_button.name = "SaveButton"
	save_button.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	save_button.pressed.connect(_save_current_game)
	header.add_child(save_button)
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
	property_panel.custom_minimum_size.x = 235
	content.add_child(property_panel)
	var property_scroll := ScrollContainer.new()
	property_scroll.name = "PropertyScroll"
	property_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	property_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	property_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	property_panel.add_child(property_scroll)
	var property_list := VBoxContainer.new()
	property_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	property_list.add_theme_constant_override("separation", 8)
	property_scroll.add_child(property_list)
	property_list.add_child(_label("YOUR PROPERTY", 14, ACCENT))
	property_count_label = _label("", 12, MUTED)
	property_count_label.name = "PropertyCount"
	property_list.add_child(property_count_label)
	property_filter = LineEdit.new()
	property_filter.name = "PropertySearch"
	property_filter.placeholder_text = "Find ship, station or site"
	property_filter.custom_minimum_size.y = 40
	property_filter.add_theme_font_size_override("font_size", 13)
	property_filter.text_changed.connect(_on_property_filter)
	property_list.add_child(property_filter)
	property_picker = OptionButton.new()
	property_picker.name = "PropertyPicker"
	property_picker.custom_minimum_size.y = 44
	property_picker.add_theme_font_size_override("font_size", 13)
	property_picker.item_selected.connect(_on_property_picked)
	property_list.add_child(property_picker)
	property_action_button = _button("Show selected property")
	property_action_button.name = "OpenPropertyButton"
	property_action_button.pressed.connect(_open_selected_property_action)
	property_list.add_child(property_action_button)
	ship_button = _button("◈   First Light")
	ship_button.name = "ShipButton"
	ship_button.pressed.connect(_show_ship)
	property_list.add_child(ship_button)
	ship_brief = _label("", 13, MUTED)
	ship_brief.name = "ShipBrief"
	property_list.add_child(ship_brief)
	property_list.add_child(_label("SHIP ROLE", 12, ACCENT))
	role_picker = OptionButton.new()
	role_picker.name = "RolePicker"
	role_picker.custom_minimum_size.y = 44
	role_picker.add_theme_font_size_override("font_size", 14)
	role_picker.add_item("Unassigned")
	role_picker.add_item("Auto trader")
	role_picker.add_item("Build supplier")
	role_picker.add_item("Station supplier")
	role_picker.item_selected.connect(_on_role_selected)
	property_list.add_child(role_picker)
	role_hint = _wrapped_label("", 12, MUTED)
	role_hint.name = "RoleHint"
	property_list.add_child(role_hint)
	var crew_button := _button("Rename / manage crew")
	crew_button.name = "ManageCrewButton"
	crew_button.pressed.connect(_open_crew_screen)
	property_list.add_child(crew_button)
	var trade_button := _button("Trade")
	trade_button.name = "TradeButton"
	trade_button.pressed.connect(_open_trade)
	property_list.add_child(trade_button)
	var wharf_button := _button("Order ships")
	wharf_button.name = "ShipyardButton"
	wharf_button.pressed.connect(_open_shipyard)
	property_list.add_child(wharf_button)
	var plan_button := _button("Plan station")
	plan_button.name = "PlanStationButton"
	plan_button.pressed.connect(_open_station_planner)
	property_list.add_child(plan_button)
	var builds_button := _button("Stations & builds")
	builds_button.name = "BuildsButton"
	builds_button.pressed.connect(_open_build_screen)
	property_list.add_child(builds_button)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	property_list.add_child(spacer)
	property_list.add_child(_label("YOUR FACTION  /  ORIGIN", 12, ACCENT))
	property_list.add_child(_wrapped_label(_faction_name(str(world.state.player_origin_faction_id)), 14, TEXT))
	property_list.add_child(_wrapped_label("Your ships belong to your own faction.", 13, MUTED))

	var map_panel := _panel()
	map_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(map_panel)
	var map_column := VBoxContainer.new()
	map_column.add_theme_constant_override("separation", 8)
	map_panel.add_child(map_column)
	var map_heading := HBoxContainer.new()
	map_heading.add_theme_constant_override("separation", 6)
	map_column.add_child(map_heading)
	map_title = _label("GALAXY MAP", 16, TEXT)
	map_title.name = "MapTitle"
	map_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_heading.add_child(map_title)
	for control in [{"text":"−", "name":"MapZoomOut", "factor":0.8}, {"text":"+", "name":"MapZoomIn", "factor":1.25}]:
		var zoom_button := _button(str(control.text))
		zoom_button.name = str(control.name)
		zoom_button.custom_minimum_size.x = 46
		zoom_button.pressed.connect(_zoom_map.bind(float(control.factor)))
		map_heading.add_child(zoom_button)
	var fit_button := _button("Fit")
	fit_button.name = "MapFit"
	fit_button.pressed.connect(_fit_map)
	map_heading.add_child(fit_button)
	map_mode_button = _button("Open sector")
	map_mode_button.name = "MapMode"
	map_mode_button.pressed.connect(_toggle_map_mode)
	map_heading.add_child(map_mode_button)
	map_view = GalaxyMapScript.new()
	map_view.name = "GalaxyMap"
	map_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map_view.set_world(world.snapshot())
	map_view.sector_selected.connect(_show_sector)
	map_column.add_child(map_view)
	sector_map = SectorMapScript.new()
	sector_map.name = "SectorMap"
	sector_map.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sector_map.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sector_map.set_world(world.snapshot())
	sector_map.select_sector(selected_sector)
	sector_map.sector_selected.connect(_show_sector)
	sector_map.station_selected.connect(_open_map_station)
	sector_map.ship_selected.connect(_show_map_ship)
	sector_map.visible = false
	map_column.add_child(sector_map)
	map_caption = _label("▲ Player ships   ◆ Faction traffic   ·   Drag to pan; pinch or use + / − to zoom.", 12, MUTED)
	map_caption.name = "MapCaption"
	map_column.add_child(map_caption)

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
	var detail_scroll := ScrollContainer.new()
	detail_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	detail_scroll.custom_minimum_size.y = 80
	detail.add_child(detail_scroll)
	detail_body = _wrapped_label("", 15, MUTED)
	detail_body.name = "DetailBody"
	detail_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail_scroll.add_child(detail_body)
	order_target = _wrapped_label("", 13, MUTED)
	order_target.name = "OrderTarget"
	detail.add_child(order_target)
	var order_button := _button("Queue fly order")
	order_button.name = "OrderButton"
	order_button.pressed.connect(_queue_order)
	detail.add_child(order_button)
	order_feedback = _wrapped_label("", 12, ACCENT)
	order_feedback.name = "OrderFeedback"
	detail.add_child(order_feedback)

	var footer := _label("OFFLINE  ·  PAUSED AT START  ·  ORIGINAL STARTER GALAXY", 11, MUTED)
	footer.name = "MainFooter"
	root.add_child(footer)
	_refresh_world_display()


func _toggle_pause() -> void:
	paused = not paused
	order_feedback.text = ""
	_update_header()
	if paused:
		_save_current_game()


func _update_header() -> void:
	credits_label.text = "%s CR" % str(int(world.state.starting_credits))
	tick_label.text = "TICK %s" % str(int(world.state.tick))
	pause_button.text = "Resume" if paused else "Pause"


func _on_sector_picked(index: int) -> void:
	_show_sector(str(sector_picker.get_item_metadata(index)))


func _toggle_map_mode() -> void:
	showing_sector_map = not showing_sector_map
	map_view.visible = not showing_sector_map
	sector_map.visible = showing_sector_map
	sector_map.select_sector(selected_sector)
	_update_map_heading()


func _update_map_heading() -> void:
	map_title.text = _sector_name(selected_sector).to_upper() if showing_sector_map else "GALAXY MAP"
	map_mode_button.text = "Galaxy" if showing_sector_map else "Open sector"
	map_caption.text = "Tap a connection, station or ship. Drag to pan; pinch or use + / − to zoom." if showing_sector_map else "▲ Player ships   ◆ Faction traffic   ·   Drag to pan; pinch or use + / − to zoom."


func _zoom_map(factor: float) -> void:
	var active_map = sector_map if showing_sector_map else map_view
	active_map.zoom_by(factor)


func _fit_map() -> void:
	var active_map = sector_map if showing_sector_map else map_view
	active_map.fit_map()


func _show_sector(sector_id: String) -> void:
	for sector in world.state.sectors:
		if sector.id == sector_id:
			selected_sector = sector_id
			selected_view = "sector"
			var faction_name := "Independent"
			for faction in world.state.factions:
				if faction.id == sector.owner:
					faction_name = faction.name
			map_view.select_sector(sector_id)
			sector_map.select_sector(sector_id)
			_update_map_heading()
			for index in sector_picker.item_count:
				if sector_picker.get_item_metadata(index) == sector_id:
					sector_picker.select(index)
			detail_title.text = sector.name
			var standing := int(world.state.relations.get(sector.owner, 0))
			detail_body.text = "Controlled by\n%s\n\nRelations: %s%d\n\n%s" % [faction_name, "+" if standing > 0 else "", standing, sector.description]
			var traffic: Array[String] = []
			for vessel in world.state.ships:
				if vessel.owner != world.state.player_faction_id and vessel.sector == sector_id:
					var movement := " → " + _sector_name(str(vessel.travel.to)) if not vessel.travel.is_empty() else ""
					traffic.append("%s · %s%s" % [vessel.name, vessel.status, movement])
			if not traffic.is_empty():
				detail_body.text += "\n\nFaction traffic\n" + "\n".join(traffic)
			order_target.text = "Destination: " + str(sector.name)
			return


func _open_map_station(station_id: String) -> void:
	if world._find_station(station_id).is_empty():
		return
	_open_trade()
	for index in trade_station_picker.item_count:
		if trade_station_picker.get_item_metadata(index) == station_id:
			trade_station_picker.select(index)
			_on_trade_selection(index)
			return


func _show_map_ship(ship_id: String) -> void:
	var ship: Dictionary = world._find_ship(ship_id)
	if ship.is_empty():
		_show_sector(selected_sector)
		return
	if ship.owner == world.state.player_faction_id:
		_activate_player_ship(ship_id)
		return
	selected_view = "npc_ship"
	selected_ship_id = ship_id
	detail_title.text = str(ship.name)
	var destination := ""
	if not ship.travel.is_empty():
		destination = "\nCrossing to " + _sector_name(str(ship.travel.to))
	detail_body.text = "%s  ·  %s\n\nFaction\n%s\n\nRole\n%s\n\nSector\n%s%s" % [ship["class"], ship.status, _faction_name(str(ship.owner)), ship.role, _sector_name(str(ship.sector)), destination]


func _show_ship() -> void:
	selected_view = "ship"
	var ship: Dictionary = _player_ship()
	if ship.is_empty():
		detail_title.text = "No selected ship"
		detail_body.text = "Choose one of your ships from the property list."
		return
	selected_property_key = "ship|" + str(ship.id)
	_refresh_property_picker()
	var sector_name := _sector_name(str(ship.sector))
	detail_title.text = ship.name
	detail_body.text = "%s  ·  %s\n\nCaptain\n%s\n\nCrew\n%s\n\nRole\n%s\n\nLocation\n%s" % [ship["class"], ship.status, ship.captain, int(ship.crew), ship.role, sector_name]
	var job: Dictionary = ship.player_trader
	if job.enabled:
		if job.phase == "to_source":
			detail_body.text += "\n\nTrader plan\nCollect from " + _station_name(str(job.source_id))
		elif job.phase == "to_destination":
			detail_body.text += "\n\nTrader cargo\n%d units for %s" % [int(job.managed_quantity), _station_name(str(job.destination_id)) if not str(job.destination_id).is_empty() else "an available buyer"]
		else:
			detail_body.text += "\n\nTrader plan\nLooking for a profitable supply run"
	if ship.build_supply.enabled:
		var supply: Dictionary = ship.build_supply
		var site: Dictionary = world.construction.find_site(world, str(supply.site_id))
		detail_body.text += "\n\nBuild supply\n" + str(site.get("name", "Build site"))
		if supply.phase == "to_source":
			detail_body.text += " · Collect from " + _station_name(str(supply.source_id))
		elif supply.phase == "to_site":
			detail_body.text += " · Deliver to site"
		elif not str(supply.wait_reason).is_empty():
			detail_body.text += " · " + str(supply.wait_reason)
	if ship.station_supply.enabled:
		var supply: Dictionary = ship.station_supply
		detail_body.text += "\n\nStation supply\n%s · %s\nSpent: %d / %d CR" % [_station_name(str(supply.station_id)), ship.status, int(supply.spent), int(supply.budget_limit)]
		if supply.phase == "to_source":
			detail_body.text += "\nCollecting from " + _station_name(str(supply.source_id))
		elif supply.phase == "to_station":
			detail_body.text += "\nDelivering to station"
	var cargo_lines: Array[String] = []
	for ware in world.state.wares:
		var quantity := int(ship.cargo.get(ware.id, 0))
		if quantity > 0:
			cargo_lines.append("%s: %d" % [ware.name, quantity])
	detail_body.text += "\n\nCargo (%d / %d)\n%s" % [world.cargo_volume(str(ship.id)), int(ship.cargo_capacity), "Empty" if cargo_lines.is_empty() else "\n".join(cargo_lines)]
	if not ship.travel.is_empty():
		detail_body.text += "\n\nCrossing to %s" % _sector_name(str(ship.travel.to))
	if not ship.orders.is_empty():
		var destinations: Array[String] = []
		for order in ship.orders:
			destinations.append(_sector_name(str(order.destination)))
		detail_body.text += "\n\nOrders\n" + " → ".join(destinations)


func _sector_name(sector_id: String) -> String:
	for sector in world.state.sectors:
		if sector.id == sector_id:
			return str(sector.name)
	return sector_id


func _station_name(station_id: String) -> String:
	var station: Dictionary = world._find_station(station_id)
	return str(station.name) if not station.is_empty() else station_id


func _faction_name(faction_id: String) -> String:
	for faction in world.state.factions:
		if faction.id == faction_id:
			return str(faction.name)
	return faction_id


## The active command ship is a UI selection, not an ownership transfer or
## saved simulation field. Orders, trading and supply always pass its stable ID.
func _player_ship() -> Dictionary:
	var ship: Dictionary = world._find_ship(active_player_ship_id)
	if not ship.is_empty() and ship.owner == world.state.player_faction_id:
		return ship
	for candidate in world.state.ships:
		if candidate.owner == world.state.player_faction_id:
			return candidate
	return {}


func _activate_player_ship(ship_id: String) -> bool:
	var ship: Dictionary = world._find_ship(ship_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id:
		return false
	active_player_ship_id = ship_id
	selected_property_key = "ship|" + ship_id
	_refresh_property_picker()
	_show_ship()
	return true


func _property_records() -> Array:
	var records: Array = []
	var site_station_ids: Dictionary = {}
	for site in world.state.get("build_sites", []):
		if int(site.completed) < site.tasks.size() or bool(site.get("cancelled", false)):
			site_station_ids[str(site.station_id)] = true
	for ship in world.state.ships:
		if ship.owner == world.state.player_faction_id:
			records.append({"key":"ship|" + str(ship.id), "kind":"Ship", "name":str(ship.name), "sector":str(ship.sector)})
	for station in world.state.stations:
		if station.owner == world.state.player_faction_id and not site_station_ids.has(str(station.id)):
			records.append({"key":"station|" + str(station.id), "kind":"Station", "name":str(station.name), "sector":str(station.sector)})
	for site in world.state.get("build_sites", []):
		if site_station_ids.has(str(site.station_id)):
			records.append({"key":"site|" + str(site.id), "kind":"Build site", "name":str(site.name), "sector":str(site.sector)})
	return records


func _refresh_property_picker() -> void:
	if not is_instance_valid(property_picker) or not is_instance_valid(property_filter):
		return
	var records: Array = _property_records()
	var ship_count := 0
	var station_count := 0
	var site_count := 0
	var visible: Array = []
	var needle: String = property_filter.text.strip_edges().to_lower()
	var signatures: Array[String] = [needle]
	for record in records:
		match str(record.kind):
			"Ship":
				ship_count += 1
			"Station":
				station_count += 1
			"Build site":
				site_count += 1
		var search_text: String = ("%s %s %s %s" % [record.kind, record.name, record.key, _sector_name(str(record.sector))]).to_lower()
		if needle.is_empty() or search_text.contains(needle):
			visible.append(record)
			signatures.append("%s=%s@%s" % [record.key, record.name, record.sector])
	property_count_label.text = "%d ships · %d stations · %d sites" % [ship_count, station_count, site_count]
	var signature: String = "|".join(signatures)
	if signature != property_picker_signature:
		property_picker.set_block_signals(true)
		property_picker.clear()
		if visible.is_empty():
			property_picker.add_item("No matching property")
			property_picker.set_item_metadata(0, "")
		else:
			for entry in visible:
				property_picker.add_item("%s: %s" % [entry.kind, entry.name])
				property_picker.set_item_metadata(property_picker.item_count - 1, str(entry.key))
		property_picker_signature = signature
		property_picker.set_block_signals(false)
	var chosen_index := 0
	for index in range(property_picker.item_count):
		if str(property_picker.get_item_metadata(index)) == selected_property_key:
			chosen_index = index
			break
	property_picker.select(chosen_index)
	property_picker.disabled = visible.is_empty()
	property_action_button.disabled = visible.is_empty()
	if not visible.is_empty():
		var key: String = str(property_picker.get_item_metadata(chosen_index))
		property_action_button.text = "Manage build site" if key.begins_with("site|") else ("Open station trade" if key.begins_with("station|") else "Show selected ship")


func _on_property_filter(_text: String) -> void:
	property_picker_signature = ""
	_refresh_property_picker()


func _on_property_picked(index: int) -> void:
	if index < 0 or index >= property_picker.item_count:
		return
	var key: String = str(property_picker.get_item_metadata(index))
	if key.is_empty():
		return
	selected_property_key = key
	if key.begins_with("ship|"):
		_activate_player_ship(key.substr(5))
	elif key.begins_with("station|"):
		_show_owned_station(key.substr(8))
	elif key.begins_with("site|"):
		_show_owned_site(key.substr(5))
	_refresh_property_picker()


func _focus_property_sector(sector_id: String) -> void:
	selected_sector = sector_id
	map_view.select_sector(sector_id)
	sector_map.select_sector(sector_id)
	_update_map_heading()
	for index in range(sector_picker.item_count):
		if str(sector_picker.get_item_metadata(index)) == sector_id:
			sector_picker.select(index)
			break
	order_target.text = "Destination: " + _sector_name(sector_id)


func _show_owned_station(station_id: String) -> void:
	var station: Dictionary = world._find_station(station_id)
	if station.is_empty() or station.owner != world.state.player_faction_id:
		_show_sector(selected_sector)
		return
	selected_view = "owned_station"
	selected_property_key = "station|" + station_id
	_focus_property_sector(str(station.sector))
	detail_title.text = str(station.name)
	var modules: Array[String] = []
	for module in station.production:
		var recipe: Dictionary = world._find_recipe(str(module.recipe_id))
		modules.append("%s · %s" % [recipe.get("name", module.recipe_id), module.get("status", "Waiting")])
	detail_body.text = "YOUR STATION\nSector: %s\nStorage: %d / %d\nProduction modules: %d\n%s" % [_sector_name(str(station.sector)), world.station_volume(station_id), int(station.storage_capacity), station.production.size(), "No active production." if modules.is_empty() else "\n".join(modules)]


func _show_owned_site(site_id: String) -> void:
	var site: Dictionary = world.construction.find_site(world, site_id)
	if site.is_empty():
		_show_sector(selected_sector)
		return
	if int(site.completed) >= site.tasks.size() and not bool(site.get("cancelled", false)):
		_show_owned_station(str(site.station_id))
		return
	selected_view = "owned_site"
	selected_property_key = "site|" + site_id
	_focus_property_sector(str(site.sector))
	detail_title.text = str(site.name)
	var stored: Array[String] = []
	for ware_id in site.build_storage:
		if int(site.build_storage[ware_id]) > 0:
			var ware: Dictionary = world._find_ware(str(ware_id))
			stored.append("%s × %d" % [ware.get("name", ware_id), int(site.build_storage[ware_id])])
	detail_body.text = "YOUR BUILD SITE\nSector: %s\nStatus: %s\nModules completed: %d / %d\nBuild storage: %s" % [_sector_name(str(site.sector)), site.status, int(site.completed), site.tasks.size(), "Empty" if stored.is_empty() else ", ".join(stored)]


func _open_selected_property_action() -> void:
	if property_picker.disabled or property_picker.selected < 0:
		return
	var key: String = str(property_picker.get_item_metadata(property_picker.selected))
	if key.begins_with("ship|"):
		_activate_player_ship(key.substr(5))
	elif key.begins_with("site|"):
		_open_build_screen(key.substr(5))
	elif key.begins_with("station|"):
		var station_id: String = key.substr(8)
		_open_trade()
		for index in range(trade_station_picker.item_count):
			if str(trade_station_picker.get_item_metadata(index)) == station_id:
				trade_station_picker.select(index)
				_on_trade_selection(index)
				break


func _on_role_selected(index: int) -> void:
	var ship: Dictionary = _player_ship()
	if index in [0, 1] and world.set_player_trader(str(ship.id), index == 1):
		_save_current_game()
	elif index == 2:
		_open_build_screen()
	elif index == 3:
		_open_trade()
		trade_feedback.text = "Select one of your stations, then choose Supply inputs."
	_refresh_world_display()


func _queue_order() -> void:
	var ship: Dictionary = _player_ship()
	if world.queue_fly_to(str(ship.id), selected_sector):
		order_feedback.text = "Order queued. Resume to travel." if paused else "Order queued."
		_save_current_game()
	else:
		order_feedback.text = "Already there, already queued, or unreachable."
	_refresh_world_display()


func _refresh_world_display() -> void:
	var ship: Dictionary = _player_ship()
	active_player_ship_id = str(ship.id)
	ship_button.text = "◈   " + str(ship.name)
	_refresh_property_picker()
	ship_brief.text = "%s  ·  %s\n%s" % [ship["class"], ship.status, _sector_name(str(ship.sector))]
	role_picker.select(3 if ship.station_supply.enabled else (2 if ship.build_supply.enabled else (1 if ship.player_trader.enabled else 0)))
	if ship.station_supply.enabled:
		role_hint.text = "Supplying a station within your purchase allowance."
	elif ship.build_supply.enabled:
		role_hint.text = "Supplying a build site using your cargo and credits."
	elif ship.player_trader.enabled:
		role_hint.text = "Uses your credits. Queued orders finish before trading."
	else:
		role_hint.text = "Turning off a role leaves cargo aboard; current orders finish."
	var current_world: Dictionary = world.snapshot()
	map_view.set_world(current_world)
	sector_map.set_world(current_world)
	if selected_view == "ship":
		_show_ship()
	elif selected_view == "npc_ship":
		_show_map_ship(selected_ship_id)
	elif selected_view == "owned_station":
		_show_owned_station(selected_property_key.substr(8))
	elif selected_view == "owned_site":
		_show_owned_site(selected_property_key.substr(5))
	else:
		_show_sector(selected_sector)


func _open_station_planner() -> void:
	if is_instance_valid(plan_screen):
		return
	plan_module_counts.clear()
	plan_import_options.clear()
	plan_screen = Control.new()
	plan_screen.name = "StationPlanner"
	plan_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(plan_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.90)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	plan_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	plan_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(920, 600)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	column.add_child(_label("STATION PLANNER", 22, TEXT))
	column.add_child(_wrapped_label("Sector: %s  ·  Fee paid upfront; materials supplied separately. Cancellation is not yet available." % _sector_name(selected_sector), 14, MUTED))
	var content := HBoxContainer.new()
	content.add_theme_constant_override("separation", 18)
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(content)
	var control_scroll := ScrollContainer.new()
	control_scroll.custom_minimum_size.x = 350
	control_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	content.add_child(control_scroll)
	var controls := VBoxContainer.new()
	controls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	controls.add_theme_constant_override("separation", 6)
	control_scroll.add_child(controls)
	controls.add_child(_label("CHOOSE PRODUCTION MODULES", 13, ACCENT))
	for recipe in world.state.recipes:
		var row := HBoxContainer.new()
		controls.add_child(row)
		var label := _label(str(recipe.name), 15, TEXT)
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(label)
		var remove := _button("−")
		remove.name = "PlanRemove_" + str(recipe.id)
		remove.custom_minimum_size.x = 44
		remove.pressed.connect(_adjust_plan_count.bind(str(recipe.id), -1))
		row.add_child(remove)
		var amount := SpinBox.new()
		amount.name = "ModuleCount_" + str(recipe.id)
		amount.min_value = 0
		amount.max_value = 100
		amount.step = 1
		amount.value = 0
		amount.custom_minimum_size = Vector2(72, 44)
		amount.add_theme_font_size_override("font_size", 15)
		amount.value_changed.connect(_on_plan_changed)
		row.add_child(amount)
		plan_module_counts[recipe.id] = amount
		var add := _button("+")
		add.name = "PlanAdd_" + str(recipe.id)
		add.custom_minimum_size.x = 44
		add.pressed.connect(_adjust_plan_count.bind(str(recipe.id), 1))
		row.add_child(add)
	controls.add_child(_label("HOW TO SOURCE INPUTS", 13, ACCENT))
	plan_mode = OptionButton.new()
	plan_mode.name = "PlanSourceMode"
	plan_mode.custom_minimum_size.y = 44
	plan_mode.add_theme_font_size_override("font_size", 15)
	for option in [{"label":"Self-sufficient", "id":"self"}, {"label":"Import selected inputs", "id":"selected"}, {"label":"Import all inputs", "id":"all"}]:
		plan_mode.add_item(str(option.label))
		plan_mode.set_item_metadata(plan_mode.item_count - 1, option.id)
	plan_mode.item_selected.connect(_on_plan_changed)
	controls.add_child(plan_mode)
	plan_import_list = VBoxContainer.new()
	plan_import_list.name = "PlanImportOptions"
	plan_import_list.visible = false
	controls.add_child(plan_import_list)
	var input_wares: Dictionary = {}
	for recipe in world.state.recipes:
		for ware_id in recipe.inputs:
			input_wares[ware_id] = true
	for ware in world.state.wares:
		if not input_wares.has(ware.id):
			continue
		var toggle := CheckButton.new()
		toggle.name = "Import_" + str(ware.id)
		toggle.text = "Import " + str(ware.name)
		toggle.custom_minimum_size.y = 44
		toggle.add_theme_font_size_override("font_size", 14)
		toggle.toggled.connect(_on_plan_changed)
		plan_import_list.add_child(toggle)
		plan_import_options[ware.id] = toggle
	var result_scroll := ScrollContainer.new()
	result_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	result_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	result_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	content.add_child(result_scroll)
	plan_result = _wrapped_label("", 15, TEXT)
	plan_result.name = "StationPlanResult"
	plan_result.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	result_scroll.add_child(plan_result)
	plan_feedback = _wrapped_label("", 13, ACCENT)
	column.add_child(plan_feedback)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	column.add_child(actions)
	plan_build_button = _button("Place build site")
	plan_build_button.name = "PlaceBuildSiteButton"
	plan_build_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	plan_build_button.pressed.connect(_place_build_site)
	actions.add_child(plan_build_button)
	var close_button := _button("Close")
	close_button.name = "ClosePlannerButton"
	close_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	close_button.pressed.connect(_close_station_planner)
	actions.add_child(close_button)
	_update_station_plan()


func _adjust_plan_count(recipe_id: String, delta: int) -> void:
	if plan_module_counts.has(recipe_id):
		var amount: SpinBox = plan_module_counts[recipe_id]
		amount.value += delta


func _on_plan_changed(_value: Variant) -> void:
	if is_instance_valid(plan_feedback):
		plan_feedback.text = ""
	_update_station_plan()


func _plan_settings() -> Dictionary:
	var mode := str(plan_mode.get_item_metadata(plan_mode.selected))
	var requested: Dictionary = {}
	for id in plan_module_counts:
		requested[id] = int(plan_module_counts[id].value)
	var imports: Array = []
	for id in plan_import_options:
		if plan_import_options[id].button_pressed:
			imports.append(id)
	return {"mode":mode, "requested":requested, "imports":imports}


func _update_station_plan() -> void:
	if not is_instance_valid(plan_screen):
		return
	var settings := _plan_settings()
	plan_import_list.visible = settings.mode == "selected"
	var result: Dictionary = station_planner.preview(world.state, settings.requested, str(settings.mode), settings.imports, selected_sector)
	var estimate: Dictionary = world.construction.quote(world, selected_sector, settings.requested, str(settings.mode), settings.imports)
	plan_build_button.disabled = not estimate.ok or (estimate.ok and int(world.state.starting_credits) < int(estimate.fee))
	if result.modules.is_empty() and result.errors.is_empty():
		plan_result.text = "Choose a production module and quantity to see the required station modules and supplies."
		return
	var lines: Array[String] = []
	if not result.errors.is_empty():
		lines.append("PLAN NEEDS ATTENTION\n" + "\n".join(result.errors))
	if estimate.ok:
		lines.append("BUILDER FEE: %d CR  ·  %d work ticks, plus travel" % [int(estimate.fee), int(estimate.ticks)])
		var material_lines: Array[String] = []
		for ware_id in estimate.materials:
			var ware: Dictionary = world._find_ware(str(ware_id))
			material_lines.append("%s × %d" % [ware.get("name", ware_id), int(estimate.materials[ware_id])])
		lines.append("BUILD MATERIALS\n" + ", ".join(material_lines) + "\nBuy and deliver these separately.")
		if int(world.state.starting_credits) < int(estimate.fee):
			lines.append("Not enough credits for the builder fee.")
	elif result.errors.is_empty():
		lines.append(str(estimate.message))
	if settings.mode != "self":
		lines.append("Imported production inputs must be delivered manually for now.")
	if not result.warnings.is_empty():
		lines.append("CHECK BEFORE BUILDING\n" + "\n".join(result.warnings))
	lines.append("MODULES")
	for row in result.modules:
		var added := "  (+%d for inputs)" % int(row.added) if int(row.added) > 0 else ""
		lines.append("%s × %d%s" % [row.name, int(row.total), added])
	if not result.wares.is_empty():
		lines.append("\nFLOW PER 60 TICKS")
		for ware in result.wares:
			var line := "%s: %.1f made, %.1f used" % [ware.name, float(ware.supply), float(ware.demand)]
			line += "\n  Import %.1f" % float(ware.imports) if float(ware.imports) > 0.000001 else "\n  Available %.1f" % float(ware.surplus)
			lines.append(line)
	plan_result.text = "\n".join(lines)


func _place_build_site() -> void:
	if not is_instance_valid(plan_screen):
		return
	var settings := _plan_settings()
	var result: Dictionary = world.construction.place(world, selected_sector, settings.requested, str(settings.mode), settings.imports)
	if not result.ok:
		plan_feedback.text = str(result.message)
		_update_station_plan()
		return
	var saved := _save_current_game()
	_update_header()
	_refresh_world_display()
	_close_station_planner()
	_open_build_screen(str(result.site_id))
	if not saved:
		build_feedback.text = "Site placed, but saving failed."


func _close_station_planner() -> void:
	if is_instance_valid(plan_screen):
		plan_screen.queue_free()
	plan_screen = null


func _open_build_screen(selected_site_id: String = "") -> void:
	if is_instance_valid(build_screen):
		return
	build_screen = Control.new()
	build_screen.name = "BuildScreen"
	build_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(build_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.90)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	build_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	build_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(900, 560)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	column.add_child(_label("STATIONS & BUILDS", 22, TEXT))
	column.add_child(_wrapped_label("Deliver materials yourself or assign your ship to supply this site.", 14, MUTED))
	build_picker = OptionButton.new()
	build_picker.name = "BuildSitePicker"
	build_picker.custom_minimum_size.y = 44
	build_picker.add_theme_font_size_override("font_size", 15)
	var selected := 0
	for site in world.state.build_sites:
		build_picker.add_item("%s  ·  %s" % [site.name, _sector_name(str(site.sector))])
		build_picker.set_item_metadata(build_picker.item_count - 1, site.id)
		if site.id == selected_site_id:
			selected = build_picker.item_count - 1
	if build_picker.item_count == 0:
		build_picker.add_item("No build sites yet")
		build_picker.set_item_metadata(0, "")
		build_picker.disabled = true
	build_picker.select(selected)
	build_picker.item_selected.connect(_on_build_selection)
	column.add_child(build_picker)
	var task_controls := HBoxContainer.new()
	task_controls.add_theme_constant_override("separation", 8)
	column.add_child(task_controls)
	build_task_picker = OptionButton.new()
	build_task_picker.name = "BuildTaskPicker"
	build_task_picker.custom_minimum_size.y = 44
	build_task_picker.add_theme_font_size_override("font_size", 14)
	build_task_picker.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	build_task_picker.item_selected.connect(_on_build_task_selection)
	task_controls.add_child(build_task_picker)
	build_move_up_button = _button("Move up")
	build_move_up_button.name = "MoveBuildTaskUp"
	build_move_up_button.pressed.connect(_move_selected_build_task.bind(-1))
	task_controls.add_child(build_move_up_button)
	build_move_down_button = _button("Move down")
	build_move_down_button.name = "MoveBuildTaskDown"
	build_move_down_button.pressed.connect(_move_selected_build_task.bind(1))
	task_controls.add_child(build_move_down_button)
	build_task_list_signature = ""
	build_task_picker_site_id = ""
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)
	build_info = _wrapped_label("", 15, TEXT)
	build_info.name = "BuildInfo"
	build_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(build_info)
	build_feedback = _wrapped_label("", 13, ACCENT)
	build_feedback.name = "BuildFeedback"
	column.add_child(build_feedback)
	column.add_child(_wrapped_label("Auto supply uses your ship's cargo and credits, and replaces its current role. Queued orders finish first.", 13, MUTED))
	build_supply_button = _button("Automatically supply this site")
	build_supply_button.name = "AutoSupplyBuildButton"
	build_supply_button.pressed.connect(_toggle_build_supply)
	column.add_child(build_supply_button)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	column.add_child(actions)
	build_dock_button = _button("Dock at site")
	build_dock_button.name = "DockBuildSiteButton"
	build_dock_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	build_dock_button.pressed.connect(_dock_build_site)
	actions.add_child(build_dock_button)
	build_deliver_button = _button("Deliver materials")
	build_deliver_button.name = "DeliverBuildMaterialsButton"
	build_deliver_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	build_deliver_button.pressed.connect(_deliver_build_materials)
	actions.add_child(build_deliver_button)
	build_pause_button = _button("Pause build")
	build_pause_button.name = "PauseBuildButton"
	build_pause_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	build_pause_button.pressed.connect(_toggle_build_pause)
	actions.add_child(build_pause_button)
	var recovery_actions := HBoxContainer.new()
	recovery_actions.add_theme_constant_override("separation", 8)
	column.add_child(recovery_actions)
	build_cancel_button = _button("Cancel unfinished construction")
	build_cancel_button.name = "CancelBuildButton"
	build_cancel_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	build_cancel_button.pressed.connect(_request_build_cancel)
	recovery_actions.add_child(build_cancel_button)
	build_recover_button = _button("Recover unused materials")
	build_recover_button.name = "RecoverBuildMaterialsButton"
	build_recover_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	build_recover_button.pressed.connect(_recover_build_materials)
	recovery_actions.add_child(build_recover_button)
	build_cancel_confirm = ConfirmationDialog.new()
	build_cancel_confirm.name = "ConfirmCancelBuild"
	build_cancel_confirm.title = "Cancel unfinished construction?"
	build_cancel_confirm.confirmed.connect(_confirm_build_cancel)
	build_screen.add_child(build_cancel_confirm)
	var close_button := _button("Close")
	close_button.name = "CloseBuildButton"
	close_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	close_button.pressed.connect(_close_build_screen)
	actions.add_child(close_button)
	_update_build_screen()


func _selected_build_site() -> Dictionary:
	if not is_instance_valid(build_picker) or build_picker.item_count == 0:
		return {}
	return world.construction.find_site(world, str(build_picker.get_item_metadata(build_picker.selected)))


func _on_build_selection(_index: int) -> void:
	build_feedback.text = ""
	_update_build_screen()


func _on_build_task_selection(_index: int) -> void:
	_update_build_screen()


func _update_build_task_picker(site: Dictionary) -> void:
	# Populating the selector programmatically must not recursively call its
	# selection handler, particularly during a one-tick state refresh.
	build_task_picker.set_block_signals(true)
	if site.is_empty():
		build_task_picker.clear()
		build_task_picker.add_item("No modules")
		build_task_picker.select(0)
		build_task_picker.disabled = true
		build_move_up_button.disabled = true
		build_move_down_button.disabled = true
		build_task_list_signature = ""
		build_task_picker_site_id = ""
		build_task_picker.set_block_signals(false)
		return
	var entries: Array[String] = []
	for index in range(site.tasks.size()):
		var task: Dictionary = site.tasks[index]
		var stage := "Completed" if index < int(site.completed) else ("Building" if task.started else "Queued")
		entries.append("%s:%s" % [task.recipe_id, stage])
	var signature := str(site.id) + "|" + "|".join(entries)
	if signature != build_task_list_signature:
		var selected_index := 0
		if build_task_picker_site_id == str(site.id) and build_task_picker.selected >= 0:
			selected_index = build_task_picker.selected
		build_task_picker.clear()
		for index in range(site.tasks.size()):
			var recipe: Dictionary = world._find_recipe(str(site.tasks[index].recipe_id))
			var stage := "Completed" if index < int(site.completed) else ("Building" if site.tasks[index].started else "Queued")
			build_task_picker.add_item("%d. %s — %s" % [index + 1, recipe.get("name", site.tasks[index].recipe_id), stage])
			build_task_picker.set_item_metadata(index, index)
		build_task_picker.select(clampi(selected_index, 0, site.tasks.size() - 1))
		build_task_list_signature = signature
		build_task_picker_site_id = str(site.id)
	build_task_picker.disabled = false
	var chosen := build_task_picker.selected
	var first: int = int(world.construction.first_editable_index(site))
	build_move_up_button.disabled = bool(site.get("cancelled", false)) or chosen <= first
	build_move_down_button.disabled = bool(site.get("cancelled", false)) or chosen < first or chosen >= site.tasks.size() - 1
	build_task_picker.set_block_signals(false)


func _move_selected_build_task(direction: int) -> void:
	var site := _selected_build_site()
	if site.is_empty() or build_task_picker.selected < 0:
		return
	var index := int(build_task_picker.get_item_metadata(build_task_picker.selected))
	var result: Dictionary = world.construction.move_queued_module(world, str(site.id), index, direction)
	build_feedback.text = str(result.message)
	if result.ok:
		build_task_list_signature = ""
		if not _save_current_game():
			build_feedback.text += " Save failed."
		_refresh_world_display()
		_update_build_screen()
		build_task_picker.select(int(result.new_index))
	_update_build_screen()


func _update_build_screen() -> void:
	if not is_instance_valid(build_screen):
		return
	var site := _selected_build_site()
	var available := not site.is_empty()
	_update_build_task_picker(site)
	build_dock_button.disabled = not available
	build_deliver_button.disabled = not available
	build_pause_button.disabled = not available or (available and (bool(site.get("cancelled", false)) or int(site.completed) >= site.tasks.size()))
	build_supply_button.disabled = not available or (available and bool(site.get("cancelled", false)))
	build_cancel_button.disabled = not available or (available and (bool(site.get("cancelled", false)) or int(site.completed) >= site.tasks.size()))
	build_recover_button.disabled = not available or (available and (not bool(site.get("cancelled", false)) or _construction_storage_empty(site)))
	if not available:
		build_info.text = "No build sites yet. Choose Plan station to create one."
		return
	build_pause_button.text = "Resume build" if site.paused else "Pause build"
	var supplier: Dictionary = _player_ship()
	var supplying_here: bool = supplier.build_supply.enabled and supplier.build_supply.site_id == site.id
	build_supply_button.text = "Stop supplying this site" if supplying_here else "Automatically supply with %s" % supplier.name
	var lines: Array[String] = []
	lines.append("%s  ·  %s\nStatus: %s\nBuilder fee paid: %d CR" % [site.name, _sector_name(str(site.sector)), site.status, int(site.fee)])
	var needed: Dictionary = world.construction.remaining_materials(site)
	var material_lines: Array[String] = []
	for ware_id in needed:
		var ware: Dictionary = world._find_ware(str(ware_id))
		material_lines.append("%s: %d still needed  ·  %d in build storage" % [ware.get("name", ware_id), int(needed[ware_id]), int(site.build_storage.get(ware_id, 0))])
	if bool(site.get("cancelled", false)):
		var recover_lines: Array[String] = []
		for ware_id in site.build_storage:
			if int(site.build_storage[ware_id]) > 0:
				var ware: Dictionary = world._find_ware(str(ware_id))
				recover_lines.append("%s: %d units" % [ware.get("name", ware_id), int(site.build_storage[ware_id])])
		lines.append("CONSTRUCTION CANCELLED\nRefunded builder fees: %d CR\nRecoverable materials: %s" % [int(site.refunded_fee), ", ".join(recover_lines) if not recover_lines.is_empty() else "None remaining"])
	else:
		lines.append("BUILD MATERIALS\n" + ("All required materials delivered." if material_lines.is_empty() else "\n".join(material_lines)))
	if supplying_here:
		lines.append("Supplier: %s · %s" % [supplier.name, supplier.status])
	var builder: Dictionary = world._find_ship(str(site.builder_id))
	lines.append("Builder: %s\nModules completed: %d / %d" % [str(builder.name) if not builder.is_empty() else "Waiting for a ready site", int(site.completed), site.tasks.size()])
	if int(site.completed) < site.tasks.size():
		var task: Dictionary = site.tasks[int(site.completed)]
		var recipe: Dictionary = world._find_recipe(str(task.recipe_id))
		lines.append("Current module: %s  ·  %d / %d ticks" % [recipe.get("name", task.recipe_id), int(task.progress), int(task.duration)])
	lines.append("BUILD ORDER\nMove up or down changes priority only among unstarted modules. Completed and building modules remain fixed.")
	lines.append("AUTO SUPPLY\nUses %s's suitable cargo, then collects from your stations or buys from NPC markets using your credits. Current orders finish first; changing the ship's role stops supply and leaves cargo aboard." % supplier.name)
	lines.append("Cancellation returns fees for never-started modules and retains physical materials for dockside recovery. A module already underway finishes; no further modules start." if bool(site.get("cancelled", false)) else "Pause or cancel remaining work. Completed modules remain operational; cancellation refunds fees for unstarted modules only.")
	build_info.text = "\n\n".join(lines)


func _construction_storage_empty(site: Dictionary) -> bool:
	for quantity in site.build_storage.values():
		if int(quantity) > 0:
			return false
	return true


func _request_build_cancel() -> void:
	var site := _selected_build_site()
	if site.is_empty() or bool(site.get("cancelled", false)) or int(site.completed) >= site.tasks.size():
		return
	build_cancel_site_id = str(site.id)
	build_cancel_confirm.dialog_text = "Cancel unstarted modules at %s? Their builder fees will be refunded, delivered unused materials will remain for physical recovery, and an active module will finish. Completed modules are kept." % site.name
	build_cancel_confirm.popup_centered()


func _confirm_build_cancel() -> void:
	var site_id := build_cancel_site_id
	build_cancel_site_id = ""
	var result: Dictionary = world.construction.cancel(world, site_id)
	build_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			build_feedback.text += " Save failed."
		_refresh_world_display()
	_update_build_screen()


func _recover_build_materials() -> void:
	var site := _selected_build_site()
	if site.is_empty():
		return
	var result: Dictionary = world.construction.recover(world, str(_player_ship().id), str(site.id))
	build_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			build_feedback.text += " Save failed."
		_refresh_world_display()
	_update_build_screen()


func _dock_build_site() -> void:
	var site := _selected_build_site()
	if site.is_empty():
		return
	var result: Dictionary = world.dock_ship(str(_player_ship().id), str(site.station_id))
	build_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			build_feedback.text += " Save failed."
		_refresh_world_display()
	_update_build_screen()


func _deliver_build_materials() -> void:
	var site := _selected_build_site()
	if site.is_empty():
		return
	var result: Dictionary = world.construction.deliver(world, str(_player_ship().id), str(site.id))
	build_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			build_feedback.text += " Save failed."
		_refresh_world_display()
	_update_build_screen()


func _toggle_build_pause() -> void:
	var site := _selected_build_site()
	if not site.is_empty() and world.construction.set_paused(world, str(site.id), not bool(site.paused)):
		build_feedback.text = "Build paused." if site.paused else "Build resumed."
		if not _save_current_game():
			build_feedback.text += " Save failed."
	_update_build_screen()


func _toggle_build_supply() -> void:
	var site := _selected_build_site()
	if site.is_empty():
		return
	var ship: Dictionary = _player_ship()
	if ship.build_supply.enabled and ship.build_supply.site_id == site.id:
		world.build_supply.stop(ship)
		build_feedback.text = "Supply stopped. Cargo stays aboard and queued orders finish."
	else:
		var result: Dictionary = world.build_supply.assign(world, str(ship.id), str(site.id))
		build_feedback.text = str(result.message)
		if not result.ok:
			_update_build_screen()
			return
	if not _save_current_game():
		build_feedback.text += " Save failed."
	_refresh_world_display()
	_update_build_screen()


func _close_build_screen() -> void:
	if is_instance_valid(build_screen):
		build_screen.queue_free()
	build_screen = null
	build_task_list_signature = ""
	build_task_picker_site_id = ""


func _open_crew_screen() -> void:
	if is_instance_valid(crew_screen):
		return
	var ship: Dictionary = _player_ship()
	if ship.is_empty():
		return
	crew_screen_ship_id = str(ship.id)
	_show_ship()
	crew_screen = Control.new()
	crew_screen.name = "CrewScreen"
	crew_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(crew_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.94)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	crew_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	crew_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(820, 540)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 9)
	panel.add_child(column)
	column.add_child(_label("SHIP & CREW MANAGEMENT", 22, TEXT))
	var name_row := HBoxContainer.new()
	name_row.add_theme_constant_override("separation", 8)
	column.add_child(name_row)
	crew_rename_input = LineEdit.new()
	crew_rename_input.name = "CrewShipName"
	crew_rename_input.text = str(ship.name)
	crew_rename_input.max_length = world.personnel.MAX_NAME_LENGTH
	crew_rename_input.custom_minimum_size.y = 44
	crew_rename_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_row.add_child(crew_rename_input)
	var rename_button := _button("Rename ship")
	rename_button.name = "RenameShipButton"
	rename_button.pressed.connect(_rename_crew_ship)
	name_row.add_child(rename_button)
	var scrolling := ScrollContainer.new()
	scrolling.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scrolling.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scrolling)
	crew_info = _wrapped_label("", 15, TEXT)
	crew_info.name = "CrewInfo"
	crew_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scrolling.add_child(crew_info)
	crew_feedback = _wrapped_label("", 13, ACCENT)
	crew_feedback.name = "CrewFeedback"
	column.add_child(crew_feedback)
	var count_row := HBoxContainer.new()
	count_row.add_theme_constant_override("separation", 8)
	column.add_child(count_row)
	count_row.add_child(_label("Crew quantity", 14, TEXT))
	crew_quantity = SpinBox.new()
	crew_quantity.name = "CrewQuantity"
	crew_quantity.min_value = 1
	crew_quantity.max_value = 100
	crew_quantity.step = 1
	crew_quantity.value = 1
	crew_quantity.custom_minimum_size = Vector2(105, 44)
	count_row.add_child(crew_quantity)
	var hire_button := _button("Hire")
	hire_button.name = "HireCrewButton"
	hire_button.pressed.connect(_hire_crew)
	count_row.add_child(hire_button)
	var discharge_button := _button("Discharge")
	discharge_button.name = "DischargeCrewButton"
	discharge_button.pressed.connect(_discharge_crew)
	count_row.add_child(discharge_button)
	var transfer_row := HBoxContainer.new()
	transfer_row.add_theme_constant_override("separation", 8)
	column.add_child(transfer_row)
	crew_transfer_picker = OptionButton.new()
	crew_transfer_picker.name = "CrewTransferPicker"
	crew_transfer_picker.custom_minimum_size.y = 44
	crew_transfer_picker.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	transfer_row.add_child(crew_transfer_picker)
	var transfer_button := _button("Transfer crew")
	transfer_button.name = "TransferCrewButton"
	transfer_button.pressed.connect(_transfer_crew)
	transfer_row.add_child(transfer_button)
	crew_captain_swap_button = _button("Swap captains")
	crew_captain_swap_button.name = "SwapCaptainsButton"
	crew_captain_swap_button.pressed.connect(_swap_crew_captains)
	transfer_row.add_child(crew_captain_swap_button)
	var close_button := _button("Close")
	close_button.name = "CloseCrewButton"
	close_button.pressed.connect(_close_crew_screen)
	column.add_child(close_button)
	_update_crew_screen()


func _crew_ship() -> Dictionary:
	var ship: Dictionary = world._find_ship(crew_screen_ship_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id:
		return {}
	return ship


func _crew_quantity_value() -> int:
	return int(crew_quantity.value)


func _update_crew_screen() -> void:
	if not is_instance_valid(crew_screen):
		return
	var ship: Dictionary = _crew_ship()
	if ship.is_empty():
		crew_info.text = "Selected ship is no longer owned."
		crew_transfer_picker.disabled = true
		return
	var station: Dictionary = world._find_station(str(ship.docked_at))
	var at_npc: bool = not station.is_empty() and station.owner != world.state.player_faction_id and world.state.crew_pools.has(station.id)
	var count: int = int(ship.crew)
	var capacity: int = int(world.personnel.capacity(ship))
	var lines: Array[String] = []
	lines.append("%s · %s\nCaptain: %s (separate from service crew)\nService crew: %d / %d berths" % [ship.name, ship["class"], ship.captain, count, capacity])
	var captain: Dictionary = ship.captain_profile
	var crew: Dictionary = ship.crew_profile
	var pay: Dictionary = ship.payroll
	var until_pay: int = maxi(0, int(world.personnel.PAYROLL_TICKS) - (int(world.state.tick) - int(pay.last_tick)))
	lines.append("CAPTAIN PROFILE\n%s\nPiloting skill: %d / 5 · Experience: %d\nMorale: %d / 100" % [captain.id, int(captain.skill), int(captain.experience), int(captain.morale)])
	lines.append("SERVICE CREW PROGRESSION\nAverage skill: %d / 5 · Total crew experience: %d\nMorale: %d / 100" % [int(crew.skill), int(crew.experience), int(crew.morale)])
	lines.append("PAYROLL\nCurrent wage: %d CR every %d ticks\nNext payroll in: %d ticks\nOutstanding: %d CR · Total paid: %d CR\nConsecutive unpaid cycles: %d" % [world.personnel._ship_wages(ship), world.personnel.PAYROLL_TICKS, until_pay, int(pay.arrears), int(pay.total_paid), int(pay.unpaid_periods)])
	lines.append("DOCKSIDE STAFFING\n%s" % ("Docked at " + str(station.name) if not station.is_empty() else "Not docked. Dock at an NPC station in Trade to hire or discharge crew."))
	if at_npc:
		lines.append("Available recruits: %d\nHiring cost: %d CR per crew member\nYour faction credits: %d CR" % [int(world.state.crew_pools[station.id]), int(world.personnel.HIRE_COST), int(world.state.starting_credits)])
	else:
		lines.append("Recruitment and discharge require an NPC recruitment station. The station pool is finite and hires are paid to its operating budget.")
	lines.append("CREW AND CAPTAIN TRANSFERS\nTwo player-owned ships must be docked at the same station, with no active orders. Move service crew or swap named captains with the selected ship. Captains retain their own skill and morale.")
	lines.append("Real sector crossings and physical trade or delivery work earn experience. Payroll transfers credits to an NPC agency station; unpaid wages accrue as arrears and reduce morale. Skill and morale do not yet change job speed or efficiency.")
	crew_info.text = "\n\n".join(lines)
	var previous_id := ""
	if crew_transfer_picker.item_count > 0 and crew_transfer_picker.selected >= 0:
		previous_id = str(crew_transfer_picker.get_item_metadata(crew_transfer_picker.selected))
	var transfers: Array = world.personnel.eligible_transfers(world, str(ship.id))
	crew_transfer_picker.set_block_signals(true)
	crew_transfer_picker.clear()
	var selected_index := 0
	for candidate in transfers:
		crew_transfer_picker.add_item("%s · %d / %d" % [candidate.name, int(candidate.crew), int(world.personnel.capacity(candidate))])
		crew_transfer_picker.set_item_metadata(crew_transfer_picker.item_count - 1, str(candidate.id))
		if candidate.id == previous_id:
			selected_index = crew_transfer_picker.item_count - 1
	if transfers.is_empty():
		crew_transfer_picker.add_item("No other ship at this dock")
		crew_transfer_picker.set_item_metadata(0, "")
	crew_transfer_picker.select(selected_index)
	crew_transfer_picker.disabled = transfers.is_empty()
	crew_captain_swap_button.disabled = transfers.is_empty()
	crew_transfer_picker.set_block_signals(false)


func _finish_crew_action(result: Dictionary) -> void:
	crew_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			crew_feedback.text += " Save failed."
		_update_header()
		_refresh_world_display()
	_update_crew_screen()


func _rename_crew_ship() -> void:
	_finish_crew_action(world.personnel.rename(world, crew_screen_ship_id, crew_rename_input.text))


func _hire_crew() -> void:
	_finish_crew_action(world.personnel.hire(world, crew_screen_ship_id, _crew_quantity_value()))


func _discharge_crew() -> void:
	_finish_crew_action(world.personnel.discharge(world, crew_screen_ship_id, _crew_quantity_value()))


func _transfer_crew() -> void:
	var destination_id := ""
	if crew_transfer_picker.selected >= 0:
		destination_id = str(crew_transfer_picker.get_item_metadata(crew_transfer_picker.selected))
	_finish_crew_action(world.personnel.transfer(world, crew_screen_ship_id, destination_id, _crew_quantity_value()))


func _swap_crew_captains() -> void:
	var destination_id := ""
	if crew_transfer_picker.selected >= 0:
		destination_id = str(crew_transfer_picker.get_item_metadata(crew_transfer_picker.selected))
	_finish_crew_action(world.personnel.swap_captains(world, crew_screen_ship_id, destination_id))


func _close_crew_screen() -> void:
	if is_instance_valid(crew_screen):
		crew_screen.queue_free()
	crew_screen = null
	crew_screen_ship_id = ""


func _open_shipyard() -> void:
	if is_instance_valid(shipyard_screen):
		return
	shipyard_screen = Control.new()
	shipyard_screen.name = "ShipyardScreen"
	shipyard_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(shipyard_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.94)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shipyard_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shipyard_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(820, 530)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 9)
	panel.add_child(column)
	column.add_child(_label("NPC WHARF — SHIP ORDERS", 22, TEXT))
	column.add_child(_wrapped_label("Remote contracts consume actual alloy stock and transfer credits at Vellum Foundry. One berth builds the ships in order. The price includes an initial contract pilot and crew.", 14, MUTED))
	column.add_child(_label("CHOOSE HULL", 12, ACCENT))
	shipyard_hull_picker = OptionButton.new()
	shipyard_hull_picker.name = "ShipyardHullPicker"
	shipyard_hull_picker.custom_minimum_size.y = 44
	shipyard_hull_picker.add_theme_font_size_override("font_size", 15)
	for hull_id in world.state.shipyard.catalog:
		var hull: Dictionary = world.state.shipyard.catalog[hull_id]
		shipyard_hull_picker.add_item("%s  ·  %d CR" % [hull.name, int(hull.price)])
		shipyard_hull_picker.set_item_metadata(shipyard_hull_picker.item_count - 1, str(hull_id))
	shipyard_hull_picker.select(0)
	shipyard_hull_picker.item_selected.connect(_on_shipyard_hull_selected)
	column.add_child(shipyard_hull_picker)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)
	shipyard_info = _wrapped_label("", 15, TEXT)
	shipyard_info.name = "ShipyardInfo"
	shipyard_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(shipyard_info)
	shipyard_feedback = _wrapped_label("", 13, ACCENT)
	shipyard_feedback.name = "ShipyardFeedback"
	column.add_child(shipyard_feedback)
	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", 8)
	column.add_child(buttons)
	shipyard_buy_button = _button("Place ship order")
	shipyard_buy_button.name = "OrderShipButton"
	shipyard_buy_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	shipyard_buy_button.pressed.connect(_request_ship_order)
	buttons.add_child(shipyard_buy_button)
	var close_button := _button("Close")
	close_button.name = "CloseShipyardButton"
	close_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	close_button.pressed.connect(_close_shipyard)
	buttons.add_child(close_button)
	shipyard_confirm = ConfirmationDialog.new()
	shipyard_confirm.name = "ConfirmShipOrder"
	shipyard_confirm.title = "Confirm ship contract"
	shipyard_confirm.confirmed.connect(_confirm_ship_order)
	shipyard_screen.add_child(shipyard_confirm)
	_update_shipyard_screen()


func _selected_hull_id() -> String:
	if not is_instance_valid(shipyard_hull_picker) or shipyard_hull_picker.selected < 0:
		return ""
	return str(shipyard_hull_picker.get_item_metadata(shipyard_hull_picker.selected))


func _on_shipyard_hull_selected(_index: int) -> void:
	shipyard_feedback.text = ""
	_update_shipyard_screen()


func _update_shipyard_screen() -> void:
	if not is_instance_valid(shipyard_screen):
		return
	var hull_id: String = _selected_hull_id()
	var hull: Dictionary = world.state.shipyard.catalog.get(hull_id, {})
	if hull.is_empty():
		shipyard_buy_button.disabled = true
		shipyard_info.text = "No available hulls."
		return
	var wharf: Dictionary = world._find_station(str(world.state.shipyard.wharf_station_id))
	var stock_lines: Array[String] = []
	for ware_id in hull.materials:
		var ware: Dictionary = world._find_ware(str(ware_id))
		stock_lines.append("%s: %d required · %d physically at wharf" % [ware.get("name", ware_id), int(hull.materials[ware_id]), int(wharf.get("stock", {}).get(ware_id, 0))])
	var quote: Dictionary = world.shipyard.quote(world, hull_id)
	shipyard_buy_button.disabled = not bool(quote.get("ok", false))
	var lines: Array[String] = []
	lines.append("%s — %s\nPrice: %d CR  ·  Assembly: %d simulation ticks\nCargo capacity: %d  ·  Initial crew: %d\nWharf: %s in %s" % [hull.name, hull["class"], int(hull.price), int(hull.ticks), int(hull.cargo_capacity), int(hull.crew), wharf.get("name", "Unavailable"), _sector_name(str(wharf.get("sector", "")))])
	lines.append("PHYSICAL CONSTRUCTION MATERIALS\n" + "\n".join(stock_lines))
	lines.append("ORDER STATUS\n" + str(quote.message))
	var queue_lines: Array[String] = []
	for order in world.state.shipyard.orders:
		var ordered: Dictionary = world.state.shipyard.catalog.get(str(order.hull_id), {})
		queue_lines.append("%s · %s · %d / %d ticks · %s" % [order.id, ordered.get("name", order.hull_id), int(order.progress), int(order.duration), str(order.status).capitalize()])
	lines.append("SHIP ASSEMBLY QUEUE\n" + ("No orders yet." if queue_lines.is_empty() else "\n".join(queue_lines)))
	lines.append("Completed ships appear in Your Property, docked at the wharf. A ship awaiting assembly has paid its contract and committed its metal. Ship order cancellation, refunds and dedicated player shipyards are future features.")
	shipyard_info.text = "\n\n".join(lines)


func _request_ship_order() -> void:
	var hull_id: String = _selected_hull_id()
	var quote: Dictionary = world.shipyard.quote(world, hull_id)
	if not bool(quote.get("ok", false)):
		shipyard_feedback.text = str(quote.message)
		_update_shipyard_screen()
		return
	var hull: Dictionary = quote.hull
	shipyard_confirm.dialog_text = "Spend %d CR and the listed physical wharf material on one %s? The ship will arrive only after its %d-tick assembly completes. This prototype contract cannot be cancelled." % [int(hull.price), str(hull.name), int(hull.ticks)]
	shipyard_confirm.popup_centered()


func _confirm_ship_order() -> void:
	var result: Dictionary = world.shipyard.place_order(world, _selected_hull_id())
	shipyard_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			shipyard_feedback.text += " Save failed."
		_update_header()
		_refresh_world_display()
	_update_shipyard_screen()


func _close_shipyard() -> void:
	if is_instance_valid(shipyard_screen):
		shipyard_screen.queue_free()
	shipyard_screen = null


func _open_trade() -> void:
	if is_instance_valid(trade_screen):
		return
	trade_screen = Control.new()
	trade_screen.name = "TradeScreen"
	trade_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(trade_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.90)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	trade_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	trade_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(850, 560)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	column.add_child(_label("STATION TRADE", 22, TEXT))
	column.add_child(_wrapped_label("Travel to the station's sector, dock, then exchange cargo for credits.", 14, MUTED))
	var content := HBoxContainer.new()
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 20)
	column.add_child(content)
	var controls := VBoxContainer.new()
	controls.custom_minimum_size.x = 355
	controls.add_theme_constant_override("separation", 8)
	content.add_child(controls)
	controls.add_child(_label("STATION", 12, ACCENT))
	trade_station_picker = OptionButton.new()
	trade_station_picker.name = "TradeStationPicker"
	trade_station_picker.custom_minimum_size.y = 44
	trade_station_picker.add_theme_font_size_override("font_size", 15)
	var current_sector: String = _player_ship().sector
	var selected_index := 0
	var selected_current := false
	for station in world.state.stations:
		trade_station_picker.add_item("%s  ·  %s" % [station.name, _sector_name(str(station.sector))])
		trade_station_picker.set_item_metadata(trade_station_picker.item_count - 1, station.id)
		if station.sector == current_sector and not selected_current:
			selected_index = trade_station_picker.item_count - 1
			selected_current = true
	trade_station_picker.select(selected_index)
	trade_station_picker.item_selected.connect(_on_trade_selection)
	controls.add_child(trade_station_picker)
	var dock_button := _button("Dock at selected station")
	dock_button.name = "DockButton"
	dock_button.pressed.connect(_dock_at_station)
	controls.add_child(dock_button)
	trade_station_actions = HBoxContainer.new()
	trade_station_actions.add_theme_constant_override("separation", 8)
	controls.add_child(trade_station_actions)
	trade_archive_button = _button("Read historical records")
	trade_archive_button.name = "ReadArchiveButton"
	trade_archive_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	trade_archive_button.pressed.connect(_open_archive)
	trade_station_actions.add_child(trade_archive_button)
	trade_research_button = _button("Research")
	trade_research_button.name = "ResearchButton"
	trade_research_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	trade_research_button.pressed.connect(_open_research)
	trade_station_actions.add_child(trade_research_button)
	trade_station_supply_button = _button("Supply inputs")
	trade_station_supply_button.name = "StationSupplyButton"
	trade_station_supply_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	trade_station_supply_button.pressed.connect(_open_station_supply)
	trade_station_actions.add_child(trade_station_supply_button)
	controls.add_child(_label("WARE", 12, ACCENT))
	trade_ware_picker = OptionButton.new()
	trade_ware_picker.name = "TradeWarePicker"
	trade_ware_picker.custom_minimum_size.y = 44
	trade_ware_picker.add_theme_font_size_override("font_size", 15)
	for ware in world.state.wares:
		trade_ware_picker.add_item(str(ware.name))
		trade_ware_picker.set_item_metadata(trade_ware_picker.item_count - 1, ware.id)
	trade_ware_picker.item_selected.connect(_on_trade_selection)
	controls.add_child(trade_ware_picker)
	controls.add_child(_label("QUANTITY", 12, ACCENT))
	trade_quantity = SpinBox.new()
	trade_quantity.name = "TradeQuantity"
	trade_quantity.min_value = 1
	trade_quantity.max_value = maxi(1, int(_player_ship().cargo_capacity))
	trade_quantity.step = 1
	trade_quantity.value = 1
	trade_quantity.custom_minimum_size.y = 44
	trade_quantity.add_theme_font_size_override("font_size", 16)
	controls.add_child(trade_quantity)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	controls.add_child(actions)
	for option in [{"name": "Buy", "buy": true}, {"name": "Sell", "buy": false}]:
		var button := _button(str(option.name))
		button.name = "BuyButton" if option.buy else "SellButton"
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.pressed.connect(_perform_trade.bind(bool(option.buy)))
		actions.add_child(button)
		if option.buy:
			trade_buy_button = button
		else:
			trade_sell_button = button
	trade_feedback = _wrapped_label("", 13, ACCENT)
	trade_feedback.name = "TradeFeedback"
	controls.add_child(trade_feedback)
	var details := VBoxContainer.new()
	details.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details.add_theme_constant_override("separation", 10)
	content.add_child(details)
	details.add_child(_label("MARKET & CARGO", 12, ACCENT))
	trade_info = _wrapped_label("", 15, TEXT)
	trade_info.name = "TradeInfo"
	details.add_child(trade_info)
	trade_production_heading = _label("PRODUCTION", 12, ACCENT)
	details.add_child(trade_production_heading)
	trade_production = _wrapped_label("", 13, MUTED)
	trade_production.name = "TradeProduction"
	details.add_child(trade_production)
	details.add_child(_label("TRANSACTION LEDGER", 12, ACCENT))
	var ledger_scroll := ScrollContainer.new()
	ledger_scroll.name = "TradeLedgerScroll"
	ledger_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	ledger_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	ledger_scroll.custom_minimum_size.y = 70
	details.add_child(ledger_scroll)
	trade_ledger = _wrapped_label("", 13, MUTED)
	trade_ledger.name = "TradeLedger"
	trade_ledger.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ledger_scroll.add_child(trade_ledger)
	var close_button := _button("Close")
	close_button.name = "CloseTradeButton"
	close_button.pressed.connect(_close_trade)
	column.add_child(close_button)
	_update_trade_screen()


func _trade_station_id() -> String:
	return str(trade_station_picker.get_item_metadata(trade_station_picker.selected))


func _trade_ware_id() -> String:
	return str(trade_ware_picker.get_item_metadata(trade_ware_picker.selected))


func _on_trade_selection(_index: int) -> void:
	trade_feedback.text = ""
	_update_trade_screen()


func _open_archive() -> void:
	if is_instance_valid(archive_screen):
		return
	var station: Dictionary = world._find_station(_trade_station_id())
	var result: Dictionary = world.archives.read(world, str(_player_ship().id), str(station.id))
	if not result.ok:
		trade_feedback.text = str(result.message)
		return
	if result.first_visit and not _save_current_game():
		trade_feedback.text = "The visit could not be saved."
	var entry: Dictionary = result.entry
	archive_screen = Control.new()
	archive_screen.name = "HistoricalArchiveScreen"
	archive_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(archive_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.95)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	archive_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	archive_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(900, 570)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	column.add_child(_label(str(entry.name).to_upper(), 22, TEXT))
	column.add_child(_wrapped_label("%s · %s · Maintained by %s" % [entry.civilization, entry.homeworld, _faction_name(str(station.owner))], 14, MUTED))
	var scroll := ScrollContainer.new()
	scroll.name = "ArchiveRecordsScroll"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)
	var records := VBoxContainer.new()
	records.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	records.add_theme_constant_override("separation", 12)
	scroll.add_child(records)
	var overview := _wrapped_label("HOMEWORLD\n%s\n\nRESEARCH SUBJECTS\n%s\nSubjects from visited archives can support research." % [entry.world_type, ", ".join(entry.research_subjects)], 15, TEXT)
	overview.name = "ArchiveOverview"
	records.add_child(overview)
	for index in entry.records.size():
		var record: Dictionary = entry.records[index]
		var title := _label(str(record.title).to_upper(), 15, ACCENT)
		records.add_child(title)
		var description := _wrapped_label("%s\n%s" % [record.medium, record.text], 15, TEXT)
		description.name = "ArchiveRecord_%d" % index
		records.add_child(description)
	var close_button := _button("Close archive")
	close_button.name = "CloseArchiveButton"
	close_button.pressed.connect(_close_archive)
	column.add_child(close_button)


func _close_archive() -> void:
	if is_instance_valid(archive_screen):
		archive_screen.queue_free()
	archive_screen = null


func _open_research() -> void:
	if is_instance_valid(research_screen):
		return
	var station: Dictionary = world._find_station(_trade_station_id())
	if station.is_empty() or station.owner != world.state.player_faction_id or not world.research.has_lab(station):
		trade_feedback.text = "A completed player research laboratory is required."
		return
	research_screen = Control.new()
	research_screen.name = "ResearchScreen"
	research_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(research_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.95)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	research_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	research_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(900, 570)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	column.add_child(_label("RESEARCH PROJECTS", 22, TEXT))
	column.add_child(_wrapped_label("Laboratory: %s · Completed projects improve your faction's stations." % station.name, 14, MUTED))
	research_picker = OptionButton.new()
	research_picker.name = "ResearchProjectPicker"
	research_picker.custom_minimum_size.y = 44
	research_picker.add_theme_font_size_override("font_size", 15)
	var selected := 0
	for project_id in world.research.project_order:
		var project: Dictionary = world.research.definition(str(project_id))
		research_picker.add_item(str(project.name))
		research_picker.set_item_metadata(research_picker.item_count - 1, project_id)
		if project_id == world.state.research.active_project_id:
			selected = research_picker.item_count - 1
	research_picker.select(selected)
	research_picker.item_selected.connect(_on_research_selection)
	column.add_child(research_picker)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)
	research_info = _wrapped_label("", 15, TEXT)
	research_info.name = "ResearchInfo"
	research_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(research_info)
	research_feedback = _wrapped_label("", 13, ACCENT)
	research_feedback.name = "ResearchFeedback"
	column.add_child(research_feedback)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	column.add_child(actions)
	research_start_button = _button("Start project here")
	research_start_button.name = "StartResearchButton"
	research_start_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	research_start_button.pressed.connect(_start_research)
	actions.add_child(research_start_button)
	research_pause_button = _button("Pause research")
	research_pause_button.name = "PauseResearchButton"
	research_pause_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	research_pause_button.pressed.connect(_pause_research)
	actions.add_child(research_pause_button)
	var close_button := _button("Close")
	close_button.name = "CloseResearchButton"
	close_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	close_button.pressed.connect(_close_research)
	actions.add_child(close_button)
	_update_research_screen()


func _selected_research_id() -> String:
	return str(research_picker.get_item_metadata(research_picker.selected))


func _on_research_selection(_index: int) -> void:
	research_feedback.text = ""
	_update_research_screen()


func _update_research_screen() -> void:
	if not is_instance_valid(research_screen):
		return
	var station: Dictionary = world._find_station(_trade_station_id())
	var project_id := _selected_research_id()
	var project: Dictionary = world.research.definition(project_id)
	if station.is_empty() or project.is_empty():
		return
	var state: Dictionary = world.state.research
	var completed: bool = project_id in state.completed
	var active: bool = state.active_project_id == project_id and state.lab_station_id == station.id
	var status := "Completed" if completed else ("Active" if active else "Not active")
	if not completed and not active and state.active_project_id == project_id:
		status = "Active at " + _station_name(str(state.lab_station_id))
	if active and int(station.stock.get("research_notes", 0)) == 0:
		status = "Waiting for research notes"
	var references: Array = world.research.references(world, project_id)
	var bonus: int = mini(world.research.MAX_ARCHIVE_BONUS, references.size())
	var sources: Array[String] = []
	for index in references.size():
		var reference: Dictionary = references[index]
		var contribution := "+1 per note" if index < world.research.MAX_ARCHIVE_BONUS else "bonus cap reached"
		sources.append("%s · %s · %s" % [reference.name, ", ".join(reference.topics), contribution])
	var lines: Array[String] = []
	lines.append("%s\n%s\nProgress: %d / %d · %s" % [project.name, project.description, int(state.progress.get(project_id, 0)), int(project.target), status])
	lines.append("REWARD\n" + str(project.reward))
	lines.append("ARCHIVE REFERENCES\nEach note adds %d base progress, plus 1 per relevant visited archive (maximum %d). Current progress per note: %d.\n%s" % [world.research.BASE_PROGRESS, world.research.MAX_ARCHIVE_BONUS, world.research.BASE_PROGRESS + bonus, "\n".join(sources) if not sources.is_empty() else "No relevant archives visited yet."])
	lines.append("LABORATORY\nResearch Notes in storage: %d\nThe laboratory makes one note from one Recorded Data and two Energy Cells every 15 ticks." % int(station.stock.get("research_notes", 0)))
	lines.append("Switching projects preserves each project's progress. Only the selected laboratory supplies the active project.")
	research_info.text = "\n\n".join(lines)
	research_start_button.disabled = completed or active or not world.research.has_lab(station)
	research_start_button.text = "Project active here" if active else "Start project here"
	research_pause_button.disabled = str(state.active_project_id).is_empty()


func _start_research() -> void:
	var result: Dictionary = world.research.start(world, _trade_station_id(), _selected_research_id())
	research_feedback.text = str(result.message)
	if result.ok and not _save_current_game():
		research_feedback.text += " Save failed."
	_update_research_screen()


func _pause_research() -> void:
	if world.research.pause(world):
		research_feedback.text = "Research paused; completed work is retained."
		if not _save_current_game():
			research_feedback.text += " Save failed."
	_update_research_screen()


func _close_research() -> void:
	if is_instance_valid(research_screen):
		research_screen.queue_free()
	research_screen = null


func _open_station_supply() -> void:
	if is_instance_valid(station_supply_screen):
		return
	var station: Dictionary = world._find_station(_trade_station_id())
	if station.is_empty() or station.owner != world.state.player_faction_id:
		trade_feedback.text = "Choose one of your stations."
		return
	station_supply_screen = Control.new()
	station_supply_screen.name = "StationSupplyScreen"
	station_supply_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(station_supply_screen)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.04, 0.06, 0.95)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	station_supply_screen.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	station_supply_screen.add_child(center)
	var panel := _panel()
	panel.custom_minimum_size = Vector2(900, 570)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	column.add_child(_label("STATION INPUT SUPPLY", 22, TEXT))
	column.add_child(_wrapped_label("%s · %s" % [station.name, _sector_name(str(station.sector))], 14, MUTED))
	column.add_child(_wrapped_label("%s uses matching cargo, collects surplus from your stations or buys inputs within this limit. Current orders finish and the existing ship role is replaced." % _player_ship().name, 14, TEXT))
	column.add_child(_label("MAXIMUM PURCHASE SPEND FOR THIS ASSIGNMENT (CR)", 12, ACCENT))
	station_supply_budget = SpinBox.new()
	station_supply_budget.name = "StationSupplyBudget"
	station_supply_budget.min_value = 0
	station_supply_budget.max_value = 1000000000
	station_supply_budget.step = 1
	station_supply_budget.custom_minimum_size.y = 44
	station_supply_budget.add_theme_font_size_override("font_size", 15)
	var ship: Dictionary = _player_ship()
	var active_here: bool = ship.station_supply.enabled and ship.station_supply.station_id == station.id
	station_supply_budget.value = int(ship.station_supply.budget_limit) if active_here else mini(1000, int(world.state.starting_credits))
	column.add_child(station_supply_budget)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)
	station_supply_info = _wrapped_label("", 15, TEXT)
	station_supply_info.name = "StationSupplyInfo"
	station_supply_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(station_supply_info)
	station_supply_feedback = _wrapped_label("", 13, ACCENT)
	station_supply_feedback.name = "StationSupplyFeedback"
	column.add_child(station_supply_feedback)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	column.add_child(actions)
	var assign_button := _button("Assign / update")
	assign_button.name = "AssignStationSupplyButton"
	assign_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	assign_button.pressed.connect(_assign_station_supply)
	actions.add_child(assign_button)
	station_supply_stop_button = _button("Stop supply")
	station_supply_stop_button.name = "StopStationSupplyButton"
	station_supply_stop_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	station_supply_stop_button.pressed.connect(_stop_station_supply)
	actions.add_child(station_supply_stop_button)
	var close_button := _button("Close")
	close_button.name = "CloseStationSupplyButton"
	close_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	close_button.pressed.connect(_close_station_supply)
	actions.add_child(close_button)
	_update_station_supply_screen()


func _update_station_supply_screen() -> void:
	if not is_instance_valid(station_supply_screen):
		return
	var station: Dictionary = world._find_station(_trade_station_id())
	if station.is_empty():
		return
	var ship: Dictionary = _player_ship()
	var active_here: bool = ship.station_supply.enabled and ship.station_supply.station_id == station.id
	station_supply_stop_button.disabled = not active_here
	var desired: Dictionary = world.station_supply.targets(world, station)
	var rows: Array[String] = []
	for ware_id in desired:
		var ware: Dictionary = world._find_ware(str(ware_id))
		rows.append("%s: %d in storage · target %d" % [ware.get("name", ware_id), int(station.stock.get(ware_id, 0)), int(desired[ware_id])])
	var lines: Array[String] = []
	lines.append("INPUT TARGETS\n" + ("No imports needed right now; the supplier can wait for changes." if rows.is_empty() else "\n".join(rows)))
	lines.append("Targets cover about %d ticks of net demand and any reusable source, with room kept for output. They adjust to production and resource changes." % world.station_supply.BUFFER_TICKS)
	if active_here:
		lines.append("SUPPLIER\n%s · %s\nSpent: %d / %d CR" % [ship.name, ship.status, int(ship.station_supply.spent), int(ship.station_supply.budget_limit)])
	else:
		lines.append("No ship assigned to this station.")
	lines.append("The limit is a cap, not an upfront payment. Set it to zero to use only carried cargo or surplus from your own stations. Working stock and reusable sources at those stations are protected.")
	station_supply_info.text = "\n\n".join(lines)


func _assign_station_supply() -> void:
	var ship: Dictionary = _player_ship()
	var result: Dictionary = world.station_supply.assign(world, str(ship.id), _trade_station_id(), int(station_supply_budget.value))
	station_supply_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			station_supply_feedback.text += " Save failed."
		_refresh_world_display()
	_update_station_supply_screen()


func _stop_station_supply() -> void:
	var ship: Dictionary = _player_ship()
	if ship.station_supply.enabled and ship.station_supply.station_id == _trade_station_id():
		world.station_supply.stop(ship)
		station_supply_feedback.text = "Supply stopped. Cargo stays aboard and queued orders finish."
		if not _save_current_game():
			station_supply_feedback.text += " Save failed."
		_refresh_world_display()
	_update_station_supply_screen()


func _close_station_supply() -> void:
	if is_instance_valid(station_supply_screen):
		station_supply_screen.queue_free()
	station_supply_screen = null


func _update_trade_screen() -> void:
	if not is_instance_valid(trade_screen):
		return
	var ship: Dictionary = _player_ship()
	var station: Dictionary = world._find_station(_trade_station_id())
	var ware: Dictionary = world._find_ware(_trade_ware_id())
	var own_station: bool = station.owner == world.state.player_faction_id
	trade_archive_button.visible = station.has("archive")
	trade_research_button.visible = own_station and world.research.has_lab(station)
	trade_station_supply_button.visible = own_station
	trade_station_actions.visible = trade_archive_button.visible or trade_research_button.visible or trade_station_supply_button.visible
	trade_archive_button.disabled = ship.docked_at != station.id
	trade_archive_button.text = "Read historical records" if ship.docked_at == station.id else "Dock to read records"
	trade_buy_button.text = "Take from station" if own_station else "Buy"
	trade_sell_button.text = "Transfer to station" if own_station else "Sell"
	var buy_price := "%d CR" % int(station.sell_prices[ware.id]) if station.sell_prices.has(ware.id) else "Not sold"
	var sell_price := "%d CR" % int(station.buy_prices[ware.id]) if station.buy_prices.has(ware.id) else "Not bought"
	var docked := "Docked here" if ship.docked_at == station.id else "Not docked here"
	trade_info.text = "%s\n%s  ·  %s\nShip: %s  ·  %s\nCargo: %d / %d  ·  Storage: %d / %d\n%s: %d in cargo / %d at station\nStation sells: %s  ·  buys: %s\nStation credits: %d" % [station.name, _faction_name(str(station.owner)), _sector_name(str(station.sector)), _sector_name(str(ship.sector)), docked, world.cargo_volume(str(ship.id)), int(ship.cargo_capacity), world.station_volume(str(station.id)), int(station.storage_capacity), ware.name, int(ship.cargo.get(ware.id, 0)), int(station.stock.get(ware.id, 0)), buy_price, sell_price, int(station.credits)]
	if own_station:
		trade_info.text = "%s\nYour station  ·  %s\nShip: %s  ·  %s\nCargo: %d / %d  ·  Storage: %d / %d\n%s: %d in cargo / %d at station\nTransfers between your ship and station are free." % [station.name, _sector_name(str(station.sector)), _sector_name(str(ship.sector)), docked, world.cargo_volume(str(ship.id)), int(ship.cargo_capacity), world.station_volume(str(station.id)), int(station.storage_capacity), ware.name, int(ship.cargo.get(ware.id, 0)), int(station.stock.get(ware.id, 0))]
	var production_lines: Array[String] = []
	for report in world.production_report(str(station.id)):
		var inputs: Array[String] = []
		var outputs: Array[String] = []
		for ware_id in report.inputs:
			var input_ware: Dictionary = world._find_ware(str(ware_id))
			inputs.append("%s ×%d" % [input_ware.get("name", ware_id), int(report.inputs[ware_id])])
		if not str(report.source).is_empty():
			inputs.append(str(report.source).capitalize())
		if not report.deposit.is_empty():
			var deposit_ware: Dictionary = world._find_ware(str(report.deposit.resource))
			inputs.append("%s deposit ×%d" % [deposit_ware.get("name", report.deposit.resource), int(report.deposit.quantity)])
		for ware_id in report.outputs:
			var output_ware: Dictionary = world._find_ware(str(ware_id))
			outputs.append("%s ×%d" % [output_ware.get("name", ware_id), int(report.outputs[ware_id])])
		production_lines.append("%s: %s (%d/%d)\n%s → %s" % [report.name, report.status, int(report.progress), int(report.duration), " + ".join(inputs), " + ".join(outputs)])
		for ware_id in report.catalysts:
			var catalyst: Dictionary = world._find_ware(str(ware_id))
			if station.has("archive") and report.catalog_source and ware_id == "recorded_data":
				production_lines.append("Reusable source: this archive's historical collection")
			else:
				production_lines.append("Reusable source: %s ×%d" % [catalyst.get("name", ware_id), int(report.catalysts[ware_id])])
		if not report.deposit.is_empty():
			production_lines.append("Deposit remaining: %d" % int(world._station_deposits(station).get(report.deposit.resource, 0)))
	trade_production_heading.text = "ARCHIVE SERVICE & PRODUCTION" if station.has("archive") else "PRODUCTION"
	if station.has("archive"):
		production_lines.push_front("Archive: %s · Staff paid: %d CR\nRecords are readable on site even when service needs upkeep." % [station.archive.status, int(station.archive.staff_credits)])
	trade_production.text = "No production modules." if production_lines.is_empty() else "\n".join(production_lines)
	var lines: Array[String] = []
	var ledger: Array = world.state.ledger
	for index in range(ledger.size() - 1, -1, -1):
		var entry: Dictionary = ledger[index]
		var entry_ware: Dictionary = world._find_ware(str(entry.ware_id))
		var entry_station: Dictionary = world._find_station(str(entry.station_id))
		var entry_ship: Dictionary = world._find_ship(str(entry.ship_id))
		var actor := str(entry_ship.get("name", entry.ship_id))
		if entry.kind == "funding":
			lines.append("#%d  T%d  %s funded +%d CR\n%s" % [int(entry.id), int(entry.tick), actor, int(entry.amount), entry_station.get("name", entry.station_id)])
		elif entry.kind == "construction_fee":
			lines.append("#%d  T%d  Builder %s hired · %d CR\n%s" % [int(entry.id), int(entry.tick), actor, int(entry.amount), entry_station.get("name", entry.station_id)])
		elif entry.kind == "ship_order":
			lines.append("#%d  T%d  Ship contract %s · %d CR paid\n%s" % [int(entry.id), int(entry.tick), actor, -int(entry.amount), entry_station.get("name", entry.station_id)])
		elif entry.kind == "ship_delivery":
			lines.append("#%d  T%d  New ship delivered: %s\n%s" % [int(entry.id), int(entry.tick), actor, entry_station.get("name", entry.station_id)])
		elif entry.kind in ["build_delivery", "transfer_in", "transfer_out"]:
			var action := "Delivered to build storage" if entry.kind == "build_delivery" else ("Transferred to station" if entry.kind == "transfer_in" else "Taken from station")
			lines.append("#%d  T%d  %s: %s %d %s\n%s" % [int(entry.id), int(entry.tick), actor, action, int(entry.quantity), entry_ware.get("name", entry.ware_id), entry_station.get("name", entry.station_id)])
		else:
			lines.append("#%d  T%d  %s: %s %d %s  ·  %s%d CR\n%s" % [int(entry.id), int(entry.tick), actor, str(entry.kind).capitalize(), int(entry.quantity), entry_ware.get("name", entry.ware_id), "+" if int(entry.amount) > 0 else "", int(entry.amount), entry_station.get("name", entry.station_id)])
	var ledger_text := "No transactions yet." if lines.is_empty() else "\n\n".join(lines)
	if trade_ledger.text != ledger_text:
		trade_ledger.text = ledger_text


func _dock_at_station() -> void:
	var result: Dictionary = world.dock_ship(str(_player_ship().id), _trade_station_id())
	trade_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			trade_feedback.text += " Save failed."
		_refresh_world_display()
	_update_trade_screen()


func _perform_trade(buy: bool) -> void:
	var station: Dictionary = world._find_station(_trade_station_id())
	var result: Dictionary
	if station.owner == world.state.player_faction_id:
		result = world.transfer_player_station(str(_player_ship().id), str(station.id), _trade_ware_id(), int(trade_quantity.value), not buy)
	else:
		result = world.trade(str(_player_ship().id), str(station.id), _trade_ware_id(), int(trade_quantity.value), buy)
	trade_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			trade_feedback.text += " Save failed."
		_update_header()
		_refresh_world_display()
	_update_trade_screen()


func _close_trade() -> void:
	_close_archive()
	_close_research()
	_close_station_supply()
	trade_screen.queue_free()
	trade_screen = null
