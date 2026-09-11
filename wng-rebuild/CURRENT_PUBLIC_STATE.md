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

**`442800f3bd84de018c47403ec50663252a60b7c5` — `docs: record hardened Queen recovery contract`**

Important recent state-changing commits after the canonical-ledger snapshot include:

- `647fa984a6383a7fa85ec753c5393294f45fe728` — Ha'tak heavy plasma battery;
- `0ce8830238eb5844208084dc5f4565b9aaa7333c` — real Ha'tak Death Glider fighter;
- `ef04575fb88ed6300b7c681c32971eec0c98d253` — exact System-Lord/Jaffa Death Glider strikes;
- `9c78be450aebedbc94b6e279bbd761c91bc63baf` — landed hostile System-Lord Ha'tak carrier site;
- `f2becbde25bf58e5e026d5ee5270ce8c5d08f2c3` — true cross-map/orbital Ha'tak bombardment and full-RimWorld-DLC dependency correction;
- `1184456f8dc7719a6d129e20baf6bc3d575b0a67` / `79d4cb2d5e7a6404a33f5be052f29e457d222e80` / `d50637fa34e16631fa87874015f63221992ffcc3` — human-form Replicator/Asuran nanite-physiology foundation, corrected xenotype UI Def and same-tick starvation reconciliation;
- `e0aedd036fc9ad041b1f07eee25cf4acbd5d38f6` — first exact Replicator Queen / physical Asuran recovery implementation;
- `54cb2d5fc539fd1f49e20c9b03fc535e056215c5` / `0f0868eb0467c493b5ad5c16fa8e169ea675fb38` / `442800f3bd84de018c47403ec50663252a60b7c5` — hardened Queen release identity, exact all-or-nothing four-operative recovery and nonlethal recovery-job semantics, with checkpoint reconciliation.

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

Required later branches remain genuine Queen sovereign authority, richer player sovereignty/control and mixed human-form + block threats.

## Wraith

Current public source/Defs contain Wraith xenotype/castes/factions; Life Force, Drain Life, regeneration and hibernation; strategic faction hunger; Mature-Hive feeding ecology/retaliation; exact captivity/rescue foundations; living-tech bootstrap; stun staff; native-boardable Dart/scout/cruiser craft; and the Odyssey-native Wraith gravship family with living-hull regeneration.

Ordinary Drain Life, strategic faction hunger, Mature-Hive local feeding and Mature-Hive retaliation remain separate systems.

## Human-form Replicator / Asuran — CURRENT

Current public source/Defs contain a real human-form nanite identity and the first exact Queen storyline layer:

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
- the older broad rule saying Replicator consumption can never be survival fuel is superseded **only for human-form nanite bodies**. Block Replicators remain unchanged;
- one exact persistent female Replicator Queen is generated at fixed age 13 with `WNG_NaniteHumanoid` identity;
- the Queen is physically held in RimWorld's real `CryptosleepCasket` at a neutral precursor-vault world site;
- only the Dormant exact Queen physically emerging on that vault map triggers release/recruitment, preventing later map transitions from replaying release or resetting the recovery timer;
- release immediately makes that exact pawn a player pawn and globally schedules the first Asuran recovery operation;
- the recovery attempt requires the complete configured team — currently exactly four human-form `WNG_AsuranOperative` pawns — or rolls the partial spawn back and remains eligible to retry;
- recovery operatives are generated without ordinary weapons and use dedicated subdue/load/hold jobs with damage override disabled, rather than switching into generic lethal raid AI;
- one operative non-damagingly subdues the exact Queen with RimWorld's real `StunHandler`, physically carries her to a real Asuran recovery Jumper, and transfers her into its native transporter;
- surviving operatives physically board that same Jumper;
- capture does **not** commit on stun, down, carry or loading;
- capture commits only inside WNG's native `PassengerShuttleLeaving.LeaveMap()` hook when the exact Queen is still physically present in the exact departing transit container;
- successful departure registers that same pawn in the exact Asuran faction's native `KidnappedPawnsTracker` and marks the global Queen state `CapturedByAsurans`;
- failed/unprovable departure is halted rather than proxying or silently losing the Queen.

Still unfinished here: genuine Queen sovereign control of block Replicators, later recurring recovery raids/consequences, Neural Lattice implant control, temporary lattice intrusion, infiltration and mixed human-form/block sovereign threats.

## Asuran / Ancient-derived technology

Current public source/Defs also contain the Asuran nanite workshop/fabrication branch and an Odyssey-native Asuran gravship family with themed native GravEngine/hull/substructure, nanite-sludge fuel family, power/fuel networks, shield and supporting Odyssey equivalents. Puddle Jumper remains a real native-boardable shuttle. The Queen-recovery carrier is a physical Asuran-operated Puddle-Jumper-derived native shuttle using the existing placeholder Ancient/Asuran power abstraction and no generated art.

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

1. **Replicator Queen sovereign control** — genuine exact-Queen authority over appropriate block Replicators, with explicit ownership/control state rather than a statistical outbreak modifier.
2. **Human-form Replicator/Asuran infiltration + Neural Interface / Sovereign Neural Lattice**, temporary lattice intrusion and mixed human-form/block integration.
3. **Later Queen recovery/capture consequences** — recurring recovery raids on the map where the exact Queen physically exists, Asuran retention/recruitment consequences and mixed Asuran + sovereign block threats.
4. **Hostile Ha'tak world behavior** — genuine takeoff/retreat/pursuit and hostile orbital use only if safe real Odyssey/world mechanics support it; current singleton blocker is recorded above.
5. **Goa'uld sensors/other Odyssey equivalents** only where Stargate function actually justifies them.
6. **Bombardment of otherwise-unloaded settlements/sites** only if map generation/consequences can be handled without pretending damage occurred on a nonexistent map.
7. **Safe standalone Goa'uld resource/research path** when ONAC is absent remains unresolved. Do not invent uranium/chemfuel.
8. **Final Puddle Jumper/Ancient power-fuel abstraction** remains deliberate future work.
9. **Professional final art/audio pass** — dedicated faction assets, all rotation/connection/corner states, Ha'tak/Death-Glider visuals, shield/VFX/audio, Wraith/Asuran production assets.
10. **Broad live RimWorld validation** — source/API/static reasoning is not live gameplay validation.

---

# NEXT ACTUAL SLICE

After `442800f3...`, active implementation moves to **genuine Replicator Queen sovereign authority over block Replicators**.

Current contract:
- sovereignty belongs to the one exact persistent Queen, not to ordinary `WNG_NaniteHumanoid` pawns and not to ordinary Asuran rank;
- it must act on real block-Replicator pawns/state already present in the rebuilt hierarchy;
- it must be genuine control/ownership/command state, not a raid probability modifier, stat aura or decorative label;
- Drone -> Hunter -> Bulwark -> Titan -> Siege Mass and specialist block forms must retain their real hierarchy/split/recombine/matter/adaptation mechanics while under sovereign control;
- command/control must not merge the Queen's personal human-form Nanite Reserve with block Replicators' separate stored-matter economy;
- EMP/containment and existing Replicator physical behavior remain real constraints rather than being bypassed by sovereignty;
- ordinary Asurans must not inherit sovereign authority merely from sharing the nanite-humanoid xenotype;
- any future Neural Lattice/player-control path must integrate with this authority model rather than replace it with a second incompatible system.

---

# VALIDATION STATUS

Current work has been source/API checked against RimWorld 1.6 classes and Def patterns. No claim is made that RimWorld itself has been launched in this environment.

Live validation still required includes Def load, pawn generation, nanite-reserve need replacement, native eating/caravan behavior, same-tick Malnutrition removal, reserve-funded repair/fabrication, EMP suppression, Asuran faction/PawnKind generation, Queen vault/casket release, exact four-operative recovery, physical carrying/boarding/native departure, exact Queen kidnapping/save-load, carrier sites, power/fuel/shields, Death Glider launch/return and orbital targeting/bombardment.

---

# HANDOFF MAINTENANCE

After every meaningful implementation batch:
- update the exact mod HEAD above;
- state exactly what changed;
- move completed requirements out of unfinished state;
- record live-test-needed status honestly;
- derive the next slice from actual current `main`;
- never make Vardath reconstruct already-settled project state from raw chat again.
