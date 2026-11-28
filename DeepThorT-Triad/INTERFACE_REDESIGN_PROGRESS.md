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
