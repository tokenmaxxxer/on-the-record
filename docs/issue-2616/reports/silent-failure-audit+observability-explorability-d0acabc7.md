---
issue: 2616
role: silent-failure-audit+observability-explorability-d0acabc7
author: silent-failure-audit+observability-explorability-d0acabc7
skills: silent-failure-audit (skill-repository(297e350)), observability-explorability (skill-repository(297e350))
code_under_review:
  - pipeline.py
  - skills.py
  - spawn.py
  - test/test_managed_clone_staleness_report.py
type: fix
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: spawn.py (checkout_staleness())
    sha: c87423c171c94aeef425bbf01876355e0ec6667d
  - path: pipeline.py
    sha: same-commit
  - path: skills.py
    sha: same-commit
---

# issue-2616 — silent-failure-audit+observability-explorability-d0acabc7 record

## What was done

Added `pipeline._report_managed_clone_staleness(d, label)`, which calls
`spawn.checkout_staleness(root=d, fetch=True)` (issue #2506's detector,
reused verbatim — no second detector written) and prints one line to
stderr naming the clone path and the exact fix command whenever the result
is anything other than `checked: True, stale: False`. Wired it into both
managed-clone resolvers that share the identical TTL-pull code path:

- `pipeline.core_root()` — the `runs/rulebooks/tokenmaxxxer-core` clone
  this issue is about, in the branch that reuses an already-valid existing
  clone (right after the existing TTL-gated `git pull --ff-only`, before
  returning `d`).
- `skills._skill_repo_managed_root()` — the `runs/rulebooks/skill-repository`
  managed clone. Checked whether it shares core's code path (the issue's
  non-goal carve-out): it does, verbatim — both call the same
  `_pull_is_fresh()` / `_run_net()` / `_mark_pulled()` / `_locked_rulebook_dir()`
  helpers with the same TTL semantics, so the same defect (TTL window says
  "recently pulled," origin has since moved, nothing re-checks) applies to
  it too. Wired the same report in rather than leaving a twin gap for a
  future issue to rediscover.

canonical: `git show --stat 434ac942` — result: `pipeline.py | 36 ++++++++++++++++++++++++++++++++++++`,
`skills.py | 5 +++++`, `spawn.py | 1 +`,
`test/test_managed_clone_staleness_report.py | 174 +++++++++++++++++++++++++++`,
`4 files changed, 216 insertions(+)`.

Two report shapes, both naming the clone path and a runnable command
(never just the condition):
- stale: `[<label>] <path> 이(가) origin 대비 N개 커밋 뒤처졌다 — 고치려면:
  git -C <path> pull --ff-only`
- undetermined (`checked: False` — e.g. not a git clone, no origin/HEAD,
  a git error): `[<label>] <path> 의 origin 대비 최신 여부를 판정할 수
  없다 (<detail>) — 확인하려면: git -C <path> fetch origin && git -C
  <path> status -sb`

Current clone (`checked: True, stale: False`) prints nothing — same empty
state as today, per acceptance.

Tests added in `test/test_managed_clone_staleness_report.py`:
`ReportFormattingTest` (mocked `checkout_staleness` results — current/
stale/undetermined formatting), `ReportAgainstRealCloneTest` (executable-
live: a real bare-repo fixture put one commit behind reproduces the
acceptance's first two checks directly — a deliberately-stale real clone
produces the reported line, and a plain non-git directory reports
undetermined, never current), and `WiringTest` (`core_root()` and
`_skill_repo_managed_root()` both reach the report on their existing-valid-
clone path, with the right directory and label).

acceptance: `python3 -m pytest test/test_managed_clone_staleness_report.py test/test_checkout_staleness.py -q` — result:
```
15 passed in 1.02s
```

Full regression check, derived: `python3 -m pytest test/ -q` — result: 15
failed, 316 passed. All 15 failures are in `test_convention_equivalence.py`,
`test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`, and
`test_spawn_skill_judge_haiku_timeout_overlap.py` — the same five files
and same count as docs/issue-2603's record documents as pre-existing
(fixture requires a real `origin` remote this sandbox doesn't have).
Confirmed unrelated to this change, derived: `git stash && python3 -m
pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo
-q ; git stash pop` — result: same `SystemExit: 브랜치 체크아웃: fetch
실패` failure on the tree with this issue's commit stashed out.

## Why

**Design decision (acceptance's third bullet): the clone stays on its
existing auto-update path (TTL-gated `git pull --ff-only` in `core_root()`
/ `_skill_repo_managed_root()`), unchanged. This session does not add a
second, staleness-triggered auto-update.** Reasoning: that pull mechanism
already exists, is already the deliberate auto-update choice made when the
TTL/pull design landed, and is exercised on every spawn — changing its
trigger (e.g. from time-based TTL to `checkout_staleness()`-driven) would
touch a hot path for a change this issue's acceptance does not ask for.
derived: `grep -rl "core_root(\|_skill_repo_managed_root" test/` (run
against `HEAD~1`, i.e. before this session's own commit) — result: no
match; neither function had any direct test coverage before this session
added `test/test_managed_clone_staleness_report.py`'s `WiringTest`. The
acceptance asks for visibility, not a second mutation policy — so the fix
is additive and read-only: `checkout_staleness(fetch=True)` always fetches
and compares, independent of the TTL marker, and never resets/checks
out/merges (the same restraint #2506 established for the orchestrator-
checkout case, explicitly carried over here per the issue's must-not).

Consequence of "not auto-updated by this report": a session that spawns
inside the TTL window after a core merge still bootstraps against the old
code (unchanged from today) — but it no longer does so silently. It now
gets a stderr line naming the exact path and the exact command
(`git -C runs/rulebooks/tokenmaxxxer-core pull --ff-only`) an operator or
the session itself can run immediately to fix it, satisfying the
acceptance's "actionable from the line alone" requirement. A session
already mid-run when a merge lands is unaffected either way — the plugin
mount happens once at bootstrap, before this check or any check could act
on it; retroactively patching a running session's already-mounted hooks is
outside what a bootstrap-time check can do.

Reused `spawn.checkout_staleness()` rather than writing a second detector.
Two staleness definitions that can disagree is exactly the class of defect
issue #2603 fixed today for a different pair of functions (roster-load
classifiers) — the same reasoning applies here: one detector, called from
two more places.

Placed the call inside `core_root()`/`_skill_repo_managed_root()`'s
existing-valid-clone branch (not the freshly-cloned branch) — a clone that
was just created this call is trivially not stale, so checking it there
would just be a wasted extra `git fetch`.

## Upstream basis

`spawn.checkout_staleness(root, fetch=True)` (landed by issue #2506, PR
#2612, commit `c87423c171c94aeef425bbf01876355e0ec6667d`) is the sole
staleness detector reused here — returns `{checked, stale, behind,
fetch_ok, detail}`, `checked: False` on any git error rather than a
confident `stale: False`. Not modified by this change.

## Open findings

**Silent-failure-audit finding (not fixed in this change — out of this
issue's acceptance, named with its remedy per the mandate not to name a
state without a fix):** in both `core_root()` and
`_skill_repo_managed_root()`, the TTL-gated `git pull --ff-only`'s result
(`_sp._run_net([...], "[core] pull")` / `"[skill-repo] pull"`) is a
`CompletedProcess` that is never inspected — the call's return value is
discarded, and `_sp._mark_pulled(d)` runs unconditionally immediately
after, regardless of the pull's `returncode`.

```
pipeline.py:
    if not _sp._pull_is_fresh(d):
        _sp._run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"], "[core] pull")
        _sp._mark_pulled(d)
```

Silently-absorbed pattern: result ignored, caller assumes success. Forward
trace: pull fails for any non-timeout reason (e.g. local drift makes
`--ff-only` impossible, a transient non-hanging network error) →
`_mark_pulled(d)` stamps the TTL marker anyway → `_pull_is_fresh(d)` reads
that marker as true for the next `MUSTER_RULEBOOK_TTL` minutes (default
15) → every spawn in that window skips pulling entirely, believing a pull
was just attempted → the clone sits on old code longer than the TTL alone
would explain. This session's new report line still surfaces the
resulting staleness correctly (it independently fetches+compares, it does
not trust the marker), so the defect described in issue #2616 is fixed
regardless of this one — but the marker-on-failure bug is a separable,
pre-existing correctness gap in the pull path itself. Suggested remedy for
a follow-up issue: only call `_mark_pulled(d)` when the pull's
`returncode == 0`.

## Next steps

None.

## What did not work

None.

skill-verdict: silent-failure-audit — applied: invoked; audited
`core_root()`/`_skill_repo_managed_root()`'s pull-result handling and the
new report function's own error paths, produced the Open Findings entry
above (unconditional `_mark_pulled()` after a discarded pull result).
skill-verdict: observability-explorability — not-applicable: this issue is
a single bootstrap-time report line, not a dashboard or ad-hoc incident-
query surface the skill's dashboard-design/explorability scope covers.
