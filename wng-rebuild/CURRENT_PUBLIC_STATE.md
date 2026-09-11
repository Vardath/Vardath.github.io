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

**`ff4f8dcb7b8ba17760a48a54f616466642189b0c` — `rebuild: complete strategic Wraith feeding request UI`**

Public diff from `e1a080c...` is exactly:
- `Source/WNG/Wraith/WraithFactionHunger.cs` — strategic request flow modified;
- `Source/WNG/Wraith/WraithFeedingRequestDialog.cs` — paused stage-one subject dialog added.

Validation run **`34613728004` — SUCCESS** before clean promotion. Release build, Def/Patch XML and request-flow invariants passed using the corrected small-helper/minimal-workflow validation method. This is source/Def validation, not broad live RimWorld validation.

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
- AntiShield persistent evidence/state + block adaptive-shield countermeasure + native energy-shield integration.

Grav and AntiShield are implemented foundations but still require live-game/save-load tuning and verification.

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
- **complete paused two-stage strategic-hunger feeding-request UI**.

### Strategic hunger request UI — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- opens only from genuine faction-level strategic hunger;
- stage 1 is force-paused and selects/identifies eligible biological prisoner/feeding-stock subjects only;
- no Wraith selection exists in stage 1;
- stage 1 Submit preserves the request lock and advances to stage 2;
- stage 2 is force-paused and shows selected subject plus exact involved-Wraith count and names;
- involved names are real same-faction Wraith pawn identities, never generated presentation-only names: physically present same-faction Wraiths are used when available, otherwise the exact living faction leader;
- if no valid exact Wraith identity exists, the request retries instead of fabricating one;
- final Submit uses the existing exact-prisoner strategic feeding consequence and reduces strategic hunger;
- Cancel/Escape at either stage uses the existing refusal/raid-pressure path;
- ordinary Drain Life, Mature-Hive feeding stock, Dormancy Vault, Growth Chamber and retaliation remain separate.

### Growth Chamber — IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED

- real powered `WNG_WraithGrowthChamber` using current WNG bio-sludge biomass and normal RimWorld power;
- Def-tunable first-build values: 60,000-tick cycle, 60 bio-sludge per replacement, 0.35 Queen Life Force, 4,000W draw, 45/55 Hunter/Warrior weighting;
- only links to initialized same-faction Mature Hive Heart and reads exact founding cap/current living demographic count;
- requires living operational same-faction Queen;
- Hunter/Warrior output only and no production above recorded founding cap;
- exact pawn validates/registers before biomass/Queen cost commits.

Explicit Growth-Chamber dependency:
- generated hostile Mature Hive sites do **not** yet receive the chamber because those sites currently have no grounded Wraith electrical-power source. Site placement waits for explicit Wraith ground-power/bioelectric-energy reconciliation; no fake ZPM/Gravcore substitute was introduced.

Still required:
- broader discovery/story progression;
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

Strategic Wraith hunger count/names UI is removed from missing-required debt because it is public.

1. **Broader discovery/story progression.**
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

# GENUINE NEXT PASS

**Broader discovery/story progression reconciliation only.**

Before code:
- inspect all current public WNG incidents, site parts, discovery/recovery events, research gates and acquisition paths;
- compare them against the retained progression theme `mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery`;
- recover which historical site concepts are still requirements versus reference ideas only;
- preserve Vardath's rejection of old fixed day-20-to-day-84 gating and keep major content reachable in shorter campaigns;
- do not turn the mod into one giant starting research dump or make every eligible event fire together;
- identify the smallest concrete missing progression slice that connects existing public systems without inventing unrelated content;
- checkpoint that exact slice before implementation.
