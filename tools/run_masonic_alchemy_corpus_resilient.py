#!/usr/bin/env python3
"""Acquisition-safe wrapper for the preregistered Masonic/alchemy corpus test.

This does not alter shard definitions, motif lexicons, matching, declared endpoints,
or statistics. It adds Retry-After/exponential backoff for public APIs and bounds the
Commons visual channel to the first 100 accepted records per target/control query so
that deep search pagination cannot turn API throttling into an inclusion rule.
"""
import json
import time
import urllib.error
import urllib.request

import test_masonic_alchemy_corpus as test


def resilient_fetch_json(url, tries=10):
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': test.USER_AGENT,
                    'Accept': 'application/json',
                },
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            err = e
            if e.code == 429:
                retry = e.headers.get('Retry-After')
                try:
                    delay = float(retry) if retry else min(60.0, 6.0 * (i + 1))
                except Exception:
                    delay = min(60.0, 6.0 * (i + 1))
                time.sleep(max(6.0, delay))
                continue
            if 500 <= e.code < 600:
                time.sleep(min(30.0, 3.0 * (i + 1)))
                continue
            raise
        except Exception as e:
            err = e
            time.sleep(min(30.0, 3.0 * (i + 1)))
    raise RuntimeError(f'fetch failed after resilient backoff {url}: {err}')


_original_commons_search = test.commons_search

def bounded_commons_search(query, tradition, cohort, limit=300):
    return _original_commons_search(query, tradition, cohort, min(limit, 100))


test.fetch_json = resilient_fetch_json
test.commons_search = bounded_commons_search

if __name__ == '__main__':
    test.main()
