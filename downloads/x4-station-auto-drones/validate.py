#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile
root=Path(__file__).resolve().parent
mod=root/'vardath_station_auto_drones'
required={'content.xml','ui.xml','README.md','md/vardath_station_auto_drones.xml','ui/vardath_station_auto_drones.lua'}
assert set(str(x.relative_to(mod)) for x in mod.rglob('*') if x.is_file())==required
for f in mod.rglob('*.xml'): ET.parse(f)
assert ET.parse(mod/'content.xml').getroot().get('id')=='vardath_station_auto_drones'
d=ET.parse(mod/'md/vardath_station_auto_drones.xml')
assert d.find('.//cue[@name="ManagePlayerStations"][@checkinterval="1min"]') is not None
assert d.find('.//create_control_entity[@post="controlpost.manager"]') is not None
assert len(d.findall('.//find_module[@checkoperational="true"]'))==2
lua=(mod/'ui/vardath_station_auto_drones.lua').read_text()
assert '{60,5,5,30}' in lua and '{90,5,5,0}' in lua
assert 'UpdateSupplyOverrides' in lua and 'GetUnitStorageData' in lua
archive=root/'vardath_station_auto_drones_TEST.zip'
if archive.exists():
 with ZipFile(archive) as z:
  assert z.testzip() is None
  assert set(z.namelist())=={'vardath_station_auto_drones/'+p for p in required}
  for p in required:
   assert z.read('vardath_station_auto_drones/'+p)==(mod/p).read_bytes()
print('Static X4 station automation checks passed. In-game testing remains necessary.')
