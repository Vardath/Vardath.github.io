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
assert int(manifest.get("version"))>=105
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
assert component.find(".//connection[@name='con_vardath_turret_01']") is None
assert component.find(".//connection[@name='con_storage02']") is not None
# Regression: the copied 9.00 Terran Kopis uses ADVANCED, not STANDARD.
# A mismatched socket makes even valid Terran weapons vanish at the wharf.
gun_socket=component.find(".//connection[@name='con_weapon_01']")
assert gun_socket is not None
assert gun_socket.get("tags").split()==["advanced","combat","mining","platformcollision","small","weapon","symmetry","symmetry_right"]
assert component.find(".//connection[@name='defencenpc'][@tags='defence']") is not None
# No dorsal turret socket, but keep legacy macro/equipment files for save compatibility.
assert component.find(".//connection[@name='con_vardath_turret_01']") is None
assert (mod/"assets/props/weaponsystems/energy/turret_vardath_kopis_s.xml").exists()

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
  assert ware.find("./use[@threshold='0']") is not None
load=ET.parse(mod/"libraries/loadouts.xml").getroot()
kit=load.find(".//loadout[@id='vardath_kopis_factory_kit']")
assert kit is not None and kit.get("macro")=="ship_vardath_kopis_factory_macro"
assert len(kit.findall("./ammunition/unit"))>=3
assert kit.find("./groups/turrets") is None
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
# Astrid ownership watch runs on existing saves and every minute thereafter.
# Check true ownership galaxy-wide, INCLUDING docked/off-sector ships, and
# keep creation inside the zero-owned branch: no duplicate rewards.
astrid_root=ET.parse(mod/"md/vardath_astrid_builder_start.xml").getroot()
assert astrid_root.get("name")=="VardathAstridBuilderStart"
watch=astrid_root.find("./cues/cue[@name='MaintainPlayerAstrid_v103']")
assert watch is not None, "New cue name reactivates the watch on existing saves"
assert watch.get("instantiate")=="true" and watch.get("checkinterval")=="1min"
assert watch.find("./actions/reset_cue[@cue='this']") is not None
search=watch.find("./actions/find_ship_by_true_owner")
assert search is not None and search.get("faction")=="faction.player"
assert search.get("macro")=="macro.ship_gen_m_yacht_01_a_macro"
assert search.get("space")=="player.galaxy" and search.get("multiple")=="true"
assert search.get("recursive") is None, "find_ship_by_true_owner in X4 9.00 does not accept recursive"
missing=watch.find("./actions/do_if[@value='$PlayerAstrids.count == 0']")
assert missing is not None
assert len(watch.findall(".//create_ship"))==1, "Exactly one spawn per missing-Astrid check"
astrid=missing.find("./create_ship[@macro='macro.ship_gen_m_yacht_01_a_macro'][@sector='player.sector']")
assert astrid is not None and astrid.get("name")=="$Astrid"
assert astrid.find("./owner[@exact='faction.player']") is not None
assert astrid.find("./pilot/select[@faction='faction.yaki']") is not None
assert astrid.find("./people[@ref='player_yaki_veteran_freighter_crew']/fillpercent") is not None
assert astrid.find("./safepos[@object='player.ship'][@exact='3km']") is not None
assert watch.find("./actions/create_ship") is None, "Do not grant a ship unless player owns zero"
# No ownership-based creation happens from a startup-only cue.
assert astrid_root.find(".//cue[@name='AddAstridEscort']") is None

assert md.find(".//add_blueprints") is not None
assert "ware.turret_vardath_kopis_beam" in md.find(".//add_blueprints").get("wares")
print(f"PASS: {len(files)} source/ZIP file matches, XML, cargo/crew, 10-start spawn, persistent owned-Astrid replacement, vanilla-compatible weapon socket, S turret template, owner equipment wares and build supply static invariants")

# Optional Sector Explorer compatibility patch and startup syntax regression.
compat=ET.parse(mod/"aiscripts/sectorexplorer.xml").getroot()
assert compat.tag=="diff"
check=compat.find("./replace")
assert check is not None and "isblacklisted.{null}" in check.get("sel")
assert "blacklisttype.sectoractivity" in check.text
assert manifest.find("./dependency[@id='ws_2074838459'][@optional='true']") is not None
assert "Vardath Kopis startup cue reached" in (mod/"md/vardath_kopis_builder_start.xml").read_text()
assert "\\'Vardath Kopis startup" not in (mod/"md/vardath_kopis_builder_start.xml").read_text()
