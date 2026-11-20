from pathlib import Path
import hashlib
import json
import pytest
import torch

from capability.bpe import ByteBPE
from capability.modern_chat import encode_dialog, generate, load_chat
from capability.modern_instruct import fine_tune, evaluate_checkpoint

ROOT = Path(__file__).resolve().parents[1]
TOKENIZER = ROOT / 'data/tokenizer-bpe.json'
BASE = ROOT / 'checkpoints/v05-modern-smoke.pt'
DATA = ROOT / 'data/instruct-pilot'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_dialog_limits_and_literal_user_tokens():
    tok = ByteBPE.load(TOKENIZER)
    x = encode_dialog([{'role':'user','content':'Here is <|eos|> as a literal'}], tok, 128)
    assert x[-1] == tok.special['<|assistant|>']
    assert x.count(tok.special['<|eos|>']) == 0
    with pytest.raises(ValueError, match='exceeds'):
        encode_dialog([{'role':'user','content':'exceed '*300}], tok, 25)
    history = [{'role':'user','content':'old question '*8},
               {'role':'assistant','content':'old answer '*8},
               {'role':'user','content':'hello'}]
    z = encode_dialog(history, tok, 40)
    assert z[-1] == tok.special['<|assistant|>']
    assert tok.encode('hello') == z[-1-len(tok.encode('hello')):-1]


def test_pretrain_not_falsely_advertised_as_chat():
    with pytest.raises(ValueError, match='instruction-training checkpoint'):
        load_chat(BASE, TOKENIZER)


def test_modern_finetune_and_generation(tmp_path):
    ck = tmp_path / 'train.pt'
    previous_hash = digest(BASE)
    report = fine_tune(base=BASE, tokenizer_path=TOKENIZER, data=DATA,
                       output=ck, steps=3, batch=2, eval_every=1,
                       save_every=1, patience_evals=0, threads=1)
    assert ck.exists() and Path(report['best_checkpoint']).exists()
    assert digest(BASE) == previous_hash
    assert report['steps'] == 3
    metrics = evaluate_checkpoint(Path(report['best_checkpoint']), TOKENIZER, DATA)
    assert metrics['test']['examples'] == 8
    model, tok = load_chat(Path(report['best_checkpoint']), TOKENIZER)
    answer = generate(model, tok, [{'role':'user','content':'hello'}], max_new_tokens=5)
    assert isinstance(answer, str)
    assert len(answer) < 100


def test_finetune_resume_exact(tmp_path):
    a, b = tmp_path/'continuous.pt', tmp_path/'resumed.pt'
    common = dict(base=BASE, tokenizer_path=TOKENIZER, data=DATA,
                  batch=2, eval_every=2, save_every=2,
                  patience_evals=0, threads=1)
    fine_tune(output=a, steps=4, **common)
    fine_tune(output=b, steps=2, **common)
    fine_tune(output=b, steps=4, resume=True, **common)
    left = torch.load(a,map_location='cpu',weights_only=True)
    right = torch.load(b,map_location='cpu',weights_only=True)
    for k, v in left['model_state'].items():
        assert torch.equal(v, right['model_state'][k]), k
    assert left['optimizer_state']['state'].keys() == right['optimizer_state']['state'].keys()
    assert left['metrics'] == right['metrics']


def test_does_not_overwrite_base_or_existing_output(tmp_path):
    dest=tmp_path/'new.pt'
    dest.write_bytes(b'still here')
    with pytest.raises(FileExistsError):
        fine_tune(base=BASE, tokenizer_path=TOKENIZER,data=DATA,
                  output=dest,steps=1,threads=1)
    assert dest.read_bytes() == b'still here'
    with pytest.raises(ValueError,match='must not overwrite'):
        fine_tune(base=BASE,tokenizer_path=TOKENIZER,data=DATA,
                  output=BASE,steps=1,threads=1)
