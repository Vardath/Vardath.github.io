"""Bounded startup wait for the exact supervised Triad broker."""
from __future__ import annotations
import time


def wait_residency(health, expected_pid, validate, *, alive, cancelled, notify,
                   timeout=300, clock=time.monotonic, interval=1):
    """Poll without starting/replacing workers or relaxing readiness validation.

    Returns (models, result). A cancelled, exited, mismatched, failed or timed
    out broker is never treated as ready. The caller retains its original PID.
    """
    if cancelled.is_set():
        return None, {'status': 'cancelled', 'detail': 'Test stopped before residency check'}
    if type(expected_pid) is not int or expected_pid <= 0:
        return None, {'status': 'blocked', 'detail': 'No supervised broker existed when test began; start AI and rerun'}
    deadline = clock() + timeout
    notified = False
    while True:
        if cancelled.is_set():
            return None, {'status': 'cancelled', 'detail': 'Test stopped while waiting for model residency'}
        if not alive():
            return None, {'status': 'blocked', 'detail': 'Original supervised broker exited while waiting for readiness'}
        try:
            sample = health()
        except (OSError, ValueError, TypeError, KeyError):
            sample = None
        if isinstance(sample, dict):
            if sample.get('pid') not in (None, expected_pid):
                return None, {'status': 'blocked', 'detail': 'Broker PID changed; refusing to test a different process'}
            if sample.get('phase') in ('failed', 'error') or sample.get('error'):
                return None, {'status': 'blocked', 'detail': 'Supervised broker reported a startup error; inspect Processes'}
            if sample.get('ready') is True:
                try:
                    models = validate(sample, expected_pid)
                except (OSError, ValueError, TypeError, KeyError) as error:
                    return None, {'status': 'blocked', 'detail': str(error)[:300]}
                if cancelled.is_set():
                    return None, {'status': 'cancelled', 'detail': 'Test stopped before residency was accepted'}
                if not alive():
                    return None, {'status': 'blocked', 'detail': 'Original supervised broker exited before readiness acceptance'}
                return models, {'status': 'passed',
                    'detail': 'Three distinct model child PIDs ready in the supervised Triad broker.',
                    'evidence': {'models': {r: {'name': m['name'], 'pid': m['pid']} for r, m in models.items()}}}
        remaining = deadline - clock()
        if remaining <= 0:
            return None, {'status': 'blocked', 'detail': 'Supervised broker did not become ready within the bounded startup wait; inspect Processes and rerun'}
        if not notified:
            notify('Waiting for the original supervised broker to finish loading (cancellable)')
            notified = True
        cancelled.wait(min(interval, remaining))
