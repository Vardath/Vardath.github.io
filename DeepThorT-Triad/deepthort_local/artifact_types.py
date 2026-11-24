"""Format routing is metadata, not a hardcoded project design.

Recognised binary outputs cannot be written by the text-source pipeline.
An unsupported native format needs a learned producer and stronger evidence.
"""
from pathlib import PurePosixPath

_GROUPS={
    'mesh':('obj','stl','ply','gltf','glb','fbx','blend','dae','xmf','xac','xsm'),
    'texture':('png','jpg','jpeg','webp','dds','tga','bmp','gif','ktx','ktx2','psd','exr','tif','tiff'),
    'audio':('wav','flac','mp3','ogg','opus','aac','m4a','mid','midi'),
    'video':('mp4','webm','mov','avi','mkv'),
    'compiled':('exe','dll','so','dylib','class','wasm','o','objbin','lib','a','dex','pdb','bin'),
    'package':('zip','apk','aab','jar','msi','7z','rar','pak','pck','unitypackage','tar','gz'),
    'document':('pdf','docx','xlsx','pptx','odt','ods','odp'),
}
_TEXT_NATIVE={'obj','gltf','dae'}
_CHECKED={'obj','png','wav','glb','dds','zip','apk','aab','jar','exe','dll'}
_FORMATS={ext:kind for kind,extensions in _GROUPS.items() for ext in extensions}

def artifact_type(path):
    ext=PurePosixPath(str(path).replace('\\','/')).suffix.casefold().lstrip('.')
    kind=_FORMATS.get(ext,'source')
    if ext=='svg':kind='vector'
    if ext in ('xml','json','toml','svg'):checker='structural'
    elif ext in _CHECKED:checker='structural'
    elif kind=='source':checker='source_or_project_tests'
    else:checker='needs_format_verifier'
    return {'kind':kind,'format':ext or 'extensionless',
            'producer':'text' if kind in ('source','vector') or ext in _TEXT_NATIVE else 'native_tool',
            'verification':checker}

def require_text_target(path):
    info=artifact_type(path)
    if info['producer']!='text':
        raise ValueError(f"{path}: {info['kind']} ({info['format']}) requires a native producer, not generated source text")
    return info

def require_checked_receipt(task,receipt):
    info=task.get('artifact_type')
    if info is None:return True  # historical obligations retain their original semantics
    if info!=artifact_type(task['output']):raise ValueError('Artifact format metadata changed')
    if info['verification']!='structural' or receipt.get('scope') in (None,'nonempty bytes only'):
        raise ValueError('Required artifact needs a format-specific verifier; file existence is insufficient')
    return True
