# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-11 — Quiet Lattice / human-form society foundation promoted to public

## Public implementation state

Public mod `main` is now:

**`b242dc72d139910172e8de3290530b505fcfa823` — `rebuild: add Quiet Lattice human-form society`**

Promotion used the validated **pre-workflow** source tree from branch commit `8d3810ae372179d72375a08d0a53418d7848f755`, with public parent `87da0e...`. The temporary validator therefore did **not** enter public `main` even though connector safety blocked deleting it from the old branch.

## What is now public

Added:
- `Defs/FactionDefs/Factions_QuietLattice.xml`;
- `Defs/PawnKindDefs/PawnKinds_HumanFormSocieties.xml`.

Implemented:
- real non-hostile `WNG_HumanFormEnclave` / **The Quiet Lattice** as a separate society from hostile `WNG_AsuranLattice`;
- current-architecture `WNG_NaniteHumanoid` society rather than old `WNG_NanitePrecursor`;
- `WNG_HumanFormReplicator` generalist role;
- `WNG_HumanFormEngineer` fabrication/infrastructure role;
- `WNG_HumanFormSoldier` defensive role;
- `WNG_HumanFormCoordinator` leadership/coordinator role;
- `WNG_PlayerHumanFormReplicator` player-aligned human-form role;
- bounded Combat, Peaceful and Settlement group compositions;
- Quiet Lattice is not permanently/naturally hostile and can exist as a settlement faction;
- hostile Asuran Lattice remains separate and unchanged;
- no references to obsolete/missing historical precursor weapon/armor/uniform Defs.

## Reconciliation basis

Recovered chat/history required:
- hostile Asuran/Lattice society;
- separate non-hostile Quiet Lattice human-form enclave;
- player human-form variants;
- engineer / infiltrator / soldier / coordinator-command role structure;
- later native WNG backstories;
- later friendly Quiet-Lattice/Puddle-Jumper Stargate courier.

Historical/private `WNG_HumanFormEnclave`, human-form role PawnKinds and `Backstories_WNG.xml` were used only as requirement evidence. Superseded `WNG_NanitePrecursor` and missing precursor equipment were not restored.

Stargate lore gate: Quiet Lattice is explicitly a **WNG-created splinter society**, not a canon-named faction. Its basis is canon-compatible Asuran ideological divergence such as Niam's anti-aggression/ascension-seeking group and the existence of individual human-form Replicator identities.

## Validation

GitHub Actions run **`34606524857` — SUCCESS**:
- Release C# build passed;
- all current Def/Patch XML parsed;
- Quiet Lattice faction identity, non-hostility and current xenotype wiring passed;
- Peaceful/Settlement/Combat group wiring passed;
- engineer/soldier/coordinator/generalist/player-role presence passed;
- hostile `WNG_AsuranLattice` separation passed;
- forbidden obsolete `WNG_NanitePrecursor` / precursor equipment references absent.

This is **source/Def validation, not live RimWorld validation**.

## Remaining human-form dependencies

- native WNG backstories are still missing; Quiet Lattice currently uses generic `Outlander`/`Offworld` generation categories only as provisional compatibility;
- hostile Asuran roles also still lack native WNG synthetic biographies;
- Wraith native backstories remain missing too;
- Quiet-Lattice/Puddle-Jumper friendly Stargate courier remains later integration after faction/backstory foundation;
- live faction world-generation, relations, settlement, pawn-group and save/load testing remains required;
- final art/audio remains later debt.

## Exact next pass

**Native WNG BackstoryDef foundation** covering both Wraith and human-form synthetic society roles.

Required steps:
1. inspect the complete historical `Backstories_WNG.xml` as requirement/reference evidence;
2. inspect current Wraith and human-form PawnKinds/faction generation filters and current RimWorld 1.6 `BackstoryDef` schema;
3. reconcile backstory text/roles against Stargate lore — do not invent false canon claims;
4. rebuild native WNG origin/adulthood categories against current identities (`WNG_Wraith`, `WNG_NaniteHumanoid`, Quiet Lattice/current Asuran roles), not superseded precursor identities;
5. preserve race/xenotype, caste/PawnKind, faction and backstory as separate identity layers;
6. wire faction/PawnKind generation to native WNG backstory categories without breaking existing current pawns;
7. validate Release build + XML/reference/category invariants;
8. checkpoint before promotion/next subsystem.

---

# PRIOR PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**.
- Recurring exact-map Queen recovery: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**.
- Captured Queen sovereign consequences: **`0b8150f3ff6ca7138482ba9a604847f5967fc48b`**.
- Neural Interface / exact reconstruction: **`8495b846c7dd31c079db6d4f007be490df3247f3`**.
- Infiltration conceal/reveal: **`c7a9b46a3bef9393301d153e3f56c3c44c7ce95c`**.
- Covert visitor impersonation: **`87da0e524324190584ac31e1830265db76688fae`**.
- Quiet Lattice human-form society: **`b242dc72d139910172e8de3290530b505fcfa823`**.

All are source/Def validated before public promotion; broad live RimWorld validation remains outstanding.
