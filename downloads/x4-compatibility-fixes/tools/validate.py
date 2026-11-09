#!/usr/bin/env python3
"""Verify pinned upstreams, apply real X4 diffs, then test failure boundaries.

This is source/static/mocked validation, never an X4 runtime test. Upstream
reference files are downloaded to a temporary cache and are not redistributed.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
import tempfile
import unittest
import urllib.request
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

BASE = Path(__file__).resolve().parents[1]
MOD = BASE / 'vardath_compatibility_fixes'
SOURCES = json.loads((BASE / 'tools/sources.json').read_text())
CHECKS = []
def normalized(data):
    return data.removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n')

def references(cache):
    result = {}
    for item in SOURCES:
        p = cache / item['path']
        if not p.exists():
            request = urllib.request.Request(item['url'], headers={'User-Agent': 'Vardath-X4-compatibility-validation/1.0'})
            data = urllib.request.urlopen(request, timeout=40).read()
            if item.get('catalog_path'):
                pattern = re.escape(item['catalog_path'].encode()) + rb' (\d+) (\d+) ([0-9a-f]{32})\n'
                m = re.search(pattern, data)
                if not m: raise ValueError('Workshop catalog entry not found')
                data = data[m.end():m.end()+int(m[1])]
                if hashlib.md5(data).hexdigest() != item['catalog_md5'] or m[3].decode() != item['catalog_md5']:
                    raise ValueError('Workshop catalog checksum mismatch')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(normalized(data))
        data = normalized(p.read_bytes())
        if hashlib.sha256(data).hexdigest() != item['sha256_lf']:
            raise ValueError('Pinned reference mismatch: ' + item['path'])
        result[item['path']] = E.fromstring(data)
    return result

def apply_patch(root, patch, counts=None):
    root = copy.deepcopy(root)
    for op in patch:
        if not isinstance(op.tag, str): continue
        matches = root.xpath(op.get('sel'))
        if not matches and op.get('silent') == 'true': continue
        if len(matches) != 1: raise ValueError(f'{op.get("sel")}: expected one match, got {len(matches)}')
        if counts is not None: counts.append(op.get('sel'))
        selected = matches[0]
        if isinstance(selected, E._ElementUnicodeResult):
            if not selected.is_attribute: raise ValueError('Only attribute selections supported here')
            parent, attr = selected.getparent(), selected.attrname
            if op.tag == 'replace': parent.set(attr, op.text or '')
            elif op.tag == 'remove': del parent.attrib[attr]
            else: raise ValueError('Unsupported attribute operation')
        elif op.tag == 'replace':
            parent, index = selected.getparent(), selected.getparent().index(selected)
            parent.remove(selected)
            for child in op: parent.insert(index, copy.deepcopy(child)); index += 1
        elif op.tag == 'remove': selected.getparent().remove(selected)
        elif op.tag == 'add':
            if op.get('pos') in ('before', 'after'):
                parent, index = selected.getparent(), selected.getparent().index(selected)
                if op.get('pos') == 'after': index += 1
            else: parent, index = selected, len(selected)
            for child in op: parent.insert(index, copy.deepcopy(child)); index += 1
        else: raise ValueError('Unsupported diff action')
    return root

def canonical(e):
    # Ignore formatting introduced by XML diffs, retain actual structure/text.
    e = copy.deepcopy(e)
    for n in e.iter():
        if n.text is not None and not n.text.strip(): n.text = None
        if n.tail is not None and not n.tail.strip(): n.tail = None
    return E.tostring(e, method='c14n')

def expr(source, values):
    """Small scalar evaluator for the actual installed guard strings in tests.

    Refuses unresolved X4 fields instead of silently treating them as true.
    It is deliberately not an X4 engine/emulator.
    """
    bindings = {}
    # Optional field lookup defaults only for the one optional diagnostic timer.
    values = dict(values)
    values.setdefault('@this.$vcf_gate_notice', None)
    for index, key in enumerate(sorted(values, key=len, reverse=True)):
        token = f'v{index}'
        source = source.replace(key, token)
        bindings[token] = values[key]
    source = re.sub(r'\b(\d+)min\b', lambda m: str(int(m[1])*60), source)
    for old, new in [(' gt ', ' > '), (' lt ', ' < '), (' le ', ' <= '), (' ge ', ' >= ')]: source = source.replace(old, new)
    source = re.sub(r'\btrue\b', 'True', source)
    source = re.sub(r'\bfalse\b', 'False', source)
    source = re.sub(r'\bnull\b', 'None', source)
    tree = ast.parse(source, mode='eval')
    allowed = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.Compare, ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Name, ast.Load, ast.Constant, ast.BinOp, ast.Add)
    if any(not isinstance(n, allowed) for n in ast.walk(tree)): raise ValueError('Unresolved or unsupported X4 expression: ' + source)
    return eval(compile(tree, '<source guard>', 'eval'), {'__builtins__': {}}, bindings)

class Contracts(unittest.TestCase):
    original = patched = None
    def one(self, path, selector, patched=True):
        values = (self.patched if patched else self.original)[path].xpath(selector)
        self.assertEqual(len(values), 1, selector)
        return values[0]

    def test_trade_mismatch_retries_before_amount_or_order_changes(self):
        p = 'aiscripts/order.trade.routine.xml'
        guards = self.patched[p].xpath("./attention/actions/do_if[@value='$buyoffer.exists and $selloffer.exists and $buyoffer.ware != $selloffer.ware']")
        self.assertEqual(len(guards), 2)  # normal return and saved resume label
        for guard in guards:
            for buy, sell, bw, sw, retry in [(True,True,'mre','medical',True),(True,True,'ore','ore',False),(True,False,'ore',None,False),(False,True,None,'ore',False),(False,False,None,None,False)]:
                with self.subTest(buy=buy,sell=sell,bw=bw,sw=sw):
                    v={'$buyoffer.exists':buy,'$selloffer.exists':sell,'$buyoffer.ware':bw,'$selloffer.ware':sw}
                    self.assertEqual(bool(expr(guard.get('value'),v)), retry)
            self.assertEqual([(n.tag,n.get('name'),n.get('exact')) for n in guard if n.tag=='set_value'], [('set_value','$buyoffer','null'),('set_value','$selloffer','null')])
            self.assertEqual(guard[-1].tag, 'resume');self.assertEqual(guard[-1].get('label'),'find trade run')
            self.assertFalse(guard.xpath('.//create_order|.//remove_order|.//add_money|.//remove_cargo|.//add_cargo|.//wait'))
        actions=self.one(p,'./attention/actions')
        start=list(actions).index(self.one(p,"./attention/actions/label[@name='find trade run']"))
        end=list(actions).index(self.one(p,"./attention/actions/label[@name='perform trade run']"))
        self.assertTrue(any(n.tag=='run_script' and n.get('name')=="'move.idle'" for n in list(actions)[start:end]))
        # Exact original routine, including reservations and orders, otherwise.
        q=copy.deepcopy(self.patched[p])
        for n in q.xpath("./attention/actions/do_if[@value='$buyoffer.exists and $selloffer.exists and $buyoffer.ware != $selloffer.ware']"): n.getparent().remove(n)
        self.assertEqual(canonical(q), canonical(self.original[p]))

    def test_cleanup_only_live_thread_and_waiting_listener(self):
        p='md/mc_management.xml';base=".//cue[@name='Thread_Manager_Submission_Ended']/actions"
        gate=self.one(p,base+"//do_if[@value='$FailedMissions == 0 and $ThreadCue.hasmission']")
        for failed,hasmission,allowed in [(0,True,True),(0,False,False),(1,True,False),(1,False,False)]:
            self.assertEqual(bool(expr(gate.get('value'),{'$FailedMissions':failed,'$ThreadCue.hasmission':hasmission})),allowed)
        signals=self.patched[p].xpath(base+"//signal_cue[@cue='Thread_Manager_Cleanup']")
        self.assertEqual(len(signals),2)
        for sig in signals:
            self.assertEqual(sig.get('check'),'false') # narrow same-frame duplicate race
            for state in ('waiting','active','complete','cancelled','disabled'):
                self.assertEqual(bool(expr(sig.getparent().get('value'),{'Thread_Manager_Cleanup.state':state,'cuestate.waiting':'waiting'})),state=='waiting')
        # Reward-bearing cleanup and other callback bookkeeping are untouched.
        self.assertEqual(canonical(self.one(p,".//cue[@name='Thread_Manager_Cleanup']")),canonical(self.one(p,".//cue[@name='Thread_Manager_Cleanup']",False)))
        self.assertEqual(len(self.patched[p].xpath(base+"//set_value[@name='$FailedMissions'][@operation='add']")),1)
        self.assertFalse(self.patched[p].xpath(base+'//reset_cue|'+base+'//reward_player'))

    def test_gate_snapshot_excludes_stale_and_preserves_saved_invasion(self):
        p='md/factiongoal_hold_space.xml';base=".//cue[@name='EvaluateState']"
        guard=self.one(p,base+"//do_for_each[@name='this.$vcf_entry']/do_if")
        cases=[(True,True,'target',True),(True,True,'wrong',False),(True,False,None,False),(False,False,None,False)]
        for exists,exit_exists,sector,accepted in cases:
            values={'this.$vcf_entry.exists':exists,'this.$vcf_entry.exit.exists':exit_exists,'this.$vcf_entry.exit.sector':sector,'$Target':'target'}
            self.assertEqual(bool(expr(guard.get('value'),values)),accepted)
        self.assertEqual(guard[0].get('name'),'this.$vcf_entrypoints')
        self.assertEqual(guard[0].get('exact'),'this.$vcf_entry')
        loop=self.one(p,base+"//do_all[@exact='this.$vcf_entrypoints.count']")
        self.assertFalse(any('$Invasions.{$i}.$AlliedEntryPoints.{$k}' in v for n in loop.iter() for v in n.attrib.values()))
        self.assertEqual(len(loop.xpath('./assert')),1) # original invariant retained
        self.assertEqual(len(loop.xpath(".//append_to_list[@name='this.$PotentialDefendAreaDefinitions']")),1)
        # Restore the original operands/remove only inserted preamble. Everything
        # else must be structurally identical, including station defence fallback.
        q=copy.deepcopy(self.patched[p]);l=q.xpath(base+"//do_all[@exact='this.$vcf_entrypoints.count']")[0]
        for n in l.iter():
            for k,v in list(n.attrib.items()): n.set(k,v.replace('this.$vcf_entrypoints.{$k}','$Invasions.{$i}.$AlliedEntryPoints.{$k}'))
        l.set('exact','$Invasions.{$i}.$AlliedEntryPoints.count')
        parent=l.getparent();index=parent.index(l)
        self.assertEqual([n.tag for n in list(parent)[index-4:index]],['set_value','do_for_each','remove_value','do_if'])
        for n in list(parent)[index-4:index]:parent.remove(n)
        self.assertEqual(canonical(q),canonical(self.original[p]))

    def test_gate_diagnostic_is_bounded(self):
        p='md/factiongoal_hold_space.xml'
        guard=self.one(p,".//do_if[@value='this.$vcf_entrypoints.count != $Invasions.{$i}.$AlliedEntryPoints.count and (not @this.$vcf_gate_notice or this.$vcf_gate_notice le player.age)']")
        for usable,total,last,now,expected in [(1,1,None,0,False),(0,1,None,0,True),(0,1,600,599,False),(0,1,600,600,True)]:
            self.assertEqual(bool(expr(guard.get('value'),{'this.$vcf_entrypoints.count':usable,'$Invasions.{$i}.$AlliedEntryPoints.count':total,'@this.$vcf_gate_notice':last,'this.$vcf_gate_notice':last,'player.age':now})),expected)
        self.assertEqual(expr(guard[-1].get('exact'),{'player.age':30}),630)

    def test_academy_captainless_ship_is_ineligible(self):
        p='extensions/galaxy_trader/md/gt_context_academy.xml';s=".//library[@name='GT_Academy_BuildShipEntryIfEligible']/actions/do_if"
        g=self.one(p,s)
        for ship,pilot,owned,expected in [(True,True,True,True),(True,False,True,False),(False,False,True,False),(True,True,False,False)]:
            self.assertEqual(bool(expr(g.get('value'),{'$ship?':True,'$ship.exists':ship,'$ship.isclass.ship':ship,'$ship.isplayerowned':owned,'$ship.pilot.isclass.npc':pilot})),expected)
        q=copy.deepcopy(self.patched[p]);q.xpath(s)[0].set('value',self.one(p,s,False).get('value'))
        self.assertEqual(canonical(q),canonical(self.original[p]))

    def test_research_listener_waits_for_real_current_hq_manager(self):
        p='extensions/researchblueprintsmod/md/researchblueprintsmod.xml';s=".//cue[@name='RBM_Start']/conditions"
        conditions=self.one(p,s)
        self.assertFalse(conditions.xpath('./check_any/*/@actor'))
        guards=conditions.xpath('./check_value');self.assertEqual(len(guards),2)
        self.assertEqual(guards[-1].get('value'),'@player.entity.$x4ep1_hq_research_unlocked')
        for manager,actor,eligible in [(None,'bob',False),('boso','boso',True),('boso','other',False),('new','old',False),('new','new',True)]:
            self.assertEqual(bool(expr(guards[0].get('value'),{'@player.headquarters.assignedcontrolentity.{controlpost.manager}.isclass.npc':manager is not None,'@player.headquarters.assignedcontrolentity.{controlpost.manager}':manager,'event.object':actor})),eligible)
        # No research initialization/reset or UI code changed.
        q=copy.deepcopy(self.patched[p]);c=q.xpath(s)[0];c.remove(c.xpath('./check_value')[0])
        for e in c.xpath('./check_any/*'): e.set('actor','@player.headquarters.controlentity.{controlpost.manager}')
        self.assertEqual(canonical(q),canonical(self.original[p]))

    def test_flyby_uses_specific_ammo_capacity_without_destroying_drop(self):
        p='extensions/fbl/md/fbl.xml';s=".//do_if[@value='$drop.isclass.collectableammo']/do_if"
        g=self.one(p,s)
        for drop,ship,missile,ware,capacity,wanted in [(True,True,True,'missile',1,True),(True,True,True,'missile',0,False),(True,True,True,None,10,False),(True,True,False,'drone',10,False),(False,True,True,'missile',10,False),(True,False,True,'missile',10,False)]:
            values={'$drop.exists':drop,'player.ship.exists':ship,'$drop.ammo.macro.isclass.missile':missile,'$drop.ammo.macro.ware':ware,'player.ship.ammostorage.{$drop.ammo.macro.ware}.free':capacity}
            self.assertEqual(bool(expr(g.get('value'),values)),wanted)
        self.assertEqual([(n.tag,n.get('object'),n.get('drop')) for n in g],[('collect_drop','player.ship','$drop')])
        q=copy.deepcopy(self.patched[p]);q.xpath(s)[0].set('value',self.one(p,s,False).get('value'))
        self.assertEqual(canonical(q),canonical(self.original[p]))

    def test_optional_exact_old_guard_patches_do_not_overwrite_upstream_fix(self):
        for p,s in [('extensions/galaxy_trader/md/gt_context_academy.xml',".//library[@name='GT_Academy_BuildShipEntryIfEligible']/actions/do_if"),('extensions/fbl/md/fbl.xml',".//do_if[@value='$drop.isclass.collectableammo']/do_if")]:
            original=copy.deepcopy(self.original[p]);original.xpath(s)[0].set('value','upstream_future_guard')
            patched=apply_patch(original,E.parse(str(MOD/p)).getroot())
            self.assertEqual(canonical(original),canonical(patched))

    def test_protected_ui_inventory_collector_and_companions_untouched(self):
        files={p.relative_to(MOD).as_posix() for p in MOD.rglob('*') if p.is_file()}
        self.assertFalse(any(p.endswith('.lua') or p.startswith(('ui/','assets/','index/')) for p in files))
        self.assertFalse(any('fs_inv' in p or 'vardath_galactic' in p or 'kopis' in p for p in files))
        content=E.parse(str(MOD/'content.xml')).getroot()
        self.assertEqual(content.get('save'),'0')
        self.assertEqual(content.find('./dependency[@version]').get('version'),'900')
        self.assertTrue(all(x.get('optional')=='true' for x in content.findall('./dependency[@id]')))

def validate(cache, archive=None):
    original=references(cache)
    schema=E.XMLSchema(E.ElementTree(original['libraries/diff.xsd']))
    patched={};counts=[]
    for item in SOURCES:
        p=MOD/item['path']
        if not p.exists():continue
        patch=E.parse(str(p)).getroot();schema.assertValid(patch)
        patched[item['path']]=apply_patch(original[item['path']],patch,counts)
    if len(patched)!=6:raise ValueError('Expected exactly six targeted diff files')
    # Check the actual native metadata supporting the added guards.
    props=original['libraries/scriptproperties.xml']
    for name in ('ware','hasmission','ammostorage.{$ware}.free'):
        if not props.xpath('.//property[@name="'+name+'"]'):raise ValueError('Missing native property '+name)
    n={'x':'http://www.w3.org/2001/XMLSchema'}
    md=original['libraries/md.xsd'];common=original['libraries/common.xsd']
    if not md.xpath('.//x:enumeration[@value="cuestate.waiting"]',namespaces=n):raise ValueError('Missing native cue state')
    for event in ('event_conversation_started','event_conversation_returned_to_section'):
        doc=' '.join(common.xpath('.//x:element[@name="'+event+'"]//x:documentation/text()',namespaces=n))
        if 'object = actor' not in doc:raise ValueError('Conversation actor event mapping changed')
    Contracts.original,Contracts.patched=original,patched
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    count=suite.countTestCases();result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise ValueError('Source/guard contracts failed')
    members=[]
    if archive:
        with ZipFile(archive) as z:
            if z.testzip():raise ValueError('ZIP CRC failure')
            expected={'extensions/'+MOD.name+'/'+p.relative_to(MOD).as_posix():p.read_bytes() for p in MOD.rglob('*') if p.is_file()}
            if set(z.namelist())!=set(expected):raise ValueError('Archive source membership mismatch')
            for name,data in expected.items():
                if z.read(name)!=data:raise ValueError('Archive source mismatch '+name)
            members=sorted(expected)
    return {'version':'1.0.0','reference_files':len(original),'diff_files':len(patched),'single_match_operations':len(counts),'contract_tests':count,'result':'pass','archive_members':len(members),'runtime_tested':False,'limitations':['No X4 executable, save or merged installed catalogs available.','Tests apply patches to exact pinned references, not the effective installed load order.','Native runtime, reload and same-frame event behavior require in-game acceptance.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-cache',type=Path);parser.add_argument('--zip',type=Path);parser.add_argument('--report',type=Path);args=parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:report=validate(args.source_cache or Path(tmp),args.zip)
    if args.report:args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
