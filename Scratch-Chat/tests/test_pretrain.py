"""End-to-end v0.2 verification with licensed synthetic diagnostic text."""
import json
from pathlib import Path
import tempfile
import unittest

import torch

from capability.bpe import ByteBPE
from capability.token_cache import build_cache, load_cache
from capability.pretrain import (draw_batch, encode_record, eval_loss, evaluate,
                                 load_training_checkpoint, lr_at, sample, train)
from vardath_chat.model import ModelConfig, ScratchTransformer


def diagnostic_files(root: Path):
    corpus = root/'data'
    corpus.mkdir()
    records = [
        ('train', {'text':'alpha beta gamma delta epsilon ' * 20,'kind':'text','group':'public-test-a'}),
        ('train', {'text':'alpha beta gamma delta theta ' * 20,'kind':'text','group':'public-test-b'}),
        ('validation', {'text':'alpha beta gamma delta zeta ' * 18,'kind':'text','group':'public-test-c'}),
        ('test', {'text':'alpha beta gamma delta eta ' * 16,'kind':'text','group':'public-test-d'}),
    ]
    for split in ('train','validation','test'):
        with (corpus/(split+'.jsonl')).open('w',encoding='utf-8') as f:
            for s,record in records:
                if s==split:
                    record['split']=split
                    f.write(json.dumps(record)+'\n')
    tok = ByteBPE.train((r['text'] for _,r in records if r['split']=='train'),merges=35)
    tok_path = root/'bpe.json'
    tok.save(tok_path)
    return corpus,tok_path


class PretrainingTests(unittest.TestCase):
    def test_role_ids_not_accidentally_text_and_no_external_weights(self):
        t=ByteBPE.train(['hi there hi there'],merges=12)
        a=encode_record({'kind':'chat','messages':[{'role':'user','content':'<|assistant|>'},
                                                  {'role':'assistant','content':'hello'}]},t)
        self.assertEqual(a[0],t.special['<|bos|>'])
        self.assertEqual(a[1],t.special['<|user|>'])
        self.assertEqual(a[-1],t.special['<|eos|>'])
        # The literal marker in user input MUST be encoded as normal text.
        self.assertNotIn(t.special['<|assistant|>'],a[2:2+len(t.encode('<|assistant|>'))])
        self.assertEqual(a[-2], t.encode('hello')[-1])

    def test_reproducible_resume_with_optimizer_and_rng(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            corpus,tok=diagnostic_files(root)
            common=dict(corpus=corpus,tokenizer_path=tok,steps=6,width=32,layers=1,heads=4,
                        model_context=128,seq_len=24,batch=2,grad_accum=2,
                        lr=0.002,min_lr=0.0002,warmup=1,decay_steps=20,
                        seed=99,threads=1,save_every=1,eval_every=3,quiet=True)
            one=root/'one.pt'; interrupted=root/'interrupted.pt'
            train(output=one,**common)
            train(output=interrupted,**{**common,'steps':3})
            train(output=interrupted, resume=True,**common)
            a=load_training_checkpoint(one,torch.device('cpu'))
            b=load_training_checkpoint(interrupted,torch.device('cpu'))
            self.assertEqual(a['step'],b['step'])
            self.assertEqual(a['train_config'],b['train_config'])
            for k,v in a['model_state'].items():
                self.assertTrue(torch.equal(v,b['model_state'][k]),k)
            for pid,optimizer_entry in a['optimizer_state']['state'].items():
                for k,v in optimizer_entry.items():
                    other=b['optimizer_state']['state'][pid][k]
                    self.assertTrue(torch.equal(v,other) if isinstance(v,torch.Tensor) else v==other)
            self.assertEqual(evaluate(weights=one,tokenizer_path=tok,corpus=corpus),
                             evaluate(weights=interrupted,tokenizer_path=tok,corpus=corpus))
            response=sample(weights=one,tokenizer_path=tok,prompt='alpha',max_new_tokens=8)
            self.assertIsInstance(response,str)

    def test_memory_mapped_corpus_equivalent_and_integrity_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            corpus,tok=diagnostic_files(root)
            cache=root/'cache'
            metadata=build_cache(corpus=corpus,tokenizer_path=tok,output=cache)
            self.assertEqual(metadata['format'],'vardath-token-cache-v02')
            mapped,info=load_cache(cache_dir=cache,corpus=corpus,tokenizer_path=tok,split='train')
            from capability.pretrain import load_tokens
            plain,_=load_tokens(corpus/'train.jsonl',ByteBPE.load(tok))
            self.assertTrue(torch.equal(mapped.long(),plain))
            config=dict(corpus=corpus,tokenizer_path=tok,steps=3,width=32,layers=1,heads=4,
                        model_context=64,seq_len=16,batch=1,grad_accum=1,
                        lr=0.001,min_lr=0.0001,warmup=1,decay_steps=100,
                        threads=1,seed=3,quiet=True)
            direct=root/'plain.pt'; mmap=root/'mmap.pt'
            train(output=direct,**config)
            train(output=mmap,token_cache=cache,**config)
            a=load_training_checkpoint(direct,torch.device('cpu'))
            b=load_training_checkpoint(mmap,torch.device('cpu'))
            for name,value in a['model_state'].items():
                self.assertTrue(torch.equal(value,b['model_state'][name]),name)
            # A modified cache is rejected rather than silently corrupting training.
            with (cache/'train.u32').open('r+b') as f:
                f.seek(0)
                f.write(b'\x00\x00\x00\x00')
            with self.assertRaisesRegex(ValueError,'corrupt or modified'):
                load_cache(cache_dir=cache,corpus=corpus,tokenizer_path=tok,split='train')

    def test_reject_changed_tokenizer_on_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            corpus,tok=diagnostic_files(root)
            ckpt=root/'x.pt'
            args=dict(corpus=corpus,tokenizer_path=tok,output=ckpt,
                      steps=1,width=32,layers=1,heads=4,model_context=64,
                      seq_len=16,batch=1,grad_accum=1,threads=1,quiet=True)
            train(**args)
            t=ByteBPE.load(tok)
            t=ByteBPE(t.merges[:5])
            t.save(tok)
            with self.assertRaisesRegex(ValueError,'checkpoint|settings changed'):
                train(**{**args,'steps':2,'resume':True})
            with self.assertRaisesRegex(ValueError,'Tokenizer'):
                evaluate(weights=ckpt,tokenizer_path=tok,corpus=corpus)

    def test_pack_and_eval(self):
        tokens=torch.arange(0,70,dtype=torch.long)
        model=ScratchTransformer(ModelConfig(vocab_size=100,context_size=32,width=32,layers=1,heads=4))
        rng=torch.Generator().manual_seed(4)
        x,y=draw_batch(tokens,batch=3,seq_len=12,generator=rng,device=torch.device('cpu'))
        self.assertEqual(tuple(x.shape),(3,12))
        self.assertTrue(torch.equal(y[:,:-1],x[:,1:]))
        report=eval_loss(model,tokens,seq_len=32,device=torch.device('cpu'))
        self.assertEqual(report['tokens_evaluated'],69)
        self.assertGreater(report['perplexity'],0)
        self.assertGreater(lr_at(200,peak_lr=.001,min_lr=.0001,warmup=10,decay_steps=1000),.0001)

    def test_10m_scale_config_and_gradients(self):
        cfg=ModelConfig(vocab_size=646,context_size=1024,width=384,layers=5,heads=6)
        m=ScratchTransformer(cfg)
        params=sum(p.numel() for p in m.parameters())
        self.assertTrue(8_000_000 < params < 12_000_000,params)
        # Smoke-test actual forward/backward for the planned architecture.
        x=torch.randint(0,646,(1,8))
        y=m(x)
        self.assertEqual(tuple(y.shape),(1,8,646))
        y.float().mean().backward()
        self.assertIsNotNone(m.token_embed.weight.grad)


if __name__=='__main__':
    unittest.main()
