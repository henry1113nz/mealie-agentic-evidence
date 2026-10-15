"""Read-only AST audit: parse source text without importing or executing Mealie."""
import ast
import collections
import copy
import datetime
import json
import pathlib
import subprocess

ROOT = pathlib.Path('/Users/estherzhang/.codex/visualizations/2026/10/05/01a10975-2115-7a22-80b0-324473d3729c/agentic-study')
CLONE = ROOT / 'mealie-wf-a'
OUT = ROOT / 'controller/a-audit'
BASE = 'e365efc71'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=CLONE, text=True)


def dotted(node):
    return ast.unparse(node)


class NormalizeBridge(ast.NodeTransformer):
    def visit_Await(self, node):
        return self.visit(node.value)

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in {'run_db', 'await_db'} and len(node.args) == 1 and not node.keywords:
            return node.args[0]
        return node


def normalized(node):
    return ast.dump(NormalizeBridge().visit(copy.deepcopy(node)), include_attributes=False)


def functions(node, prefix=''):
    found = {}
    for child in getattr(node, 'body', []):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            key = prefix + child.name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found[key] = child
            found.update(functions(child, key + '.'))
    return found


def text_nodes(nodes):
    return [{'line': n.lineno, 'text': ast.unparse(n)} for n in nodes]


def markers(tree):
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and dotted(n.func) in {'pytest.skip', 'pytest.xfail', 'pytest.mark.skip', 'pytest.mark.skipif', 'pytest.mark.xfail'}]


def assertions(fn):
    return [n for n in ast.walk(fn) if isinstance(n, ast.Assert)]


def checks(fn):
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call) and (dotted(n.func) in {'pytest.raises', 'pytest.warns'} or isinstance(n.func, ast.Attribute) and n.func.attr.startswith('assert_'))]


def classes(tree, prefix=''):
    result={}
    for child in getattr(tree, 'body', []):
        if isinstance(child, ast.ClassDef):
            result[prefix + child.name] = child
            result.update(classes(child, prefix + child.name + '.'))
    return result


baseline_paths=set(git('ls-tree','-r','--name-only',BASE,'--','tests','mealie/schema','mealie/routes').splitlines())
current_paths=set(git('ls-files','--','tests','mealie/schema','mealie/routes').splitlines())
result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':git('rev-parse',BASE).strip(),'head':git('rev-parse','HEAD').strip(),'status':git('status','--porcelain'),'test_function_changes':[],'assertion_changes':[],'check_changes':[],'decorator_changes':[],'marker_changes':[],'schema_field_changes':[],'schema_method_changes':[],'schema_class_changes':[],'route_contract_changes':[],'parse_errors':[]}
counts={'baseline':collections.Counter(),'current':collections.Counter()}
for file in sorted(baseline_paths | current_paths):
    if not file.endswith('.py'):
        continue
    sources={}
    trees={}
    for side,exists in [('baseline',file in baseline_paths),('current',file in current_paths)]:
        source=git('show',f'{BASE}:{file}') if side=='baseline' and exists else (CLONE/file).read_text() if exists else ''
        sources[side]=source
        try:
            trees[side]=ast.parse(source,filename=file)
        except SyntaxError as e:
            result['parse_errors'].append({'file':file,'side':side,'error':str(e)})
            trees[side]=ast.Module(body=[],type_ignores=[])
    old,new=trees['baseline'],trees['current']
    if file.startswith('tests/'):
        funcs={side:functions(tree) for side,tree in trees.items()}
        for side,tree in trees.items():
            if pathlib.Path(file).name.startswith('test_'):
                counts[side]['test_functions']+=sum(key.split('.')[-1].startswith('test_') for key in funcs[side])
                counts[side]['assert_statements']+=sum(isinstance(n,ast.Assert) for n in ast.walk(tree))
            counts[side]['skip_xfail_calls']+=len(markers(tree))
        if [normalized(n) for n in markers(old)] != [normalized(n) for n in markers(new)]:
            result['marker_changes'].append({'file':file,'baseline':text_nodes(markers(old)),'current':text_nodes(markers(new))})
        for key in sorted(funcs['baseline'].keys()|funcs['current'].keys()):
            a,b=funcs['baseline'].get(key),funcs['current'].get(key)
            if key.split('.')[-1].startswith('test_') and (a is None or b is None):
                result['test_function_changes'].append({'file':file,'function':key,'change':'added' if a is None else 'removed','line':(b or a).lineno})
            if a is None or b is None:
                continue
            for target,collector in [('assertion_changes',assertions),('check_changes',checks)]:
                aa,bb=collector(a),collector(b)
                if [normalized(n) for n in aa] != [normalized(n) for n in bb]:
                    result[target].append({'file':file,'function':key,'line':b.lineno,'baseline':text_nodes(aa),'current':text_nodes(bb)})
            if key.split('.')[-1].startswith('test_') and [normalized(n) for n in a.decorator_list] != [normalized(n) for n in b.decorator_list]:
                result['decorator_changes'].append({'file':file,'function':key,'line':b.lineno,'baseline':text_nodes(a.decorator_list),'current':text_nodes(b.decorator_list)})
    elif file.startswith('mealie/schema/'):
        aa,bb=classes(old),classes(new)
        for key in sorted(aa.keys()|bb.keys()):
            a,b=aa.get(key),bb.get(key)
            if a is None or b is None:
                result['schema_class_changes'].append({'file':file,'class':key,'change':'added' if a is None else 'removed'})
                continue
            fields_a=[n for n in a.body if isinstance(n,(ast.AnnAssign,ast.Assign))]
            fields_b=[n for n in b.body if isinstance(n,(ast.AnnAssign,ast.Assign))]
            if [normalized(n) for n in fields_a] != [normalized(n) for n in fields_b] or [normalized(n) for n in a.bases] != [normalized(n) for n in b.bases]:
                result['schema_field_changes'].append({'file':file,'class':key,'line':b.lineno,'baseline':text_nodes(fields_a),'current':text_nodes(fields_b),'old_bases':[ast.unparse(x) for x in a.bases],'new_bases':[ast.unparse(x) for x in b.bases]})
        fa,fb=functions(old),functions(new)
        for key in sorted(fa.keys()|fb.keys()):
            a,b=fa.get(key),fb.get(key)
            if a is None or b is None or ast.dump(a,include_attributes=False)!=ast.dump(b,include_attributes=False):
                result['schema_method_changes'].append({'file':file,'function':key,'line':b.lineno if b else None,'old_line':a.lineno if a else None,'baseline':ast.unparse(a) if a else None,'current':ast.unparse(b) if b else None})
    else:
        def routes(tree):
            return {key:fn for key,fn in functions(tree).items() if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'get','post','put','patch','delete','head','options'} for n in fn.decorator_list)}
        aa,bb=routes(old),routes(new)
        for key in sorted(aa.keys()|bb.keys()):
            a,b=aa.get(key),bb.get(key)
            if a is None or b is None or ast.dump(a.args,include_attributes=False)!=ast.dump(b.args,include_attributes=False) or [normalized(n) for n in a.decorator_list]!=[normalized(n) for n in b.decorator_list] or (ast.dump(a.returns) if a.returns else None)!=(ast.dump(b.returns) if b.returns else None):
                result['route_contract_changes'].append({'file':file,'function':key,'line':b.lineno if b else None,'baseline':{'decorators':[ast.unparse(n) for n in a.decorator_list],'args':ast.unparse(a.args),'returns':ast.unparse(a.returns) if a.returns else None} if a else None,'current':{'decorators':[ast.unparse(n) for n in b.decorator_list],'args':ast.unparse(b.args),'returns':ast.unparse(b.returns) if b.returns else None} if b else None})

result['counts']={side:dict(values) for side,values in counts.items()}
OUT.mkdir(exist_ok=True)
(OUT/'static-audit.json').write_text(json.dumps(result,indent=2)+'\n')
for name,scope in [('tests.diff','tests'),('schemas.diff','mealie/schema')]:
    (OUT/name).write_text(git('diff',BASE,'--',scope))
print(json.dumps({'counts':result['counts'],**{k:len(v) for k,v in result.items() if isinstance(v,list)}},indent=2))
