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

**`f2b9c0b3c7ac6ac440dd80d715d44f47a0981973` — `docs: record validated Queen sovereignty build`**

Important recent state-changing commits after the canonical-ledger snapshot include:

- `647fa984a6383a7fa85ec753c5393294f45fe728` — Ha'tak heavy plasma battery;
- `0ce8830238eb5844208084dc5f4565b9aaa7333c` — real Ha'tak Death Glider fighter;
- `ef04575fb88ed6300b7c681c32971eec0c98d253` — exact System-Lord/Jaffa Death Glider strikes;
- `9c78be450aebedbc94b6e279bbd761c91bc63baf` — landed hostile System-Lord Ha'tak carrier site;
- `f2becbde25bf58e5e026d5ee5270ce8c5d08f2c3` — true cross-map/orbital Ha'tak bombardment and full-RimWorld-DLC dependency correction;
- `1184456f8dc7719a6d129e20baf6bc3d575b0a67` / `79d4cb2d5e7a6404a33f5be052f29e457d222e80` / `d50637fa34e16631fa87874015f63221992ffcc3` — human-form Replicator/Asuran nanite-physiology foundation, corrected xenotype UI Def and same-tick starvation reconciliation;
- `e0aedd036fc9ad041b1f07eee25cf4acbd5d38f6` through `442800f3bd84de018c47403ec50663252a60b7c5` — exact Replicator Queen vault/release and hardened physical four-operative Asuran recovery/capture layer;
- `f2b9c0b3c7ac6ac440dd80d715d44f47a0981973` — validated genuine exact-Queen sovereign block-Replicator control, controller-domain persistence and hierarchy integration.

The old ledger statements that Ha'tak, human-form Replicators, the exact Queen or Queen sovereignty were absent are historical snapshot state only.

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

## Block Replicators — CURRENT

Current public source/Defs contain the fresh block-Replicator ecology: hierarchy and genuine split/recombine behavior, specialist roles, cumulative material/adaptation state, assimilation and physical map-cell consumption, regeneration/EMP suppression, retaliation, dangerous loose blocks, containment, population limits, salvage/matter economy and Child's Toy foundations.

Block Replicators **do not gain a food/hunger system**. Their stored matter remains the separate reproduction/construction/adaptation economy.

Queen sovereignty is now a real block-state layer:

- every WNG block body inherits `CompReplicatorSovereignty` from `WNG_ReplicatorRaceBase`;
- authority domains are explicitly distinguished as `None`, `Queen`, future `NeuralLattice`, and future `TemporaryAsuran`;
- one controlled block stores the exact controller pawn reference, pre-control faction, control faction, save-persistent domain key and optional expiry state;
- the exact Queen changes the real target block pawn to her faction rather than applying a passive stat aura or outbreak modifier;
- ordinary Asurans do not gain Queen authority merely by sharing `WNG_NaniteHumanoid` physiology;
- Queen control remains valid only while controller and block are physically together on the same map or in the same caravan;
- invalid authority releases and restores the prior faction when possible, otherwise the real autonomous Replicator-swarm faction;
- EMP disruption and active Replicator containment block acquisition/commands and place controlled blocks into a dedicated non-combat suppression job;
- that suppression node has priority above queued/player orders in the Replicator ThinkTree;
- Queen-controlled blocks expose dedicated move, attack, specialist repair/breach, explicit recombine and release commands rather than pretending vanilla mechanitor control exists;
- the Queen exposes exact-target control, bounded nearby-swarm seizure and release commands;
- current first-build Queen tuning is Def-driven: 40-cell direct control, 24-cell local swarm acquisition and 12 controlled spawned blocks on the Queen's map;
- split children inherit the exact sovereign controller domain;
- upward recombination conserves adaptations, stored matter and authority/domain;
- blocks in different controller domains cannot recombine merely because their faction matches;
- Controller coordination, Repairer support and local retaliation signaling now use the same controller-domain test rather than faction equality alone;
- operational sovereign authority is a valid combat-permission source for future hostile controller domains, while EMP/containment interference removes operational permission.

Still later for block-control integration: Sovereign Neural Lattice bearer control, temporary Asuran lattice intrusion, captured-Queen hostile sovereign consequences and mixed human-form/block threat composition.

## Wraith

Current public source/Defs contain Wraith xenotype/castes/factions; Life Force, Drain Life, regeneration and hibernation; strategic faction hunger; Mature-Hive feeding ecology/retaliation; exact captivity/rescue foundations; living-tech bootstrap; stun staff; native-boardable Dart/scout/cruiser craft; and the Odyssey-native Wraith gravship family with living-hull regeneration.

Ordinary Drain Life, strategic faction hunger, Mature-Hive local feeding and Mature-Hive retaliation remain separate systems.

## Human-form Replicator / Asuran / exact Queen — CURRENT

Current public source/Defs contain a real human-form nanite identity and the exact Queen storyline/control layers:

- non-inheritable `WNG_NaniteHumanoid` xenotype for Asurans/compatible human-form Replicators;
- ordinary Asuran role PawnKinds (`Operative`, `Technician`, `Commander`) kept separate from unique Queen sovereignty;
- hidden hostile `WNG_AsuranLattice` faction foundation;
- human-form Replicator personal matter economy uses RimWorld's **native food system itself**;
- the exact native `Need_Food` runtime class is retained but exposed through WNG as **Nanite Reserve**;
- ordinary edible matter therefore refills the reserve through native eating/caravan/feeding behavior;
- normal Need_Food drain represents ongoing matter consumption by the nanite body;
- self-repair and Asuran workshop assembly spend the **same** reserve directly;
- critical reserve depletion applies WNG nanite-depletion/shutdown effects rather than biological starvation;
- vanilla Malnutrition created by native `Need_Food` is removed on the same pawn tick after needs update;
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
- failed/unprovable departure is halted rather than proxying or silently losing the Queen;
- the exact Queen now receives `WNG_ReplicatorQueenSovereignty`, including maintenance for an existing-save Queen;
- Queen sovereignty is innate to that exact persistent pawn and acts on exact existing block pawns through the real controller-domain/faction system described above.

Still unfinished here: Sovereign Neural Lattice implant control, temporary lattice intrusion, later recurring Queen recovery attacks/consequences, infiltration, and mixed human-form/block sovereign threats.

## Asuran / Ancient-derived technology

Current public source/Defs contain the Asuran nanite workshop/fabrication branch and an Odyssey-native Asuran gravship family with themed native GravEngine/hull/substructure, nanite-sludge fuel family, power/fuel networks, shield and supporting Odyssey equivalents. Puddle Jumper remains a real native-boardable shuttle. The Queen-recovery carrier is a physical Asuran-operated Puddle-Jumper-derived native shuttle using the existing placeholder Ancient/Asuran power abstraction and no generated art.

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

1. **Sovereign Neural Lattice implant** — a non-Queen bearer gets bounded target-specific block control using the now-live controller-domain system; exact controller identity/save-load/split-recombine continuity and domain isolation are required.
2. **Temporary Asuran lattice intrusion** — a separate temporary override with explicit restoration/expiry semantics; it must not become permanent Queen/implant authority.
3. **Later Queen recovery/capture consequences** — recurring recovery operations on the map where the exact Queen physically exists, plus real consequences if the Asuran Lattice retains her.
4. **Mixed human-form/block sovereign threats and infiltration** — suitable future Lattice threats can use genuine controlled block Replicators when authority exists; do not fake this as an outbreak probability modifier.
5. **Hostile Ha'tak world behavior** — genuine takeoff/retreat/pursuit and hostile orbital use only if safe real Odyssey/world mechanics support it; current singleton blocker is recorded above.
6. **Goa'uld sensors/other Odyssey equivalents** only where Stargate function actually justifies them.
7. **Bombardment of otherwise-unloaded settlements/sites** only if map generation/consequences can be handled without pretending damage occurred on a nonexistent map.
8. **Safe standalone Goa'uld resource/research path** when ONAC is absent remains unresolved. Do not invent uranium/chemfuel.
9. **Final Puddle Jumper/Ancient power-fuel abstraction** remains deliberate future work.
10. **Professional final art/audio pass** — dedicated faction assets, all rotation/connection/corner states, Ha'tak/Death-Glider visuals, shield/VFX/audio, Wraith/Asuran production assets.
11. **Broad live RimWorld validation** — source/API/static/CI validation is not live gameplay validation.

---

# NEXT ACTUAL SLICE

After `f2b9c0b3...`, active implementation moves to the **Sovereign Neural Lattice implant control layer**.

Current contract:

- an implant bearer is **not** transformed into or treated as the Queen;
- it must reuse `CompReplicatorSovereignty` and the existing `NeuralLattice` authority domain rather than create an incompatible second control system;
- control is bounded and target-specific, with author-tunable capacity/range/cost/cooldown as appropriate;
- controller identity and domain persist through save/load;
- controlled blocks retain the real hierarchy, adaptations, stored matter, EMP, containment and specialist behavior;
- split/recombine transactions preserve the exact implant-controller domain where valid;
- blocks belonging to different Queen/implant/temporary-Asuran domains must never merge accidentally;
- invalid controller state must release/restore ownership cleanly;
- implant authority must remain mechanically weaker/more bounded than the exact Queen according to the settled design;
- temporary Asuran intrusion remains a later separate override with its own expiry/restoration semantics.

---

# VALIDATION STATUS

Queen sovereignty source/API behavior was checked against RimWorld 1.6 decompiled classes and then compiled through temporary GitHub Actions validation run **34576583840**:

- `Source/WNG/WNG.csproj` build: **SUCCESS**;
- all current Def/Patch XML parsed: **SUCCESS**;
- sovereignty wiring/domain invariants: **SUCCESS**;
- temporary workflow removed after validation.

No claim is made that RimWorld itself has been launched in this environment.

Live validation still required includes Def load, pawn generation, nanite-reserve behavior, Queen vault/casket release, physical four-operative recovery/capture/save-load, Queen acquisition/release commands, block movement/combat/specialist commands, EMP/containment interruption, split/recombine authority inheritance and domain isolation, carrier sites, power/fuel/shields, Death Glider launch/return and orbital targeting/bombardment.

---

# HANDOFF MAINTENANCE

After every meaningful implementation batch:
- update the exact mod HEAD above;
- state exactly what changed;
- move completed requirements out of unfinished state;
- record live-test-needed status honestly;
- derive the next slice from actual current `main`;
- never make Vardath reconstruct already-settled project state from raw chat again.
