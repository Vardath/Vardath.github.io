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

**`b5cde48e3cbcb2d608edabc78758e5fe9e4aec39` — `rebuild: integrate Replicator AntiShield with native energy shields`**

Public diff from `12590e8...` contains exactly:
- `Defs/ThingDefs/Projectiles_Replicator.xml` — added;
- `Source/WNG/Replicators/ReplicatorAdaptiveProjectile.cs` — added;
- `Source/WNG/Replicators/ReplicatorAdaptationEffects.cs` — modified.

Corrected validation run **`34610731875` — SUCCESS** before clean promotion. The earlier run `34610597370` failed at the temporary workflow-wrapper level before creating a job and did not produce a source result. Release build, Def/Patch XML and AntiShield invariants passed in the corrected run. This is source/Def validation, not broad live RimWorld validation.

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
- AntiShield persistent evidence/state + block adaptive-shield countermeasure + **native energy-shield integration**.

### Grav adaptation — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- learned through existing grav/gravity assimilation evidence;
- native `JumpUtility.DoJump` / `PawnFlyer` exact-pawn reposition;
- no MoveSpeed bonus, teleport, permanent flight, phasing or pawn recreation;
- current Def tuning: range 7, minimum useful distance 3, cooldown 360 ticks, landing radius 2;
- native valid/walkable/LOS constraints;
- EMP and WNG containment suppress use;
- player command + bounded autonomous tactical use;
- cooldown save-persistent.

### AntiShield — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- AntiShield remains a later countermeasure unlocked only after repeated shield/barrier evidence; current threshold is Def-tunable and set to 3;
- adaptive ranged fire now uses a real native `Bullet` projectile instead of direct `TakeDamage`, so walls/cover and native projectile shields participate normally;
- non-AntiShield shots are normally intercepted by `CompProjectileInterceptor` / `CompGravshipShieldGenerator` shields;
- an AntiShield launcher presents the existing Def-tunable `antiShieldDamageMultiplier` as increased shield depletion to native interceptors;
- ordinary unshielded body impact remains normal configured adaptive-ranged body damage/armor penetration rather than a generic AntiShield body-damage bonus;
- existing WNG block adaptive-shield countermeasure behavior is retained;
- Wraith living-hull regeneration is not an energy shield and receives no AntiShield interaction;
- no Harmony patch is used;
- third-party shield systems outside the native projectile-interceptor path remain explicit future integrations only if their real APIs are later supplied/verified.

## Controller / Queen architecture

Distinct public authorities: autonomous `None`, exact Queen, physical Sovereign Neural Lattice, Temporary Asuran, and captured-retained-Queen remote sovereignty. Exact Queen vault/release/recovery/capture, real sovereignty and captured-Queen mixed consequences are implemented foundations. Live testing remains required.

## Human-form Replicators / Asurans

Implemented:
- `WNG_NaniteHumanoid`, Nanite Reserve, synthetic depletion/self-repair/fabrication, EMP disruption;
- hostile `WNG_AsuranLattice` with Operative / Technician / Commander / Infiltrator roles;
- Temporary Asuran block intrusion and captured-Queen mixed threats;
- Neural Interface recruit/imprison/Ideology-slave/skill-copy/exact reconstruction;
- same-pawn conceal/reveal and covert visitor impersonation with valid native cover-faction/guest mechanics;
- non-hostile **The Quiet Lattice** / `WNG_HumanFormEnclave` as separate WNG-created splinter society;
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
- native WNG Wraith backstories.

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

Wraith/Asuran Odyssey-native mechanical families and family fuel networks are implemented. Wraith defense is living-hull regeneration; generic Wraith shield reskin is rejected. Asuran uses a real powered shield emitter. Goa'uld Ha'tak/Death-Glider/carrier/orbital-bombardment foundations are public.

Still required/blocked: safe standalone Goa'uld ship material/fuel/research path without ONAC; safely solved hostile Ha'tak native takeoff only if Odyssey ownership permits it; professional hull topology presentation; final art/audio/live testing.

---

# CURRENT REQUIRED UNFINISHED INVENTORY

Broader native AntiShield integration is removed from missing debt because it is now public.

1. **Wraith Growth Chamber.**
2. Strategic Wraith hunger involved-Wraith count/names UI stage.
3. Broader discovery/story progression.
4. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
5. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
6. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
7. Unloaded-world-site transport-ring exact-pawn/world-object transport.
8. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
9. Final professional craft/gravship/implant/building/weapon/resource art review.
10. Professional WNG audio layer.
11. Hostile Ha'tak native takeoff/retreat/pursuit only if safely solvable through Odyssey ownership; never fake it.
12. Broad current-build live RimWorld/save-load/mod-stack/performance validation/tuning.
13. Human-form synthetic disease/implant/temperature/vacuum physiology audit.
14. Optional broader DLC identity-copy fidelity audit for Neural Interface copies.
15. Explicit third-party shield integration only for verified shield systems outside RimWorld's native projectile-interceptor path.
16. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear.

---

# GENUINE NEXT PASS

**Wraith Growth Chamber reconciliation only.**

Before code:
- recover the Growth Chamber requirement from chat/history/plan and inspect historical file evidence without treating it as known-good;
- inspect current public Wraith Hive infrastructure, feeding, reproduction/population and living-tech files/assets;
- perform Stargate lore gate: distinguish canon Wraith cloning facilities/growth systems from WNG gameplay abstractions;
- define exactly what the Growth Chamber adds that current Hive Heart / Feeding Niche / Hibernation Pod / Dormancy Vault do not already provide;
- ensure it does not merge ordinary feeding, strategic hunger, mature-Hive ecology or retaliation;
- checkpoint the reconciliation decision before implementation.
