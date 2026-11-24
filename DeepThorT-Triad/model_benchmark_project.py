"""Independent behavior checks for a two-module dispatch fixture."""
import ast
import json
import sys

from model_benchmark_score import Unsupported, code_result, equal, pairs

BUILD = """Create a tiny Python package with two files. stock.py defines loadable(stock, capacity), which returns the smaller of these nonnegative integers. dispatch.py must import loadable using 'from stock import loadable' and define remaining(stock, capacity), which returns the stock left after loading. Use the imported function. Return exactly one JSON object mapping both file names to complete Python source strings, without markdown. Keep each implementation to its one function and the required import. Use ordinary integer expressions, min/max and return."""
AMEND = """Keep the original package contract. The new rule reserves two units of stock before loading, even if the destination has more room. Amend only stock.py. Return exactly one JSON object mapping stock.py to its complete replacement source."""
REPAIR = """Fix this existing two-file package. loadable(stock, capacity) returns the smaller nonnegative argument. remaining(stock, capacity) must return the stock left after loading, using the imported loadable function. A consumer reported a failing test. Preserve the public interface and stock.py. Return exactly one JSON object mapping dispatch.py to its complete replacement source."""
SEED = {
    'stock.py': 'def loadable(stock, capacity):\n    return min(stock, capacity)\n',
    'dispatch.py': 'from stock import loadable\n\ndef remaining(stock, capacity):\n    return capacity - loadable(stock, capacity)\n',
}
CASES = [(0, 0), (8, 3), (3, 8), (1, 1), (9, 0), (7, 7), (13, 12), (2, 9)]

def check(files, reserved):
    load = files['stock.py']
    tree = ast.parse(files['dispatch.py'])
    if len(tree.body) != 2 or not isinstance(tree.body[0], ast.ImportFrom):
        raise ValueError('dispatch.py requires the stock import followed by remaining')
    dep, fn = tree.body
    if dep.level or dep.module != 'stock' or len(dep.names) != 1 or dep.names[0].name != 'loadable' or dep.names[0].asname:
        raise ValueError('dispatch.py must import loadable from stock')
    body = ast.unparse(fn)
    for stock, capacity in CASES:
        expected = min(max(0, stock-reserved), capacity)
        if not equal(code_result(load, 'loadable', [stock,capacity]), expected):
            return f'loadable({stock}, {capacity}) expected {expected}'
        calls = []
        def dependency(a, b):
            calls.append((a, b))
            return code_result(load, 'loadable', [a,b])
        actual = code_result(body, 'remaining', [stock,capacity], {'loadable':dependency})
        if not equal(actual, stock-expected) or (stock,capacity) not in calls:
            return f'remaining({stock}, {capacity}) expected {stock-expected} using loadable(stock, capacity)'
    return None

def judge(stage, before, answer):
    expected = {'build':set(SEED), 'amend':{'stock.py'}, 'repair':{'dispatch.py'}}[stage]
    try:
        if len(answer) > 16000:
            raise ValueError('answer exceeds response budget')
        changes = json.loads(answer, object_pairs_hook=pairs)
        if type(changes) is not dict or set(changes) != expected or not all(type(s) is str and len(s)<=6000 for s in changes.values()):
            raise ValueError('return exactly the requested file paths and source strings')
        files = {**before, **changes}
        failure = check(files, 2 if stage == 'amend' else 0)
        return {'passed':failure is None, 'diagnostic':failure, 'files':files}
    except (ValueError, TypeError, SyntaxError, ArithmeticError, LookupError, RecursionError) as exc:
        return {'passed':False, 'diagnostic':str(exc)[:350], 'files':before}

if __name__ == '__main__':
    request = json.load(sys.stdin)
    if request['op']=='spec':
        print(json.dumps(dict(build=BUILD, amend=AMEND, repair=REPAIR, seed=SEED, seed_failure=check(SEED,0))))
    else:
        print(json.dumps(judge(request['stage'], request['before'], request['answer'])))
