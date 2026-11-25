"""Fixed adversarial retrieval cases: known target, decoys and exact citations."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.document_knowledge import DocumentKnowledge, _query_terms, _digest


class KnowledgeRetrievalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'project'
        (self.root / 'docs').mkdir(parents=True)
        self.index = DocumentKnowledge(Path(temp.name) / 'state.sqlite3')

    def enroll(self, name, content):
        path = 'docs/' + name
        (self.root / path).write_text(content, encoding='utf-8')
        self.index.index(self.root, path)
        return path

    def test_repetitive_manual_does_not_starve_second_source(self):
        self.enroll('a.md', 'Quasar renderer configuration\n' * 120)
        expected = self.enroll('z.md', 'Quasar renderer configuration uses Vulkan pipeline caches\n')
        hits = self.index.search(self.root, 'Quasar renderer configuration', limit=2)
        self.assertEqual(len(hits), 2)
        self.assertIn(expected, [x['path'] for x in hits])
        self.assertEqual(len({x['excerpt'] for x in hits}), 2)

    def test_stale_dominant_manual_does_not_starve_valid_hit(self):
        stale = self.enroll('a.md', 'Quasar renderer configuration\n' * 120)
        expected = self.enroll('z.md', 'Quasar renderer configuration requires Vulkan\n')
        (self.root / stale).write_text('Changed source; not current.')
        hits = self.index.search(self.root, 'Quasar renderer configuration')
        self.assertEqual([x['path'] for x in hits], [expected])

    def test_rare_term_ranking_beats_generic_overlap(self):
        self.enroll('a.md', 'Renderer configuration setup\n' * 120)
        expected = self.enroll('z.md', 'Quasar Vulkan renderer configuration\n')
        hits = self.index.search(self.root, 'renderer configuration setup Quasar Vulkan', limit=1)
        self.assertEqual(hits[0]['path'], expected)
        self.assertEqual(hits[0]['number'], 1)

    def test_query_order_and_adjacent_phrase(self):
        expected = self.enroll('z.md', 'Quasar Vulkan renderer configuration\n')
        self.enroll('a.md', 'Vulkan configuration Quasar renderer\n')
        self.assertEqual(self.index.search(self.root, 'Quasar Vulkan renderer configuration', limit=1)[0]['path'], expected)
        words = ['unique'+str(i) for i in range(30)]
        terms = _query_terms(' '.join(words))
        self.assertEqual(terms, [_digest(w.encode())[:24] for w in words[:24]])

    def test_forget_during_extraction_refuses_old_observation(self):
        from deepthort_local import document_knowledge as module
        path = self.enroll('a.md', 'Quasar renderer configuration\n')
        extract = module._extract
        def forget(raw, suffix):
            result = extract(raw, suffix)
            self.index.remove(self.root, path)
            return result
        with patch.object(module, '_extract', side_effect=forget):
            self.assertFalse(self.index.search(self.root, 'Quasar'))

    def test_bounded_discovery_advances_to_unseen_and_skips_forgotten(self):
        for name in ('a.md', 'b.md', 'c.md'):
            (self.root / 'docs' / name).write_text('Quasar technical reference\n'*1900)
        with patch('deepthort_local.document_knowledge.MAX_AUTO', 1):
            self.index.refresh(self.root)
            self.assertEqual(len(self.index.documents(self.root)), 1)
            self.index.refresh(self.root)
            self.assertEqual(len(self.index.documents(self.root)), 2)
            self.index.remove(self.root, 'docs/a.md')
            self.index.refresh(self.root)
        self.assertEqual({r['path'] for r in self.index.documents(self.root)}, {'docs/b.md','docs/c.md'})

    def test_excluded_document_not_a_ranking_candidate(self):
        first = self.enroll('a.md', 'Quasar Vulkan configuration\n')
        second = self.enroll('b.md', 'Quasar renderer notes\n')
        hits = self.index.search(self.root, 'Quasar Vulkan configuration', exclude=[first])
        self.assertEqual([x['path'] for x in hits], [second])
