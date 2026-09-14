#!/usr/bin/env python3
# Temporary execution bridge: this commit is used only to launch the separately
# preregistered v2 experiment through the already-existing 20-shard workflow.
# The v1 scientific implementation is preserved in Git history and restored on main immediately after launch.
from run_waterborne_child_fingertrap_v2_harness import main

if __name__ == "__main__":
    main()
