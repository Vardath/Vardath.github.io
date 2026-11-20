"""Offline integration tests: synthetic WikiText ZIP, no network or paid API."""
from pathlib import Path
import json
import zipfile
import pytest
from capability.wikitext import _paragraph_articles, digest_file, fetch_archive, import_archive


def _write_archive(path: Path, *, leaked: bool = False):
    articles = {
        'train': ('Alpha', 'The training article discusses stars, planets, distant galaxies, and navigation across complex environments. ' * 3),
        'valid': ('Beta', 'This validation article covers weather, instruments, and a completely separate account of another subject. ' * 3),
        'test': ('Gamma', 'This test article concerns economics, resources, markets, and ship transportation in space simulations. ' * 3),
    }
    if leaked:
        articles['test'] = ('Alpha', articles['train'][1])
    with zipfile.ZipFile(path, 'w') as z:
        for split, (title, body) in articles.items():
            z.writestr(f'wikitext-2/wiki.{split}.raw', f'\n = {title} = \n\n{body}\n')


def test_article_preserves_sections():
    src = ' = Alpha = \nFirst sentence.\n = = Side = = \nDetail.\n = Beta = \nSecond sentence.'
    result = list(_paragraph_articles(src))
    assert len(result) == 2
    assert result[0][0] == 'Alpha'
    assert 'Side' in result[0][1]


def test_publisher_partitions_preserved(tmp_path):
    source = tmp_path/'synthetic.zip'
    _write_archive(source)
    out = tmp_path/'prepared'
    report = import_archive(source, out, verify=False)
    assert list(report['counts']) == ['train', 'validation', 'test']
    assert report['verified_against_publisher_checksum'] is False
    for split in ('train', 'validation', 'test'):
        rows = [json.loads(x) for x in (out/f'{split}.jsonl').read_text().splitlines()]
        assert len(rows) == 1
        assert rows[0]['split'] == split
        assert rows[0]['license'] == 'CC BY-SA 4.0'
    assert len(digest_file(source)) == 64


def test_leakage_fails_closed(tmp_path):
    source = tmp_path/'leaked.zip'
    _write_archive(source, leaked=True)
    with pytest.raises(ValueError, match='leakage'):
        import_archive(source, tmp_path/'prepared', verify=False)
    assert not (tmp_path/'prepared'/'train.jsonl').exists()


def test_checksum_enforced(tmp_path):
    source = tmp_path/'synthetic.zip'
    _write_archive(source)
    with pytest.raises(ValueError, match='Wrong .* archive size'):
        import_archive(source, tmp_path/'prepared')


def test_empty_or_missing_split_fails(tmp_path):
    source = tmp_path/'partial.zip'
    with zipfile.ZipFile(source, 'w') as z:
        z.writestr('wikitext-2/wiki.train.raw', ' = Alpha = \n' + 'TEXT ' * 100)
    with pytest.raises(ValueError, match='wiki.valid.raw'):
        import_archive(source, tmp_path/'prepared', verify=False)


def test_huggingface_streaming_preserves_splits(tmp_path):
    from capability.wikitext import import_huggingface
    mapping = {
        'train': 'The alpha article covers technical information about physics and scientific methods.',
        'validation': 'The beta article explains gardens, planting and caring for seedlings in wet weather.',
        'test': 'The gamma article describes starship computers, propulsion and interstellar journeys.',
    }
    def loader(repo, config, *, split, streaming):
        assert repo == 'Salesforce/wikitext' and streaming is True
        return [{'text': ' = Heading = '}, {'text': mapping[split]}, {'text': 'More substantial details. '*6}]
    report = import_huggingface(tmp_path/'prepared', loader=loader)
    assert all(v['articles'] == 1 for v in report['counts'].values())
    assert 'Hugging Face' in report['acquisition']


def test_huggingface_leakage_rejected(tmp_path):
    from capability.wikitext import import_huggingface
    def loader(repo, config, *, split, streaming):
        return [{'text': ' = Identical = '}, {'text': 'The identical article paragraph is long enough to survive all filtering conditions.'*3}]
    with pytest.raises(ValueError, match='leakage'):
        import_huggingface(tmp_path/'prepared', loader=loader)
