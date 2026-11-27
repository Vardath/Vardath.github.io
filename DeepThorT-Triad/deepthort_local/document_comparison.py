"""Reviewed local document text comparison, not a visual or semantic diff."""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local.action_guards import snapshot_file
from deepthort_local.document_conversion import path_for,source_lines,MAX_BYTES,MAX_PDF_BYTES
from deepthort_local.pdf_table_extract import output_path
from deepthort_local.source_security import exclusions
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-document-comparison-v1'
MAX_LINES=2000
MAX_PAIRS=2_000_000
MAX_OUTPUT=4_000_000

def limit(path):
    return MAX_PDF_BYTES if path.suffix.casefold()=='.pdf' else MAX_BYTES

def review(root,before,after,output,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    a=path_for(root,before,exclude,source=True);b=path_for(root,after,exclude,source=True)
    output_path(root,output,exclude)
    if a==b or os.path.samefile(a,b):raise ValueError('Choose two distinct document files')
    if a.stat().st_size>limit(a) or b.stat().st_size>limit(b):
        raise ValueError('Document exceeds comparison byte budget')
    return {'schema':SCHEMA,'root':str(root),'before':before,'after':after,'output':output,
            'exclude':exclude,'guards':[snapshot_file(a),snapshot_file(b)],'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','root','before','after','output','exclude','guards','expires_at'}
        or plan['schema']!=SCHEMA or plan['root']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800
        or exclusions(plan['exclude'])!=plan['exclude']):
        raise ValueError('Invalid or expired comparison approval')
    a=path_for(root,plan['before'],plan['exclude'],source=True)
    b=path_for(root,plan['after'],plan['exclude'],source=True)
    out=output_path(root,plan['output'],plan['exclude'])
    if a==b or os.path.samefile(a,b) or a.stat().st_size>limit(a) or b.stat().st_size>limit(b):
        raise ValueError('Invalid comparison sources')
    if [snapshot_file(a),snapshot_file(b)]!=plan['guards']:
        raise ValueError('Reviewed documents changed')
    return a,b,out

def read_exact(path,guard):
    with path.open('rb') as f:raw=f.read(limit(path)+1)
    if len(raw)>limit(path) or hashlib.sha256(raw).hexdigest()!=guard['expected']:
        raise ValueError('Reviewed document bytes changed')
    return raw

def compare_lines(before,after):
    if (len(before)>MAX_LINES or len(after)>MAX_LINES or len(before)*len(after)>MAX_PAIRS):
        raise ValueError('Document line comparison exceeds bounded work; split into smaller sections')
    matcher=difflib.SequenceMatcher(None,before,after,autojunk=False)
    counts={'unchanged_lines':0,'removed_lines':0,'added_lines':0,'replace_blocks':0,
            'delete_blocks':0,'insert_blocks':0}
    changes=[];reconstructed=[]
    for tag,i,j,k,l in matcher.get_opcodes():
        if tag=='equal':
            counts['unchanged_lines']+=j-i;reconstructed.extend(before[i:j]);continue
        counts['removed_lines']+=j-i;counts['added_lines']+=l-k
        counts[tag+'_blocks']+=1
        reconstructed.extend(after[k:l])
        changes.append({'operation':tag,'before_start_line':i+1,'before_line_count':j-i,
                        'after_start_line':k+1,'after_line_count':l-k,
                        'before_text':before[i:j],'after_text':after[k:l]})
    if reconstructed!=after:raise ValueError('Text comparison reconstruction failed')
    return counts,changes

def execute(root,plan):
    a,b,out=validate(root,plan)
    require_storage(a.parent,out.parent);require_storage(b.parent,out.parent)
    raw_a=read_exact(a,plan['guards'][0]);raw_b=read_exact(b,plan['guards'][1])
    before=source_lines(raw_a,a.suffix.casefold());after=source_lines(raw_b,b.suffix.casefold())
    counts,changes=compare_lines(before,after)
    result={'schema':'janus-document-comparison-data-v1',
            'before_sha256':plan['guards'][0]['expected'],'after_sha256':plan['guards'][1]['expected'],
            'same_file_bytes':raw_a==raw_b,'same_extracted_text':before==after,
            'before_lines':len(before),'after_lines':len(after),'counts':counts,'changes':changes,
            'scope':'Extracted main-body text lines or paragraphs, in parser order; no formatting, images, page geometry, fields, links, OCR or semantic equivalence comparison. Newline encoding is normalized. Positions refer to extracted text, not source page numbers.',
            'full_document_equivalence_verified':False,'visual_verification':False}
    payload=(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    if len(payload)>MAX_OUTPUT or json.loads(payload)!=result:raise ValueError('Comparison report exceeds output bound')
    a,b,out=validate(root,plan);require_storage(out.parent)
    fd,tmp=tempfile.mkstemp(prefix='.janus-comparison-',suffix='.tmp',dir=out.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
        validate(root,plan);os.link(tmp,out)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    # The report itself contains selected text; the process log contains counts only.
    return {'schema':'janus-document-comparison-result-v1','status':'text_comparison_verified',
            'output':plan['output'],'sha256':hashlib.sha256(payload).hexdigest(),
            'same_file_bytes':result['same_file_bytes'],'same_extracted_text':result['same_extracted_text'],
            'counts':counts,'sources_unchanged':True,'visual_verification':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({'schema':'janus-document-comparison-result-v1','status':'blocked','error_type':type(exc).__name__,
                          'reason':'Comparison unavailable; inspect reviewed source files, extraction limits and installed tools'}),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
