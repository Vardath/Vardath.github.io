"""One-time explicit download of public ONNX coding model. Inference is offline.

Only downloads the selected q4 model and tokenizer, never all 21 GB of variants.
Transfers use small streaming buffers and resumable .part files when supported.
"""
from __future__ import annotations
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import HTTPError

REPO = 'onnx-community/Qwen2.5-Coder-1.5B-Instruct'
ROOT = Path(__file__).resolve().parent
MODEL = ROOT / 'models' / 'onnx-community' / 'Qwen2.5-Coder-1.5B-Instruct'
FILES = {
    'config.json': 100,
    'generation_config.json': 50,
    'added_tokens.json': 50,
    'special_tokens_map.json': 50,
    'tokenizer.json': 1_000_000,
    'tokenizer_config.json': 100,
    'merges.txt': 100_000,
    'vocab.json': 100_000,
    'onnx/model_q4.onnx': 1_700_000_000,
}
# This is an initial-install bandwidth throttle, not an OS-wide disk limit.
RATE_BYTES_PER_SECOND = 3 * 1024 * 1024


def download(relative: str, minimum: int) -> None:
    target = MODEL / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size >= minimum:
        print(f'Already present: {relative}', flush=True)
        return
    part = Path(str(target)+'.part')
    offset = part.stat().st_size if part.exists() else 0
    url = f'https://huggingface.co/{REPO}/resolve/main/{quote(relative)}?download=true'
    headers = {'User-Agent': 'DeepThorT-Offline-Setup/3'}
    if offset: headers['Range'] = f'bytes={offset}-'
    req = Request(url, headers=headers)
    print(f'Downloading {relative}' + (f' (resuming at {offset/1e6:.1f} MB)' if offset else ''), flush=True)
    try:
        response = urlopen(req, timeout=90)
    except HTTPError as exc:
        raise RuntimeError(f'Model download HTTP {exc.code} for {relative}; retry the setup later') from exc
    with response:
        status = response.status
        if offset and status != 206:
            # Server ignored Range. Restart cleanly rather than appending duplicate bytes.
            print('Server did not support resume; restarting this file.', flush=True)
            offset = 0
        mode = 'ab' if offset else 'wb'
        content_length = response.headers.get('Content-Length')
        expected = (offset+int(content_length)) if content_length and content_length.isdigit() else None
        written = offset
        last = time.monotonic()
        with part.open(mode) as dest:
            while True:
                start = time.monotonic()
                block = response.read(128 * 1024)
                if not block: break
                dest.write(block)
                written += len(block)
                wait = len(block)/RATE_BYTES_PER_SECOND-(time.monotonic()-start)
                if wait > 0: time.sleep(wait)
                if time.monotonic()-last > 10:
                    print(f'   {relative}: {written/1e6:,.1f} MB saved', flush=True)
                    last = time.monotonic()
    if expected is not None and part.stat().st_size != expected:
        raise RuntimeError(f'Interrupted transfer of {relative}; run installer again to resume')
    if part.stat().st_size < minimum:
        raise RuntimeError(f'Incomplete {relative}: got {part.stat().st_size} bytes. Run installer again.')
    os.replace(part, target)
    print(f'Saved: {target} ({target.stat().st_size / 1e6:.1f} MB)', flush=True)


def main() -> None:
    for relative, minimum in FILES.items():
        download(relative, minimum)
    print('ONNX model ready. All inference after installation is local-only.', flush=True)


if __name__ == '__main__':
    main()
