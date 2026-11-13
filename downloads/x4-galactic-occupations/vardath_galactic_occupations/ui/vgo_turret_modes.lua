-- Add a virtual turret mode to existing-ship Loadout controls. No native enum or menu replacement.
local VGO = { mode = "vgo_minecrystals", hooks = {}, pending = {} }
local function luaid(component) return ConvertStringToLuaID(tostring(component)) end
local function id64(component) return ConvertStringTo64Bit(tostring(component)) end
local function valid(component)
    return component ~= nil and tostring(component) ~= "0" and IsValidComponent(id64(component))
end
local function eligibleShip(ship)
    if not valid(ship) then return false end
    local owner, macro = GetComponentData(id64(ship), "owner", "macro")
    return owner == "player" and (IsMacroClass(macro, "ship_s") or IsMacroClass(macro, "ship_m") or IsMacroClass(macro, "ship_l") or IsMacroClass(macro, "ship_xl"))
end
local function eligibleTurret(turret)
    if not valid(turret) then return false end
    local macro, tug = GetComponentData(id64(turret), "macro", "istugweapon")
    return not tug
end
local function shipstate(ship)
    if not VGO.player then return nil end
    for _, row in ipairs(GetNPCBlackboard(VGO.player, "$vgo_ui") or {}) do
        if tostring(row[1]) == tostring(luaid(ship)) then return row end
    end
end
local function enabled(ship, turret, scope)
    local object = scope == "all" and ship or turret
    local key = tostring(object) .. ":" .. scope
    if VGO.pending[key] ~= nil then return VGO.pending[key] end
    local state = shipstate(ship)
    if not state then return false end
    if scope == "all" then return state[2] == true or state[2] == 1 end
    for _, row in ipairs(state[5] or {}) do
        if tostring(row[1]) == tostring(luaid(turret)) then return row[2] == true or row[2] == 1 end
    end
    return false
end
local function setmode(ship, turret, scope, on)
    -- IDs stay component values in MD; never round 64-bit IDs through tonumber().
    VGO.pending[tostring(scope == "all" and ship or turret) .. ":" .. scope] = on
    AddUITriggeredEvent("VGO", "turretmode", { luaid(ship), luaid(turret or ship), scope, on })
end
local function decorate(cell, ship, turret, scope, refresh)
    if not cell or cell.type ~= "dropdown" or not eligibleShip(ship) then return end
    if scope ~= "all" and not eligibleTurret(turret) then return end
    if cell.vgo_decorated then return end
    cell.vgo_decorated = true
    -- Copy options: other menus and ordinary modes keep their original tables.
    local options = {}
    for _, option in ipairs(cell.properties.options or {}) do
        options[#options + 1] = option
    end
    options[#options + 1] = { id = VGO.mode, text = ReadText(191180, 30), icon = "", displayremoveoption = false }
    cell.properties.options = options
    local originalStart = cell.properties.startOption
    cell.properties.startOption = function (...)
        if enabled(ship, turret, scope) then return VGO.mode end
        if type(originalStart) == "function" then return originalStart(...) end
        return originalStart
    end
    local originalConfirmed = cell.handlers.onDropDownConfirmed
    cell.handlers.onDropDownConfirmed = function (_, selection, ...)
        setmode(ship, turret, scope, selection == VGO.mode)
        if refresh then refresh() end
        -- The virtual ID must NEVER reach C.SetWeaponMode/SetAllTurretModes or an upgrade plan.
        if selection ~= VGO.mode and originalConfirmed then return originalConfirmed(_, selection, ...) end
    end
end
function VGO.install()
    if not Helper or not Helper.getMenu then return end
    local map = Helper.getMenu("MapMenu")
    if map and type(map.setupLoadoutInfoSubmenuRows) == "function" and map.setupLoadoutInfoSubmenuRows ~= VGO.hooks.map then
        local original = map.setupLoadoutInfoSubmenuRows
        VGO.hooks.map = function (mode, ftable, ship, instance, ...)
            local first = #(ftable.rows or {}) + 1
            local result = original(mode, ftable, ship, instance, ...)
            if mode == "ship" and eligibleShip(ship) then
                for i = first, #ftable.rows do
                    local row = ftable.rows[i]
                    local id = tostring(row.rowdata)
                    if id == "info_turretconfig" then
                        local compatible = false
                        for _, turret in ipairs(map.turrets or {}) do compatible = compatible or eligibleTurret(turret) end
                        for _, group in ipairs(map.turretgroups or {}) do compatible = compatible or eligibleTurret(group.currentcomponent) end
                        if compatible then decorate(row[5], ship, ship, "all", function () map.noupdate = false end) end
                    else
                        local slot = id:match("^info_turretconfig(%d+)$")
                        local group = id:match("^info_turretgroupconfig(%d+)$")
                        if slot and map.turrets[tonumber(slot)] then
                            decorate(row[5], ship, map.turrets[tonumber(slot)], "turret", function () map.noupdate = false end)
                        elseif group and map.turretgroups[tonumber(group)] then
                            decorate(row[5], ship, map.turretgroups[tonumber(group)].currentcomponent, "group", function () map.noupdate = false end)
                        end
                    end
                end
            end
            -- Keep native Map info rows and columns untouched. A hard-coded
            -- 13-column status line may corrupt the native narrow info pane.
            -- Occupation activity remains in the logbook and ledger.
            return result
        end
        map.setupLoadoutInfoSubmenuRows = VGO.hooks.map
    end
    local outfitter = Helper.getMenu("ShipConfigurationMenu")
    if outfitter and type(outfitter.displayWeaponModeSelection) == "function" and outfitter.displayWeaponModeSelection ~= VGO.hooks.outfitter then
        local original = outfitter.displayWeaponModeSelection
        VGO.hooks.outfitter = function (ftable, upgradetype, slot, data, ...)
            local first = #(ftable.rows or {}) + 1
            local result = original(ftable, upgradetype, slot, data, ...)
            local ship, turret = outfitter.object, nil
            if upgradetype == "turretgroup" and outfitter.groups[slot] then
                turret = outfitter.groups[slot].turret.currentcomponent
            elseif upgradetype == "turret" and outfitter.slots.turret[slot] then
                turret = outfitter.slots.turret[slot].component
            end
            for i = first, #ftable.rows do
                decorate(ftable.rows[i][7], ship, turret, upgradetype == "turretgroup" and "group" or "turret")
            end
            return result
        end
        outfitter.displayWeaponModeSelection = VGO.hooks.outfitter
    end
end
RegisterEvent("VGO.Install", function (_, player) VGO.player = player or VGO.player; VGO.pending = {}; VGO.install() end)
VGO.install()
return VGO
