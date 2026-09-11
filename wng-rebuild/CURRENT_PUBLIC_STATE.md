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

**`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — `rebuild: add Wraith Hive Heart evidence-analysis bridge`**

Public diff from `9f45ebf18...` is exactly:
- `Defs/ThingDefs/Wraith_HiveHeart.xml` — Hive Heart made native in-place analyzable Wraith evidence;
- `Defs/ResearchProjectDefs/Research_WraithBootstrap.xml` — `WNG_WraithLivingTechnology` additionally requires analyzed Hive Heart.

Validation run **`34616521496` — SUCCESS** before clean promotion. Release build, Def/Patch XML, unique analysis-ID, in-place analysis, exact `requiredAnalyzed` and unchanged Mature-Hive population invariants passed. Explicit cleanup paths were used; no generated build outputs entered public main. This is source/Def validation, not broad live RimWorld validation.

## Recent public milestones

- `26680fe84...` — Temporary Asuran lattice intrusion.
- `9ce7137045...` — recurring exact-map Queen recovery.
- `0b8150f3ff...` — captured-Queen sovereign consequences.
- `8495b846c7...` — Neural Interface / exact reconstruction.
- `c7a9b46a3b...` — Asuran conceal/reveal.
- `87da0e5243...` — covert visitor impersonation.
- `b242dc72d1...` — Quiet Lattice human-form society.
- `45e62cd7f5...` — native WNG backstories.
- `12590e8ea8...` — physical Replicator Grav adaptation.
- `b5cde48e3c...` — native-projectile AntiShield integration.
- `e1a080c938...` — bounded Wraith Growth Chamber.
- `ff4f8dcb7b...` — paused strategic Wraith feeding-request UI.
- `9f45ebf18c...` — Replicator evidence-analysis progression bridge.
- `d38ce6f321...` — Wraith Hive Heart evidence-analysis progression bridge.

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
- native Replicator encounter/evidence/research progression bridge.

Replicator evidence progression:
- destroyed Replicators yield real `WNG_ReplicatorMatter`;
- Replicator Matter retains dangerous reassembly mechanics/tuning and is native Odyssey analyzable evidence (`analysisID=160912001`);
- one 1.5-hour colonist/research-bench analysis does not consume the blocks;
- `WNG_ReplicatorStudy` requires `Machining` plus analyzed `WNG_ReplicatorMatter`;
- rarer `WNG_ReplicatorCoreFragment` remains deeper later evidence/material.

Grav, AntiShield and evidence analysis remain live-test-needed.

## Controller / Queen architecture

Distinct public authorities: autonomous `None`, exact Queen, physical Sovereign Neural Lattice, Temporary Asuran, and captured-retained-Queen remote sovereignty. Exact Queen vault/release/recovery/capture, real sovereignty and captured-Queen mixed consequences are implemented foundations. Live testing remains required.

## Human-form Replicators / Asurans

Implemented:
- `WNG_NaniteHumanoid`, Nanite Reserve, synthetic depletion/self-repair/fabrication, EMP disruption;
- hostile `WNG_AsuranLattice` with Operative / Technician / Commander / Infiltrator roles;
- Temporary Asuran block intrusion and captured-Queen mixed threats;
- Neural Interface recruit/imprison/Ideology-slave/skill-copy/exact reconstruction;
- same-pawn conceal/reveal and covert visitor impersonation with valid native cover-faction/guest mechanics;
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
- paused two-stage strategic-hunger feeding-request UI;
- **native Mature-Hive evidence -> Wraith Living Technology progression bridge**.

### Wraith evidence progression — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- every generated Mature Hive already requires one exact `WNG_WraithHiveHeart` before site generation succeeds;
- Mature Hive discovery has no WNG research prerequisite, so this evidence genuinely predates `WNG_WraithLivingTechnology`;
- a Mature Hive is neutralized by removing active hostile threats rather than mandatory Heart destruction, allowing a deliberate preserve-and-study route;
- the Heart now uses Odyssey native analyzable research (`analysisID=160912002`), 2-hour colonist analysis, no mechanitor, no destruction, `canStudyInPlace=true`;
- `WNG_WraithLivingTechnology` keeps `Fabrication` and additionally requires analyzed `WNG_WraithHiveHeart`;
- bio-sludge/Living Forge were rejected as first gates because their ordinary colony production is already behind this research;
- no shuttle/gravship/Growth-Chamber-power coupling was introduced.

### Strategic hunger request UI — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- opens only from genuine faction-level strategic hunger;
- stage 1 force-paused biological prisoner/feeding-stock selection only;
- stage 2 force-paused exact involved-Wraith count/names using real same-faction pawn identities;
- final Submit uses existing acceptance effect; Cancel/Escape uses existing refusal/raid pressure;
- ordinary Drain Life and Mature-Hive local feeding remain separate.

### Growth Chamber — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- powered bounded `WNG_WraithGrowthChamber` using bio-sludge, Queen Life Force and normal RimWorld power;
- links to initialized same-faction Hive Heart, respects exact founding demographic cap and produces Hunter/Warrior replacements only;
- exact pawn registration precedes resource commit.

Explicit Growth-Chamber dependency:
- generated hostile Mature Hive sites still do **not** receive Growth Chambers because current sites have no grounded Wraith electrical-power source. Site placement waits for explicit Wraith ground-power/bioelectric-energy reconciliation; no fake ZPM/Gravcore substitute is allowed.

Still required:
- broader discovery/story progression beyond the now-public Replicator and Wraith first evidence bridges;
- generated-Mature-Hive Growth Chamber placement after real Wraith ground power exists;
- final presentation/audio/live testing.

Ordinary feeding, strategic hunger, mature-Hive ecology and retaliation remain separate systems.

## Craft / Stargate integration

Implemented mechanical foundations include Wraith Dart, Wraith scout/Strike Craft, Wraith Cruiser, Puddle Jumper, **Al'kesh**, Death Glider, Asuran recovery Jumper, Goa'uld transport rings and CatCraft/ONAC/RimGate ownership boundaries.

Still required: Quiet-Lattice/Puddle-Jumper courier, deliberate Ancient/Puddle-Jumper power/fuel abstraction, unloaded-world-site exact-pawn ring transport, live craft/save-load validation and final art/audio.

## Gravships / Goa'uld

Wraith/Asuran Odyssey-native mechanical families and family fuel networks are implemented. Wraith defense is living-hull regeneration; generic Wraith shield reskin is rejected. Asuran uses a real powered shield emitter. Goa'uld Ha'tak/Death-Glider/carrier/orbital-bombardment foundations are public.

Still required/blocked: safe standalone Goa'uld ship material/fuel/research path without ONAC; safely solved hostile Ha'tak native takeoff only if Odyssey ownership permits it; professional hull topology presentation; final art/audio/live testing.

---

# CURRENT REQUIRED UNFINISHED INVENTORY

Broader discovery/story progression remains unfinished. The Replicator and Wraith first encounter/evidence/research bridges are public; do not mark the whole progression system complete.

1. **Broader discovery/story progression** — continue as short evidence/reconstruction bridges, next Asuran/Ancient only.
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

**Reconcile one Asuran/Ancient evidence-to-research bridge only.**

Before code:
- inspect what real Asuran/Ancient evidence is obtainable from existing covert visitors, hostile Lattice encounters, Queen-recovery content, Quiet Lattice interaction and existing structures/items before `WNG_AsuranFabrication`;
- distinguish Asuran nanite-fabrication evidence from later Ancient shuttle engineering; do not gate both together by convenience;
- prefer existing recoverable physical evidence or an already-existing captured/revealed synthetic object over a new timed site;
- ensure the chosen evidence genuinely exists before the research it gates;
- use native Odyssey analysis where coherent;
- checkpoint the exact object/acquisition path before implementation.
