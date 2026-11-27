"""Standalone interactive chart viewer using the existing verified SVG chart producer."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.chart_creation import checked,dataset,render_data
from deepthort_local.interactive_table import hash_source

SCHEMA='janus-interactive-chart-v1'
EXTRA=('csv','.csv')
CORE_JS="""function pointState(data, seriesIndex, row, visible) {
  const names = data.names;
  if (!Number.isInteger(seriesIndex) || !Number.isInteger(row) ||
      seriesIndex < 0 || seriesIndex >= names.length || row < 0 || row >= data.x.length)
    return null;
  const name = names[seriesIndex];
  return {name, row, x: data.x[row], y: data.series[name][row], visible: Boolean(visible[seriesIndex])};
}
"""
UI_JS="""(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('chart-data').textContent);
  const toggles = Array.from(document.querySelectorAll('input[data-series-index]'));
  const series = document.getElementById('selected-series'), row = document.getElementById('selected-row');
  const details = document.getElementById('details'), marks = Array.from(document.querySelectorAll('svg [data-series]'));
  const groups = data.names.map((_, i) => document.getElementById('series-' + i));
  function refresh() {
    const visible = toggles.map(t => t.checked);
    groups.forEach((g, i) => g.classList.toggle('hidden-series', !visible[i]));
    const point = pointState(data, Number(series.value), Number(row.value), visible);
    marks.forEach(mark => mark.classList.toggle('selected-mark', Boolean(point && point.visible &&
      mark.getAttribute('data-series') === point.name && Number(mark.getAttribute('data-row')) === point.row)));
    details.textContent = point ? point.name + ': ' + point.x + ' = ' + point.y +
      (point.visible ? '' : ' (series hidden)') : 'Select a valid point.';
  }
  toggles.forEach(t => t.addEventListener('change', refresh));
  series.addEventListener('change', refresh);
  row.addEventListener('change', refresh);
  document.getElementById('reset').addEventListener('click', () => {
    toggles.forEach(t => { t.checked = true; });
    series.value = '0'; row.value = '0'; refresh();
  });
  marks.forEach(mark => mark.addEventListener('click', () => {
    const index = data.names.indexOf(mark.getAttribute('data-series'));
    if (index < 0) return;
    series.value = String(index); row.value = mark.getAttribute('data-row'); refresh();
  }));
  refresh();
})();
"""
SCRIPT=CORE_JS+UI_JS
STYLE="""body{font:15px system-ui,sans-serif;margin:24px;background:#fff;color:#253142}
h1{font-size:24px}p{max-width:80ch}fieldset{display:flex;flex-wrap:wrap;gap:14px;align-items:center;border:1px solid #cbd5e1;margin-bottom:12px;padding:12px}
button,select{font:inherit;padding:6px 8px;max-width:100%}label{overflow-wrap:anywhere}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid #245e9e}
.chart-wrap{overflow:auto;border:1px solid #cbd5e1;max-width:1040px}svg{display:block;width:100%;min-width:680px;height:auto}
svg .hidden-series{display:none}svg [data-series]{cursor:pointer}
svg .selected-mark{stroke:#17202c;stroke-width:3;paint-order:stroke}
#details{font-weight:600;white-space:pre-wrap;overflow-wrap:anywhere}
"""
def render(raw,spec):
    data=dataset(raw,spec);svg,receipt=render_data(data,spec)
    # The chart producer emits only trusted static XML tags, literal text/attributes,
    # and no scripts, links or external references. Remove its XML declaration for HTML.
    chart=svg.decode('utf-8').split('?>',1)[1].lstrip()
    data=dict(data,names=spec['series'])
    encoded=json.dumps(data,ensure_ascii=True,separators=(',',':')).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    if json.loads(encoded)!=data or '<' in encoded or len(encoded)>2*1024*1024:
        raise ValueError('Interactive chart data failed roundtrip or exceeds limit')
    esc=html.escape;title=esc(spec['title'])
    csp="default-src 'none'; script-src "+hash_source(SCRIPT)+"; style-src "+hash_source(STYLE)+"; base-uri 'none'; form-action 'none'; object-src 'none'; connect-src 'none'"
    toggles=''.join('<label><input type="checkbox" checked data-series-index="'+str(i)+'"> '+esc(s)+'</label>' for i,s in enumerate(data['names']))
    names=''.join('<option value="'+str(i)+'">'+esc(s)+'</option>' for i,s in enumerate(data['names']))
    rows=''.join('<option value="'+str(i)+'">'+str(i+1)+': '+esc(x)+'</option>' for i,x in enumerate(data['x']))
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="'''+esc(csp,quote=True)+'''">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+title+'''</title><style>'''+STYLE+'''</style></head>
<body><h1>'''+title+''' — interactive view</h1><p>Toggle series visibility; the original axis scale remains fixed. Select a data point using the controls or click a visible mark. Values are literal source values.</p>
<fieldset><legend>Visible series</legend>'''+toggles+'''</fieldset>
<fieldset><legend>Inspect a data point</legend><label>Series <select id="selected-series">'''+names+'''</select></label>
<label>Source row / x value <select id="selected-row">'''+rows+'''</select></label><button type="button" id="reset">Reset</button></fieldset>
<p id="details" aria-live="polite">Choose a data point with JavaScript enabled.</p>
<noscript><p>JavaScript disabled. The full static chart is available below.</p></noscript>
<div class="chart-wrap">'''+chart+'''</div>
<script type="application/json" id="chart-data">'''+encoded+'''</script><script>'''+SCRIPT+'''</script></body></html>'''
    payload=page.encode('utf-8')
    return payload,dict(receipt,embedded_data_sha256=hashlib.sha256(encoded.encode('ascii')).hexdigest())
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)
    _,_,path=validate(root,plan);data=dataset(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    return plan,dict(spec,exact_chart_data=data)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,receipt=render(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-interactive-chart-result-v1','status':'interactive_chart_structure_verified','output':plan['output'],
        'sha256':sha,**receipt,'source_unchanged':True,'browser_render_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Interactive chart unavailable; inspect reviewed chart data and limits'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
