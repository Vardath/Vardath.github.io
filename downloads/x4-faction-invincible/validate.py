#!/usr/bin/env python3
"""Static XML and ZIP checks. Not an X4 runtime verification."""
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile
root = Path(__file__).resolve().parent
mod = root / "vardath_faction_invincible"
expected = {"content.xml", "README.md", "md/vardath_faction_invincible.xml"}
assert all((mod / path).is_file() for path in expected)
manifest = ET.parse(mod / "content.xml").getroot()
assert manifest.tag == "content"
assert manifest.get("id") == "vardath_faction_invincible"
assert manifest.get("save") == "1"
assert int(manifest.get("version")) >= 101

assert manifest.find("./dependency").get("version") == "900"
md = ET.parse(mod / "md/vardath_faction_invincible.xml").getroot()
assert all(node.get("recursive") is None for node in md.findall(".//find_ship_by_true_owner")), "Unsupported X4 9.00 find_ship_by_true_owner recursive attribute"
assert md.find(".//cue[@name='SweepPlayerProperty'][@checkinterval='1min']") is not None
assert md.find(".//library[@name='SetAssetProtection'][@purpose='run_actions']") is not None
for action in ("find_ship_by_true_owner", "find_station_by_true_owner", "find_object",
               "set_object_hull", "set_object_shield",
               "set_object_min_hull", "set_object_min_shield"):
    assert md.find(".//" + action) is not None, action
for cls in ("class.module", "class.engine", "class.shieldgenerator",
            "class.turret", "class.weapon"):
    assert md.find(".//find_object_component[@class='" + cls + "'][@recursive='true']") is not None
assert md.find(".//set_object_min_hull[@exact='100']") is not None
assert md.find(".//set_object_min_hull[@exact='0']") is not None
assert md.find(".//set_object_min_shield[@exact='100']") is not None
assert md.find(".//set_object_min_shield[@exact='0']") is not None
archive = root / "vardath_faction_invincible_TEST.zip"
if archive.exists():
    with ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {"vardath_faction_invincible/" + f for f in expected}
        assert all(z.read("vardath_faction_invincible/" + f) == (mod / f).read_bytes()
                   for f in expected)
print("X4 player-faction protection static validation passed")
