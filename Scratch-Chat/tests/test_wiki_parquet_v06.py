import json
from pathlib import Path
import pytest
from capability.wiki_parquet import convert, filename, CHECKSUMS


def test_pinned_names():
    assert all(len(h)==64 for h in CHECKSUMS.values())
    assert filename('train')=='train-00000-of-00001.parquet'
    with pytest.raises(ValueError): filename('unknown')


def test_import_preserves_splits(tmp_path):
    fixtures={
      'train': ['= Train Article =','The sample training article has a sentence with many words and a distinct ending.'],
      'validation': ['= Validation Article =','The validation content is unrelated to the sample training article and used only for evaluation.'],
      'test': ['= Test Article =','An independent test document provides a different text sequence from the previous examples.'],
    }
    def rows(path):
        split=path.name.split('-')[0]
        return ({'text':x} for x in fixtures[split])
    report=convert(tmp_path,tmp_path/'out',row_reader=rows,verify=False,min_chars=35)
    assert report['article_counts']=={'train':1,'validation':1,'test':1}
    for split in ('train','validation','test'):
        rows2=[json.loads(s) for s in (tmp_path/'out'/f'{split}.jsonl').read_text().splitlines()]
        assert len(rows2)==1 and rows2[0]['split']==split


def test_reject_cross_split_duplicates(tmp_path):
    def rows(path):
        return ({'text':x} for x in ['= Article =','Same document sentence with enough detail to satisfy minimum length every time.'])
    with pytest.raises(ValueError,match='leakage'):
        convert(tmp_path,tmp_path/'out',row_reader=rows,verify=False,min_chars=30)
