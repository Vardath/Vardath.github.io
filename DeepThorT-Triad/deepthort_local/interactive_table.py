"""Produce a reviewed standalone offline interactive table from exact CSV data."""
from __future__ import annotations
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.csv_processing import parse,DELIMITERS
from deepthort_local.long_form_writing import literal

SCHEMA='janus-interactive-table-v1'
EXTRA=('csv','.csv')
MAX_ROWS=5000
MAX_DATA=2*1024*1024
CORE_JS="""function selectRows(data, query, column, descending, page, size) {
  const q = query.toLowerCase();
  let rows = data.rows.map((row, index) => ({row, index})).filter(x =>
    !q || x.row.some(cell => cell.toLowerCase().includes(q)));
  if (column >= 0 && column < data.columns.length) {
    rows.sort((a, b) => {
      const x = a.row[column].toLowerCase(), y = b.row[column].toLowerCase();
      const cmp = x < y ? -1 : x > y ? 1 : 0;
      return cmp ? (descending ? -cmp : cmp) : a.index - b.index;
    });
  }
  const total = rows.length, pages = Math.max(1, Math.ceil(total / size));
  page = Math.min(Math.max(1, page), pages);
  return {rows: rows.slice((page - 1) * size, page * size).map(x => x.row),
          total, page, pages};
}
"""
UI_JS="""(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('dataset').textContent);
  const search = document.getElementById('search'), size = document.getElementById('size');
  const previous = document.getElementById('previous'), next = document.getElementById('next');
  const body = document.getElementById('rows'), status = document.getElementById('status');
  const heads = Array.from(document.querySelectorAll('thead button'));
  let column = -1, descending = false, page = 1;
  function refresh() {
    const result = selectRows(data, search.value, column, descending, page, Number(size.value));
    page = result.page;
    const fragment = document.createDocumentFragment();
    for (const row of result.rows) {
      const tr = document.createElement('tr');
      for (const cell of row) {
        const td = document.createElement('td');
        td.textContent = cell;
        tr.appendChild(td);
      }
      fragment.appendChild(tr);
    }
    body.replaceChildren(fragment);
    status.textContent = result.total + ' of ' + data.rows.length + ' rows; page ' + page + ' of ' + result.pages;
    previous.disabled = page <= 1;
    next.disabled = page >= result.pages;
    heads.forEach((button, i) => button.parentElement.setAttribute('aria-sort',
      i === column ? (descending ? 'descending' : 'ascending') : 'none'));
  }
  search.addEventListener('input', () => { page = 1; refresh(); });
  size.addEventListener('change', () => { page = 1; refresh(); });
  previous.addEventListener('click', () => { page--; refresh(); });
  next.addEventListener('click', () => { page++; refresh(); });
  heads.forEach((button, i) => button.addEventListener('click', () => {
    descending = column === i ? !descending : false;
    column = i; page = 1; refresh();
  }));
  refresh();
})();
"""
SCRIPT=CORE_JS+UI_JS
STYLE="""body{font:15px system-ui,sans-serif;margin:24px;color:#1f2937;background:#fff}
h1{font-size:24px}p{max-width:75ch}fieldset{display:flex;flex-wrap:wrap;gap:12px;align-items:center;border:0;padding:8px 0}
input,select,button{font:inherit;padding:6px 8px}button{cursor:pointer}button:disabled{cursor:default}
.wrap{overflow:auto;border:1px solid #cbd5e1}table{border-collapse:collapse;min-width:100%}
th,td{border-bottom:1px solid #dbe2ea;text-align:left;padding:9px 12px;white-space:pre-wrap;overflow-wrap:anywhere;max-width:44rem}
th{background:#e7edf4}th button{border:0;background:transparent;text-align:left;font-weight:600}
tr:nth-child(even){background:#f6f8fb}button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #245e9e}
"""
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'csv','delimiter','columns','title','page_size'}:
        raise ValueError('Expected CSV, delimiter, selected columns, title and page size')
    if not isinstance(spec['csv'],str) or not isinstance(spec['delimiter'],str) or spec['delimiter'] not in DELIMITERS:
        raise ValueError('Invalid CSV or delimiter')
    cols=spec['columns']
    if not isinstance(cols,list) or not 1<=len(cols)<=40 or any(not isinstance(c,str) or not c or len(c)>500 for c in cols) or len(set(cols))!=len(cols):
        raise ValueError('Select 1–40 distinct exact CSV columns')
    literal(spec['title'],200)
    if type(spec['page_size']) is not int or spec['page_size'] not in (25,50,100):
        raise ValueError('Page size must be 25, 50 or 100')
    return spec

def dataset(raw,spec):
    header,rows=parse(raw,spec['delimiter'])
    try:indices=[header.index(c) for c in spec['columns']]
    except ValueError as exc:raise ValueError('Selected column missing') from exc
    if len(rows)>MAX_ROWS:raise ValueError('Table exceeds 5,000 rows; project the CSV first')
    data={'columns':spec['columns'],'rows':[[row[i] for i in indices] for row in rows]}
    # JSON is inert data: escape markup delimiters even inside script data.
    encoded=json.dumps(data,ensure_ascii=True,separators=(',',':')).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    if len(encoded.encode('ascii'))>MAX_DATA or json.loads(encoded)!=data:
        raise ValueError('Interactive table exceeds embedded data bound')
    return data,encoded

def hash_source(text):
    return "'sha256-"+base64.b64encode(hashlib.sha256(text.encode('utf-8')).digest()).decode('ascii')+"'"

def render(raw,spec):
    data,encoded=dataset(raw,spec)
    esc=html.escape
    csp="default-src 'none'; script-src "+hash_source(SCRIPT)+"; style-src "+hash_source(STYLE)+"; base-uri 'none'; form-action 'none'; object-src 'none'; connect-src 'none'"
    title=esc(spec['title'])
    heads=''.join('<th scope="col" aria-sort="none"><button type="button">'+esc(c)+'</button></th>' for c in data['columns'])
    initial=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in data['rows'][:spec['page_size']])
    sizes=''.join('<option value="'+str(n)+'"'+(' selected' if n==spec['page_size'] else '')+'>'+str(n)+'</option>' for n in (25,50,100))
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="'''+esc(csp,quote=True)+'''">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+title+'''</title><style>'''+STYLE+'''</style></head>
<body><h1>'''+title+'''</h1><p>Local CSV snapshot. Search all displayed columns; select a header to sort literal text, not numeric values.</p>
<fieldset><label>Search <input id="search" type="search" maxlength="250"></label>
<label>Rows per page <select id="size">'''+sizes+'''</select></label>
<button id="previous" type="button" disabled>Previous</button><button id="next" type="button" disabled>Next</button></fieldset>
<p id="status" aria-live="polite">First page of '''+str(len(data['rows']))+''' rows.</p>
<noscript><p>JavaScript is disabled. The first page is shown; interactive controls require JavaScript.</p></noscript>
<div class="wrap"><table><thead><tr>'''+heads+'''</tr></thead><tbody id="rows">'''+initial+'''</tbody></table></div>
<script type="application/json" id="dataset">'''+encoded+'''</script><script>'''+SCRIPT+'''</script></body></html>'''
    payload=page.encode('utf-8')
    if len(payload)>guard.MAX_OUTPUT or '</script>' in encoded or '<' in encoded or json.loads(encoded)!=data:
        raise ValueError('Interactive table verification failed')
    return payload,{'rows':len(data['rows']),'columns':len(data['columns']),'embedded_data_sha256':hashlib.sha256(encoded.encode('ascii')).hexdigest()}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)
    _,_,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    data,encoded=dataset(raw,spec)
    return plan,dict(spec,preview_rows=data['rows'][:25],total_rows=len(data['rows']),
                     preview_is_sample=len(data['rows'])>25,embedded_data_sha256=hashlib.sha256(encoded.encode('ascii')).hexdigest())

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)

def execute(root,plan):
    spec,dst,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    payload,receipt=render(raw,spec);sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-interactive-table-result-v1','status':'offline_table_structure_verified','output':plan['output'],
        'sha256':sha,**receipt,'source_unchanged':True,'browser_render_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Interactive table unavailable; inspect selected CSV columns and limits'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
