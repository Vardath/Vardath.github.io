# DeepThorT v55 — local regression evidence (23 November 2026)

Using exactly the DeepThorT v54 user-installable source-overlay baseline, changed JANUS/Sentinel structured-reply recovery and honest instruction-handoff acceptance status were tested by isolated Python `unittest` modules under Xvfb.

**Result: 662 tests, 81 modules, zero failures.** All modules were run in separate processes. New tests cover strict/fenced JSON, JANUS and Sentinel bounded format-repair prompts, persistent failed/staged/reviewed/delivered inbox states, and omission of original user instructions and error text from the redacted acceptance report. The prior v53 GUI test was updated: a database with no user instructions is *inconclusive*, not proof of successful handoff. The v54 seven-probe JANUS core health tests remain intact.

Both unchanged ONNX JavaScript programs pass `node --check` and preserve their expected v53 SHA-256 fingerprints. No Windows runtime model was run in this Linux environment. The supplied Windows diagnostics showed a previous failed JSON council response; the new recovery behaviour has been verified with scripted model responses only. The nine Xenon PE planning requirements remain unresolved; no game builds or live game playtests are claimed.

This is a locally tested source overlay, **not a GitHub Actions-verified commit**. The real Windows v55 one-click acceptance test remains necessary.
