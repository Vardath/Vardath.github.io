"""Reproduce empty service-slot selection; no X4 runtime is simulated here."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as E

BASE=Path(__file__).resolve().parents[2]
PATCH=BASE/'vardath_galactic_occupations/md/npc_instantiation.xml'
OLD='this.$ServiceSlots.count + this.$GenericSlots.count ge 2'

def eligible(expression,service,generic):
    expr=expression.replace('this.$ServiceSlots.count',str(service)).replace('this.$GenericSlots.count',str(generic))
    expr=re.sub(r'\bge\b','>=',expr);expr=re.sub(r'\bgt\b','>',expr)
    return eval(expr,{'__builtins__':{}},{})

class EmptyWorkforceSlot(unittest.TestCase):
    def setUp(self):self.ops=list(E.parse(PATCH).getroot());self.guard=self.ops[0].text
    def test_logged_empty_service_list_cannot_reach_index_one(self):
        # Native combined-slot gate accepts this; the non-casual branch indexes [] at one.
        self.assertTrue(eligible(OLD,0,2))
        with self.assertRaises(IndexError):[][1-1]
        self.assertFalse(eligible(self.guard,0,2))
    def test_any_number_of_generic_slots_cannot_supply_a_service_slot(self):
        for generic in range(250):self.assertFalse(eligible(self.guard,0,generic))
    def test_all_nonempty_service_slot_choices_keep_the_native_decision(self):
        for service in range(1,20):
            for generic in range(20):self.assertEqual(eligible(self.guard,service,generic),eligible(OLD,service,generic))
    def test_native_reserve_one_space_rule_is_retained(self):
        self.assertFalse(eligible(self.guard,1,0));self.assertTrue(eligible(self.guard,1,1))
    def test_patch_scopes_actual_included_library_before_actor_creation(self):
        # StartTrackingObject is the runtime caller, not the location of the included source.
        self.assertEqual(len(self.ops),1);self.assertEqual(self.ops[0].tag,'replace')
        self.assertEqual(self.ops[0].get('sel'),"/mdscript//library[@name='InstantiateNPCs']//do_if[@value='"+OLD+"']/@value")
        self.assertEqual(len(self.ops[0]),0)
        self.assertNotIn('create_cue_actor',PATCH.read_text())

if __name__=='__main__':unittest.main()
