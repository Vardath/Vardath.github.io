#!/usr/bin/env python3
"""Kopis Mobile Forge static release QA; XML/ZIP checks are not X4 runtime tests."""
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile
root=Path(__file__).resolve().parent
mod=root/"vardath_kopis_production_cheat"
archive=root/"vardath_kopis_production_cheat_TEST.zip"
files={str(p.relative_to(mod)) for p in mod.rglob("*") if p.is_file()}
assert archive.exists()
with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  assert set(z.namelist())=={"vardath_kopis_production_cheat/"+f for f in files}
  for f in files:
    disk=(mod/f).read_bytes()
    assert disk==z.read("vardath_kopis_production_cheat/"+f), f
    if f.endswith(".xml"):
      ET.fromstring(disk)
manifest=ET.parse(mod/"content.xml").getroot()
assert manifest.get("id")=="vardath_kopis_production_cheat"
assert int(manifest.get("version"))>=102
assert manifest.find("./dependency[@id='ego_dlc_terran']") is not None
macro=ET.parse(mod/"assets/units/size_s/macros/ship_vardath_kopis_factory_macro.xml").getroot()
ship=macro.find("./macro[@name='ship_vardath_kopis_factory_macro']")
assert ship is not None
assert ship.find("./component").get("ref")=="ship_vardath_kopis_factory"
assert ship.find("./properties/storage").get("unit")=="512"
assert ship.find("./properties/storage").get("missile")=="5000"
assert ship.find("./properties/storage").get("deployable")=="5000"
assert ship.find("./properties/storage").get("countermeasure")=="500"
assert ship.find("./properties/people").get("capacity")=="250"
assert ship.find("./properties/physics").get("mass")=="1.6"
assert ship.find("./properties/physics/drag").get("forward")=="0.6"
assert {c.get("ref") for c in ship.findall("./connections/connection")} >= {"con_storage01","con_storage02","con_storage03"}
component=ET.parse(mod/"assets/units/size_s/ship_vardath_kopis_factory.xml").getroot()
assert component.find("./component[@name='ship_vardath_kopis_factory']") is not None
assert component.find(".//connection[@name='con_vardath_turret_01']") is not None
assert component.find(".//connection[@name='con_storage02']") is not None
# Regression: the copied 9.00 Terran Kopis uses ADVANCED, not STANDARD.
# A mismatched socket makes even valid Terran weapons vanish at the wharf.
gun_socket=component.find(".//connection[@name='con_weapon_01']")
assert gun_socket is not None
assert gun_socket.get("tags").split()==["advanced","combat","mining","platformcollision","small","weapon","symmetry","symmetry_right"]
assert component.find(".//connection[@name='defencenpc'][@tags='defence']") is not None
turret_socket=component.find(".//connection[@name='con_vardath_turret_01']")
assert turret_socket is not None and turret_socket.get("group")=="group_vardath_dorsal"
turret_component=ET.parse(mod/"assets/props/weaponsystems/energy/turret_vardath_kopis_s.xml").getroot()
turret=turret_component.find("./component[@name='turret_vardath_kopis_s'][@class='turret']")
assert turret is not None
turret_mount=turret.find("./connections/connection[@name='con_beam_turret_01']")
assert turret_mount is not None
for tag in ["advanced","combat","small","turret","unhittable"]:
  assert tag in turret_socket.get("tags").split(), tag
  assert tag in turret_mount.get("tags").split(), tag
assert "component" in turret_mount.get("tags").split()
assert turret.find("./connections/connection[@name='con_aimtarget_01']") is not None
turret_macro=ET.parse(mod/"assets/props/weaponsystems/energy/macros/turret_vardath_kopis_beam_macro.xml").getroot()
assert turret_macro.find("./macro/component").get("ref")=="turret_vardath_kopis_s"
assert turret_macro.find("./macro/properties/weapon") is not None

for t in ("container","solid","liquid"):
  data=ET.parse(mod/f"assets/units/size_s/macros/storage_vardath_kopis_{t}_macro.xml").getroot()
  storage=data.find("./macro/properties/cargo")
  assert storage.get("tags")==t and int(storage.get("max"))==1_000_000
bullet=ET.parse(mod/"assets/fx/weaponfx/macros/bullet_vardath_kopis_laser_macro.xml").getroot()
assert int(bullet.find("./macro/properties/damage").get("value"))>=90
weapon=ET.parse(mod/"assets/props/weaponsystems/standard/macros/weapon_vardath_kopis_laser_macro.xml").getroot()
assert weapon.find("./macro/properties/bullet").get("class")=="bullet_vardath_kopis_laser_macro"
assert weapon.find("./macro/component").get("ref")=="weapon_ter_s_laser_01_mk2"
wares=ET.parse(mod/"libraries/wares.xml").getroot()
assert wares.find(".//ware[@id='ship_vardath_kopis_factory']/component").get("ref")=="ship_vardath_kopis_factory_macro"
assert wares.find(".//ware[@id='weapon_vardath_kopis_laser']") is not None
for wareid, group in [('weapon_vardath_kopis_laser','weapons'),('weapon_vardath_kopis_beam','weapons'),('turret_vardath_kopis_beam','turrets')]:
  ware=wares.find(".//ware[@id='%s']" % wareid)
  assert ware is not None and ware.get("group")==group
  assert ware.find("./component").get("ref")==wareid+"_macro"
  assert {o.get("faction") for o in ware.findall("./owner")} >= {"terran","pioneers"}
load=ET.parse(mod/"libraries/loadouts.xml").getroot()
kit=load.find(".//loadout[@id='vardath_kopis_factory_kit']")
assert kit is not None and kit.get("macro")=="ship_vardath_kopis_factory_macro"
assert len(kit.findall("./ammunition/unit"))>=3
assert kit.find("./groups/turrets").get("group")=="group_vardath_dorsal"
md=ET.parse(mod/"md/vardath_kopis_mobile_forge.xml").getroot()
assert md.get("name")=="VardathKopisMobileForge"
producer=md.find(".//cue[@name='ProduceResources']")
supplier=md.find(".//cue[@name='DeliverBuildStorage']")
assert producer is not None and producer.get("checkinterval")=="10min"
assert supplier is not None and supplier.get("checkinterval")=="2min"
assert producer.find(".//do_for_each[@in='lookup.ware.list']") is not None
assert producer.find(".//add_cargo[@object='$Ship']") is not None
assert supplier.find(".//remove_cargo[@object='$Ship']") is not None
assert supplier.find(".//add_cargo[@object='$Station.buildstorage']") is not None
assert supplier.find(".//do_if[@value='not $DeliveredThisTick and $Station.exists and $Station.buildstorage.exists and $Ship.distanceto.{$Station} le 35km and ($Station.isplayerowned or $Station.trueowner.hasrelation.dock.{faction.player}) and ($Station.buildstorage.builds.queued.count + $Station.buildstorage.builds.inprogress.count gt 0)']") is not None
crew=md.find(".//cue[@name='GrowYakiCrew']")
assert crew is not None and crew.get("checkinterval")=="10min"
assert crew.find(".//get_character_definition[@faction='faction.yaki'][@tags='tag.service']") is not None
assert crew.find(".//create_npc_template[@role='entityrole.service'][@macro='$YakiCrewMacro']") is not None
assert crew.find(".//set_skill[@type='skilltype.engineering']") is not None
start=ET.parse(mod/"md/vardath_kopis_builder_start.xml").getroot()
spawn=start.find(".//cue[@name='AddKopisEscort']//do_all[@exact='10']")
assert spawn is not None and spawn.get("counter")=="$ForgeIndex"
assert len(spawn.findall("./create_ship"))==1
assert spawn.find("./create_ship[@macro='macro.ship_vardath_kopis_factory_macro']/owner[@exact='faction.player']") is not None
assert spawn.find("./create_ship/loadout[@ref='vardath_kopis_factory_kit']") is not None
assert md.find(".//add_blueprints") is not None
assert "ware.turret_vardath_kopis_beam" in md.find(".//add_blueprints").get("wares")
print(f"PASS: {len(files)} source/ZIP file matches, XML, cargo/crew, 10-start spawn, vanilla-compatible weapon socket, S turret template, owner equipment wares and build supply static invariants")
