# JANUS — Missing Ability Progress

Register: [MISSING_ABILITY_REGISTER.md](MISSING_ABILITY_REGISTER.md). Start baseline: V72, green source/native-Windows CI [45897512810](https://github.com/Vardath/Vardath.github.io/actions/runs/45897512810). All 210 original IDs remain unchanged.

Owner requested implementation beginning at the ease-ranked register. Preserve original five model roles, recursive JANUS/Sentinel, resource limits and approval/evidence mechanisms. A source implementation, CI pass and native on-PC acceptance are separate milestones. No intermediate installer requested.

| Ease rank | Original ID | Capability | Source status | Acceptance / remaining scope |
|---:|---:|---|---|---|
| 1 | 45 | Git commit management | Implemented, bounded | Staged-tree and explicit selected-file commits through existing approved action queue. Pass 001 Linux green; Windows and Pass 002 CI pending. Initial/unborn and merge commits, autonomous job integration and native desktop acceptance outstanding. |
| 2 | 46 | Git branch management | Partial — listing and creation | Exact local branch inventory and create-only CAS ref update through reviewed action queue. Switching, rename and safe deletion not implemented; native acceptance pending. |
| 3–210 | — | Remaining register entries | Not started in this programme | Inspect current source before each implementation. |

## Pass 001 — 27 November 2026

- Existing Git status was already exposed; added reviewed staged commits rather than duplicating status or creating a new dispatcher.
- Snapshot exact repository root, checked-out branch, HEAD, index tree and bounded full diff. Explicit user approval binds message and snapshot; queued operations expire and recheck exact scope before creating the commit and compare-and-swap updating the local ref. No working-tree writes, implicit staging, remote publication, hooks or destructive operations.
- Fixed regression fixtures use actual temporary Git repositories; verify staged/unstaged separation, stale approval, detached HEAD, subdirectory and expiry refusal. Desktop GUI and actual JANUS execution on owner PC remain unverified.
- Limitations: requires Git, configured author identity, existing local branch/parent commit and user-staged changes. Ordinary trusted local Git process, not a security sandbox; external concurrent Git processes must not be used during the reviewed operation. No autonomous authority expansion.
- Next register entry: rank 2 / ID 46, Git branch management; first verify this pass's CI and repair any demonstrated defect. Rank 1 remains partial until staging/workflow integration is complete.

## Pass 002 — 27 November 2026

- Pass 001 Linux CI passed, including actual Git repository fixtures ([run 45899945770](https://github.com/Vardath/Vardath.github.io/actions/runs/45899945770)); Windows still running at implementation time.
- Selected-file commits: construct a proposed tree with a private temporary Git index, display exact diff, require explicit approval, reject pre-existing staged changes or changed selected files. Stage only approved paths, recheck resulting tree, then commit via original exact-tree path. Reject hidden/protected paths, links, oversized files, and unselected changes. Failed staging or concurrent edits can leave staged changes; inspect index rather than reset user work. Trusted local repo only, not security isolation.
- Branch listing and creation: observe bounded local refs and exact current HEAD, approve a named new branch, compare-and-swap create without checkout or overwrite. No remote operations. Switching, rename and deletion remain future scoped operations.
- Added four real Git fixture regressions. Pass 002 CI pending; native desktop review and model-driven workflow use remain unverified.
- Next: verify both passes green, finish safe local branch operations, proceed to rank 3 worktree management. No installer.
