#!/usr/bin/env python3
"""Verify X4 v1.2 ZIP/source and static payment-ledger invariants.

These are structural, NOT an X4 runtime or engine-XSD conformance test.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
mod = root / "vardath_living_factions_builders"
archive = root / "vardath_living_factions_builders_v1.2.zip"
expected = {
    "content.xml",
    "aiscripts/order.build.find.task.xml",
    "aiscripts/build.buildstorage.xml",
    "md/factionlogic_economy.xml",
    "md/vardath_faction_build_requests.xml",
    "md/vardath_builder_contracts.xml",
    "libraries/parameters.xml",
    "libraries/modules.xml",
    "LICENSE",
    "ATTRIBUTION.md",
    "README.md",
}
assert archive.is_file(), "Missing v1.2 release ZIP"
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
            root_name = ("content" if rel == "content.xml" else
                         "mdscript" if rel.startswith("md/vardath_") else "diff")
            assert node.tag == root_name, rel
            if node.tag == "diff":
                assert node.find("./replace") is not None or node.find("./add") is not None

manifest = ET.parse(mod / "content.xml").getroot()
assert manifest.get("id") == "vardath_living_factions_builders"
assert manifest.get("version") == "120"
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
print(f"PASS: {len(expected)} matching ZIP/source files; XML; recurring request broker; persisted fee/hourly/final settlement design")
