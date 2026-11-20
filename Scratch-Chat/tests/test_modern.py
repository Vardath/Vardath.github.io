import json
from pathlib import Path
import tempfile

import pytest
import torch
from capability.modern_model import ModernConfig, ModernScratchTransformer, apply_rope
from capability.modern_train import train, evaluate
from capability.bpe import ByteBPE


def test_modern_model_forward_backward():
    torch.manual_seed(11)
    model=ModernScratchTransformer(ModernConfig(vocab_size=300,context_size=24,width=32,layers=2,heads=4))
    x=torch.randint(0,300,(2,16))
    logits=model(x)
    assert logits.shape==(2,16,300)
    logits.square().mean().backward()
    assert model.embed.weight.grad is not None
    assert torch.isfinite(model.embed.weight.grad).all()


def test_causal_mask_future_cannot_affect_past():
    torch.manual_seed(13)
    model=ModernScratchTransformer(ModernConfig(vocab_size=400,context_size=64,width=32,layers=2,heads=4)).eval()
    x=torch.randint(0,400,(1,18))
    with torch.no_grad():
        a=model(x[:,:9])
        b=model(x)
    assert torch.allclose(a,b[:,:9],atol=1e-5,rtol=1e-5)


def test_rope_preserves_vector_length():
    v=torch.randn(2,3,6,8)
    w=apply_rope(v)
    assert torch.allclose(v.float().norm(dim=-1),w.float().norm(dim=-1),atol=1e-5)
    assert torch.allclose(v[:,:,:1],w[:,:,:1],atol=1e-6)


def _make_corpus(root):
    text=['Alpha beta gamma data to train a small local experiment.']*40
    tok=ByteBPE.train(text,merges=30)
    token_path=root/'tok.json';tok.save(token_path)
    corpus=root/'corpus'; corpus.mkdir()
    for split in ('train','validation','test'):
        with (corpus/f'{split}.jsonl').open('w') as f:
            for i,one in enumerate(text):
                f.write(json.dumps({'text':one,'group':f'{split}-{i}','split':split})+'\n')
    return corpus,token_path


def test_modern_checkpoint_exact_resume():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        corpus,tok=_make_corpus(root)
        one=root/'full.pt';two=root/'resumed.pt'
        kw=dict(corpus=corpus,tokenizer_path=tok,width=32,layers=1,heads=4,
                context_size=32,seq_len=8,batch=2,grad_accum=1,
                seed=23,threads=1,eval_every=1,save_every=1,min_train_tokens=10,quiet=True)
        train(output=one,steps=3,**kw)
        train(output=two,steps=1,**kw)
        train(output=two,steps=3,resume=True,**kw)
        a=torch.load(one,weights_only=True)
        b=torch.load(two,weights_only=True)
        for k in a['model_state']:
            assert torch.equal(a['model_state'][k],b['model_state'][k]),k
        assert evaluate(checkpoint=two,tokenizer_path=tok,corpus=corpus)['checkpoint_step']==3


def test_production_data_guard():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        corpus,tok=_make_corpus(root)
        with pytest.raises(ValueError,match='Corpus is inadequate'):
            train(corpus=corpus,tokenizer_path=tok,output=root/'guard.pt',steps=1,
                  width=32,layers=1,heads=4,context_size=32,seq_len=8,threads=1)
