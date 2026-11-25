extends SceneTree
# Fixed Godot 4 integration probe. Executes only the declared project scene.
func _initialize():
    call_deferred("run_probe")

func run_probe():
    var args = OS.get_cmdline_user_args()
    if args.size() != 1:
        quit(19)
        return
    var path: String = args[0]
    if not path.begins_with("res://") or not path.ends_with(".tscn"):
        quit(19)
        return
    var packed = ResourceLoader.load(path, "PackedScene")
    if not packed is PackedScene:
        quit(19)
        return
    var scene = packed.instantiate()
    if scene == null:
        quit(19)
        return
    root.add_child(scene)
    current_scene = scene
    for i in range(12):
        await process_frame
        if not is_instance_valid(scene) or not scene.is_inside_tree():
            quit(19)
            return
    var nodes = get_node_count()
    if nodes <= 1:
        quit(19)
        return
    print("DEEPTHORT_SCENE_PROBE " + JSON.stringify({"scene":path,"nodes":nodes,"frames":12}))
    quit(0)
