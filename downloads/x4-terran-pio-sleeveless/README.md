> **Update — 15 November 2026:** The installable **[Terran and Pioneer Short Skirts v1.0](../x4-terran-pioneer-short-skirts/)** is now available, with four edited and exported body models. Sleeves remain unchanged. Blender and file validation passed; in-game testing is still pending. The sleeveless specification and experimental tools below describe the earlier, unfinished project.

# Vardath — Terran / Pioneer sleeveless shorter dresses

**Status: asset editing and in-game validation blocked; this is an incomplete mod project, NOT an installable clothing-mod release.** This directory holds the source-controlled specification, tools and tests for the final stand-alone X4 extension. It deliberately contains no dummy XAC files and does not modify the base game.

## Requested change

- Replace the Terran white and Segaris Pioneer blue formal dresses with sleeveless versions.
- Remove the lower two or three horizontal skirt bands and reconstruct a clean, shorter above-knee hem.
- Keep the original bodice design, colours and material quality.
- Add genuinely rendered shoulders, upper arms, forearms, hands, thighs and lower legs where the original dress omitted covered body geometry.
- Preserve skin colour, skeleton, bone weights, clipping at the shoulders and hips, UVs, body materials, XAC limits, and existing animation.
- Affect the existing NPC outfits globally rather than asking the player to edit individual characters.
- Preserve the user's current save and character generation; no changes to Terran/Yaki race tables, character group spawning, HeadHunter, Personal Envoy or Protected UI.

## Inputs received

23 Blender projects, including `terran dress 1.blend`, `uniform1.blend`, `uniform2.blend`, `uniformcrew1.blend`, `uniformdiplomat1.blend`, full Terran character variants, and `yishabody.blend` as a potential source of exposed limbs. These projects are uploaded into the ChatGPT conversation, **not redistributed in this public repository**. Their actual mesh content and armature compatibility have not been established, because the local binary-processing runtime failed. Filenames are not evidence of geometry.

## Target / export approach

[X4 XAC Tools](https://github.com/ToffelsKater/x4-xac-tools) 0.6.2 supports X4 9.00 and the Blender 5.1/4.2 LTS import-export pipeline. Use its `Replace Body` mode to generate catalog substitutions for the exact imported uniform XAC paths. It requires an X4 armature, a matching original XAC template, and meshes marked `BODY`; replaced game heads remain unchanged. A valid exported replacement body changes that uniform for all in-game characters which reference it.

A complete deliverable will be a single `extensions/vardath_terran_pio_sleeveless/` extension containing `content.xml`, `subst_01.cat/.dat` for complete replacement .xac files and optional `ext_01.cat/.dat` for added materials/textures. The source-verified `tools/merge_replace_bodies.py` script is intended to combine two or more **already edited/exported** XAC Replace Body catalog outputs. To avoid broken texture references, stage source exports with the same desired Mod ID and reject conflicting assets.

**Do not use the merger on the unedited original character .blend files**. A .blend is not an installable X4 extension, and copying original uniform models back into the game would not shorten the skirt or expose limbs.

## Source-vs-runtime checks remaining

1. Inspect the actual .blend meshes, object names, rig, skin materials, vertices and bodypart omissions. Check if the Yisha body has mesh geometry compatible with the Terran/Pioneer skeleton.
2. Make the mesh changes, rebuild the skin surfaces and weights if needed, and preview front/side and animation poses in Blender.
3. Set Replace Body for the source XAC target and mark the final outfit meshes Body. Export both with X4 XAC Tools 0.6.2.
4. Merge the resulting **individually staged** generated extensions into one ID with `tools/merge_replace_bodies.py`.
5. Validate catalog hashes and target file paths. Test an existing save in X4 9.00, look for missing models, absent limbs, material errors, clipping, and restore the original if needed.

## No claim of a completed playable mod

As of 2026-11-15, the core body geometry has not been edited, and no .xac replacement asset has been exported or tested. The source tools and metadata are not a playable mod and should not be installed as one.

## Automated local Blender build (experimental, not a finished downloadable mod)

The \`build_on_windows.bat\` entry point uses **Blender installed on your own Windows computer** with X4 XAC Tools 0.6.2 enabled. Put the source projects \`terran dress 1.blend\`, \`uniform1.blend\`, \`uniform2.blend\`, \`uniformcrew1.blend\`, \`uniformdiplomat1.blend\` and \`yishabody.blend\` in the same directory as the batch file or any subdirectory. Then run the batch file. The source Blender project files are **not** redistributed by this repository.

The Blender program attempts real face cuts at the hem and on the arm sleeves, transplants weighted arm/leg surface geometry from the Yisha body, exports XAC replacement assets via the installed add-on, and merges the files into a *new* X4 extension. If geometry is unrecognised or bone mappings are incompatible, it deliberately stops instead of installing broken uniforms. This has **not been verified against the uploaded .blend models**, since the local binary-processing runtime was unavailable. It is a best-effort automated builder, **not** a prebuilt playable mod or guarantee of correct in-game visuals. Inspect and compare skin colour and animations, especially for non-Caucasian Terran models, before adopting as final.

Blender 5.1 is preferred. The script does not install Blender, and XAC Tools must be enabled in the Blender version run by the batch file. The generated extension is installed to \`X4 Foundations/extensions/vardath_terran_pio_sleeveless\`, and a ZIP and build report are created alongside the input files. It refuses to overwrite an existing extension.

The GitHub Actions test checks Python syntax and synthetic archive packaging only; a green workflow does **not** establish that character models import, export or render properly.
