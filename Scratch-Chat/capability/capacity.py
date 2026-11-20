"""Transparent compute/storage planner for original (random-weight) transformer training.

Uses the 6*N*D approximation for dense transformer training compute; excludes
optimizer overhead, attention quadratic terms, tokenization, evaluation, and I/O.
Planning is not proof of model quality. Time estimates require measured tokens/s.
"""
from __future__ import annotations
import argparse
import json
import math


def estimate(parameters: int, tokens: int, *, tokens_per_second: float | None = None,
             bytes_per_parameter: int = 16) -> dict:
    if parameters < 1 or tokens < 1 or bytes_per_parameter < 1:
        raise ValueError('Positive model size, token count and bytes/parameter required')
    if tokens_per_second is not None and tokens_per_second <= 0:
        raise ValueError('Throughput must be positive')
    result = {
        'parameters': parameters,
        'training_tokens': tokens,
        'parameter_to_token_ratio': round(tokens/parameters, 3),
        'dense_training_flops_approx': 6 * parameters * tokens,
        'approx_train_state_gib': round(parameters * bytes_per_parameter / 1024**3, 3),
        'assumptions': [
            '6*N*D is a rough dense-transformer forward+backward approximation, not a benchmark',
            'Memory estimate includes model, gradients and optimizer states but not activations or caches',
            'Data and compute do not guarantee reasoning, instruction following or safe autonomy',
        ],
    }
    if tokens_per_second is not None:
        seconds = tokens / tokens_per_second
        result['measured_machine_projection'] = {
            'throughput_tokens_per_second': tokens_per_second,
            'training_hours_at_that_rate': round(seconds / 3600, 2),
            'training_days_at_that_rate': round(seconds / 86400, 2),
            'warning': 'Assumes sustained effective training throughput on the same hardware and configuration',
        }
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description='Estimate scratch-model training requirements')
    p.add_argument('--parameters', type=int, default=9514368)
    p.add_argument('--tokens', type=int, default=10_000_000)
    p.add_argument('--measured-tokens-per-second', type=float)
    a = p.parse_args(argv)
    print(json.dumps(estimate(a.parameters, a.tokens,
                              tokens_per_second=a.measured_tokens_per_second), indent=2))


if __name__ == '__main__':
    main()
