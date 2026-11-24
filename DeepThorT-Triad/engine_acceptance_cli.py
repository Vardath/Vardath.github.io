"""Offline static engine audit entry point. Does not execute project files."""
from deepthort_local.engine_acceptance import main

if __name__ == '__main__':
    raise SystemExit(main())
