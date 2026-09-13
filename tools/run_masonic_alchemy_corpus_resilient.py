#!/usr/bin/env python3
"""Transport-only wrapper for the preregistered Masonic/alchemy corpus test.

This does not alter shard definitions, motif lexicons, matching, endpoints, or statistics.
It only adds respectful Retry-After/exponential backoff for public APIs after the first
Commons run exposed HTTP 429 rate limiting.
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
                    delay = float(retry) if retry else min(90.0, 8.0 * (i + 1))
                except Exception:
                    delay = min(90.0, 8.0 * (i + 1))
                time.sleep(max(8.0, delay))
                continue
            if 500 <= e.code < 600:
                time.sleep(min(45.0, 4.0 * (i + 1)))
                continue
            raise
        except Exception as e:
            err = e
            time.sleep(min(45.0, 4.0 * (i + 1)))
    raise RuntimeError(f'fetch failed after resilient backoff {url}: {err}')


test.fetch_json = resilient_fetch_json

if __name__ == '__main__':
    test.main()
