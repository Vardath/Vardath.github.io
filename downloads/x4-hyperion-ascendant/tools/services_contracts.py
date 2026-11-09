"""Execute the shipped service XML with explicit mocked native boundaries.

This is not an X4 engine. Native module attachment, docking and construction
still need live acceptance. Unsupported actions/expressions fail these tests.
"""
import ast
import copy
import re
import unittest
from pathlib import Path
from lxml import etree as E

MOD = Path(__file__).resolve().parents[1] / 'vardath_hyperion_ascendant'
REFS = {}
ASC = 'macro.ship_vardath_hyperion_ascendant_macro'
CARGO = 'macro.ship_gen_xs_cargodrone_empty_01_a_macro'
BUILD = 'macro.ship_gen_xs_buildingdrone_01_a_macro'
FLARES = 'macro.countermeasure_flares_01_macro'
DEPLOYABLES = ['macro.eq_arg_satellite_02_macro', 'macro.eq_arg_resourceprobe_01_macro',
               'macro.env_deco_nav_beacon_t1_macro', 'macro.weapon_gen_mine_03_macro']
STORES = {f'macro.storage_vardath_hyperion_{k}_macro': k for k in ('container', 'solid', 'liquid')}
HANGAR = 'macro.shipstorage_vardath_hyperion_s_macro'
VAR = re.compile(r'@?\$[A-Za-z_]\w*(?:\.(?:\$?\w+|\{[^{}]+\}))*\??')

class Part:
    def __init__(self, macro, parent, capacity=0, stored=None, isstorage=True):
        self.macro, self.container, self.exists = macro, parent, True
        self.isstorage, self.docksize = isstorage, ['tag.dock_s']
        self.shipstorage = {'capacity': capacity}
        self.stored = list(stored or [])

class Ship:
    def __init__(self, new=False, owner='player', macro=ASC):
        self.exists = self.isoperational = True
        self.owner = self.trueowner = owner
        self.macro, self.state = macro, {}
        self.cap = dict(container=2000000 if new else 12000, solid=0, liquid=0, universal=0)
        self.unit_max, self.units = 1024, {}
        self.unavailable = {}  # subset of the stored inventory, not extra free slots
        self.ammo_max = dict(countermeasure=1000, deployable=10000, missile=10000)
        self.ammo, self.crew_capacity = {}, 700
        self.bays = [Part(HANGAR if new else 'macro.shipstorage_gen_s_two_macro', self,
                          1000 if new else 2, stored=['original-S1', 'original-S2'])]
        self.parts = []
        self.cargo = {'ore': 125, 'foodrations': 40}
        self.crew = ['original-captain', 'original-service', 'original-passenger']
        self.equipment = {'engine': 'custom-drive', 'mods': ['original-upgrade']}
        self.orders = ['original-player-order', 'original-default']
    @property
    def isplayerowned(self): return self.trueowner == 'player'

class Proxy:
    def __init__(self, ship, kind, key=None): self.ship, self.kind, self.key = ship, kind, key

class VM:
    def __init__(self, ships=None, age=0, create_mode='attached', accept_supplies=True):
        self.ships, self.age = list(ships or []), age
        self.values, self.calls, self.logs = {}, [], []
        self.create_mode, self.accept_supplies = create_mode, accept_supplies
        self.tree = E.parse(str(MOD / 'md/VHA_Services.xml'))
    def ammo_type(self, macro):
        return 'countermeasure' if macro == FLARES else ('deployable' if macro in DEPLOYABLES else 'missile')
    def ammo_count(self, ship, kind): return sum(v for k, v in ship.ammo.items() if self.ammo_type(k) == kind)
    def get(self, obj, key):
        if obj is None and key == 'exists': return False
        if isinstance(obj, Ship):
            if str(key).startswith('$'): return obj.state[key]
            if key == 'cargo': return Proxy(obj, 'cargo')
            if key == 'units': return Proxy(obj, 'units')
            if key == 'ammostorage': return Proxy(obj, 'ammo')
            if key == 'people': return {'capacity': obj.crew_capacity}
            return getattr(obj, key)
        if isinstance(obj, Proxy):
            s = obj.ship
            if obj.kind == 'cargo' and key == 'capacity': return Proxy(s, 'capacity')
            if obj.kind == 'capacity': return s.cap[str(key).removeprefix('tag.')]
            if obj.kind == 'units':
                if key == 'count': return sum(s.units.values())
                if key == 'maxcount': return s.unit_max
                if key == 'free': return s.unit_max - sum(s.units.values())
                return Proxy(s, 'unit-selection', key)
            if obj.kind == 'unit-selection' and key == 'count':
                if obj.key == 'unitcategory.build': return s.units.get(BUILD, 0)
                if obj.key == 'unitcategory.transport': return s.units.get(CARGO, 0)
                return s.units.get(obj.key, 0)
            if obj.kind == 'ammo': return Proxy(s, 'ammo-selection', key)
            if obj.kind == 'ammo-selection':
                if key == 'count': return self.ammo_count(s, obj.key)
                if key == 'capacity': return s.ammo_max[obj.key]
                if key == 'free': return s.ammo_max[obj.key] - self.ammo_count(s, obj.key)
            raise KeyError((obj.kind, key))
        if isinstance(obj, list):
            if key == 'count': return len(obj)
            if key == 'indexof': return lambda k: obj.index(k) + 1 if k in obj else 0
            if isinstance(key, int): return obj[key - 1]
        if callable(obj): return obj(key)
        if isinstance(obj, dict): return obj[key]
        return getattr(obj, key)
    def path(self, token):
        raw = token.removeprefix('@').removesuffix('?')[1:]
        out = []
        for dynamic, plain in re.findall(r'\{([^{}]+)\}|([^\.{}]+)', raw):
            out.append(self.expr(dynamic) if dynamic else plain)
        return out
    def variable(self, token):
        try:
            parts = self.path(token); obj = self.values[parts[0]]
            for key in parts[1:]: obj = self.get(obj, key)
            return True if token.endswith('?') else obj
        except (KeyError, AttributeError, IndexError, TypeError):
            if token.endswith('?'): return False
            if token.startswith('@'): return None
            raise ValueError('Unresolved native field: ' + token)
    def expr(self, source):
        source = source.strip()
        if source == 'table[]': return {}
        if source.startswith('if '):
            cond, branches = source[3:].split(' then ', 1); yes, no = branches.split(' else ', 1)
            return self.expr(yes if self.expr(cond) else no)
        for suffix, fn in [('.min', min), ('.max', max)]:
            if source.endswith(suffix): return fn(self.expr(source[:-len(suffix)]))
        bindings = {}
        def bind(value, lazy=False):
            key = 'v' + str(len(bindings)); bindings[key] = value; return key + ('()' if lazy else '')
        source = VAR.sub(lambda m: bind(lambda token=m[0]: self.variable(token), lazy=True), source)
        source = re.sub(r'\b(?:macro|tag|unitcategory)\.\w+', lambda m: bind(m[0]), source)
        source = re.sub(r'\bplayer\.(?:galaxy\.exists|exists|age)\b', lambda m: bind(self.age if m[0] == 'player.age' else True), source)
        source = re.sub(r'\b(\d+)min\b', lambda m: str(int(m[1]) * 60), source)
        source = re.sub(r'\b(\d+)s\b', r'\1', source)
        for word, op in [(' ge ', ' >= '), (' le ', ' <= '), (' gt ', ' > '), (' lt ', ' < ')]: source = source.replace(word, op)
        for word, value in [('true', 'True'), ('false', 'False'), ('null', 'None')]: source = re.sub(r'\b' + word + r'\b', value, source)
        tree = ast.parse(source, mode='eval')
        allowed = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Name, ast.Load, ast.Constant, ast.UnaryOp, ast.Not, ast.USub, ast.BinOp, ast.Add, ast.Sub, ast.List, ast.Call)
        if any(not isinstance(n, allowed) for n in ast.walk(tree)): raise ValueError('Unsupported XML expression: ' + source)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and (not isinstance(n.func, ast.Name) or not callable(bindings.get(n.func.id)) or n.args or n.keywords): raise ValueError('Only generated lazy field lookups are permitted')
        return eval(compile(tree, '<service XML>', 'eval'), {'__builtins__': {}}, bindings)
    def assign(self, target, value):
        parts = self.path(target)
        if len(parts) == 1: self.values[parts[0]] = value; return
        obj = self.values[parts[0]]
        for key in parts[1:-1]: obj = self.get(obj, key)
        if isinstance(obj, Ship): obj.state[parts[-1]] = value
        else: obj[parts[-1]] = value
    def execute(self, nodes):
        taken = None
        for node in nodes:
            tag = node.tag
            if not isinstance(tag, str): continue
            if tag == 'do_if':
                taken = bool(self.expr(node.get('value')))
                if taken: self.execute(node)
                continue
            if tag in ('do_elseif', 'do_else'):
                if taken is None: raise ValueError('Orphan branch')
                if not taken and (tag == 'do_else' or self.expr(node.get('value'))): self.execute(node); taken = True
                continue
            taken = None
            if tag == 'set_value': self.assign(node.get('name'), self.expr(node.get('exact')))
            elif tag == 'do_for_each':
                for index, value in enumerate(list(self.expr(node.get('in'))), 1):
                    self.assign(node.get('name'), value)
                    if node.get('counter'): self.assign(node.get('counter'), index)
                    self.execute(node)
            elif tag == 'do_all':
                for index in range(1, int(self.expr(node.get('exact'))) + 1):
                    if node.get('counter'): self.assign(node.get('counter'), index)
                    self.execute(node)
            elif tag == 'include_actions': self.library(node.get('ref'))
            elif tag == 'find_ship_by_true_owner':
                if node.get('faction') != 'faction.player' or node.get('space') != 'player.galaxy': raise ValueError('Wrong scope')
                self.assign(node.get('name'), [s for s in self.ships if s.trueowner == 'player' and s.macro == self.expr(node.get('macro'))])
            elif tag == 'find_object_component':
                ship = self.expr(node.get('object')); macro = self.expr(node.get('macro'))
                self.assign(node.get('name'), [p for p in ship.parts + ship.bays if p.exists and p.macro == macro])
            elif tag == 'find_dockingbay': self.assign(node.get('name'), list(self.expr(node.get('object')).bays))
            elif tag == 'create_module':
                ship, macro = self.expr(node.get('object')), self.expr(node.get('macro')); self.calls.append((tag, macro))
                part = None
                if self.create_mode == 'throw': raise RuntimeError('Native module rejection')
                if self.create_mode != 'refused':
                    part = Part(macro, ship if self.create_mode != 'detached' else None, 1000 if macro == HANGAR else 0)
                    if self.create_mode == 'attached':
                        if macro == HANGAR: ship.bays.append(part)
                        elif macro in STORES: ship.cap[STORES[macro]] += 2000000; ship.parts.append(part)
                        else: raise ValueError('Unknown module macro')
                self.assign(node.get('name'), part)
            elif tag in ('add_ammo', 'add_units'):
                ship, macro = self.expr(node.get('object')), self.expr(node.get('macro'))
                amount = self.expr(node.get('amount') if tag == 'add_ammo' else node.get('exact'))
                self.calls.append((tag, macro, amount))
                if amount <= 0: raise ValueError('Non-positive supply')
                if tag == 'add_ammo':
                    if macro not in [FLARES, *DEPLOYABLES]: raise ValueError('Non-requested ammunition')
                    if amount > ship.ammo_max[self.ammo_type(macro)] - self.ammo_count(ship, self.ammo_type(macro)): raise ValueError('Ammo overfill')
                    if self.accept_supplies: ship.ammo[macro] = ship.ammo.get(macro, 0) + amount
                else:
                    if macro not in (BUILD, CARGO): raise ValueError('Non-requested drone')
                    if amount > ship.unit_max - sum(ship.units.values()): raise ValueError('Unit overfill')
                    if self.accept_supplies: ship.units[macro] = ship.units.get(macro, 0) + amount
            elif tag in ('debug_text', 'write_to_logbook'): self.logs.append((tag, node.get('text'), dict(self.values)))
            elif tag != 'reset_cue': raise ValueError('Unsupported XML action: ' + tag)
    def library(self, name): self.execute(self.tree.find(".//library[@name='" + name + "']/actions"))
    def cue(self, name):
        node = self.tree.find(".//cue[@name='" + name + "']")
        if self.expr(node.find('conditions/check_value').get('value')): self.execute(node.find('actions'))
        return self

class ServiceContracts(unittest.TestCase):
    def test_hangar_is_real_internal_small_storage_served_by_existing_pads(self):
        r=E.parse(str(MOD/'assets/props/SurfaceElements/macros/shipstorage_vardath_hyperion_s_macro.xml'))
        self.assertEqual(r.find('macro').get('class'),'dockingbay');self.assertEqual(r.find('.//component').get('ref'),'generic_dockingbay')
        self.assertEqual(r.find('.//dock').attrib,{'capacity':'1000','storage':'1'});self.assertEqual(r.find('.//docksize').get('tags'),'dock_s');self.assertEqual(r.find('.//room').get('walkable'),'0')
        ship=E.parse(str(MOD/'assets/units/size_l/macros/ship_vardath_hyperion_ascendant_macro.xml'))
        self.assertEqual(ship.find(".//connection[@ref='con_shipstorage_s_01']/macro").get('ref'),HANGAR.removeprefix('macro.'))
    def test_native_and_optional_payroll_patches_only_expand_real_builder_queries(self):
        cases=[('buildstorage',MOD/'aiscripts/build.buildstorage.xml','$constructionvessels'),('builder_contracts',MOD/'extensions/vardath_living_factions_builders/md/vardath_builder_contracts.xml','$Builders')]
        for key,path,name in cases:
            original=REFS[key];patched=copy.deepcopy(original);ops=[n for n in E.parse(str(path)).getroot() if isinstance(n.tag,str)];self.assertEqual(len(ops),1)
            op=ops[0];matches=patched.xpath(op.get('sel'));self.assertEqual(len(matches),1);attribute=matches[0];self.assertTrue(attribute.is_attribute);self.assertEqual(attribute.attrname,'class');self.assertEqual(str(attribute),'class.ship_xl')
            attribute.getparent().set(attribute.attrname,op.text);expected=copy.deepcopy(original);expected.xpath("//find_ship[@name='"+name+"']")[0].set('class','[class.ship_l, class.ship_xl]')
            self.assertEqual(E.tostring(patched,method='c14n'),E.tostring(expected,method='c14n'))
        text=REFS['interact'];block=text.split('elseif actiontype == "build" then',1)[1].split('elseif actiontype == "buildships"',1)[0]
        self.assertIn('"primarypurpose") == "build"',block);self.assertNotIn('ship_xl',block)
    def test_new_native_actions_use_only_declared_command_attributes(self):
        roots=[REFS['commands'],REFS['md_schema']];ns={'xs':'http://www.w3.org/2001/XMLSchema'}
        definitions={}
        for root in roots:
            for n in root.xpath('xs:attributeGroup[@name] | xs:complexType[@name]',namespaces=ns):definitions[n.get('name')]=n
        def attributes(node,seen=None):
            seen=set(seen or []);out=set(node.xpath('.//xs:attribute/@name',namespaces=ns))
            for ref in node.xpath('.//xs:attributeGroup/@ref | .//xs:extension/@base',namespaces=ns)+([node.get('type')] if node.get('type') else []):
                if ref not in seen and ref in definitions:out.update(attributes(definitions[ref],seen|{ref}))
            return out
        script=E.parse(str(MOD/'md/VHA_Services.xml'))
        for n in script.xpath('//actions//* | //conditions/check_value'):
            if not isinstance(n.tag,str):continue
            found=[x for root in roots for x in root.xpath('.//xs:element[@name="'+n.tag+'"]',namespaces=ns)]
            self.assertTrue(found,'Undeclared native action '+n.tag)
            self.assertTrue(set(n.attrib)<=set().union(*(attributes(x) for x in found)),(n.tag,set(n.attrib)))
    def test_capacities_double_actual_forge_and_crew_700(self):
        ship = E.parse(str(MOD / 'assets/units/size_l/macros/ship_vardath_hyperion_ascendant_macro.xml'))
        old = REFS['kopis_ship'].find('.//properties/storage'); new = ship.find('.//properties/storage')
        for key in ('missile', 'unit', 'deployable', 'countermeasure'): self.assertEqual(int(new.get(key)), 2 * int(old.get(key)))
        self.assertEqual(ship.find('.//people').get('capacity'), '700')
        for kind in ('container', 'solid', 'liquid'):
            macro = E.parse(str(MOD / f'assets/props/StorageModules/macros/storage_vardath_hyperion_{kind}_macro.xml'))
            self.assertEqual(int(macro.find('.//cargo').get('max')), 2 * int(REFS['kopis_' + kind].find('.//cargo').get('max')))
            self.assertEqual(macro.find('.//cargo').get('tags'), kind)
    def test_native_l_build_orders_drone_rules_and_connection_support(self):
        for key in ('build_deploy', 'find_build_task'):
            self.assertEqual(REFS[key].find('./order/requires').get('primarypurpose'), 'purpose.build')
            self.assertIsNone(REFS[key].find('./order/requires').get('class'))
        self.assertTrue(REFS['defaults'].xpath("/defaults/dataset[@class='ship']/connections/connection[@name='constructionvessel']"))
        self.assertTrue(REFS['unit_rules'].xpath("//rule[@category='build'][contains(@classes,'ship_l')][contains(@purposes,'build')]"))
        ship = E.parse(str(MOD / 'assets/units/size_l/macros/ship_vardath_hyperion_ascendant_macro.xml'))
        self.assertEqual(ship.find('macro').get('class'), 'ship_l'); self.assertEqual(ship.find('.//purpose').get('primary'), 'build'); self.assertEqual(ship.find('.//properties/ship').get('type'), 'builder')
        self.assertEqual(ship.find(".//connection[@ref='con_buildmodule_01']/macro").get('ref'), 'buildmodule_gen_carrier_s_macro')
    def test_mine_is_actual_friend_foe_not_tracker_or_standard(self):
        self.assertEqual(REFS['texts'].xpath("//page[@id='20201']/t[@id='20901']/text()")[0], 'Friend/Foe Mine')
        self.assertEqual(REFS['wares'].xpath("//ware[@name='{20201,20901}']/component/@ref"), ['weapon_gen_mine_03_macro'])
        tree = E.parse(str(MOD / 'md/VHA_Services.xml'))
        self.assertIn('macro.weapon_gen_mine_03_macro', tree.find(".//set_value[@name='$AmmoMacros']").get('exact'))
    def test_existing_retrofit_is_additive_idempotent_and_preserves_originals(self):
        ship = Ship(); before = copy.deepcopy((ship.cargo, ship.crew, ship.equipment, ship.orders, ship.bays[0].stored))
        VM([ship], age=0).cue('RetrofitV102'); vm = VM([ship], age=60).cue('RetrofitV102')
        self.assertEqual(len([c for c in vm.calls if c[0] == 'create_module']), 4)
        self.assertGreaterEqual(min(ship.cap[k] for k in ('container', 'solid', 'liquid')), 2000000)
        self.assertEqual(sum(b.shipstorage['capacity'] for b in ship.bays), 1002)
        self.assertEqual(ship.state['$vha_capacity_state_v102'], 'verified')
        self.assertEqual((ship.cargo, ship.crew, ship.equipment, ship.orders, ship.bays[0].stored), before)
        self.assertFalse(VM([ship], age=120).cue('RetrofitV102').calls)
    def test_new_hull_needs_only_the_two_additional_typed_bays(self):
        ship = Ship(new=True); VM([ship], age=0).cue('RetrofitV102'); vm = VM([ship], age=60).cue('RetrofitV102')
        self.assertEqual([c[1] for c in vm.calls], ['macro.storage_vardath_hyperion_solid_macro', 'macro.storage_vardath_hyperion_liquid_macro'])
        self.assertEqual(ship.state['$vha_capacity_state_v102'], 'verified')
    def test_physical_pads_and_other_size_storage_do_not_count_as_small_storage(self):
        ship = Ship(); pad = Part('physical-pad', ship, 999, isstorage=False); medium = Part('medium-bay', ship, 999); medium.docksize = ['tag.dock_m']
        ship.bays.extend([pad, medium]); vm = VM(); vm.values['Ship'] = ship; vm.library('ReadSmallStorageV102'); self.assertEqual(vm.values['SmallCapacity'], 2)
    def test_refused_or_detached_modules_are_pending_without_repeated_creation(self):
        for mode in ('refused', 'detached'):
            with self.subTest(mode=mode):
                ship = Ship(); VM([ship], age=0).cue('RetrofitV102'); vm = VM([ship], age=60, create_mode=mode).cue('RetrofitV102')
                self.assertEqual(ship.state['$vha_capacity_state_v102'], 'pending')
                self.assertEqual(len(vm.calls), 4); self.assertFalse(VM([ship], age=120, create_mode=mode).cue('RetrofitV102').calls)
    def test_native_attachment_error_does_not_disable_independent_replenishment(self):
        ship = Ship(); VM([ship], age=0).cue('RetrofitV102')
        with self.assertRaises(RuntimeError): VM([ship], age=60, create_mode='throw').cue('RetrofitV102')
        VM([ship], age=60).cue('ReplenishV102'); vm = VM([ship], age=660).cue('ReplenishV102')
        self.assertEqual(ship.ammo.get(FLARES), 5); self.assertTrue(any(c[0] == 'add_units' for c in vm.calls))
    def test_existing_universal_cargo_is_not_mixed_with_typed_bays(self):
        ship = Ship(); ship.cap['universal'] = 6000000; VM([ship], age=0).cue('RetrofitV102'); vm = VM([ship], age=60).cue('RetrofitV102')
        self.assertFalse(any(c[1] in STORES for c in vm.calls)); self.assertEqual(ship.cap['universal'], 6000000)
        self.assertEqual(ship.state['$vha_capacity_state_v102'], 'pending')
    def test_saved_deadline_prevents_load_farming_and_clock_jump_catchup(self):
        ship = Ship(); VM([ship], age=0).cue('ReplenishV102'); VM([ship], age=60).cue('ReplenishV102')
        self.assertFalse(ship.ammo); self.assertEqual(ship.units.get(BUILD), 30)
        VM([ship], age=599).cue('ReplenishV102'); self.assertFalse(ship.ammo)
        VM([ship], age=600).cue('ReplenishV102'); self.assertEqual(ship.ammo.get(FLARES), 5)
        saved = copy.deepcopy(ship.state); VM([ship], age=600).cue('ReplenishV102'); self.assertEqual(ship.state, saved)
        VM([ship], age=86400).cue('ReplenishV102'); self.assertEqual(ship.ammo.get(FLARES), 10); self.assertEqual(ship.state['$vha_supply_due_v102'], 87000)
    def test_requested_supplies_only_with_no_overfill_or_repair_missile_generation(self):
        ship = Ship(); ship.ammo = {'unrelated-missile': 8}; vm = VM(); vm.values['Ship'] = ship; vm.library('SupplyBatchV102')
        self.assertEqual(ship.ammo[FLARES], 5)
        for macro in DEPLOYABLES: self.assertEqual(ship.ammo[macro], 1)
        self.assertEqual(ship.units, {CARGO: 1, BUILD: 1}); self.assertEqual(ship.ammo['unrelated-missile'], 8)
        ship.ammo_max.update(countermeasure=6, deployable=5); ship.unit_max = 3
        vm.library('SupplyBatchV102'); self.assertEqual(vm.ammo_count(ship, 'countermeasure'), 6); self.assertEqual(vm.ammo_count(ship, 'deployable'), 5); self.assertEqual(sum(ship.units.values()), 3)
        before = copy.deepcopy((ship.ammo, ship.units)); vm.library('SupplyBatchV102'); self.assertEqual((ship.ammo, ship.units), before)
    def test_last_shared_slot_rotates_deployables_and_drone_priority(self):
        ship = Ship(); ship.ammo_max['countermeasure'] = 0; ship.ammo_max['deployable'] = 1; ship.unit_max = 1
        vm = VM(); vm.values['Ship'] = ship; picked = []; drones = []
        for _ in range(4):
            ship.ammo = {}; ship.units = {}; start = len(vm.calls); vm.library('SupplyBatchV102')
            picked.extend(c[1] for c in vm.calls[start:] if c[0] == 'add_ammo'); drones.extend(ship.units)
        self.assertEqual(picked, DEPLOYABLES); self.assertEqual(drones, [CARGO, BUILD, CARGO, BUILD])
    def test_unavailable_requested_drones_still_use_capacity_and_do_not_trigger_seed(self):
        ship = Ship(); ship.unit_max = 40; ship.units = {CARGO: 10, BUILD: 30}; ship.unavailable = dict(ship.units)
        VM([ship], age=0).cue('ReplenishV102'); vm = VM([ship], age=60).cue('ReplenishV102'); VM([ship], age=600).cue('ReplenishV102')
        self.assertEqual(ship.units, ship.unavailable); self.assertFalse(any(c[0] == 'add_units' for c in vm.calls))
    def test_starter_construction_kit_respects_free_space_and_is_not_replayed(self):
        ship = Ship(); ship.unit_max = 3; VM([ship], age=0).cue('ReplenishV102'); VM([ship], age=60).cue('ReplenishV102')
        self.assertEqual(ship.units.get(BUILD), 3); self.assertTrue(ship.state['$vha_builder_seed_v102'])
        ship.units = {}; VM([ship], age=120).cue('ReplenishV102'); self.assertFalse(ship.units)
    def test_owner_unavailable_and_other_macro_are_excluded(self):
        valid, npc, original, dead = Ship(), Ship(owner='npc'), Ship(macro='macro.ship_par_l_expeditionary_01_a_macro'), Ship()
        dead.exists = False
        VM([valid, npc, original, dead], age=0).cue('ReplenishV102'); VM([valid, npc, original, dead], age=600).cue('ReplenishV102')
        self.assertTrue(valid.ammo)
        for ship in (npc, original, dead): self.assertFalse(ship.state); self.assertFalse(ship.ammo); self.assertFalse(ship.units)
    def test_native_supply_refusal_is_not_logged_as_received_and_still_advances_deadline(self):
        ship = Ship(); ship.units = {BUILD: 1}; VM([ship], age=0).cue('ReplenishV102'); vm = VM([ship], age=600, accept_supplies=False).cue('ReplenishV102')
        self.assertEqual(vm.values['AddedAmmo'], 0); self.assertEqual(vm.values['AddedUnits'], 0)
        self.assertFalse(vm.logs); self.assertEqual(ship.state['$vha_supply_due_v102'], 1200)
    def test_new_services_never_remove_stock_ships_people_orders_or_add_trade_cargo(self):
        tree = E.parse(str(MOD / 'md/VHA_Services.xml'))
        for name in ('add_cargo', 'add_wares', 'add_inventory', 'add_money', 'transfer_money_to_player', 'remove_units', 'remove_cargo', 'destroy_object', 'create_ship', 'set_owner', 'remove_npc_template', 'cancel_all_orders', 'apply_loadout'):
            self.assertFalse(tree.findall('.//' + name), name)
        self.assertEqual({n.get('name') for n in tree.findall('./cues/cue')}, {'RetrofitV102', 'ReplenishV102'})
