# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Wraith Growth Chamber reconciliation complete

## Public state

Public mod `main` remains:

**`b5cde48e3cbcb2d608edabc78758e5fe9e4aec39` — native energy-shield AntiShield integration.**

No Growth Chamber code was changed in this reconciliation pass.

## Recovered plan/chat-history requirement

The Wraith subsystem has always retained a dedicated Growth Chamber / cloning branch. The requirement is not generic population spawning:
- support **bounded biological Wraith replacement/growth**;
- caste outcome and resources must be coherent with Wraith biology and Hive ecology;
- no uncontrolled infinite spawning;
- timers/costs remain tunable;
- earlier design specifically described rapid warrior production at **very high biomass and power cost**;
- older visual/history material used a Wraith Growth Pod/Chamber identity, but old code/builds remain reference only.

## Current public architecture inspected

Current Mature Hive generation already creates:
- exact Hive Heart;
- exact active Queen, Keeper, Hunters and Warriors;
- ordinary exact hibernators in Hibernation Pods;
- finite combat reserve in Dormancy Vaults;
- finite exact biological feeding stock in Feeding Niches.

`CompMatureWraithHivePopulation` deliberately records a **founding Wraith population cap** and explicitly says it does not create demographic replacements because Growth Chamber integration is the later replacement layer.

Important existing separation:
- Hibernation Pods preserve existing Wraith; they do not create them;
- Dormancy Vaults are a finite sealed combat reserve and are explicitly outside the demographic replacement pool;
- Feeding Niches hold exact captives/feeding stock;
- Hive Heart is the exact demographic anchor/cap, not a cloning machine.

Current public also has real `WNG_WraithBioSludge` produced from biological feedstock through the Wraith living-tech economy, and current Wraith structures already use ordinary RimWorld power where a gameplay power interface is needed.

## Stargate lore gate

Canon source: SGA **“Spoils of War.”**

Established behavior:
- a Wraith Queen creates a small number of warriors/genetic material;
- a cloning facility reproduces those warriors thousands of times;
- the process uses numerous growth/cloning pods;
- Queen participation is exhausting and she needs to feed afterwards;
- energy requirements are enormous;
- Ancient ZPMs were used to power the facility;
- the facility's purpose was mass **warrior** production, not cloning replacement Queens/Keepers as ordinary output.

Therefore WNG's single-building Growth Chamber is a **RimWorld-scale abstraction of the canon cloning-pod/facility function**, not a claim that one small chamber in the series could independently equal the full planet-side facility.

## Exact WNG first implementation role

**Growth Chamber = bounded mature-Hive Hunter/Warrior demographic replacement facility.**

It is distinct from every existing Hive system.

Required behavior:
- must belong to the same Wraith faction/map as a real initialized Hive Heart;
- must read that Hive Heart's recorded `FoundingPopulationCap` and current `LivingDemographicCount`;
- may only grow replacements while the living demographic count is below that cap;
- first-build output is **Hunter/Warrior only**; it must not manufacture Queens, Keepers or Commanders as routine replacement output;
- must require a living same-faction Wraith Queen on the map as the genetic source;
- each completed growth cycle must impose a real Queen biological cost through WNG Life Force/exhaustion rather than treating Queen participation as free;
- must consume real current WNG biological feedstock (`WNG_WraithBioSludge`) as the biomass abstraction;
- must require substantial power through the existing RimWorld power system as WNG's current first-build abstraction for the canon enormous energy requirement;
- do **not** invent a fake ZPM/gravcore resource merely to satisfy the chamber; Ancient/ZPM-specific power remains a later higher-end integration/progression opportunity;
- cycle time, biomass cost, power draw, Queen Life Force cost and Hunter/Warrior weighting must be Def-tunable;
- no cycle may commit resources and then silently fail to produce a valid exact pawn; resource/cycle transaction must fail safely;
- generated replacement must be a real exact Wraith pawn of the chamber/Hive faction and be registered into the Hive Heart demographic list before another replacement can be authorized;
- chamber must not use or replenish Dormancy Vault reserve;
- chamber must not consume/replace Feeding Niche captive identities directly; bio-sludge is the production input abstraction;
- chamber must not modify strategic faction hunger, open feeding-request UI, perform ordinary Drain Life, or trigger mature-Hive retaliation.

## Queen-loss boundary

If the exact local Queen is dead/missing/downed beyond valid operation, the chamber cannot begin/complete another cloning cycle. Growth Chamber does not create a substitute Queen.

## Population-cap boundary

The current founding cap is the first-build demographic ceiling. The chamber replaces losses **up to that recorded cap** rather than expanding a generated Mature Hive indefinitely. Any later mechanic that deliberately raises a Hive's cap must be a separate explicit progression/design change.

## Exact next pass

**Implement Growth Chamber only** on a fresh public-repo branch from `b5cde48...`:
1. expose a safe Hive Heart registration/replacement API without breaking exact demographic references;
2. add Growth Chamber building/component Def with Def-tunable cycle/power/bio-sludge/Queen-Life-Force settings;
3. find/validate same-map initialized same-faction Hive Heart + living Queen;
4. bound production to `FoundingPopulationCap` and Hunter/Warrior output only;
5. make biomass/Queen-cost/output transaction safe;
6. integrate chamber into Mature Hive site generation as required infrastructure only if the whole generated-site transaction remains all-or-nothing;
7. keep all feeding/hunger/dormancy/retaliation systems separate;
8. Release build + XML/static invariants;
9. checkpoint validated branch before promotion.

---

# PUBLIC MILESTONES

- `26680fe84...` — Temporary Asuran lattice intrusion.
- `9ce7137045...` — recurring exact-map Queen recovery.
- `0b8150f3ff...` — captured-Queen sovereign consequences.
- `8495b846c7...` — Neural Interface / exact reconstruction.
- `c7a9b46a3b...` — infiltration conceal/reveal.
- `87da0e5243...` — covert visitor impersonation.
- `b242dc72d1...` — Quiet Lattice society.
- `45e62cd7f5...` — native WNG backstories.
- `12590e8ea8...` — physical Replicator Grav adaptation.
- `b5cde48e3c...` — native energy-shield AntiShield integration.

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
