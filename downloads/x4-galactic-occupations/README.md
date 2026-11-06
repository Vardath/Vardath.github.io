# Galactic Occupations 0.2.2 — saved-job recovery and Logbook receipts

[Download Galactic Occupations](Galactic_Occupations_0.2.2_DEV.zip) · [All four updated mods](../x4-updates/X4_Job_Recovery_2026-11-07.zip) · [Installation and limits](vardath_galactic_occupations/README.md)

The supplied debug(3).log confirms actual startup/display faults, a rejected optional-presence expression, missing passenger/police values and incompatible restored script stacks. This update fixes those known source causes, keeps infinite behaviours retrying when a worker returns, and provides active-order/missing-equipment messages in the ordinary General Logbook. Ships already switched to Hold Position must have their intended occupation selected again; intentional Hold commands are not overridden.

Verified payments are copied from the actual paid journal into native General Logbook entries titled **Vardath Payment**. The newest twenty recorded payments can be recovered once; their original game time is shown and no money is transferred again. Both income mods share a saved receipt cursor, so they cannot print the same receipt twice. Existing native transaction rows and the data-only text callback remain; the removed income UI is not restored. Protected UI stays enabled.

**Crystal mining is not runtime verified.** Its invalid location display is fixed and unsuitable turrets produce a waiting message while retaining the behaviour. Actual deposits, targeting/hits, dropped items, collection, selling and save/load still require the dedicated in-game test. Static/XML/Lua tests are not evidence those gameplay effects succeed.

The bundle also contains Builders 1.75 (independent payment receipts), Kopis 1.15 (Astrid equipment-use/licence metadata) and Yaki Habitats 1.22 (safe indexed plan inspection to prevent repeated habitat additions). Existing stations/modules, crew, equipment and the Forge special main weapon are preserved. The crash cause cannot be established from the supplied log, which ends during asset loading.
