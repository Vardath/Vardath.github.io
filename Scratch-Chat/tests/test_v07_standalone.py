import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest
import torch

from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.bpe import ByteBPE
from capability.modern_chat import encode_dialog, generate, generate_tokens
from capability.chat_quality import flags, probe
from capability.modern_server import make_handler


@pytest.fixture(scope='module')
def scratch():
    tok=ByteBPE([])
    cfg=ModernConfig(vocab_size=tok.vocab_size,context_size=128,width=32,layers=1,heads=4)
    torch.manual_seed(42)
    model=ModernScratchTransformer(cfg).eval()
    return model,tok


def test_generation_is_deterministic_in_greedy_mode(scratch):
    model,tok=scratch
    messages=[{'role':'user','content':'Hello'}]
    first=generate(model,tok,messages,max_new_tokens=8)
    second=generate(model,tok,messages,max_new_tokens=8)
    assert first==second


def test_token_accounting_is_exact(scratch):
    model,tok=scratch
    messages=[{'role':'user','content':'Hi'}]
    ids,n=generate_tokens(model,tok,messages,max_new_tokens=8)
    assert n==len(encode_dialog(messages,tok,model.cfg.context_size))
    assert len(ids)<=8
    assert all(i not in tok.special.values() for i in ids)


def test_sampling_settings_and_invalid_inputs(scratch):
    model,tok=scratch
    msg=[{'role':'user','content':'Hi'}]
    assert isinstance(generate(model,tok,msg,max_new_tokens=5,temperature=0.8,top_p=0.7,top_k=15,repetition_penalty=1.3),str)
    for kwargs in ({'top_p':0},{'temperature':-1},{'top_k':-1},{'repetition_penalty':.9},{'max_new_tokens':True}):
        with pytest.raises(ValueError):
            generate(model,tok,msg,**kwargs)


def test_blank_and_repetitive_response_detection():
    assert 'blank_or_whitespace_only' in flags('   ')
    assert 'repeated_sequence' in flags('xyz'*10)
    assert flags('This is a somewhat normal text response.')==[]


def test_probe_contains_real_generated_outputs(scratch):
    model,tok=scratch
    report=probe(model,tok,[{'prompt':'abc','category':'probe'}],max_tokens=5)
    assert report['questions']==1
    assert report['results'][0]['answer']==generate(model,tok,[{'role':'user','content':'abc'}],max_new_tokens=5)


def test_http_completions_and_rejected_requests(scratch):
    model,tok=scratch
    srv=ThreadingHTTPServer(('127.0.0.1',0),make_handler(model,tok))
    thread=threading.Thread(target=srv.serve_forever,daemon=True)
    thread.start()
    host=f'http://127.0.0.1:{srv.server_address[1]}'
    try:
        with urlopen(host+'/health') as resp:
            assert json.load(resp)['status']=='running'
        with urlopen(host+'/v1/models') as resp:
            assert json.load(resp)['data'][0]['id']=='vardath-scratch-chat'
        payload=json.dumps({'model':'vardath-scratch-chat','messages':[{'role':'user','content':'Hi'}],
                            'max_tokens':8}).encode('utf8')
        with urlopen(Request(host+'/v1/chat/completions',data=payload,headers={'Content-Type':'application/json'}),timeout=15) as resp:
            doc=json.load(resp)
            assert doc['choices'][0]['message']['role']=='assistant'
            assert doc['usage']['total_tokens']==doc['usage']['prompt_tokens']+doc['usage']['completion_tokens']
        invalid=json.dumps({'model':'other','messages':[{'role':'user','content':'Hi'}]}).encode('utf8')
        with pytest.raises(HTTPError) as err:
            urlopen(Request(host+'/v1/chat/completions',data=invalid),timeout=15)
        assert err.value.code==400
    finally:
        srv.shutdown()
        thread.join(timeout=3)
        srv.server_close()


def test_modern_trainer_memory_map_recovery_and_eval(tmp_path):
    """True mmap training and deterministic restart on a prepared corpus."""
    from capability.modern_train import train, evaluate
    from capability.token_cache import build_cache
    corpus = tmp_path/'corpus'
    corpus.mkdir()
    tok_path = tmp_path/'tok.json'
    tok = ByteBPE.train(['One short example of ordinary natural language.']*30, merges=20)
    tok.save(tok_path)
    for split in ('train','validation','test'):
        with (corpus/f'{split}.jsonl').open('w', encoding='utf8') as out:
            for i in range(12):
                out.write(json.dumps({'kind':'text','text':f'This is example number {i} in {split}.',
                                      'split':split,'group':f'{split}-{i}'})+'\n')
    cache=tmp_path/'cache'
    build_cache(corpus=corpus,tokenizer_path=tok_path,output=cache)
    kw=dict(corpus=corpus,tokenizer_path=tok_path,token_cache=cache,
            width=32,layers=1,heads=4,context_size=32,seq_len=8,batch=2,
            grad_accum=1,seed=72,threads=1,eval_every=1,save_every=1,
            min_train_tokens=10,quiet=True,device='cpu',amp='off')
    full=tmp_path/'full.pt'; resumed=tmp_path/'resumed.pt'
    train(output=full,steps=3,**kw)
    train(output=resumed,steps=1,**kw)
    train(output=resumed,steps=3,resume=True,**kw)
    a=torch.load(full,weights_only=True)
    b=torch.load(resumed,weights_only=True)
    assert a['metrics']['data_backend']=='mmap'
    for key in a['model_state']:
        assert torch.equal(a['model_state'][key],b['model_state'][key]),key
    result=evaluate(checkpoint=full,tokenizer_path=tok_path,corpus=corpus,token_cache=cache)
    assert result['results']['test']['tokens_evaluated']>0


def test_gpu_backend_request_fails_without_gpu(tmp_path):
    if torch.cuda.is_available():
        pytest.skip('GPU is present; this test is for CPU environments')
    from capability.modern_train import train
    with pytest.raises(ValueError,match='CUDA requested'):
        train(corpus=tmp_path,tokenizer_path=tmp_path/'tokenizer.json',
              output=tmp_path/'model.pt',device='cuda',steps=1)
