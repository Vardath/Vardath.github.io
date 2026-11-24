import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.document_knowledge import DocumentKnowledge, discover_documents
from deepthort_local.knowledge_dialog import selected_relative
from deepthort_local.capability_library import CapabilityLibrary


class KnowledgeManagementTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name) / 'project'
        (self.root / 'docs').mkdir(parents=True)
        self.index = DocumentKnowledge(Path(t.name) / 'state.sqlite3')

    def test_discovery_above_preview_limit(self):
        p = self.root / 'docs/manual.md'
        p.write_text(('Background text ' + 'x'*80 + '\n') * 1950 +
                     'Quasar Vulkan reference\n', encoding='utf-8')
        self.assertGreater(p.stat().st_size, 180000)
        stats = self.index.refresh(self.root)
        self.assertEqual(stats['indexed'], 1)
        self.assertTrue(self.index.search(self.root, 'Quasar Vulkan'))

    def test_partial_scan_preserves_unseen_auto_docs(self):
        path = self.root / 'docs/manual.md'
        path.write_text('Quasar technical reference\n'*1900)
        self.index.index(self.root, 'docs/manual.md', origin='auto')
        self.index.refresh(self.root, [])
        self.assertTrue(self.index.search(self.root, 'Quasar'))
        path.unlink()
        self.index.refresh(self.root, [])
        self.assertFalse(self.index.documents(self.root))

    def test_project_quota_preserves_previous_index(self):
        for name in ('a.md', 'b.md'):
            (self.root / 'docs' / name).write_text('Quasar Vulkan technical reference\n')
        self.index.index(self.root, 'docs/a.md')
        with patch('deepthort_local.document_knowledge.MAX_PROJECT_POSTINGS', 4):
            with self.assertRaisesRegex(ValueError, 'quota'):
                self.index.index(self.root, 'docs/b.md')
        self.assertEqual(len(self.index.documents(self.root)), 1)
        self.assertTrue(self.index.search(self.root, 'Quasar'))

    def test_cancelled_index_leaves_no_partial_rows(self):
        (self.root / 'docs/a.md').write_text('Quasar Vulkan technical reference\n')
        calls = iter((False, False, True))
        with self.assertRaisesRegex(ValueError, 'cancelled'):
            self.index.index(self.root, 'docs/a.md', cancelled=lambda: next(calls))
        self.assertFalse(self.index.documents(self.root))

    def test_selection_exclusions_and_outside_scope(self):
        path = self.root / 'docs/a.md'
        self.assertEqual(selected_relative(self.root, path), 'docs/a.md')
        with self.assertRaises(ValueError):
            selected_relative(self.root, path, ['docs/a.md'])
        with self.assertRaises(ValueError):
            selected_relative(self.root, self.root.parent / 'outside.pdf')

    def test_bounded_discovery_and_secret_folders(self):
        (self.root / 'docs/manual.md').write_text('Quasar technical reference\n'*1900)
        (self.root / 'secrets').mkdir()
        (self.root / 'secrets/manual.md').write_text('Quasar technical reference\n'*1900)
        paths, bounded = discover_documents(self.root)
        self.assertEqual(paths, ['docs/manual.md'])
        self.assertFalse(bounded)
        with patch('deepthort_local.document_knowledge.MAX_DISCOVERY_ENTRIES', 1):
            self.assertTrue(discover_documents(self.root)[1])
