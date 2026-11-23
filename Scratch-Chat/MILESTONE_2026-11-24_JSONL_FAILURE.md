# Scratch Chat milestone — 2026-11-24 JSONL smoke failure diagnosis

Verified Actions run 45257993758: original-dialogue-smoke FAILED at "Exercise real DeepThorT multi-turn JSON-line transport and recovery". Corpus build, tokenizer, random-initialized 80-step dialogue training and held-out task-family evaluation steps succeeded. Independent acceptance and artifact upload were skipped, so no conversational-quality result can be inferred. Source-test run 45258019585 succeeded.

Inspection of the workflow found its inline Python payload constructed lines with the literal two-character backslash-n sequence (`"\\\\n"` in the YAML's Python source), rather than newline delimiters (`"\\n"` in Python source). This can concatenate JSON objects into an invalid JSONL stream. Commit 2e26a9b corrects all three delimiters to Python newline escapes. Commit 12882c3 additionally makes artifact upload unconditional with `if: always()`, so failed experiments retain available diagnostics.

The workflow push itself is the bounded follow-on experiment; its result must be checked before claiming repair. Root cause is a code-level diagnosis, not confirmed without rerun logs. Do not classify protocol smoke success as semantic multi-turn or tool-use success.

Next: verify the follow-on workflow, inspect failure logs/artifacts if still red, acquire substantially larger verified-license dialogue corpora, audit decontaminated splits, train original weights on that corpus, independently grade multi-turn/tool-use behavior, and test the actual DeepThorT host. GitHub CPU is for pilot tests only. No Shakespeare-only training or pretrained-weight substitution.
