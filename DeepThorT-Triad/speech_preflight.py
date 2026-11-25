"""Exercise actual installed Windows speech within the inherited 40% job."""
import sys
from pathlib import Path
from deepthort_local.win_cpu_cap import run_capped
from deepthort_local.speech_probe import native_exercise
if __name__=='__main__':
    if sys.argv[1:]==['--inside']:
        result=native_exercise()
        print(result,flush=True)
        # A clean runner may have no installed English voice; explicitly
        # report blocked rather than pretend actual synthesis passed.
        raise SystemExit(0 if result['status'] in ('passed','blocked') else 1)
    raise SystemExit(run_capped([sys.executable,str(Path(__file__).resolve()),'--inside'],
        cwd=str(Path(__file__).resolve().parent),percent=40,ram_percent=40))
