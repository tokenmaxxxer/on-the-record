---
proposal: docs/issue-1123/proposals/consult-raw-output-persist-complex-question.md
---

# Hunt record — consult-raw-output-persist-complex-question

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — `_persist_consult_raw_output()`'s path is embedded unquoted (no backticks) in the consult trace's outcome string, so `record_lint.py`'s existing "untracked working-tree path citation" guard (issue #1085, `git_tracked_path_reference_check`) never sees it and never fires, even though the raw-failure `.txt` file it points to is guaranteed to be untracked (freshly written, never committed).
Kind: silent-failure
Seed: spawn.py `_persist_consult_raw_output()` / `consult_cmd()` (new in this diff), compared against `gates/record_lint.py`'s `_PATH_REF` regex and `git_tracked_path_reference_check()` (pre-existing, issue #1085)
cap_seconds: 120
tier: default
diff_stat_lines: ~166 insertions across spawn.py, gates/test_consult_json_parse.py, docs/reports/consult-log.md
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:20:00Z

### Reproduce
```
cd /tmp/repro   # scratch git repo with a fake origin/main
git init -q; git branch main; git remote add origin .; git fetch origin main

# simulate the exact untracked raw-failure artifact _persist_consult_raw_output() creates
mkdir -p docs/issue-9999/reports/consult-raw-failures
echo "raw model output" > docs/issue-9999/reports/consult-raw-failures/20260813T000000Z-1.txt

# a record citing that path exactly the way spawn.py's f-string does today (unquoted):
cat > docs/issue-9999/reports/implementation.md <<'REC'
---
role: implementation
issue: 9999
loop_state: in-progress
---

- 2026-08-13T00:00:00Z | role=implementation | issue=9999 | question='q' | outcome='error: model output missing verdict JSON (raw saved at docs/issue-9999/reports/consult-raw-failures/20260813T000000Z-1.txt, tail: xyz)'
REC

CORE_OFF=1 python3 <path-to-repo>/gates/record_lint.py docs/issue-9999/reports/implementation.md
```

### Observed
```
record_lint: docs/issue-9999/reports/implementation.md — 위반 없음.
```
exit code 0 — no violation reported, despite the record citing a path to a file that has never been (and, by design, likely never will be) committed. Re-running the identical scenario with the same path wrapped in backticks (the format `_PATH_REF`/issue #1085 actually requires) correctly produces:
```
레코드가 git 이력에 한 번도 커밋된 적 없는 경로를 인용한다 (issue #1085): `docs/issue-9999/reports/consult-raw-failures/20260813T000000Z-1.txt` — 작업 트리에는 존재하지만 `git log --all --diff-filter=A` 결과가 비어 있다 — 커밋된 적 없는 임시 워킹트리 파일이다.
```
confirming the guard exists and works, but is silently defeated by spawn.py's unquoted format.

### Expected
Either `_persist_consult_raw_output()`'s path shouldn't be cited in a record at all, or `consult_cmd()`'s outcome string should backtick-quote `raw_path` (matching `_PATH_REF`'s `` `docs/...` `` convention used everywhere else in this codebase) so issue #1085's existing untracked-path guard actually covers the new artifact it was seemingly designed to catch. As written, every consult raw-output-persist failure line silently escapes the one check meant to flag "record cites a file nobody will ever be able to find in git history."
