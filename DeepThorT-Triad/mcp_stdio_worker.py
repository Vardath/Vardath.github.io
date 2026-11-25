"""Fixed stdio discovery wrapper, launched only within the root/nested job."""
import json
import sys
from pathlib import Path
from deepthort_local.triad_job import verify_root_cap
from deepthort_local.mcp_stdio import prepare,stdio_discover
from deepthort_local.structured_source import strict_json

def main():
    verify_root_cap()
    if len(sys.argv)!=3:raise ValueError('Expected fixed discovery request and response paths')
    config,result=map(Path,sys.argv[1:])
    if config.stat().st_size>20000 or result.exists():raise ValueError('Invalid request')
    proposal=strict_json(config.read_text('utf-8'))
    if prepare(proposal['project'],proposal['argv'][0],proposal['argv'][1:])!=proposal:
        raise ValueError('Server input changed')
    response=stdio_discover(proposal['argv'],proposal['project'])
    encoded=json.dumps(response,ensure_ascii=True)
    if len(encoded)>128000:raise ValueError('Response exceeds bound')
    result.write_text(encoded,encoding='utf-8')
if __name__=='__main__':
    try:main()
    except Exception as error:
        print(type(error).__name__,flush=True)
        raise SystemExit(1)
