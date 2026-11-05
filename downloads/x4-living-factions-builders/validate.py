#!/usr/bin/env python3
"""Verify current Kopis-adjacent Living Factions & Builders ZIP/source and static payment invariants.

These are structural, NOT an X4 runtime or engine-XSD conformance test.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
mod = root / "vardath_living_factions_builders"
archive = root / "vardath_living_factions_builders_TEST.zip"
expected = {
    "content.xml",
    "aiscripts/order.build.find.task.xml",
    "aiscripts/build.buildstorage.xml",
    "md/factionlogic_economy.xml",
    "md/vardath_faction_build_requests.xml",
    "md/vardath_builder_contracts.xml",
    "libraries/gamestarts.xml",
    "libraries/loadouts.xml",
    "libraries/character_macros.xml",
    "t/0001-l044.xml",
    "libraries/parameters.xml",
    "libraries/modules.xml",
    "LICENSE",
    "ATTRIBUTION.md",
    "README.md",
}
assert archive.is_file(), "Missing current TEST ZIP"
with zipfile.ZipFile(archive) as zf:
    assert zf.testzip() is None, "ZIP CRC mismatch"
    members = set(zf.namelist())
    assert members == {"vardath_living_factions_builders/" + x for x in expected}, (members, expected)
    for rel in expected:
        disk = (mod / rel).read_bytes()
        embedded = zf.read("vardath_living_factions_builders/" + rel)
        assert embedded == disk, f"ZIP differs from GitHub source: {rel}"
        if rel.endswith(".xml"):
            node = ET.fromstring(disk)
            root_name = ("language" if rel.startswith("t/") else
                         "content" if rel == "content.xml" else
                         "mdscript" if rel.startswith("md/vardath_") else "diff")
            assert node.tag == root_name, rel
            if node.tag == "diff":
                assert node.find("./replace") is not None or node.find("./add") is not None

manifest = ET.parse(mod / "content.xml").getroot()
assert manifest.get("id") == "vardath_living_factions_builders"
assert int(manifest.get("version")) >= 171
assert manifest.get("save") == "1"
assert manifest.find("./dependency").get("version") == "900"

broker = ET.parse(mod / "md/vardath_faction_build_requests.xml").getroot()
assert broker.get("name") == "Vardath_FactionBuildRequests"
cue = broker.find(".//cue[@name='DispatchFactionConstruction_v12']")
assert cue is not None and cue.get("instantiate") == "true"
assert cue.get("checkinterval") == "5min"
assert cue.find("./actions/reset_cue").get("cue") == "this", "Request broker must repeat"
ships = cue.find(".//find_ship")
assert ships is not None and ships.get("owner") == "faction.player"
assert ships.get("primarypurpose") == "purpose.build"
assert ships.get("class") == "class.ship_xl"
stations = cue.find(".//find_station")
assert stations is not None
assert any("$AvailableBuilders.count gt 0" in (n.get("value") or "")
           for n in cue.findall(".//do_if")), "Galaxy scan must be gated on available player builders"
signal = cue.find(".//signal_objects")
assert signal is not None
assert signal.get("param") == "'request construction vessel'"
assert signal.get("param2") == "$BuildModule"
assert signal.get("object") == "$Builder"
conditions = [n.get("value") or "" for n in cue.findall(".//do_if")]
assert any("iswaitingforconstructionvessel" in x and "constructionvessel" in x for x in conditions)
assert any("FindBuildTasks" in x and "not $Builder.nextorder" in x for x in conditions)
assert any("not $Station.isplayerowned" in x and
           "$Station.trueowner.hasrelation.dock.{faction.player}" in x
           for x in conditions), "Hostile NPC stations must be refused at dispatch"

ai = ET.parse(mod / "aiscripts/order.build.find.task.xml").getroot()
selectors = [x.get("sel") for x in ai if x.get("sel")]
assert len(selectors) == len(set(selectors)), "Duplicate XPath selectors"
assert ai.find("./replace").get("sel")=="//param[@name='playeronly']/@default"
assert ai.find("./replace").text.strip()=="false"
assert ai.find("./add").get("sel")=="//handler[@comment='Requested for build']/conditions/event_object_signalled"
assert ai.findall(".//transfer_money") == [], "Payment must have exactly one MD authority"
assert any("event.param2.container.trueowner.hasrelation.dock.{faction.player}" in (x.get("value") or "")
           for x in ai.findall(".//check_value")), "Native requests must reject hostile employers"

billing = ET.parse(mod / "md/vardath_builder_contracts.xml").getroot()
assert billing.get("name") == "Vardath_BuilderContracts"
pay = billing.find(".//cue[@name='ContractBilling']")
assert pay is not None and pay.get("checkinterval") == "1min"
assert pay.find("./actions/reset_cue").get("cue") == "this"
assert any(s.get("name") == "md.$VardathBuilderContracts" and s.get("exact") == "table[]"
           for s in pay.findall(".//set_value"))
sets = {(s.get("name"), s.get("exact")) for s in pay.findall(".//set_value")}
# SETA and delayed checks must settle every actual in-game minute.
assert ("$Delta", "player.age - $Contract.$LastSample") in sets
assert not any(s.get("name")=="$Delta" and "2min" in (s.get("exact") or "")
               for s in pay.findall(".//set_value")), "A two-minute clamp would underpay SETA-delayed checks"
assert any(n.get("value") == "$Delta gt 0s" for n in pay.findall(".//do_if")), "Reject nonpositive elapsed intervals"
# Arithmetic check: 3, 10 and 60 in-game minutes must not be clamped to two.
for game_minutes in (1, 3, 10, 60):
    for hourly_credits in (100000, 25000):
        actual_credits = (game_minutes / 60) * hourly_credits
        if game_minutes > 2:
            assert actual_credits > (2 / 60) * hourly_credits
assert ("$Contract.$Owed", "200000Cr") in sets
assert ("$Contract.$Earned", "$Contract.$Earned + ($Delta / 1h) * 100000Cr") in sets
assert ("$Contract.$Earned", "$Contract.$Earned + ($Delta / 1h) * 25000Cr") in sets
assert ("$Contract.$Elapsed", "0s") in sets
assert ("$Contract.$Owed", "$Contract.$Owed + $Contract.$Earned") in sets
assert not any(s.get("value") == "$Contract.$Elapsed ge 1h" for s in pay.findall(".//do_if")), "Wages must settle every minute, not after one full game hour"
assert any(s.get("name") == "$Contract.$LastSample" and s.get("exact") == "player.age"
           for s in pay.findall(".//set_value"))
assert any(x.get("name") == "md.$VardathBuilderContracts.{$Builder}"
           for x in pay.findall(".//remove_value"))
assert any(x.get("value") == "$Contract.$Closing and $Contract.$Owed le 0Cr"
           for x in pay.findall(".//do_if"))
assert not pay.findall(".//transfer_money"), "Do not gate payroll on faction treasury transfers"
rewards = pay.findall(".//reward_player")
assert len(rewards) == 2 and all(x.get("money") == "$Payout" for x in rewards), "Both hire and recurring pay must reach player credits via native reward_player"
assert len(pay.findall(".//set_value[@name='$Contract.$Owed'][@exact='0Cr']")) >= 2, "Debt must be cleared before each reward to prevent duplicate payments on reload"
assert len(pay.findall(".//debug_text")) >= 2, "Log both hire and wage transactions"
assert pay.find(".//find_ship[@class='class.ship_xl'][@owner='faction.player']") is not None
assert all(x.get("primarypurpose") is None for x in pay.findall(".//find_ship")), "Payroll must find any player XL assigned to construction, regardless of ship purpose classification"
assert not any("constructionvessel == $Builder" in (x.get("value") or "") for x in pay.findall(".//do_if")), "Do not require ship to be deployed before paying an assigned construction job"
assert any("$Builder.constructionmodule.exists" in (x.get("value") or "") for x in pay.findall(".//do_if")), "Registration requires an actual construction assignment"
assert any("$Builder.constructionmodule == $Contract.$BuildModule" in (x.get("value") or "") for x in pay.findall(".//do_if")), "Ongoing contract must remain assigned to its original build module"
assert all(x.get("checkoperational") is None for x in pay.findall(".//find_ship")), "Do not filter out deployed builders"

assert all(x.get("value") != "true" for x in pay.findall(".//check_value"))
# Reputation is awarded only once, on observed completed NPC construction.
# The saved persistent contract survives save/reload and carries two flags.
assert ("$Contract.$SawConstruction", "false") in sets
assert ("$Contract.$SawConstruction", "true") in sets
assert ("$Contract.$RepGranted", "false") in sets
assert ("$Contract.$RepGranted", "true") in sets
guards = [x.get("value","") for x in pay.findall(".//do_if")]
assert any("$Contract.$SawConstruction" in x and "not $Contract.$RepGranted" in x
           and "builds.queued.count" in x and "builds.inprogress.count == 0" in x
           and "$Contract.$Faction.hasrelation.dock.{faction.player}" in x
           for x in guards), "Reputation completion gate must exclude hostility and canceled queued builds"
rewards = pay.findall(".//add_faction_relation")
assert len(rewards) == 1, "Only one reputation authority"
reward = rewards[0]
assert reward.get("faction") == "faction.player"
assert reward.get("otherfaction") == "$Contract.$Faction"
assert reward.get("value") == "0.00064"
assert reward.get("reason") == "relationchangereason.missioncompleted"
assert any("$Station.trueowner.hasrelation.dock.{faction.player}" in v for v in guards)
assert any("$Contract.$Faction.hasrelation.dock.{faction.player}" in v for v in guards)
# The optional-free game mode now requires the Cradle of Humanity DLC.
assert manifest.find("./dependency[@id='ego_dlc_terran']") is not None
gs = ET.parse(mod / "libraries/gamestarts.xml").getroot()
start = gs.find(".//gamestart[@id='vardath_gamestart_terran_yaki_builder']")
assert start is not None and start.get("group") == "6"
player = start.find("./player")
assert player is not None and player.get("female") == "true"
assert player.get("macro") == "vardath_terran_female_white_dress_macro"
ship = player.find("./ship")
assert ship is not None and ship.get("macro") == "ship_ter_xl_builder_01_a_macro"
assert ship.find("./pilot").get("faction") == "yaki"
assert ship.find("./people").get("people") == "player_yaki_veteran_freighter_crew"
assert ship.find("./loadout").get("ref") == "vardath_kyushu_yaki_start"
macros = ET.parse(mod / "libraries/character_macros.xml").getroot()
char = macros.find(".//macro[@name='vardath_terran_female_white_dress_macro']")
assert char is not None and char.get("class") == "player"
assert char.find("./component").get("ref") == "character_player_terran_female_01"
assert any("char_ter_f_crew_uniform_01" in x.get("ref", "")
           for x in char.findall("./properties/models/model"))
lo = ET.parse(mod / "libraries/loadouts.xml").getroot()
fit = lo.find(".//loadout[@id='vardath_kyushu_yaki_start']")
assert fit is not None and fit.get("macro") == ship.get("macro")
assert any(x.get("macro") == "ship_gen_xs_buildingdrone_01_a_macro"
           and int(x.get("exact")) >= 30 for x in fit.findall("./ammunition/unit"))
english = ET.parse(mod / "t/0001-l044.xml").getroot()
assert english.get("id") == "44" and english.find("./page[@id='995503']") is not None
print(f"PASS: {len(expected)} matching ZIP/source files; XML; request broker; immediate 200k hire and uncapped SETA-safe full game-time payouts, persisted ledger, hostile guards and completion reputation")

assert ".trueowner.exists" not in (mod/"md/vardath_builder_contracts.xml").read_text()
assert ".trueowner.exists" not in (mod/"md/vardath_faction_build_requests.xml").read_text()
assert "$Contract.$Faction.exists" not in (mod/"md/vardath_builder_contracts.xml").read_text()
