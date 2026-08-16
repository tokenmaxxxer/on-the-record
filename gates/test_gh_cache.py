from __future__ import annotations
from types import SimpleNamespace

import gh_cache


def _response(status: int, headers: dict, body: str) -> SimpleNamespace:
    head_lines = [f"HTTP/2 {status}"] + [f"{k}: {v}" for k, v in headers.items()]
    stdout = "\r\n".join(head_lines) + "\r\n\r\n" + body
    return SimpleNamespace(returncode=0, stdout=stdout)


def test_two_consumers_second_gets_304_revalidation_from_disk(tmp_path):
    """issue #1682 amended acceptance: two consumers -> at most one FULL-BODY
    fetch; the second consumer's conditional 304 revalidation counts as a
    cache hit and serves the body from disk, not from the (empty) 304
    response."""
    url = "repos/acme/widget/issues"
    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        if len(calls) == 1:
            assert "If-None-Match" not in " ".join(cmd)
            return _response(200, {"etag": '"abc123"'}, '[{"number": 1}]')
        assert "If-None-Match: \"abc123\"" in " ".join(cmd)
        return _response(304, {}, "")

    data1, ok1, billed1 = gh_cache.cached_get(url, run=fake_run, cache_root=tmp_path)
    data2, ok2, billed2 = gh_cache.cached_get(url, run=fake_run, cache_root=tmp_path)

    assert ok1 and ok2
    assert len(calls) == 2
    assert data1 == [{"number": 1}]
    assert data2 == [{"number": 1}]
    assert billed1 == 1
    assert billed2 == 1


def test_cold_cache_behaves_like_unconditional_fetch(tmp_path):
    url = "repos/acme/widget/issues"
    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        assert "If-None-Match" not in " ".join(cmd)
        return _response(200, {"etag": '"xyz"'}, '[{"number": 7}]')

    data, ok, billed = gh_cache.cached_get(url, run=fake_run, cache_root=tmp_path)

    assert ok is True
    assert data == [{"number": 7}]
    assert billed == 1
    assert len(calls) == 1


def test_cache_write_is_atomic_no_stray_temp_files(tmp_path):
    url = "repos/acme/widget/issues"

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        return _response(200, {"etag": '"e1"'}, "[]")

    gh_cache.cached_get(url, run=fake_run, cache_root=tmp_path)

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert not files[0].name.startswith(".gh-cache-")


def test_broken_cache_file_falls_back_to_unconditional_fetch(tmp_path):
    url = "repos/acme/widget/issues"
    cache_file = gh_cache._cache_file(tmp_path, url)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("not json", encoding="utf-8")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        assert "If-None-Match" not in " ".join(cmd)
        return _response(200, {"etag": '"e2"'}, '[{"number": 1}]')

    data, ok, billed = gh_cache.cached_get(url, run=fake_run, cache_root=tmp_path)
    assert ok is True
    assert data == [{"number": 1}]
