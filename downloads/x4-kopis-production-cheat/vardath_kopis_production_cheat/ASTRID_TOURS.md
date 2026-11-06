# Astrid Tours — Kopis extension v1.13

Adds a separate Astrid-derived yacht named **Astrid Tours**. It does not replace an ordinary Astrid, alter the Forge's special weapon or refit existing ships.

| Setting | Implementation |
|---|---|
| Appearance and mounts | Original Astrid component, cockpit, interiors, storage, two weapon slots and six turret slots. All ten equipment paths were checked against published Astrid component data. |
| Speed | Dedicated engine forward thrust 2,415 → 7,245, with original forward drag 3.155 and travel multiplier 12 retained: 3× nominal cruise/travel speed relative to that native baseline. Equipment mods/engine updates can change measured values. |
| Handling | Lower mass and angular inertia, lower angular drag, faster jerk response, stronger reverse thrust and rapid travel/boost release. |
| Three-second stop | Scoped player flight-assist controller notices zero translation/rotation throttle input, ends travel, sets throttle zero, and clamps remaining linear velocity to zero after 2.5 game seconds. Poll interval is 0.1 second. It never holds velocity constant afterward. |
| Primary weapons | Two dedicated Astrid laser copies; damage 82 → 82,000, exactly 1,000×. |
| Turrets | Six dedicated Astrid beam turret copies; damage 160 → 160,000, exactly 1,000×. |
| Ownership and crew | Player-owned, Yaki-selected captain plus a custom Yaki service/marine crew definition. |
| Replacement | Every in-game minute, checks all player-owned ships for this exact custom macro. If none exists, spawns one near the player's ship. Sold/destroyed Tours can be replaced. Ordinary Astrid replacement remains separate. |

The stop controller operates only when the player pilots Astrid Tours, flight assist is enabled, autopilot/match-speed are off, boost is not being held and all six flight axes are released. Autopilot and AI occupation orders retain native navigation. It does not alter other ships, control bindings or turret modes. Its 2.5-second deadline plus poll interval targets a stop within three game seconds; that bound has not been measured in a running X4 session.

Install the updated Kopis extension normally and load the existing save. Within the next in-game minute, Astrid Tours should spawn if not already owned. No new game is required by the new cue. The default loadout explicitly names its custom engine, both custom weapons and all six custom turrets, rather than relying on faction equipment selection.

## Source and validation

The Astrid component/layout and base macro were inspected from the unmodified native reference retained in [Shuul/VRO's Astrid file](https://github.com/Shuul/VRO/blob/40766687fab2498761d9033a336b792469c726a4/extensions/ego_dlc_pirate/assets/units/size_m/macros/ship_gen_m_yacht_01_a_macro.xml), cross-checked against [published extracted component data](https://github.com/Valandur/x4-data/tree/fc9b55744b7150ada066f88ef1153636312a86c8/docs/en/macros/ship_m/ship_gen_m_yacht_01_a_macro). No VRO balance replacement or VRO dependency is included. Native 2026 Astrid engine/weapon/projectile references were inspected in [the extracted DLC files](https://github.com/ArtByunex/x4-foundation-artbyunex/tree/e3e8a345e5624db118bff3eb171b60b0993fcc2c/extensions/ego_dlc_pirate/assets). New equipment/projectiles have their own IDs and use the required installed DLC's components/effects.

Checked: XML parsing; documented MD command attributes; new macro/index/loadout links; all equipment paths; separate 3× thrust and 1,000× damage values; ZIP/source consistency. Original Forge weapon assets, its hull/component and weapon-recovery MD scripts remain byte-for-byte unchanged.

Unverified: actual game loading, mount installation, damage, measured speed/handling, stop timing, respawn, crew selection, save/load and interaction with the installed DLC/mod set. Test in an existing manual-save copy: inspect the spawn's two guns/six turrets, attain full travel speed, release controls with flight assist on, time the stop, save/reload, then sell the Tours and wait for replacement. Confirm unrelated ships and the Forge weapon remain as before.

Version 1.13: Astrid Tours has 32 people berths. New replacements use 50% crew fill, leaving room for a ten-passenger tour. Existing crew are retained; the expanded capacity also gives existing copies free passenger space. The Forge hull, its special weapon and weapon-recovery scripts are unchanged.

1.14 repair: brake polling first checks `player.occupiedship.exists`, so walking on a station or having no occupied ship does not evaluate ownership on null. Other brake behavior, equipment and crew are retained. Runtime retest remains pending.
