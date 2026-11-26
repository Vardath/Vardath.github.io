import tempfile
import unittest
from pathlib import Path

from deepthort_local.chat_capabilities import chat_context


class ChatCapabilityTests(unittest.TestCase):
    def test_self_review_without_workspace_reads_real_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "desktop_app.py").write_text(
                "def _governed_memory():\n    return 'actual evidence'\n",
                encoding="utf-8")
            request = "Look online at chat models, look at your own code and fill any gaps"
            prompt, tokens, route, count = chat_context(
                request, request, root, project="(general)", model_ready=True)
            self.assertEqual(route, "self_review")
            self.assertEqual(tokens, 640)
            self.assertEqual(count, 1)
            self.assertTrue(prompt.startswith(request))
            self.assertIn("return 'actual evidence'", prompt)
            self.assertIn("desktop_app.py sha256=", prompt)
            self.assertIn("General web research is not dispatched", prompt)
            self.assertIn("no modifications made", prompt)

    def test_simple_chat_and_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            prompt, tokens, route, count = chat_context(
                "Hello", "Hello", root, project="(general)")
            self.assertEqual(route, "conversation")
            self.assertEqual(tokens, 256)
            self.assertEqual(count, 0)
            self.assertIn("DeepThorT Triad", prompt)
            original = "x" * 7490
            prompt, _, _, _ = chat_context(original, "inspect your code", root,
                                            project="(general)")
            self.assertEqual(prompt, original)

    def test_unrelated_state_not_inspected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "state").mkdir()
            (root / "state" / "secret.txt").write_text("DO NOT EXPOSE THIS")
            prompt, _, route, count = chat_context(
                "Inspect your code", "Inspect your code", root,
                project="(general)")
            self.assertEqual(route, "self_review")
            self.assertEqual(count, 0)
            self.assertNotIn("DO NOT EXPOSE THIS", prompt)

    def test_action_and_detected_tool_are_not_execution_claims(self):
        with tempfile.TemporaryDirectory() as folder:
            prompt, tokens, route, _ = chat_context(
                "Create a game", "Create a game", Path(folder), project="selected",
                inventory={"tools": [{"name": "Godot", "found": True},
                                     {"name": "missing", "found": False}]})
            self.assertEqual((tokens, route), (512, "action"))
            self.assertIn("Previously detected tools (not tested now): Godot", prompt)
            self.assertNotIn("missing", prompt)
            self.assertIn("do not claim it has started", prompt)


if __name__ == "__main__":
    unittest.main()
