import unittest
from deepthort_local.mcp_calls import validate_args
from deepthort_local.mcp_calls_probe import exercise

class MCPCallTests(unittest.TestCase):
    def test_loopback(self):
        result=exercise();self.assertEqual(result['status'],'passed',result)
    def test_closed_schema_subset(self):
        schema={'type':'object','properties':{'count':{'type':'integer','minimum':1,'maximum':3},'mode':{'type':'string','enum':['safe']}},'required':['count']}
        self.assertEqual(validate_args(schema,{'count':2}),{'count':2})
        for args in ({},{'count':True},{'count':4},{'count':2,'extra':1},{'count':2,'mode':'wrong'}):
            with self.assertRaises(ValueError):validate_args(schema,args)
        with self.assertRaises(ValueError):validate_args(dict(schema,allOf=[]),{'count':2})
        with self.assertRaises(ValueError):validate_args({'type':'object','properties':{'x':{'type':'array'}}},{'x':[]})
