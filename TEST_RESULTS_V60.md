# DeepThorT v60 independent PE attachment benchmark

The Windows run resumed the original PE request and its measured ore asteroid in a copy of the v59 planning state. A local Qwen inference selected option 3 from four upper-rear placements with verified surface crossings. Only measurements from the vanilla game and DeepThorT's previous draft entered the selection. Replaying the response against the identical prompt verified the exported release bundle.

| Measurement | Result |
| --- | --- |
| Rock translation in ship coordinates, XYZ | 0.155, 28.975, −52.092 |
| Cockpit, dock, elevator, weapon, turret and engine anchors screened | 16 |
| Shortest screened distance | 3.607 native units, at the nominal rear approach ray from con_engine_01 |
| Overlap of main-hull and fitted-rock boxes, XYZ | 42.681, 13.808, 38.392 |
| New asteroid XMFs | 4 visual levels of detail and 1 collision mesh |
| Original ship geometry files copied byte-for-byte | 259 |
| Registry and definition XML | Independent ship macro, independent component and their two indexes |

The verifier resolved both index entries, checked the macro's component reference, compared every original geometry member against its vanilla catalog bytes, and compared the component XML after removing the new rock connection and restoring the two renamed attributes. The assembled draft contains 270 files, including the measurement report and a ship-space OBJ for viewing the main hull and rock in Blender.

The first bounding-box-only run left the two main visual surfaces apart. The revised solver requires an interior segment/triangle crossing between the actual LOD0 surfaces at every offered position. A separate check on the exported OBJ confirmed contact between the visible rock and main hull.

Screening used the combined axis-aligned bounds of all fitted XMFs. The two-unit clearance threshold is a development heuristic. Cockpit and weapon screening used nominal forward rays, engine screening used nominal rear rays, and docking used a downward ray. Elevators and turrets were screened at their connection points. Articulated geometry, sight cones, firing arcs, actual docking, character walking paths and X4's cooked physics data require further verification. The draft does not generate cooked asteroid JCS data.

The export contains source assets for the geometry milestone. It omits an install manifest and gameplay scripts. The two model versions' persisted results remain distinct: v59 produced a scaled standalone mesh; v60 produced a registered ship component with its own fitted rock geometry. The full planner retained four planned paths and ten open checks in this bounded run.
