# Personal Envoy Auto 1.21: provisional compatibility guard

**Reported:** X4 9.00 session `debug(20261114-041309).log`, 14 November 2026.

**Installed plugin:** `ws_3744204222`, Personal Envoy Auto by Shpeck, version `1.21`, timestamp 2026-06-28, extension folder `personal_envoy_auto`. Installed MD path from log: `extensions/personal_envoy_auto/md/personal_envoy_full_crew.xml`.

**Reproducible diagnostic:** The full log contains **2,795** identical errors:

```text
[=ERROR=] 80172.41 Error in MD cue md.Personal_Envoy_Full_Crew.EnsurePermanentCrew: Property lookup failed: $PilotActor
```

First at ~80172.41 game seconds, repeating after that. This confirms that the cue reads an absent property. It does not confirm the trigger, the precise location of the failing expression within the cue, whether a pilot could not be created or whether another mod altered the crew/ship.

The Workshop page advertises a unique personal Envoy and one respawning max-skill mod crew member while preserving player-hired crew. It is important **not** to remove or replace the entire `EnsurePermanentCrew` cue merely to silence errors.

## Overlay in Compatibility Fixes 1.0.7

The optional cross-extension path is exactly:

```
extensions/vardath_compatibility_fixes/
  extensions/personal_envoy_auto/md/personal_envoy_full_crew.xml
```

Inside the nested XML diff, select the one cue `/mdscript/cues/cue[@name='EnsurePermanentCrew']/actions` and use `add pos="prepend"` to execute the following **before** all original actions:

```xml
<do_if value="not $PilotActor?">
  <set_value name="$PilotActor" exact="null"/>
</do_if>
```

If a previously valid actor reference exists, it is preserved. The remaining original actions stay in place. No ship, crew, position, order or camera state is modified by this overlay.

## Critical verification limits

The exact **upstream 1.21** `personal_envoy_full_crew.xml` was **not obtainable** via public GitHub repositories, web indexing or the Steam Workshop page. This patch was **not** actually merged with the installed original. It is only an initial missing-variable guard. Initialising a missing value to `null` may not be sufficient if downstream code assumes a valid NPC actor or if the failing lookup occurs in the cue conditions before its actions. Some original errors may remain or appear with a different form.

The repository validator tests:

- X4's pinned `diff.xsd` accepts the overlay syntax and `pos="prepend"`.
- The selector uniquely matches a **synthetic** expected cue, and fails on a missing cue.
- The guard comes before original actions without modifying or deleting them, or any other cue.
- Optional `ws_3744204222` dependency, no UI/Lua intervention, save-neutral `content.xml`.
- Existing sourced XML compatibility diffs, exact ZIP content, and known upstream partial-coverage report.

These are **not** original-source, native engine, saved-game or actual crew-restoration tests. The static report is intentionally marked `partial`. A green CI only proves these limited checks.

## Runtime test

1. Back up the save and install only the new Compatibility Fixes 1.0.7 ZIP over the existing `extensions/vardath_compatibility_fixes` folder. Keep Personal Envoy Auto installed at its existing location.
2. Confirm both mods are enabled, X4 loads, and the existing Envoy and its legitimate hired crew remain intact.
3. Play through several of the old 2-second maintenance cycles and check the next log for `md.Personal_Envoy_Full_Crew.EnsurePermanentCrew` errors.
4. Verify the mod still maintains exactly one personal Envoy and a replacement mod-created crew member after a legitimate loss, without replacing manually hired crew. Do not intentionally destroy valuable ships on the only copy of a save.
5. If `$PilotActor` errors remain, check whether the patch log says **No matching node**, **Multiple matching nodes** or whether the error now changes to a null actor. That differentiates a selector/load-order issue from an inadequate missing-value guard.

To make a robust, source-verified patch rather than a provisional guard, obtain the installed `personal_envoy_full_crew.xml` from the user's own game directory or Steam Workshop `steamapps/workshop/content/392160/3744204222/` and inspect the full cue, its parent variables and all `$PilotActor` references. A Workshop CAT/DAT archive may need XRCatTool extraction.

Removed Amaterasu is separate and needs no additional patch or reinstallation here.
