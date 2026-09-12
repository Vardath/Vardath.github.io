# WNG — MANDATORY IMPLEMENTATION CHECKLIST

Author/final design authority: **Vardath**.

This checklist applies to every WNG implementation, correction, rebuild, integration, balance, art/audio and subsystem review.

# STOP — PLAN FIRST

Do not write/change/delete/rebuild WNG code until the relevant plan slice has been read and reconciled with actual current public source.

Checkpoint files and pass logs were removed on 2026-09-12 by explicit Vardath instruction. Do not recreate or use them.

# A. AUTHORITY GATE

Before implementation confirm:

- [ ] I applied the newest explicit Vardath instruction.
- [ ] I read `STANDING_RULES.md`.
- [ ] I read the relevant sections of `MASTER_PLAN.md` completely.
- [ ] I read every active master-plan append relevant to this slice.
- [ ] I read `CORRECTIONS_LOG.md` for superseding design/process corrections.
- [ ] I used `CANONICAL_RECOVERY_LEDGER.md` only for recovered history/design context and unresolved historical conflicts, not as a competing plan.
- [ ] I understand that public source is implementation truth for what currently exists, while the plan defines what WNG must become.

There are no known-good historical WNG builds. Private/old branches are reference evidence only.

# B. STARGATE LORE / FUNCTION GATE

Before implementation answer:

- [ ] What exactly is this in Stargate?
- [ ] What is it called there?
- [ ] What does it actually do?
- [ ] Who uses/owns it and why?
- [ ] What scale is it?
- [ ] What limitations/interactions matter?
- [ ] What visual/audio/behavioral cues make it recognisable?
- [ ] How has Vardath chosen to represent it in WNG?

If the result would be a generic sci-fi substitute with a Stargate label, redesign before coding.

# C. CURRENT PUBLIC SOURCE GATE

Fetch actual current `Vardath/Wraith-Nanite-Gravtech-1.6` `main`.

Confirm:

- [ ] What is current HEAD?
- [ ] Does the planned feature already exist fully or partially?
- [ ] What do current Defs/source/assets actually do?
- [ ] What recent commits changed the affected files?
- [ ] What related systems depend on the current implementation?
- [ ] What current art/audio/assets belong to it?

Never treat an old “next”, “unfinished”, “rebuild”, “correct”, old branch or old private implementation as proof of present absence.

Never remove an existing required current feature merely because the plan says rebuild/refine it.

# D. COMPLETE FEATURE MAP GATE

Before coding, inventory the whole affected plan slice:

- [ ] every required feature/branch;
- [ ] race/xenotype/caste/PawnKind/faction/backstory identity layers;
- [ ] hierarchy/transformations;
- [ ] resources/economy;
- [ ] research/acquisition;
- [ ] incidents/sites/quests/story progression;
- [ ] exact-pawn/save-load/state requirements;
- [ ] integrations and verified external Def/package IDs;
- [ ] retained/approved assets;
- [ ] author-tunable values;
- [ ] final art/audio/UI hooks that mechanics must leave room for.

No planned item may silently disappear.

# E. NATIVE RIMWORLD / DLC / OPTIONAL-MOD GATE

Before inventing custom code determine:

- [ ] What native RimWorld 1.6/DLC system already performs the function?
- [ ] Can WNG faithfully extend native behavior instead of replacing it?
- [ ] What native classes/Defs/components must remain authoritative for save/load/UI/AI/boarding/gravships/power/fuel/genes/factions/surgery/containment/research?
- [ ] Which part genuinely requires WNG custom logic?
- [ ] Who owns optional Stargate mechanics: CatCraft, ONAC, RimGate, WNG or vanilla?
- [ ] Are external package/Def identities verified from source rather than guessed?

Do not invent fallback resources/fuels/factions merely because integration is inconvenient. In particular, no arbitrary Goa'uld uranium/chemfuel fallback.

# F. IDENTITY / SEPARATION GATE

Confirm the implementation does not collapse distinct systems:

- [ ] Wraith ordinary Drain Life is separate from strategic faction hunger.
- [ ] Mature-Hive local feeding ecology is separate from strategic hunger.
- [ ] Mature-Hive retaliation is separate from both.
- [ ] Wraith castes remain role/PawnKind layers, not accidental separate races.
- [ ] Human-form Replicators/Asurans remain distinct from block Replicators.
- [ ] Block Replicator size hierarchy, specialists, adaptations and controller authority remain distinct layers.
- [ ] Queen, Sovereign Neural Lattice and Temporary Asuran authority remain distinct.

# G. IMPLEMENTATION GATE

Only after A-F:

- [ ] I am implementing the next genuinely unfinished **plan requirement**, not a stale handoff task.
- [ ] I am preserving existing required current behavior unless the plan/new Vardath instruction changes it.
- [ ] Author-tunable design values are centralized/Def-driven where practical.
- [ ] I am not substituting flavor text, a marker, an empty comp or decorative object for a required mechanic.
- [ ] I am not inventing unsupported generic substitutes.
- [ ] Save/load/exact-identity transactions are safe where required.

# H. VERIFICATION GATE

Use only proportionate checks needed for the slice:

- [ ] C# compile/build when relevant;
- [ ] XML/Def/reference sanity;
- [ ] direct API/transaction/state inspection;
- [ ] live RimWorld/save-load/log testing when available/required.

Static validation is not live gameplay validation.

Do not rebuild design-locking anti-regression/release bureaucracy.

# I. RECONCILIATION GATE

Before moving on:

- [ ] Compare the implementation back against the full relevant plan slice.
- [ ] Confirm no planned branch was silently omitted.
- [ ] Confirm no existing required feature was accidentally removed.
- [ ] Record genuine unfinished dependencies in plan/current-state material only where needed.
- [ ] Update corrections if Vardath changed/superseded a decision.
- [ ] Do **not** create checkpoint files, pass logs or numbered-pass diaries.

# MANDATORY WORKING ORDER

**NEWEST VARDATH INSTRUCTION -> MASTER PLAN + ACTIVE APPENDS + CORRECTIONS -> RELEVANT RECOVERED HISTORY -> STARGATE LORE/FUNCTION -> CURRENT PUBLIC SOURCE/ASSETS -> NATIVE/OPTIONAL-MOD MECHANICS -> COMPLETE FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE AGAINST PLAN**

The plan defines the target. Current public source defines what already exists. Nothing else chooses the next feature.
