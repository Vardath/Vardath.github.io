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
archive = root / "vardath_yaki_terran_habs_TEST.zip"
expected = {"content.xml", "README.md", "libraries/material_library.xml",
            "libraries/wares.xml", "libraries/races.xml",
            "libraries/modules.xml", "libraries/modulegroups.xml",
            "index/macros.xml", "index/components.xml", "libraries/characters.xml",
            "md/vardath_yaki_faction_habitats.xml",
            "md/vardath_yaki_habitats.xml", "t/0001-l044.xml",
            "assets/textures/yaki_black.dds", "assets/textures/yaki_red.dds"}
for size in "sml":
    expected.add(f"assets/structures/habitat/vardath_yaki_hab_{size}.xml")
    expected.add(f"assets/structures/habitat/macros/vardath_yaki_hab_{size}_macro.xml")

assert archive.is_file(), "Missing current TEST ZIP"
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
assert int(manifest.get("version")) >= 121
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
    # The original Terran ring has precisely FOUR snap connectors.
    # Preserve not just the names, but the original S/M/L snap spacing,
    # orientations and absence of a cosmetic or invalid fifth connector.
    original_radius={"s":400,"m":600,"l":800}[size]
    expected_positions=((0,0,original_radius),(0,0,-original_radius),(-original_radius,0,0),(original_radius,0,0))
    snaps=[c for c in node.findall("./connections/connection")
           if "snap" in c.get("tags","").split()]
    assert len(snaps)==4, (size, len(snaps))
    for i,(snap,expected_position) in enumerate(zip(snaps,expected_positions),1):
        assert snap.get("name") == f"ConnectionSnap{i:03d}", (size,i,snap.get("name"))
        pos=snap.find("./offset/position")
        assert pos is not None
        assert tuple(float(pos.get(a,0)) for a in ("x","y","z")) == expected_position, (size,i)
        if i > 1:
            q=snap.find("./offset/quaternion")
            assert q is not None, (size,i)

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

# Three explicit, registered custom components and macros, with no fourth Yaki module.
component_index=ET.parse(mod/"index/components.xml").getroot()
macro_index=ET.parse(mod/"index/macros.xml").getroot()
ci=component_index.findall(".//entry")
mi=macro_index.findall(".//entry")
assert {x.get("name") for x in ci} == {f"vardath_yaki_hab_{size}" for size in "sml"}
assert {x.get("name") for x in mi} == {f"vardath_yaki_hab_{size}_macro" for size in "sml"}
for entry in ci+mi:
    assert entry.get("value","").startswith("extensions\\vardath_yaki_terran_habs\\assets\\structures\\habitat\\")
    assert "vardath_yaki_hab_" in entry.get("value","")
assert not (mod/"libraries/constructionplans.xml").exists(), "Do not corrupt the Argon wharf plan with hardcoded Terran habitat positions"
npc=ET.parse(mod/"md/vardath_yaki_faction_habitats.xml").getroot()
assert npc.get("name")=="VardathYakiFactionHabitats"
cue=npc.find(".//cue[@name='RetrofitYakiWharfRings_v2']")
assert cue is not None and cue.get("checkinterval")=="10min" and cue.get("instantiate")=="true"
assert cue.find("./actions/reset_cue[@cue='this']") is not None
finder=cue.find(".//find_station")
assert finder is not None and finder.get("owner")=="faction.yaki" and finder.get("space")=="player.galaxy"
guards=[x.get("value","") for x in cue.findall(".//do_if")]
assert any("$Station.iswharf" in x and "$Station.trueowner == faction.yaki" in x for x in guards)
assert any("$Station.buildstorage.builds.queued.count" in x and "$MissingRings.count gt 0" in x for x in guards)
for size in "sml":
    m=f"macro.vardath_yaki_hab_{size}_macro"
    assert any(x.get("exact")==m for x in cue.findall(".//append_to_list[@name='$MissingRings']"))
    assert any(x.get("value")==f"$Entry.macro == {m}" for x in cue.findall(".//do_if")+cue.findall(".//do_elseif"))
builder=cue.find(".//create_construction_sequence")
assert builder is not None and builder.get("base")=="$CurrentPlan" and builder.get("macros")=="$MissingRings"
assert builder.get("station")=="$Station" and builder.get("connectors")=="$TerranConnectors"
assert builder.find("./immediate[@result='$NewSequence']") is not None
adapters=cue.find(".//set_value[@name='$TerranConnectors']")
assert adapters is not None
for connector in ["struct_ter_base_02_macro","struct_ter_cross_01_macro","struct_ter_vertical_01_macro"]:
    assert connector in adapters.get("exact")
expand=cue.find(".//add_build_to_expand_station")
assert expand is not None and expand.get("constructionplan")=="$NewSequence"
assert expand.get("object")=="$Station.buildstorage" and expand.get("buildobject")=="$Station"
assert not any(x.tag=="create_ship" for x in npc.iter()), "Never spawn a free NPC builder"

# Match race='yaki' with real Yaki category clones, without mutating originals.
actors = ET.parse(mod/"libraries/characters.xml").getroot()
characters = actors.findall(".//character")
assert len(characters) >= 16
assert len({c.get("id") for c in characters}) == len(characters)
assert all(c.get("id","").startswith("vardath_") for c in characters)
assert all(c.find("./category").get("race") == "yaki"
           and "yaki" in c.find("./category").get("faction","")
           and "faction.player" in c.find("./category").get("faction","")
           for c in characters)
assert any("service" in c.find("./category").get("tags","") for c in characters)
assert any("marine" in c.find("./category").get("tags","") for c in characters)

print(f"PASS: {len(expected)} files; ZIP CRC and exact source; S/M/L Terran four-snap geometry, six asset index entries, red-black materials, Yaki workforce, three-only blueprints and adaptive Yaki wharf integration")

# Regression: worker/NPC definitions must be available at player stations.
assert all(c.find("./category").get("race")=="yaki" and
           c.find("./category").get("faction")=="[yaki, faction.player]" and
           c.find("./owner").get("exact")=="yaki" for c in characters)
