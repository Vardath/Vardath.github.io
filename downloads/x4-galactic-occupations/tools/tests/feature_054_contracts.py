#!/usr/bin/env python3
"""0.5.4 source contracts: crystal-only fire, selective native hacks, EMP survey.
These prove source invariants and save defaults, not live X4 physics/menu behaviour.
"""
from pathlib import Path
from lxml import etree as E

BASE=Path(__file__).resolve().parents[2]/"vardath_galactic_occupations"
def xml(path):return E.parse(str(BASE/path)).getroot()
def one(root,xpath):
    found=root.xpath(xpath)
    assert len(found)==1,(xpath,len(found))
    return found[0]
def check(cond,message):
    assert cond,message
    print("PASS",message)

turret=xml("md/VGO_Turrets.xml")
selection=one(turret,".//cue[@name='Selection']")
controller=one(turret,".//cue[@name='Controller']")
check(bool(selection.xpath(".//set_value[@name='player.entity.$vgo_objects.{$turret}.$vgo_saved_native_mode'][@exact='$turret.mode']")),
      "existing native weapon modes are saved before enabling crystal mode")
check(bool(selection.xpath(".//set_weapon_mode[@weapon='$turret'][@weaponmode='weaponmode.holdfire']")),
      "native mining stops independently targeting asteroid bodies")
check(bool(selection.xpath(".//set_weapon_mode[@weapon='$turret'][contains(@weaponmode,'$vgo_saved_native_mode')]")),
      "switching back restores exact original native weapon mode")
check(bool(selection.xpath(".//remove_value[contains(@name,'$vgo_saved_native_mode')]")),
      "restored-mode cache is removed")
check(bool(controller.xpath(".//set_weapon_mode[@weaponmode='weaponmode.holdfire']")),
      "previously enabled saves also suppress native mining fire")
check(bool(controller.xpath(".//find_object_component[@class='class.crystal'][@object='$rock']")),
      "only actual crystals embedded in asteroids are collected as targets")
check(bool(controller.xpath(".//set_value[@name='$target'][@exact='$deposit']")),
      "scripted aim takes crystal component, not asteroid")
check(not controller.xpath(".//aim_turret[@target='$rock']|.//fire_turret[@target='$rock']"),
      "no scripted turret action targets whole asteroid")
check(bool(controller.xpath(".//find_object[@class='class.asteroid'][@sortlimit='96']")),
      "crystal-candidate search covers 96 nearest rocks")

horder=xml("aiscripts/order.vardath.go.hacker.xml")
param=one(horder,".//order/params/param[@name='hackobjective']")
check(param.get('default')=='0' and param.get('type')=='number'
      and bool(param.xpath("./input_param[@name='min'][@value='0']"))
      and bool(param.xpath("./input_param[@name='max'][@value='7']")),
      "hacker objective is a save-safe 0-to-7 native Behaviour parameter")
names=('hack_production','hack_all_turrets','hack_shieldgenerators','hack_storage',
       'hack_radar','hack_buildmodules','hack_watchdogs')
for i,name in enumerate(names,1):
    got=horder.xpath(f".//attention/actions/*[self::do_if or self::do_elseif][@value='$hackobjective == {i}']/set_value[@name='$requestedpanel']")
    check(len(got)==1 and got[0].get('exact')=="'"+name+"'",f"target selection {i} resolves {name}")
check(bool(horder.xpath(".//run_script[@name=\"'vardath.go.worker'\"]/param[@name='hackpanel'][@value='$requestedpanel']")),
      "autonomous hacker passes selected objective to the worker")
worker=xml("aiscripts/vardath.go.worker.xml")
check(bool(worker.xpath("./params/param[@name='hackpanel']"))
      and bool(worker.xpath(".//set_value[@name='player.entity.$vgo_objects.{this.ship}.$vgo_hack_forcedpanel'][@exact='$hackpanel']")),
      "existing worker forwards selected hack panel to native catalogue filter")
hack=xml("aiscripts/vardath.go.task.hacker.xml")
check(bool(hack.xpath(".//do_if[contains(@value,'$vgo_hack_forcedpanel == $entry.{2}')]")),
      "no random substitute is chosen when the requested panel is absent")
check(bool(hack.xpath(".//set_value[contains(@name,'$vgo_status')][contains(@exact,'Hacker objective')]")),
      "selected native hacking system appears in ship status")

scanner=xml("aiscripts/order.vardath.go.scanner.xml")
emp=one(scanner,".//order/params/param[@name='blueprintemp']")
check(emp.get('default')=='false' and emp.get('type')=='bool' and bool(emp.xpath("./patch[@sinceversion='11']")),
      "EMP auto-blueprints opt in, and older saved orders default off")
check(bool(scanner.xpath(".//run_script[@name=\"'vardath.go.worker'\"]/param[@name='empscan'][@value='$blueprintemp']"))
      and bool(worker.xpath(".//set_value[@name='player.entity.$vgo_objects.{this.ship}.$vgo_emp_enabled']")),
      "EMP option remains scoped to active scanning role")

survey=xml("md/VGO_Survey.xml")
q=one(survey,".//cue[@name='QueuePublication']/actions/do_if")
predicate=q.get('value')
for phrase in ("$sample.$finished ge $sample.$started + 10s",
               "$sample.$ship == $ship","$ship.order == @player.entity.$vgo_objects.{$ship}.$vgo_order",
               "$station.isoperational","$ship.distanceto.{$module}"):
    check(phrase in predicate,"verified sample gate: "+phrase)
check(bool(q.xpath("./set_known[@object='$module'][@known='true'][@updatesnapshot='true']"))
      and bool(q.xpath("./set_known[@object='$station'][@known='true'][@updatesnapshot='true']")),
      "each verified surveyed module identity is published to native map")
check(not q.xpath("./set_object_scanned")
      and bool(survey.xpath(".//library[@name='PublishPending']//set_object_scanned[@object='$module']")),
      "native high-detail scan stays bounded by deferred player scanner cap")
condition=one(q,"./do_if[contains(@value,'$vgo_emp_enabled')]")
for phrase in ("$module.isclass.module","not player.blueprints.{$module.macro.ware}.any.exists",
               "noplayerblueprint","inventory.{ware.bomb_player_limpet_emp_01_mk1}.count"):
    check(phrase in condition.get('value'),"EMP entitlement: "+phrase)
check(bool(condition.xpath(".//set_value[@name='$precursors'][contains(@exact,'research.requiredprecursors.list')]"))
      and bool(condition.xpath(".//do_for_each[@name='$precursor'][@in='$precursors']"))
      and bool(condition.xpath(".//do_if[@value='not $precursor.research.unlocked']")),
      "research prerequisites match native data leak blueprint restrictions")
check(len(condition.xpath(".//remove_inventory[@entity='player.entity'][@ware='ware.bomb_player_limpet_emp_01_mk1'][@exact='1']"))==1
      and len(condition.xpath(".//add_blueprints[@macros='$module.macro']"))==1,
      "exactly one real EMP consumed per eligible blueprint grant")
check(not survey.xpath(".//create_bomb|.//create_signalleak|.//teleport_player|.//set_owner"),
      "no physical EMP explosion, fake leak, player teleport, or ownership mutation")

for file in ("aiscripts/vardath.go.survey.publish.xml","aiscripts/vardath.go.task.scanner.xml"):
    root=xml(file)
    check(bool(root.xpath(".//set_known[@object='$module'][@updatesnapshot='true']")),
          "native module snapshot refreshed in "+file)

texts=[xml("t/0001.xml"),xml("t/0001-l044.xml")]
def labels(root):return {x.get('id'):x.text for x in root.xpath("./page[@id='191180']/t")}
a,b=(labels(root) for root in texts)
check(a==b and all(k in a for k in ("73","74","75","203","213")),
      "English fallback and L044 objective/EMP labels are identical")
print("PASS: 0.5.4 feature contracts — runtime X4 acceptance still required")
