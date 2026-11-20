"""Lossless UTF-8 byte-pair encoder trained entirely from user-approved text.

This implementation intentionally avoids pretrained tokenizer files. Pair merging
is bounded to regex word/space/punctuation segments, which keeps tokens stable.
It is a reference implementation; large corpus tokenizer training will need a
faster implementation in the subsequent scaling stage.
"""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import json
import re
from pathlib import Path

PIECES = re.compile(r'\s+|[^\W\d_]+|\d+|_+|[^\w\s]+', re.UNICODE)
SPECIAL_NAMES = ('<|bos|>', '<|system|>', '<|user|>', '<|assistant|>', '<|eos|>', '<|pad|>')


def _merge(sequence: tuple[int, ...], left: int, right: int, new_id: int) -> tuple[int, ...]:
    out = []
    i = 0
    while i < len(sequence):
        if i < len(sequence) - 1 and sequence[i] == left and sequence[i+1] == right:
            out.append(new_id)
            i += 2
        else:
            out.append(sequence[i])
            i += 1
    return tuple(out)


class ByteBPE:
    def __init__(self, merges: list[tuple[int, int]] | None = None):
        self.merges = [tuple(pair) for pair in (merges or [])]
        self._rank = {pair: n for n, pair in enumerate(self.merges)}
        self.byte_values = [bytes([i]) for i in range(256)]
        for left, right in self.merges:
            if left >= len(self.byte_values) or right >= len(self.byte_values):
                raise ValueError('Invalid merge references')
            self.byte_values.append(self.byte_values[left] + self.byte_values[right])
        self.special = {name: len(self.byte_values) + i for i, name in enumerate(SPECIAL_NAMES)}

    @property
    def vocab_size(self) -> int:
        return 256 + len(self.merges) + len(SPECIAL_NAMES)

    @classmethod
    def train(cls, texts, *, merges: int = 384, max_chars: int = 1_000_000,
              min_pair_count: int = 2):
        if merges < 0 or max_chars < 1 or min_pair_count < 1:
            raise ValueError('Bad BPE training parameters')
        counts = Counter()
        consumed = 0
        for text in texts:
            if consumed >= max_chars:
                break
            text = text[:max_chars-consumed]
            consumed += len(text)
            for match in PIECES.finditer(text):
                seq = tuple(match.group().encode('utf-8'))
                if len(seq) > 1:
                    counts[seq] += 1
        if not counts:
            raise ValueError('No training text of length >=2')
        learned = []
        for _ in range(merges):
            pair_counts = Counter()
            for seq, n in counts.items():
                for a, b in zip(seq, seq[1:]):
                    pair_counts[a,b] += n
            if not pair_counts:
                break
            pair, frequency = max(pair_counts.items(), key=lambda kv: (kv[1], -kv[0][0], -kv[0][1]))
            if frequency < min_pair_count:
                break
            next_id = 256 + len(learned)
            updated = Counter()
            for seq, count in counts.items():
                updated[_merge(seq, pair[0], pair[1], next_id)] += count
            counts = updated
            learned.append(pair)
        return cls(learned)

    @lru_cache(maxsize=32_768)
    def _encode_piece(self, piece: str) -> tuple[int, ...]:
        ids = tuple(piece.encode('utf-8'))
        while len(ids) > 1:
            matches = [(self._rank[(a,b)], a, b) for a,b in zip(ids, ids[1:]) if (a,b) in self._rank]
            if not matches:
                break
            _, a,b = min(matches)
            ids = _merge(ids,a,b,256+self._rank[(a,b)])
        return ids

    def encode(self, text: str) -> list[int]:
        # This is text encoding, not the chat serializer. Literal strings such
        # as <|eos|> in user text remain literal text, not control tokens.
        ids = []
        for match in PIECES.finditer(text):
            ids.extend(self._encode_piece(match.group()))
        if ''.join(match.group() for match in PIECES.finditer(text)) != text:
            raise ValueError('Unexpected character unsupported by pretokenizer')
        return ids

    def decode(self, ids: list[int]) -> str:
        raw = bytearray()
        for token in ids:
            if token < 0 or token >= len(self.byte_values):
                raise ValueError(f'{token} is not a text token')
            raw.extend(self.byte_values[token])
        return raw.decode('utf-8', errors='strict')

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'format':'vardath-byte-bpe-v1', 'merges': self.merges,
                                    'special': self.special}, indent=2), encoding='utf-8')

    @classmethod
    def load(cls, path: Path):
        obj = json.loads(path.read_text(encoding='utf-8'))
        if obj.get('format') != 'vardath-byte-bpe-v1':
            raise ValueError('Unknown tokenizer format')
        inst = cls(obj['merges'])
        if inst.special != obj['special']:
            raise ValueError('Malformed special token table')
        return inst
