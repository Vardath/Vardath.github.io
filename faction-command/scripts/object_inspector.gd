extends RefCounted
## Read-only, ownership-gated context for the map-first object inspector.
## This is an original faction-command presentation layer. It never changes
## simulation state, issues orders, or creates/stages inventory. The main UI
## validates actions again against current selection before invoking them.

func tabs(world: RefCounted, kind: String, id: String) -> Array[String]:
	var result: Array[String] = []
	match kind:
		"sector":
			if _sector(world, id).is_empty():
				return result
			return ["Info", "Orders", "Assets"]
		"ship":
			var vessel: Dictionary = world._find_ship(id)
			if vessel.is_empty() or vessel.owner != world.state.player_faction_id:
				return result
			return ["Info", "Orders", "Cargo", "Crew", "Trade"]
		"npc_ship":
			var vessel: Dictionary = world._find_ship(id)
			if vessel.is_empty() or vessel.owner == world.state.player_faction_id:
				return result
			return ["Info"]
		"station", "npc_station":
			var station: Dictionary = world._find_station(id)
			if station.is_empty() or (kind == "station") != (station.owner == world.state.player_faction_id):
				return result
			result = ["Info", "Trade", "Cargo", "Production", "Population"]
			if kind == "station":
				result.append_array(["Construction", "Research", "Education"])
			if station.has("archive"):
				result.append("History")
		"site":
			var site: Dictionary = world.construction.find_site(world, id)
			if site.is_empty():
				return result
			var station: Dictionary = world._find_station(str(site.station_id))
			if station.is_empty() or station.owner != world.state.player_faction_id:
				return result
			return ["Info", "Construction", "Cargo"]
	return result


func actions(world: RefCounted, kind: String, id: String, tab: String) -> Array[Dictionary]:
	var options: Array[Dictionary] = []
	if tab not in tabs(world, kind, id):
		return options
	match kind:
		"ship":
			match tab:
				"Crew": options.append({"id":"crew", "label":"Manage crew"})
				"Trade": options.append({"id":"trade", "label":"Open trade"})
		"sector":
			if tab == "Assets":
				options.append({"id":"open_sector", "label":"Open sector map"})
		"station", "npc_station":
			match tab:
				"Info", "Trade", "Cargo":
					options.append({"id":"station_trade", "label":"Open station trade"})
				"Population":
					options.append({"id":"population", "label":"Population overview"})
				"Construction":
					if kind == "station":
						options.append({"id":"builds", "label":"Manage builds"})
				"Education":
					if kind == "station" and not world._find_station(id).get("education", {}).get("modules", []).is_empty():
						options.append({"id":"education", "label":"Manage staffed education"})
				"Research":
					if kind == "station" and world.research.has_lab(world._find_station(id)):
						options.append({"id":"research", "label":"Open research"})
				"History":
					options.append({"id":"station_trade", "label":"Dock to read records"})
		"site":
			if tab == "Construction":
				options.append({"id":"build_site", "label":"Manage build site"})
			if tab == "Cargo":
				options.append({"id":"trade", "label":"Open cargo trade"})
	return options


func _sector(world: RefCounted, id: String) -> Dictionary:
	for entry in world.state.sectors:
		if str(entry.id) == id:
			return entry
	return {}


func _sector_name(world: RefCounted, id: String) -> String:
	return str(_sector(world, id).get("name", id))


func _named_ware(world: RefCounted, ware_id: String) -> String:
	return str(world._find_ware(ware_id).get("name", ware_id))


func _stock_lines(world: RefCounted, stock: Dictionary) -> Array[String]:
	var rows: Array[String] = []
	for ware in world.state.wares:
		var number: int = int(stock.get(ware.id, 0))
		if number > 0:
			rows.append("%s: %d" % [ware.name, number])
	return rows


func _route_lines(world: RefCounted, destination: String) -> String:
	var ship: Dictionary = world._find_ship(_commander_id(world))
	if ship.is_empty() or ship.owner != world.state.player_faction_id:
		return "No player-controlled command ship available."
	if not _sector(world, destination).is_empty():
		var path: Array = world._find_route(str(ship.sector), destination)
		if str(ship.sector) == destination:
			return "%s is already in %s." % [ship.name, _sector_name(world, destination)]
		if path.is_empty():
			return "%s cannot reach %s with the known route network." % [ship.name, _sector_name(world, destination)]
		return "Command ship: %s\nDestination: %s\nKnown route: %s\nTravel estimate: %d ticks (plus existing orders)\nOrders are queued explicitly; selection alone never moves a ship." % [ship.name, _sector_name(world, destination), " → ".join(path), maxi(0, path.size() - 1) * world.TICKS_PER_CROSSING]
	return "Choose a connected destination sector."


func _commander_id(world: RefCounted) -> String:
	for ship in world.state.ships:
		if ship.owner == world.state.player_faction_id:
			return str(ship.id)
	return ""


func content(world: RefCounted, kind: String, id: String, tab: String, info_text: String, active_ship_id: String, selected_sector: String) -> String:
	if tab not in tabs(world, kind, id):
		return "This tab is not available for the selected object."
	if tab == "Info":
		return info_text
	if kind == "sector":
		var sector: Dictionary = _sector(world, id)
		if tab == "Orders":
			return _target_route(world, active_ship_id, id)
		var assets: Array[String] = []
		for station in world.state.stations:
			if station.sector == id:
				assets.append("Station · %s" % str(station.name))
		for vessel in world.state.ships:
			if vessel.sector == id:
				assets.append("Ship · %s" % str(vessel.name))
		return "%s\nOwner: %s\n\n%s" % [sector.name, sector.owner, "No known objects in this sector." if assets.is_empty() else "\n".join(assets)]
	if kind in ["ship", "npc_ship"]:
		var ship: Dictionary = world._find_ship(id)
		match tab:
			"Orders":
				var queued: Array[String] = []
				for item in ship.orders:
					queued.append(_sector_name(world, str(item.destination)))
				return "%s · %s\nCaptain: %s\nActive role: %s\nOrders: %s\n\n%s" % [ship.name, ship.status, ship.captain, ship.role, "None" if queued.is_empty() else " → ".join(queued), _target_route(world, active_ship_id, selected_sector)]
			"Cargo":
				var stock: Array[String] = _stock_lines(world, ship.cargo)
				return "%s\nCargo capacity: %d / %d\nCivilian passengers: %d\n%s" % [ship.name, world.cargo_volume(id), int(ship.cargo_capacity), int(ship.get("settler_passengers", 0)), "Empty" if stock.is_empty() else "\n".join(stock)]
			"Crew":
				var pilot: Dictionary = ship.captain_profile
				var staff: Dictionary = ship.crew_profile
				var pay: Dictionary = ship.payroll
				return "%s\nCaptain: %s\nPilot skill: %d / 5 · XP: %d\nPilot morale: %d / 100\nService crew: %d / %d berths\nCrew skill: %d / 5 · XP: %d\nCrew morale: %d / 100\nPassengers: %d · Free transport berths: %d\nWages: %d CR per %d ticks\nArrears: %d CR" % [ship.name, ship.captain, int(pilot.skill), int(pilot.experience), int(pilot.morale), int(ship.crew), world.personnel.capacity(ship), int(staff.skill), int(staff.experience), int(staff.morale), int(ship.get("settler_passengers", 0)), world.settlement.free_berths(world, ship), world.personnel._ship_wages(ship), world.personnel.PAYROLL_TICKS, int(pay.arrears)]
			"Trade":
				return "Command ship: %s\nCargo: %d / %d\nSelect a station in the map to inspect its market, or open trade for this ship.\nAutomatic trading and supply roles remain managed separately." % [ship.name, world.cargo_volume(id), int(ship.cargo_capacity)]
	if kind in ["station", "npc_station"]:
		var station: Dictionary = world._find_station(id)
		match tab:
			"Trade":
				var markets: Array[String] = []
				for ware in world.state.wares:
					var sells: String = "%d CR" % int(station.sell_prices[ware.id]) if station.sell_prices.has(ware.id) else "—"
					var buys: String = "%d CR" % int(station.buy_prices[ware.id]) if station.buy_prices.has(ware.id) else "—"
					if sells != "—" or buys != "—":
						markets.append("%s · sells %s · buys %s" % [ware.name, sells, buys])
				return "%s\nFaction: %s\nMarket credits: %d\n\n%s\n\nSelect Open station trade for real docked transactions." % [station.name, station.owner, int(station.credits), "No current market listings." if markets.is_empty() else "\n".join(markets)]
			"Cargo":
				var stock: Array[String] = _stock_lines(world, station.stock)
				return "%s\nStation storage: %d / %d\n\n%s" % [station.name, world.station_volume(id), int(station.storage_capacity), "Empty" if stock.is_empty() else "\n".join(stock)]
			"Production":
				var cycles: Array[String] = []
				for item in world.production_report(id):
					var detail: String = ""
					if item.name in ["Wastewater & Compost Recycler", "Regenerative Soil Farms"]:
						var input_rows: Array[String] = []
						var output_rows: Array[String] = []
						for ware_id in item.inputs:
							input_rows.append("%d %s" % [int(item.inputs[ware_id]), str(world._find_ware(str(ware_id)).get("name", ware_id))])
						for ware_id in item.outputs:
							output_rows.append("%d %s" % [int(item.outputs[ware_id]), str(world._find_ware(str(ware_id)).get("name", ware_id))])
						detail = "\nPhysical inputs: %s\nPhysical outputs: %s" % [", ".join(input_rows), ", ".join(output_rows)]
					cycles.append("%s\n%s · %d/%d ticks%s" % [item.name, item.status, int(item.progress), int(item.duration), detail])
				for school_id in station.get("education", {}).get("modules", []):
					var school: Dictionary = world.state.education_catalog.get(school_id, {})
					cycles.append("%s\\nStaffed education service · %d seats; no resource production" % [school.get("name", school_id), int(school.get("seats", 0))])
				for habitat in station.get("habitation", []):
					var home: Dictionary = world.state.habitation_catalog.get(str(habitat.id), {})
					cycles.append("%s\n%s · %d energy/60 ticks" % [home.get("name", habitat.id), habitat.status, int(home.get("energy_per_60", 0))])
				return "%s\n\n%s" % [station.name, "No production or residence modules." if cycles.is_empty() else "\n\n".join(cycles)]
			"Population":
				var cohort: Dictionary = world.population.station_cohort(world, id)
				if cohort.is_empty():
					return "No known residents at this station."
				var powered: int = world.habitation.operational_capacity(station, world.state.habitation_catalog)
				var needs: Dictionary = world.provisions.facility_needs(world, station)
				var shortage: String = world.provisions.missing_provision(world, station)
				var occupied: int = world.demographics.residents(cohort) if world.state.has("demographics_version") else int(cohort.cohorts.assigned_workers)
				var free_beds: int = maxi(0, powered - occupied)
				var deficit: int = maxi(0, occupied - powered)
				var resident_needs: Dictionary = world.settlement.resident_needs(occupied)
				var waste_yield: int = world.ecology.recovered_waste(resident_needs)
				var ecology_status: String = "Wastewater & biosolids in stock: %d · Fertile soil: %d\nRecoverable organic waste per successful resident cycle: %d (requires real food and water consumption)\nRecycling and soil agriculture use the normal station Production modules; neither creates stock without physical inputs." % [int(station.stock.get("organic_waste", 0)), int(station.stock.get("fertile_soil", 0)), waste_yield]
				var families: int = world.demographics.known_households(world, station, int(cohort.cohorts.assigned_workers)) if world.state.has("demographics_version") else 0
				var born: int = int(cohort.get("family", {}).get("births_total", 0))
				var grown: int = int(cohort.get("family", {}).get("grown_total", 0))
				var family_info: String = "Households: %d · Birth readiness: %d/%d ticks · Recorded births: %d · Youth matured: %d\nFamily Habitats, two settled adults, adequate food/water/medical care and a free powered bed permit births. Children and school-age youths count toward bed occupancy; actual staffed schools provide introductory civilian credentials; full professional licensing follows later." % [families, int(cohort.get("family", {}).get("birth_progress", 0)), world.demographics.BIRTH_INTERVAL, born, grown]
				return "%s\nKnown available workers: %d\nChildren: %d · Students: %d · Assigned: %d\nHousing: %d physical · %d powered · %d occupied · %d free powered beds\nShelter deficit: %d\nLife support: %s\nConsumption/60 ticks: Energy %d · Water %d · Food %d · Medical %d\nResident share: Water %d · Food %d · Medical %d (additional to module baseline)\nResident status: %s · Critical cycles: %d\n%s\n%s\nNew births are medically gated in Family Habitats; immigration still uses real passenger ships, while staffed on-site Education modules provide paid foundational learning." % [station.name, int(cohort.cohorts.available_workers), int(cohort.cohorts.children), int(cohort.cohorts.students), occupied, int(cohort.hab_capacity), powered, occupied, free_beds, deficit, cohort.housing_status, int(needs.get("energy_cells", 0)), int(needs.get("potable_water", 0)), int(needs.get("food_rations", 0)), int(needs.get("medical_supplies", 0)), int(resident_needs.get("potable_water", 0)), int(resident_needs.get("food_rations", 0)), int(resident_needs.get("medical_supplies", 0)), str(cohort.get("resident_status", "Unoccupied")), int(cohort.get("resident_alert_cycles", 0)), "Next shortage: " + shortage if not shortage.is_empty() else "No current service-stock shortages", "Emergency response: resupply or dock an owned ship and use Ship & Crew > Evacuate residents." if deficit > 0 or int(cohort.get("resident_alert_cycles", 0)) > 0 else "Residents are conserved through supply cycles."] + "\n" + ecology_status + "\n" + family_info
			"Education":
				var school: Array[String] = world.education.report(world, id)
				return "%s\\n%s\\nClasses run only with a physical school, resident adults appointed as instructors, actual youths/adults enrolled, records, station power and funded salaries. Certificates are foundational course records; specialist licences and ship skill transfers are not implemented." % [station.name, "No built school modules. Use the station planner to build a school alongside powered residential housing." if station.get("education", {}).get("modules", []).is_empty() else "\\n\\n".join(school)]
			"Construction":
				var jobs: Array[String] = []
				for site in world.state.build_sites:
					if str(site.station_id) == id:
						jobs.append("%s · %d/%d modules · %s" % [site.name, int(site.completed), site.tasks.size(), site.status])
				return "%s\n%s\nConstruction is carried out by hired builders using paid materials and work ticks." % [station.name, "No active build queue at this station." if jobs.is_empty() else "\n".join(jobs)]
			"Research":
				return "%s\nResearch laboratory: %s\nResearch projects consume physical notes; merely owning a habitat grants no discoveries." % [station.name, "Installed" if world.research.has_lab(station) else "Not installed"]
			"History":
				var entries: Array[String] = []
				var record: Dictionary = world.archives.definitions.get(id, {})
				for page in record.get("records", []):
					entries.append(str(page.title))
				return "%s · Historical archive\n%s\n\nDock an owned ship to access full records and research history." % [station.name, "Records: " + ", ".join(entries) if not entries.is_empty() else "Records available at the archive"]
	if kind == "site":
		var site: Dictionary = world.construction.find_site(world, id)
		if tab == "Cargo":
			var wares: Array[String] = _stock_lines(world, site.build_storage)
			return "%s\nBuild storage:\n%s" % [site.name, "Empty" if wares.is_empty() else "\n".join(wares)]
		var tasks: Array[String] = []
		for index in range(site.tasks.size()):
			var task: Dictionary = site.tasks[index]
			var state: String = "Complete" if index < int(site.completed) else ("Working" if task.started else "Queued")
			tasks.append("%d. %s · %s · %d/%d ticks" % [index + 1, task.recipe_id, state, int(task.progress), int(task.duration)])
		return "%s\nStatus: %s\n\n%s\n\nSelect Manage build site for delivery and queue controls." % [site.name, site.status, "\n".join(tasks)]
	return info_text


func _target_route(world: RefCounted, ship_id: String, sector_id: String) -> String:
	var ship: Dictionary = world._find_ship(ship_id)
	if ship.is_empty() or ship.owner != world.state.player_faction_id:
		return "Only player-owned ships may receive fly orders."
	var path: Array = world._find_route(str(ship.sector), sector_id)
	if str(ship.sector) == sector_id:
		return "%s is already at %s. Select a different sector." % [ship.name, _sector_name(world, sector_id)]
	if path.is_empty():
		return "No known route from %s to %s." % [_sector_name(world, str(ship.sector)), _sector_name(world, sector_id)]
	return "Command ship: %s\nDestination: %s\nRoute: %s\nExpected travel: %d ticks, after existing queued orders\nTap Queue fly order to commit. Selecting or panning the map never issues a command." % [ship.name, _sector_name(world, sector_id), " → ".join(path), maxi(0, path.size() - 1) * world.TICKS_PER_CROSSING]
