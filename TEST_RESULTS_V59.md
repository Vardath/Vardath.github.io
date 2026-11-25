# Independent PE mesh benchmark

The local model resumed DeepThorT's own v58 draft. Two inference calls covered asteroid selection and a full-roadmap correction. Both ran offline using the capped Windows ONNX worker. The installed OpenCode mod was the comparison baseline.

| Evidence | v59 result |
| --- | --- |
| Vanilla PE main hull LOD0 dimensions in native XYZ | 47.051 × 37.796 × 128.107 |
| Vanilla ore candidates measured | 6 |
| Model selection | env_ast_ore_m_05 |
| Selected bounding-box roundness | 0.89202, second of six. The highest was 0.90042. |
| Uniform scale | 0.10838868 |
| Verified resized dimensions in native XYZ | 42.372 × 37.796 × 38.392 |
| Output | 3,930 vertex records and 1,386 triangle faces |
| Native output SHA-256 | 7b58779c65d5745f6945af83b520e23a4f3bf17b91a99ecbd8b6917374c82c4f |

DeepThorT stored one native visual mesh as an intermediate of the full request. The development test exported it through the same export function used by the desktop. The OBJ contains geometry only. The native visual retains its source material assignments.

The next model reply received the new dimensions and repeated the existing ship macro. The validator retained four planned paths with ten open checks. The project folder remained empty. The installed OpenCode comparison contained 24 XML files and 10 XMF files. The v59 workpiece still needs placement, lower levels of detail, a collision mesh, and save-compatible in-game verification.

Regression cases exercise catalog checksums, overlapping chunks, vertex attributes, face indices, project-scoped persistence, invalid model selections and export overwrite protection.
