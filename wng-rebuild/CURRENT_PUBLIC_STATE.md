# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-12**  
Author/final design authority: **Vardath**

This file is **descriptive only**. It records what current public WNG contains. It does **not** choose the next task and it does not outrank the master plan.

Checkpoint files and the rebuild pass log were removed by explicit Vardath instruction on 2026-09-12. Do not recreate or consult them.

# AUTHORITY

- Target/design authority: newest Vardath instruction -> `MASTER_PLAN.md` + active master-plan append(s) + `CORRECTIONS_LOG.md`.
- Recovered historical/design context: `CANONICAL_RECOVERY_LEDGER.md`.
- Implementation truth: actual current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main`.
- This file: convenience inventory only.

There are no known-good historical WNG builds. Private/old source is reference evidence only.

# CURRENT PUBLIC MOD HEAD

Repository: **`Vardath/Wraith-Nanite-Gravtech-1.6`**

Current public `main`:

**`11f29e2f739c4fda15be04670b97f407bf93291c` — `docs: remove rebuild pass log`**

The immediately preceding documentation cleanup removed the old WNG checkpoint files and rebuild pass log only. The latest gameplay/content change before that cleanup is:

**`da7b659c456563e76a0110877294536eaf26ca37` — `rebuild: restore one-day Replicator Matter dormancy`**

That correction restored the intended **60,000-tick / one full RimWorld day** Replicator Matter dormancy after an immediately preceding mistaken half-day change.

# RECENT IMPLEMENTATION ADVANCES AFTER THE OLD `d38ce6f...` STATE

Public source advanced materially beyond the previous website snapshot. Notable real public changes include:

- `2b86da292...` — validated hostile/covert Asuran nanite-residue evidence -> native analysis -> `WNG_AsuranFabrication` bridge;
- `9b741406f...` — Wraith shuttle/flight progression gated downstream of analyzed Wraith Living Technology;
- `ff6811316...` — native Odyssey pilot-subpersona support preserved for themed gravships;
- `80b5dec4d...` — restored human-form Nanite Reserve injury repair and missing-part reconstruction;
- `5a97e6e78...` — conservative legacy Nanite Reserve save migration;
- `6f3d1bb5a...` — Neural Interface reconstruction made more exact by restoring source genome/appearance before WNG nanite layering;
- `2890e0ae6...` — native airtight Asuran gravship door;
- `957f3a2d6...` — native airtight Wraith living gravship door;
- `e4d723ff8...` — Wraith atmosphere support;
- `b7a4ce8d3...` — Wraith orbital sensor using native Odyssey scanning;
- `1185fbd72...` — Wraith living free-passage vacuum membrane using native vacuum-barrier behavior;
- `1acd5c799...` — Wraith bioelectric gravship power organ using Odyssey native gravcore-power behavior;
- `8a419389a...` / `f92b39aa0...` — native Wraith and Asuran power conduits;
- `7a1de9b11...` / `de1360877...` — explicit gravship-family markers on those conduits;
- `45bd77b0c...` — static verification that existing Replicator hierarchy/split/recombine behavior already matched the required contract; no gameplay rewrite was needed;
- `da7b659c4...` — restored Replicator Matter to one full day of dormancy before hostile reformation checks.

These commits are implementation evidence only. They do not replace the plan.

# IMPLEMENTED FOUNDATIONS — CURRENT PUBLIC SOURCE

## Block Replicators

Public source contains:
- Drone -> Hunter -> Bulwark -> Titan -> Siege Mass hierarchy;
- real downward destruction splitting;
- split-born recombination lockout;
- Controller / Repairer / Burrower / Artillery specialists;
- assimilation/stored-matter economy, dangerous Replicator Matter, bounded growth, EMP, containment, regeneration/retaliation and Child's Toy branch;
- controller-domain inheritance through split/recombine/assimilation offspring;
- Material / Armor / Ranged / Power / Shield adaptation foundations;
- real physical Grav adaptation behavior;
- native projectile/energy-shield AntiShield integration;
- Replicator Matter evidence-analysis progression;
- current dangerous Matter dormancy restored to one full day before reformation checks.

Live-game validation remains required where not already observed in RimWorld.

## Controller / Queen architecture

Public source contains distinct autonomous, exact-Queen, Sovereign Neural Lattice, Temporary Asuran and captured-retained-Queen remote control architectures. Exact Queen vault/release/recovery/capture, real sovereignty, recurring recovery, captured-Queen consequences and mixed sovereign threats have public implementations.

## Human-form Replicators / Asurans

Public source contains:
- `WNG_NaniteHumanoid` / Food-backed visible Nanite Reserve physiology;
- self-repair, missing-part reconstruction, fabrication and EMP disruption;
- hostile Asuran Lattice roles including infiltration;
- Temporary Asuran block intrusion and captured-Queen mixed threats;
- Neural Interface recruit/imprison/Ideology-slave/skill-copy/exact reconstruction paths;
- same-pawn conceal/reveal and covert visitor impersonation;
- Quiet Lattice / `WNG_HumanFormEnclave`;
- generalist / engineer / soldier / coordinator / player human-form roles;
- native WNG synthetic backstories;
- hostile/covert Asuran nanite-residue evidence-analysis bridge into Asuran fabrication;
- legacy Nanite Reserve save migration.

Still subject to plan-driven completion/refinement includes synthetic disease/implant/temperature/vacuum physiology review, friendly Quiet-Lattice/Puddle-Jumper courier behavior, broader live faction/Neural-Interface/infiltration/save-load testing, final presentation/audio and any later plan additions.

## Wraith

Public source contains:
- one Wraith identity/xenotype and Hunter / Warrior / Commander / Keeper / Queen roles;
- pale/white hair handling;
- Life Force, full Drain Life, Partial Feed, regeneration and hibernation;
- Sable Brood / Cinder Court / Veiled Hive / Pale Covenant;
- strategic faction hunger separate from ordinary feeding;
- exact captivity/rescue;
- Feeding Niche / Hibernation Pod / Dormancy Vault / Hive Heart;
- mature-Hive ecology/retaliation foundations;
- living-tech bootstrap and real Wraith Grav Engine path;
- Wraith stun staff and Dart/captivity foundation;
- bounded Wraith Growth Chamber;
- complete two-stage strategic-hunger request UI with involved-Wraith count/names;
- Wraith Hive Heart evidence-analysis gate into Living Technology;
- downstream Wraith flight/shuttle progression tied to that living-tech gate;
- Wraith gravship family mechanics and living-hull regeneration;
- native airtight living door, atmosphere support, vacuum membrane, orbital sensor, bioelectric power organ and native family-marked power conduits.

Ordinary feeding, strategic hunger, mature-Hive local ecology and mature-Hive retaliation remain separate systems.

## Craft / Stargate integration

Mechanical foundations exist for Wraith Dart, Wraith scout/Strike Craft, Wraith Cruiser, Puddle Jumper, **Al'kesh**, Death Glider, Asuran recovery Jumper, Goa'uld transport rings and the CatCraft/ONAC/RimGate ownership boundaries.

Do not remove Al'kesh. Do not invent an arbitrary standalone Goa'uld ship fuel/resource fallback.

## Gravships / Goa'uld

Wraith/Asuran Odyssey-native mechanical families and family fuel/power networks are present. Wraith defense uses living-hull regeneration rather than the rejected generic shield reskin. Asuran uses a powered native shield emitter. Goa'uld Ha'tak/Death-Glider/carrier/orbital-bombardment foundations are public.

Native themed-family door/power/atmosphere support has advanced, but final professional topology/art/audio and broad live construction/fuel/power/launch/save-load validation remain incomplete.

# PLAN-TRACKED UNFINISHED AREAS

This section is not a priority list. The master plan and active appends decide order after current source is checked.

Known unfinished/refinement areas still include, where not superseded by newer Vardath instruction:
- broader discovery/story progression beyond the current Replicator/Wraith/Asuran evidence bridges;
- generated Mature-Hive Growth Chamber placement once real Wraith ground power/bioelectric support is reconciled for those sites;
- friendly Quiet-Lattice/Puddle-Jumper Stargate courier path;
- safe standalone WNG-owned Goa'uld craft/gravship material/fuel/research route when ONAC is absent;
- deliberate final Ancient/Puddle-Jumper power/fuel abstraction;
- unloaded-world-site transport-ring exact-pawn/world-object transport;
- faction-specific professional gravship corner/inside-corner/diagonal/transition presentation;
- final professional craft/gravship/implant/building/weapon/resource art review;
- professional WNG audio layer;
- hostile Ha'tak native takeoff/retreat/pursuit only if safely solvable through Odyssey ownership; never fake it;
- broad current-build live RimWorld/save-load/mod-stack/performance validation/tuning;
- human-form synthetic disease/implant/temperature/vacuum physiology review;
- optional broader DLC identity-copy fidelity review;
- explicit third-party shield integration only for verified external shield systems not already covered by native projectile-interceptor integration;
- approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches only when Vardath advances them.

No item silently disappears. Newer Vardath instructions can add, change, defer or reject items.

# NO NEXT-PASS AUTHORITY HERE

There is intentionally no “genuine next pass” section in this file.

To continue work, read the master plan/appends/corrections, inspect current public source, and choose the next genuinely unfinished **plan requirement**. Do not derive direction from this descriptive inventory alone.
