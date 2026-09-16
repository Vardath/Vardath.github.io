# WNG Master Plan Append — Chat-Limit Handoff / Asuran Statue Provenance Correction

Date: **2026-09-16**  
Design authority: **Vardath**  
Status: **NEWEST AUTHORITY FOR ASURAN STATUE MANUFACTURE; D099 REMAINS THE SEALED GAMEPLAY CHECKPOINT UNTIL THIS CORRECTION IS IMPLEMENTED.**

## 1. Why this append exists

A final conversation-history reconciliation was requested at the chat limit. The sealed D099 checkpoint is internally coherent and remains the newest implementation restore authority, but one player-facing design rule has now changed again.

D099 deliberately allowed any suitable pawn/faction with `WNG_PrecursorFabrication`, Art Bench access, Artistic skill and materials to manufacture the three trap statues. Vardath's newest explicit instruction supersedes that rule:

> **The trap statues may be traded, but they can only be made by Asurans.**

Do not rewrite D099 history or alter its sealed archive. Implement this as the next bounded correction on top of D099.

## 2. Current required statue family

Three distinct Asuran trap-statue identities remain required.

### Sleeper / awakening statue
- remains a tradeable Asuran artifact;
- hidden danger begins only on first actual map placement;
- first placement rolls one save-persistent random **5–60 day** deadline;
- when mature and physically placed, the statue becomes one hostile human-form Asuran/Replicator pawn;
- minification after activation preserves the exact deadline but prevents awakening until re-placement;
- it does not also feed prisoners or release a Replicator swarm.

### Dark-feeder statue
- remains a tradeable Asuran artifact;
- never becomes a pawn;
- first placement rolls/initializes the **5–20 day** feeding cycle;
- only installed low-light/dark time advances the cycle; bright light pauses it;
- minification preserves and pauses accumulated progress;
- when mature, it may consume a suitable nearby flesh pawn and leave recoverable existing Asuran nanite slurry/residue;
- deliberate placement in a dark prison with captives as feedstock is intended gameplay;
- after feeding, the statue remains and begins another cycle;
- it does not later awaken as an Asuran.

### Replicator reliquary
- remains a separate tradeable Asuran artifact;
- first placement rolls one save-persistent **5–60 day** release deadline;
- when mature and physically placed, the exact statue is consumed and releases **exactly five real hostile autonomous Replicator Drones** sharing one autonomous domain;
- pre-commit placement failure must preserve/restore the statue rather than partially releasing a swarm;
- minification preserves the deadline and defers release until re-placement;
- it is not also a feeder or human-form sleeper.

## 3. Manufacture provenance — newest rule

All three statues must be **Asuran-manufactured**.

Player-facing requirement:
- trade availability through the Quiet Lattice / appropriate Asuran artifact trader remains valid;
- if player manufacture is exposed, the actual worker performing the manufacture must satisfy the project's current Asuran identity contract;
- ordinary human, Wraith, Jaffa, Ancient-affinity, Goa'uld or generic colonist workers must not be able to manufacture the statues merely because the colony owns the research;
- the exact technical worker gate should reuse the current authoritative Asuran identity/xenotype utility rather than inventing a second contradictory list;
- `WNG_PrecursorFabrication`, Art Bench usage and advanced material costs may remain part of the recipe progression, but research alone is no longer sufficient authorization.

This supersedes the D099 statement that there is "no Asuran-worker/xenotype gate."

## 4. Current implementation status at handoff

Newest sealed implementation remains:

`WNGv1-CHECKPOINT-20260916-ASURAN-STATUE-CRAFTING-PLACEMENT-TIMERS-COMPLETE.zip`  
SHA-256 `6301942e6ded7e22ef805a936d094a5172b3e8afa390b0f0ebd4b8f0ba2130bc`

D099 remains valid as a restore point and still owns the accepted first-placement timer behavior. Its only known design debt introduced by the newest instruction is the generic-worker manufacture permission.

Next bounded source slice should therefore be **D100 — Asuran-only statue fabrication provenance correction**, unless Vardath gives a newer priority first.

## 5. Conversation-history reconciliation rule

The recent late-rebuild ideas are already represented in durable planning/continuity: generalized animal containment and comparative xenobiology; Iratus physical attachment, study, pharmacology and Queen restorative; Wraith telepathy and advanced pharmacology; Kassa farming/refining/persistent dependent market; Goa'uld fuel fallback and biochemical drugs; Nish'ta; Hoffan treatment; Wraith retroviral humanization, hybrid stabilisation and feeding-independence therapy; Replicator sovereign swarm deployment and Child's Toy feral release; Whispers/Michael hybrids and derived implants; and the three Asuran statue traps.

Future handoffs must continue the same rule: when Vardath introduces or changes gameplay in chat, record it in durable continuity and the appropriate master-plan layer even if implementation has not yet occurred. When a newer instruction contradicts an older append, preserve historical implementation records and add an explicit superseding decision rather than silently rewriting history.
