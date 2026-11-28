# DeepThorTriad — Interface Redesign Progress

Register: [INTERFACE_REDESIGN_REGISTER.md](INTERFACE_REDESIGN_REGISTER.md). Baseline main `3688f6094872050f5ad3c010ac88e091ea1c8c43`, previous missing-ability programme pass 279 merged. Baseline main workflow [46093350764](https://github.com/Vardath/Vardath.github.io/actions/runs/46093350764) was in progress during inspection. Do not merge until predecessor and exact candidate checks are green.

## Ledger
| ID | Status | Evidence |
|---|---|---|
| UI-001 | Partial, candidate | Shared Nordic palette, angular serpent mark, correct visible application name, consistent selection and entry colours. Header/navigation reflow still required. |
| UI-010 | Partial, candidate | Existing media production rows housed in searchable two-axis scroll shelf, compact preview; original labels and callbacks retained. Full categorisation/preview redesign pending. |
| UI-002–009, UI-011–018 | Pending | Screen source inventory recorded in register; further implementation and native acceptance required. |

## Pass 001 — 28 November 2026
Inspected desktop_app.py main UI construction (eight fixed notebook tabs, project sidebar, global controls, and inline dialogs), tooltips, current layout regression, and production row structure. Files & Images has over 40 action rows; normal-height windows cannot accommodate this layout. Added UI-only lattice_ui.py and integrated it without changing tab indices, tool callback bindings, approval rules, model/runtime or persisted state. Added GUI regression for searchable tool access and empty/restored queries. Candidate CI pending; no native Windows visual acceptance or installer. Next: chat-first shell/navigation, compact global controls and queue/workspace visibility. Complete per-dialog inventory and high-DPI inspection remain outstanding.

### Pass 001 CI registration
The inherited workflow did not run test_layout_v12.py. Add an isolated native Tk shelf test to both CI jobs (Xvfb on Linux, Tk on Windows) to verify search, restoration, exact callback identity, horizontal scrolling and the mark without launching inference. Full desktop integration regression is retained for native acceptance; both candidate and predecessor CI remain pending until checked.

### Pass 001 correction — 28 November
Both Linux and Windows candidate jobs failed the new shelf test because the helper `_options` shadowed Tkinter's internal widget configuration method. Rename the helper to `_pack_options` and retain its original geometry-option extraction behavior. No change to commands or permissions. [Failed run](https://github.com/Vardath/Vardath.github.io/actions/runs/46094122618); corrected candidate requires fresh green checks.


## Pass 002 — 28 November 2026 — stacked candidate, not merged
UI-001/UI-002/UI-003 partial extension: keep Start/Stop AI and guide visible, consolidate maintenance and specialist project controls in labelled menus; keep chat, task approval, cancellation and JANUS actions on the primary workspace. Add native transcript/composer scrollbars, default compact composer and opt-in expansion without loss of unsent text. Keep the exact existing conversation notebook/identity and project file tree; archive reopening is accessible from the conversation menu. Add menu and resize interaction regressions to the previously registered Tk test, and update desktop layout expectation. No authorization, state, scheduler, model or resource changes. Pass 001's corrected Tk step was green on both Linux and Windows in [run 46094270091](https://github.com/Vardath/Vardath.github.io/actions/runs/46094270091), full predecessor checks still running at preparation. This stacked candidate must not merge before pass 001 and its exact candidate are green. Searchable conversation navigation, project switcher and full desktop/DPI acceptance remain outstanding.


## Pass 003 — 28 November 2026 — stacked candidate
UI-002/UI-003: add searchable conversation and recent workspace pickers using the existing chat registry and exact stored identities; no implicit chat selection or model invocation. A recent workspace is opened only explicitly, after availability checking and resolution of unsent material. Add path filtering over existing file inventory and verified X4 references (no extra scan), native file-tree scrollbar, and correct assistant transcript branding. Retain original notebook indices, project selection callback and review boundaries. Add duplicate-title, no-auto-open, path-filter and recent identity regressions to both existing GUI CI jobs. Pass 002's new GUI tests passed on both systems in [run 46094647824](https://github.com/Vardath/Vardath.github.io/actions/runs/46094647824); full earlier CI still running at preparation. No merge before exact predecessors green. Recent list is based on last created chat per workspace, not a separate visit-history store. Full native desktop verification outstanding.


## Pass 004 — 28 November 2026
UI-004/UI-006 partial: reorganised work queue into project priorities, scheduling, reviewed backup/checkpoint and development/testing menus; retained direct cancellation, resume and stop controls. Add display-only state/text filters, visible/total counts, native scrollbars and exact-ID table refresh preserving selection only when still visible. Existing graph/dependency and journal evidence retained. Manual task board receives its own filters and counts. No scheduler, permission or task-state mutation introduced. Group labels are display-only; All states retains every row. Added native GUI regression. Passes 001, 002, 003 full candidate CI green (46094270091, 46094647824, 46094764349); pass 001 merged via PR 349. Pass 002 PR 350 opened; pass 003/004 remain dependent. Native desktop acceptance and structured milestone linkage outstanding.


## Pass 005 — 28 November 2026
UI-005 partial: distinct read-only source inspection and editable pending proposal mode, two-axis scrolling, text find and numbered-line navigation, inspection-only exact diff with source/candidate SHA-256, coloured diff evidence, themed direct editor, explicit saved-but-not-tested state. Comparison cannot approve a write. Existing exact review, snapshot, syntax, stale-source checks and backed-up save path preserved. Workspace switch clears previous preview and proposal. Native GUI regression covers read-only navigation and exact diff rendering. Pass 004 full candidate CI green (46097637301); pass 002 merged via PR 350 after full baseline/PR checks; pass 003 PR 351 open. Full application visual acceptance, artifact metadata/line gutter and broader dialog review outstanding.


## Pass 006 — 28 November 2026
UI-007 partial: measured PID/resource table with distinct CPU, resident and private commit metrics, observed timestamp and unavailable state; separate scrollable process details and actual desktop activity log; searchable log navigation and optional follow-latest; compact diagnostic menu with direct cancellation and stop retained. Removed obsolete three-model denominator from process report. Reuses existing 2.2-second sample and existing durable log path; no new polling, inferred token progress or aggregate claims. GUI regressions test exact sample mapping and read-only refresh. Pass 005 new GUI checks green on Linux and Windows (46099068125); comprehensive checks and PR 351 merge gate still running at preparation. Individual five-operative and resource cap acceptance, full desktop testing and accessibility remain outstanding.


## Pass 007 — 28 November 2026
UI-008 partial: operative screen split into five-worker observation, two recursive societies, approved processes and independent interface messages. Broker PID identity gates neural readiness; distinguish Gemma's observed creative-lane activity from model residency. Add interactive 11-core topology for each society based on actual CORE_NAMES and both-hemisphere architecture; selected core displays exact recorded appraisal including internal faculties, not invented thought or live message traffic. Preserve existing raw inspector, goals, pause/resume, action cancellation and acknowledgements. Stable action selection and scrollable status/messages. Existing process tick and society refresh reused, no new inference or polling. Tests cover stale broker, Gemma PID distinction and independent core records. Pass 006 GUI regression green on both systems (46099373748); full CI and predecessor PR gate pending at preparation. Assignment-level attribution and native visual acceptance outstanding.
