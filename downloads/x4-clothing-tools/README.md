# X4 clothing: read-only diagnostic pass

This is an asset-inspection helper for the uploaded Terran and Pioneer Blender projects, **not yet a finished clothing mod**. It never saves over the existing .blend originals.

## Use on Windows 10

1. Download **inspect_blend.py** and **audit_clothing.bat** from this directory (via GitHub Raw links). Keep both in the same folder.
2. Put COPIES of the .blend files in that folder. Or drag an existing folder containing the .blend files onto the BAT.
3. Double-click **audit_clothing.bat**. It finds Blender 5.3 or 5.1 under Program Files and opens each .blend read-only in background mode.
4. The batch creates **X4_Clothing_Diagnostics.zip** beside your .blend files. Upload the ZIP to ChatGPT.

The ZIP contains JSON inventories of object types, polygon/vertex counts, body/skirt and bone names, materials, whether textures are packed, skinning vertex groups, bounding boxes and a low-resolution geometric preview. The script also records warnings and process errors; preview rendering is optional and failures do not alter originals.

## Scope of intended final mod

Terran and Pioneer formal dresses: remove decorative lower bands, shorten hem to above the knee, remove sleeves, and reconstruct/expose skinned arms and legs as needed. Retain both race colour variants, armature, rigging and existing save references.

A proper mesh edit needs inspection of real 3D geometry, body occlusion, materials and weights. It must not be faked by deleting polygons or changing XML alone. X4 XAC Tools can build Replace Body mods after the model is edited in Blender, according to its documentation: https://github.com/ToffelsKater/x4-xac-tools

The direct .blend uploads are intact; the temporary processing environment in this chat session was unavailable when this utility was authored, so **none of the uploaded models has yet been loaded or modified**. The tool enables user-side inspection using the Blender installation already present.

## Safety

- No writes to the original .blend files and no X4 save changes.
- Only JSON, PNG and a ZIP are created in the output folder.
- Output PNGs are geometry previews; they may not reproduce in-game textures.
- Blender 5.3 is the installed version, but the XAC add-on's official import/export support states Blender 5.1. This report uses only Blender's built-in Python API and does not run the XAC exporter.
