extends Control

const WorldScript = preload("res://scripts/world.gd")
const GalaxyMapScript = preload("res://scripts/galaxy_map.gd")
const SaveStoreScript = preload("res://scripts/save_store.gd")
const BACKGROUND := Color("080f1b")
const PANEL := Color("101e2d")
const BORDER := Color("24394a")
const TEXT := Color("e2f0f0")
const MUTED := Color("8ca4b3")
const ACCENT := Color("71dfcc")

var world = WorldScript.new()
var save_store = SaveStoreScript.new()
var save_path := "user://faction_command_save.json"
var _last_saved_tick := 0
var paused := true
var _elapsed := 0.0
var map_view
var credits_label: Label
var tick_label: Label
var pause_button: Button
var detail_title: Label
var detail_body: Label
var sector_picker: OptionButton
var ship_brief: Label
var order_target: Label
var order_feedback: Label
var selected_sector := "hearthreach"
var selected_view := "sector"
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
var trade_ledger: Label
var trade_feedback: Label


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
	ship_brief = _label("", 13, MUTED)
	ship_brief.name = "ShipBrief"
	property_list.add_child(ship_brief)
	var trade_button := _button("Trade")
	trade_button.name = "TradeButton"
	trade_button.pressed.connect(_open_trade)
	property_list.add_child(trade_button)
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

	root.add_child(_label("OFFLINE  ·  PAUSED AT START  ·  ORIGINAL STARTER GALAXY", 11, MUTED))
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
			for index in sector_picker.item_count:
				if sector_picker.get_item_metadata(index) == sector_id:
					sector_picker.select(index)
			detail_title.text = sector.name
			var standing := int(world.state.relations.get(sector.owner, 0))
			detail_body.text = "Controlled by\n%s\n\nRelations: %s%d\n\n%s" % [faction_name, "+" if standing > 0 else "", standing, sector.description]
			order_target.text = "Destination: " + str(sector.name)
			return


func _show_ship() -> void:
	selected_view = "ship"
	var ship: Dictionary = world.state.ships[0]
	var sector_name := _sector_name(str(ship.sector))
	detail_title.text = ship.name
	detail_body.text = "%s  ·  %s\n\nCaptain\n%s\n\nCrew\n%s\n\nRole\n%s\n\nLocation\n%s" % [ship["class"], ship.status, ship.captain, int(ship.crew), ship.role, sector_name]
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


func _faction_name(faction_id: String) -> String:
	for faction in world.state.factions:
		if faction.id == faction_id:
			return str(faction.name)
	return faction_id


func _queue_order() -> void:
	var ship: Dictionary = world.state.ships[0]
	if world.queue_fly_to(str(ship.id), selected_sector):
		order_feedback.text = "Order queued. Resume to travel." if paused else "Order queued."
		_save_current_game()
	else:
		order_feedback.text = "Already there, already queued, or unreachable."
	_refresh_world_display()


func _refresh_world_display() -> void:
	var ship: Dictionary = world.state.ships[0]
	ship_brief.text = "%s  ·  %s\n%s" % [ship["class"], ship.status, _sector_name(str(ship.sector))]
	map_view.set_world(world.snapshot())
	if selected_view == "ship":
		_show_ship()
	else:
		_show_sector(selected_sector)


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
	var current_sector: String = world.state.ships[0].sector
	var selected_index := 0
	for station in world.state.stations:
		trade_station_picker.add_item("%s  ·  %s" % [station.name, _sector_name(str(station.sector))])
		trade_station_picker.set_item_metadata(trade_station_picker.item_count - 1, station.id)
		if station.sector == current_sector:
			selected_index = trade_station_picker.item_count - 1
	trade_station_picker.select(selected_index)
	trade_station_picker.item_selected.connect(_on_trade_selection)
	controls.add_child(trade_station_picker)
	var dock_button := _button("Dock at selected station")
	dock_button.name = "DockButton"
	dock_button.pressed.connect(_dock_at_station)
	controls.add_child(dock_button)
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
	trade_quantity.max_value = maxi(1, int(world.state.ships[0].cargo_capacity))
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


func _update_trade_screen() -> void:
	if not is_instance_valid(trade_screen):
		return
	var ship: Dictionary = world.state.ships[0]
	var station: Dictionary = world._find_station(_trade_station_id())
	var ware: Dictionary = world._find_ware(_trade_ware_id())
	var buy_price := "%d CR" % int(station.sell_prices[ware.id]) if station.sell_prices.has(ware.id) else "Not sold"
	var sell_price := "%d CR" % int(station.buy_prices[ware.id]) if station.buy_prices.has(ware.id) else "Not bought"
	var docked := "Docked here" if ship.docked_at == station.id else "Not docked here"
	trade_info.text = "%s\n%s  ·  %s\n\nShip: %s  ·  %s\nCargo: %d / %d\nStation storage: %d / %d\n\n%s: %d in cargo / %d at station\nStation sells: %s\nStation buys: %s\nStation credits: %d" % [station.name, _faction_name(str(station.owner)), _sector_name(str(station.sector)), _sector_name(str(ship.sector)), docked, world.cargo_volume(str(ship.id)), int(ship.cargo_capacity), world.station_volume(str(station.id)), int(station.storage_capacity), ware.name, int(ship.cargo.get(ware.id, 0)), int(station.stock.get(ware.id, 0)), buy_price, sell_price, int(station.credits)]
	var lines: Array[String] = []
	var ledger: Array = world.state.ledger
	for index in range(ledger.size() - 1, -1, -1):
		var entry: Dictionary = ledger[index]
		var entry_ware: Dictionary = world._find_ware(str(entry.ware_id))
		var entry_station: Dictionary = world._find_station(str(entry.station_id))
		lines.append("#%d  T%d  %s %d %s  ·  %s%d CR\n%s" % [int(entry.id), int(entry.tick), str(entry.kind).capitalize(), int(entry.quantity), entry_ware.get("name", entry.ware_id), "+" if int(entry.amount) > 0 else "", int(entry.amount), entry_station.get("name", entry.station_id)])
	var ledger_text := "No transactions yet." if lines.is_empty() else "\n\n".join(lines)
	if trade_ledger.text != ledger_text:
		trade_ledger.text = ledger_text


func _dock_at_station() -> void:
	var result: Dictionary = world.dock_ship(str(world.state.ships[0].id), _trade_station_id())
	trade_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			trade_feedback.text += " Save failed."
		_refresh_world_display()
	_update_trade_screen()


func _perform_trade(buy: bool) -> void:
	var result: Dictionary = world.trade(str(world.state.ships[0].id), _trade_station_id(), _trade_ware_id(), int(trade_quantity.value), buy)
	trade_feedback.text = str(result.message)
	if result.ok:
		if not _save_current_game():
			trade_feedback.text += " Save failed."
		_update_header()
		_refresh_world_display()
	_update_trade_screen()


func _close_trade() -> void:
	trade_screen.queue_free()
	trade_screen = null
