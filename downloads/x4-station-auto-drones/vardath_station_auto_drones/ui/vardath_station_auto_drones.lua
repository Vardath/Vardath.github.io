-- Vardath automatic station drones. Works through X4's Logical Overview supply orders.
-- No menu, free physical drones, or changes to non-player stations.
local ffi=require('ffi')
local C=ffi.C
-- Use the same SupplyOverride ABI as the base-game UI and other X4 UI mods.
ffi.cdef[[
 typedef uint64_t UniverseID;
 typedef struct { const char* macro; int amount; } SupplyOverride;
 uint32_t GetNumSupplyOrders(UniverseID containerid, bool defaultorders);
 uint32_t GetSupplyOrders(SupplyOverride* result, uint32_t resultlen, UniverseID containerid, bool defaultorders);
 void UpdateSupplyOverrides(UniverseID containerid, SupplyOverride* overrides, uint32_t numoverrides);
 void SetSupplyManual(UniverseID containerid, const char* type, bool onoff);
 bool IsSupplyManual(UniverseID containerid, const char* type);
 void UpdateProductionTradeOffers(UniverseID containerid);
]]
local TYPES={
 {storage='transport',manual='units_trade'},
 {storage='defence',manual='units_defence'},
 {storage='repair',manual='units_repair'},
 {storage='build',manual='units_build'}
}
local function id64(x)
 if x==nil then return nil end
 local str=tostring(x)
 local n=str:match('ID:%s*(%d+)') or str:match('^(%d+)$')
 local ok,v=pcall(ConvertStringTo64Bit,n or str)
 if ok and v and tostring(v)~='0' then return v end
end
local function units(id,category)
 local ok,data
 if category then ok,data=pcall(GetUnitStorageData,id,category)
 else ok,data=pcall(GetUnitStorageData,id) end
 if ok and type(data)=='table' then return data end
end
local function read(id)
 local ok,n=pcall(C.GetNumSupplyOrders,id,false)
 if not ok then return nil end
 n=tonumber(n)
 if not n or n<0 or n>5000 then return nil end
 local out={}
 if n==0 then return out end
 local buffer=ffi.new('SupplyOverride[?]',n)
 local success,got=pcall(C.GetSupplyOrders,buffer,n,id,false)
 if not success or tonumber(got)~=n then return nil end
 for i=0,n-1 do
  if buffer[i].macro==nil then return nil end
  out[ffi.string(buffer[i].macro)]=tonumber(buffer[i].amount) or 0
 end
 return out
end
local function write(id,orders)
 local keys={}
 for k in pairs(orders) do keys[#keys+1]=k end
 table.sort(keys)
 local buf=ffi.new('SupplyOverride[?]',#keys)
 local keep={}
 for i,k in ipairs(keys) do
  local str=ffi.new('char[?]',#k+1)
  ffi.copy(str,k)
  keep[#keep+1]=str
  buf[i-1].macro=str
  buf[i-1].amount=math.max(0,math.floor(orders[k]))
 end
 return pcall(C.UpdateSupplyOverrides,id,buf,#keys)
end
local function distribute(total,percent)
 local values,remainders,sum={},{},0
 for i,p in ipairs(percent) do
  local float=total*p/100
  values[i]=math.floor(float)
  sum=sum+values[i]
  remainders[#remainders+1]={i=i,f=float-values[i]}
 end
 table.sort(remainders,function(a,b)
  if a.f==b.f then return a.i<b.i end
  return a.f>b.f
 end)
 for j=1,total-sum do
  local i=remainders[(j-1)%#remainders+1].i
  values[i]=values[i]+1
 end
 return values
end
local function apply(station)
 local id=id64(station)
 if not id then return end
 local isShipBuilder=GetComponentData(ConvertStringToLuaID(tostring(id)),'canbuildships')
 local shared=units(id)
 if not shared then return end
 local capacity=math.floor(tonumber(shared.capacity) or 0)
 if capacity<=0 then return end
 local targets=distribute(capacity,(isShipBuilder==true or isShipBuilder==1) and {60,5,5,30} or {90,5,5,0})
 local overrides=read(id)
 if not overrides then return end -- UpdateSupplyOverrides is a FULL replacement: preserve unrelated missile entries.
 local storage,choice,stock={}, {}, {}
 local totalStock=0
 for i,t in ipairs(TYPES) do
  local list=units(id,t.storage) or {}
  storage[i]=list
  local bestScore=-1
  stock[i]=0
  for _,e in ipairs(list) do
   local amount=math.max(0,tonumber(e.amount) or 0)
   stock[i]=stock[i]+amount
   if type(e.macro)=='string' and e.macro~='' then
    local score=amount+(((overrides[e.macro] or 0)>0) and 100000 or 0)
    if score>bestScore then bestScore=score;choice[i]=e.macro end
   end
  end
  totalStock=totalStock+stock[i]
 end
 -- Unsupported categories relinquish their allocation to cargo.
 for i=2,4 do
  if not choice[i] then targets[1]=targets[1]+targets[i];targets[i]=0 end
 end
 if not choice[1] then
  for i=2,4 do if choice[i] then targets[i]=targets[i]+targets[1];break end end
  targets[1]=0
 end
 local remaining=math.max(0,capacity-totalStock)
 local inbound={}
 for i=1,4 do
  inbound[i]=math.min(math.max(0,targets[i]-stock[i]),remaining)
  remaining=remaining-inbound[i]
 end
 local changed=false
 for i,t in ipairs(TYPES) do
  for _,e in ipairs(storage[i]) do
   if type(e.macro)=='string' then
    local desired=(e.macro==choice[i]) and (stock[i]+inbound[i]) or 0
    if overrides[e.macro]~=desired then overrides[e.macro]=desired;changed=true end
   end
  end
 end
 local resetManual=false
 for _,t in ipairs(TYPES) do
  local ok,manual=pcall(C.IsSupplyManual,id,t.manual)
  if ok and manual then resetManual=true end
 end
 if not changed and not resetManual then return end
 for _,t in ipairs(TYPES) do pcall(C.SetSupplyManual,id,t.manual,false) end
 if changed and not write(id,overrides) then return end
 pcall(C.UpdateProductionTradeOffers,id)
end
RegisterEvent('Vardath.StationAutoDrones.Apply',function(_,station)
 local ok,err=pcall(apply,station)
 if not ok and type(DebugError)=='function' then
  DebugError('[Vardath Auto Drones] '..tostring(err))
 end
end)
