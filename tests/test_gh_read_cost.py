#!/usr/bin/env python3
"""이슈 #1459: gh 읽기 비용 절감 3종(per_page=100, REST 벌크 코멘트 읽기,
ETag 조건부 재조회)이 관측 의미론을 바꾸지 않는지 검증한다 — 합성
스레드에 대해 mocked transport(`subprocess.run` 스텁)로 돌린다,
네트워크 없음.

`_issue_comments`(spawn.py)가 실제로 소비하는 필드는 `login`과 `body`
뿐이다(모든 호출부 grep 확인, 이슈 본문의 id/author login/createdAt 은
"세션이 실제로 소비하는 필드"로 스코프가 좁혀진다는 이슈의 §2 조건에
따라 이 두 필드로 좁힌다) — `test_read_equivalence`, `test_no_observation_loss`
는 이 두 필드로 비교한다.
"""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn


def _raw_comment(i: int) -> dict:
    return {"id": 1000 + i, "user": {"login": f"user{i}"}, "body": f"comment {i}",
            "created_at": f"2026-08-{(i % 28) + 1:02d}T00:00:00Z"}


class FakeGitHub:
    """`gh api` 를 흉내내는 스텁 transport — GitHub 컬렉션 엔드포인트처럼
    행동한다: 1페이지 조건부(`-i` + `If-None-Match`) 요청은 ETag 가
    일치하면 304(카운트 안 됨), 아니면 200 + `Etag`/`Link` 헤더를 낸다.
    무조건(`--paginate --slurp`) 요청은 나머지/전체 페이지를 낸다.
    `counted_calls` 는 이슈 #1459 의 "카운트된 호출 = non-304 응답"
    정의를 그대로 따른다."""

    def __init__(self, comments):
        self.comments = comments
        self.etag = f'"etag-for-{len(comments)}-comments"'
        self.counted_calls = 0
        self.calls = []

    def _pages_from(self, start_page):
        pages = []
        p = start_page
        total = len(self.comments)
        while (p - 1) * 100 < total:
            pages.append(self.comments[(p - 1) * 100: p * 100])
            p += 1
        return pages

    def run(self, cmd, **kwargs):
        self.calls.append(cmd)
        if "-i" in cmd:
            if_none_match = None
            if "-H" in cmd:
                hv = cmd[cmd.index("-H") + 1]
                if hv.lower().startswith("if-none-match:"):
                    if_none_match = hv.split(":", 1)[1].strip()
            if if_none_match == self.etag:
                out = "HTTP/2.0 304 Not Modified\r\n\r\n"
                return _Result(0, out)
            self.counted_calls += 1
            page1 = self.comments[:100]
            headers = f"Etag: {self.etag}\r\n"
            if len(self.comments) > 100:
                headers += 'Link: <https://api.example/comments?page=2>; rel="next"\r\n'
            out = "HTTP/2.0 200 OK\r\n" + headers + "\r\n" + json.dumps(page1)
            return _Result(0, out)
        start_page = 1
        if "page=2" in cmd:
            start_page = 2
        pages = self._pages_from(start_page)
        self.counted_calls += len(pages)
        return _Result(0, json.dumps(pages))


class _Result:
    def __init__(self, returncode, stdout):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def _patched(fake):
    orig_run = spawn.subprocess.run
    orig_slug = spawn._repo_slug

    def fake_run(cmd, **kwargs):
        return fake.run(cmd, **kwargs)

    spawn.subprocess.run = fake_run
    spawn._repo_slug = lambda root: "acme/repo"
    return orig_run, orig_slug


def _restore(orig_run, orig_slug):
    spawn.subprocess.run = orig_run
    spawn._repo_slug = orig_slug


class TestReadEquivalence(unittest.TestCase):
    def test_read_equivalence(self):
        """새 읽기 경로(ETag 프로브 + REST 벌크)가 반환하는 코멘트 집합이
        옛 무조건 전체 재조회 경로(`_issue_comments_uncached`)의 결과와
        소비 필드(login, body) 기준으로 바이트 동일한지 확인한다."""
        raw = [_raw_comment(i) for i in range(37)]
        with self._workdir() as root:
            fake = FakeGitHub(raw)
            orig_run, orig_slug = _patched(fake)
            try:
                old_raw, _n = spawn._issue_comments_uncached(root, "acme/repo", 1)
                old = [{"login": c["user"]["login"], "body": c["body"]} for c in old_raw]
                new, new_ok = spawn._issue_comments(root, 1)
            finally:
                _restore(orig_run, orig_slug)
        self.assertTrue(old_raw is not None)
        self.assertTrue(new_ok)
        self.assertEqual(old, new)

    def _workdir(self):
        import contextlib
        import tempfile

        @contextlib.contextmanager
        def _cm():
            with tempfile.TemporaryDirectory() as d:
                yield Path(d)
        return _cm()


class TestCountedCallsBounded(unittest.TestCase):
    def test_counted_calls_bounded(self):
        """N in {100, 1000}: 한 번의 전체-스레드 읽기의 카운트(non-304)
        호출 수는 ceil(N/100)+1 이하이고, 변경 없는 재조회는 0 회다
        (이슈 #1320 스타일의 상수-보장 형태)."""
        import contextlib
        import tempfile

        for n in (100, 1000):
            raw = [_raw_comment(i) for i in range(n)]
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                fake = FakeGitHub(raw)
                orig_run, orig_slug = _patched(fake)
                try:
                    _out1, ok1 = spawn._issue_comments(root, 1)
                    first_read_calls = fake.counted_calls
                    self.assertTrue(ok1)
                    bound = math.ceil(n / 100) + 1
                    self.assertLessEqual(first_read_calls, bound,
                                          f"n={n}: {first_read_calls} > {bound}")

                    calls_before = fake.counted_calls
                    _out2, ok2 = spawn._issue_comments(root, 1)
                    self.assertTrue(ok2)
                    repeat_calls = fake.counted_calls - calls_before
                    self.assertEqual(repeat_calls, 0,
                                      f"n={n}: repeat unchanged read counted {repeat_calls}")
                finally:
                    _restore(orig_run, orig_slug)


class TestCacheFailureFallback(unittest.TestCase):
    def test_cache_failure_fallback(self):
        """손상되었거나 없는 ETag 저장소는 무조건 전체 재조회로 저하될
        뿐, 빈/부분 결과를 내면 안 된다."""
        import tempfile

        raw = [_raw_comment(i) for i in range(150)]

        # case 1: 캐시 파일이 아예 없음 (첫 조회) — 이미 정상 경로지만
        # "없는 저장소" 케이스로 명시적으로 확인한다.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fake = FakeGitHub(raw)
            orig_run, orig_slug = _patched(fake)
            try:
                out, ok = spawn._issue_comments(root, 1)
            finally:
                _restore(orig_run, orig_slug)
            self.assertTrue(ok)
            self.assertEqual(len(out), 150)

        # case 2: 캐시 파일이 손상됨(파싱 불가) — fail-open 으로 전체
        # 무조건 재조회를 타야 하고, 빈/부분 결과를 내면 안 된다.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cache_path = spawn._etag_cache_path(root, 1)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text("{not valid json", encoding="utf-8")
            fake = FakeGitHub(raw)
            orig_run, orig_slug = _patched(fake)
            try:
                out, ok = spawn._issue_comments(root, 1)
            finally:
                _restore(orig_run, orig_slug)
            self.assertTrue(ok)
            self.assertEqual(len(out), 150)
            self.assertEqual(out[0], {"login": "user0", "body": "comment 0"})
            self.assertEqual(out[-1], {"login": "user149", "body": "comment 149"})

        # case 3: 캐시가 존재하지만 필드 모양이 기대와 다름(etag 없음) —
        # 역시 fail-open, 빈/부분 결과 금지.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cache_path = spawn._etag_cache_path(root, 1)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps({"raw": "not-a-list"}), encoding="utf-8")
            fake = FakeGitHub(raw)
            orig_run, orig_slug = _patched(fake)
            try:
                out, ok = spawn._issue_comments(root, 1)
            finally:
                _restore(orig_run, orig_slug)
            self.assertTrue(ok)
            self.assertEqual(len(out), 150)


class TestNoObservationLoss(unittest.TestCase):
    def test_no_observation_loss(self):
        """새 경로가 돌려주는 코멘트 집합은 무조건 재조회(옛 경로)의
        집합과 같다 — watch-coverage 회귀 잠금: 필터링/샘플링/커서링
        없음."""
        import tempfile

        for n in (0, 1, 100, 250):
            raw = [_raw_comment(i) for i in range(n)]
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                fake = FakeGitHub(raw)
                orig_run, orig_slug = _patched(fake)
                try:
                    unconditioned_raw, _n = spawn._issue_comments_uncached(root, "acme/repo", 1)
                finally:
                    _restore(orig_run, orig_slug)
                unconditioned = [{"login": c["user"]["login"], "body": c["body"]}
                                  for c in unconditioned_raw]

            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                fake = FakeGitHub(raw)
                orig_run, orig_slug = _patched(fake)
                try:
                    new, ok = spawn._issue_comments(root, 1)
                finally:
                    _restore(orig_run, orig_slug)
                self.assertTrue(ok)
                self.assertEqual(new, unconditioned, f"n={n}: observation loss")


if __name__ == "__main__":
    unittest.main()
