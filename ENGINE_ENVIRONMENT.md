# DeepThorT v30 — real local engine/toolchain preflight (22 November 2026)

This is the next **read-only validation stage** after v29's engine artifact checks.
It does not install software, run an engine, edit the selected project, approve a
build, or declare X4 or Android gameplay correct.

## What it actually does

* The existing **Computer & Tools → Scan this computer** action now reports
  engine prerequisites for the currently selected project, alongside the
  existing hardware and program inventory. The scan occurs on its existing
  worker thread; no new UI controls or unsolicited execution were added.
* For Godot projects it distinguishes a real executable from a directory or
  an installed-application registry hint. It supports a real binary on PATH,
  the already discovered executable, or a user-set `GODOT_EXECUTABLE` path.
  Official `Godot_vX.Y...exe` distributions can be selected explicitly.
  The existing **Verify build** action can use that executable only after
  its normal, explicit confirmation.
* For Gradle/Android projects it locates a real Java executable, an Android SDK
  containing `platforms` and `build-tools`, and an installed Gradle executable.
  This does **not** prove they are compatible or attempt a Gradle build. It does
  not run a project-controlled Gradle wrapper automatically.
* For X4 extensions it checks whether the selected game directory contains an
  X4 executable or paired catalog files, and whether selected extracted XML
  references contain usable vanilla index files. Mere directory existence is
  never a successful installation claim.
* New full macro/component definitions in asset macro/component folders are
  checked against this extension's `index/macros.xml` and
  `index/components.xml` registration. **Diff-only patches** are not treated
  as newly defined assets and do not require new index entries.
* If the user selected extracted vanilla XML, the bounded source linker
  compares explicit `macro/@ref` and `component/@ref` identifiers in project
  assets/MD/libraries against actual extracted vanilla macro/component indexes
  and this extension's own indexes. Unknown IDs remain **unresolved** because
  they could come from DLC, another extension, or missing references. The
  index file hashes and inspected project-file hashes accompany the read-only
  report, but this source-link report is **not** an approved verification
  snapshot or proof of X4 behavior.

## Read-only command-line probes

From `D:\deepthort` on Windows:

```powershell
python engine_environment_cli.py "D:\x4mods\my_extension" --x4-game "D:\Games\X4 Foundations" --x4-reference "D:\deepthort\reference\x4"
python engine_environment_cli.py "D:\games\FactionCommand"
python -m deepthort_local.engine_acceptance "D:\x4mods\my_extension"
```

These commands do not execute X4, Godot, Gradle, or project scripts. Exceeding
bounded XML/index scan sizes is reported, never silently accepted as a full
scan. The toolchain report distinguishes presence from successful invocation.

## Why Windows testing is now needed

The local v30 tests create synthetic installed-engine paths and X4 XML
references. They do not run the user's installed Windows executables, validate
vanilla PE equipment IDs against the actual extracted X4 game, build an APK,
or test the Mission Director spawn in an existing save.

After installing v30, select the X4 mod project, click **Scan this computer**,
then **Export diagnostics**. The resulting log and an actual draft/approved
verification run, when available, will reveal which real tools/sources are
usable and what integration still fails. No new game is required for an
engine-environment scan.

## Safety and limitations

* No new background processes, installs, downloads or GUI controls.
* Inference/plan limits, JANUS/Sentinel, approval, stop, resource limits and
  the user's saved conversations/requirements are unchanged.
* A successful static X4 audit does **not** prove weapon damage, equipment
  compatibility, spawning, player-only ownership or save compatibility.
* A Godot editor-load is not a playable Android game; an Android SDK path is
  not a compiled APK; an unknown vanilla reference is not automatically an error.
* Existing async Tk test teardown issues remain. Release verification uses
  test-module process isolation; report the monolithic crash separately.
