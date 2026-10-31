#!/usr/bin/env python3
"""Static validation of the standalone Yaki Terran habitat extension.

Not a substitute for testing in Egosoft's X4 runtime/material renderer.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile
import struct

root = Path(__file__).resolve().parent
mod = root / "vardath_yaki_terran_habs"
archive = root / "vardath_yaki_terran_habs_v1.1.zip"
expected = {"content.xml", "README.md", "libraries/material_library.xml",
            "libraries/wares.xml", "libraries/races.xml",
            "libraries/modules.xml", "libraries/modulegroups.xml",
            "libraries/constructionplans.xml", "libraries/characters.xml",
            "md/vardath_yaki_faction_habitats.xml",
            "md/vardath_yaki_habitats.xml", "t/0001-l044.xml",
            "assets/textures/yaki_black.dds", "assets/textures/yaki_red.dds"}
for size in "sml":
    expected.add(f"assets/structures/habitat/vardath_yaki_hab_{size}.xml")
    expected.add(f"assets/structures/habitat/macros/vardath_yaki_hab_{size}_macro.xml")

assert archive.is_file(), "Missing v1.0 ZIP"
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None, "ZIP CRC failed"
    assert set(z.namelist()) == {"vardath_yaki_terran_habs/" + x for x in expected}
    for name in expected:
        disk = (mod/name).read_bytes()
        assert z.read("vardath_yaki_terran_habs/"+name) == disk, "Archive differs: "+name
        if name.endswith(".xml"):
            ET.fromstring(disk)

manifest = ET.parse(mod/"content.xml").getroot()
assert manifest.tag == "content"
assert manifest.get("version") == "110"
assert manifest.get("id") == "vardath_yaki_terran_habs"
assert manifest.find("./dependency[@id='ego_dlc_terran']") is not None
assert manifest.find("./dependency").get("version") == "900"

races = ET.parse(mod/"libraries/races.xml").getroot()
race = races.find(".//race[@id='yaki']")
assert race is not None and "workforce" in race.get("tags","")
wares = ET.parse(mod/"libraries/wares.xml").getroot()
assert wares.find(".//method[@id='vardath_yaki']/default[@race='yaki']") is not None
recipes = wares.findall(".//production[@method='vardath_yaki']")
assert len(recipes) == 2
assert all(set(x.get("ware") for x in p.findall("./primary/ware")) ==
           {"terranmre", "medicalsupplies"} for p in recipes)
group = ET.parse(mod/"libraries/modulegroups.xml").getroot()
assert len(group.findall(".//group[@name='hab_vardath_yaki']/select")) == 3

materials = ET.parse(mod/"libraries/material_library.xml").getroot()
custom = materials.find(".//collection[@name='vardathyaki']")
assert custom is not None
names = {m.get("name") for m in custom.findall("./material")}
assert names == {"black_hull","red_panels","red_fx"}
for material in custom.findall("./material"):
    assert any("vardath_yaki_terran_habs" in v.get("value","")
           for v in material.findall("./properties/property")
           if v.get("name") == "diffuse_map")

for size,capacity in [("s",100),("m",250),("l",500)]:
    component = ET.parse(mod/f"assets/structures/habitat/vardath_yaki_hab_{size}.xml").getroot()
    node = component.find(f"./component[@name='vardath_yaki_hab_{size}']")
    assert node is not None
    assert f"hab_ter_{size}_01_data" in node.find("./source").get("geometry")
    refs = [x.get("ref") for x in node.findall(".//material")]
    assert "vardathyaki.black_hull" in refs
    assert "vardathyaki.red_panels" in refs
    lights = node.findall(".//lights/omni") + node.findall(".//lights/box")
    assert len(lights) >= 10
    assert any(int(l.get("r",0)) > int(l.get("g",0))*3 for l in lights)
    macro = ET.parse(mod/f"assets/structures/habitat/macros/vardath_yaki_hab_{size}_macro.xml").getroot()
    entry = macro.find(f"./macro[@name='vardath_yaki_hab_{size}_macro']")
    assert entry is not None and entry.find("./component").get("ref") == f"vardath_yaki_hab_{size}"
    workforce=entry.find("./properties/workforce")
    assert workforce.get("race") == "yaki" and int(workforce.get("capacity")) == capacity
    ware = wares.find(f".//ware[@id='module_vardath_yaki_hab_{size}']")
    assert ware is not None
    assert ware.find("./component").get("ref") == f"vardath_yaki_hab_{size}_macro"
    assert ware.find("./production/primary/ware[@ware='computronicsubstrate']") is not None
    assert ware.find("./production/primary/ware[@ware='siliconcarbide']") is not None

md = ET.parse(mod/"md/vardath_yaki_habitats.xml").getroot()
assert md.tag == "mdscript"
blueprint = md.find(".//add_blueprints")
assert blueprint is not None
assert all("ware.module_vardath_yaki_hab_"+s in blueprint.get("wares") for s in "sml")

for name in ("yaki_red.dds","yaki_black.dds"):
    d=(mod/"assets/textures"/name).read_bytes()
    assert len(d) == 8320 and d[:4] == b"DDS "
    assert struct.unpack_from("<III", d, 4) == (124,0x81007,128)
    assert d[84:88] == b"DXT1"

# Target only the vanilla Yaki wharf. Avoid patching emergency story plans.
plans = ET.parse(mod/"libraries/constructionplans.xml").getroot()
repl = plans.findall("./replace")
assert len(repl) == 2
assert all("plan[@id='yak_wharf']" in x.get("sel", "") for x in repl)
assert {x.text for x in repl} == {"vardath_yaki_hab_m_macro", "vardath_yaki_hab_l_macro"}
assert all("story_yaki_emergency_station" not in x.get("sel", "") for x in repl)
assert not any(x.get("sel","").startswith("/factions") for x in plans)
npc = ET.parse(mod/"md/vardath_yaki_faction_habitats.xml").getroot()
assert npc.get("name") == "VardathYakiFactionHabitats"
cue = npc.find(".//cue[@name='RetrofitYakiWharfHabitats']")
assert cue is not None and cue.get("checkinterval") == "10min"
assert cue.find("./actions/reset_cue") is not None
find = cue.find(".//find_station")
assert find is not None and find.get("owner") == "faction.yaki"
checks = [x.get("value","") for x in cue.findall(".//do_if")]
assert any("$Station.iswharf" in x and "trueowner == faction.yaki" in x for x in checks)
assert any("$HasYakiHabitat" in x for x in checks)
assert cue.find(".//create_construction_sequence/immediate") is not None
assert cue.find(".//add_build_to_expand_station") is not None
assert any(x.get("name", "").startswith("md.$VardathYakiHabitatRetrofitted.")
           for x in cue.findall(".//set_value"))
assert not any(x.tag == "create_ship" for x in npc.iter()), "Do not spawn free construction ships"

# Match race='yaki' with real Yaki category clones, without mutating originals.
actors = ET.parse(mod/"libraries/characters.xml").getroot()
characters = actors.findall(".//character")
assert len(characters) >= 16
assert len({c.get("id") for c in characters}) == len(characters)
assert all(c.get("id","").startswith("vardath_") for c in characters)
assert all(c.find("./category").get("race") == "yaki"
           and "yaki" in c.find("./category").get("faction","")
           for c in characters)
assert any("service" in c.find("./category").get("tags","") for c in characters)
assert any("marine" in c.find("./category").get("tags","") for c in characters)

print(f"PASS: {len(expected)} files; ZIP CRC and exact source; well-formed XML; separate Terran geometry, dark/red materials; DXT1 textures; Yaki workforce, recipes, S/M/L blueprints")
