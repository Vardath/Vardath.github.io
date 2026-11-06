-- Executable tests against native-shaped menu/widget data. No X4 runtime is simulated or claimed.
local root = arg[1] or "downloads/x4-galactic-occupations/vardath_galactic_occupations"
local unpack = unpack or table.unpack
local checks, nativeCalls, events, callbacks, blackboard = 0, 0, {}, {}, {}
local objects = { [10]={owner="player",macro="ship_m"},[20]={owner="player",macro="ship_l"},[30]={owner="argon",macro="ship_m"},[101]={macro="beam"},[102]={macro="missileturret"},[104]={macro="beam"} }
function ConvertStringToLuaID(v) return tonumber(v) end
function ConvertStringTo64Bit(v) return tonumber(v) end
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
check(#t.rows[3][5].properties.options==2,"missile turret unchanged")
check(#t.rows[5][5].properties.options==2,"armed button unchanged")
t.rows[1][5].handlers.onDropDownConfirmed(nil,vgo.mode)
check(nativeCalls==0 and events[#events][3][3]=="all" and events[#events][3][4],"virtual mode handled without native enum call")
t.rows[2][5].handlers.onDropDownConfirmed(nil,"attackenemies")
check(nativeCalls==1 and not events[#events][3][4],"native mode passed through and overlay disabled")
t.rows[4][5].handlers.onDropDownConfirmed(nil,vgo.mode)
check(events[#events][3][2]==104 and events[#events][3][3]=="group","group uses actual representative")
local oldHook=map.setupLoadoutInfoSubmenuRows;vgo.install();check(map.setupLoadoutInfoSubmenuRows==oldHook,"install idempotent")
local cap={rows={}};map.setupLoadoutInfoSubmenuRows("ship",cap,20);check(#cap.rows[1][5].properties.options==2,"capital ship excluded")
local npc={rows={}};map.setupLoadoutInfoSubmenuRows("ship",npc,30);check(#npc.rows[1][5].properties.options==2,"NPC ship excluded")
local out={rows={}};outfitter.displayWeaponModeSelection(out,"turret",1,{})
out.rows[1][7].handlers.onDropDownConfirmed(nil,vgo.mode);check(outfitter.upgradeplan.turret[1].weaponmode=="defend","virtual ID never enters upgrade plan")
out.rows[1][7].handlers.onDropDownConfirmed(nil,"attackenemies");check(outfitter.upgradeplan.turret[1].weaponmode=="attackenemies","native outfitter option preserved")
blackboard[101]={['$vgo_minecrystals']=true};callbacks['VGO.Install']();local saved={rows={}};map.setupLoadoutInfoSubmenuRows("ship",saved,10);check(saved.rows[2][5].properties.startOption()==vgo.mode,"saved per-turret selection read")
-- Minimal native-shaped widget builder for the income section.
local function uiCell()
    local c={properties={},handlers={}}
    function c:setColSpan(_) return self end
    function c:createIcon(icon,_) self.icon=icon;self.type="icon";return self end
    function c:createText(text,_) self.text=text;self.type="text";return self end
    function c:createDropDown(options,properties) self.properties=properties;self.options=options;return self end
    function c:createButton(properties) self.properties=properties;return self end
    function c:setText(text) self.text=text;return self end
    return c
end
local testLedgerData, testModern
local function frame()
    local f={content={}}
    function f:addTable(columns,properties)
        local t={type="table",numcolumns=columns,properties=properties,rows={}}
        function t:setColWidthPercent(...) return self end
        function t:addRow(data,properties)
            local r={rowdata=data,properties=properties,index=#self.rows+1,table=self};for i=1,columns do r[i]=uiCell();r[i].row=r end;self.rows[#self.rows+1]=r;return r
        end
        function t:setSelectedRow(index) self.selectedrow=index end
        function t:setTopRow(index) self.toprow=index end
        function t:getFullHeight() return self.rows[1] and self.rows[1][1].properties.height or #self.rows*22 end
        self.content[#self.content+1]=t;return t
    end
    return f
end
Helper.viewHeight=900;Helper.borderSize=2;Helper.frameBorder=8
function Helper.createTransactionLog(f)
    local native
    if testModern then
        local navigation=f:addTable(8,{tabOrder=1,x=8,y=8,width=480})
        navigation:addRow(false,{fixed=true})[1]:setColSpan(8):createText("Transaction Log")
        local header=navigation:addRow("search",{fixed=true});header[5]:setText("1 / 1")
        native=f:addTable(7,{tabOrder=2,x=8,y=54,maxVisibleHeight=830,width=480})
        native:addRow(false,{fixed=true})[2]:setColSpan(2):createText("Transaction")
        if testLedgerData then testLedgerData.pageEditBox=header[5] end
    else
        native=f:addTable(9,{tabOrder=1,y=8,maxVisibleHeight=884})
        if testLedgerData then
            native:addRow(false,{fixed=true})[1]:setColSpan(9):createText("Transaction Log")
            local header=native:addRow("search",{fixed=true});header[6]:setText("1 / 1")
        end
    end
    if testLedgerData then Helper.transactionLogData=testLedgerData end
    local g=f:addTable(4,{tabOrder=3,x=500,y=8,width=800});local r=g:addRow(false,{})
    r[1].type="graph";r[1].properties.height=500
    if testModern then
        local range=f:addTable(3,{tabOrder=4,x=500,y=520,width=800});range:addRow(false,{})[1].properties.height=44
    end
    return "native ledger"
end
blackboard[10]={['$vardath_income_seq']=2,['$vardath_income']={{1,100,"occupation_5","Galactic Sightseeing Tour",5000000,10,"Astrid Tours","10 passengers; 10 sites; 5 sectors"},{2,200,"builder_hire","Builder hiring fee",200000,10,"Builder","ARG: Test station"}},['$vardath_income_totals']={{"occupation_5","Galactic Sightseeing Tour",5000000,1},{"builder_hire","Builder hiring fee",200000,1}}}
function Helper.transactionLogSearchHelper(entry,text)
    return (entry.eventtypename.." "..entry.description.." "..entry.partnername.." "..entry.warename.." "..entry.partnername_secondary):lower():find(text:lower(),1,true)~=nil
end
local ledger=dofile(root.."/ui/vardath_income_ledger.lua");callbacks['Vardath.IncomeLedger.Install'](nil,10)
local f=frame();check(Helper.createTransactionLog(f,10,{height=884},function()end,{})=="native ledger","native ledger return preserved")
check(#f.content==3 and f.content[1].numcolumns==9,"income panel added without replacing native transactions")
local allText={};for _,r in ipairs(f.content[3].rows) do for i=1,4 do if r[i].text then allText[#allText+1]=r[i].text end end end
check(table.concat(allText," "):find("5000000 Cr",1,true) and table.concat(allText," "):find("200000 Cr",1,true),"actual amounts and both providers displayed")
ledger.view="totals";ledger.job="occupation_5";local totals=frame();Helper.createTransactionLog(totals,10,{height=884},function()end,{});check(#totals.content[3].rows==3,"per-job lifetime filter works")
local station=frame();Helper.createTransactionLog(station,20,{height=884},function()end,{});check(#station.content==2,"non-player station ledger unchanged")
local hook=Helper.createTransactionLog;dofile(root.."/ui/vardath_income_ledger.lua");check(Helper.createTransactionLog==hook,"second extension cannot duplicate income panel")
-- Vanilla-list integration: actual native identifiers/amounts, simultaneous rewards and receipt-only credits.
blackboard[10]['$vardath_income_now']=1000
local function nativeData(entries)
    return {accountLogUnfiltered=entries,accountLog=entries,curPage=1,numPages=1,searchtext="",xZoom=6,graphdata={{t=1000,y=7000000}},expandedEntries={}}
end
local payment={time=100,money=5000000,entryid=9001,eventtype="reward",eventtypename="Reward",description="",partnername="",ware=""}
local matched=nativeData({payment});ledger.prepareNative(matched)
check(payment.entryid==9001 and payment.money==5000000 and payment.time==100,"native ID, money and time preserved")
check(payment.eventtypename:find("Galactic Sightseeing Tour",1,true) and matched._vardathUsed[1],"verified payment labels actual vanilla entry")
local a={time=200,money=200000,entryid=9002,eventtype="reward",eventtypename="Reward",description="",partnername="",ware=""}
local b={time=200,money=200000,entryid=9003,eventtype="reward",eventtypename="Other reward",description="",partnername="",ware=""}
local ambiguous=nativeData({a,b});ledger.prepareNative(ambiguous)
check(not ambiguous._vardathUsed[2] and ambiguous._vardathOverlap[2] and a.eventtypename=="Reward","ambiguous equal-value native entries are not falsely relabeled")
Helper.transactionLogConfig={transactionLogPage=1,zoomSteps={[6]={zoom=60}}}
Helper.transactionLogData=nil;testLedgerData=nativeData({})
local active
local function refreshNative() active=frame();Helper.createTransactionLog(active,10,{height=884},refreshNative,{}) end
refreshNative()
local main=active.content[1]
check(#main.rows==4 and main.rows[3][2].text:find("Builder hiring fee",1,true),"receipt appears in the existing vanilla list without a native detailed row")
check(main.rows[3].rowdata==false,"receipt never masquerades as native transaction ID")
check(main.rows[2][8].properties.active and Helper.transactionLogData.numPages==2,"vanilla paging includes receipt-only income")
main.rows[2][8].handlers.onClick()
check(active.content[1].rows[3][2].text:find("Galactic Sightseeing Tour",1,true) and Helper.transactionLogData.curPage==2,"vanilla next-page control reaches earlier income")
testLedgerData=nativeData({});testLedgerData.searchtext="10 sites";Helper.transactionLogData=nil;refreshNative()
check(#active.content[1].rows==4 and active.content[1].rows[3][2].text:find("Galactic Sightseeing Tour",1,true),"vanilla text search includes receipt descriptions")
testLedgerData=nativeData({});blackboard[10]['$vardath_income_now']=10000;Helper.transactionLogData=nil;refreshNative()
check(#active.content[1].rows==3 and active.content[1].rows[3][2].text:find("No transactions",1,true),"vanilla time window excludes old receipts")
check(testLedgerData.graphdata[1].y==7000000,"native account graph balance is not replaced with income totals")
-- Equal-time/equal-amount payments are not assigned arbitrary ship labels.
local preserved=ledger.entries
ledger.entries={{11,200,"builder_hire","Builder hiring fee",200000,10,"Builder A","Fee"},{12,200,"builder_hire","Builder hiring fee",200000,10,"Builder B","Fee"}}
local simultaneous=nativeData({a,b});ledger.prepareNative(simultaneous)
check(not simultaneous._vardathUsed[11] and not simultaneous._vardathUsed[12] and simultaneous._vardathOverlap[11],"simultaneous identical credits use receipts instead of arbitrary native labels")
ledger.entries=preserved
-- Actual 9.00 layout: separate eight-column navigation, seven-column body and range bar.
testModern=true;blackboard[10]['$vardath_income_now']=1000;testLedgerData=nativeData({});Helper.transactionLogData=nil;refreshNative()
check(active.content[1].numcolumns==8 and active.content[2].numcolumns==7 and active.content[2].rows[2][3].text:find("Builder hiring fee",1,true),"9.00 native navigation/body layout receives payment descriptions")
active.content[1].rows[2][6].handlers.onClick()
check(active.content[2].rows[2][5].text:find("5000000 Cr",1,true) and Helper.transactionLogData.curPage==2,"9.00 native next-page button reaches earlier receipt")
check(active.content[5].properties.tabOrder==5 and active.content[5].properties.y>=active.content[4].properties.y+active.content[4]:getFullHeight(),"income preview does not overlap 9.00 native time-range controls")
blackboard[10]['$vardath_income_seq']=3;blackboard[10]['$vardath_income']={blackboard[10]['$vardath_income'][1]}
local currentPayment={time=100,money=5000000,entryid=9004,eventtype="reward",eventtypename="Reward",eventicon="reward",description="",partnername="",partnername_secondary="",ware="",warename=""}
testLedgerData=nativeData({currentPayment});testLedgerData.curEntryId=9004;Helper.transactionLogData=nil;refreshNative()
check(active.content[2].rows[2].rowdata==9004 and active.content[2].rows[2][3].text:find("Galactic Sightseeing Tour",1,true),"9.00 native entry keeps its real ID and receives its verified job label")
check(active.content[2].rows[2][2].icon=="reward" and active.content[2].selectedrow==2,"9.00 native icon and graph-selected transaction retained")
testLedgerData=nativeData({currentPayment});testLedgerData.searchtext="Sightseeing";Helper.transactionLogData=nil;refreshNative()
check(active.content[2].rows[2][3].text:find("Galactic Sightseeing Tour",1,true),"9.00 native search includes verified job labels")
print("PASS: "..checks.." executable UI contract checks; X4 runtime NOT RUN")
