-- Galactic Occupations 0.5.3 UI regression test: no native confirmer hook.
local path = arg[1] .. "/ui/vgo_spacesuit.lua"
local checks, calls, events, installs = 0, {}, {}, {}
local function check(title, fn)
    fn(); checks=checks+1
end
local function confirm(...)
    calls[#calls+1]={...}
    return "native confirmation", 17
end
local menu={mode="transporter",transportertarget={component=9007199254740997},confirm=confirm}
Helper={getMenu=function(name)
    if name=="UserQuestionMenu" then return menu end
end}
RegisterEvent=function(name,fn) installs[name]=fn end
AddUITriggeredEvent=function(...) events[#events+1]={...} end
local S=dofile(path)
check("native confirmation never wrapped",function()
    assert(menu.confirm==confirm)
    assert(installs["VGO.Install"]==S.install)
end)
check("legacy install leaves native menus untouched",function()
    for i=1,100 do installs["VGO.Install"](nil,9007199254740995) end
    assert(menu.confirm==confirm)
end)
check("transporter operation goes through native function exactly once",function()
    local a,b=menu.confirm("redocking",23)
    assert(a=="native confirmation" and b==17)
    assert(#calls==1 and calls[1][1]=="redocking" and calls[1][2]==23)
    assert(#events==0)
end)
check("all menu modes remain native",function()
    for _,mode in ipairs({"transporter","abortupgrade","hackpanel","other"}) do
        menu.mode=mode;menu.confirm(mode)
    end
    assert(#events==0 and #calls==5)
end)
check("reload singleton does not change native function",function()
    assert(dofile(path)==S)
    assert(menu.confirm==confirm)
end)
print("PASS: "..checks.." native redocking/spacesuit UI safety contracts; no X4 runtime")
