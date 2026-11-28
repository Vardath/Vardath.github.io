"""Reviewed Unity batch-mode scene creation and reopen probe."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.android_emulator import real_file
from deepthort_local.android_game_compilation import run_profile
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-unity-scene-probe-v1'
MARKER='JANUS_UNITY_SCENE_PROBE '
VERSION=r'(?:20[2-9]\d|6000)\.\d+\.\d+f\d+'
SCRIPT='''using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class JanusSceneProbe {
    [Serializable]
    public class Result {
        public string version;
        public string project;
        public string scene;
        public int rootCount;
    }
    public static void Run() {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var obj = new GameObject("JanusProbe");
        obj.transform.position = new Vector3(1, 2, 3);
        const string path = "Assets/JanusProbe.unity";
        if (!EditorSceneManager.SaveScene(scene, path))
            throw new Exception("Scene save failed");
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
        var roots = scene.GetRootGameObjects();
        if (roots.Length != 1 || roots[0].name != "JanusProbe" ||
            roots[0].transform.position != new Vector3(1, 2, 3))
            throw new Exception("Scene reopen assertion failed");
        string root = Directory.GetParent(Application.dataPath).FullName;
        var result = new Result { version = Application.unityVersion, project = root,
            scene = scene.path, rootCount = roots.Length };
        File.WriteAllText(Path.Combine(root, "janus-result.json"), JsonUtility.ToJson(result));
        Debug.Log("JANUS_UNITY_SCENE_PROBE " + result.version);
    }
}
'''

def checked(s):
    if not isinstance(s,dict) or set(s)!={'editor_version'} or not isinstance(s['editor_version'],str) or not re.fullmatch(VERSION,s['editor_version']):
        raise ValueError('Choose exact installed stable Unity editor version')
    return s

def resolve_runtime(root):
    value=os.environ.get('UNITY_EDITOR_EXE')
    if not value:raise ValueError('Set UNITY_EDITOR_EXE to installed licensed Unity.exe')
    exe=real_file(value)
    if exe.name.casefold()!='unity.exe' or exe.is_relative_to(Path(root).resolve()):
        raise ValueError('Use separately installed Unity editor')
    return snapshot_file(exe,kind='stat')

def command(exe,stage):
    return [exe,'-batchmode','-nographics','-quit','-projectPath',str(stage),
            '-executeMethod','JanusSceneProbe.Run','-logFile','-']

def stage_files(s):
    checked(s)
    return {'ProjectSettings/ProjectVersion.txt':'m_EditorVersion: '+s['editor_version']+'\n',
            'Packages/manifest.json':'{"dependencies":{}}\n',
            'Assets/Editor/JanusSceneProbe.cs':SCRIPT}

def assess(s,result,log):
    checked(s)
    if not isinstance(result,dict) or set(result)!={'version','project','scene','rootCount'}:
        raise ValueError('Invalid native scene receipt')
    if (result['version']!=s['editor_version'] or not isinstance(result['project'],str)
        or result['scene']!='Assets/JanusProbe.unity' or type(result['rootCount']) is not int or result['rootCount']!=1):
        raise ValueError('Native editor, scene or root-count mismatch')
    lines=[line[len(MARKER):].strip() for line in log.splitlines() if line.startswith(MARKER)]
    if lines!=[s['editor_version']] or re.search(r'(?im)(?:error CS\d+|Scripts have compiler errors|Scene reopen assertion failed|Aborting batchmode)',log):
        raise ValueError('Missing or failed native editor evidence')
    return {'editor_version':s['editor_version'],'native_scene_reopen_verified':True,
            'build_verified':False,'gameplay_verified':False,'external_project_tested':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:raise ValueError('Missing Unity runtime guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=resolve_runtime(root):raise ValueError('Reviewed Unity runtime changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(resolve_runtime(root))
    return plan,dict(s,command_profile=command(plan['guards'][1]['path'],'<temporary project>'),
        scope='Run trusted licensed Unity batch editor under shared cap on generated temporary project. Compile fixed C# editor script, save and reopen scene, verify root object and transform. Unity may write host caches or use networking; no licence handling, installation, external project execution, build or gameplay.')

def execute(root,plan):
    s,dst=validate(root,plan)
    from deepthort_local.triad_job import verify_root_cap
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap();sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<20:raise ValueError('Insufficient host RAM reserve')
    require_storage(dst.parent,install=True)
    with tempfile.TemporaryDirectory(prefix='.janus-unity-probe-',dir=dst.parent) as tmp:
        stage=Path(tmp)/'project';stage.mkdir()
        for name,content in stage_files(s).items():
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding='utf-8')
        log=Path(tmp)/'editor.log';verify_guards(plan['guards'])
        run_profile(command(plan['guards'][1]['path'],stage),stage,log,300,sampler)
        observed=json.loads(guard.read_bound(stage/'janus-result.json',8192).decode('utf-8-sig'))
        rawlog=guard.read_bound(log,4*1024*1024)
        result=assess(s,observed,rawlog.decode('utf-8',errors='replace'))
        if Path(observed['project']).resolve()!=stage.resolve():raise ValueError('Native project identity changed')
        scene=guard.read_bound(stage/'Assets/JanusProbe.unity',guard.MAX_INPUT)
        result.update(scene_sha256=hashlib.sha256(scene).hexdigest(),log_sha256=hashlib.sha256(rawlog).hexdigest(),shared_root_cap_verified=True)
    payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'native_unity_scene_probe_passed','output':plan['output'],'sha256':digest,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Native Unity scene evidence unavailable; check installed licensed editor, version and resource limits'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
