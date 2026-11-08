-- Execute the shipped confirmation observer with native menu/FFI boundaries mocked.
local path = arg[1] .. "/ui/vgo_spacesuit.lua"
local passed, events, nativecalls, handlers = 0, {}, {}, {}
local player, source, zone = "9007199254740997", "9007199254740999", "9007199254741001"
local classes = { [source] = "ship", [zone] = "zone", suit = "spacesuit", station = "station" }
local failClass, failContext, failEvent, failNative = false, false, false, false
local menu = { mode = "transporter", transportertarget = { component = zone } }
local function eq(a,b) assert(a == b, tostring(a) .. " ~= " .. tostring(b)) end
local function check(name, fn) fn(); passed = passed + 1 end
local function native(...)
    nativecalls[#nativecalls + 1] = { ... }
    if failNative then error("native confirmation refused") end
    return "original", 17
end
menu.confirm = native
Helper = { getMenu = function (name) if name == "UserQuestionMenu" then return menu end end }
ConvertStringTo64Bit = function (id) return id end
ConvertStringToLuaID = function (id) return id end
AddUITriggeredEvent = function (screen, control, payload)
    if failEvent then error("unavailable UI event") end
    events[#events + 1] = { screen, control, payload }
end
RegisterEvent = function (name, fn) handlers[name] = fn end
package.preload.ffi = function () return { cdef = function () end, C = {
    IsComponentClass = function (id, class)
        if failClass then error("native unavailable") end
        return classes[id] == class or (classes[id] == "spacesuit" and class == "ship")
    end,
    GetContextByClass = function (id, class, self)
        if failContext then error("no context") end
        eq(id, player); eq(class, "ship"); eq(self, false); return source
    end,
} } end
local S = dofile(path)
check("uninformed observer preserves early native exit", function ()
    local a,b=menu.confirm("before install");eq(a,"original");eq(b,17);eq(#events,0);eq(#nativecalls,1)
end)
handlers["VGO.Install"](nil,player)
check("confirmed spacesuit sends exact source and zone once", function ()
    local before=#nativecalls;local a,b=menu.confirm("native arg",23)
    eq(a,"original");eq(b,17);eq(#nativecalls,before+1);eq(#events,1)
    eq(events[1][1],"VGO.Spacesuit");eq(events[1][2],"confirmed")
    eq(events[1][3][1],source);eq(events[1][3][2],zone)
    eq(nativecalls[#nativecalls][1],"native arg");eq(nativecalls[#nativecalls][2],23)
end)
check("periodic installation cannot nest its own wrapper", function ()
    local hook=menu.confirm
    for i=1,100 do S.install(nil,player) end
    eq(menu.confirm,hook);local n=#events;local c=#nativecalls;menu.confirm();eq(#events,n+1);eq(#nativecalls,c+1)
end)
check("other confirmation modes stay native", function ()
    local n=#events
    for _,mode in ipairs({"hackpanel","abortupgrade","markashostile","custom","removebuildstorage"}) do
        menu.mode=mode;menu.confirm()
    end
    eq(#events,n);menu.mode="transporter"
end)
check("station and room transporter targets stay native", function ()
    local n=#events;menu.transportertarget.component="station";menu.confirm();eq(#events,n)
    menu.transportertarget.component=zone
end)
check("missing or cleaned transporter target stays native", function ()
    local n=#events;menu.transportertarget=nil;menu.confirm();eq(#events,n)
    menu.transportertarget={component=zone}
end)
check("FFI class error cannot block normal confirmation", function ()
    local c=#nativecalls;local n=#events;failClass=true;menu.confirm();failClass=false
    eq(#nativecalls,c+1);eq(#events,n)
end)
check("missing ship context cannot block normal confirmation", function ()
    local c=#nativecalls;local n=#events;failContext=true;menu.confirm();failContext=false
    eq(#nativecalls,c+1);eq(#events,n)
end)
check("failed UI signal cannot block or repeat normal confirmation", function ()
    local c=#nativecalls;local n=#events;failEvent=true;menu.confirm();failEvent=false
    eq(#nativecalls,c+1);eq(#events,n)
end)
check("native failure propagates once without substituting another transport", function ()
    local c=#nativecalls;failNative=true;local ok=pcall(menu.confirm);failNative=false
    eq(ok,false);eq(#nativecalls,c+1)
end)
check("reload singleton cannot duplicate the observer", function ()
    local hook=menu.confirm;eq(dofile(path),S);eq(menu.confirm,hook)
end)
check("no available menu leaves UI untouched", function ()
    local helper=Helper;Helper=nil;S.install(nil,player);Helper=helper
    local hook=menu.confirm;S.install(nil,player);eq(menu.confirm,hook)
end)
check("another addon wrapper remains in the call chain", function ()
    local old=menu.confirm;local called=0
    menu.confirm=function (...) called=called+1;return old(...) end
    S.install(nil,player);local c=#nativecalls;local n=#events
    menu.confirm();eq(called,1);eq(#nativecalls,c+1);eq(#events,n+1)
end)
print("PASS: " .. passed .. " spacesuit observer contracts; no X4 runtime")
