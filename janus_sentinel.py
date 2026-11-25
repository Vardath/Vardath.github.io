"""Local JANUS Sentinel child. Runs inside the DeepThorT.exe job resource cap."""
from __future__ import annotations
import argparse
from deepthort_local.watchdog import JanusSentinel
from deepthort_local.flight_recorder import record,install_crash_hooks


def main():
    p=argparse.ArgumentParser()
    for n in ('sentinel','janus','jobs','games','heartbeat'):
        p.add_argument('--'+n,required=True)
    a=p.parse_args()
    install_crash_hooks(__import__("pathlib").Path(a.sentinel).parent,"sentinel")
    record(__import__("pathlib").Path(a.sentinel).parent,"sentinel","sentinel_started")
    JanusSentinel(sentinel_db=a.sentinel,janus_db=a.janus,jobs_db=a.jobs,
                  games_file=a.games,gui_heartbeat=a.heartbeat).run()


if __name__=='__main__':main()
