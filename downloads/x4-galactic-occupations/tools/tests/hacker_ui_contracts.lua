-- Execute the actual hacker addon with native-shaped FFI/menu data; this is not X4 runtime testing.
local root = arg[1] or 'downloads/x4-galactic-occupations/vardath_galactic_occupations'
local checks, events, callbacks, calls, originalCalls, time = 0, {}, {}, {}, 0, 100
local objects = { [1]={owner='player',class='npc'}, [10]={owner='player',class='ship_m'}, [11]={owner='player',class='ship_l'}, [12]={owner='argon',class='ship_m'}, [20]={owner='argon',class='station'}, [21]={owner='player',class='station'}, [30]={class='room'}, [31]={class='room'} }
local board, panels, native = {}, {}, {}
function ConvertStringTo64Bit(v) return tonumber(v) end
function ConvertStringToLuaID(v) return tonumber(v) end
function IsValidComponent(v) return objects[v] ~= nil end
function GetComponentData(v,k) return (objects[v] or {})[k] end
function GetNPCBlackboard(_,key) return board[key] end
function RegisterEvent(name,fn) callbacks[name]=fn end
function AddUITriggeredEvent(screen,control,data) events[#events+1]={screen,control,data} end
function ReadText(_,id) return id==51 and 'Hack station' or tostring(id) end
function IsMacroClass(m,c) return m==c end
native.IsComponentClass=function(id,class) return objects[id] and objects[id].class==class end
native.GetPlayerOccupiedShipID=function() return 11 end
native.GetCurrentGameTime=function() return time end
native.GetControlPanelInfo=function(slot) local p=panels[slot.component..':'..slot.connection];assert(p,'missing real panel');return p end
native.GetControlPanelRequiredWares=function(buffer,n,slot)
    local costs=panels[slot.component..':'..slot.connection].costs or {}
    for i,c in ipairs(costs) do buffer[i-1]={ware=c[1],amount=c[2]} end
    return #costs
end
native.StartControlPanelHack=function(slot,kind) calls[#calls+1]={slot.component,slot.connection,kind};return nil end
package.preload.ffi=function() return {C=native,string=tostring,cdef=function() end,new=function(kind,n) assert(not n or n>0,'zero-count allocation');return {} end} end
local menu={componentSlot={component=20},selectedplayerships={10,11,12},actions={selected_orders={}},insertInteractionContent=function(section,entry) menu.actions[section][#menu.actions[section]+1]=entry end}
-- Lua 5.1 closures must refer to a declared local rather than an initializer's global.
menu.insertInteractionContent=function(section,entry) menu.actions[section][#menu.actions[section]+1]=entry end
menu.prepareActions=function() originalCalls=originalCalls+1;menu.actions={selected_orders={{text='Fly and wait',script=function() end}}};return 'original' end
menu.handleSubSectionOption=function(section) menu.opened=section.id end
menu.onCloseElement=function() menu.closed=true end
Helper={getMenu=function(name) return name=='InteractMenu' and menu or nil end}
local function check(value,message) assert(value,message);checks=checks+1 end
local H=dofile(root..'/ui/vgo_hacker.lua');callbacks['VGO.Install'](nil,1)
check(menu.prepareActions()=='original' and originalCalls==1,'native menu return preserved')
check(events[#events][2]=='hackcatalogue' and events[#events][3]==20,'actual station catalogue requested')
check(menu.actions.selected_orders[1].text=='Fly and wait','normal order retained')
check(menu.actions.vgo_hack_panels[1].active==false,'unqueried panel list disabled')
local n=#events;menu.prepareActions();check(#events==n,'pending catalogue requests coalesced')
board['$vgo_hack_catalogue_ui']={{20,{{'hack_storage','Storage',false},{'hack_all_turrets','Turrets',true}},700}}
callbacks['VGO.HackCatalogue'](nil,20);menu.prepareActions()
check(menu.refresh==true,'reply requests ordinary menu refresh')
check(#menu.actions.selected_orders==2 and #menu.actions.vgo_hack_panels==2,'single additive root and actual panel list')
check(menu.actions.vgo_hack_panels[1].active and not menu.actions.vgo_hack_panels[2].active,'already active panel disabled')
menu.actions.selected_orders[2].script();check(menu.opened=='vgo_hack_panels','native submenu opened')
menu.actions.vgo_hack_panels[1].script();local ev=events[#events]
check(ev[2]=='hackstation' and ev[3][1]==20 and ev[3][3]=='hack_storage','requested panel is preserved')
check(#ev[3][2]==1 and ev[3][2][1]==10,'current player ship and non-player ships excluded')
check(menu.closed,'native menu close delegated')
H.decorate(menu);check(#menu.actions.selected_orders==2,'repeat decoration has no duplicate command')
menu.componentSlot.component=21;menu.prepareActions();check(#menu.actions.selected_orders==1,'player station has no hack command')
menu.componentSlot.component=20;menu.selectedplayerships={12};menu.prepareActions();check(#menu.actions.selected_orders==1,'non-player ship cannot queue hack')
menu.selectedplayerships={10};local oldhook=menu.prepareActions;H.install();check(menu.prepareActions==oldhook,'hook installation idempotent')
time=701;check(H.catalogue(20)==nil,'expired panel catalogue re-queried');time=100
panels['30:wrong']={ishack=true,hacked=false,type='hack_production',numrequiredwares=0,price=0}
panels['30:storage']={ishack=true,hacked=false,type='controlpaneltype.hack_storage',numrequiredwares=1,price=120,costs={{'inv_securitydecryptionsystem',2}}}
board['$vgo_hack_probe']={10,123,'hack_storage',{{30,'wrong',30},{30,'storage',30}}}
H.probe(nil,10);ev=events[#events]
check(ev[2]=='hackprobe' and ev[3][3] and ev[3][5]=='storage','probe selects actual requested native panel type')
check(ev[3][7][1][1]=='inv_securitydecryptionsystem' and ev[3][7][1][2]==2 and ev[3][8]==120,'actual native tools and price returned')
board['$vgo_hack_probe']={10,124,'hack_all_turrets',{{30,'wrong',30}}};H.probe(nil,10);check(not events[#events][3][3],'unmatched native panel never accepted')
board['$vgo_hack_probe']={10,125,'hack_production',{{30,'wrong',30}}};H.probe(nil,10);check(events[#events][3][3] and #events[#events][3][7]==0,'native zero-cost panel avoids invalid zero-buffer allocation')
board['$vgo_hack_call']={10,200,30,'storage','hack_storage'};H.invoke(nil,10)
check(#calls==1 and calls[1][1]==30 and calls[1][3]=='controlpaneltype.hack_storage','native hack receives exact actual slot and type')
check(events[#events][2]=='hackinvoked' and events[#events][3][3],'void native return acknowledged only as issued call')
H.invoke(nil,10);check(#calls==1,'duplicate native event cannot consume tools twice')
board['$vgo_hack_call']={10,201,30,'wrong','hack_storage'};H.invoke(nil,10);check(#calls==1 and not events[#events][3][3],'changed panel rejected without native effect')
board['$vgo_hack_call']={10,202,30,'storage','hack_storage'};panels['30:storage'].hacked=true;H.invoke(nil,10);check(#calls==1,'already hacked panel not charged again');panels['30:storage'].hacked=false
board['$vgo_hack_call']={10,203,30,'storage','hack_storage'};local request=board['$vgo_hack_call'];board['$vgo_hack_call']=nil;H.invoke(nil,10);check(#calls==1,'cancelled request cannot reach engine')
board['$vgo_hack_call']=request;local fn=native.StartControlPanelHack;native.StartControlPanelHack=nil;H.invoke(nil,10);check(#calls==1 and not events[#events][3][3],'missing protected native export fails safely');native.StartControlPanelHack=fn
board['$vgo_hack_call']={10,204,30,'storage','hack_storage'};time=200;H.invoke(nil,10);time=50;H.invoke(nil,10);check(#calls==3,'older-save timeline permits its genuine token after time reversal')
H.install(nil,2);H.invoke(nil,10);check(#calls==4,'new world/player does not inherit stale consumed-token cache')
print('PASS: '..checks..' hacker UI/native-bridge mock checks (no X4 runtime)')
