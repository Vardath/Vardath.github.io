# DeepThorT v48 verification (23 November 2026)

Focused scripted-model regressions:

- Reproduces the old instant failure after all indexed X4 sections are reviewed and mandatory X4 coverage is still absent. Confirms that retry now performs a real model correction call, saves the generated XML-file intentions and creates a validated roadmap without queueing execution.
- Confirms unfinished corrections persist in SQLite and a later retry uses a new call identity rather than replaying the same failed answer.
- Confirms malformed JSON, path traversal, Python app stages in X4, and changed specification hashes are rejected.
- Confirms exact original indexed source section text is carried unmodified into the correction context.
- Existing hierarchical, large-specification, legacy recovery and GUI workflow regressions pass under Xvfb.

Full GitHub Actions isolated-module regression and archive-integrity results are published with the release commit. Native Windows resource, model quality and X4 playtest acceptance still require the user's PC.
