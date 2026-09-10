# WNG — Wraith Mature Hive / captivity checkpoint — 2026-09-10

This checkpoint records the current fresh public 1.6 implementation after the Wraith identity/Life Force/faction-hunger foundation. It does not supersede newer Vardath instructions.

## Current implementation repository

`Vardath/Wraith-Nanite-Gravtech-1.6` on public `main`.

Historical Wraith code remains reference evidence only. There are no known-good historical states and no old source was restored wholesale.

## Implemented and verified in this pass

### Exact-pawn captivity registry

Fresh `WraithCaptivityRegistry` stores the exact abducted/captive pawn plus source Wraith lineage. It does not manufacture proxy victims.

Current saved state includes:
- exact Pawn reference;
- captor faction Def name;
- captured tick;
- local feeding-stock flag;
- next rescue-trace tick;
- active rescue-site world-object ID and expiry;
- rescue-attempt count.

The old experimentation / conditioning / enthrallment escalation has deliberately **not** been restored. That branch is not authoritative until reconciled separately against current requirements.

### Feeding Niches / local Mature-Hive feeding ecology

`WNG_WraithFeedingNiche` is a real prisoner bed operating on its exact occupant.

Current behavior:
- requires a valid biological prisoner held by the same Wraith faction;
- registers that exact pawn as local feeding stock;
- current first-build ration cycle is tunable in the Def;
- ages the captive non-fatally and refreshes Life Drained;
- restores Life Force to a bounded number of the hungriest nearby same-faction Wraith;
- Keeper/Queen supervision is required by default;
- does not open or modify strategic faction-hunger UI.

### Mature-Hive population boundaries

Fresh Mature Hive ecology explicitly separates four pools:
1. active demographic Wraith;
2. ordinary exact Wraith sleepers in Hibernation Pods;
3. finite sealed combat reserve in Dormancy Vaults;
4. finite biological feeding-stock prisoners.

Feeding stock never counts as Wraith population. Dormancy Vault defenders are a separate one-way reserve and do not count toward the demographic founder cap.

The Hive Heart records the exact active + ordinary dormant founding Wraith as the demographic ceiling. Growth Chamber replacement is intentionally deferred until the living-tech/resource layer and must later replace losses only within that bounded cap.

### Hibernation Pods

`WNG_WraithHibernationPod` maintains the existing Wraith hibernation Hediff on a real exact Wraith bed occupant. It does not create Wraith, refill strategic hunger or fabricate sleepers.

### Dormancy Vaults

`WNG_WraithDormancyVault` contains a finite saved reserve. Damage or nearby player intrusion can wake Hunter/Warrior defenders in bounded waves. The reserve only decreases and never auto-refills.

### Mature Hive site generation/discovery

Fresh `SitePartWorker_WraithMatureHive` generates an all-or-nothing Hive package:
- Hive Heart;
- 3 Feeding Niches;
- 2 Hibernation Pods;
- 2 Dormancy Vaults;
- active Queen + Keeper + 2 Hunters + 2 Warriors;
- exact ordinary dormant Hunter + Warrior;
- 3 finite exact biological feeding-stock captives.

If any required infrastructure, founder, sleeper, captive, or population-anchor step fails, the generated attempt is cleaned up rather than leaving a partial Hive.

`WNG_WraithMatureHiveDiscovered` creates bounded world sites independently of strategic hunger. Current first-build limit is 2 active Mature Hives globally and no duplicate active site for the same Wraith lineage.

### Mature-Hive retaliation

Fresh retaliation is a separate saved queue keyed by neutralized Mature-Hive site ID and exact source Wraith lineage.

A hostile Mature Hive is considered neutralized only after no hostile active/dormant threat remains on its map. One delayed response is scheduled for that source site. Retaliation does not read or modify strategic faction hunger and ordinary feeding has no path into it.

### Exact-pawn rescue sites

Due captivity traces can create `WNG_WraithHoldingSite` world sites.

The exact abducted pawn is transferred into the SitePart ThingOwner and later spawned on the holding-site map. No `GenStep_PrisonerWillingToJoin` or replacement-pawn generator is used.

A bounded Wraith guard detail protects the captive. Keeper acts as custodian; repeated rescue attempts increase Hunter/Warrior numbers and can add a Commander. Queens are not generated merely as holding-site guards.

A successfully recovered pawn is removed from the WNG captivity ledger only when genuinely returned to player safety. A missed unvisited site returns the same pawn through world-pawn handling and schedules a later trace rather than substituting a different captive.

### Ordinary Wraith raid kidnapping bridge

Vanilla RimWorld remains responsible for the physical down/carry/exit kidnapping sequence. Once a Wraith lineage actually has the exact pawn in its vanilla kidnapped tracker, WNG adopts that exact world pawn into its captivity/rescue lifecycle and removes it from vanilla ransom drift.

This means pickup/downing alone is not treated as completed WNG capture.

## Verification

Each of the following fresh slices passed RimWorld 1.6 C# compilation and Def XML parsing before its temporary verification workflow was removed:
- exact-pawn captivity + Feeding Niche;
- Mature-Hive population/structure foundation;
- Mature-Hive discovery/site generation after correcting the current RimWorld 1.6 `TileFinder.TryFindNewSiteTile` call;
- Mature-Hive neutralization/retaliation;
- exact-pawn rescue/holding sites;
- ordinary Wraith raid kidnap bridge.

No permanent compile/audit workflow is retained.

## Explicit remaining dependencies / next work

### Wraith Dart abduction

Still dependency-recorded rather than faked. Current requirement remains:
- real Wraith Dart flyover/culling passes;
- ray-of-absorption style real abduction;
- exact abductee identity enters `WraithCaptivityRegistry`;
- capture is reversible if the Dart is interrupted/hacked/destroyed before successful withdrawal;
- current first-build intent is two real passes, but pass count remains tunable;
- Dart/craft implementation must be rebuilt in the fresh Wraith craft layer rather than by creating an isolated placeholder vehicle.

### Growth Chamber / Hive replacement

Not yet implemented. Must be reconciled with the fresh living-tech/resource economy and may only replace demographic losses up to the Hive Heart founding population cap. It must not refill Dormancy Vault reserves or create infinite Hive growth.

### Hive Heart repair / bioelectric / biomass economy

Deliberately deferred to the living-technology/resource slice. The current Heart is a population anchor; no obsolete biomass assumptions have been silently restored.

### Experimentation / conditioning / thrall/hybrid branches

Still explicitly unresolved. Old treatment-stage code is historical reference only until current requirements are reconciled.

### Living Forge and Wraith Grav Engine

Next major Wraith technology layer. Must preserve living-host and corpse pathways where currently required and must use the intended **Wraith Grav Engine**, never obsolete `Gravcore` substitution.
