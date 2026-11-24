# v49 validation and acceptance

**Prerelease checks:** v48 indexed repair regressions, v49 new productive planning/stall/SQLite tests, source compile, Xvfb GUI integration, and source SHA-256 checks. Full isolated GitHub Actions regression must pass before distribution. Use only main-branch `DeepThorT-v49-source-overlay` artifact after a successful CI run.

Acceptance cases: successful 40-call review-batch rollover only after a reviewed section; one-call correction-batch rollover only after real acceptance coverage improvement; no rollover for stagnant calls; eight consecutive zero-gain X4 corrections pause safely; exact original source included in correction prompt; do not re-open satisfied criteria by appending new assets without their registration; durable outcome audit survives SQLite reconnect; user cancellation and model failures do not approve or write files. The release still requires native Windows+actual ONNX model quality acceptance.
