"""Native V20 supervised stdio acceptance in the actual shared Windows job."""
import sys
from pathlib import Path
from deepthort_local.win_cpu_cap import run_capped
from deepthort_local.mcp_stdio_probe import exercise
if __name__=='__main__':
    if sys.argv[1:]==['--inside']:
        result=exercise()
        print(result,flush=True)
        raise SystemExit(0 if result['status']=='passed' else 1)
    raise SystemExit(run_capped([sys.executable,str(Path(__file__).resolve()),'--inside'],
        cwd=str(Path(__file__).resolve().parent),percent=40,ram_percent=40))
