---
issue: 2543
role: implementation
author: implementation
loop_state: landed
upstream: []
code_under_review:
  - path: gates/closure_sweep.py
    sha: same-commit
  - path: gates/gates.py
    sha: same-commit
  - path: board.py
    sha: same-commit
  - path: docs/specs/requirements.md
    sha: same-commit
type: fix
breaking: none — `_current_accumulation_counts()`'s returned dict shape changed (`shape5_files` key removed, `shape1_ok` key added), but grep confirmed (see below) no caller outside this file reads either key
verdict: pass
---

# issue-2543 — implementation record

## What was done

canonical: this session's own executed checks, quoted verbatim under
"Acceptance verification" below (checks 1-5) — every claim in this section
is discharged there, not asserted here.

Two retirement remnants, both fixed in commit `e380f7f7` on top of
`480d1a78`:

**A — `gates/closure_sweep.py`, the trend metric that couldn't fail loudly.**

- `_current_accumulation_counts()`: removed the shape5 block (`git ls-files
  roles/*.json` + `shape5_files` key) entirely. Docstring now states why:
  `roles/` was deleted whole by #2539 (consolidated into one file,
  `spawn_roles.json`), so shape 5 ("many near-identical files") has no
  subject left to count.
- Fixed the identical failed-call-reports-as-zero pattern in shape1 (the
  survivor): `_current_accumulation_counts()` now returns `{"shape1_sites":
  int, "shape1_ok": bool}` — `shape1_ok` is `p.returncode == 0` from the
  `git ls-files *.py` call, tracked explicitly instead of collapsed into
  the count.
- `accumulation_trend()`: skips delta computation *and* skips overwriting
  the on-disk trend state when `shape1_ok` is `False` — a failed call no
  longer poisons the next tick's delta with a spurious zero.
- `format_accumulation_trend()`: prints the literal
  `"accumulation-trend: shape1_sites=ERROR(git-ls-files-failed)"` (no
  number at all) when `shape1_ok` is `False`, instead of a count that could
  be mistaken for a genuine zero. Both cases run and quoted side by side
  under check 2 below.

**B — `docs/specs/requirements.md` / `gates/gates.py`, the 75%-dangling registry.**

- `docs/specs/requirements.md`: R002/R003/R004's `check:` field converted
  from `gates/test_upstream_finding_channel.py::<test-name>` (a path that
  no longer exists — that file was deleted when the plugin's own pytest
  suite was retired, per #2137) to `UNVERIFIABLE: <reason>` naming both
  #2137 and the suite retirement. `quote`/`source_issue`/`status` on all
  three entries are byte-identical to before; no entry deleted or
  renumbered. R001 untouched. Before/after quoted under check 3 below.
- `gates/gates.py`: added `requirement_registry_unverifiable_summary(d,
  cfg) -> str`, parsing the same registry as `requirement_registry()` and
  returning a summary line — quoted, with the exact executed output
  (`derived: python3 -c "...gates.requirement_registry_unverifiable_summary(Path('.'), {})..."`),
  under check 4 below. Deliberately **not** folded into
  `requirement_registry()`'s own `list[str]` return, because that list also
  feeds `gates/ci.py`'s `main()`, which treats any non-empty entry as a
  hard CI-blocking failure; permanently injecting a summary line there
  would make every future PR fail CI merge-gate forever once any registry
  entry is `UNVERIFIABLE`.
- `board.py`: `gate_report()` — the post-session, non-blocking advisory
  report `spawn.py` prints after every session (`spawn.py:3778`, the exact
  site the issue names as printing "요구사항 체크 소실 on every spawn") — now
  calls `requirement_registry_unverifiable_summary()` inside the same
  `try/except Exception` block as `ci.check()`, and appends its result as
  an extra line to the report regardless of whether `bad` was empty.
  Exercised by a real (non-`--dry-run`) spawn under check 5 below.

## Why

canonical: this session's own executed checks under "Acceptance
verification" below (checks 1-5) back every claim made in this section.

Both remnants shared the operator-named root lens: a signal that reports
its own breakage as a clean result. The fix in each case is the same
shape: stop collapsing "couldn't check" into the same value as "checked,
successfully, and the count is zero" — track the failure/skip explicitly
in a separate field, and print it as literal text that shares no substring
with a real zero (check 2), rather than adding a general duplicate-detector
(rejected by #419/#424) or reintroducing a test file (forbidden by #2137).

`requirement_registry_unverifiable_summary()` was kept as a separate
function rather than added to `requirement_registry()`'s blocking list
specifically because `requirement_registry()` is dual-consumed: once by
`board.gate_report()` (advisory, never blocks) and once by `gates/ci.py`'s
`main()` (blocking CI gate, exit 1 on any non-empty `bad` —
`derived: gates/ci.py:707-711`, `if not bad: print("게이트 통과"); ... else:
print("게이트 차단:"); ...; return 1`). Silencing the "요구사항 체크 소실"
complaint would have been the disease the issue named; making the CI
merge-gate permanently red once any entry is `UNVERIFIABLE` would have
been a different, equally real regression — surfacing the count needed a
channel that isn't also a merge blocker.

## What did not work

None — no reverted approach, no abandoned attempt.

## Acceptance verification

**Check 1 — shape5 removed, record states why it has no subject.**

canonical: `gates/closure_sweep.py` `_current_accumulation_counts()`
docstring (quoted from the file as committed in `e380f7f7`):
```
이슈 #2543: 모양 5(`roles/*.json` 근-중복 파일 더미)는 여기서 뺐다 —
#2539 가 `roles/` 를 통째로 지우고 `spawn_roles.json` 파일 하나로
합쳤으므로, 셀 대상 자체가 없다(이사 간 게 아니라 없어졌다). 상수 0을
영원히 내보내는 키를 남기는 대신 지운다 — 한 가지 값만 낼 수 있는
지표는 아예 없는 지표보다 나쁘다.
```
No `shape5_files` key remains anywhere in the returned dict —
derived: `grep -n "shape5" gates/*.py board.py spawn.py` — result: only 2
hits, both in `closure_sweep.py`: the `_current_accumulation_counts`
docstring comment above, and a historical-incident mention inside the
`accumulation_trend` docstring (`shape5_files=0 (-87)` misfire, cited as
motivation). No live key or reader remains.

**Check 2 — failed `git ls-files` in shape1 distinguishable from a genuine zero.**

Simulated both cases directly against `_current_accumulation_counts()` /
`format_accumulation_trend()` post-fix:

acceptance: genuine-zero case (fresh empty git repo, no `.py` files) —
checked: `python3 -c "..."` against a throwaway `git init` repo — result:
```
accumulation-trend: no prior tick data (first run) — shape1_sites=0
```

acceptance: failure case (`root=/nonexistent-root-2543`, so `git -C
<root> ls-files` exits non-zero) — checked: same script against a bad
root — result:
```
accumulation-trend: shape1_sites=ERROR(git-ls-files-failed)
```

Side by side, the two lines share no substring after `accumulation-trend:
` — one prints `shape1_sites=0`, the other prints
`shape1_sites=ERROR(git-ls-files-failed)` with no digit anywhere.

**Check 3 — 3 dangling checks converted to `UNVERIFIABLE: <reason>`, entries otherwise intact.**

Before (R002, `git show 480d1a78:docs/specs/requirements.md` — this repo's
HEAD before this issue's commit):
```
## R002

quote: Consumers file ISSUES ONLY — never PRs. The channel must not offer, scaffold, or allow an upstream PR path from consumer sessions.
source_issue: 1131
check: gates/test_upstream_finding_channel.py::test_pr_creation_denied
status: enforced
```

After (`docs/specs/requirements.md`, this commit):
```
## R002

quote: Consumers file ISSUES ONLY — never PRs. The channel must not offer, scaffold, or allow an upstream PR path from consumer sessions.
source_issue: 1131
check: UNVERIFIABLE: gates/test_upstream_finding_channel.py was deleted when the plugin's own pytest suite was retired (#2137 — persistent test files are not a default deliverable); no replacement test file was reintroduced per that policy
status: enforced
```
`quote`/`source_issue`/`status` byte-identical; only `check:` changed.
R003/R004 got the identical treatment (byte-identical `UNVERIFIABLE:`
reason string) — derived: `git diff 480d1a78..e380f7f7 -- docs/specs/requirements.md`
— result: 3 hunks, each changing exactly one `check:` line, no entry
added/removed/renumbered (R001 absent from the diff, R002-R004 each show
exactly one `-`/`+` line pair).

**Check 4 — UNVERIFIABLE count surfaced where the missing-check complaint is surfaced.**

Before (this repo at `480d1a78`, `gates.requirement_registry(Path('.'),
{})` run directly) — checked: `git stash` to `480d1a78`, then
`python3 -c "import sys; sys.path.insert(0,'gates'); import gates; from pathlib import Path; print(gates.requirement_registry(Path('.'), {}))"`
— result:
```
["요구사항 체크 소실: R002 (issue #1131) — check='gates/test_upstream_finding_channel.py::test_pr_creation_denied' 이 가리키는 경로가 HEAD 에 없다", "요구사항 체크 소실: R003 (issue #1131) — check='gates/test_upstream_finding_channel.py::test_no_filing_before_confirmation' 이 가리키는 경로가 HEAD 에 없다", "요구사항 체크 소실: R004 (issue #1131) — check='gates/test_upstream_finding_channel.py::test_unreachable_upstream_falls_back_to_local_draft' 이 가리키는 경로가 HEAD 에 없다"]
```
3 blocking complaints, and nothing anywhere reporting the 3-of-4
proportion — exactly the "silently invisible" state the issue named.

After (same command, post-fix) — checked: `python3 -c "import sys; sys.path.insert(0,'gates'); import gates; from pathlib import Path; print(gates.requirement_registry(Path('.'), {})); print(gates.requirement_registry_unverifiable_summary(Path('.'), {}))"`
— result:
```
[]
요구사항 레지스트리: 3 of 4 체크가 UNVERIFIABLE
```
The blocking list (`bad`) is empty — the 3 "요구사항 체크 소실" complaints
are gone because those entries no longer claim a check path that doesn't
exist. The proportion (3 of 4) is now printed by the new function, called
from the same site (`board.gate_report()`) that used to print the
missing-check complaints — quoted directly under check 5 below, inside
the actual advisory report a real spawn prints.

**Check 5 — a real (non-`--dry-run`) spawn runs end to end with no `요구사항 체크 소실` line.**

Ran `python3 spawn.py implementation "trivial no-op verification task for
issue 2543 gate_report check" -C <disposable clone of this branch's tip>
--no-contract --max-turns 3 --model haiku` (no `--dry-run`), against a
disposable local clone whose `origin/main` was re-pointed at this branch's
own tip (`e380f7f7`) to simulate a post-merge empty diff for the
pre-session protected-path classifier — same technique #2539's record used
for the identical check (`docs/issue-2539/reports/implementation.md`,
"check 5").

acceptance: real spawn's own stderr, the `[게이트]` block printed by
`board.gate_report()` after the nested session completed — checked:
non-dry-run `spawn.py` run against the disposable clone — result:
```
[게이트] 확인 필요:
  - 보호 경로 변경: gates/closure_sweep.py
  - 보호 경로 변경: gates/gates.py
  - roles/specs/brand-design.spec.json: 인덱스에 있지만 파일이 없다
  - roles/specs/content-design.spec.json: 인덱스에 있지만 파일이 없다
  - roles/specs/market-analysis.spec.json: 인덱스에 있지만 파일이 없다
  (요구사항 레지스트리: 3 of 4 체크가 UNVERIFIABLE)
[implementation] silent-failure, 보드 무변화, 비용 $0.02
```
No `요구사항 체크 소실` line anywhere in the output. The `보호 경로 변경`
lines are the pre-session protected-path gate correctly flagging that this
very session edited `gates/closure_sweep.py`/`gates/gates.py` — expected
and unrelated to this check; the `roles/specs/*.spec.json` lines are a
pre-existing, unrelated stale-index condition inherited from #2539
(`spec_index.check`), not touched by this issue. The nested haiku session
itself asked for clarification and made no board change (`silent-failure,
보드 무변화`) — the check only needed `_spawn_one()` to reach
`gate_report()` after a real session exit, which it did.

## Upstream basis

None — this issue's fixes are self-contained in `gates/closure_sweep.py`,
`gates/gates.py`, `board.py`, and `docs/specs/requirements.md`; no other
`docs/issue-*/` record or external commit is built upon.

## Open findings

None outstanding.

## Next steps

None. Issue #2543 is fully discharged by this commit.

skill-verdict: work-in-english — applied: invoked; loaded before writing
this record and all code comments/docstrings/commit messages, per the
trigger (Korean-language task instructions on an English-repo coding
task) — repo-bound text (commit message, docstrings, this record's prose)
written in English; code comments that were already Korean in the
surrounding file (`gates/closure_sweep.py`, `gates/gates.py`) were
extended in Korean to match the existing in-file convention rather than
mixed languages within one docstring block.
