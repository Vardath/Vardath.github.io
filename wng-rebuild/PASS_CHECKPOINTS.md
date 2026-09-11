# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Strategic Wraith hunger two-stage UI promoted to public

## Public state

Public mod `main` is now:

**`ff4f8dcb7b8ba17760a48a54f616466642189b0c` — `rebuild: complete strategic Wraith feeding request UI`**

Promotion used clean validated tree `f2c5a161a65fa0879a4980d29eadf21d7c9ed492` with parent `e1a080c...`. Temporary workflow/helper history did not enter public `main`.

Public diff is exactly:
- `Source/WNG/Wraith/WraithFactionHunger.cs` — strategic request flow modified;
- `Source/WNG/Wraith/WraithFeedingRequestDialog.cs` — paused subject dialog added.

## Public behavior now

- genuine strategic faction hunger remains the only feeding-request source;
- stage 1 is force-paused and presents eligible prisoner/feeding-stock subjects only;
- no Wraith selection exists in stage 1;
- stage 1 Submit keeps the request lock active and advances to stage 2;
- stage 2 is force-paused and displays selected subject plus exact involved-Wraith count and names;
- involved Wraith identities are real same-faction pawns: physically present Wraiths when available, otherwise the exact living faction leader;
- presentation-only Wraith pawns/names are never generated;
- final Submit uses the existing strategic acceptance effect; Cancel/Escape uses the existing refusal/raid consequence;
- no changes were made to ordinary Drain Life, Mature-Hive feeding ecology, Dormancy Vault, Growth Chamber or retaliation.

## Validation

Run **`34613728004` — SUCCESS**:
- Release C# build passed;
- all Def/Patch XML parsed;
- two-stage force-pause/request-lock/count-name invariants passed;
- old `FloatMenu` prisoner stage removed;
- fake Wraith identity generation explicitly rejected;
- subsystem-boundary invariants passed;
- temporary validation files removed before promoted tree.

Validation used the corrected small-helper/minimal-workflow method. This remains **source/Def validation, not live RimWorld validation**.

`CURRENT_PUBLIC_STATE.md` now records exact public HEAD `ff4f8dcb...` and removes strategic-hunger count/names UI from missing-required debt.

## Exact next pass

**Broader discovery/story progression reconciliation only.**

1. inventory current public WNG incidents, site parts, world discoveries, research gates and acquisition routes;
2. compare current reachability against `mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery`;
3. distinguish retained requirements from old site-name/reference ideas;
4. preserve rejection of fixed day-20-to-day-84 gating and keep major systems reachable in shorter campaigns;
5. do not dump all research/content at start and do not fire every eligible incident at once;
6. identify the smallest missing progression bridge that connects existing public mechanics;
7. checkpoint that exact bridge before code.

---

# PUBLIC MILESTONES

- `26680fe84...` — Temporary Asuran lattice intrusion.
- `9ce7137045...` — recurring exact-map Queen recovery.
- `0b8150f3ff...` — captured-Queen sovereign consequences.
- `8495b846c7...` — Neural Interface / exact reconstruction.
- `c7a9b46a3b...` — infiltration conceal/reveal.
- `87da0e5243...` — covert visitor impersonation.
- `b242dc72d1...` — Quiet Lattice society.
- `45e62cd7f5...` — native WNG backstories.
- `12590e8ea8...` — physical Replicator Grav adaptation.
- `b5cde48e3c...` — native energy-shield AntiShield integration.
- `e1a080c938...` — bounded Wraith Growth Chamber.
- `ff4f8dcb7b...` — paused two-stage strategic Wraith feeding-request UI.

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
