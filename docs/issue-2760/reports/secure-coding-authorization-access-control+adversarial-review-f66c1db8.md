---
issue: 2760
role: secure-coding-authorization-access-control+adversarial-review-f66c1db8
author: secure-coding-authorization-access-control+adversarial-review-f66c1db8
skills: secure-coding-authorization-access-control (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: fix
breaking: false
verdict: pass — all six broken-git conditions on a relative exempt-suffix payload now deny, matching the activation check; healthy-git exemption and deny paths unchanged; bug confirmed to predate PR #2752 by executing the merge-base script
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: same-commit
---

# issue-2760 — secure-coding-authorization-access-control+adversarial-review-f66c1db8 record

## What was done

Fixed `on-the-record/hooks/deliverable-guard.sh`'s exemption-resolution
path (`_git_root_from` plus the `root_relative_n` computation that backs
`EXEMPT_SUFFIXES` and `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`) so it fails
closed when git cannot answer, matching the activation check PR #2752
already hardened.

canonical: `git diff origin/main -- on-the-record/hooks/deliverable-guard.sh` (same-commit) — result: 1 file changed, 52 insertions(+), 6 deletions(-)

Two changes, both confined to `_git_root_from` and its caller:

1. `_git_root_from` now returns one of three distinct values instead of
   collapsing two different situations into a single `None`: a real
   root path (git answered with a usable absolute toplevel), `None`
   (git *confidently* said "not a git repository" — a real answer), or
   a new sentinel `_GIT_UNKNOWN` (git could not answer at all: missing
   binary, timeout/hang, a nonzero exit with no recognizable message,
   or a zero exit with empty/non-absolute stdout).
   derived: `sed -n '183,238p' on-the-record/hooks/deliverable-guard.sh` (same-commit)

2. The exemption-resolution caller now tracks
   `_git_unknown_for_exemption` and gates the two `root_relative_n`-based
   membership checks (`EXEMPT_SUFFIXES`, `PRODUCT_CAPTURE_PRIORITIES_DIR_RE`)
   on it being `False`. When git could not answer, the write is no
   longer granted the exemption via the raw-path fallback — it falls
   through to the existing hardened activation check further down,
   which independently calls git again and denies for the same broken
   condition. `PRODUCT_CAPTURE_ISSUE_RE` (matched against raw `n`
   directly, never through `_git_root_from`) is untouched — it does not
   depend on git and was never part of this bug.
   derived: `sed -n '239,270p' on-the-record/hooks/deliverable-guard.sh` (same-commit)

The raw-path fallback itself is kept, not deleted: when
`_git_root_from` returns `None` (git *confirmed* there is no repository
here), `root_relative_n` still falls back to the raw path, so a
legitimate exempt write outside any git repo keeps working exactly as
before.

## Why

Traced the six broken-git conditions through the exemption code by
reading `_git_root_from`/`_run_git` and the caller at
`on-the-record/hooks/deliverable-guard.sh:222-241` (pre-fix, i.e. the
version at this branch's `HEAD` before this commit — `git show HEAD:on-the-record/hooks/deliverable-guard.sh`):

- git missing / errors / hangs: `_run_git` catches `OSError`/`TimeoutExpired`
  and returns `None`; `_git_root_from` then also returned `None`
  (pre-fix) because its only check was `if r is not None and r.returncode == 0`.
- garbage stdout / empty stdout: `_run_git` returns a real
  `CompletedProcess` with `returncode == 0`; pre-fix, `_git_root_from`
  trusted `r.stdout.strip()` as a literal root path whenever it was
  non-empty (accepting garbage) and returned `None` only when it was
  empty.
- In every one of these five cases, `_git_root_from` returning `None`
  was indistinguishable from the one case where `None` is a real
  answer: git confidently reporting "not a git repository". The caller
  then fell back to `root_relative_n = n` (the raw, unresolved
  `file_path`) — and a payload whose relative `file_path` is already
  exactly an `EXEMPT_SUFFIXES` entry trivially matches its own
  unresolved raw form, regardless of what (if anything) git said.

canonical: `sed -n '267,309p' on-the-record/hooks/deliverable-guard.sh` (same-commit) — the activation check's own `_run_git(["rev-parse", "--is-inside-work-tree"], probe)` call and its `deny("could not determine whether ...")` branches for `r is None` and for a non-`true`/`false` result, unchanged by this fix.

The fix separates "git said no repo here" (a real, safe-to-trust
answer — the raw-path fallback is fine) from "git could not answer"
(nothing was learned — the exemption must not be granted on a guess).
Rather than have the exemption path invent its own denial, an unknown
answer simply lets the write fall through to that existing activation
check, which already asks git independently and already fails closed
on exactly this class of failure (issue #2659 / PR #2752) — reusing
that logic instead of duplicating it satisfies rule 7 of the
`secure-coding-authorization-access-control` skill (apply the same
permission check on every entry path, not a special case on one) and
rule 1 (deny by default when no rule confidently matches).

Considered and rejected: making `_git_root_from`'s ambiguous case call
`deny()` directly from inside the exemption block. Rejected because it
would duplicate the activation check's git call and its exact error
message under a second, parallel deny path — two places that must stay
in sync — instead of one obviously-already-correct one. Falling through
to the existing check costs one extra `_run_git` call only on the rare
git-broken path (see the timing evidence below), never on the common
healthy-git path.

## Evidence

### Acceptance check 1+2 — six conditions, relative exempt-suffix payload, before/after, plus healthy-git

Harness: `/tmp/dg_probe.py` (ad-hoc, not committed — a real git fixture
repo plus a "no-repo" fixture directory verified live to have no `.git`
ancestor, a real `docs/specs/approvers.md`-shaped relative payload
against each hook variant, run as real `bash` subprocesses over real
stdin JSON, same harness shape as `test_deliverable_guard_worktree_submodule.py`).
Five broken-git conditions are simulated with a fake `git` executable
placed first on `PATH`; the sixth (git missing) simply omits it; "no
repo" uses the real git binary against a directory with no `.git`
ancestor.

derived: `python3 /tmp/dg_probe.py /tmp/deliverable-guard-prefix.sh "BEFORE"` (`/tmp/deliverable-guard-prefix.sh` = `git show HEAD:on-the-record/hooks/deliverable-guard.sh`, i.e. this branch before this fix, identical to origin/main) — result:
```
condition            exempt-suffix rc   time     deny-shaped rc   stderr(exempt)
healthy git          rc=0        0.05s   rc=2       0.04s  ''
a' git missing       rc=0        0.03s   rc=2       0.04s  ''
b' git errors        rc=0        0.04s   rc=2       0.05s  ''
c1' garbage stdout   rc=0        0.04s   rc=2       0.04s  ''
c2' empty stdout     rc=0        0.03s   rc=2       0.03s  ''
d' hangs             rc=0       10.04s   rc=2      20.06s  ''
e' no repo           rc=0        0.04s   rc=0       0.03s  ''
```
All 6/6 broken-git conditions ALLOW (rc=0) the exempt-suffix payload —
reproduces the issue exactly, including the timing tell (hang: 10.04s /
one `_run_git` call for the exemption path vs. 20.06s / two calls for
the deny-shaped path).

derived: `python3 /tmp/dg_probe.py /tmp/deliverable-guard-postfix.sh "AFTER"` (working tree with this fix applied) — result:
```
condition            exempt-suffix rc   time     deny-shaped rc   stderr(exempt)
healthy git          rc=0        0.04s   rc=2       0.04s  ''
a' git missing       rc=2        0.03s   rc=2       0.03s  'orchestrate: could not determine whether docs/specs/approvers.md is in'
b' git errors        rc=2        0.03s   rc=2       0.03s  'orchestrate: could not determine whether docs/specs/approvers.md is in'
c1' garbage stdout   rc=2        0.04s   rc=2       0.03s  'orchestrate: could not determine whether docs/specs/approvers.md is in'
c2' empty stdout     rc=2        0.04s   rc=2       0.03s  'orchestrate: could not determine whether docs/specs/approvers.md is in'
d' hangs             rc=2       20.05s   rc=2      20.05s  'orchestrate: could not determine whether docs/specs/approvers.md is in'
e' no repo           rc=0        0.03s   rc=0       0.03s  ''
```
After the fix: the 5 conditions where git could not answer at all
(missing/errors/garbage/empty/hang) now DENY (rc=2) with the same
"could not determine..." message the activation check already used —
matching the deny-shaped payload's rc on every condition. `d' hangs`
now costs 20.05s (two `_run_git` calls), the same shape the deny path
already had — the timing tell from the issue disappears because the
exemption path now does the same work as the deny path when git is
unresponsive. `e' no repo` still ALLOWs (rc=0) on both payloads — by
design: the activation check itself allows here too (a path confirmed
to be outside any git repo is "not this gate's business" per the
hook's existing comment), so parity with the activation check means
matching *this* outcome too, not turning it into a new deny.
`healthy git` is unchanged in both directions (rc=0 exempt, rc=2 deny).

### Acceptance check 3 — merge-base of PR #2752, six conditions, execution not inference

`git show --format="%H %P" -s 67ba4644` (the #2752 fix commit) → single
parent `43f86ce54a3209221461d8547657eaf8051d4a3c` — the merge-base.
Extracted with `git show 43f86ce5:on-the-record/hooks/deliverable-guard.sh > /tmp/deliverable-guard-mergebase.sh`.

derived: `python3 /tmp/dg_probe.py /tmp/deliverable-guard-mergebase.sh "MERGE-BASE"` — result:
```
condition            exempt-suffix rc   time     deny-shaped rc   stderr(exempt)
healthy git          rc=0        0.03s   rc=2       0.03s  ''
a' git missing       rc=0        0.04s   rc=2       0.03s  ''
b' git errors        rc=0        0.03s   rc=2       0.03s  ''
c1' garbage stdout   rc=0        0.03s   rc=2       0.03s  ''
c2' empty stdout     rc=0        0.02s   rc=2       0.03s  ''
d' hangs             rc=0        0.03s   rc=2       0.03s  ''
e' no repo           rc=0        0.03s   rc=0       0.02s  ''
```
**Answer: the bug predates PR #2752.** 6/6 broken-git conditions ALLOW
the exempt-suffix payload at the merge-base too — same observable
defect. The mechanism differs, though, and that difference is worth
recording:

derived: `grep -n "subprocess" /tmp/deliverable-guard-mergebase.sh` — result: no match; the embedded Python's only import line is `import json, os, posixpath, re, sys` (no `subprocess`).

At the merge-base, `_git_root_from` never calls the `git` binary at
all — it walks the filesystem with `os.path.isdir(<probe>/".git")`
instead (the same walk issue #2659 later replaced with `git rev-parse`
for the activation check only). So "git missing/errors/garbage/empty/hang"
are all inert at the merge-base — the `d' hangs` row costs 0.03s there,
not 10s, because there is no subprocess to hang. The bug at the
merge-base and the bug this issue fixes are the same *symptom* (a
relative exempt-suffix payload bypasses activation under conditions
where the resolution path can't, or pre-#2752 doesn't need to, get a
confident answer) produced by two different root causes across the
#2659/#2752 refactor — PR #2752 swapped the activation check's
resolution mechanism from a filesystem walk to a `git` subprocess call
and hardened its own new failure modes, but never touched the
exemption path's mirrored fallback, which carried its old "no answer →
trust the raw path" shape forward into a mechanism (git subprocess)
that now has failure modes the filesystem walk never had.

## Standing invariants

**1. Role axis must not come back.**
derived: `git grep -wIn "role" -- . ':!docs/'` (this branch, working tree with fix applied) — result: `1103`
derived: `git grep -wIn "role" origin/main -- . ':!docs/'` — result: `1103`
Identical count before/after — this change adds zero "role" occurrences. (`git merge-base HEAD origin/main` == `HEAD` == `1d6e746c`, i.e. this branch has zero commits ahead of origin/main other than this uncommitted working-tree change, so "origin/main" and "this branch pre-fix" are the same code.)

**2. No new bug — failing-test set as names, not counts.**
acceptance: `python3 -m pytest test/ -q` (this branch, working tree with fix applied) — result: `15 failed, 414 passed, 3 xfailed in 3.37s`
acceptance: `python3 -m pytest test/ -q` run inside `git worktree add /tmp/otr-main-check origin/main` — result: `15 failed, 414 passed, 3 xfailed in 2.90s`
derived: `diff <(grep '^FAILED' /tmp/after_full.log | sort) <(grep '^FAILED' /tmp/main_full.log | sort)` — result: empty diff, i.e. byte-identical set of 15 failing test IDs on both sides (`test_convention_equivalence.py::...`, `test_spawn_cross_family_skill_selection.py::...`, `test_spawn_skill_judge_haiku_timeout_overlap.py::...`, `test_spawn_artifact_skill_pairing.py::...`, `test_local_dependency_env.py::...` — all pre-existing, unrelated to `deliverable-guard.sh`). Same pass count too (414 vs 414) since this fix added no new test file.

**3. No overhead increase — this hook runs on every write.**
The only code path with an added `git` subprocess call is the one that
was previously insecure (git could not answer at all). The common
healthy-git path is unchanged: `healthy git` row above, exempt-suffix
payload, `0.05s` before vs. `0.04s` after; deny-shaped payload,
`0.04s` before vs. `0.04s` after — within run-to-run noise, no material
increase. `python3 -m pytest test/test_deliverable_guard_priorities_shard.py test/test_deliverable_guard_worktree_submodule.py -q` (both real-subprocess hook tests, all healthy-git) — result: `24 passed, 1 xfailed in 1.05s`, unchanged shape from before this fix (same test files, untouched).

**4. Monitor/watch machinery unaffected.**
checked: `python3 -m pytest test/ -q` output above — `test/test_watchdog_heartbeat_noise.py` is included in the 414-passed set, not in either run's 15-name failing set. checked: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q` — result: `30 passed in 2.43s`. checked: `grep -l "deliverable-guard\|deliverable_guard" on-the-record/monitors/*.py` — result: no match, confirming the monitors code has no coupling to this hook to begin with. `git diff origin/main --stat -- .` (above, under "What was done") shows only `on-the-record/hooks/deliverable-guard.sh` changed — nothing under `on-the-record/monitors/` or `gates/` was touched.

## Skill application

- skill-verdict: secure-coding-authorization-access-control — applied: invoked; loaded the skill's rules after independently designing the fix, then confirmed the design against rule 1 (deny by default when git cannot confidently answer, rather than the old permit-by-omission fallback) and rule 7 (the exemption path now falls through to and reuses the activation check's own git call and denial reasoning instead of special-casing itself as a separately-trusted entry path) — both cited above under "Why".
- skill-verdict: adversarial-review — not-applicable: this record is a direct build/fix of an issue with concrete, executable acceptance criteria (run six conditions, report results), not a review of another agent's artifact by a structurally independent evaluator; no second session or blind evaluator was warranted or spawned for this delivery.

## Open findings

None outstanding. `PRODUCT_CAPTURE_ISSUE_RE` remains intentionally
unanchored/unresolved (pre-existing, out of scope per the code comment
at `on-the-record/hooks/deliverable-guard.sh:213-220` — issue #2661) —
untouched by this fix since it never calls `_git_root_from` and was
never part of the git-can't-answer failure mode this issue addresses.

## What did not work

None — no reverted approach, no scope-exceeded stop. The design
(distinguish "git said no" from "git couldn't answer", gate the
raw-path fallback on that distinction, let the unknown case fall
through to the existing hardened activation check) worked on the first
implementation and needed no rework after the six-condition probe.

## Next steps

None — `loop_state: landed`. Self-contained hardening fix with no
follow-on work implied; the one adjacent open item
(`PRODUCT_CAPTURE_ISSUE_RE`'s unanchored match) is explicitly out of
scope per issue #2661 and unaffected by this change.
