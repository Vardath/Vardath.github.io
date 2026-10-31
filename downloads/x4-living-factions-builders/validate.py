#!/usr/bin/env python3
"""Verify X4 v1.3 ZIP/source and static payment-ledger invariants.

These are structural, NOT an X4 runtime or engine-XSD conformance test.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
mod = root / "vardath_living_factions_builders"
archive = root / "vardath_living_factions_builders_v1.3.zip"
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
assert archive.is_file(), "Missing v1.3 release ZIP"
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
assert manifest.get("version") == "130"
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
assert any("not $Station.isplayerowned" in x for x in conditions)

ai = ET.parse(mod / "aiscripts/order.build.find.task.xml").getroot()
selectors = [x.get("sel") for x in ai if x.get("sel")]
assert len(selectors) == len(set(selectors)), "Duplicate XPath selectors"
assert any("or this.ship.isplayerowned" in (x.text or "") for x in ai.findall("./replace"))
assert ai.findall(".//transfer_money") == [], "Payment must have exactly one MD authority"

billing = ET.parse(mod / "md/vardath_builder_contracts.xml").getroot()
assert billing.get("name") == "Vardath_BuilderContracts"
pay = billing.find(".//cue[@name='ContractBilling']")
assert pay is not None and pay.get("checkinterval") == "1min"
assert pay.find("./actions/reset_cue").get("cue") == "this"
assert any(s.get("name") == "md.$VardathBuilderContracts" and s.get("exact") == "table[]"
           for s in pay.findall(".//set_value"))
sets = {(s.get("name"), s.get("exact")) for s in pay.findall(".//set_value")}
assert ("$Contract.$Owed", "200000Cr") in sets
assert ("$Contract.$Earned", "$Contract.$Earned + ($Delta / 1h) * 100000Cr") in sets
assert ("$Contract.$Earned", "$Contract.$Earned + ($Delta / 1h) * 25000Cr") in sets
assert ("$Contract.$Elapsed", "0s") in sets
assert any(s.get("name") == "$Contract.$LastSample" and s.get("exact") == "player.age"
           for s in pay.findall(".//set_value"))
assert any(x.get("name") == "md.$VardathBuilderContracts.{$Builder}"
           for x in pay.findall(".//remove_value"))
assert any(x.get("value") == "$Contract.$Closing and $Contract.$Owed le 0Cr"
           for x in pay.findall(".//do_if"))
transfers = pay.findall(".//transfer_money")
assert len(transfers) == 2, "Single initial and recurring debt-settlement payment paths"
assert all(x.get("from") == "$Contract.$Faction" and
           x.get("to") == "faction.player" and
           x.get("result") == "$Paid" and x.get("amount") == "$Contract.$Owed"
           for x in transfers)
assert all(x.get("value") != "true" for x in pay.findall(".//check_value"))
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
print(f"PASS: {len(expected)} matching ZIP/source files; XML; recurring request broker; persisted fee/hourly/final settlement design")
