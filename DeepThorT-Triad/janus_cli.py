"""Console entrypoint for the explicitly enabled local JANUS developer gateway."""
from deepthort_local.headless_client import main
if __name__=='__main__':
    raise SystemExit(main())
