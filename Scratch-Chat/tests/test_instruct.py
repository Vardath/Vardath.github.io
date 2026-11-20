from pathlib import Path
import json
import tempfile
import torch
import pytest
from capability.bpe import ByteBPE
from capability.build_chat_pilot import prepare
from capability.instruct import (encode_chat,read_examples,train_instruct,reply,evaluate_examples)


def test_only_final_assistant_target_is_supervised():
    tok=ByteBPE([])
    inp,labels=encode_chat([{'role':'system','content':'be concise'},
                            {'role':'user','content':'hello'},
                            {'role':'assistant','content':'fine'}],tok)
    first_target=next(i for i,y in enumerate(labels) if y!=-100)
    assert inp[first_target] == tok.special['<|assistant|>']
    assert tok.decode([y for y in labels if 0<=y<256])=='fine'
    assert labels[-1] == tok.special['<|eos|>']
    assert len(inp)==len(labels)


def test_pilot_splits_and_cross_split_integrity(tmp_path):
    source=Path(__file__).resolve().parents[1]/'data/starter.jsonl'
    folder=tmp_path/'pilot'; summary=prepare(source,folder)
    assert sum(summary.values())==51
    tok=ByteBPE([])
    results=read_examples(folder,tok,context_size=1024)
    assert len(results['test'])>=5
    record=json.loads((folder/'validation.jsonl').read_text().splitlines()[0])
    record['group']=json.loads((folder/'train.jsonl').read_text().splitlines()[0])['group']
    with (folder/'validation.jsonl').open('a',encoding='utf8') as f:
        f.write(json.dumps(record)+'\n')
    with pytest.raises(ValueError,match='leakage'):
        read_examples(folder,tok,context_size=1024)


def test_incompatible_length_rejected(tmp_path):
    folder=tmp_path/'data';folder.mkdir()
    tok=ByteBPE([])
    for split in ('train','validation','test'):
        (folder/(split+'.jsonl')).write_text(json.dumps({'messages':[{'role':'user','content':'x'*250},{'role':'assistant','content':'yes'}]})+'\n')
    with pytest.raises(ValueError,match='context'):
        read_examples(folder,tok,context_size=16)


def _setup(tmp_path):
    tok=ByteBPE([])
    tokenizer=tmp_path/'tokenizer.json';tok.save(tokenizer)
    data=tmp_path/'data';data.mkdir()
    for split, q in [('train','hello'),('validation','hi'),('test','greetings')]:
        (data/(split+'.jsonl')).write_text(json.dumps({'messages':[{'role':'user','content':q},
               {'role':'assistant','content':'hello'}],'group':split})+'\n')
    return data,tokenizer


def test_train_eval_reply_and_reproducible_restart(tmp_path):
    data,tok=_setup(tmp_path)
    opts={'data':data,'tokenizer_path':tok,'steps':4,'width':32,'layers':1,
          'heads':4,'context_size':64,'batch':2,'lr':0.01,'threads':1,
          'seed':9,'quiet':True,'save_every':1,'eval_every':2}
    a=tmp_path/'a.pt';b=tmp_path/'b.pt'
    train_instruct(output=a,**opts)
    train_instruct(output=b,**{**opts,'steps':2})
    train_instruct(output=b,resume=True,**opts)
    x=torch.load(a,weights_only=True,map_location='cpu')
    y=torch.load(b,weights_only=True,map_location='cpu')
    for k in x['model_state']:
        assert torch.equal(x['model_state'][k],y['model_state'][k]),k
    assert x['optimizer_state']['state'].keys()==y['optimizer_state']['state'].keys()
    assert x['step']==4
    result=reply(a,tok,[{'role':'user','content':'hello'}],max_new_tokens=12)
    assert isinstance(result,str)
    assert x['metrics']['validation']['answer_tokens']>0
    # This is an observed learning test, not proof of general chat capability.
    assert x['metrics']['validation']['answer_token_loss'] < x['metrics']['before']['answer_token_loss']
