# WNG — refresh memory and continue

Read this before touching the WNG 1.6 repository after any context reset.

# ⛔ THE BROAD HISTORY RECOVERY HAS ALREADY BEEN DONE

Historical reconstruction: **`CANONICAL_RECOVERY_LEDGER.md`**.  
Mutable implementation state: **`CURRENT_PUBLIC_STATE.md`**.

Do not make Vardath reconstruct the project again. Do not reread weeks of raw chat by default. Use raw history only for a genuine ledger gap/conflict, a current-repo contradiction, or an explicit Vardath request.

## Identity and authority

- Mod: **Wraith & Nanite Gravtech (WNG)** for RimWorld 1.6.
- Author/final design authority: **Vardath**.
- Active code: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable continuity: public `Vardath/Vardath.github.io/wng-rebuild/`.
- Old/private builds are reference evidence only.
- There are **no known-good historical WNG builds**.

## Mandatory recovery order

1. Read `STANDING_RULES.md`.
2. Read **all of `CANONICAL_RECOVERY_LEDGER.md`**.
3. Read **all of `CURRENT_PUBLIC_STATE.md`**.
4. Read `WNG_IMPLEMENTATION_CHECKLIST.md`.
5. Fetch current public mod `main`; compare it to `CURRENT_PUBLIC_STATE.md`.
6. Inspect any newer real commits/files before relying on old state.
7. Read the active subsystem contract/master-plan append(s).
8. Read `PLAN_EXECUTION_PROTOCOL.md`.
9. Continue implementation; do not stop at a summary.
10. Update `CURRENT_PUBLIC_STATE.md` before handoff.

Mandatory working order:

**CANONICAL LEDGER -> CURRENT PUBLIC STATE -> STARGATE LORE -> CURRENT REPO -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE HANDOFF**

## Current live public snapshot

Current mod HEAD:

**`0e5dfc893a8efec624053e677ae99d6983c25fc9` — `cleanup: remove temporary Neural Lattice validation workflow`**

The ledger's `4af4f60...` is an old reconstruction checkpoint only.

### Critical current state

- Full block hierarchy/specialists/adaptations/matter/EMP/containment foundations exist.
- Exact Queen vault/release/first recovery/capture boundary exists.
- Exact Queen sovereignty exists as genuine per-block controller/faction state.
- **Sovereign Neural Lattice implant now exists** as a physical craftable Asuran-workshop item with native brain installation/removal and real bounded `NeuralLattice` controller-domain ownership.
- Queen and implant authority remain separate identities; ordinary Asurans do not gain innate Queen authority.
- Neural Lattice current first-build acquisition tuning is 24 cells / normal cap 3; EMP disruption is 1,800 ticks; no nearby-swarm seizure.
- Removing the implant releases that exact bearer's implant-controlled blocks; invalid physical state also releases authority.
- Split/recombine preserves exact controller domains and does not cross-contaminate Queen/implant domains.
- Block stored matter remains separate from human-form Nanite Reserve.
- Human-form Nanite Reserve is the renamed native food need; ordinary edible matter refuels it.
- Wraith subsystem, native craft stack, gravship families, Ha'tak/Death-Glider/carrier/orbital layers remain implemented; **Al'kesh stays**.
- Hostile Ha'tak takeoff remains blocked by Odyssey's player-oriented `Current.Game.Gravship` singleton; never fake it with deletion/proxy replacement.
- All five official DLCs are hard WNG dependencies: Royalty, Ideology, Biotech, Anomaly, Odyssey.
- CatCraft/ONAC/RimGate remain optional external ownership boundaries.

Validation:
- Queen sovereignty run **34576583840** passed.
- Neural Lattice corrected run **34580647197** passed C# build, all Def/Patch XML parsing and physical implant/surgery/domain invariants after an earlier candidate compile defect was fixed.
- temporary workflows removed.
- **This does not equal live RimWorld validation.**

## Genuine next implementation slice

**Temporary Asuran lattice intrusion.**

It must:
- use `ReplicatorControlAuthority.TemporaryAsuran`;
- remain a temporary hijack, not Queen or implant ownership;
- preserve enough exact pre-intrusion authority/faction/domain state to restore Queen/Neural-Lattice/autonomous ownership correctly on expiry/interruption;
- keep EMP/containment real;
- keep duration/range/cap/trigger rules author-tunable;
- preserve coherent state through any hierarchy transactions during the intrusion;
- never grant ordinary Asurans permanent Queen sovereignty.

After that, derive the next work from actual current `main` plus the plans.

## Critical standing reminders

- WNG is a Stargate mod; lore/function check precedes implementation.
- `next`, `unfinished`, `correct`, `rebuild`, or `refine` never means delete required existing content.
- Ordinary Wraith feeding, strategic faction hunger, Mature-Hive feeding ecology and Mature-Hive retaliation are separate.
- Use **Wraith Grav Engine**, not Gravcore.
- Do not invent Goa'uld fuel/resources to solve integration inconvenience.
- CatCraft owns its Stargate network/dial/iris/receive buffer.
- No replacement/generated art unless Vardath explicitly requests it.
- Approved planned Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa content is recorded in the two 2026-09-11 planning appends and remains required planned work.

## Handoff maintenance

Before ending a meaningful batch, record:
- exact new public HEAD;
- what actually changed;
- implemented / unfinished dependency / Vardath change / live-test-needed status;
- superseded decisions;
- next genuine slice derived from current `main`.

The objective is that Vardath can say **“refresh memory and continue”** and work resumes without interrogation or reconstruction.
