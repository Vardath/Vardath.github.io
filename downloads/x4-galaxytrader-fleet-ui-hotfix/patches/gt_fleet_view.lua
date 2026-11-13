--[[
GalaxyTrader fleet screen - FleetView
Renders a FleetModel projection into a MapMenu info frame with the widgets and styling of the native
map panels (menu_map createObjectList, createInfoSubmenu, the logbook pager, menu_diplomacy sort headers):
title band (title, live status line, notices, Refresh) on top, then the controls band
(grouping, role filter, search, pager, multi-selection), selected-ship detail pinned at the
bottom, ship list as the scroll viewport between them. The list is the frame's first table so
MapMenu binds it as menu.infoTable. No data access, eligibility or mutation here; controls only
report FleetModel intents through ctx.onIntent.

List rows carry rowdata { ROW_TAG, shipId }; column LIST_COLS is the multi-selection check box.
Group header rows carry no rowdata and are not selectable.
]]

local FleetView = { ROW_TAG = "gt_fleet_ship", PILOT_TAG = "gt_fleet_pilot" }

local TXT = {
    title = 8000, shipId = 8100, pilot = 8101, ship = 8102, location = 8108, refresh = 8200,
    role = 8602, subordinate = 8603, loading = 8604, empty = 8605, malformed = 8606,
    unsupported = 8607, selectHint = 8610, noPilot = 8613, notRegistered = 8614,
    commander = 8615, shipGone = 8616, actions = 8704,
    groupNone = 8680, groupCommander = 8681, groupHomeStation = 8682, groupHomeSector = 8683,
    groupRole = 8684, independent = 8685, noHomeStation = 8686, noHomeSector = 8687, groupFleet = 8850,
    groupTotal = 8688, allRoles = 8689, searchHint = 8690, matching = 8691, previous = 8692, next = 8693,
    noMatch = 8694, markedCount = 8695, markedGone = 8696, markAll = 8697, clearMarked = 8698, markColumn = 8699,
    -- ticket 04 qualification (ids 8740-8753; "Status" and "Unknown" reuse the existing 8103 and 8629).
    qualification = 8740, shipClass = 8741, pilotLevel = 8742, requiredLevel = 8743, qualified = 8744,
    unqualified = 8745, status = 8103, researchNeeded = 8747, researchTier = 8748, unknownPilot = 8749,
    unknownClass = 8750, onlyUnqualified = 8751, showAll = 8752, qualSummary = 8753,
    -- ticket 05 detail section. Training and the home labels reuse existing texts (30010 Home Station,
    -- 31011 Home Sector); the home values are the ticket 03 row fields.
    activity = 8617, destination = 8618, cargo = 8619, home = 31011, homeStation = 30010, buy = 8630, sell = 8631,
    showOnMap = 8632, openOrders = 8633, unknown = 8629,
    -- ticket 06 attention view and activity filter (ids 8790-8806; "Unqualified" reuses 8745, "Show all ships" 8752).
    attention = 8790, attentionCount = 8791, allActivities = 8792, lasting = 8803, lastingAtLeast = 8804,
    noDuration = 8805, staleReason = 8806,
    -- fleet commander filter
    commanderCount = 8848, onlyCommanders = 8849,
    -- ticket 08 bulk edit (ids 8760-8786; "Close" reuses 8205, "Unknown" 8629).
    editRange = 8760, editScope = 8761, keep = 8762, current = 8763, mixed = 8764, previewSummary = 8765,
    apply = 8766, cancel = 8767, close = 8205, changeLine = 8768, now = 8769, afterQueued = 8770,
    appliedSummary = 8784, autoRange = 8785,
    -- ticket 09 (ids 8820-8823; yes/no reuse the native order editor's 1001/2617 and 1001/2618).
    editNotifications = 8820, editTrading = 8821, mixedYesNo = 8822,
    -- Pilots and Profit tabs (ids 8825-8838; column and empty texts reuse the former pilot overview's 81xx/83xx/84xx).
    tabFleet = 8825, tabPilots = 8826, tabProfit = 8358, rank = 8104, level = 8105, xp = 8106, lifetimeProfit = 8107,
    tradeCount = 8113, profit = 8358, noPilots = 8400, fleetSummary = 8831, profitByShip = 8832, profitByWare = 8833,
    averageProfit = 8834, ware = 8835, noProfit = 8836, gtShips = 8837, wareSince = 8838,
    -- Pilot exchange from the Pilots tab: marked count, the two planner buttons and their mouse-over texts.
    markedExchange = 8839, exchangeMarked = 8840, exchangeAll = 8841, exchangeMarkedHint = 8842, exchangeAllHint = 8843,
    -- Pilots tab qualification filter ("All Pilots" and "No pilots match filter" are the former overview's).
    allPilots = 8300, noPilotMatch = 8401, overqualified = 8844, fitHint = 8845,
    -- Pilots tab status filter.
    allStatuses = 8846, pilotTotal = 8847,
}
local PILOT_STATUS = { active = 8827, paused = 8828, ejected = 8829, crew = 8830 }
-- Rank titles: global.$GT_Config.$XP.$TraderTitles index 1..6 is text 6000 + index.
local RANK_TEXT_BASE = 6000
local TABS = {
    { id = "fleet", text = TXT.tabFleet, icon = "mapst_ol_fleets" },
    { id = "pilots", text = TXT.tabPilots, icon = "pi_personnelmanagement" },
    { id = "profit", text = TXT.tabProfit, icon = "pi_statistics" },
}
-- Bulk actions of the summary band, shown while more than one ship is selected. `setting` is a
-- GT_FleetBulkEdit.SETTINGS id and edits only the selected fleet commanders (subordinates follow their
-- commander); rename opens the GT rename dialog for every selected ship. Pilot exchange is on the Pilots tab.
local BULK_ACTIONS = {
    { kind = "rename", icon = "menu_edit", text = 9001 },
    { kind = "edit", setting = "trading", icon = "order_traderoutine", text = TXT.editTrading },
    { kind = "edit", setting = "notifications", icon = "logbook_notifications", text = TXT.editNotifications },
    { kind = "edit", setting = "range", icon = "mapst_ao_default_global", text = TXT.editRange },
}
local EDIT_STATUS = {
    change = 8771, same = 8772, skipped = 8773, applied = 8774, rejected = 8775, incompatible = 8776, unknown = 8629,
}
-- Page 77000 text ids, or { page, id } for a game text (Undock is the vanilla order name).
local ACTIVITY_TEXT = {
    working = 8621, waiting = 8622, searching = 8623, training = 8302, repair = 8625,
    resupply = 8626, retreat = 8627, exchange = 8628, undocking = { 1041, 531 }, unknown = 8629,
}
-- One text per GT_FleetModel.ATTENTION code.
local REASON_TEXT = {
    unqualified = 8745, training_funds = 8800, training_station = 8801, funds = 8794, no_trade = 8793,
    trade_rules = 8795, route_blocked = 8796, no_home = 8797, unreachable = 8798, cargo_unsellable = 8799,
    no_trade_unknown = 8802,
}
-- Ship action buttons are icons; the action label is their mouse-over text.
local ACTION_ICONS = {
    diagnose = "menu_info", academy = "vt_reward_crewskill", rename = "menu_edit", promote = "order_assigncommander",
}
local SHOW_ON_MAP_ICON, OPEN_ORDERS_ICON = "mapst_mission_guidance", "mapst_orderqueue"
-- The selected ship's row ends with its action icons: the two native jumps, then the GT ship actions.
local ROW_ACTION_COLS = 2 + #GT_FleetActions.LIST
local ALL = "all"
local ALL_ACTIVITIES = "all_activities"
local ALL_STATUSES = "all_statuses"
-- Ship, Role, Pilot, the row action icons, selection check box (always last). A qualification badge column
-- (while qualification is shown) and an attention column (while the Attention needed filter is on) precede
-- the action icons.
local LIST_COLS = 5 + ROW_ACTION_COLS
local GROUPINGS = {
    { id = "none", text = TXT.groupNone }, { id = "commander", text = TXT.groupCommander },
    { id = "fleet", text = TXT.groupFleet },
    { id = "homeStation", text = TXT.groupHomeStation }, { id = "homeSector", text = TXT.groupHomeSector },
    { id = "role", text = TXT.groupRole },
}
local NONE_GROUP = { commander = TXT.independent, fleet = TXT.independent, homeStation = TXT.noHomeStation,
                     homeSector = TXT.noHomeSector }

local T = GT_UI.text

local function activityLabel(activity)
    local text = ACTIVITY_TEXT[activity]
    if type(text) == "table" then
        return GT_UI.safeReadText(text[1], text[2])
    end
    return T(text)
end

-- menu_map config.mapRowHeight
local ROW_HEIGHT = GT_UI.DEFAULTS.rowHeight

-- `short` drops the brand every locale's GT order name starts with ("GalaxyTrader MK1 Sales" -> "MK1 Sales").
local function roleText(row, short)
    local role = row.roleName or row.roleOrderId
    if short then
        role = string.gsub(role, "^GalaxyTrader ", "")
    end
    return row.isSubordinate and T(TXT.subordinate, role) or role
end

local function pilotText(row)
    if row.pilotName then
        return row.pilotName
    end
    return row.pilotId and "?" or T(TXT.noPilot)
end

local function shipLabel(name, idcode)
    return idcode and (name .. " (" .. idcode .. ")") or name
end

-- Qualification badge of a list row (only while qualification is shown). Qualified ships carry none.
-- Facts come from the snapshot row; the view holds no thresholds.
local function badgeCell(row)
    local q = row.qualification
    if q.state == "unqualified" then
        return T(TXT.unqualified), Color["text_warning"]
    elseif q.state == "qualified" then
        return q.researchTier > 0 and T(TXT.researchNeeded) or ""
    end
    return "?"
end

-- Attention texts: reason, and how long it has lasted up to the snapshot (unknown when no start was recorded).
local function reasonText(reason)
    return T(REASON_TEXT[reason.code])
end

local function durationText(reason)
    if not reason.duration then
        return T(TXT.noDuration)
    end
    return T(reason.sinceExact and TXT.lasting or TXT.lastingAtLeast, ConvertTimeString(reason.duration, "%h:%M:%S"))
end

-- Number of list columns: the badge column exists only while qualification is shown, the attention
-- column only while the Attention needed filter is on.
-- Compact Fleet layout retains core columns (ship, role, pilot, home, select)
-- and never asks a narrow Map panel to reserve seven fixed-width icon cells.
local function compactList(ctx)
    local icon = Helper.scaleY(ROW_HEIGHT)
    local text = Helper.scaleX(85)
    local required = (ROW_ACTION_COLS + 1) * icon + 4 * text + 32
    return (tonumber(ctx.width) or 0) < required
end

local function listColumns(projection, compact)
    local cols = compact and 5 or LIST_COLS
    if projection.qualification.shown then
        cols = cols + 1
    end
    if projection.filters.attention then
        cols = cols + 1
    end
    return cols
end

-- Width percents of the text columns but the last one, which takes the rest; the check box column has a
-- fixed width.
local function listPercents(projection)
    local badge, attention = projection.qualification.shown, projection.filters.attention
    if badge and attention then
        return { 19, 12, 11, 11, 10 }
    elseif badge then
        return { 26, 17, 16, 15 }
    elseif attention then
        return { 22, 14, 13, 13 }
    end
    return { 32, 20, 18 }
end

-- Group header inside the scroll list, styled as a native property section title (not fixed: fixed rows
-- pin to the top).
local function addGroupRow(list, group, groupBy, cols)
    local name
    if group.key == nil then
        name = T(NONE_GROUP[groupBy])
    else
        name = shipLabel(group.name or "?", group.idcode)
    end
    GT_UI.addSectionRow(list, T(TXT.groupTotal, name, group.count), cols)
end

-- Sortable column header bound to a FleetModel / FleetOverview sort intent.
local function addSortHeader(cell, text, column, sort, intent)
    GT_UI.addSortHeader(cell, text, { active = sort.column == column, descending = sort.descending,
                                      onClick = function() intent("setSort", column) end })
end

local function addHeaderText(cell, text, mouseOverText)
    cell:createText(text, { halign = "center", cellBGColor = Color["row_title_background"], mouseOverText = mouseOverText })
end

-- Why an action is not available (or the state of its request); "" when there is nothing to say.
local function actionNote(item)
    if not item.note then
        return ""
    end
    if item.noteArg then
        return T(item.note, T(item.noteArg))
    end
    return T(item.note)
end

-- The action icons of one ship row, from column `first`: Show on map, Open orders, then the GT ship actions
-- with their availability (ctx.actions). The label and the note are the mouse-over text. The Trading Academy
-- is left out in vanilla XP mode, where it has no effect.
local function addRowActions(added, first, row, ctx, vanillaXp)
    local shipId = row.id
    GT_UI.iconButton(added[first], SHOW_ON_MAP_ICON, { mouseOverText = T(TXT.showOnMap), onClick = function() ctx.onShowMap(shipId) end })
    GT_UI.iconButton(added[first + 1], OPEN_ORDERS_ICON, { mouseOverText = T(TXT.openOrders), onClick = function() ctx.onOpenOrders(shipId) end })
    local col = first + 1
    for _, item in ipairs(ctx.actions(row)) do
        if not (vanillaXp and item.id == "academy") then
            local icon = assert(ACTION_ICONS[item.id], "[GT Fleet] no icon for action " .. tostring(item.id))
            local note = actionNote(item)
            local tip = note ~= "" and (T(item.label) .. " - " .. note) or T(item.label)
            col = col + 1
            GT_UI.iconButton(added[col], icon, { mouseOverText = tip, onClick = function() ctx.onAction(shipId, item.id) end, active = item.state == "available" })
        end
    end
    -- Fewer actions can be shown when vanilla XP hides the Academy.
    -- Fill every unused action cell so widget CreateTable never sees nil.
    local last = first + ROW_ACTION_COLS - 1
    if col < last then
        added[col + 1]:setColSpan(last - col):createText("")
    end
end

local function addListRows(list, projection, intent, ctx)
    local compact = compactList(ctx)
    local cols = listColumns(projection, compact)
    local firstAction = cols - (compact and 0 or ROW_ACTION_COLS)
    local badge = projection.qualification.shown
    local ready = projection.status == "ready"
    local header = list:addRow(ready or nil, { fixed = true })
    local col = 0
    for _, h in ipairs({ { TXT.ship, "name" }, { TXT.role, "role" }, { TXT.pilot, "pilot" }, { TXT.home, "sector" } }) do
        col = col + 1
        if ready then
            addSortHeader(header[col], T(h[1]), h[2], projection.sort, intent)
        else
            addHeaderText(header[col], T(h[1]))
        end
    end
    if badge then
        col = col + 1
        addHeaderText(header[col], T(TXT.qualification))
    end
    local attention = projection.filters.attention and projection.attention.byId
    if attention then
        col = col + 1
        addHeaderText(header[col], T(TXT.attention))
    end
    if not compact then
        addHeaderText(header[firstAction]:setColSpan(ROW_ACTION_COLS), T(TXT.actions))
    end
    -- The check box column is one row height wide: its title is the mouse-over text.
    addHeaderText(header[cols], "", T(TXT.markColumn))
    local message
    if projection.status == "loading" then
        message = T(TXT.loading)
    elseif projection.status == "error" then
        message = T(projection.error == "unsupported" and TXT.unsupported or TXT.malformed)
    elseif projection.status == "empty" then
        message = T(TXT.empty)
    elseif #projection.rows == 0 then
        message = T(TXT.noMatch)
    end
    if message then
        list:addRow(false, { interactive = false })[1]:setColSpan(cols):createText(message, { halign = "center" })
        return nil
    end
    local page = projection.page
    local groupAt = {}
    for _, group in ipairs(projection.groups or {}) do
        groupAt[group.first] = group
        if group.first < page.first and group.first + group.count > page.first then
            groupAt[page.first] = group
        end
    end
    local selectedIndex
    for i = page.first, page.last do
        local row = projection.rows[i]
        if groupAt[i] then
            addGroupRow(list, groupAt[i], projection.groupBy, cols)
        end
        local added = list:addRow({ FleetView.ROW_TAG, row.id }, {})
        added[1]:createText(shipLabel(row.name, row.idcode), { x = Helper.standardTextOffsetx })
        added[2]:createText(roleText(row, true))
        added[3]:createText(pilotText(row))
        local sector = row.homeSectorName or T(TXT.unknown)
        added[4]:createText(row.fleetStationName and (row.fleetStationName .. " - " .. sector) or sector)
        local col = 4
        if badge then
            col = col + 1
            local text, color = badgeCell(row)
            added[col]:createText(text, { color = color })
        end
        if attention then
            col = col + 1
            local main = attention[row.id].reasons[1]
            added[col]:createText(reasonText(main) .. " - " .. durationText(main), { color = Color["text_warning"] })
        end
        -- The widget system shares 200 buttons across every open map panel: icons on all 50 rows of a page
        -- would exhaust them, so only the selected ship's row carries its actions.
        if not compact then
            if projection.selected == row then
                addRowActions(added, firstAction, row, ctx, projection.vanillaXp)
            else
                -- Every non-selected row must supply valid content for all
                -- unused action columns; a span preserves a blank region.
                added[firstAction]:setColSpan(ROW_ACTION_COLS):createText("")
            end
        end
        local shipId = row.id
        added[cols]:createCheckBox(projection.marked.ids[shipId] == true, { width = ROW_HEIGHT, height = ROW_HEIGHT })
        added[cols].handlers.onClick = function(_, checked) intent("setMarked", shipId, checked) end
        if projection.selected == row then
            selectedIndex = added.index
        end
    end
    return selectedIndex
end

-- Detail value texts. A field the snapshot did not observe reads as unknown, never as idle,
-- empty or healthy.
local function unknownText()
    return T(TXT.unknown)
end

local function activityText(row)
    return activityLabel(row.activity)
end

local function destinationText(row)
    if not row.destinationName then
        return unknownText()
    end
    local where = row.destinationSector and (row.destinationName .. ", " .. row.destinationSector) or row.destinationName
    if row.destinationLeg == "buy" then
        return T(TXT.buy, where)
    elseif row.destinationLeg == "sell" then
        return T(TXT.sell, where)
    end
    return where
end

local function number(n)
    return ConvertIntegerString(math.floor(n + 0.5), true, 0, true)
end

local function cargoText(row)
    if not row.cargoCapacity then
        return unknownText()
    end
    local text = number(row.cargoUsed) .. " / " .. number(row.cargoCapacity)
    local wares = {}
    for i, ware in ipairs(row.cargoWares) do
        wares[i] = ware.name .. " x" .. number(ware.count)
    end
    if #wares > 0 then
        text = text .. " - " .. table.concat(wares, ", ")
    end
    return text
end

-- Label / value row of the detail pane, laid out as the native object info rows (menu_map addInfoSubmenuRow).
local function addInfoLine(detail, label, value, color)
    local row = detail:addRow(false, {})
    row[1]:createText(label, { x = Helper.standardTextOffsetx + Helper.standardIndentStep })
    row[2]:createText(value, { halign = "right", wordwrap = true, color = color })
end

-- Fleet name of the ship's top-level fleet, editable in place: a confirmed change renames the fleet (also one
-- attached to a station, where the native map offers no rename).
local function addFleetRow(detail, row, ctx)
    local label = GT_UI.safeReadText(1001, 9919)
    if not row.fleetCommanderId then
        addInfoLine(detail, label, "-")
        return
    end
    local line = detail:addRow(true, {})
    line[1]:createText(label, { x = Helper.standardTextOffsetx + Helper.standardIndentStep })
    local current, commanderId = row.fleetName or "", row.fleetCommanderId
    line[2]:createEditBox({ description = GT_UI.safeReadText(1001, 7895), height = ROW_HEIGHT })
        :setText(current, { halign = "right" })
    line[2].handlers.onEditBoxActivated = function() ctx.onEditing(true) end
    line[2].handlers.onEditBoxDeactivated = function(_, text, _, isconfirmed)
        ctx.onEditing(false)
        if isconfirmed and text ~= "" and text ~= current then
            ctx.onRenameFleet(commanderId, text)
        end
    end
end

-- Information section of the detail pane (ticket 05).
local function addInfoRows(detail, row, ctx)
    local function line(labelId, value)
        addInfoLine(detail, T(labelId), value)
    end
    line(TXT.ship, row.name)
    line(TXT.shipId, row.idcode)
    addFleetRow(detail, row, ctx)
    line(TXT.role, roleText(row))
    if row.isSubordinate then
        line(TXT.commander, row.commanderName or unknownText())
    end
    line(TXT.activity, activityText(row))
    line(TXT.destination, destinationText(row))
    line(TXT.cargo, cargoText(row))
    local pilot = row.pilotName or (row.pilotId and unknownText() or T(TXT.noPilot))
    if row.pilotId and not row.pilotKnown then
        line(TXT.pilot, pilot .. " (" .. T(TXT.notRegistered) .. ")")
    else
        line(TXT.pilot, pilot)
    end
    if row.homeStationName then
        line(TXT.homeStation, row.homeStationName)
    end
    line(TXT.home, row.homeSectorName or unknownText())
    line(TXT.location, row.sector or unknownText())
end

-- Information section of the detail pane. Navigation and the gameplay actions are icons on the ship's
-- list row (addRowActions).
local function addDetailRows(detail, projection, ctx)
    local row = projection.selected
    if not row then
        if projection.selectedGone then
            GT_UI.addCaptionRow(detail, T(TXT.shipGone), { colSpan = 2, halign = "left", fixed = false })
        elseif projection.status == "ready" then
            GT_UI.addCaptionRow(detail, T(TXT.selectHint), { colSpan = 2, halign = "left", fixed = false })
        end
        return
    end
    addInfoRows(detail, row, ctx)
end

-- Qualification section of the detail pane (its own section, only while qualification is shown).
-- Every fact is the snapshot's: state, class and levels come from the shared MD read, so unknown
-- pilot / unknown class are reported as unknown and never as qualified or unqualified. No penalty
-- or installed-effect line exists: the snapshot carries no authoritative data for them.
local function addQualificationRows(detail, projection)
    local row = projection.selected
    if not row or not projection.qualification.shown then
        return
    end
    local q = row.qualification
    GT_UI.addSectionRow(detail, T(TXT.qualification), 2)
    local function line(labelId, value)
        addInfoLine(detail, T(labelId), value)
    end
    local function note(text)
        GT_UI.addCaptionRow(detail, text, { colSpan = 2, halign = "left", fixed = false })
    end
    local status, color = T(TXT.unknown), nil
    if q.state == "unqualified" then
        status, color = T(TXT.unqualified), Color["text_warning"]
    elseif q.state == "qualified" then
        status = q.researchTier > 0 and T(TXT.researchNeeded) or T(TXT.qualified)
    end
    addInfoLine(detail, T(TXT.status), status, color)
    if q.class then
        line(TXT.shipClass, string.upper(q.class))
    end
    if q.pilotLevel then
        line(TXT.pilotLevel, tostring(q.pilotLevel))
    end
    if q.requiredLevel then
        line(TXT.requiredLevel, tostring(q.requiredLevel))
    end
    if q.state == "unknown_pilot" then
        note(T(TXT.unknownPilot))
    elseif q.state == "unknown_class" then
        note(T(TXT.unknownClass))
    elseif q.state == "qualified" and q.researchTier > 0 then
        note(T(TXT.researchTier, tostring(q.researchTier)))
    end
end

-- Search, grouping, filter, paging and multi-selection controls (only with an accepted snapshot).
local function dropdownOption(id, text)
    return { id = id, text = text, icon = "", displayremoveoption = false }
end

-- Controls grid: two wide columns, then the clear-search and pager icon columns around the page number
-- (the native logbook search / pager row). Wider controls span columns 3 to 8.
local CONTROL_COLS = 8
local ICON_COLS = { 3, 4, 5, 7, 8 }

local function setupControlColumns(controls)
    controls:setColWidthPercent(1, 30)
    controls:setColWidthPercent(2, 30)
    for _, col in ipairs(ICON_COLS) do
        controls:setColWidth(col, Helper.scaleY(ROW_HEIGHT), false)
    end
end

local function addFilterRow(controls, projection, intent, ctx)
    local row = controls:addRow(true, { fixed = true })
    local groupings = {}
    for _, g in ipairs(GROUPINGS) do
        groupings[#groupings + 1] = dropdownOption(g.id, T(g.text))
    end
    GT_UI.dropDown(row[1], groupings, projection.groupBy, function(id) intent("setGroup", id) end, nil, ctx.onEditing)
    local roles = { dropdownOption(ALL, T(TXT.allRoles)) }
    for _, role in ipairs(projection.roles) do
        roles[#roles + 1] = dropdownOption(role.id, T(TXT.groupTotal, role.name, role.count))
    end
    GT_UI.dropDown(row[2], roles, projection.filters.role or ALL, function(id)
        intent("setFilter", "role", id ~= ALL and id or nil)
    end, nil, ctx.onEditing)
    local activities = { dropdownOption(ALL_ACTIVITIES, T(TXT.allActivities)) }
    for _, activity in ipairs(projection.activities) do
        activities[#activities + 1] = dropdownOption(activity.id,
            T(TXT.groupTotal, activityLabel(activity.id), activity.count))
    end
    GT_UI.dropDown(row[3]:setColSpan(CONTROL_COLS - 2), activities, projection.filters.activity or ALL_ACTIVITIES, function(id)
        intent("setFilter", "activity", id ~= ALL_ACTIVITIES and id or nil)
    end, nil, ctx.onEditing)
end

local function addSearchRow(controls, projection, intent, ctx)
    local row = controls:addRow(true, { fixed = true })
    row[1]:setColSpan(2):createEditBox({ description = T(TXT.searchHint), defaultText = T(TXT.searchHint), height = ROW_HEIGHT })
        :setText(projection.search, { halign = "left", x = Helper.standardTextOffsetx })
    row[1].handlers.onEditBoxActivated = function() ctx.onEditing(true) end
    row[1].handlers.onEditBoxDeactivated = function(_, text)
        ctx.onEditing(false)
        intent("setSearch", text)
    end
    GT_UI.iconButton(row[3], "widget_cross_01", { onClick = function() intent("setSearch", "") end })

    local page = projection.page
    local back, forward = page.number > 1, page.number < page.count
    GT_UI.iconButton(row[4], "widget_arrow_skip_left_01", { onClick = function() intent("setPage", 1) end, active = back })
    GT_UI.iconButton(row[5], "widget_arrow_left_01", { mouseOverText = T(TXT.previous), onClick = function() intent("setPage", page.number - 1) end, active = back })
    row[6]:createText(page.number .. " / " .. page.count, { halign = "center" })
    GT_UI.iconButton(row[7], "widget_arrow_right_01", { mouseOverText = T(TXT.next), onClick = function() intent("setPage", page.number + 1) end, active = forward })
    GT_UI.iconButton(row[8], "widget_arrow_skip_right_01", { onClick = function() intent("setPage", page.count) end, active = forward })
end

local function addControlRows(controls, projection, intent, ctx)
    addFilterRow(controls, projection, intent, ctx)
    addSearchRow(controls, projection, intent, ctx)
end

-- Filter band below the controls: each summary line with its filter toggle directly after it.
local SUMMARY_COLS = 3

local function addSummaryTable(frame, projection, intent, ctx, y)
    local summary = GT_UI.addPanelTable(frame, SUMMARY_COLS, ctx.width, ctx.frameborder, { tabOrder = 5, y = y, reserveScrollBar = false })
    summary:setColWidthPercent(1, 35)
    summary:setColWidth(2, Helper.scaleY(ROW_HEIGHT), false)

    local lines = {}
    local qualification = projection.qualification
    if qualification.shown then
        local active = projection.filters.unqualified == true
        lines[#lines + 1] = { text = T(TXT.qualSummary, qualification.unqualified, qualification.research, qualification.unknown),
                              icon = "menu_filter", tip = T(active and TXT.showAll or TXT.onlyUnqualified), selected = active,
                              toggle = function() intent("setFilter", "unqualified", (not active) or nil) end }
    end
    local attention = projection.filters.attention == true
    lines[#lines + 1] = { text = T(TXT.attentionCount, projection.attention.count), icon = "menu_warning",
                          tip = T(attention and TXT.showAll or TXT.attention), selected = attention,
                          toggle = function() intent("setFilter", "attention", (not attention) or nil) end }
    local commanders = projection.filters.commanders == true
    lines[#lines + 1] = { text = T(TXT.commanderCount, projection.commanders), icon = "menu_filter",
                          tip = T(commanders and TXT.showAll or TXT.onlyCommanders), selected = commanders,
                          toggle = function() intent("setFilter", "commanders", (not commanders) or nil) end }

    for _, line in ipairs(lines) do
        local row = summary:addRow(true, { fixed = true })
        row[1]:createText(line.text, { wordwrap = true })
        GT_UI.iconButton(row[2], line.icon, { mouseOverText = line.tip, onClick = line.toggle, selected = line.selected })
    end
    return summary
end

-- Selection band below the filters: matching and selected counts, select all / clear, and the bulk actions
-- right-aligned on the selected line while more than one ship is selected.
local SELECTION_COLS = 3 + #BULK_ACTIONS

local function addSelectionTable(frame, projection, intent, ctx, y)
    local selection = GT_UI.addPanelTable(frame, SELECTION_COLS, ctx.width, ctx.frameborder, { tabOrder = 6, y = y, reserveScrollBar = false })
    selection:setColWidthPercent(1, 30)
    selection:setColWidthPercent(2, 30)
    for col = 4, SELECTION_COLS do
        selection:setColWidth(col, Helper.scaleY(ROW_HEIGHT), false)
    end

    local page = projection.page
    selection:addRow(false, { fixed = true })[1]:setColSpan(SELECTION_COLS)
        :createText(T(TXT.matching, #projection.rows, projection.total, page.number, page.count))

    local marked = projection.marked
    local row = selection:addRow(true, { fixed = true })
    row[1]:setColSpan(3):createText(T(TXT.markedCount, marked.shown + marked.hidden, marked.hidden))
    if #marked.rows > 1 then
        local shipIds = {}
        for k, r in ipairs(marked.rows) do
            shipIds[k] = r.id
        end
        local canEdit = ctx.edit() == nil and #GT_FleetBulkEdit.commanders(marked) > 0
        for k, action in ipairs(BULK_ACTIONS) do
            local onClick, active
            if action.kind == "rename" then
                onClick = function() ctx.onBulkRename(shipIds) end
            else
                local setting = action.setting
                onClick, active = function() ctx.onEdit("open", setting, marked) end, canEdit
            end
            GT_UI.iconButton(row[3 + k], action.icon, { mouseOverText = T(action.text), onClick = onClick, active = active })
        end
    end
    if marked.gone > 0 then
        selection:addRow(false, { fixed = true })[1]:setColSpan(SELECTION_COLS)
            :createText(T(TXT.markedGone, marked.gone), { color = Color["text_warning"] })
    end
    local matching = {}
    for i, r in ipairs(projection.rows) do
        matching[i] = r.id
    end
    local buttons = selection:addRow(true, { fixed = true })
    GT_UI.createButton(buttons[1], T(TXT.markAll), { onClick = function() intent("markAll", matching) end, fontSize = GT_UI.DEFAULTS.fontSize })
    GT_UI.createButton(buttons[2], T(TXT.clearMarked), { onClick = function() intent("clearMarked") end, active = next(marked.ids) ~= nil or marked.gone > 0, fontSize = GT_UI.DEFAULTS.fontSize })
    return selection
end

-- Attention section of the detail pane (ticket 06), only for a ship with an attention entry: each recorded
-- reason with its duration (a stale one says so). The actions for them are the icons on the ship's row.
local function addAttentionRows(detail, projection)
    local row = projection.selected
    local entry = row and projection.attention.byId[row.id]
    if not entry then
        return
    end
    GT_UI.addSectionRow(detail, T(TXT.attention), 2)
    for _, reason in ipairs(entry.reasons) do
        local line = detail:addRow(false, {})
        line[1]:createText(reasonText(reason), { x = Helper.standardTextOffsetx + Helper.standardIndentStep,
                                                 wordwrap = true, color = Color["text_warning"] })
        line[2]:createText(durationText(reason), { halign = "right" })
        if reason.stale then
            GT_UI.addCaptionRow(detail, T(TXT.staleReason), { colSpan = 2, halign = "left", fixed = false })
        end
    end
end

-- Bulk edit section (ticket 08): replaces the detail pane while an edit is open. Shows the scope,
-- one value choice per field with the current values (mixed when they differ), what Apply would do
-- to each ship, then the per-ship outcome after Apply. Plan facts come from ctx.edit().
local function valueText(scale, value)
    if scale.type == "bool" then
        return GT_UI.safeReadText(1001, value and 2617 or 2618)
    end
    return tostring(value)
end

-- Current values of the compatible ships: one value, or mixed (range for numbers, counts for bool).
local function currentText(field)
    local current = field.current
    if current.count == 0 then
        return "-"
    end
    if field.scale.type == "bool" then
        if current.yes == 0 or current.yes == current.count then
            return valueText(field.scale, current.yes > 0)
        end
        return T(TXT.mixedYesNo, current.yes, current.count - current.yes)
    end
    return current.low == current.high and tostring(current.low) or T(TXT.mixed, current.low, current.high)
end

local function valueOptions(field)
    local options = { dropdownOption("keep", T(TXT.keep)) }
    if field.scale.type == "bool" then
        options[2] = dropdownOption("true", valueText(field.scale, true))
        options[3] = dropdownOption("false", valueText(field.scale, false))
    elseif field.max then
        for value = field.scale.min, field.max, field.scale.step do
            options[#options + 1] = dropdownOption(tostring(value), tostring(value))
        end
    end
    return options
end

local function chosenValue(field, id)
    if id == "keep" then
        return nil
    end
    if field.scale.type == "bool" then
        return id == "true"
    end
    return tonumber(id)
end

local function editShipText(ship)
    if ship.status == "change" then
        local parts = {}
        for i, change in ipairs(ship.changes) do
            local scale = change.field.scale
            parts[i] = T(TXT.changeLine, GT_UI.safeReadText(change.field.page, change.field.text), valueText(scale, change.from), valueText(scale, change.to))
        end
        local text = table.concat(parts, "; ") .. " - "
            .. (ship.queued > 0 and T(TXT.afterQueued, ship.queued) or T(TXT.now))
        if ship.autoRange then
            text = text .. " - " .. T(TXT.autoRange)
        end
        return text
    end
    if not ship.reason then
        return ""
    end
    return T(ship.reason, ship.arg ~= nil and tostring(ship.arg) or "")
end

local function addEditRows(detail, edit, ctx)
    local function text(value)
        detail:addRow(false, {})[1]:setColSpan(2):createText(value, { wordwrap = true })
    end
    local indent = Helper.standardTextOffsetx + Helper.standardIndentStep
    GT_UI.addSectionRow(detail, T(edit.setting.label), 2)
    text(T(TXT.editScope, edit.total, edit.hidden, edit.gone))
    -- Only fields at least one selected ship can take: a field no selected role has is not offered.
    local offered = {}
    for _, field in ipairs(edit.fields) do
        if field.current.count > 0 then
            offered[#offered + 1] = field
        end
    end
    if #offered == 0 then
        GT_UI.addCaptionRow(detail, T(GT_FleetBulkEdit.EDIT_TEXT.noSetting), { colSpan = 2, halign = "left", fixed = false })
    end
    for _, field in ipairs(offered) do
        local row = detail:addRow(true, {})
        row[1]:createText(GT_UI.safeReadText(field.page, field.text) .. " - " .. T(TXT.current, currentText(field)),
                          { x = indent, wordwrap = true })
        local chosen = field.value ~= nil
        if edit.state == "preview" then
            GT_UI.dropDown(row[2], valueOptions(field), chosen and tostring(field.value) or "keep", function(id)
                ctx.onEdit("value", field.param, chosenValue(field, id))
            end, nil, ctx.onEditing)
        else
            row[2]:createText(chosen and valueText(field.scale, field.value) or T(TXT.keep), { halign = "right" })
        end
    end
    local c = edit.counts
    if edit.state == "preview" then
        text(T(TXT.previewSummary, c.change or 0, c.same or 0, c.incompatible or 0, c.skipped or 0, c.rejected or 0))
        local row = detail:addRow(true, { fixed = true })
        local id = edit.id
        GT_UI.createButton(row[1], T(TXT.apply), { onClick = function() ctx.onEdit("apply", id) end, active = edit.canApply, fontSize = GT_UI.DEFAULTS.fontSize })
        GT_UI.createButton(row[2], T(TXT.cancel), { onClick = function() ctx.onEdit("close") end, fontSize = GT_UI.DEFAULTS.fontSize })
    else
        text(T(TXT.appliedSummary, c.applied or 0, c.skipped or 0, c.rejected or 0, c.unknown or 0))
        GT_UI.createButton(detail:addRow(true, { fixed = true })[1], T(TXT.close), { onClick = function() ctx.onEdit("close") end, fontSize = GT_UI.DEFAULTS.fontSize })
    end
    for _, ship in ipairs(edit.ships) do
        local row = detail:addRow(false, {})
        local warn = ship.status == "rejected" or ship.status == "unknown"
        row[1]:createText(shipLabel(ship.row.name, ship.row.idcode), { x = indent, wordwrap = true })
        local status = T(EDIT_STATUS[ship.status])
        local detailText = editShipText(ship)
        row[2]:createText(detailText ~= "" and (status .. ": " .. detailText) or status,
                          { wordwrap = true, color = warn and Color["text_warning"] or nil })
    end
    if edit.pageCount > 1 then
        local row = detail:addRow(true, { fixed = true })
        GT_UI.createButton(row[1], T(TXT.previous), { onClick = function() ctx.onEdit("page", edit.page - 1) end, active = edit.page > 1, fontSize = GT_UI.DEFAULTS.fontSize })
        GT_UI.createButton(row[2], T(TXT.next), { onClick = function() ctx.onEdit("page", edit.page + 1) end, active = edit.page < edit.pageCount, fontSize = GT_UI.DEFAULTS.fontSize })
    end
end

--[[
ctx:
  width, height  info frame size
  status()       live status line text ("" when nothing to report); drawn every frame
  notices        player-visible capability notices (strings)
  onRefresh()    Refresh button handler
  onShowMap(shipId), onOpenOrders(shipId)  native navigation for the selected ship (ticket 05)
  onIntent(name, ...)  view intent; name is a FleetModel intent (setSearch, ...)
  actions(row)   FleetActions items for the selected ship (see GT_FleetActions.describe)
  onAction(shipId, actionId)  action button handler
  edit()         the open bulk edit (GT_FleetBulkEdit.editView) or nil
  onEdit(name, ...)  bulk edit intent: open(settingId, marked) | value(param, n|nil) | apply(planId)
                 | close() | page(n)
  topRow         list top row to restore, or nil
  frameborder    id of the panel frame border the tables attach to
  iconSize       tab button size (the native sidebar width)
  tab            "fleet" | "pilots" | "profit"; onTab(tab) switches
  pilots, profit GT_FleetOverview projections of the Pilots and Profit tabs; onPilotSort(column),
                 onProfitSort(ranking, column)
  onPilotMark(pilotId, on), onPilotClear()  pilot exchange marks; onPilotFilter(fit | nil) qualification filter;
                 onPilotStatus(status | nil) status filter
  onPilotExchange(shipIds | nil)  pilot exchange planner for the marked pilots' ships, or every GT ship (nil)
]]

-- Title, tab row and active tab name as the native property panel draws them (menu_map createPropertyOwned),
-- then the live status line with Refresh and the notices. Shared by every tab.
local TITLE_COLS = #TABS + 2

local function addTitleTable(frame, ctx)
    local gap = Helper.standardContainerOffset
    local title = GT_UI.addPanelTable(frame, TITLE_COLS, ctx.width, ctx.frameborder, { tabOrder = 1, y = gap, reserveScrollBar = false })
    for i = 1, #TABS do
        title:setColWidth(i, ctx.iconSize, false)
    end
    title:setColWidthPercent(TITLE_COLS, 25)
    title:addRow(false, { fixed = true, bgColor = Color["frame_background_black"], borderBelow = false })[1]
        :setColSpan(TITLE_COLS):createText(T(TXT.title), Helper.tabTitleTextProperties)
    local row = title:addRow(true, { fixed = true, bgColor = Color["frame_background_black"], borderBelow = false })
    local activeName, activeCol
    for i, tab in ipairs(TABS) do
        local active = tab.id == ctx.tab
        if active then
            activeName, activeCol = T(tab.text), i
        end
        row[i]:createButton({ width = ctx.iconSize, height = ctx.iconSize, scaling = false, y = gap, mouseOverText = T(tab.text),
                              bgColor = active and Color["row_background_selected"] or Color["row_title_background"] })
            :setIcon(tab.icon)
        row[i].handlers.onClick = function() ctx.onTab(tab.id) end
    end
    row[#TABS + 1]:setColSpan(TITLE_COLS - #TABS):createText(" ", { minRowHeight = ctx.iconSize + 2 * gap, scaling = false })
    -- The widget cursor highlights the selected cell: keep it on the active tab, as the native tab rows do
    -- (menu_map createPropertyOwned tabtable:setSelectedRow / setSelectedCol); otherwise it stays on column 1.
    title:setSelectedRow(row.index)
    title:setSelectedCol(activeCol)
    title:addRow(false, { fixed = true, borderBelow = false })[1]:setColSpan(TITLE_COLS)
        :createText(activeName, Helper.subTabTitleTextProperties)
    row = title:addRow(true, { fixed = true })
    row[1]:setColSpan(TITLE_COLS - 1):createText(ctx.status, { wordwrap = true })
    GT_UI.createButton(row[TITLE_COLS], T(TXT.refresh), { onClick = ctx.onRefresh, fontSize = GT_UI.DEFAULTS.fontSize })
    for _, notice in ipairs(ctx.notices or {}) do
        GT_UI.addCaptionRow(title, notice, { colSpan = TITLE_COLS, halign = "left", fixed = false, color = Color["text_warning"] })
    end
    return title
end

local function credits(n)
    return ConvertIntegerString(n, true, 0, true) .. " " .. ReadText(1001, 101)
end

local function profitColor(n)
    return n < 0 and Color["text_negative"] or nil
end

-- The one scroll list of the Pilots and Profit tabs, below the title table (and the tab's controls, when
-- addControls(controls) is given) and filling the frame.
local function addTabList(frame, ctx, cols, addControls)
    local gap = Helper.standardContainerOffset
    local list = GT_UI.addPanelTable(frame, cols, ctx.width, ctx.frameborder, { tabOrder = 2 })
    local title = addTitleTable(frame, ctx)
    local top = title.properties.y + title:getFullHeight() + gap
    title:addConnection(1, 2, true)
    if addControls then
        local controls = GT_UI.addPanelTable(frame, 3, ctx.width, ctx.frameborder, { tabOrder = 3, y = top, reserveScrollBar = false })
        addControls(controls)
        top = top + controls:getFullHeight() + gap
        controls:addConnection(2, 2)
    end
    list.properties.y = top
    list.properties.maxVisibleHeight = math.max(ctx.height - top - gap, 4 * ROW_HEIGHT)
    list:addConnection(addControls and 3 or 2, 2)
    return list
end

local function addMessageRow(list, text, cols)
    list:addRow(false, { interactive = false })[1]:setColSpan(cols):createText(text, { halign = "center" })
end

-- Loading / rejected snapshot texts shared by the tabs, nil once a snapshot is accepted.
local function snapshotMessage(projection)
    if projection.status == "loading" then
        return T(TXT.loading)
    elseif projection.status == "error" then
        return T(projection.error == "unsupported" and TXT.unsupported or TXT.malformed)
    end
end

-- Pilots tab: every registered GT pilot, also those without a ship. Unknown registry facts read "?". A pilot
-- with a ship can be marked (last column) for the pilot exchange planner; pilots without one cannot swap seats.
-- The column before it shows where the pilot is on the map (their ship, or their spacesuit when ejected).
-- In vanilla XP mode GT progression has no effect: rank, level, XP and the exchange planner are left out.

-- Text of each GT_FleetOverview.pilotStatus value (Status column and status filter).
local PILOT_STATUS_TEXT = {
    active = PILOT_STATUS.active, paused = PILOT_STATUS.paused, ejected = PILOT_STATUS.ejected, crew = PILOT_STATUS.crew,
    training = ACTIVITY_TEXT.training, unknown = TXT.unknown,
}

local function pilotStatusText(pilot)
    return T(PILOT_STATUS_TEXT[GT_FleetOverview.pilotStatus(pilot)])
end

-- Marked count, then the pilot exchange planner for the marked pilots' ships or for every GT ship.
local function addPilotControls(controls, projection, ctx)
    if not projection.vanillaXp then
        local marked = projection.marked
        local count = marked and #marked.ships or 0
        controls:addRow(false, { fixed = true })[1]:setColSpan(3):createText(T(TXT.markedExchange, count))
        local row = controls:addRow(true, { fixed = true })
        GT_UI.createButton(row[1], T(TXT.exchangeMarked), { onClick = function() ctx.onPilotExchange(marked.ships) end, active = count >= 2, mouseOverText = T(TXT.exchangeMarkedHint), fontSize = GT_UI.DEFAULTS.fontSize })
        GT_UI.createButton(row[2], T(TXT.exchangeAll), { onClick = function() ctx.onPilotExchange(nil) end, active = projection.status == "ready", mouseOverText = T(TXT.exchangeAllHint), fontSize = GT_UI.DEFAULTS.fontSize })
        GT_UI.createButton(row[3], T(TXT.clearMarked), { onClick = ctx.onPilotClear, active = marked ~= nil and next(marked.ids) ~= nil, fontSize = GT_UI.DEFAULTS.fontSize })
    end
    if projection.status ~= "ready" then
        return
    end
    -- Filters: pilot status, and the qualification fit only while qualification is shown (modifications
    -- effective), as on the Fleet tab.
    local row = controls:addRow(true, { fixed = true })
    local statuses = { dropdownOption(ALL_STATUSES, T(TXT.allStatuses)) }
    for _, option in ipairs(projection.statusFilter.options) do
        statuses[#statuses + 1] = dropdownOption(option.id, T(TXT.pilotTotal, T(PILOT_STATUS_TEXT[option.id]), option.count))
    end
    GT_UI.dropDown(row[1], statuses, projection.statusFilter.selected or ALL_STATUSES,
                   function(id) ctx.onPilotStatus(id ~= ALL_STATUSES and id or nil) end, nil, ctx.onEditing)
    local q = projection.qualification
    if q.shown then
        local options = {
            dropdownOption(ALL, T(TXT.allPilots)),
            dropdownOption("unqualified", T(TXT.groupTotal, T(TXT.unqualified), q.counts.unqualified)),
            dropdownOption("overqualified", T(TXT.groupTotal, T(TXT.overqualified), q.counts.overqualified)),
        }
        GT_UI.dropDown(row[2], options, q.filter or ALL, function(id) ctx.onPilotFilter(id ~= ALL and id or nil) end,
                       T(TXT.fitHint), ctx.onEditing)
    end
end

-- Pilots tab level colour and mouse-over by qualification grade (GT_FleetOverview pilotGrade).
local GRADE_COLOR = { full = Color["text_positive"], partial = Color["text_warning"], none = Color["text_negative"] }
local GRADE_TEXT = { full = TXT.qualified, partial = TXT.researchNeeded, none = TXT.unqualified }

-- Text columns of the Pilots tab: header text, sort key, width percent (the last one takes the rest) and
-- cell. progression: GT rank/level/XP, left out in vanilla XP mode.
local PILOT_TEXT_COLUMNS = {
    { text = TXT.pilot, sort = "name", pct = 20, cell = function(cell, pilot)
        cell:createText((pilot.name and pilot.name ~= "") and pilot.name or "?", { x = Helper.standardTextOffsetx })
    end },
    { text = TXT.rank, pct = 12, progression = true, cell = function(cell, pilot)
        cell:createText(pilot.rankIndex and T(RANK_TEXT_BASE + pilot.rankIndex) or "?")
    end },
    { text = TXT.level, sort = "level", pct = 6, progression = true, cell = function(cell, pilot, projection)
        local grade = projection.qualification.grade[pilot]
        cell:createText(pilot.level and tostring(pilot.level) or "?",
                        { halign = "right", color = GRADE_COLOR[grade], mouseOverText = grade and T(GRADE_TEXT[grade]) or nil })
    end },
    { text = TXT.xp, pct = 12, progression = true, cell = function(cell, pilot)
        local xp = pilot.xp and number(pilot.xp) or "?"
        cell:createText(pilot.xpNext and (xp .. " / " .. number(pilot.xpNext)) or xp, { halign = "right" })
    end },
    { text = TXT.status, pct = 9, cell = function(cell, pilot) cell:createText(pilotStatusText(pilot)) end },
    { text = TXT.ship, pct = 17, cell = function(cell, pilot)
        cell:createText(pilot.shipName and shipLabel(pilot.shipName, pilot.shipIdcode) or "-")
    end },
    { text = TXT.shipClass, pct = 7, cell = function(cell, pilot, projection)
        local class = projection.shipClass[pilot]
        cell:createText(class and string.upper(class) or "-", { halign = "center" })
    end },
    { text = TXT.profit, sort = "profit", cell = function(cell, pilot)
        cell:createText(pilot.profit and credits(pilot.profit) or "-", { halign = "right", color = pilot.profit and profitColor(pilot.profit) })
    end },
}

local function renderPilots(frame, projection, ctx)
    local columns = {}
    for _, c in ipairs(PILOT_TEXT_COLUMNS) do
        if not (c.progression and projection.vanillaXp) then
            columns[#columns + 1] = c
        end
    end
    local exchange = not projection.vanillaXp
    local mapCol = #columns + 1
    local cols = exchange and mapCol + 1 or mapCol
    local ready = projection.status == "ready"
    -- Without the exchange planner the controls only hold the filters, which need a snapshot.
    local addControls = (exchange or ready) and function(controls) addPilotControls(controls, projection, ctx) end or nil
    local list = addTabList(frame, ctx, cols, addControls)
    -- Freed progression widths go to the ship column.
    local spare = 0
    for _, c in ipairs(PILOT_TEXT_COLUMNS) do
        if c.progression and projection.vanillaXp then spare = spare + c.pct end
    end
    for i, c in ipairs(columns) do
        if c.pct then
            list:setColWidthPercent(i, c.text == TXT.ship and c.pct + spare or c.pct)
        end
    end
    list:setColWidth(mapCol, Helper.scaleY(ROW_HEIGHT), false)
    if exchange then
        list:setColWidth(cols, Helper.scaleY(ROW_HEIGHT), false)
    end
    local message = snapshotMessage(projection)
    if not message and #projection.rows == 0 then
        local filtered = projection.qualification.filter or projection.statusFilter.selected
        message = T(filtered and TXT.noPilotMatch or TXT.noPilots)
    end
    local header = list:addRow(ready or nil, { fixed = true })
    for col, c in ipairs(columns) do
        if ready and c.sort then
            addSortHeader(header[col], T(c.text), c.sort, projection.sort, function(_, column) ctx.onPilotSort(column) end)
        else
            addHeaderText(header[col], T(c.text))
        end
    end
    addHeaderText(header[mapCol], "")
    if exchange then
        addHeaderText(header[cols], "", T(TXT.markColumn))
    end
    if message then
        addMessageRow(list, message, cols)
        return
    end
    local selectedIndex
    for _, pilot in ipairs(projection.rows) do
        local row = list:addRow(pilot.id and { FleetView.PILOT_TAG, pilot.id } or true, {})
        local selected = pilot.id ~= nil and pilot.id == projection.selected
        if selected then
            selectedIndex = row.index
        end
        for col, c in ipairs(columns) do
            c.cell(row[col], pilot, projection)
        end
        -- Selected row only: the widget system's 200 buttons are shared by every open map panel.
        if selected and pilot.locationId then
            local locationId = pilot.locationId
            GT_UI.iconButton(row[mapCol], SHOW_ON_MAP_ICON, { mouseOverText = T(TXT.showOnMap),
                                                             onClick = function() ctx.onShowMap(locationId) end })
        end
        if exchange and pilot.id and pilot.shipId then
            local pilotId = pilot.id
            row[cols]:createCheckBox(projection.marked.ids[pilotId] == true, { width = ROW_HEIGHT, height = ROW_HEIGHT })
            row[cols].handlers.onClick = function(_, checked) ctx.onPilotMark(pilotId, checked) end
        end
    end
    if ctx.topRow then
        list:setTopRow(ctx.topRow)
    end
    if selectedIndex then
        list:setSelectedRow(selectedIndex)
    end
end

-- Profit tab: fleet summary over the listed GT ships, then the lifetime rankings by ship and by ware.
local PROFIT_COLS = 3

-- One ranking: section title, sortable column headers (name, lifetime profit, trade count), rows.
local function addRankingRows(list, ranking, ctx, title, nameText, rows, label, note)
    GT_UI.addSectionRow(list, T(title), PROFIT_COLS)
    if note then
        GT_UI.addCaptionRow(list, note, { colSpan = PROFIT_COLS, halign = "left", fixed = false })
    end
    local header = list:addRow(true, {})
    local sort = ctx.profit.sort[ranking]
    local function onSort(_, column) ctx.onProfitSort(ranking, column) end
    addSortHeader(header[1], T(nameText), "name", sort, onSort)
    addSortHeader(header[2], T(TXT.lifetimeProfit), "profit", sort, onSort)
    addSortHeader(header[3], T(TXT.tradeCount), "trades", sort, onSort)
    if #rows == 0 then
        addMessageRow(list, T(TXT.noProfit), PROFIT_COLS)
        return
    end
    for _, entry in ipairs(rows) do
        local row = list:addRow(true, {})
        row[1]:createText(label(entry), { x = Helper.standardTextOffsetx })
        row[2]:createText(credits(entry.profit), { halign = "right", color = profitColor(entry.profit) })
        row[3]:createText(number(entry.trades), { halign = "right" })
    end
end

local function renderProfit(frame, projection, ctx)
    local list = addTabList(frame, ctx, PROFIT_COLS)
    list:setColWidthPercent(2, 30)
    list:setColWidthPercent(3, 18)
    local message = snapshotMessage(projection)
    if message then
        addMessageRow(list, message, PROFIT_COLS)
        return
    end
    local summary = projection.summary
    GT_UI.addSectionRow(list, T(TXT.fleetSummary), PROFIT_COLS)
    local function line(labelId, value, color)
        local row = list:addRow(false, {})
        row[1]:createText(T(labelId), { x = Helper.standardTextOffsetx + Helper.standardIndentStep })
        row[2]:setColSpan(2):createText(value, { halign = "right", color = color })
    end
    line(TXT.gtShips, number(summary.ships))
    line(TXT.lifetimeProfit, credits(summary.profit), profitColor(summary.profit))
    line(TXT.tradeCount, number(summary.trades))
    line(TXT.averageProfit, summary.average and credits(math.floor(summary.average + 0.5)) or "-",
         summary.average and profitColor(summary.average))
    addRankingRows(list, "ships", ctx, TXT.profitByShip, TXT.ship, projection.ships,
                   function(ship) return shipLabel(ship.name, ship.idcode) end)
    addRankingRows(list, "wares", ctx, TXT.profitByWare, TXT.ware, projection.wares, function(ware) return ware.name end,
                   T(TXT.wareSince))
    if ctx.topRow then
        list:setTopRow(ctx.topRow)
    end
end

local function renderFleet(frame, projection, ctx)
    local gap = Helper.standardContainerOffset
    local compact = compactList(ctx)

    local cols = listColumns(projection, compact)
    local list = GT_UI.addPanelTable(frame, cols, ctx.width, ctx.frameborder, { tabOrder = 2 })
    for i, pct in ipairs(listPercents(projection)) do
        list:setColWidthPercent(i, pct)
    end
    if compact then
        -- Narrow map panels cannot fit 6 action icons plus a selection box.
        -- Those actions remain available from the normal ship context menu.
        list:setColWidth(cols, Helper.scaleY(ROW_HEIGHT), false)
    else
        for col = cols - ROW_ACTION_COLS, cols do
            list:setColWidth(col, Helper.scaleY(ROW_HEIGHT), false)
        end
    end

    local title = addTitleTable(frame, ctx)

    local listTop = title.properties.y + title:getFullHeight() + gap
    local controls, summary, selection
    -- The 8-column control toolbar also exceeds a narrow panel budget;
    -- suppress only in compact mode instead of producing negative widths.
    if projection.status == "ready" and not compact then
        controls = GT_UI.addPanelTable(frame, CONTROL_COLS, ctx.width, ctx.frameborder, { tabOrder = 4, y = listTop, reserveScrollBar = false })
        setupControlColumns(controls)
        addControlRows(controls, projection, ctx.onIntent, ctx)
        listTop = listTop + controls:getFullHeight() + gap
        summary = addSummaryTable(frame, projection, ctx.onIntent, ctx, listTop)
        listTop = listTop + summary:getFullHeight() + gap
        selection = addSelectionTable(frame, projection, ctx.onIntent, ctx, listTop)
        listTop = listTop + selection:getFullHeight() + gap
    end

    -- The detail table is created only when it gets rows: an empty table pinned to the frame bottom has no
    -- vertical space and the widget system skips it with an error. An open edit sits above the list instead:
    -- its dropdowns open downwards over the list, which at the frame bottom would run off the screen.
    local edit = ctx.edit()
    local detail
    local listBottom = ctx.height
    if edit or projection.selected or projection.selectedGone or projection.status == "ready" then
        detail = GT_UI.addPanelTable(frame, 2, ctx.width, ctx.frameborder, { tabOrder = 3 })
        detail:setColWidthPercent(1, edit and 45 or 35)
        if edit then
            addEditRows(detail, edit, ctx)
            detail.properties.maxVisibleHeight = math.floor(ctx.height / 2)
            detail.properties.y = listTop
            listTop = listTop + math.min(detail:getFullHeight(), detail.properties.maxVisibleHeight) + gap
        else
            addDetailRows(detail, projection, ctx)
            addQualificationRows(detail, projection)
            addAttentionRows(detail, projection)
            detail.properties.y = ctx.height - detail:getFullHeight() - gap
            listBottom = detail.properties.y
        end
    end

    list.properties.y = listTop
    local budget = listBottom - list.properties.y - gap
    list.properties.maxVisibleHeight = math.max(budget, 4 * ROW_HEIGHT)
    local selectedIndex = addListRows(list, projection, ctx.onIntent, ctx)
    if ctx.topRow then
        list:setTopRow(ctx.topRow)
    end
    if selectedIndex then
        list:setSelectedRow(selectedIndex)
    end

    title:addConnection(1, 2, true)
    if controls then
        controls:addConnection(2, 2)
        summary:addConnection(3, 2)
        selection:addConnection(4, 2)
    end
    list:addConnection(5, 2)
    if detail then
        detail:addConnection(6, 2)
    end
end

function FleetView.render(frame, projection, ctx)
    if ctx.tab == "pilots" then
        renderPilots(frame, ctx.pilots, ctx)
    elseif ctx.tab == "profit" then
        renderProfit(frame, ctx.profit, ctx)
    else
        renderFleet(frame, projection, ctx)
    end
end

_G.GT_FleetView = FleetView
return FleetView
