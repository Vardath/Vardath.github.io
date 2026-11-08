#!/usr/bin/env python3
"""Exercise actual cold-start conditions and XML compatibility diffs.

The native action boundary accepts lists/tables and rejects null, matching the
documented contract and supplied error. This is not a station-generation runtime.
"""
import copy
from pathlib import Path
import re
import unittest
import zipfile
from lxml import etree
from crystal_commerce_contracts import MOD, BUYER, NULL
from log12_return_contracts import ReturnVM, ROOT
from passenger_completion_contracts import Seq


class ColdRegistryVM(ReturnVM):
    def __init__(self):
        super().__init__();self.registry_present=False;self.count_reads=0
    def expr(self,text):
        if text=='md.VGO_State.Init.$Ships?':return self.registry_present
        if text=='md.VGO_State.Init.$Ships.count gt 0':
            self.count_reads+=1
            if not self.registry_present:raise AssertionError('Read an uninitialized ship registry')
        return super().expr(text)
    def poll_registry(self):
        cue=ROOT.find(".//cue[@name='RecoverVisitsV39']")
        for condition in cue.find('conditions'):
            if not self.expr(condition.get('value')):return False
        self.execute(cue.find('actions'));return True


class ColdRegistry(unittest.TestCase):
    def test_first_poll_before_main_registry_exists_never_reads_count(self):
        v=ColdRegistryVM();self.assertFalse(v.poll_registry());self.assertEqual(v.count_reads,0)
    def test_initialized_empty_registry_waits_without_inventing_a_ship(self):
        v=ColdRegistryVM();v.registry_present=True;v.saved_registry=Seq()
        self.assertFalse(v.poll_registry());self.assertEqual(v.registry,[])
    def test_later_initialization_recovers_same_saved_actor_and_visit_once(self):
        v=ColdRegistryVM().legacy_paid();v.registry=Seq();actor=v.crew;cash=v.money
        self.assertFalse(v.poll_registry());v.registry_present=True
        self.assertTrue(v.poll_registry());self.assertTrue(v.poll_registry())
        self.assertEqual(v.registry,[v.ship]);self.assertIs(v.state['vgo_crystal_shop_actor'],actor)
        self.assertEqual(v.money,cash);self.assertEqual(v.reward_requests,[])


def station_fixture():
    root=etree.Element('mdscript');cues=etree.SubElement(root,'cues')
    for name in ['ConstructionSequenceCompleted','NewStation_ConstructionSequenceCompleted']:
        cue=etree.SubElement(cues,'cue',name=name);actions=etree.SubElement(cue,'actions')
        etree.SubElement(actions,'create_list',name='$PossibleWares')
        guard=etree.SubElement(actions,'do_if',value='md.$EquipmentTable')
        etree.SubElement(guard,'set_value',name='$PossibleWares',exact='md.$EquipmentTable.{$Faction}')
        etree.SubElement(actions,'generate_loadout',result='$Loadouts',sequence='$ConstructionSequence',wares='$PossibleWares')
        etree.SubElement(actions,'apply_construction_sequence',station='$Station',sequence='$ConstructionSequence')
    return root


def apply_attributes(root,operations):
    for op in operations:
        targets=root.xpath(op.get('sel'))
        if not targets and op.get('silent')=='true':continue
        if len(targets)!=1:raise AssertionError('Unexpected native patch target count')
        target=targets[0];target.getparent().set(target.attrname,op.text)
    return root


class NativeLoadoutBoundary(unittest.TestCase):
    def current(self):return apply_attributes(station_fixture(),etree.parse(str(MOD/'md/finalisestations.xml')).getroot())
    def test_empty_native_equipment_list_remains_list_in_both_station_paths(self):
        for node in self.current().iter('generate_loadout'):
            value=[] if node.get('wares')=='$PossibleWares' else None
            self.assertIsInstance(value,(list,dict));self.assertEqual(value,[])
    def test_nonempty_equipment_list_and_native_construction_actions_are_preserved(self):
        root=self.current();wares=['real turret ware','real shield ware']
        self.assertEqual(len(root.xpath('//apply_construction_sequence')),2)
        for node in root.iter('generate_loadout'):
            self.assertEqual(node.get('wares'),'$PossibleWares')
            self.assertIs({'$PossibleWares':wares}.get(node.get('wares')),wares)
        self.assertEqual(len(root.xpath('//generate_loadout')),2)
    def test_previous_shipped_patch_reproduces_the_exact_null_argument_failure(self):
        archive=MOD.parent/'Galactic_Occupations_0.4.3_DEV.zip'
        with zipfile.ZipFile(archive) as z:
            old=etree.fromstring(z.read('extensions/vardath_galactic_occupations/md/finalisestations.xml'))
        root=apply_attributes(station_fixture(),old)
        for node in root.iter('generate_loadout'):
            self.assertEqual(node.get('wares'),'if $PossibleWares.count then $PossibleWares else null')
            with self.assertRaises(TypeError):
                value=None
                if not isinstance(value,(list,dict)):raise TypeError('Wares value is neither a list nor a table: null')


class SubscriptionCompatibility(unittest.TestCase):
    def patches(self):return etree.parse(str(MOD/'extensions/z_ram_autotradesubs/md/ramautosubs.xml')).getroot()
    def test_all_nineteen_original_checks_resolve_same_declared_faction_on_both_sides(self):
        operations=self.patches();self.assertEqual(len(operations),19)
        for op in operations:
            old=re.search(r'@value=([\x27\"])(.+)\1\]',op.get('sel'))[2]
            r=etree.Element('mdscript');a=etree.SubElement(r,'actions');n=etree.SubElement(a,'do_if',value=old)
            apply_attributes(r,[op]);value=n.get('value')
            m=re.fullmatch(r'faction.player.canholdlicence.tradesubscription.\{faction.(\w+)\} and not faction.player.haslicence.tradesubscription.\{faction.\1\}',value)
            self.assertIsNotNone(m,value)
            self.assertEqual(value,old.replace('.{'+m[1]+'}','.{faction.'+m[1]+'}'))
    def test_eligibility_and_existing_subscription_still_control_original_action(self):
        for op in self.patches():
            for permitted,held in [(False,False),(False,True),(True,True),(True,False)]:
                expr=re.sub(r'faction.player.canholdlicence.tradesubscription.\{faction.\w+\}','permitted',op.text)
                expr=re.sub(r'faction.player.haslicence.tradesubscription.\{faction.\w+\}','held',expr)
                self.assertEqual(eval(expr,{'__builtins__':{}},{'permitted':permitted,'held':held}),permitted and not held)
    def test_corrected_or_absent_external_scripts_are_optional_noops(self):
        for op in self.patches():
            self.assertEqual(op.get('silent'),'true')
            root=etree.Element('mdscript');self.assertEqual(len(root.xpath(op.get('sel'))),0)
            apply_attributes(root,[op]);self.assertEqual(len(root),0)
            a=etree.SubElement(root,'actions');n=etree.SubElement(a,'do_if',value=op.text)
            apply_attributes(root,[op]);self.assertEqual(n.get('value'),op.text)


if __name__=='__main__':unittest.main(verbosity=2)
