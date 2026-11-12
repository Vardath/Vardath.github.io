#!/usr/bin/env python3
"""Static X4 localization contracts, not a live multi-language client test."""
from pathlib import Path
import unittest
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "vardath_galactic_occupations"

class LocalizationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.neutral=ET.parse(MOD/"t/0001.xml").getroot()
        cls.english=ET.parse(MOD/"t/0001-l044.xml").getroot()

    def entries(self, root):
        self.assertEqual(root.tag,"language")
        pages=root.findall("page")
        self.assertEqual(len(pages),1)
        self.assertEqual(pages[0].get("id"),"191180")
        texts=pages[0].findall("t")
        self.assertEqual(len(texts),len({t.get("id") for t in texts}))
        return {t.get("id"):t.text for t in texts}

    def test_default_is_language_neutral(self):
        self.assertNotIn("id", self.neutral.attrib)
        self.assertEqual(self.english.get("id"),"44")

    def test_english_fallback_matches_native_english(self):
        self.assertEqual(self.entries(self.neutral),self.entries(self.english))

    def test_thirteen_job_names_descriptions_and_hack_command(self):
        t=self.entries(self.neutral)
        for i in range(101,114):
            self.assertTrue(t.get(str(i)),i)
            self.assertTrue(t.get(str(i+100)),i+100)
        for i in ["114","214","30","31","32","51","52"]:
            self.assertTrue(t.get(i),i)

    def test_missing_readtext_id_107_is_now_available_in_fallback(self):
        t=self.entries(self.neutral)
        self.assertEqual(t["107"],"Hostile Lure and Interception")
        self.assertIn("ten distinct galaxy sights",t["205"])
        self.assertNotIn("twenty distinct",t["205"])

    def test_literal_page_references_have_fallback_entries(self):
        entries=self.entries(self.neutral)
        refs=set()
        for file in MOD.rglob("*"):
            if file.is_file() and file.suffix in (".xml",".lua") and file.parent.name!="t":
                refs.update(re.findall(r"\\{191180,\\s*(\\d+)\\}",file.read_text()))
        for idx in refs:
            self.assertIn(idx,entries,"missing fallback for text id "+idx)

    def test_nexus_description_documents_all_thirteen_roles(self):
        description=(ROOT/"NEXUS_DESCRIPTION.md").read_text()
        for idx, job in enumerate(range(101,114),1):
            self.assertIn(self.entries(self.neutral)[str(job)],description)
        self.assertIn("ten sightseeing stops",description)

if __name__=="__main__":
    unittest.main(verbosity=2)
