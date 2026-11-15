# Local compatibility repairs — 16 November 2026

These are script-only repairs for the installed versions of sixteen third-party mods, including the earlier Yaki Evolution, Pirate Chaos and Conflict, Head Hunter, Crime Has Consequences, Koha and Equipment Mod and Recruit Service repairs, plus this round's ten stale-patch fixes. They are already installed on Steph's PC.

[Download the repair package](Third_Party_Script_Repairs_2026-11-16.zip). Install the original mods separately; this is not a collection of complete third-party mods. Original authors retain credit for their files. This is a local compatibility release, not an upstream release.

Extract the ZIP into a writable folder. Close X4. With Python 3.9+ installed, check supported files first:

```
python install_repairs.py "D:/SteamLibrary/steamapps/common/X4 Foundations"
```

To install:

```
python install_repairs.py "D:/SteamLibrary/steamapps/common/X4 Foundations" --apply
```

Absent mods are skipped. Every affected source file must match a known version or the already-repaired bytes before anything is written; unrecognized Workshop updates stop installation. Active numbered archives are rebuilt without changing other members. Original files are backed up beside the installer before writes. For rollback, restore the backup under the game's extensions folder and remove only the newly created files listed in NEW_FILES.json. Restart X4 after installation. Workshop may overwrite local fixes during updates.

[Detailed compatibility and independent-mod report](../x4-updates/COMPATIBILITY_AND_INDEPENDENCE_2026-11-16.md). The version-checked installer and patch combinations have static/file-level validation; the newest changes still need a fresh gameplay session.
