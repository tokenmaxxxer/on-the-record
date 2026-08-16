---
proposal: docs/issue-1682/proposals/change-cursor-shared-cache.md
---

# Hunt record — change-cursor-shared-cache

## after-proposal — stance 1: atomic-write failure paths in gh_cache.py / gh_delta.py

Verdict: FINDING — `_atomic_write_json`'s `tempfile.mkstemp()` call sits outside its own `try/except OSError` block, so any OSError raised while creating the temp file (e.g. permission-denied cache directory, disk full, missing dir race) propagates uncaught and crashes the whole `cached_get`/`fetch_delta` call — discarding an already-successful `gh api` response instead of the fail-open behaviour the module's own docstring promises for reads ("캐시가 없거나 깨졌으면 무조건 재조회로 폴백한다").
Kind: silent-failure
Seed: gates/gh_cache.py, gates/gh_delta.py (new modules, issue #1682 phase-2)
cap_seconds: n/a (not provided by dispatcher)
tier: n/a
diff_stat_lines: n/a
started_at: 2026-08-16T00:00:00Z
ended_at: 2026-08-16T00:20:00Z

### Reproduce
```
cd gates
python3 -c "
import subprocess, json
from pathlib import Path
import gh_cache

cache_root = Path('/tmp/gh_cache_test/cache')
cache_root.mkdir(parents=True, exist_ok=True)
cache_root.chmod(0o500)  # read+execute only -> mkstemp fails with PermissionError

def fake_run(cmd, cwd=None, capture_output=True, text=True):
    body = json.dumps({'a': 1})
    stdout = 'HTTP/2 200\r\netag: \"abc\"\r\n\r\n' + body
    return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr='')

data, ok, billed = gh_cache.cached_get('repos/acme/widget/issues', run=fake_run, cache_root=cache_root)
print('data=', data, 'ok=', ok, 'billed=', billed)
"
```

### Observed
```
Traceback (most recent call last):
  ...
  File "gh_cache.py", line 127, in cached_get
    _atomic_write_json(cache_file, {"etag": new_etag, "data": data})
  File "gh_cache.py", line 64, in _atomic_write_json
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".gh-cache-", suffix=".tmp")
  ...
PermissionError: [Errno 13] Permission denied: '/tmp/gh_cache_test/cache/.gh-cache-XXXXXXXX.tmp'
```
`cached_get` raises instead of returning `(data, True, 1)`. The identical pattern in `gh_delta._atomic_write_json` (same mkstemp-outside-try structure) means `fetch_delta` would likewise crash and lose the just-fetched `items`/`classification` result whenever the cursor directory becomes momentarily unwritable, rather than degrading gracefully (e.g. returning the fetched delta with a cache/cursor-write warning).

### Expected
`_atomic_write_json` should catch failures from `mkstemp` too (or the caller should catch and fall back), so a cache/cursor persistence failure never discards an already-successful `gh api` fetch — consistent with the fail-open policy the module documents for the read side.
