"""Prevent evaluation against silently substituted dialogue splits or tokenizers."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from capability.modern_train import verify_evaluation_corpus


class EvaluationBindingTests(unittest.TestCase):
    def test_rejects_changed_training_validation_and_tokenizer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            train = corpus / "train.jsonl"
            validation = corpus / "validation.jsonl"
            test = corpus / "test.jsonl"
            tokenizer = root / "tokenizer.json"
            for path, payload in ((train, b"train"), (validation, b"validation"), (test, b"test"), (tokenizer, b"tokenizer")):
                path.write_bytes(payload)
            immutable = {
                "corpus_hash": hashlib.sha256(train.read_bytes()).hexdigest(),
                "validation_hash": hashlib.sha256(validation.read_bytes()).hexdigest(),
                "test_hash": hashlib.sha256(test.read_bytes()).hexdigest(),
                "tokenizer_hash": hashlib.sha256(tokenizer.read_bytes()).hexdigest(),
            }
            verify_evaluation_corpus(immutable, corpus, tokenizer)
            for changed in (train, validation, test, tokenizer):
                original = changed.read_bytes()
                changed.write_bytes(original + b"tampered")
                with self.subTest(changed=changed.name), self.assertRaisesRegex(ValueError, "Evaluation input mismatch"):
                    verify_evaluation_corpus(immutable, corpus, tokenizer)
                changed.write_bytes(original)

    def test_missing_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "train.jsonl").write_text("train")
            (root / "validation.jsonl").write_text("validation")
            (root / "test.jsonl").write_text("test")
            tokenizer = root / "tokenizer.json"
            tokenizer.write_text("tokenizer")
            with self.assertRaisesRegex(ValueError, "Evaluation input mismatch"):
                verify_evaluation_corpus({}, root, tokenizer)


if __name__ == "__main__":
    unittest.main()
