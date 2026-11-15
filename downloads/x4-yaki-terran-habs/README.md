# Current installed release — 16 November 2026

[Vardath - Yaki Terran Habitats: download current release](vardath_yaki_terran_habs_latest.zip)

Content version: **123**. This ZIP and the source folder match the verified local installation. No other Vardath mod is required.

External dependencies: Cradle of Humanity (required)

[Exact file checksums and requirements](CURRENT_RELEASE.json). [Compatibility and independence audit](../x4-updates/COMPATIBILITY_AND_INDEPENDENCE_2026-11-16.md).

Restart X4 after replacing an installed extension. Static checks passed; in-game verification of the newest fixes is pending. Older downloads below are retained for reference.

---

# v1.23 — Direct native construction-plan macro access

The latest log shows a construction entry cannot be materialised as a script variable. The retrofit now uses the native pattern `$CurrentPlan.{$PlanIndex}.macro` directly and schedules no expansion if any entry cannot be read. This closes the repeated-addition risk from a failed plan inspection. Existing stations/modules are not deleted or moved. Runtime confirmation remains pending.

# v1.22 — Existing-plan inspection repair

The supplied debug(3).log rejected foreach iteration over a constructionsequence. The retrofit now reads the existing plan through its supported count/index properties, so already present/planned S/M/L habitats are detected before requesting additions. This prevents a failed scan from treating every size as missing. Existing stations, modules and connections are not deleted or moved. Runtime verification is pending.

# X4: Foundations — Vardath Yaki Terran Habitats

**Separate mod, v1.1 (experimental X4 9.00)**. Requires the **Cradle of Humanity** DLC.

[Download standalone ready-to-install ZIP](./vardath_yaki_terran_habs_v1.1.zip)

Includes new **Yaki Small (100)**, **Medium (250)** and **Large (500)** habitation modules based on Terran habitation geometries. Materials are overridden for a **black hull with crimson panels and red lights**, without changing vanilla Terran modules. Supports **Yaki** station workforce using **Terran MRE and Medical Supplies**. **Version 1.1 equips new-game NPC Yaki wharfs with Yaki M/L habitats and queues an S habitat retrofit for existing Yaki wharfs**; the three blueprints are automatically unlocked.

Extract the `vardath_yaki_terran_habs` directory into your game's `extensions` directory, alongside—not inside—Living Factions & Builders.

[Full implementation, installation and test checklist](./vardath_yaki_terran_habs/README.md)

**Testing:** XML/ZIP integrity only; appearance, crew recruitment, workforce upkeep and blueprint display are not confirmed in-game. Use a backup save.
