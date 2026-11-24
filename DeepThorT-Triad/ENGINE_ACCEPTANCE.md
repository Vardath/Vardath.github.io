# DeepThorT v29 — bounded engine-specific acceptance checks

These checks extend v28's exact-source requirement contracts, approved test evidence,
and source-hash verification. They inspect the **actual files already present** in the
selected project. They cannot prove that game mechanics work or that an Android APK
is playable. The user's full specification remains authoritative.

## X4 Foundations extensions

When a project contains `content.xml`, DeepThorT's read-only audit examines XML files
under `md`, `assets`, `libraries`, `index`, `aiscripts`, `maps`, and `t` (bounded to
256 XML files). It checks XML syntax and blocks DTD/entity declarations, missing
extension `content/@id`, unexpected MD and index roots, duplicate or incomplete
index entries, and broken **explicitly extension-local** macro/component paths.
For an index entry like `extensions/<actual folder name>/assets/...`, it checks
that the target exists and declares the registered macro/component name.

The folder name used by an index is not necessarily the `content.xml` mod ID.
References to base-game or other-extension assets remain **unverified external
references**, not falsely reported missing local files. Diff patches cannot be
validated against the installed game without extracted vanilla source/schema.
The audit does not test weapon DPS, ship connectors, crew, MD timing, player-only
scope, save compatibility or in-game spawning. It does not execute X4.

On a project with no Python tests, the existing **Verify build** button offers a
user-approved static X4 audit. With Python tests present it prefers approved tests
and also performs the read-only X4 audit before recording success. The resulting
evidence is explicitly classified `x4_static_xml_passed` or `python_tests_passed`,
**never in-game verified**.

## Godot and Android

Existing `project.godot` projects are checked for a local main scene and for local
`res://` paths in the corresponding scene and scoped `.tscn`/`.tres` files. The
Android export-preset declaration is reported as configuration only: an APK is
**not** built or proven runnable. Unresolved Godot UID references are labelled
unverified; they are not guessed.

If `addons/gut/gut_cmdln.gd` exists and real `test_*.gd` scripts with `test_`
functions are present in `test` or `tests`, the pre-existing approved verifier
selects a headless GUT invocation (`-gdir`, `-ginclude_subdirs`, `-gexit`). Its
captured result must include a positive, complete passing-test summary and no
script error; an exit code of zero alone is insufficient. Without the installed
test runner, Godot's existing editor-load verification remains labelled
`editor_load_only`, **not a gameplay test**.

For standalone Android Gradle projects, `AndroidManifest.xml` files in known
local paths are parsed and checked for a `<manifest>` root. Kotlin/Java test files
that the model explicitly links to `REQ-N` can be checked for test annotations.
This does **not** run Gradle, download an SDK, compile an APK, or assert device
compatibility. Those activities still require authorized engine/tool integration.

## Source evidence, scope and commands

Engine reports include a SHA-256 for every source file read. Approved verification
snapshots record those hashes, including relevant index files that might not belong
to the current milestone. Later changes invalidate previously accepted evidence.
Missing planned files are pending; real errors in existing files block milestone
verification. Missing external/vanilla content remains an explicitly stated limit.
The existing **Approve plan & queue** and **Verify build** actions still require
human confirmation; no script/tool/install is run as a side effect of discovery.

Read-only CLI (does not execute project code):

```powershell
python -m deepthort_local.engine_acceptance "D:\x4mods\my_extension"
python -m deepthort_local.engine_acceptance "D:\games\faction_command" --plan "D:\games\plan.json"
```

Exit code 0 means no *confirmed static* errors; exit 2 means a confirmed static
error. Inspect `issues`, `pending`, `observations`, `source_hashes` and
`acceptance_confirmed: false`. This tool is bounded to keep gaming-resource usage
low; exceeding its safe file count is a reported error, not a silent partial pass.

## Tests and limitations

The v29 regression suite uses synthetic X4, Godot and Android fixtures. The
X4 audit checks known local index conventions, but is not a replacement for
Egosoft schema verification or an in-game save test. The Godot tests are only
mock-output and source-level tests in Linux; no real Windows Godot/GUT engine,
X4 installation or Android SDK was available to validate here.

The next acceptance milestone must exercise a real installed engine against a
real test project, then link those results to concrete user requirements.
