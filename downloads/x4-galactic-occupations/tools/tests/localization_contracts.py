#!/usr/bin/env python3
"""Validate complete X4 text tables for all published language IDs.

These are structural and terminology-smoke tests, not native-speaker reviews
or an X4 runtime test. Only the English fallback and static translated text
are changed; no jobs, orders, payments or saved actors are affected.
"""
from pathlib import Path
import unittest
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "vardath_galactic_occupations"
TEXT = MOD / "t"
# The game has 14 Steam interface language selections; the two Spanish
# variants share the native L034 text ID.
LANGUAGES = {
    "007": "Russian", "033": "French", "034": "Spanish",
    "039": "Italian", "042": "Czech", "044": "English",
    "048": "Polish", "049": "German", "055": "Brazilian Portuguese",
    "081": "Japanese", "082": "Korean",
    "086": "Simplified Chinese", "088": "Traditional Chinese",
}

class LocalizationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.neutral=ET.parse(TEXT/"0001.xml").getroot()
        cls.english=ET.parse(TEXT/"0001-l044.xml").getroot()

    def entries(self, root):
        self.assertEqual(root.tag,"language")
        pages=root.findall("page")
        self.assertEqual(len(pages),1)
        self.assertEqual(pages[0].get("id"),"191180")
        self.assertEqual(pages[0].get("voice"),"no")
        self.assertTrue(pages[0].get("title"))
        self.assertTrue(pages[0].get("descr"))
        texts=pages[0].findall("t")
        self.assertEqual(len(texts),len({t.get("id") for t in texts}))
        return {t.get("id"):t.text for t in texts}

    def test_default_is_language_neutral(self):
        self.assertNotIn("id", self.neutral.attrib)
        self.assertEqual(self.english.get("id"),"44")

    def test_english_fallback_matches_native_english(self):
        self.assertEqual(self.entries(self.neutral),self.entries(self.english))

    def test_complete_official_language_set_and_lowercase_filenames(self):
        found={p.name for p in TEXT.glob("0001-l*.xml")}
        expected={f"0001-l{code}.xml" for code in LANGUAGES}
        self.assertEqual(found,expected)
        self.assertTrue(all(p.name==p.name.lower() for p in TEXT.glob("0001-l*.xml")))

    def test_every_locale_preserves_exact_text_id_set(self):
        original=self.entries(self.english)
        self.assertEqual(len(original),60)
        for code,language in LANGUAGES.items():
            with self.subTest(language=language):
                root=ET.parse(TEXT/f"0001-l{code}.xml").getroot()
                self.assertEqual(root.get("id"),str(int(code)))
                actual=self.entries(root)
                self.assertEqual(set(actual),set(original))
                self.assertTrue(all(isinstance(v,str) and v.strip() for v in actual.values()))
                if code!="044":
                    for idx in ("101","102","202","203","205","213","214","75"):
                        self.assertNotEqual(actual[idx],original[idx],(language,idx))
                    self.assertNotEqual(root.find("page").get("title"),"Galactic Occupations")
                for idx in ("202","203","205","206","211","213","214","74","75"):
                    self.assertFalse(re.search(r"\{\d+,\s*\d+\}",actual[idx]),
                        (language,idx,"unresolved nested X4 text reference"))
                # Preserve the numbered hack objectives, not just their labels.
                for n in range(8):
                    self.assertRegex(actual["75"],rf"(?<!\d){n}(?!\d)")

    def test_russian_is_genuinely_cyrillic_and_has_no_untranslated_long_tooltips(self):
        ru=self.entries(ET.parse(TEXT/"0001-l007.xml").getroot())
        for idx in ("1","2","101","113","202","203","205","206","213","214"):
            self.assertRegex(ru[idx],r"[А-Яа-яЁё]{3,}",idx)
        self.assertIn("8 000",ru["202"])
        self.assertIn("500 000",ru["205"])
        self.assertIn("25%",ru["211"])

    def test_thirteen_job_names_descriptions_and_hack_command(self):
        t=self.entries(self.neutral)
        for i in range(101,114):
            self.assertTrue(t.get(str(i)),i)
            self.assertTrue(t.get(str(i+100)),i+100)
        for i in ["114","214","30","31","32","51","52"]:
            self.assertTrue(t.get(i),i)

    def test_missing_readtext_id_107_is_available_in_fallback(self):
        t=self.entries(self.neutral)
        self.assertEqual(t["107"],"Hostile Lure and Interception")
        self.assertIn("ten distinct galaxy sights",t["205"])
        self.assertNotIn("twenty distinct",t["205"])

    def test_literal_page_references_have_fallback_entries(self):
        entries=self.entries(self.neutral)
        refs=set()
        for file in MOD.rglob("*"):
            if file.is_file() and file.suffix in (".xml",".lua") and file.parent.name!="t":
                refs.update(re.findall(r"\{191180,\s*(\d+)\}",file.read_text()))
        for idx in refs:
            self.assertIn(idx,entries,"missing fallback for text id "+idx)

    def test_nexus_description_documents_all_thirteen_roles(self):
        description=(ROOT/"NEXUS_DESCRIPTION.md").read_text()
        for idx in range(101,114):
            self.assertIn(self.entries(self.neutral)[str(idx)],description)
        self.assertIn("ten sightseeing stops",description)

if __name__=="__main__":
    unittest.main(verbosity=2)
