# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-11**  
Author/final design authority: **Vardath**

# PURPOSE

This is the **mutable live-state supplement** to `CANONICAL_RECOVERY_LEDGER.md`.

The canonical ledger preserves the one-time history reconstruction and its original implementation snapshot. It is intentionally not rewritten to pretend later work existed at ledger creation. This file records what the public rebuild actually contains **now**.

Mandatory recovery rule after a context reset:

1. read `STANDING_RULES.md`;
2. read all of `CANONICAL_RECOVERY_LEDGER.md`;
3. read **this file**;
4. read `WNG_IMPLEMENTATION_CHECKLIST.md`;
5. fetch current public mod `main` and compare it with the HEAD below;
6. if `main` advanced, inspect those commits/files before coding and update this file;
7. then read the active subsystem contract(s) and `PLAN_EXECUTION_PROTOCOL.md`.

Current public `main` always beats stale checkpoint prose.

---

# CURRENT MOD HEAD

Repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

**`d50637fa34e16631fa87874015f63221992ffcc3` — `fix: reconcile nanite reserve starvation tick`**

Important recent state-changing commits after the canonical-ledger snapshot include:

- `647fa984a6383a7fa85ec753c5393294f45fe728` — Ha'tak heavy plasma battery;
- `0ce8830238eb5844208084dc5f4565b9aaa7333c` — real Ha'tak Death Glider fighter;
- `ef04575fb88ed6300b7c681c32971eec0c98d253` — exact System-Lord/Jaffa Death Glider strikes;
- `9c78be450aebedbc94b6e279bbd761c91bc63baf` — landed hostile System-Lord Ha'tak carrier site;
- `f2becbde25bf58e5e026d5ee5270ce8c5d08f2c3` — true cross-map/orbital Ha'tak bombardment and full-RimWorld-DLC dependency correction;
- `1184456f8dc7719a6d129e20baf6bc3d575b0a67` / `79d4cb2d5e7a6404a33f5be052f29e457d222e80` / `d50637fa34e16631fa87874015f63221992ffcc3` — human-form Replicator/Asuran nanite-physiology foundation, corrected xenotype UI Def and same-tick starvation reconciliation.

The old ledger statements that Ha'tak or human-form Replicators were absent are historical snapshot state only.

---

# GLOBAL RIMWORLD CONTENT REQUIREMENT

Vardath explicitly requires WNG 1.6 to depend on the **complete RimWorld DLC set**:

- Royalty;
- Ideology;
- Biotech;
- Anomaly;
- Odyssey.

WNG does not have to force every subsystem to use every DLC, but the rebuild may use the most appropriate native mechanic from any of them. `About/About.xml` declares all five DLCs as hard dependencies.

Third-party Stargate ecosystem mods remain optional unless Vardath changes that:
- CatCraft Stargates!;
- ONAC;
- RimGate - Jaffa, Kree! (Biotech).

---

# CURRENT BROAD IMPLEMENTATION STATE

## Block Replicators

Current public source/Defs contain the fresh block-Replicator ecology: hierarchy and genuine split/recombine behavior, specialist roles, cumulative material/adaptation state, assimilation and physical map-cell consumption, regeneration/EMP suppression, retaliation, dangerous loose blocks, containment, population limits, salvage/matter economy and Child's Toy foundations.

Block Replicators **do not gain a food/hunger system**. Their stored matter remains the separate reproduction/construction/adaptation economy.

Required later branches remain Queen sovereign authority, richer player sovereignty/control and mixed human-form + block threats.

## Wraith

Current public source/Defs contain Wraith xenotype/castes/factions; Life Force, Drain Life, regeneration and hibernation; strategic faction hunger; Mature-Hive feeding ecology/retaliation; exact captivity/rescue foundations; living-tech bootstrap; stun staff; native-boardable Dart/scout/cruiser craft; and the Odyssey-native Wraith gravship family with living-hull regeneration.

Ordinary Drain Life, strategic faction hunger, Mature-Hive local feeding and Mature-Hive retaliation remain separate systems.

## Human-form Replicator / Asuran — CURRENT FOUNDATION

Current public source/Defs now contain a real human-form nanite identity rather than only an abstract reserve gene:

- non-inheritable `WNG_NaniteHumanoid` xenotype for Asurans/compatible human-form Replicators;
- ordinary Asuran role PawnKinds (`Operative`, `Technician`, `Commander`) kept separate from unique Queen sovereignty;
- hidden hostile `WNG_AsuranLattice` faction foundation;
- human-form Replicator personal matter economy uses RimWorld's **native food system itself**;
- the exact native `Need_Food` runtime class is retained but exposed through WNG as **Nanite Reserve**;
- ordinary edible matter therefore refills the reserve through native eating/caravan/feeding behavior;
- normal Need_Food drain represents ongoing matter consumption by the nanite body;
- self-repair and Asuran workshop assembly spend the **same** reserve directly;
- critical reserve depletion applies WNG nanite-depletion/shutdown effects rather than biological starvation;
- vanilla Malnutrition created by native `Need_Food` is removed on the same pawn tick after needs update, because RimWorld ticks needs before genes;
- nanite self-repair is bounded and author-tunable;
- EMP applies persistent lattice disruption and suspends self-repair;
- nanite humanoids are ageless/sterile synthetic bodies in the current first-build physiology;
- the older broad rule saying Replicator consumption can never be survival fuel is superseded **only for human-form nanite bodies**. Block Replicators remain unchanged.

The exact Replicator Queen, sovereign control, capture storyline, infiltration and mixed human-form/block threat logic remain unfinished.

## Asuran / Ancient-derived technology

Current public source/Defs also contain the Asuran nanite workshop/fabrication branch and an Odyssey-native Asuran gravship family with themed native GravEngine/hull/substructure, nanite-sludge fuel family, power/fuel networks, shield and supporting Odyssey equivalents. Puddle Jumper remains a real native-boardable shuttle.

## Stargate / shuttle integration

Current WNG shuttles use the complete native RimWorld/Odyssey player-shuttle stack wherever applicable. CatCraft Stargates! owns its network/dial/direction/iris/receive-buffer mechanics. WNG integrates around it.

Al'kesh remains implemented and required.

## Goa'uld / Ha'tak — CURRENT

The Ha'tak family is now a substantial Odyssey-native gravship branch. Current public content includes:

- `WNG_GoauldGravships` research;
- Goa'uld engine seed converting into Odyssey's exact native `GravEngine` with `Goauld` runtime theme;
- Goa'uld native gravship substructure;
- hull seed converting into exact native `GravshipHull` with Goa'uld runtime theme;
- pel'tac using native `CompPilotConsole` behavior;
- ONAC liquid-Naquadria tanks and fuel network;
- directional native gravship thrusters;
- gravitic field projector;
- native Odyssey energy shield;
- naquadah power core and native power network;
- heavy plasma battery for local gravship combat;
- real two-seat native-shuttle Death Glider with ONAC fuel, exact loaded crew, physical staff-cannon attack passes, return-to-deck behavior and hacking/capture;
- bounded hostile Death Glider strikes bound only to verified existing Apophis/Anubis/Ra factions and exact RimGate Jaffa PawnKinds;
- real landed hostile Ha'tak carrier site built from the exact native GravEngine/GravshipHull plus actual Goa'uld WNG facilities, exact Jaffa defenders and physically parked crewed Death Gliders;
- bounded defensive Glider sorties from the carrier deck;
- true player-controlled cross-map/orbital bombardment from the exact physical heavy plasma battery when it is powered, on connected Goa'uld substructure, and the source map is Odyssey `Orbit`;
- orbital targeting selects a different generated Surface-layer `MapParent`, then an exact impact cell on that target map;
- the target receives Royalty's exact native `Bombardment` Thing, configured from author-tunable WNG Def values;
- no same-map turret shot/local explosion is relabeled as orbital fire.

ONAC/RimGate ownership is preserved. Do not create duplicate Goa'uld/Jaffa factions or duplicate `ONAC_LiquidNaquadria`.

### Hostile Ha'tak takeoff blocker — VERIFIED NATIVE BOUNDARY

Odyssey's real gravship generation/travel path was inspected before attempting hostile takeoff.

`GravshipUtility.GenerateGravship` writes the generated traveling gravship into the singleton `Current.Game.Gravship`, and the native traveling `Gravship` restores itself through that same player-oriented singleton on load. Although faction ownership itself can survive through `gravship.Engine.Faction`, driving a hostile System-Lord Ha'tak through this singleton risks overwriting/corrupting the player's current gravship state.

Therefore hostile Ha'tak takeoff/retreat/pursuit is **not** claimed implemented and must not be faked by deleting the real carrier and spawning an abstract proxy. Revisit only if a safe native/world-state separation is found.

---

# CURRENT REQUIRED UNFINISHED BRANCHES

These remain required unless Vardath changes them:

1. **Exact Replicator Queen / Asuran recovery layer** — persistent exact Queen, real cryosleep release, immediate recruitment, four-operative Asuran recovery attack, physical exact-pawn capture/escape semantics, later sovereign consequences.
2. **Human-form Replicator/Asuran infiltration + Neural Interface + sovereign control**, including mixed human-form/block integration.
3. **Hostile Ha'tak world behavior** — genuine takeoff/retreat/pursuit and hostile orbital use only if safe real Odyssey/world mechanics support it; current singleton blocker is recorded above.
4. **Goa'uld sensors/other Odyssey equivalents** only where Stargate function actually justifies them.
5. **Bombardment of otherwise-unloaded settlements/sites** only if map generation/consequences can be handled without pretending damage occurred on a nonexistent map.
6. **Safe standalone Goa'uld resource/research path** when ONAC is absent remains unresolved. Do not invent uranium/chemfuel.
7. **Final Puddle Jumper/Ancient power-fuel abstraction** remains deliberate future work.
8. **Professional final art/audio pass** — dedicated faction assets, all rotation/connection/corner states, Ha'tak/Death-Glider visuals, shield/VFX/audio, Wraith/Asuran production assets.
9. **Broad live RimWorld validation** — source/API/static reasoning is not live gameplay validation.

---

# NEXT ACTUAL SLICE

After `d50637fa...`, active implementation moves to the settled **Replicator Queen / Asuran recovery foundation**.

Current contract:
- one exact persistent female human-form Replicator Queen;
- age **13** in the current first-build design;
- uses the nanite-humanoid identity, not a block-machine race;
- held in a real RimWorld cryosleep/cryptosleep chamber at the recovery site;
- opening/releasing the casket recruits the exact Queen immediately;
- release triggers a hostile Asuran/Lattice recovery operation after a bounded tunable delay;
- current recovery team is four human-form Asuran operatives;
- they prioritize/subdue the exact Queen rather than generic destruction;
- downing or picking her up does **not** commit capture;
- capture commits only when a hostile carrier physically exits the map with the exact Queen;
- interrupting escape leaves her recoverable/player-owned;
- later recovery raids may target any player map where the exact Queen is physically present;
- sovereign Queen authority over block Replicators is a later concrete layer and must be genuine control state, not a statistical outbreak modifier.

---

# VALIDATION STATUS

Current work has been source/API checked against RimWorld 1.6 classes and Def patterns. No claim is made that RimWorld itself has been launched in this environment.

Live validation still required includes Def load, pawn generation, nanite-reserve need replacement, native eating/caravan behavior, same-tick Malnutrition removal, reserve-funded repair/fabrication, EMP suppression, Asuran faction/PawnKind generation, carrier sites, power/fuel/shields, Death Glider launch/return, orbital targeting/bombardment and save-load.

---

# HANDOFF MAINTENANCE

After every meaningful implementation batch:
- update the exact mod HEAD above;
- state exactly what changed;
- move completed requirements out of unfinished state;
- record live-test-needed status honestly;
- derive the next slice from actual current `main`;
- never make Vardath reconstruct already-settled project state from raw chat again.
