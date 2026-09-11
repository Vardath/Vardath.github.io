# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-12**  
Author/final design authority: **Vardath**

This is the mutable implementation-state supplement to `CANONICAL_RECOVERY_LEDGER.md`, `PUBLIC_RECONCILIATION_2026-09-11.md` and `PASS_CHECKPOINTS.md`.

**Current public source is implementation truth. Private/old WNG is requirement/reference evidence only. There are no known-good historical builds.**

Mandatory continuation order:

`STANDING_RULES -> CANONICAL_RECOVERY_LEDGER -> PUBLIC_RECONCILIATION -> CURRENT_PUBLIC_STATE -> latest PASS_CHECKPOINTS -> WNG_IMPLEMENTATION_CHECKLIST -> actual public main/files/assets -> active plan/contracts -> Stargate lore -> native RimWorld/optional-mod mechanics -> implement -> validate -> reconcile -> checkpoint`

Every known item must remain implemented, explicitly partial, explicitly missing-required, changed/rejected, planned-only/deferred or live-test-needed.

---

# CURRENT PUBLIC MOD HEAD

Repository: **`Vardath/Wraith-Nanite-Gravtech-1.6`**

**`9f45ebf18caacde671f015cdd1a25217eebb6838` — `rebuild: add Replicator evidence-analysis bridge`**

Public diff from `ff4f8dcb...` is exactly:
- `Defs/ThingDefs/Things_Replicator.xml` — recovered Replicator blocks made native analyzable evidence;
- `Defs/ResearchProjectDefs/Research_Replicator.xml` — `WNG_ReplicatorStudy` additionally requires analyzed Replicator blocks.

Validation run **`34615590179` — SUCCESS** before clean promotion. Release build, Def/Patch XML and evidence-bridge invariants passed. A cleanup command accidentally staged generated build outputs on the temporary branch; that head was rejected and never promoted. The branch/public tree was reconstructed from the exact public base plus the two validated XML blobs. Public compare is exactly the intended two files.

## Recent public milestones

- `26680fe84b95a0bfd5a23841b714fdba9cde1a98` — Temporary Asuran lattice intrusion.
- `9ce713704505a220d357f8a6f234fb6e040e0b2e` — recurring exact-map Queen recovery.
- `0b8150f3ff6ca7138482ba9a604847f5967fc48b` — captured-Queen sovereign consequences.
- `8495b846c7dd31c079db6d4f007be490df3247f3` — Neural Interface / exact reconstruction.
- `c7a9b46a3bef9393301d153e3f56c3c44c7ce95c` — Asuran conceal/reveal.
- `87da0e524324190584ac31e1830265db76688fae` — covert visitor impersonation.
- `b242dc72d139910172e8de3290530b505fcfa823` — Quiet Lattice human-form society.
- `45e62cd7f5ea18d2cf3f57df8b25beda1aabe1ad` — native WNG backstories.
- `12590e8ea88ce208a640fe2475de1843a7e227af` — physical Replicator Grav adaptation.
- `b5cde48e3cbcb2d608edabc78758e5fe9e4aec39` — native-projectile AntiShield integration.
- `e1a080c93893ff5742f5aa91bc00fd7ecc1699f7` — bounded Wraith Growth Chamber.
- `ff4f8dcb7b8ba17760a48a54f616466642189b0c` — paused two-stage strategic Wraith feeding request UI.
- `9f45ebf18caacde671f015cdd1a25217eebb6838` — first encounter/evidence/research progression bridge.

---

# IMPLEMENTED FOUNDATIONS

## Block Replicators

Implemented:
- Drone -> Hunter -> Bulwark -> Titan -> Siege Mass hierarchy and real downward destruction splitting;
- split-born recombination lockout;
- Controller / Repairer / Burrower / Artillery specialists;
- assimilation/stored-matter offspring economy, dangerous Replicator Matter, EMP, containment, regeneration/retaliation, Child's Toy branch;
- controller-domain inheritance through split/recombine/assimilation offspring;
- Material / Armor / Ranged / Power / Shield adaptation foundations;
- Grav evidence/save state + approved overlay + real physical gravitic reposition behavior;
- AntiShield persistent evidence/state + block adaptive-shield countermeasure + native energy-shield integration;
- **native Replicator evidence-analysis progression bridge**.

### Replicator evidence progression — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- destroyed Replicators already yield real `WNG_ReplicatorMatter`;
- Replicator Matter retains its existing dangerous reassembly mechanics and tuning;
- Replicator Matter now uses Odyssey native `CompAnalyzableUnlockResearch` with stable WNG analysis ID `160912001`;
- one 1.5-hour research-bench analysis by a colonist is sufficient and does not consume the blocks;
- `WNG_ReplicatorStudy` still requires `Machining` and now also requires analyzed `WNG_ReplicatorMatter` through native `requiredAnalyzed`;
- no fixed-day gate, new incident, Quest or custom progression component was introduced;
- rarer `WNG_ReplicatorCoreFragment` remains available for deeper later containment/lattice/reconstruction use rather than being consumed as the first-tier gate.

Grav, AntiShield and evidence analysis are implemented foundations but still require live-game/save-load tuning and verification.

## Controller / Queen architecture

Distinct public authorities: autonomous `None`, exact Queen, physical Sovereign Neural Lattice, Temporary Asuran, and captured-retained-Queen remote sovereignty. Exact Queen vault/release/recovery/capture, real sovereignty and captured-Queen mixed consequences are implemented foundations. Live testing remains required.

## Human-form Replicators / Asurans

Implemented:
- `WNG_NaniteHumanoid`, Nanite Reserve, synthetic depletion/self-repair/fabrication, EMP disruption;
- hostile `WNG_AsuranLattice` with Operative / Technician / Commander / Infiltrator roles;
- Temporary Asuran block intrusion and captured-Queen mixed threats;
- Neural Interface recruit/imprison/Ideology-slave/skill-copy/exact reconstruction;
- same-pawn conceal/reveal and covert visitor impersonation with native cover-faction/guest mechanics;
- non-hostile **The Quiet Lattice** / `WNG_HumanFormEnclave`;
- generalist / engineer / soldier / coordinator / player human-form PawnKinds;
- Peaceful / Settlement / bounded Combat Quiet-Lattice composition;
- native WNG synthetic backstories.

Still required:
- complete synthetic disease/implant/temperature/vacuum physiology audit;
- friendly Quiet-Lattice/Puddle-Jumper Stargate courier;
- optional broader DLC identity-copy fidelity audit;
- final art/audio;
- live world-generation/faction/Neural-Interface/infiltration/captivity/save-load testing.

## Wraith

Implemented:
- one Wraith xenotype and Hunter / Warrior / Commander / Keeper / Queen roles;
- pale/white hair handling;
- Life Force, full Drain Life, Partial Feed, regeneration, hibernation;
- Sable Brood / Cinder Court / Veiled Hive / Pale Covenant;
- strategic faction hunger separate from ordinary feeding;
- exact captivity/rescue;
- Feeding Niche / Hibernation Pod / Dormancy Vault / Hive Heart;
- mature-Hive feeding-stock/population/retaliation foundation;
- living-tech bootstrap, real Wraith Grav Engine, stun staff, Dart/captivity foundation, Wraith gravship mechanics and living-hull regeneration;
- native WNG Wraith backstories;
- bounded Wraith Growth Chamber;
- complete paused two-stage strategic-hunger feeding-request UI.

Still required:
- broader discovery/story progression, including a real Wraith evidence-to-research bridge;
- generated-Mature-Hive Growth Chamber placement after a real Wraith ground-power solution exists;
- final presentation/audio/live testing.

Ordinary feeding, strategic hunger, mature-Hive feeding ecology and mature-Hive retaliation remain separate systems.

## Craft / Stargate integration

Implemented mechanical foundations include Wraith Dart, Wraith scout/Strike Craft, Wraith Cruiser, Puddle Jumper, **Al'kesh**, Death Glider, Asuran recovery Jumper, Goa'uld transport rings and CatCraft/ONAC/RimGate ownership boundaries.

Still required: Quiet-Lattice/Puddle-Jumper courier, deliberate Ancient/Puddle-Jumper power/fuel abstraction, unloaded-world-site exact-pawn ring transport, live craft/save-load validation and final art/audio.

## Gravships / Goa'uld

Wraith/Asuran Odyssey-native mechanical families and family fuel networks are implemented. Wraith defense is living-hull regeneration; generic Wraith shield reskin is rejected. Asuran uses a real powered shield emitter. Goa'uld Ha'tak/Death-Glider/carrier/orbital-bombardment foundations are public.

Still required/blocked: safe standalone Goa'uld ship material/fuel/research path without ONAC; safely solved hostile Ha'tak native takeoff only if Odyssey ownership permits it; professional hull topology presentation; final art/audio/live testing.

---

# CURRENT REQUIRED UNFINISHED INVENTORY

Broader discovery/story progression remains unfinished; the first Replicator encounter/evidence/research bridge is now public rather than the whole progression family being marked complete.

1. **Broader discovery/story progression** — continue as short evidence bridges for Wraith, Asuran/Ancient and other retained families.
2. Generated Mature Hive Growth Chamber placement after real Wraith ground-power/bioelectric-energy support exists.
3. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
4. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
5. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
6. Unloaded-world-site transport-ring exact-pawn/world-object transport.
7. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
8. Final professional craft/gravship/implant/building/weapon/resource art review.
9. Professional WNG audio layer.
10. Hostile Ha'tak native takeoff/retreat/pursuit only if safely solvable through Odyssey ownership; never fake it.
11. Broad current-build live RimWorld/save-load/mod-stack/performance validation/tuning.
12. Human-form synthetic disease/implant/temperature/vacuum physiology audit.
13. Optional broader DLC identity-copy fidelity audit for Neural Interface copies.
14. Explicit third-party shield integration only for verified shield systems outside RimWorld's native projectile-interceptor path.
15. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear.

---

# GENUINE NEXT SHORT PASS

**Reconcile one Wraith evidence-to-research bridge only.**

Before code:
- inspect what physical Wraith evidence is genuinely available before `WNG_WraithLivingTechnology` is researched;
- prefer evidence already present at Mature Hive/Dart/feeding/living-tech encounters rather than inventing a new timed site;
- ensure the evidence is actually obtainable before the research it gates;
- use the native Odyssey analysis path where coherent;
- do not bundle Wraith shuttle, gravship, Growth Chamber power or Asuran/Ancient progression into the same pass;
- checkpoint the exact Wraith evidence object/acquisition path before implementation.
