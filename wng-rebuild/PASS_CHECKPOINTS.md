# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-11 — Asuran covert visitor impersonation promoted to public

## Public implementation state

Public mod `main` is now:

**`87da0e524324190584ac31e1830265db76688fae` — `rebuild: add Asuran covert visitor impersonation`**

It was promoted as one clean public commit with parent `c7a9b46...` from the validated clean tree `3a140d0774600e92162baf74b4af153fed35b3a0`.

Public diff contains only:
- `Defs/IncidentDefs/Incidents_AsuranCovertPresence.xml` — added;
- `Source/WNG/Asuran/AsuranCovertPresence.cs` — added;
- `Source/WNG/Asuran/AsuranInfiltration.cs` — updated.

No temporary validation workflow entered public `main`.

## What is now public

- save-persistent Def-tunable covert-visitor scheduler;
- real `WNG_AsuranInfiltrator` covert arrival on player-home maps;
- real visible non-hostile humanlike faction used as temporary cover identity;
- exact true `WNG_AsuranLattice` source faction saved on the same pawn's persistent infiltration state;
- native `GuestStatus.Guest` and native `LordJob_VisitColony` under that valid cover identity;
- visitor letter does not disclose hidden Asuran source;
- direct scan, EMP, meaningful injury and suspicious self-repair all break cover through the same reveal path;
- exact same pawn restores its stored Asuran faction and enters real `LordJob_AssaultColony` behavior when revealed and free;
- prisoner reveal preserves prisoner status while restoring true faction;
- slave reveal defers hostile activation rather than destroying native slavery state;
- downed/off-map activation is deferred until physically valid;
- no pawn recreation/proxy and no Queen/block-sovereignty inference.

## Native API correction preserved

Current RimWorld `Pawn_GuestTracker.SetGuestStatus(... Guest)` rejects a pawn whose current faction is hostile to the proposed host. The earlier idea of keeping active hostile Asuran faction while simply adding player Guest status is therefore superseded.

The public implementation instead temporarily uses a genuine non-hostile human cover faction while storing the exact true Asuran source on the same pawn. This is actual impersonation and obeys native guest mechanics.

## Validation

GitHub Actions run **`34605318105` — SUCCESS**:
- Release C# build passed;
- all current Def/Patch XML parsed;
- persistent scheduler/true-cover faction/native Guest/native VisitColony/reveal-assault invariants passed.

This remains **source/Def validation, not live RimWorld validation**.

`CURRENT_PUBLIC_STATE.md` has been corrected to public HEAD `87da0e...` and strategic infiltration/impersonation is now recorded as implemented foundation / live-test-needed rather than missing-required.

---

# QUIET LATTICE RECONCILIATION — completed before next code pass

## Recovered chat/history requirement

The human-form slice must not collapse identity layers or silently discard branches. Required society/role structure includes:
- hostile Asuran/Lattice society;
- non-hostile **Quiet Lattice** human-form Replicator enclave;
- player human-form variants;
- engineer / infiltrator / soldier / coordinator-command roles where distinct;
- later native WNG backstories;
- later friendly Quiet-Lattice / Puddle-Jumper Stargate courier integration.

Quiet Lattice is defined by recovered WNG history as a human-form Replicator enclave choosing **controlled replication and negotiated coexistence over unrestricted expansion**.

## Historical file evidence inspected

Historical/reference branch `rebuild/wngr2-humanform-factions-20260909` contains:
- `WNG_HumanFormEnclave` / **The Quiet Lattice** as non-hostile, coordinator-led, settlement-capable human-form synthetic faction;
- hostile `WNG_PrecursorCollective` / Lattice Collective as a separate society;
- role PawnKinds `WNG_PrecursorEngineer`, `WNG_PrecursorSoldier`, `WNG_PrecursorCommander`, generic `WNG_HumanFormReplicator`, and `WNG_PlayerHumanFormReplicator`;
- `Backstories_WNG.xml` with synthetic origins and engineer/soldier/commander/human-form/player backstory categories.

Those old Defs use superseded identities such as `WNG_NanitePrecursor` and old equipment tags/assets that are not present in current public. They are **requirement evidence only and must not be copied wholesale**.

## Current public file reality

Current public uses:
- `WNG_NaniteHumanoid` as the real human-form nanite xenotype;
- current Asuran Operative / Technician / Commander / Infiltrator PawnKinds;
- current hostile `WNG_AsuranLattice` as the canon-Asuran hostile society;
- current Nanite Reserve / Neural Interface / concealment / covert-presence systems.

Search of current public found no current equivalents for old `WNG_PrecursorWeapon`, `WNG_PrecursorFieldArmor`, `WNG_PrecursorCommandArmor` or `WNG_HumanFormUniform`. Therefore the next pass must **not** resurrect references to those absent assets/Defs.

## Stargate lore gate

Quiet Lattice is **not a canon-named faction**. Its basis is a WNG extrapolation grounded in canon evidence that:
- Asurans are individual functioning beings linked by shared base-code/subspace updates rather than a single hive mind;
- Niam and others sought removal/suppression of the aggression directive and were willing to stop attacks on Atlantis;
- Niam's group represents internal ideological divergence;
- the later Niam-associated splinter group pursued ascension separately from Oberoth's main Asuran society and created human replicas/impersonations after base-code alteration.

Therefore a non-hostile splinter society choosing restrained replication/coexistence is lore-compatible WNG design, but must not be falsely described as a canon faction called “Quiet Lattice.”

## Exact next implementation pass

Create a fresh branch from public `87da0e...` and implement one coherent **Quiet Lattice / broader human-form faction-role foundation**:
1. real non-hostile `WNG_HumanFormEnclave` / The Quiet Lattice faction using current `WNG_NaniteHumanoid` architecture;
2. current human-form engineer, soldier and coordinator roles without references to missing old gear/assets;
3. generic human-form Replicator and player human-form Replicator PawnKinds where they remain distinct from those roles;
4. Quiet Lattice Peaceful / Settlement / bounded Combat group composition;
5. preserve hostile `WNG_AsuranLattice` as separate faction; do not merge or replace it;
6. preserve infiltrator as distinct hostile/covert role rather than making Quiet Lattice secretly hostile by default;
7. explicitly leave native WNG backstories as the next dependency rather than using old generic biography as final design;
8. leave Quiet-Lattice/Puddle-Jumper courier as later integration after the faction foundation;
9. Release build + XML/reference validation, remove temp validator, checkpoint before promotion/next pass.

---

# PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**.
- Recurring exact-map Queen recovery: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**.
- Captured Queen sovereign consequences: **`0b8150f3ff6ca7138482ba9a604847f5967fc48b`**.
- Neural Interface / exact reconstruction: **`8495b846c7dd31c079db6d4f007be490df3247f3`**.
- Infiltration conceal/reveal: **`c7a9b46a3bef9393301d153e3f56c3c44c7ce95c`**.
- Covert visitor impersonation: **`87da0e524324190584ac31e1830265db76688fae`**.

All are source/Def validated; broad live RimWorld validation remains outstanding.
