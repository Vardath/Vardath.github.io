-- Native station context submenu and a verified panel-API bridge. No ledger/menu replacement.
local existing = rawget(_G, "VGOHacker")
if existing then return existing end
local ffi = require("ffi")
local C = ffi.C
local H = { requested = {}, invoked = {}, player = nil, nextPoll = 0 }
_G.VGOHacker = H
local function id64(v) return ConvertStringTo64Bit(tostring(v or 0)) end
local function luaid(v) return ConvertStringToLuaID(tostring(v)) end
local function valid(v) return v ~= nil and tostring(v) ~= "0" and IsValidComponent(id64(v)) end
local function cfunction(name)
    local ok, fn = pcall(function () return C[name] end)
    return ok and fn or nil
end
function H.nativeAvailable()
    -- Signatures/layout match the inspected native X4 9.00 menus/target monitor.
    -- Use existing declarations first. A restricted environment fails safely.
    if not cfunction("GetControlPanelInfo") and ffi.cdef then
        pcall(ffi.cdef, [[
            typedef struct {
                const char* type; const char* name; const char* desc; const char* hackeddesc;
                int64_t price; int32_t numrequiredwares; bool ishack; bool hacked;
                double hackduration; double hackexpiretime;
            } VGOHackControlPanelInfo;
            VGOHackControlPanelInfo GetControlPanelInfo(UIComponentSlot controlpanel);
        ]])
    end
    if not cfunction("GetControlPanelRequiredWares") and ffi.cdef then
        pcall(ffi.cdef, "uint32_t GetControlPanelRequiredWares(UIWareInfo* result, uint32_t resultlen, UIComponentSlot controlpanel);")
    end
    if not cfunction("StartControlPanelHack") and ffi.cdef then
        pcall(ffi.cdef, "void StartControlPanelHack(UIComponentSlot target, const char* paneltypeid);")
    end
    return cfunction("GetControlPanelInfo") and cfunction("GetControlPanelRequiredWares") and cfunction("StartControlPanelHack")
end
local function key(component) return tostring(id64(component)) end
local function flag(value) return value == true or value == 1 end
local function elapsed()
    -- Native menu animation/hover clock continues while the simulation is paused.
    if type(getElapsedTime) == "function" then return getElapsedTime() end
    return cfunction("GetCurrentGameTime") and C.GetCurrentGameTime() or 0
end
local function board(key) return H.player and GetNPCBlackboard(H.player, key) or nil end
local function text(v) return type(v) == "string" and v or ffi.string(v) end
local function normalized(v) return text(v):gsub("^controlpaneltype%.", "") end
local function slot(component, connection)
    local s = ffi.new("UIComponentSlot")
    s.component = id64(component)
    s.connection = connection
    return s
end
function H.probe(_, ship)
    local request = board("$vgo_hack_probe")
    if not request or tostring(request[1]) ~= tostring(luaid(ship)) then return end
    local answer = { luaid(ship), request[2], false, 0, "", 0, {}, 0 }
    if H.nativeAvailable() then
        for _, row in ipairs(request[4] or {}) do
            if valid(row[1]) then
                local s = slot(row[1], row[2])
                local ok, info = pcall(C.GetControlPanelInfo, s)
                if ok and info.ishack and not info.hacked and normalized(info.type) == request[3] then
                    local costs = {}
                    local count = tonumber(info.numrequiredwares) or 0
                    if count >= 0 and count <= 64 then
                        local readok, complete = pcall(function ()
                            local buffer = count > 0 and ffi.new("UIWareInfo[?]", count) or nil
                            local n = count > 0 and tonumber(C.GetControlPanelRequiredWares(buffer, count, s)) or 0
                            if n ~= count then return false end
                            for i = 0, n - 1 do
                                local ware, amount = text(buffer[i].ware), tonumber(buffer[i].amount)
                                if ware == "" or not amount or amount <= 0 or amount ~= math.floor(amount) then return false end
                                costs[#costs + 1] = { ware, amount }
                            end
                            return true
                        end)
                        if readok and complete then
                            answer = { luaid(ship), request[2], true, luaid(row[1]), row[2], luaid(row[3]), costs, tonumber(info.price) or 0 }
                            break
                        end
                    end
                end
            end
        end
    end
    AddUITriggeredEvent("VGO", "hackprobe", answer)
end
function H.invoke(_, ship)
    local request = board("$vgo_hack_call")
    if not request or tostring(request[1]) ~= tostring(luaid(ship)) then return end
    local now = cfunction("GetCurrentGameTime") and C.GetCurrentGameTime() or 0
    if H.lastInvokeTime and now < H.lastInvokeTime then H.invoked = {} end
    H.lastInvokeTime = now
    local token = tostring(request[1]) .. ":" .. tostring(request[2])
    if H.invoked[token] then return end
    -- MD persists call-sent before dispatch; UI also guards duplicate event delivery.
    H.invoked[token] = true
    local ok, reason = false, "Native panel API unavailable"
    if H.nativeAvailable() and valid(request[3]) then
        local s = slot(request[3], request[4])
        local readok, info = pcall(C.GetControlPanelInfo, s)
        if readok and info.ishack and not info.hacked and normalized(info.type) == request[5] then
            -- Uses the actual engine-provided panel type. Native code charges its
            -- real tools/price and applies the panel-specific station effect.
            ok, reason = pcall(C.StartControlPanelHack, s, text(info.type))
        else
            reason = "Panel unavailable, changed, or already hacked"
        end
    end
    AddUITriggeredEvent("VGO", "hackinvoked", { luaid(ship), request[2], ok == true, tostring(reason or "Native call issued; effect verification pending") })
end
local function isclass(component, classname)
    if not valid(component) then return false end
    if cfunction("IsComponentClass") then return C.IsComponentClass(id64(component), classname) end
    local macro = GetComponentData(id64(component), "macro")
    return IsMacroClass(macro, classname)
end
function H.catalogue(station)
    for _, row in ipairs(board("$vgo_hack_catalogue_ui") or {}) do
        if key(row[1]) == key(station) then
            if cfunction("GetCurrentGameTime") and row[3] and C.GetCurrentGameTime() >= row[3] then return nil end
            return row[2] or {}, row[4] or "ready"
        end
    end
end
function H.requestCatalogue(station, retry)
    local stationkey = key(station)
    if not retry and H.requested[stationkey] then return false end
    H.requested[stationkey] = { deadline = elapsed() + 10 }
    AddUITriggeredEvent("VGO", "hackcatalogue", luaid(station))
    return true
end
local function selectedShips(menu)
    local ships = {}
    local occupied = cfunction("GetPlayerOccupiedShipID") and C.GetPlayerOccupiedShipID() or 0
    for _, ship in ipairs(menu.selectedplayerships or {}) do
        if valid(ship) and tostring(id64(ship)) ~= tostring(occupied) and GetComponentData(id64(ship), "owner") == "player" then
            ships[#ships + 1] = luaid(ship)
        end
    end
    return ships
end
local function fingerprint(station, ships, rows, status, request)
    local parts = { key(station), status or "pending" }
    for _, ship in ipairs(ships) do parts[#parts + 1] = key(ship) end
    if rows then
        for _, row in ipairs(rows) do
            parts[#parts + 1] = tostring(row[1]) .. ":" .. tostring(row[2]) .. ":" .. tostring(flag(row[3]))
        end
    else
        parts[#parts + 1] = request and elapsed() >= request.deadline and "timeout" or "waiting"
    end
    return table.concat(parts, "|")
end
function H.decorate(menu)
    local station = menu.componentSlot and menu.componentSlot.component
    if not H.player or not valid(station) or not isclass(station, "station") or GetComponentData(id64(station), "owner") == "player" then return false end
    local ships = selectedShips(menu)
    if #ships == 0 or not menu.actions or not menu.actions.selected_orders then return false end
    local stationkey = key(station)
    local rows, status = H.catalogue(station)
    if rows == nil then H.requestCatalogue(station, false) end
    local request = H.requested[stationkey]
    menu.actions.vgo_hack_panels = {}
    if rows == nil then
        local timedout = request and elapsed() >= request.deadline
        menu.actions.vgo_hack_panels[1] = {
            text = timedout and "Station panel lookup timed out" or "Checking available station panels...",
            active = false,
            mouseOverText = "Mission Director must run to inspect the station. Unpause the game if it is paused; the menu also checks for a reply automatically.",
        }
        if timedout then
            menu.actions.vgo_hack_panels[2] = { text = "Retry station panel lookup", active = true, script = function ()
                if menu.componentSlot and key(menu.componentSlot.component) == stationkey then
                    H.requestCatalogue(station, true)
                    H.decorate(menu)
                    menu.refresh = true
                end
            end }
        end
    elseif #rows == 0 then
        menu.actions.vgo_hack_panels[1] = {
            text = status == "unavailable" and "Station unavailable for hacking" or "No accessible station panels found",
            active = false,
            mouseOverText = "No real panels were returned. The station interior may not be loaded. Dock or approach the station and retry; no panel is invented.",
        }
        menu.actions.vgo_hack_panels[2] = { text = "Refresh station panels", active = true, script = function ()
            if menu.componentSlot and key(menu.componentSlot.component) == stationkey then
                H.requestCatalogue(station, true)
                menu.refresh = true
            end
        end }
    else
        for _, row in ipairs(rows) do
            local panelid, label, hacked = row[1], row[2], flag(row[3])
            menu.actions.vgo_hack_panels[#menu.actions.vgo_hack_panels + 1] = {
                text = label, active = not hacked,
                mouseOverText = hacked and "This panel effect is already active" or "Queue one station hack for each selected ship. Existing crew must walk out and return; real tools are consumed. Unpause to let game scripts queue the order.",
                script = function ()
                    -- Re-read selection and station at click time; do not queue stale targets.
                    if not menu.componentSlot or key(menu.componentSlot.component) ~= stationkey or not valid(station) then return end
                    local currentShips = selectedShips(menu)
                    if #currentShips == 0 then return end
                    AddUITriggeredEvent("VGO", "hackstation", { luaid(station), currentShips, panelid })
                    if menu.onCloseElement then menu.onCloseElement("close") end
                end,
            }
        end
    end
    H.rendered = fingerprint(station, ships, rows, status, request)
    for _, entry in ipairs(menu.actions.selected_orders) do if entry.vgo_hack_root then return true end end
    menu.insertInteractionContent("selected_orders", {
        text = ReadText(191180, 51), vgo_hack_root = true, active = H.nativeAvailable() and true or false,
        mouseOverText = "One-off hack using selected ships; choose a real panel in the submenu. Default behaviour and queued orders are retained.",
        script = function () menu.handleSubSectionOption({ id = "vgo_hack_panels", y = 0 }, true) end,
    })
    return true
end
function H.poll(menu)
    if elapsed() < H.nextPoll then return end
    H.nextPoll = elapsed() + 0.5
    if not menu.actions or not menu.actions.vgo_hack_panels or not menu.componentSlot then return end
    local station = menu.componentSlot.component
    if not valid(station) then return end
    local rows, status = H.catalogue(station)
    if fingerprint(station, selectedShips(menu), rows, status, H.requested[key(station)]) ~= H.rendered then
        -- Native refresh redraws existing actions; it never calls prepareActions.
        -- Replace only our submenu before requesting that redraw.
        H.decorate(menu)
        menu.refresh = true
    end
end
function H.catalogueReady(_, station)
    H.requested[key(station)] = nil
    if not Helper or not Helper.getMenu then return end
    local menu = Helper.getMenu("InteractMenu")
    if menu and menu.componentSlot and key(menu.componentSlot.component) == key(station) and menu.actions and menu.actions.vgo_hack_panels then
        H.decorate(menu)
        menu.refresh = true
    end
end
function H.install(_, player)
    if player and H.player and key(player) ~= key(H.player) then
        H.invoked = {}; H.requested = {}; H.nextPoll = 0; H.rendered = nil
    end
    H.player = player or H.player
    if not Helper or not Helper.getMenu then return end
    local menu = Helper.getMenu("InteractMenu")
    if not menu then return end
    if type(menu.prepareActions) == "function" and menu.prepareActions ~= H.hook then
        local original = menu.prepareActions
        H.hook = function (...)
            local result = original(...)
            local added = H.decorate(menu)
            return result or added
        end
        menu.prepareActions = H.hook
    end
    if type(menu.onUpdate) == "function" and menu.onUpdate ~= H.updateHook then
        local original = menu.onUpdate
        H.updateHook = function (...)
            H.poll(menu)
            return original(...)
        end
        menu.onUpdate = H.updateHook
    end
end
RegisterEvent("VGO.Install", H.install)
RegisterEvent("VGO.HackProbe", H.probe)
RegisterEvent("VGO.HackInvoke", H.invoke)
RegisterEvent("VGO.HackCatalogue", H.catalogueReady)
H.install()
return H
