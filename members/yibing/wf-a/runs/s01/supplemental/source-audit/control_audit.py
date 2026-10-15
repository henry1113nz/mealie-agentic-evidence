"""Supplementary read-only comparison of test guards and constants."""
import ast
import collections
import copy
import json
import pathlib
import subprocess

ROOT = pathlib.Path('/Users/estherzhang/.codex/visualizations/2026/10/05/01a10975-2115-7a22-80b0-324473d3729c/agentic-study')
CLONE = ROOT / 'mealie-wf-a'
OUT = ROOT / 'controller/a-audit'
BASE = 'e365efc71'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=CLONE, text=True)

def functions(tree, prefix=''):
    result = {}
    for node in getattr(tree, 'body', []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            key = prefix + node.name
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result[key] = node
            result.update(functions(node, key + '.'))
    return result

class Bridge(ast.NodeTransformer):
    def visit_Await(self, node):
        return self.visit(node.value)
    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in {'run_db', 'await_db'} and len(node.args) == 1 and not node.keywords:
            return node.args[0]
        return node

def norm(node):
    return ast.dump(Bridge().visit(copy.deepcopy(node)), include_attributes=False)

def consts(node):
    return collections.Counter(repr(x.value) for x in ast.walk(node) if isinstance(x, ast.Constant))

result = {'guard_changes': [], 'constant_changes': [], 'fixture_helper_constant_changes': []}
baseline_paths = set(git('ls-tree', '-r', '--name-only', BASE, '--', 'tests').splitlines())
for file in git('diff', '--name-only', BASE, '--', 'tests').splitlines():
    if not file.endswith('.py') or file.startswith('tests/fixtures/legacy_') or file not in baseline_paths:
        continue
    old = functions(ast.parse(git('show', f'{BASE}:{file}')))
    new = functions(ast.parse((CLONE / file).read_text()))
    for key in sorted(old.keys() & new.keys()):
        a, b = old[key], new[key]
        is_test = key.split('.')[-1].startswith('test_')
        guards_a = [x.test for x in ast.walk(a) if isinstance(x, (ast.If, ast.While, ast.IfExp))]
        guards_b = [x.test for x in ast.walk(b) if isinstance(x, (ast.If, ast.While, ast.IfExp))]
        if is_test and [norm(x) for x in guards_a] != [norm(x) for x in guards_b]:
            result['guard_changes'].append({'file': file, 'function': key, 'line': b.lineno, 'baseline': [ast.unparse(x) for x in guards_a], 'current': [ast.unparse(x) for x in guards_b]})
        ca, cb = consts(a), consts(b)
        if ca != cb:
            result['constant_changes' if is_test else 'fixture_helper_constant_changes'].append({'file': file, 'function': key, 'line': b.lineno, 'removed': dict(ca - cb), 'added': dict(cb - ca)})
(OUT / 'control-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
