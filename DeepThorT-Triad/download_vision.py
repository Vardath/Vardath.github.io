"""User-approved, one-time local Florence-2 vision weights download (q8 ONNX)."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
import os,time
REPO='onnx-community/Florence-2-base-ft'
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'models'/'onnx-community'/'Florence-2-base-ft'
FILES={
 'config.json':100,'generation_config.json':50,'added_tokens.json':100,
 'special_tokens_map.json':100,'tokenizer.json':100_000,'tokenizer_config.json':100,
 'vocab.json':1000,'merges.txt':1000,'preprocessor_config.json':100,
 'onnx/vision_encoder_quantized.onnx':50_000_000,
 'onnx/encoder_model_quantized.onnx':10_000_000,
 'onnx/embed_tokens_quantized.onnx':10_000_000,
 'onnx/decoder_model_quantized.onnx':10_000_000,
 'onnx/decoder_with_past_model_quantized.onnx':10_000_000,
 'onnx/decoder_model_merged_quantized.onnx':10_000_000,
}
def main():
  for rel,minimum in FILES.items():
    target=TARGET/rel;target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file() and target.stat().st_size>=minimum:
      print('Already exists:',rel,flush=True);continue
    part=target.with_name(target.name+'.part');offset=part.stat().st_size if part.exists() else 0
    url=f'https://huggingface.co/{REPO}/resolve/main/{quote(rel)}?download=true'
    req=Request(url,headers={'Range':f'bytes={offset}-'} if offset else {})
    print('Fetching',rel,flush=True)
    with urlopen(req,timeout=90) as r:
      mode='ab' if offset and r.status==206 else 'wb'
      with part.open(mode) as f:
        while block:=r.read(256*1024):f.write(block);time.sleep(.05)
    if part.stat().st_size<minimum:raise RuntimeError(f'Incomplete: {rel}; rerun installer to resume')
    os.replace(part,target)
  print('Local Florence vision files downloaded.',flush=True)
if __name__=='__main__':main()
