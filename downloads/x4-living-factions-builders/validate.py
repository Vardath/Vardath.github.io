#!/usr/bin/env python3
"""Check the X4 extension's archive, XML syntax and construction-request wiring.

Structural checks only: X4 game runtime/XSD/vanilla XPath matching are not available here.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
mod = root / "vardath_living_factions_builders"
archive = root / "vardath_living_factions_builders_v1.1.zip"
expected = {
    "content.xml",
    "aiscripts/order.build.find.task.xml",
    "aiscripts/build.buildstorage.xml",
    "md/factionlogic_economy.xml",
    "md/vardath_faction_build_requests.xml",
    "libraries/parameters.xml",
    "libraries/modules.xml",
    "LICENSE",
    "ATTRIBUTION.md",
    "README.md",
}
assert archive.is_file(), "Missing v1.1 ZIP"
with zipfile.ZipFile(archive) as zf:
    assert zf.testzip() is None, "ZIP CRC mismatch"
    members = set(zf.namelist())
    assert members == {"vardath_living_factions_builders/" + x for x in expected}, (members, expected)
    for rel in expected:
        disk = (mod / rel).read_bytes()
        embedded = zf.read("vardath_living_factions_builders/" + rel)
        assert embedded == disk, f"ZIP differs from source: {rel}"
        if rel.endswith(".xml"):
            node = ET.fromstring(disk)
            expected_root = "content" if rel == "content.xml" else (
                "mdscript" if rel == "md/vardath_faction_build_requests.xml" else "diff"
            )
            assert node.tag == expected_root, rel
            if node.tag == "diff":
                assert node.find("./replace") is not None or node.find("./add") is not None
manifest = ET.parse(mod / "content.xml").getroot()
assert manifest.get("id") == "vardath_living_factions_builders"
assert manifest.get("version") == "110"
assert manifest.find("./dependency").get("version") == "900"
broker = ET.parse(mod / "md/vardath_faction_build_requests.xml").getroot()
assert broker.get("name") == "Vardath_FactionBuildRequests"
cue = broker.find(".//cue[@name='DispatchFactionConstruction']")
assert cue is not None and cue.get("instantiate") == "true" and cue.get("checkinterval") == "5min"
ships = cue.find(".//find_ship")
assert ships is not None and ships.get("owner") == "faction.player"
assert ships.get("primarypurpose") == "purpose.build"
assert ships.get("class") == "class.ship_xl"
assert cue.find(".//find_station") is not None
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
assert any(n.get("amount") == "50000Cr" for n in ai.findall(".//transfer_money"))
print(f"PASS: {len(expected)} matching source files, ZIP CRC, well-formed XML, NPC request broker and receiver checks")
