# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-11**  
Author/final design authority: **Vardath**

This is the mutable implementation-state supplement to `CANONICAL_RECOVERY_LEDGER.md`, `PUBLIC_RECONCILIATION_2026-09-11.md` and `PASS_CHECKPOINTS.md`.

**Current public source is implementation truth. Private/old WNG is requirement/reference evidence only. There are no known-good historical builds.**

Mandatory continuation order:

`STANDING_RULES -> CANONICAL_RECOVERY_LEDGER -> PUBLIC_RECONCILIATION -> CURRENT_PUBLIC_STATE -> latest PASS_CHECKPOINTS -> WNG_IMPLEMENTATION_CHECKLIST -> actual public main/files/assets -> active plan/contracts -> Stargate lore -> native RimWorld/optional-mod mechanics -> implement -> validate -> reconcile -> checkpoint`

Every known item must remain implemented, explicitly partial, explicitly missing-required, changed/rejected, planned-only/deferred or live-test-needed.

---

# CURRENT PUBLIC MOD HEAD

Repository: **`Vardath/Wraith-Nanite-Gravtech-1.6`**

**`45e62cd7f5ea18d2cf3f57df8b25beda1aabe1ad` — `rebuild: add native WNG backstories`**

The public commit contains only:
- `Defs/BackstoryDefs/Backstories_WNG.xml`;
- current Wraith PawnKind backstory wiring;
- current Asuran PawnKind backstory wiring;
- current Quiet-Lattice/player-human-form PawnKind wiring;
- exact Replicator Queen backstory wiring.

Validation run **`34608137484` — SUCCESS**. Release build, current Def/Patch XML, current 1.6 SkillGain schema, required categories and role wiring passed. This is source/Def validation, not broad live RimWorld validation.

## Recent public milestones

- `26680fe84b95a0bfd5a23841b714fdba9cde1a98` — Temporary Asuran lattice intrusion.
- `9ce713704505a220d357f8a6f234fb6e040e0b2e` — recurring exact-map Queen recovery.
- `0b8150f3ff6ca7138482ba9a604847f5967fc48b` — captured-Queen sovereign consequences.
- `8495b846c7dd31c079db6d4f007be490df3247f3` — Neural Interface / exact reconstruction.
- `c7a9b46a3bef9393301d153e3f56c3c44c7ce95c` — Asuran conceal/reveal.
- `87da0e524324190584ac31e1830265db76688fae` — covert visitor impersonation.
- `b242dc72d139910172e8de3290530b505fcfa823` — Quiet Lattice human-form society.
- `45e62cd7f5ea18d2cf3f57df8b25beda1aabe1ad` — native WNG backstories.

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
- AntiShield persistent state and current Replicator-shield interaction;
- Grav learned/save-persistent state + visual overlay.

Still partial:
- richer physical/mobility Grav behavior;
- broader AntiShield interaction with concrete non-Replicator shields.

## Controller / Queen architecture

Distinct public authorities: autonomous `None`, exact Queen, physical Sovereign Neural Lattice, Temporary Asuran, and captured-retained-Queen remote sovereignty. Exact Queen vault/release/recovery/capture, real sovereignty and captured-Queen mixed consequences are implemented foundations. Live testing remains required.

## Human-form Replicators / Asurans

Implemented:
- `WNG_NaniteHumanoid`, Nanite Reserve, synthetic depletion/self-repair/fabrication, EMP disruption;
- hostile `WNG_AsuranLattice` with current Operative / Technician / Commander / Infiltrator roles;
- Temporary Asuran block intrusion and captured-Queen mixed threats;
- Neural Interface recruit/imprison/Ideology-slave/skill-copy/exact reconstruction;
- same-pawn conceal/reveal and real covert visitor impersonation using valid native cover-faction/guest mechanics;
- non-hostile **The Quiet Lattice** / `WNG_HumanFormEnclave` as a separate WNG-created splinter society;
- generalist / engineer / soldier / coordinator / player human-form PawnKinds;
- Peaceful / Settlement / bounded Combat Quiet-Lattice composition;
- **native WNG synthetic backstories**, with distinct origins and Operative / Engineer / Soldier / Coordinator / Infiltrator / Quiet-Lattice / Player adulthood categories.

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
- **native WNG Wraith backstories** with shared Hive origins plus Hunter / Warrior / Commander / Keeper / Queen / Player adulthood categories.

Still required:
- Wraith Growth Chamber;
- strategic-hunger involved-Wraith count/names UI stage;
- broader discovery/story progression;
- final presentation/audio/live testing.

Ordinary feeding, strategic hunger, mature-Hive feeding ecology and mature-Hive retaliation remain separate systems.

## Craft / Stargate integration

Implemented mechanical foundations include Wraith Dart, Wraith scout/Strike Craft, Wraith Cruiser, Puddle Jumper, **Al'kesh**, Death Glider, Asuran recovery Jumper, Goa'uld transport rings and CatCraft/ONAC/RimGate ownership boundaries.

Still required: Quiet-Lattice/Puddle-Jumper courier, deliberate Ancient/Puddle-Jumper power/fuel abstraction, unloaded-world-site exact-pawn ring transport, live craft/save-load validation and final art/audio.

## Gravships / Goa'uld

Wraith/Asuran Odyssey-native mechanical families and family fuel networks are implemented. Wraith defense is living-hull regeneration; generic Wraith shield reskin is rejected. Asuran uses real powered shield emitter. Goa'uld Ha'tak/Death-Glider/carrier/orbital-bombardment foundations are public.

Still required/blocked: safe standalone Goa'uld ship material/fuel/research path without ONAC; safely solved hostile Ha'tak native takeoff only if Odyssey ownership permits it; professional hull topology presentation; final art/audio/live testing.

---

# CURRENT REQUIRED UNFINISHED INVENTORY

Native WNG backstories are removed from missing debt because they are now implemented on public `main`.

1. **Richer block Grav adaptation and broader AntiShield integration.**
2. Wraith Growth Chamber.
3. Strategic Wraith hunger involved-Wraith count/names UI stage.
4. Broader discovery/story progression.
5. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
6. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
7. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
8. Unloaded-world-site transport-ring exact-pawn/world-object transport.
9. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
10. Final professional craft/gravship/implant/building/weapon/resource art review.
11. Professional WNG audio layer.
12. Hostile Ha'tak native takeoff/retreat/pursuit only if safely solvable through Odyssey ownership; never fake it.
13. Broad current-build live RimWorld/save-load/mod-stack/performance validation/tuning.
14. Human-form synthetic disease/implant/temperature/vacuum physiology audit.
15. Optional broader DLC identity-copy fidelity audit for Neural Interface copies.
16. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear.

---

# GENUINE NEXT IMPLEMENTATION SLICE

**Richer block Replicator Grav adaptation + broader AntiShield integration.**

Before code:
- inspect current public Replicator state/adaptation/effect source and all current shield/grav dependencies;
- inspect recovered history/plan for intended Grav and AntiShield behavior rather than inventing effects from the names;
- perform Stargate lore check: distinguish Replicator adaptation/resistance from ARG-style disruption and distinguish actual gravity/ship technology from generic telekinesis;
- inspect native RimWorld/Odyssey mechanics that can represent movement/grav effects and WNG/vanilla shield hooks;
- preserve existing persistent evidence-learning and overlays;
- implement only concrete currently-supported cross-system interactions, recording any dependency that still lacks a real shield target;
- bounded pass, Release/XML/static validation, public checkpoint before promotion/next subsystem.
