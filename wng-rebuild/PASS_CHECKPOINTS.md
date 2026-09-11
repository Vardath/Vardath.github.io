# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Replicator Grav adaptation reconciliation complete

## Public implementation state

Public mod `main` remains:

**`45e62cd7f5ea18d2cf3f57df8b25beda1aabe1ad` — native WNG backstories.**

No Grav code was changed in this reconciliation pass.

## Recovered plan/history boundary

The recovered plan explicitly requires:
- adaptation earned from actual assimilation evidence;
- `gravtech -> grav capability`;
- Grav must matter in gameplay;
- the already-saved Grav state and retained Grav overlay must remain;
- the unfinished effect is specifically described as a **richer physical/mobility behavior**;
- the earlier foundation checkpoint explicitly forbids substituting an unrelated generic movement/stat buff merely to mark Grav complete.

Current public source confirms:
- assimilation identities containing `grav` / `gravity` learn `ReplicatorAdaptation.Grav`;
- Grav state is save-persistent and transferred with the other learned state;
- the approved `WNG_ReplicatorAdapt_Grav` overlay is already rendered;
- `CompReplicatorAdaptationEffects` currently has no Grav gameplay effect.

## Stargate lore gate

Canon-grounded facts used for the implementation interpretation:
- individual Replicator blocks interact through reactive modulating energy fields;
- Replicators consume/study advanced technology and reproduce capabilities in their own structures/ships;
- at Halla, a Replicator mass used captured advanced technology to counter gravitational effects strong enough to trap/destroy them and then formed a Replicator cruiser to escape.

Canon does **not** establish ordinary block Replicator bugs as permanently flying/hovering infantry, and there is no basis for generic telekinesis.

Therefore WNG's pawn-scale Grav adaptation remains explicitly a **gameplay extrapolation of learned gravitic field control**, not a claim that SG-1 depicted ordinary bugs using this exact maneuver.

## Native RimWorld/Odyssey mapping

Do **not** use:
- a generic `MoveSpeed` stat buff;
- permanent hovering/flying pathing;
- teleportation;
- Harmony movement-cost replacement merely to simulate a bonus;
- gravship ownership mechanics on an individual pawn.

Use RimWorld's existing physical jump/flyer transaction instead:
- `JumpUtility.DoJump` / native `PawnFlyer` provides a real same-pawn movement transaction;
- landing remains on a native valid/walkable cell;
- use native jump target validation / line-of-sight semantics rather than phasing through sealed structures;
- the maneuver is a brief local gravitic field displacement, not sustained flight.

## Exact first implementation interpretation

**Grav adaptation = short-range gravitic reposition maneuver.**

Required behavior for the next code pass:
- only block Replicators with learned `ReplicatorAdaptation.Grav` can use it;
- same exact pawn is moved through native `PawnFlyer`; no pawn replacement/proxy;
- current first-build range/cooldown/minimum useful distance remain Def-tunable in `CompProperties_ReplicatorAdaptationEffects`;
- no passive speed bonus;
- target must be in bounds, native-valid/walkable and within range; use native/LOS constraints so the adaptation does not phase through closed structures;
- EMP disables the maneuver;
- active WNG Replicator containment at the origin or destination blocks the maneuver;
- player/controller-operational blocks expose an explicit Grav reposition target command;
- autonomous hostile blocks may use it tactically to close/reposition toward a visible hostile target, but not spam continuously and not replace specialist roles;
- preserve all existing authority/domain/combat-permission rules;
- Grav state/overlay/save inheritance remain unchanged.

Current first-build tuning can be modest (roughly a 6-8 cell local maneuver with several seconds of cooldown), but must remain Def data and is not permanent design doctrine.

## AntiShield boundary deliberately not implemented in this pass

AntiShield remains separate. Current public already has:
- save-persistent AntiShield evidence/state;
- extra damage against Replicator adaptive shields.

Concrete non-Replicator shield systems confirmed for the later AntiShield pass include native `CompProjectileInterceptor` / `CompGravshipShieldGenerator`, including the current WNG Asuran gravship shield emitter. Wraith gravship defense is **living-hull regeneration**, not an energy shield, and must not be incorrectly treated as an AntiShield target.

## Exact next pass

**Implement Grav adaptation only** on a fresh branch from public `45e62cd...`:
1. add Def-tunable grav range/cooldown/min-use-distance fields to existing adaptation comp properties;
2. add native `JumpUtility`/`PawnFlyer` transaction and target validation;
3. add controlled/player Grav target command;
4. add bounded autonomous tactical use;
5. enforce EMP + containment + existing combat/authority boundaries;
6. preserve saved state/overlay;
7. Release build + XML/static invariants;
8. checkpoint branch before promotion.

Do **not** begin AntiShield implementation until that Grav pass is closed/checkpointed.

---

# PRIOR CHECKPOINT — native WNG backstories promoted to public

Public milestone:

**`45e62cd7f5ea18d2cf3f57df8b25beda1aabe1ad` — `rebuild: add native WNG backstories`**

Validation run **`34608137484` — SUCCESS**. Native current-schema WNG Wraith/synthetic BackstoryDefs and current PawnKind category wiring are public. This remains source/Def validation, not broad live RimWorld validation.

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

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
