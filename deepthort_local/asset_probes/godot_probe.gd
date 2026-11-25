extends SceneTree
# Fixed standalone Godot 4 probe. No selected project scripts are loaded.
func _initialize():
    var args = OS.get_cmdline_user_args()
    if args.size() != 1:
        quit(19)
        return
    var path: String = args[0]
    if path.get_extension().to_lower() == "png":
        var image = Image.new()
        if image.load(path) != OK or image.is_empty():
            quit(19)
            return
        print("DEEPTHORT_ASSET_PROBE " + JSON.stringify({"kind":"image","width":image.get_width(),"height":image.get_height()}))
        quit(0)
        return
    if path.get_extension().to_lower() != "glb":
        quit(19)
        return
    var document = GLTFDocument.new()
    var state = GLTFState.new()
    if document.append_from_file(path, state) != OK:
        quit(19)
        return
    var node = document.generate_scene(state)
    if node == null:
        quit(19)
        return
    var counts = count_meshes(node)
    node.free()
    if counts.x <= 0 or counts.y <= 0:
        quit(19)
        return
    print("DEEPTHORT_ASSET_PROBE " + JSON.stringify({"kind":"mesh","meshes":counts.x,"vertices":counts.y}))
    quit(0)

func count_meshes(node: Node) -> Vector2i:
    var counts = Vector2i.ZERO
    if node is MeshInstance3D and node.mesh != null:
        counts.x += 1
        for i in range(node.mesh.get_surface_count()):
            counts.y += node.mesh.surface_get_array_len(i)
    for child in node.get_children():
        counts += count_meshes(child)
    return counts
