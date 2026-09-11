# WNG — refresh memory and continue

Read this before touching the WNG 1.6 repository after any context reset.

# ⛔ THE BROAD HISTORY RECOVERY AND PUBLIC RECONCILIATION HAVE ALREADY BEEN DONE

Historical/design reconstruction: **`CANONICAL_RECOVERY_LEDGER.md`**.  
Completed public-vs-plan/private reconciliation: **`PUBLIC_RECONCILIATION_2026-09-11.md`**.  
Mutable implementation state: **`CURRENT_PUBLIC_STATE.md`**.

Do not make Vardath reconstruct the project again. Do not reread weeks of raw chat by default. Use raw history only for a genuine ledger/reconciliation gap, current-repo contradiction, or explicit Vardath request.

## Identity and authority

- Mod: **Wraith & Nanite Gravtech (WNG)** for RimWorld 1.6.
- Author/final design authority: **Vardath**.
- Active code: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable continuity: public `Vardath/Vardath.github.io/wng-rebuild/`.
- Old/private builds are reference evidence only.
- There are **no known-good historical WNG builds**.

## Mandatory recovery order

1. Read `STANDING_RULES.md`.
2. Read **all of `CANONICAL_RECOVERY_LEDGER.md`** for recovered history/design.
3. Read **all of `PUBLIC_RECONCILIATION_2026-09-11.md`**.
4. Read **all of `CURRENT_PUBLIC_STATE.md`**.
5. Read `WNG_IMPLEMENTATION_CHECKLIST.md`.
6. Fetch current public mod `main`; compare it to the maintained HEAD.
7. Inspect any newer real commits/files before relying on old state.
8. Read the active subsystem contract/master-plan append(s).
9. Read `PLAN_EXECUTION_PROTOCOL.md`.
10. Continue implementation; do not stop at a summary when Vardath asked to continue.
11. Update live state/reconciliation before handoff.

Mandatory working order:

**CANONICAL HISTORY -> PUBLIC RECONCILIATION -> CURRENT PUBLIC STATE -> STARGATE LORE -> CURRENT REPO -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE HANDOFF**

## Current live public snapshot

Current mod HEAD:

**`0e5dfc893a8efec624053e677ae99d6983c25fc9` — `cleanup: remove temporary Neural Lattice validation workflow`**

The canonical ledger's `4af4f60...` implementation snapshot is 45 public commits behind. It is historical only.

### Hard state rule

**Public source is implementation truth.**

Never claim work exists because:
- it was discussed;
- a checkpoint said it was done;
- work was prepared against the private repository;
- an old branch contains it;
- a previous assistant believed it committed.

If public `main` does not contain an equivalent real implementation, it is not currently implemented.

### Major implemented foundations

- block Replicator hierarchy/specialists/matter/EMP/containment/Child's Toy;
- Armor/Ranged/Power/Shield adaptation effects, with Grav/broader AntiShield refinements still outstanding;
- exact Queen vault/release/first recovery/capture boundary;
- exact Queen sovereignty;
- physical Sovereign Neural Lattice;
- human-form nanite physiology/Nanite Reserve and hostile Asuran Lattice foundation;
- Wraith identity/biology/factions/strategic hunger/mature-Hive/captivity/living-tech foundations;
- native craft mechanical stacks including **Al'kesh**;
- Wraith/Asuran gravship mechanical families;
- transport rings and Wraith stunner;
- Ha'tak/Death Glider/carrier/orbital foundations.

### Do not mistake these for complete subsystems

Important current gaps include:
- Temporary Asuran intrusion;
- recurring Queen recovery/captured-Queen mixed sovereign threats;
- Neural Interface copies/reconstruction;
- infiltration;
- Quiet Lattice/player human-form variants/mixed human-form roles;
- native WNG backstories;
- richer Grav/broader AntiShield integration;
- Wraith Growth Chamber;
- strategic hunger involved-Wraith count/names UI stage;
- broader discovery/story progression;
- friendly Quiet-Lattice/Puddle-Jumper courier path;
- standalone Goa'uld ship resource/research path without ONAC;
- Puddle Jumper final power/fuel abstraction;
- themed gravship hull corner/diagonal presentation;
- final professional art/audio;
- broad live RimWorld/save-load/mod-stack testing.

The complete debt list is in `PUBLIC_RECONCILIATION_2026-09-11.md`.

## Genuine immediate controller slice

**Temporary Asuran lattice intrusion** remains a valid immediate implementation slice.

It must:
- use `ReplicatorControlAuthority.TemporaryAsuran`;
- remain temporary;
- snapshot and restore exact pre-intrusion Queen/Neural-Lattice/autonomous authority/faction/domain state;
- keep EMP/containment real;
- keep trigger/range/duration/cap tunable;
- preserve coherent temporary/restoration state through hierarchy transactions;
- never grant ordinary Asurans permanent Queen sovereignty.

The existing generic timeout release is not itself the finished restoration mechanic.

After that, derive the next work from actual public `main` plus the **entire** reconciliation debt list, not from a single stale “next” sentence.

## Critical standing reminders

- WNG is a Stargate mod; lore/function check precedes implementation.
- `next`, `unfinished`, `correct`, `rebuild` or `refine` never means delete required existing content.
- Ordinary Wraith feeding, strategic faction hunger, mature-Hive feeding ecology and mature-Hive retaliation are separate.
- Use **Wraith Grav Engine**, not Gravcore.
- Wraith gravship defense currently uses living-hull regeneration; generic shield reskin was rejected.
- Do not invent Goa'uld fuel/resources to solve integration inconvenience.
- CatCraft owns its Stargate network/dial/iris/receive buffer.
- No replacement/generated art unless Vardath explicitly requests it.
- Planned Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty content remains planned until Vardath advances it.

## Handoff maintenance

Before ending a meaningful batch, record:
- exact new public HEAD;
- what actually changed;
- implemented / partial / unfinished / changed-rejected / planned-only / live-test-needed status;
- superseded decisions;
- next genuine slice derived from current public source plus the full debt inventory.

The objective is that Vardath can say **“refresh memory and continue”** and work resumes without interrogation or reconstruction.
