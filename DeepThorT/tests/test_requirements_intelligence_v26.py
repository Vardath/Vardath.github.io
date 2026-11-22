"""v26 requirements and model-declared dependency planning regressions."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import PlanError
from deepthort_local.requirements_intelligence import (
    requirement_candidates,declared_dependencies,dependency_order)
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.specification_library import SpecificationIndex,sha


class CandidateTests(unittest.TestCase):
    def test_verbatim_spans_are_hash_checked_and_stable(self):
        original='Introductory text.\n- The game must have factions.\n- The stations should have managers.\n'
        rows=[(0,0,len(original),'','','')]
        a=requirement_candidates(original,rows)
        self.assertEqual(a,requirement_candidates(original,rows))
        self.assertEqual(len(a),3)
        self.assertEqual(''.join(original[r['start_char']:r['end_char']] for r in a),original)
        self.assertEqual([r['kind'] for r in a],['unstructured','explicit','explicit'])
        for item in a:
            self.assertEqual(sha(original[item['start_char']:item['end_char']]),item['sha256'])

    def test_unstructured_specification_is_not_dropped(self):
        original='An entire long free-form design without bullet points or headings.'
        items=requirement_candidates(original,[(0,0,len(original),'','','')])
        self.assertEqual(len(items),1)
        self.assertEqual(original[items[0]['start_char']:items[0]['end_char']],original)
        self.assertEqual(items[0]['kind'],'unstructured')

    def test_overflow_is_grouped_not_omitted(self):
        original=''.join(f'- Req {i}\n' for i in range(110))
        items=requirement_candidates(original,[(0,0,len(original),'','','')])
        self.assertEqual(len(items),64)
        self.assertEqual(''.join(original[i['start_char']:i['end_char']] for i in items),original)

    def test_explicit_dependency_is_used_not_inferred(self):
        steps=[{'path':'code/b.py','description':'Create UI; depends-on: code/a.py'},
               {'path':'code/a.py','description':'Create simulation engine'},
               {'path':'docs.md','description':'Might require code/b.py one day'}]
        ordered,deps=dependency_order(steps)
        self.assertEqual([x['path'] for x in ordered],['code/a.py','code/b.py','docs.md'])
        self.assertEqual(deps['code/b.py'],('code/a.py',))
        self.assertFalse(deps['docs.md'])

    def test_long_reverse_dependency_chain_is_stable_and_fast(self):
        count=1200
        steps=[{'path':f'code/{i}.py',
                'description':('Build step' if i==0 else f'Build step; depends-on: code/{i-1}.py')}
               for i in reversed(range(count))]
        ordered,dependencies=dependency_order(steps)
        self.assertEqual([x['path'] for x in ordered],
                         [f'code/{i}.py' for i in range(count)])
        self.assertEqual(len(dependencies),count)

    def test_cyclic_dependencies_fail_closed(self):
        steps=[{'path':'a.py','description':'One; depends-on: b.py'},
               {'path':'b.py','description':'Two; depends-on: a.py'}]
        with self.assertRaisesRegex(PlanError,'cycle'):
            dependency_order(steps)

    def test_missing_dependency_fails_closed(self):
        with self.assertRaisesRegex(PlanError,'unknown file'):
            declared_dependencies([{'path':'a.py','description':'Requires more; depends-on: imaginary.py'}])

    def test_self_dependency_fails_closed(self):
        with self.assertRaisesRegex(PlanError,'itself'):
            declared_dependencies([{'path':'a.py','description':'Myself; depends-on: a.py'}])


class RoadmapIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/'project';self.project.mkdir()
        self.index=SpecificationIndex(self.root/'spec.sqlite3')
        self.plans=HierarchicalPlanStore(self.root/'hierarchy.sqlite3')
        self.request_id=7
        self.original=''.join(f'Requirement section {i}:\n- Deliver subsystem {i} properly.\n'+'x'*3010+'\n' for i in range(1,4))
        self.index.index(self.request_id,self.original)

    def plan(self, steps):
        for content in steps:
            row=self.index.next_section(self.request_id,self.original)
            self.index.save_response(self.request_id,self.original,row['ordinal'],
                json.dumps({'files':[content]}),project=self.project)
        return self.plans.prepare(self.index,self.request_id,self.original,self.project,chat_id='chat')

    def test_model_prompt_teaches_only_declared_dependencies(self):
        prompt=self.index.model_prompt(self.request_id,self.original)
        self.assertIn('depends-on: relative/other.ext',prompt)
        self.assertIn('never invent dependencies',prompt)
        self.assertIn(self.original[:200],prompt)

    def test_real_roadmap_dependency_order_and_approval_unchanged(self):
        result=self.plan([
            {'path':'code/c.py','description':'Implement C; depends-on: code/b.py'},
            {'path':'code/b.py','description':'Implement B; depends-on: code/a.py'},
            {'path':'code/a.py','description':'Implement A'},
        ])
        self.assertEqual(result['milestones_total'],3)
        self.assertEqual([self.plans.milestone(self.index,7,self.original,n)['steps'][0]['path']
                          for n in range(1,4)],['code/a.py','code/b.py','code/c.py'])
        self.assertEqual(result['next_approvable'],1)
        report=self.plans.requirement_report(self.index,7,self.original)
        self.assertGreaterEqual(report['candidate_count'],3)
        self.assertEqual(report['candidate_count'],report['shown'])
        self.assertIn('NOT verified',report['trace_level'])
        self.assertEqual(len(self.plans.dependency_report(self.index,7,self.original)),2)
        new=HierarchicalPlanStore(self.root/'hierarchy.sqlite3')
        self.assertEqual(new.requirement_report(self.index,7,self.original)['requirements'],report['requirements'])

    def test_modified_source_cannot_reuse_requirements(self):
        self.plan([{'path':f'code/{i}.py','description':f'Implement {i}'} for i in range(3)])
        with self.assertRaises((PlanError,ValueError)):
            self.plans.requirement_report(self.index,7,self.original+' MODIFIED')

    def test_tampered_requirement_fingerprint_is_detected(self):
        self.plan([{'path':f'code/{i}.py','description':f'Implement {i}'} for i in range(3)])
        with sqlite3.connect(self.plans.path) as db:
            db.execute("UPDATE hierarchy_requirements SET source_sha256=? WHERE request_id=?",('bad',7))
        with self.assertRaisesRegex(PlanError,'candidate'):
            self.plans.requirement_report(self.index,7,self.original)

    def test_dependency_must_not_be_injected_in_saved_roadmap(self):
        self.plan([{'path':f'code/{i}.py','description':f'Implement {i}'} for i in range(3)])
        with sqlite3.connect(self.plans.path) as db:
            db.execute("INSERT INTO hierarchy_dependencies VALUES (?,?,?)",(7,'code/1.py','code/0.py'))
        with self.assertRaisesRegex(PlanError,'dependency graph'):
            self.plans.status(self.index,7,self.original)

    def test_legacy_v25_roadmap_with_no_candidate_rows_remains_accessible(self):
        self.plan([{'path':f'code/{i}.py','description':f'Implement {i}'} for i in range(3)])
        with sqlite3.connect(self.plans.path) as db:
            db.execute('DELETE FROM hierarchy_requirements WHERE request_id=7')
        self.assertEqual(self.plans.status(self.index,7,self.original)['milestones_total'],3)
        self.assertEqual(self.plans.requirement_report(self.index,7,self.original)['candidate_count'],0)


if __name__=='__main__':
    unittest.main()
