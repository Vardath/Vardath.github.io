-- Galactic Occupations 0.5.6: explicit, bounded player ship EVA/boarding rescue.
-- Do not intercept UserQuestionMenu.confirm or normal transporter controls.
-- A context menu click is the ONLY source of either native movement action.
local existing = rawget(_G, "VGOSpacesuit")
if existing then return existing end

local S = { player = nil, hook = nil, menu = nil }
_G.VGOSpacesuit = S

local function id64(v)
    return ConvertStringTo64Bit(tostring(v or 0))
end

local function luaid(v)
    return ConvertStringToLuaID(tostring(v))
end

local function valid(v)
    return v ~= nil and tostring(v) ~= "0" and IsValidComponent(id64(v))
end

local function ownedShip(v)
    if not valid(v) then return false end
    local owner = GetComponentData(id64(v), "owner")
    return owner == "player"
end

local function label(id, fallback)
    if type(ReadText) ~= "function" then return fallback end
    local text = ReadText(191180, id)
    if type(text) ~= "string" or text == "" or text:find("^=ReadText") then return fallback end
    return text
end

function S.decorate(menu)
    -- The native "selected_orders" group is gated on selected player ships.
    -- Use the always-available "main" interaction group so the action is
    -- reachable from a spacesuit without any ship selected for orders.
    if not menu or not menu.actions or not menu.actions.main or
        type(menu.insertInteractionContent) ~= "function" or not menu.componentSlot then
        return false
    end
    local ship = menu.componentSlot.component
    if not ownedShip(ship) then return false end
    for _, entry in ipairs(menu.actions.main) do
        if entry.vgo_safe_eva_v56 then return false end
    end
    local shipid = tostring(id64(ship))
    local function dispatch(control)
        -- Late click validation: do not use the stale target of a former menu.
        if not menu.componentSlot or tostring(id64(menu.componentSlot.component)) ~= shipid or
            not ownedShip(ship) or type(AddUITriggeredEvent) ~= "function" then return end
        AddUITriggeredEvent("VGO.Spacesuit", control, luaid(ship))
        if type(menu.onCloseElement) == "function" then menu.onCloseElement("close") end
    end
    menu.insertInteractionContent("main", {
        vgo_safe_eva_v56 = true, active = type(AddUITriggeredEvent) == "function",
        text = label(76, "Emergency EVA (outside hull)"),
        mouseOverText = label(78, "When aboard this undocked ship, exit via native emergency spacesuit placement outside the hull. Manual click only; no automatic ejection."),
        script = function() dispatch("safe_eva") end,
    })
    menu.insertInteractionContent("main", {
        vgo_manual_board_v56 = true, active = type(AddUITriggeredEvent) == "function",
        text = label(77, "Rescue: board this ship"),
        mouseOverText = label(79, "When in your spacesuit within 2 km of this owned ship, use the native transporter destination to recover aboard. Manual click only."),
        script = function() dispatch("recover_board") end,
    })
    return true
end

function S.install(_, player)
    S.player = player or S.player
    if not Helper or type(Helper.getMenu) ~= "function" then return end
    local menu = Helper.getMenu("InteractMenu")
    if not menu or type(menu.prepareActions) ~= "function" then return end
    if S.menu == menu and S.hook then return end
    local original = menu.prepareActions
    S.menu = menu
    S.hook = function (...)
        local result = original(...)
        local added = S.decorate(menu)
        return result or added
    end
    menu.prepareActions = S.hook
end

RegisterEvent("VGO.Install", S.install)
S.install()
return S
