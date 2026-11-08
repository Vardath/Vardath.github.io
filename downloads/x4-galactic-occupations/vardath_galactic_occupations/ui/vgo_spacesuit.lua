-- Observe a confirmed vanilla spacesuit exit. Keep the original menu and transport call.
local existing = rawget(_G, "VGOSpacesuit")
if existing then return existing end
local ffi = require("ffi")
local C = ffi.C
local S = {}
_G.VGOSpacesuit = S
pcall(ffi.cdef, "UniverseID GetContextByClass(UniverseID componentid, const char* classname, bool includeself);")
pcall(ffi.cdef, "bool IsComponentClass(UniverseID componentid, const char* classname);")
local function id64(v) return ConvertStringTo64Bit(tostring(v or 0)) end
local function luaid(v) return ConvertStringToLuaID(tostring(v)) end
local function confirmedSource(menu)
    if menu.mode ~= "transporter" or not menu.transportertarget or not S.player then return end
    local target = menu.transportertarget.component
    if not C.IsComponentClass(target, "zone") then return end
    local ship = C.GetContextByClass(id64(S.player), "ship", false)
    if tostring(ship) == "0" or not C.IsComponentClass(ship, "ship") or C.IsComponentClass(ship, "spacesuit") then return end
    return luaid(ship), luaid(target)
end
function S.install(_, player)
    S.player = player or S.player
    if not Helper or not Helper.getMenu then return end
    local menu = Helper.getMenu("UserQuestionMenu")
    if not menu or type(menu.confirm) ~= "function" or (S.menu == menu and S.hook) then return end
    S.menu = menu
    local original = menu.confirm
    S.hook = function (...)
        -- An unavailable observer must never block or repeat the native confirmation.
        local ok, ship, zone = pcall(confirmedSource, menu)
        if ok and ship then pcall(AddUITriggeredEvent, "VGO.Spacesuit", "confirmed", { ship, zone }) end
        return original(...)
    end
    menu.confirm = S.hook
end
RegisterEvent("VGO.Install", S.install)
S.install()
return S
