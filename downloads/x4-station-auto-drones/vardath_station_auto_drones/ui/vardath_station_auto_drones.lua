-- Vardath Automatic Station Drones v1.02
-- The MD cue sends ONE station roster via player.entity's blackboard.
-- Set the Logical Overview's auto drone supply-order targets; no spawned drones.
-- The one-roster bridge also supports old saves and detects missing Lua callbacks.
local ffi = require('ffi')
local C = ffi.C
ffi.cdef[[
 typedef uint64_t UniverseID;
 UniverseID GetPlayerID(void);
 typedef struct { const char* macro; int amount; } SupplyOverride;
 uint32_t GetNumSupplyOrders(UniverseID containerid, bool defaultorders);
 uint32_t GetSupplyOrders(SupplyOverride* result, uint32_t resultlen, UniverseID containerid, bool defaultorders);
 void UpdateSupplyOverrides(UniverseID containerid, SupplyOverride* overrides, uint32_t numoverrides);
 void SetSupplyManual(UniverseID containerid, const char* type, bool onoff);
 bool IsSupplyManual(UniverseID containerid, const char* type);
 void UpdateProductionTradeOffers(UniverseID containerid);
]]
local TYPES={
 {storage='transport', manual='units_trade'},
 {storage='defence',   manual='units_defence'},
 {storage='repair',    manual='units_repair'},
 {storage='build',     manual='units_build'},
}
local function log(s)
 if type(DebugError)=='function' then DebugError('[Vardath Auto Drones] '..tostring(s)) end
end
local function b(x) return x==true or x==1 or x=='true' end
local function get64(luaID)
 if luaID==nil then return nil end
 -- MD -> Lua references can arrive as IDs, userdata, or "ID: <digits>".
 -- Passing "ID: <digits>" unmodified is not a valid numeric conversion.
 local raw=tostring(luaID)
 local numeric=raw:match('ID:%s*(%d+)') or raw:match('^%s*(%d+)')
 local ok,id=pcall(ConvertStringTo64Bit,numeric or raw)
 if ok and id and tostring(id)~='0' then return id end
 return nil
end
local function getUnits(id,kind)
 local ok,res
 if kind then ok,res=pcall(GetUnitStorageData,id,kind)
 else ok,res=pcall(GetUnitStorageData,id) end
 if ok and type(res)=='table' then return res end
 return nil
end
local function readOrders(id)
 local ok,n=pcall(C.GetNumSupplyOrders,id,false)
 if not ok or not n then return nil,'GetNumSupplyOrders failed' end
 n=tonumber(n)
 if not n or n<0 or n>5000 then return nil,'invalid supply order count' end
 local map={}
 if n==0 then return map end
 local buf=ffi.new('SupplyOverride[?]',n)
 local success,got=pcall(C.GetSupplyOrders,buf,n,id,false)
 if not success or tonumber(got)~=n then return nil,'GetSupplyOrders incomplete' end
 for i=0,n-1 do
  if buf[i].macro==nil then return nil,'null supply macro' end
  map[ffi.string(buf[i].macro)]=tonumber(buf[i].amount) or 0
 end
 return map
end
local function writeOrders(id,map)
 local keys={}
 for macro in pairs(map) do keys[#keys+1]=macro end
 table.sort(keys)
 local buf=ffi.new('SupplyOverride[?]',#keys)
 local keep={}
 for i,macro in ipairs(keys) do
  local str=ffi.new('char[?]',#macro+1)
  ffi.copy(str,macro)
  keep[#keep+1]=str
  buf[i-1].macro=str
  buf[i-1].amount=math.max(0,math.floor(tonumber(map[macro]) or 0))
 end
 return pcall(C.UpdateSupplyOverrides,id,buf,#keys)
end
local function allocation(cap,weights)
 local a,f,used={},{},0
 for i,w in ipairs(weights) do
  local raw=cap*w/100
  a[i]=math.floor(raw)
  f[#f+1]={i=i,remainder=raw-a[i]}
  used=used+a[i]
 end
 table.sort(f,function(x,y)
  if x.remainder==y.remainder then return x.i<y.i end
  return x.remainder>y.remainder
 end)
 for j=1,cap-used do
  local k=f[(j-1)%#f+1].i
  a[k]=a[k]+1
 end
 return a
end
local function apply(station)
 local id=get64(station)
 if not id then return 'error','station ID could not be converted: '..tostring(station) end
 local luaID=ConvertStringToLuaID(tostring(id))
 -- A wharf and a shipyard may have different ship-building flags, so check all.
 local canBuild,isWharf,isShipyard=GetComponentData(luaID,'canbuildships','iswharf','isshipyard')
 local shipBuilder=b(canBuild) or b(isWharf) or b(isShipyard)
 local shared=getUnits(id)
 if not shared then return 'error','GetUnitStorageData failed for station '..tostring(id) end
 local cap=math.floor(tonumber(shared.capacity) or 0)
 if cap<=0 then return 'skipped','no drone storage yet' end
 local desired=allocation(cap,shipBuilder and {60,5,5,30} or {90,5,5,0})
 local before,readErr=readOrders(id)
 if not before then return 'error',readErr end
 local after={}
 for macro,n in pairs(before) do after[macro]=n end -- preserve missile orders and all unrelated types
 local lists,stocks,preferred={}, {}, {}
 local totalStored=0
 local missing={}
 for i,t in ipairs(TYPES) do
  local rows=getUnits(id,t.storage) or {}
  lists[i]=rows
  local current=0
  local maxScore=-1
  for _,row in ipairs(rows) do
   local num=math.max(0,math.floor(tonumber(row.amount) or 0))
   current=current+num
   if type(row.macro)=='string' and row.macro~='' then
    local score=num+(((before[row.macro] or 0)>0) and 100000 or 0)
    if score>maxScore then preferred[i]=row.macro;maxScore=score end
   end
  end
  stocks[i]=current
  totalStored=totalStored+current
  if not preferred[i] and desired[i]>0 then missing[#missing+1]=t.storage end
 end
 if #missing>0 then
  return 'error','no available drone macro(s) for '..table.concat(missing,', ')..' station '..tostring(id)
 end
 -- Requirements, not inventory: Logical Overview's auto-mode overrides
 -- express the target total even when the station is physically full of an
 -- old (unbalanced) drone mix. Never cap the CONFIGURED targets by free
 -- space or existing stock. X4 itself does not spawn, discard or transfer
 -- any physical drones when supply-order targets are changed.
 local changed=false
 local touched={}
 for i,t in ipairs(TYPES) do
  for _,row in ipairs(lists[i]) do
   local macro=row.macro
   if type(macro)=='string' and macro~='' then
    -- Auto supply mode uses requested absolute totals (manual uses inbound).
    -- Non-preferred variants get no new orders, but existing units remain.
    local newValue=(macro==preferred[i]) and desired[i] or 0
    if after[macro]~=newValue then changed=true end
    after[macro]=newValue
    touched[macro]=newValue
   end
  end
 end
 local needsAuto=false
 for _,t in ipairs(TYPES) do
  local ok,manual=pcall(C.IsSupplyManual,id,t.manual)
  if not ok then return 'error','IsSupplyManual failed: '..t.manual end
  if manual then needsAuto=true end
 end
 if not changed and not needsAuto then return 'unchanged','already at target' end
 -- Toggle auto THEN write the full override map; otherwise a prior manual
 -- inbound-quantity may be incorrectly interpreted as an automatic target.
 for _,t in ipairs(TYPES) do
  local ok=pcall(C.SetSupplyManual,id,t.manual,false)
  if not ok then return 'error','SetSupplyManual failed: '..t.manual end
 end
 if not writeOrders(id,after) then return 'error','UpdateSupplyOverrides failed' end
 pcall(C.UpdateProductionTradeOffers,id)
 -- Read back from the engine rather than trusting the successful FFI call.
 local actual,err=readOrders(id)
 if not actual then return 'error','readback: '..tostring(err) end
 for macro,value in pairs(touched) do
  if (actual[macro] or 0)~=value then
   return 'error',string.format('readback mismatch for %s: wanted %s, got %s',macro,value,tostring(actual[macro]))
  end
 end
 return 'changed','target updated'
end
local function onRoster(_,seq)
 -- GetNPCBlackboard/SetNPCBlackboard take a LUA component ID, not the
 -- UniverseID cdata used by C's supply-order functions. This distinction
 -- matters: a 64-bit ID here silently prevents the roster from being read.
 local ok,id=pcall(C.GetPlayerID)
 local idOk,playerID
 if ok and id and id~=0 then idOk,playerID=pcall(ConvertStringToLuaID,tostring(id)) end
 if not idOk or not playerID or playerID==0 then
  log('ERROR cannot convert X4 player ID to Lua component ID')
  return
 end
 local roster=GetNPCBlackboard(playerID,'$VAD_Roster')
 local request=tonumber(GetNPCBlackboard(playerID,'$VAD_Seq')) or tonumber(seq) or 0
 local stats={seq=request,seen=0,changed=0,unchanged=0,skipped=0,errors=0}
 if type(roster)~='table' then
  stats.errors=1
  log('ERROR MD station roster missing or not a Lua table')
 else
  for _,station in ipairs(roster) do
   stats.seen=stats.seen+1
   local ok,status,detail=pcall(apply,station)
   if not ok then
    stats.errors=stats.errors+1
    log('ERROR station '..tostring(station)..': '..tostring(status))
   elseif status=='error' then
    stats.errors=stats.errors+1
    log('ERROR station '..tostring(station)..': '..tostring(detail))
   elseif status=='changed' then
    stats.changed=stats.changed+1
   elseif status=='unchanged' then
    stats.unchanged=stats.unchanged+1
   else
    stats.skipped=stats.skipped+1
   end
  end
 end
 -- The MD cue can alert the player on a missing bridge or engine readback
 -- mismatch, and the status is inspectable in saved player blackboard.
 SetNPCBlackboard(playerID,'$VAD_Stats',stats)
 SetNPCBlackboard(playerID,'$VAD_Ack',request)
 if stats.changed>0 or stats.errors>0 then
  log(string.format('Scan %d: stations=%d, updated=%d, unchanged=%d, skipped=%d, errors=%d',
   request,stats.seen,stats.changed,stats.unchanged,stats.skipped,stats.errors))
 end
end
RegisterEvent('Vardath.StationAutoDrones.ApplyRoster',function(_,seq)
 local ok,err=pcall(onRoster,nil,seq)
 if not ok then log('ERROR unhandled roster failure: '..tostring(err)) end
end)
