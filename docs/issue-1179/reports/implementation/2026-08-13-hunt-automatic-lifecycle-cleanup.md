---
proposal: docs/issue-1179/proposals/automatic-lifecycle-cleanup.md
---

# Hunt record — automatic-lifecycle-cleanup

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — the build silently touched `docs/specs/reconciled-index.md`, a path absent from both the proposal's write set and `docs/issue-1179/reports/implementation.md`'s declared change list
Kind: silent-failure
Seed: `git show 57b391f`, `git show 31a6a20`, `git diff 6c399e5..HEAD` — proposal: docs/issue-1179/proposals/automatic-lifecycle-cleanup.md
cap_seconds: 180
tier: default
diff_stat_lines: 799 insertions, 53 deletions across 9 files (git diff --stat 6c399e5..HEAD)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:15:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1179-implementation
git diff --stat 6c399e5..HEAD
# docs/specs/reconciled-index.md appears in the diff (1 line changed: setup.md's hash)
git diff 6c399e5..HEAD -- docs/specs/reconciled-index.md
grep -n "reconciled-index" docs/issue-1179/proposals/automatic-lifecycle-cleanup.md docs/issue-1179/reports/implementation.md
# -> no matches in either file

# Show the gate that forced the touch:
cp docs/specs/reconciled-index.md /tmp/new-index.md
git show 6c399e5:docs/specs/reconciled-index.md > docs/specs/reconciled-index.md
python3 gates/spec_index.py
cp /tmp/new-index.md docs/specs/reconciled-index.md
```

### Observed
`git diff --stat` shows `docs/specs/reconciled-index.md | 2 +-` was modified by this work (the recorded SHA256 for `docs/handbooks/setup.md` changed from `240ea336…` to `bd14626a…`). Neither the proposal's write set nor `docs/issue-1179/reports/implementation.md`'s file list mentions `docs/specs/reconciled-index.md`. Reverting it to the pre-work version and running `python3 gates/spec_index.py` produces:
```
게이트 차단:
  - docs/handbooks/setup.md: 내용이 바뀌었는데 docs/specs/reconciled-index.md 의 기록된 해시와 다르다 (기록=240ea33619b4…, 실제=bd14626a298d…) — 의도된 변경이면 `python3 gates/spec_index.py --update` 로 재생성하고 관련 있다면 "Resolved ambiguities" 도 갱신하라
```
confirming this file's regeneration was mandatory to land the setup.md edit, yet it is not in the frozen write set.

### Expected
The proposal's write set (or the implementation report) should list `docs/specs/reconciled-index.md` as a path the build needed to touch, since any edit to a tracked doc (`docs/handbooks/setup.md`) mechanically forces `gates/spec_index.py --update` to regenerate this index or the gate blocks landing.
