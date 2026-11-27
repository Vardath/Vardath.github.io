"""Deterministic, inspectable analytical reports with embedded reproduction receipts."""
from __future__ import annotations
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.exploratory_analysis import checked as check_analysis,analyse
from deepthort_local.long_form_writing import literal

SCHEMA='janus-analytical-report-v1'
EXTRA=('csv','.csv')
CODE_MODULES=('analytical_report.py','exploratory_analysis.py','statistical_analysis.py',
              'data_transformation.py','csv_processing.py','long_form_writing.py')
def canonical(data):
    return json.dumps(data,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode('ascii')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def checked(spec):
    if not isinstance(spec,dict) or 'title' not in spec or 'expected_source_sha256' not in spec:
        raise ValueError('Report requires title and an explicit expected source hash')
    literal(spec['title'],200)
    expected=spec['expected_source_sha256']
    if not isinstance(expected,str) or len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('Expected SHA-256 must be lowercase hexadecimal')
    check_analysis({k:v for k,v in spec.items() if k not in ('title','expected_source_sha256')})
    return spec
def manifest(raw,spec):
    if digest(raw)!=spec['expected_source_sha256']:raise ValueError('Dataset differs from reproducible specification')
    options={k:v for k,v in spec.items() if k not in ('title','expected_source_sha256')}
    analysis=analyse(raw,options)
    if analysis!=analyse(raw,options):raise ValueError('Repeated analysis differs')
    code={name:digest(Path(__file__).with_name(name).read_bytes()) for name in CODE_MODULES}
    return {'schema':SCHEMA,'specification':spec,'analysis':analysis,'analysis_sha256':digest(canonical(analysis)),
            'algorithm_source_sha256':code,'python_version':'.'.join(map(str,sys.version_info[:3])),
            'source_sha256':digest(raw),'repeat_analysis_identical':True}
def esc(value):return html.escape(str(value),quote=True)
def table(headers,rows):
    return '<table><thead><tr>'+''.join('<th scope="col">'+esc(v)+'</th>' for v in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
def fmt(stat):
    return 'Undefined' if stat is None else stat['decimal_24_digits']
STYLE='body{font:15px system-ui,sans-serif;color:#243142;max-width:1100px;margin:36px auto;padding:0 20px}h1{font-size:30px}h2{margin-top:32px}table{border-collapse:collapse;width:100%;margin:12px 0 24px}th,td{padding:8px 10px;border:1px solid #d6dfe7;text-align:left;overflow-wrap:anywhere}th{background:#e9eff5}tr:nth-child(even){background:#f7f9fb}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:12px}p{line-height:1.5}'
class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.active=False;self.parts=[];self.count=0
    def handle_starttag(self,tag,attrs):
        if tag=='pre' and dict(attrs).get('id')=='reproduction-manifest':self.active=True;self.count+=1
    def handle_endtag(self,tag):
        if tag=='pre':self.active=False
    def handle_data(self,data):
        if self.active:self.parts.append(data)
def extract_manifest(payload):
    p=Extract();p.feed(payload.decode('utf-8'))
    if p.count!=1:raise ValueError('Missing or ambiguous reproduction manifest')
    return json.loads(''.join(p.parts))
def render(raw,spec):
    m=manifest(raw,spec);a=m['analysis']
    title=esc(spec['title'])
    overview=table(['Measure','Value'],[['Rows',a['rows']],['Source columns',a['source_columns']],['Duplicate full rows after first',a['duplicate_full_rows_after_first']]])
    profiles=table(['Column','Type','Present','Missing','Distinct literal values'],[[c,v['type'],v['count'],v['missing'],v['distinct']] for c,v in a['columns'].items()])
    sections=[]
    for c,v in a['columns'].items():
        if v['type']=='numeric':
            s=v['statistics'];rows=[[k.replace('_',' ').title(),fmt(s[k])] for k in ('minimum','maximum','sum','mean','median','q1','q3','variance')]
            rows.append(['Standard deviation',s['standard_deviation_decimal'] if s['standard_deviation_decimal'] is not None else 'Undefined'])
            if v['iqr_flags']:rows.extend([['Below IQR fence',v['iqr_flags']['below']],['Above IQR fence',v['iqr_flags']['above']]])
            detail=table(['Statistic','Value'],rows)
        else:detail=table(['Category','Count'],[[x['value'],x['count']] for x in v['top']]+[['Other category occurrences',v['other_count']]])
        sections.append('<h3>'+esc(c)+'</h3>'+detail)
    correlations=table(['Left','Right','Complete pairs','Omitted rows','Pearson r'],[[c['left'],c['right'],c['paired_count'],c['omitted_count'],c['pearson_decimal'] if c['pearson_decimal'] is not None else c['reason']] for c in a['correlations']]) if a['correlations'] else '<p>No pairwise correlations requested or available.</p>'
    style_hash=__import__('base64').b64encode(hashlib.sha256(STYLE.encode()).digest()).decode('ascii')
    csp="default-src 'none'; style-src 'sha256-"+style_hash+"'; base-uri 'none'; form-action 'none'"
    page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="'+esc(csp)+'"><title>'+title+'</title><style>'+STYLE+'</style></head><body><h1>'+title+'</h1>'
    page+='<p>Descriptive analysis of a fixed local CSV snapshot. No causal or inferential conclusions.</p><h2>Dataset overview</h2>'+overview
    page+='<h2>Column coverage</h2>'+profiles+'<h2>Detailed statistics</h2>'+''.join(sections)+'<h2>Correlations</h2>'+correlations
    page+='<h2>Methods and reproducibility</h2>'+table(['Method','Definition'],list(a['methods'].items()))
    page+='<p>Source: '+esc(spec['csv'])+'<br>SHA-256: '+esc(m['source_sha256'])+'</p><p>To reproduce, preserve the source bytes, embedded specification, Python version and algorithm source versions below. Run the same reviewed report operation with a new output filename. The analysis digest identifies the exact results. Rendering and interpretation still require review.</p>'
    page+='<pre id="reproduction-manifest">'+esc(json.dumps(m,ensure_ascii=True,sort_keys=True,indent=2))+'</pre></body></html>'
    payload=page.encode('utf-8')
    if len(payload)>guard.MAX_OUTPUT or extract_manifest(payload)!=m:raise ValueError('Report manifest roundtrip failed')
    return payload,m
def verify(raw,spec,payload):
    expected,m=render(raw,spec)
    return expected==payload and extract_manifest(payload)==m
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)
    _,_,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    _,m=render(raw,spec)
    return plan,dict(spec,reproduction_manifest=m)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT);payload,m=render(raw,spec)
    if not verify(raw,spec,payload):raise ValueError('Report reproduction failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-analytical-report-result-v1','status':'deterministic_report_verified','output':plan['output'],
            'sha256':sha,'analysis_sha256':m['analysis_sha256'],'source_unchanged':True,'visual_render_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Report unavailable; inspect exact dataset hash and reviewed analysis specification'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
