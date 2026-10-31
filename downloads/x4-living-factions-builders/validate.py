#!/usr/bin/env python3
"""Structural validation of the X4 source extension and its GitHub ZIP."""
from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
mod = root / "vardath_living_factions_builders"
archive = root / "vardath_living_factions_builders_v1.0.zip"
expected = {
    "content.xml",
    "aiscripts/order.build.find.task.xml",
    "aiscripts/build.buildstorage.xml",
    "md/factionlogic_economy.xml",
    "libraries/parameters.xml",
    "libraries/modules.xml",
    "LICENSE",
    "ATTRIBUTION.md",
    "README.md",
}
assert archive.is_file(), "Missing distribution ZIP"
with zipfile.ZipFile(archive) as zf:
    assert zf.testzip() is None, "ZIP CRC mismatch"
    members = set(zf.namelist())
    assert members == {"vardath_living_factions_builders/" + x for x in expected}, (members, expected)
    for rel in expected:
        disk = (mod / rel).read_bytes()
        embedded = zf.read("vardath_living_factions_builders/" + rel)
        assert embedded == disk, f"ZIP file differs from GitHub source: {rel}"
        if rel.endswith(".xml"):
            rootnode = ET.fromstring(disk)
            assert rootnode.tag == ("content" if rel == "content.xml" else "diff"), rel
            if rootnode.tag == "diff":
                assert rootnode.find("./replace") is not None or rootnode.find("./add") is not None
    manifest = ET.parse(mod / "content.xml").getroot()
    assert manifest.get("id") == "vardath_living_factions_builders"
    assert manifest.find("./dependency").get("version") == "900"
    dispatch = ET.parse(mod / "aiscripts/order.build.find.task.xml").getroot()
    selectors = [x.attrib.get("sel") for x in dispatch if x.attrib.get("sel")]
    assert len(selectors) == len(set(selectors)), "Duplicate selectors may result in invalid patches"
print(f"PASS: {len(expected)} exact files; ZIP CRC, source match, XML parse, manifest checks")
