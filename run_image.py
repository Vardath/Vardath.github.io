"""Launch offline diffusion backend as a module without a console window."""
from deepthort_local.local_image_engine import main
if __name__ == '__main__':
    raise SystemExit(main())
