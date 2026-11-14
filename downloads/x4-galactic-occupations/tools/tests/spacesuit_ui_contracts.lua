-- v0.5.6: explicit context actions. Native transporter confirmation remains untouched.
local path = arg[1] .. "/ui/vgo_spacesuit.lua"
local checks, calls, events, installs = 0, {}, {}, {}
local function check(title, fn) fn(); checks=checks+1 end

local function nativeConfirm(...)
    calls[#calls+1]={...}
    return "native confirmation", 17
end
local confirmMenu={ mode="transporter", confirm=nativeConfirm }
local ship=101
local menu
menu={
    componentSlot={component=ship},
    actions={main={}}, -- no selected_orders: simulate stranded EVA
    prepareActions=function() return false end,
    onCloseElement=function(x) calls[#calls+1]={"closed",x} end,
    insertInteractionContent=function(group,action)
        assert(group=="main")
        table.insert(menu.actions.main,action)
    end,
}
Helper={getMenu=function(name)
    if name=="UserQuestionMenu" then return confirmMenu end
    if name=="InteractMenu" then return menu end
end}
RegisterEvent=function(name,fn) installs[name]=fn end
AddUITriggeredEvent=function(...) events[#events+1]={...} end
ConvertStringTo64Bit=function(x)return tonumber(x) end
ConvertStringToLuaID=function(x)return tonumber(x) end
IsValidComponent=function(x)return x==ship end
GetComponentData=function(x,k) if x==ship and k=="owner" then return "player" end end
ReadText=function(_,id)
    if id==76 then return "Emergency EVA (outside hull)" end
    if id==77 then return "Rescue: board this ship" end
    return "Explanatory tooltip"
end

local S=dofile(path)
check("native confirmation is never wrapped", function()
    assert(confirmMenu.confirm==nativeConfirm)
    assert(installs["VGO.Install"]==S.install)
end)
check("recovery controls work without a selected-order group",function()
    menu.prepareActions()
    assert(#menu.actions.main==2)
    assert(menu.actions.main[1].vgo_safe_eva_v56)
    assert(menu.actions.main[2].vgo_manual_board_v56)
    assert(#events==0)
end)
check("explicit click alone emits bounded rescue request",function()
    menu.actions.main[1].script()
    assert(#events==1 and events[1][1]=="VGO.Spacesuit")
    assert(events[1][2]=="safe_eva" and events[1][3]==ship)
    menu.actions.main[2].script()
    assert(#events==2 and events[2][2]=="recover_board" and events[2][3]==ship)
end)
check("stale menu target may not dispatch",function()
    menu.componentSlot.component=102
    menu.actions.main[1].script()
    assert(#events==2)
    menu.componentSlot.component=ship
end)
check("no duplicate menu actions on repeated installation",function()
    installs["VGO.Install"](nil,1001)
    assert(menu.prepareActions==S.hook)
    S.decorate(menu)
    assert(#menu.actions.main==2)
end)
check("native menu confirms remain identical across all modes",function()
    for _,mode in ipairs({"transporter","abortupgrade","hackpanel","other"}) do
        confirmMenu.mode=mode
        local result,code=confirmMenu.confirm(mode)
        assert(result=="native confirmation" and code==17)
    end
    assert(#events==2)
end)
check("reload singleton does not double wrap",function()
    assert(dofile(path)==S)
    assert(confirmMenu.confirm==nativeConfirm)
end)
print("PASS: "..checks.." opt-in EVA/boarding and native transporter UI contracts (mock only)")
