-- Executable tests against native-shaped menu/widget data. No X4 runtime is simulated or claimed.
local root = arg[1] or "downloads/x4-galactic-occupations/vardath_galactic_occupations"
local unpack = unpack or table.unpack
local checks, nativeCalls, events, callbacks, blackboard = 0, 0, {}, {}, {}
local objects = { [10]={owner="player",macro="ship_m"},[20]={owner="player",macro="ship_l"},[40]={owner="player",macro="ship_xl"},[30]={owner="argon",macro="ship_m"},[101]={macro="beam"},[102]={macro="missileturret"},[104]={macro="beam"} }
function ConvertStringToLuaID(v) return tonumber(v) end
function ConvertStringTo64Bit(v) return #tostring(v) > 15 and tostring(v) or tonumber(v) end
function IsValidComponent(v) return objects[v] ~= nil end
function GetComponentData(v, ...)
    local result = {}; for _, key in ipairs({...}) do result[#result+1] = (objects[v] or {})[key] or false end
    return unpack(result)
end
function IsMacroClass(macro, class) return macro == class end
function GetNPCBlackboard(v,key) return (blackboard[v] or {})[key] end
function ReadText(page,id) return page == 191180 and id == 30 and "Mine Crystals" or tostring(id) end
function RegisterEvent(name, callback) callbacks[name] = callback end
function AddUITriggeredEvent(screen,control,payload) events[#events+1]={screen,control,payload} end
function ConvertMoneyString(amount) return tostring(amount) end
local function check(value, message) assert(value,message); checks=checks+1 end
local function cell(kind)
    return {type=kind or "dropdown", properties={options={{id="defend",text="Defend"},{id="attackenemies",text="Attack"}},startOption="defend"}, handlers={onDropDownConfirmed=function(_,mode) assert(mode~="vgo_minecrystals");nativeCalls=nativeCalls+1 end}}
end
local function row(id, col, kind) local r={rowdata=id};r[col]=cell(kind);return r end
local map={turrets={101,102},turretgroups={{currentcomponent=104}}}
function map.setupLoadoutInfoSubmenuRows(_,t)
    t.rows[#t.rows+1]=row("info_turretconfig",5)
    t.rows[#t.rows+1]=row("info_turretconfig1",5)
    t.rows[#t.rows+1]=row("info_turretconfig2",5)
    t.rows[#t.rows+1]=row("info_turretgroupconfig1",5)
    t.rows[#t.rows+1]=row("info_turretconfig1_2",5,"button")
    return "native map"
end
local outfitter={object=10,groups={{turret={currentcomponent=104}}},slots={turret={{component=101}}},upgradeplan={turret={{weaponmode="defend"}}}}
function outfitter.displayWeaponModeSelection(t,type,slot)
    local r=row("ammo_config",7)
    r[7].handlers.onDropDownConfirmed=function(_,mode) assert(mode~="vgo_minecrystals");outfitter.upgradeplan.turret[1].weaponmode=mode end
    t.rows[#t.rows+1]=r
end
Helper={getMenu=function(name) return name=="MapMenu" and map or name=="ShipConfigurationMenu" and outfitter end}
local vgo=dofile(root.."/ui/vgo_turret_modes.lua")
local t={rows={}};check(map.setupLoadoutInfoSubmenuRows("ship",t,10)=="native map","map return preserved")
check(t.rows[1][5].properties.options[3].text=="Mine Crystals","all-turret option added")
check(#t.rows[3][5].properties.options==3,"missile turret can select crystal mode")
check(#t.rows[5][5].properties.options==2,"armed button unchanged")
t.rows[1][5].handlers.onDropDownConfirmed(nil,vgo.mode)
check(nativeCalls==0 and events[#events][3][3]=="all" and events[#events][3][4],"virtual mode handled without native enum call")
t.rows[2][5].handlers.onDropDownConfirmed(nil,"attackenemies")
check(nativeCalls==1 and not events[#events][3][4],"native mode passed through and overlay disabled")
t.rows[4][5].handlers.onDropDownConfirmed(nil,vgo.mode)
check(events[#events][3][2]==104 and events[#events][3][3]=="group","group uses actual representative")
local oldHook=map.setupLoadoutInfoSubmenuRows;vgo.install();check(map.setupLoadoutInfoSubmenuRows==oldHook,"install idempotent")
local cap={rows={}};map.setupLoadoutInfoSubmenuRows("ship",cap,20);check(#cap.rows[1][5].properties.options==3,"large ship can select crystal mode")
local xl={rows={}};map.setupLoadoutInfoSubmenuRows("ship",xl,40);check(#xl.rows[2][5].properties.options==3,"XL ship can select per-turret crystal mode")
local npc={rows={}};map.setupLoadoutInfoSubmenuRows("ship",npc,30);check(#npc.rows[1][5].properties.options==2,"NPC ship excluded")
local out={rows={}};outfitter.displayWeaponModeSelection(out,"turret",1,{})
out.rows[1][7].handlers.onDropDownConfirmed(nil,vgo.mode);check(outfitter.upgradeplan.turret[1].weaponmode=="defend","virtual ID never enters upgrade plan")
out.rows[1][7].handlers.onDropDownConfirmed(nil,"attackenemies");check(outfitter.upgradeplan.turret[1].weaponmode=="attackenemies","native outfitter option preserved")
blackboard[10]={['$vgo_ui']={{10,false,6,'Mining crystals',{{101,true},{104,false}}}}};callbacks['VGO.Install'](nil,10);local saved={rows={}};map.setupLoadoutInfoSubmenuRows("ship",saved,10);check(saved.rows[2][5].properties.startOption()==vgo.mode,"saved per-turret selection read")

-- Native receipt data and the actual published UIX callback contract, without a frame/widget API.
-- FFI is mocked here; the game owns the real TransactionLogEntry buffer and database.
local nativeRows, registered, setCalls = {}, {}, 0
local function inWindow(starttime,endtime)
    local rows={};for _,entry in ipairs(nativeRows) do if entry.time >= starttime and entry.time <= endtime then rows[#rows+1]=entry end end
    return rows
end
package.preload.ffi=function()
    return {C={
        GetPlayerID=function() return 10 end,
        GetNumTransactionLog=function(_,starttime,endtime) return #inWindow(starttime,endtime) end,
        GetTransactionLog=function(buffer,_,_,starttime,endtime)
            local rows=inWindow(starttime,endtime);for i,entry in ipairs(rows) do buffer[i-1]=entry end;return #rows
        end,
    },new=function() return {} end,string=function(value) return value end}
end
function SetNPCBlackboard(player,key,value) blackboard[player]=blackboard[player] or {};blackboard[player][key]=value;setCalls=setCalls+1 end
local originalCreate=function() return 'untouched vanilla screen' end
local originalSearch=function() return 'untouched native search' end
Helper.createTransactionLog,Helper.transactionLogSearchHelper=originalCreate,originalSearch
Helper.transactionLogData={container=10}
local ledger=dofile(root..'/ui/vardath_income_ledger.lua')
ledger.install(nil,10)
check(not ledger.installed,'Protected UI without UIX callback remains usable')
check(Helper.createTransactionLog==originalCreate and Helper.transactionLogSearchHelper==originalSearch,'no layout or search override')
function Helper.registerCallback(name,callback,id) registered[id]={name,callback} end
ledger.install(nil,10)
check(ledger.installed and registered.VardathNativeIncome[1]=='createTransactionLog_on_before_adding_entry','published callback only')
local function pay(seq,at,key,label,credits,kind)
    local board=blackboard[10];board['$vardath_income_seq']=seq
    board['$vardath_income']=board['$vardath_income'] or {}
    board['$vardath_income'][#board['$vardath_income']+1]={seq,at,key,label,credits,10,'Test ship','Verified completed work',kind or 'script_add'}
    board['$vardath_income_totals']={{key,label,credits*seq,seq}}
    callbacks['Vardath.NativeIncome.Payment'](nil,10)
end
local function native(id,at,cents,kind)
    local row={entryid=id,time=at,money=cents,eventtype=kind or 'script_add'};nativeRows[#nativeRows+1]=row;return row
end
local function display(id,at,credits,kind)
    return {entryid=id,time=at,money=credits,eventtype=kind or 'script_add',eventtypename='Mission reward',description='Native description',partnername='ARG'}
end
native('9007199254740993',100,500000000)
pay(1,100,'occupation_5','Galactic Sightseeing Tour',5000000)
local entry=display('9007199254740993',100,5000000)
local result=ledger.onEntry(entry)
check(result==entry and entry.eventtypename=='Galactic Sightseeing Tour - Test ship','real luxury fare labelled in native row')
check(entry.entryid=='9007199254740993' and entry.money==5000000 and entry.eventtype=='script_add','64-bit identity, amount and type preserved')
check(entry.partnername=='ARG' and entry.description:find('Verified completed work',1,true),'native partner and service detail preserved')
check(entry.description:find('lifetime income:',1,true),'job total is text, never an extra money row')
local calls=setCalls
local again=dofile(root..'/ui/vardath_income_ledger.lua')
check(again==ledger and setCalls==calls,'two extensions share one adapter without duplicate payments')
-- Same-value, same-frame receipts are bound immediately to different real IDs.
native('9007199254740994',200,20000000);pay(2,200,'builder_hire','Builder hiring fee',200000)
native('9007199254740995',200,20000000);pay(3,200,'builder_hire','Builder hiring fee',200000)
check(ledger.claimed[2]~=ledger.claimed[3],'identical simultaneous payments have separate native identities')
check(ledger.onEntry(display('9007199254740995',200,200000)).eventtypename=='Builder hiring fee - Test ship','second builder payment labelled')
local unrelated=display('unrelated',200,200000,'trade')
check(ledger.onEntry(unrelated).eventtypename=='Mission reward','unrelated trade remains untouched')
local foreign=display('other-account',100,5000000)
Helper.transactionLogData.container=20
check(ledger.onEntry(foreign).eventtypename=='Mission reward','other account not annotated with player receipts')
Helper.transactionLogData.container=10
-- Do not invent a receipt row when the engine has no individual transaction left.
pay(4,250,'occupation_2','Galactic Taxi Service',80000)
check(ledger.claimed[4]==nil,'missing native record is not fabricated')
-- Existing identical old rows are ambiguous; do not claim them by amount alone.
native('ambiguous-a',300,8000000);native('ambiguous-b',300,8000000)
pay(5,300,'occupation_2','Galactic Taxi Service',80000)
local ambiguous=display('ambiguous-a',300,80000)
check(ledger.onEntry(ambiguous).eventtypename=='Mission reward','ambiguous native rows remain vanilla')
-- Collection sales use a real transfer, not a reward or a second payment.
native('broker-sale',400,100000,'transfer');pay(6,400,'occupation_6','Autonomous Crystal Miner',1000,'transfer')
check(ledger.onEntry(display('broker-sale',400,1000,'transfer')).eventtypename=='Autonomous Crystal Miner - Test ship','actual inventory sale transfer labelled')
local rowCount=#nativeRows;calls=setCalls
ledger.onEntry(display('broker-sale',400,1000,'transfer'))
check(#nativeRows==rowCount and setCalls==calls,'rendering never adds a payment or writes a transaction')
-- Protection/callback failures may remove descriptions, never the native screen.
local oldRead=GetNPCBlackboard;GetNPCBlackboard=function() error('protected read') end
ledger.sequence=nil
local safe=display('failure',100,1)
check(ledger.onEntry(safe)==safe,'data failure returns the original native row')
GetNPCBlackboard=oldRead
Helper.registerCallback=nil
check(Helper.createTransactionLog()== 'untouched vanilla screen','native renderer remains callable without callback support')
print(string.format('PASS: %d Lua contract checks (mock menu/data APIs; no X4 runtime)',checks))
