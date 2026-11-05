#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile
root=Path(__file__).resolve().parent
mod=root/'vardath_station_auto_drones'
required={'content.xml','ui.xml','README.md','md/vardath_station_auto_drones.xml','ui/vardath_station_auto_drones.lua'}
files={str(x.relative_to(mod)) for x in mod.rglob('*') if x.is_file()}
assert files==required,(files,required)
for p in mod.rglob('*.xml'): ET.parse(p)
content=ET.parse(mod/'content.xml').getroot()
assert content.attrib['id']=='vardath_station_auto_drones'
assert int(content.attrib['version'])>=102
d=ET.parse(mod/'md/vardath_station_auto_drones.xml')
assert d.find('.//cue[@name="ManagePlayerStations"][@checkinterval="1min"]') is not None
assert d.find('.//create_control_entity[@post="controlpost.manager"]') is not None
assert len(d.findall('.//find_module[@checkoperational="true"]'))==2
assert len(d.findall('.//raise_lua_event[@name="\'Vardath.StationAutoDrones.ApplyRoster\'"]'))==1
assert d.find('.//set_value[@name="player.entity.$VAD_Roster"]') is not None
assert d.find('.//show_notification') is not None
lua=(mod/'ui/vardath_station_auto_drones.lua').read_text()
for snippet in ["{60,5,5,30}","{90,5,5,0}","UpdateSupplyOverrides","GetNPCBlackboard","SetNPCBlackboard","Vardath.StationAutoDrones.ApplyRoster","readback mismatch","ConvertStringToLuaID,tostring(id)","local newValue=(macro==preferred[i]) and desired[i] or 0","raw:match('ID:%s*(%d+)')"]:
 assert snippet in lua,snippet
# Largest remainder rounding exemplars, verified independently.
def alloc(cap,weights):
 base=[cap*p//100 for p in weights]
 residual=[(cap*p%100,i) for i,p in enumerate(weights)]
 for _,i in sorted(residual,key=lambda x:(-x[0],x[1]))[:cap-sum(base)]:base[i]+=1
 return base
for cap in [1,2,3,4,5,20,32,100,200,1000]:
 for weights in [[90,5,5,0],[60,5,5,30]]:
  x=alloc(cap,weights)
  assert sum(x)==cap,(cap,weights,x)
assert alloc(100,[90,5,5,0])==[90,5,5,0]
assert alloc(200,[60,5,5,30])==[120,10,10,60]
archive=root/'vardath_station_auto_drones_TEST.zip'
if archive.exists():
 with ZipFile(archive) as z:
  assert z.testzip() is None
  assert set(z.namelist())=={'vardath_station_auto_drones/'+p for p in required}
  for p in required:
   assert z.read('vardath_station_auto_drones/'+p)==(mod/p).read_bytes()
print('X4 station automation v1.02 source, XML and ZIP checks passed; game runtime still untested.')
