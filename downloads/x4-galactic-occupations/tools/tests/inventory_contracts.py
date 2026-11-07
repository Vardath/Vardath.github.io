#!/usr/bin/env python3
"""Execute the forwarding XML against mocked inventory actions, not the X4 engine.

This deliberately limited interpreter checks the actual helper's accounting and
rollback paths. It cannot establish X4 expression parsing or native pickup effects.
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

MOD = Path(__file__).resolve().parents[2] / 'vardath_galactic_occupations'
WARES = [f'inv_crystal_0{i}' for i in range(1, 6)]
SENT = 'player.entity.$vgo_objects.{this.ship}.$vgo_crystal_sent'

class Return(Exception): pass
class Continue(Exception): pass

class InventoryVM:
    def __init__(self, source=None, player=None, remove_limit=None, credit_limit=None,
                 owned=True, pilot=True, same_entity=False):
        self.stock = {'captain': dict(source or {}), 'player': dict(player or {})}
        self.vars = {}
        self.sent = 0
        self.remove_limit, self.credit_limit = remove_limit, credit_limit
        self.owned, self.pilot, self.same_entity = owned, pilot, same_entity
        self.root = ET.parse(MOD / 'aiscripts/vardath.go.forwardcrystals.xml').getroot()

    def expression(self, text):
        s = text.replace('@' + SENT, 'sent').replace(SENT, 'sent')
        s = re.sub(r'this\.ship\.pilot\.inventory\.\{\$ware\}\.count', "inventory('captain', v('ware'))", s)
        s = re.sub(r'player\.entity\.inventory\.\{\$ware\}\.count', "inventory('player', v('ware'))", s)
        s = s.replace('this.ship.isplayerowned', 'owned').replace('this.ship.pilot.exists', 'pilot')
        s = s.replace('this.ship.pilot == player.entity', 'same_entity')
        s = re.sub(r'ware\.(inv_crystal_0[1-5])', lambda m: repr(m[1]), s)
        s = re.sub(r'\$(\w+)', lambda m: "v(" + repr(m[1]) + ")", s)
        for token, op in [('le', '<='), ('ge', '>='), ('lt', '<'), ('gt', '>')]:
            s = re.sub(r'\b' + token + r'\b', op, s)
        while re.search(r'\[([^\[\]]*)\]\.(min|max)', s):
            s = re.sub(r'\[([^\[\]]*)\]\.(min|max)', lambda m: m[2] + '(' + m[1] + ')', s)
        return eval(s, {'__builtins__': {}}, {
            'v': lambda name: self.vars[name],
            'inventory': lambda owner, ware: self.stock[owner].get(ware, 0),
            'min': min, 'max': max, 'owned': self.owned, 'pilot': self.pilot,
            'same_entity': self.same_entity, 'sent': self.sent,
        })

    def execute(self, nodes):
        for n in nodes:
            if n.tag == 'set_value':
                value = self.expression(n.get('exact'))
                if n.get('name') == SENT: self.sent = value
                else: self.vars[n.get('name').lstrip('$')] = value
            elif n.tag == 'do_if':
                if self.expression(n.get('value')): self.execute(n)
            elif n.tag == 'do_for_each':
                for value in self.expression(n.get('in')):
                    self.vars[n.get('name').lstrip('$')] = value
                    try: self.execute(n)
                    except Continue: pass
            elif n.tag == 'continue': raise Continue()
            elif n.tag == 'return': raise Return(self.expression(n.get('value')))
            elif n.tag in ('remove_inventory', 'add_inventory'):
                owner = {'this.ship.pilot': 'captain', 'player.entity': 'player'}[n.get('entity')]
                ware, requested = self.expression(n.get('ware')), self.expression(n.get('exact'))
                if requested < 0: raise AssertionError('Negative inventory mutation')
                stock = self.stock[owner]
                if n.tag == 'remove_inventory':
                    amount = min(requested, stock.get(ware, 0))
                    if self.remove_limit is not None: amount = min(amount, self.remove_limit)
                    stock[ware] = stock.get(ware, 0) - amount
                else:
                    amount = requested
                    if owner == 'player' and self.credit_limit is not None: amount = min(amount, self.credit_limit)
                    stock[ware] = stock.get(ware, 0) + amount
            elif n.tag in ('write_to_logbook', 'debug_text'): pass
            elif not isinstance(n.tag, str): pass
            else: raise AssertionError('Unsupported test-interpreter action: ' + n.tag)

    def run(self):
        try: self.execute(self.root.find('attention/actions'))
        except Return as result: return result.args[0]
        raise AssertionError('Missing return')

class InventoryContracts(unittest.TestCase):
    def test_all_five_existing_crystals_forward_with_quantity_preserved(self):
        vm = InventoryVM({w: i + 1 for i, w in enumerate(WARES)}, {w: 20 for w in WARES})
        self.assertEqual(vm.run(), 15)
        self.assertEqual(vm.sent, 15)
        for i, w in enumerate(WARES):
            self.assertEqual(vm.stock['captain'][w], 0)
            self.assertEqual(vm.stock['player'][w], 21 + i)

    def test_empty_inventory_never_creates_crystals(self):
        vm = InventoryVM()
        self.assertEqual(vm.run(), 0)
        self.assertEqual(vm.stock['player'], {})

    def test_rejected_withdrawal_never_credits_player(self):
        vm = InventoryVM({WARES[0]: 5}, remove_limit=0)
        self.assertEqual(vm.run(), 0)
        self.assertEqual(vm.stock['captain'][WARES[0]], 5)
        self.assertEqual(vm.stock['player'], {})

    def test_rejected_player_addition_restores_source(self):
        vm = InventoryVM({WARES[0]: 5}, credit_limit=0)
        self.assertEqual(vm.run(), 0)
        self.assertEqual(vm.stock['captain'][WARES[0]], 5)
        self.assertEqual(vm.stock['player'].get(WARES[0], 0), 0)

    def test_partial_withdrawal_credits_only_removed_amount(self):
        vm = InventoryVM({WARES[0]: 5}, remove_limit=2)
        self.assertEqual(vm.run(), 2)
        self.assertEqual(vm.stock['captain'][WARES[0]], 3)
        self.assertEqual(vm.stock['player'][WARES[0]], 2)

    def test_partial_player_addition_and_retry_do_not_duplicate(self):
        vm = InventoryVM({WARES[0]: 5}, credit_limit=2)
        self.assertEqual(vm.run(), 2)
        self.assertEqual(vm.stock['captain'][WARES[0]], 3)
        vm.credit_limit = None
        self.assertEqual(vm.run(), 3)
        self.assertEqual(vm.run(), 0)
        self.assertEqual(vm.stock['player'][WARES[0]], 5)
        self.assertEqual(vm.sent, 5)

    def test_unrelated_inventory_items_are_untouched(self):
        vm = InventoryVM({WARES[0]: 5, 'inv_parts': 19}, {'inv_parts': 7})
        self.assertEqual(vm.run(), 5)
        self.assertEqual(vm.stock['captain']['inv_parts'], 19)
        self.assertEqual(vm.stock['player']['inv_parts'], 7)

    def test_unowned_missing_pilot_and_same_inventory_are_not_modified(self):
        for args in [{'owned': False}, {'pilot': False}, {'same_entity': True}]:
            with self.subTest(args=args):
                vm = InventoryVM({WARES[0]: 5}, **args)
                self.assertEqual(vm.run(), 0)
                self.assertEqual(vm.stock['captain'][WARES[0]], 5)
                self.assertEqual(vm.stock['player'], {})

if __name__ == '__main__': unittest.main(verbosity=1)
