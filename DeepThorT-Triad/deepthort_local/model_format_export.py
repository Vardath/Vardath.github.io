"""Reviewed SafeTensors to NPZ weight conversion."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import model_format_conversion as core

def review(root,source,output,exclude=()):
    return core.review(root,source,output,exclude,target='npz')

def execute(root,plan):
    return core.execute(root,plan,target='npz')

if __name__=='__main__':sys.exit(core.main('npz'))
