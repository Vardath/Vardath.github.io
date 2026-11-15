#!/usr/bin/env python3
"""Standard-library synthetic CAT/DAT merger tests; NOT actual X4 runtime tests."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

spec = importlib.util.spec_from_file_location("merge_replace_bodies", Path(__file__).with_name("merge_replace_bodies.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def stage(path: Path, target: str, payload: bytes, assets=None):
    path.mkdir()
    root = ET.Element("content", id=mod.ID, name="Stage", version="100", save="0")
    ET.SubElement(root, "dependency", id="ego_dlc_terran", optional="true")
    ET.ElementTree(root).write(path / "content.xml", encoding="utf-8")
    mod.write_catalog(path, "subst_01", {target: payload})
    if assets:
        mod.write_catalog(path, "ext_01", assets)


class MergeTests(unittest.TestCase):
    def test_combines_two_body_targets(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            a, b, out = p/"terran", p/"pio", p/"output"
            stage(a, "extensions/ego_dlc_terran/asset_dress_white.xac", b"XAC "+b"a"*100)
            stage(b, "extensions/ego_dlc_terran/asset_dress_blue.xac", b"XAC "+b"b"*120)
            report = mod.merge([a,b],out)
            self.assertEqual(len(report["body_targets"]),2)
            self.assertEqual(set(mod.read_catalog(out,"subst_01")),set(report["body_targets"]))
            self.assertEqual(ET.parse(out/"content.xml").getroot().get("save"),"0")
            self.assertTrue((out/"MERGE_REPORT.json").is_file())

    def test_rejects_changed_game_files_or_invalid_xac(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            stage(p/"a", "libraries/characters.xml", b"<diff/>")
            stage(p/"b", "extensions/game/body.xac", b"XAC "+b"x"*24)
            with self.assertRaises(ValueError):mod.merge([p/"a",p/"b"],p/"out")

    def test_rejects_material_conflicts(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            stage(p/"a","a.xac",b"XAC "+b"a"*20,{"assets/characters/tex.gz":b"a"})
            stage(p/"b","b.xac",b"XAC "+b"b"*20,{"assets/characters/tex.gz":b"b"})
            with self.assertRaisesRegex(ValueError,"conflicting"):
                mod.merge([p/"a",p/"b"],p/"out")

    def test_detects_catalog_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);stage(p/"a","a.xac",b"XAC "+"abc".encode())
            (p/"a"/"subst_01.dat").write_bytes(b"corrupted")
            with self.assertRaises(ValueError):mod.read_catalog(p/"a","subst_01")


if __name__ == "__main__":
    unittest.main()
