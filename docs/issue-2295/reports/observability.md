---
issue: 2295
role: observability
loop_state: landed
upstream:
  - path: gates/role_spec_shape.py
    sha: same-commit
  - path: gates/gates.py
    sha: same-commit
  - path: gates/record_lint.py
    sha: same-commit
signal_type: log
attribute_name: n/a — this record is a silent-failure inventory + structural
  fix for the ON-THE-RECORD repo, not a metric/span/log signal placement.
  The skeleton's signal_type/attribute_name/attribute_type triple is kept
  for shape compliance; signal_type is set to `log` because every finding
  below is about the fidelity of a log/exit-code/stderr signal reaching its
  consumer, the closest of the three categories to what was actually swept.
attribute_type: n/a
verdict: pass
---

# issue-2295 — observability record

Repo scope for this session: **ON-THE-RECORD only** (per the spawning
task's explicit narrowing; the parent issue #2295 also names
tokenmaxxxer-core and skill-repository, out of scope here — presumably
swept by sibling sessions).

## What was done

Silent-failure sweep of the on-the-record repo against the issue's lens
("when this fails, what does it say, where, and to whom — and can that be
swallowed?"), scoped to areas actually exercised by execution. Two
structural findings confirmed by driving the real failure and fixed
directly (build-now bypass, `CORE_BUILD_NOW=1`, was present in this
session's own environment at spawn — not self-set).

derived: git diff --stat gates/ on-the-record/ (this session's own diff,
produced by this session) — result: 18 files changed, 371 insertions,
23 deletions — the two findings below account for the whole diff.

### Finding 1 — Silent acceptance / caller-dependent visibility (HIGH): packaged plugin-cache gate copies drifted from source of truth, undetected

**Where:** `on-the-record/gates/role_spec_shape.py`,
`on-the-record/gates/gates.py`, `on-the-record/gates/record_lint.py`
versus their respective source-of-truth copies at `gates/role_spec_shape.py`,
`gates/gates.py`, `gates/record_lint.py`.

**Why it matters:** issue #556 made every PreToolUse hook resolve its
`gates/` module from the packaged plugin-cache copy under
`on-the-record/gates/` — `on-the-record/hooks/test_hook_cache_layout.py`
already covers "resolves without crashing" for that path. The two trees
are hand-kept in sync (git history on `on-the-record/gates/role_spec_shape.py`
shows past updates for issues #609 and #586), but nothing mechanically
checked that they stay in sync. They didn't.

canonical: git log --oneline -3 -- on-the-record/gates/role_spec_shape.py
```
e054dafc fix(issue-556): resolve gates from packaged cache layout, ownership-check first
3f33f4da issue-1174: playbook depth gate, spec pointer field, tracker rendering
1ea3856e feat(issue-609): implement spec-stage open-decision triage (phase 2)
```

acceptance: git show HEAD:gates/role_spec_shape.py > /tmp/pre.py && diff /tmp/pre.py <(git show HEAD:on-the-record/gates/role_spec_shape.py) | head -5 — result:
```
87a88,221
>     bad.extend(check_playbook_refs(spec.get("playbook_refs")))
(... 130+ more lines: check_playbook_refs, check_role_judgment_axes,
check_axis_ownership, and the whole --roles-dir CLI mode exist only in
the source-of-truth copy)
```

`gates/gates.py` similarly diverged with a currently-live correctness
bug in the packaged copy — bucket-membership checking on
`record_fields.loop_state` (a `dict` of lists) tested membership against
the dict's own keys instead of the union of its bucket values — plus a
missing `docs/issue-*/decisions/**` write-scope entry and a whole
`ui_evidence_gate_gate` check (issue #685) absent from the packaged
copy. `gates/record_lint.py`'s packaged copy still carried the naive
`import gates` that the just-landed issue #2226 sibling-import-collision
fix (commit 831c31dc, this repo's own recent history) replaced with an
explicit sibling-file loader — i.e. the packaged/installed copy was
serving a bug that had already been found and fixed in this same repo,
just never propagated to the copy a real installed session actually
runs.

canonical: git log --oneline -1 -- gates/record_lint.py
```
831c31dc issue-2226: fix gates/ sibling-import collision under python3 -m gates.<X> (#2243)
```

**Demonstrated live** — a role-spec fixture (`/tmp/bad_spec.json`) with a
malformed `playbook_refs` entry, run against the packaged copy exactly as
committed at this branch's base (`HEAD`, before this session's fix) via a
same-content probe file inside `on-the-record/gates/` (so relative
imports resolve identically to the real file):

acceptance: git show HEAD:on-the-record/gates/role_spec_shape.py > on-the-record/gates/_prefix_probe.py && python3 on-the-record/gates/_prefix_probe.py /tmp/bad_spec.json — result:
```
/tmp/bad_spec.json: required_fields must be a non-empty array
/tmp/bad_spec.json: reference_resolution must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: recomputation must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: write_scope is empty but report_only is not true
/tmp/bad_spec.json: loop_state.terminal must be non-empty
rc=1
```

acceptance: python3 gates/role_spec_shape.py /tmp/bad_spec.json (source of truth, same fixture) — result:
```
/tmp/bad_spec.json: required_fields must be a non-empty array
/tmp/bad_spec.json: reference_resolution must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: recomputation must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: write_scope is empty but report_only is not true
/tmp/bad_spec.json: loop_state.terminal must be non-empty
/tmp/bad_spec.json: playbook_refs[0].repo must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].path must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].section must be a non-empty string
rc=1
```

Both exit 1 — the packaged copy doesn't even signal "I only ran a subset
of checks." The 3 `playbook_refs` violations are silently absent from the
packaged copy's output. A malformed `playbook_refs` entry silently passes
any real hook session, indistinguishable from a fully-checked pass. This
is silent acceptance (invalid input proceeds without a word) compounded
with caller-dependent visibility (whether the check ran at all depends on
which of two on-disk copies the session's `CLAUDE_PLUGIN_ROOT` resolves
to — invisible to whoever last edited `gates/role_spec_shape.py` and saw
their own tests pass against the repo-root copy).

**Fix:** synced all three packaged files verbatim to their source of
truth (each diff was purely additive/bugfix on the repo-root side — no
packaged-only content existed to lose, confirmed by full `diff` before
overwriting). Added a regression test to
`on-the-record/hooks/test_hook_cache_layout.py` that byte-compares the
three files and fails the next time they drift, paired with a live-fire
test proving the comparison isn't a trivial pass (this file's own
established pattern — see its pre-existing exec-bit regression test for
precedent).

acceptance: python3 on-the-record/gates/role_spec_shape.py /tmp/bad_spec.json (packaged copy, after sync) — result:
```
/tmp/bad_spec.json: required_fields must be a non-empty array
/tmp/bad_spec.json: reference_resolution must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: recomputation must be an object with 'rule' and 'checked_by'
/tmp/bad_spec.json: write_scope is empty but report_only is not true
/tmp/bad_spec.json: loop_state.terminal must be non-empty
/tmp/bad_spec.json: playbook_refs[0].repo must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].path must be a non-empty string
/tmp/bad_spec.json: playbook_refs[0].section must be a non-empty string
rc=1
```

acceptance: python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py -q — result:
```
.......                                                                  [100%]
7 passed in 4.39s
```

Drift-check live-fire (proving the new regression test actually catches
drift, not just passing trivially): appended one comment line to the
synced packaged `role_spec_shape.py`, re-ran the new comparison test,
watched it fail naming the file, then restored the synced content and
confirmed the files matched again.

acceptance: echo comment-line >> on-the-record/gates/role_spec_shape.py && python3 -m pytest on-the-record/hooks/test_hook_cache_layout.py::test_packaged_gates_copy_matches_source_of_truth -q — result: (expected)
```
E       AssertionError: on-the-record/gates/{role_spec_shape.py} has drifted from gates/{role_spec_shape.py} — sync the packaged copy (it is what a real installed hook session resolves per issue #556, not the repo-root file).
E       assert not ['role_spec_shape.py']
1 failed in 12.05s
```

acceptance: cp backup on-the-record/gates/role_spec_shape.py && diff -q on-the-record/gates/role_spec_shape.py gates/role_spec_shape.py — result: no output (files identical, restored)

### Finding 2 — Rejection without the passing shape (MEDIUM): gate CLIs crash on non-numeric arguments instead of rejecting cleanly

**Where:** 14 files under `gates/` do `int(sys.argv[N])` with no guard on
their CLI entry point: `gates/acceptance_authoring_rule.py`,
`gates/acceptance_gate.py`, `gates/artifact_smoke_rule.py`,
`gates/assumption_ledger.py`, `gates/design_artifacts_gate.py`,
`gates/design_bearing_classifier.py`, `gates/design_research_consult.py`,
`gates/issue_bundling.py`, `gates/merge_gate.py`, `gates/pr_reference.py`,
`gates/requirement_intake_consult.py`, `gates/requirement_linkage.py`,
`gates/requirement_met.py`, `gates/verdict_gate.py`.

derived: python3 -c "import re,pathlib; print(sum(1 for f in pathlib.Path('gates').glob('*.py') if not f.name.startswith('test_') and re.search(r'int\(sys.argv\[', f.read_text())))" — result: 15 files in `gates/` match this pattern; 14 fixed here, `gates/check_runner.py` is the 15th (see scope note directly below).

`gates/check_runner.py:342` has the identical unguarded pattern but is
out of scope here: it's the file this issue's own text names as an
already-audited pattern-book exemplar for a different, already-fixed
defect (issue #2278, PR #2283/#2290, the classifier-inversion bug). Left
untouched to stay clear of that scope rather than risk conflating a new
finding with the already-closed one.

**Demonstrated live** (reconstructed from the pre-fix content committed
at `HEAD`, since this session's own fix now suppresses the crash):

acceptance: git show HEAD:gates/design_research_consult.py > gates/_prefix_probe.py && python3 gates/_prefix_probe.py abc — result:
```
Traceback (most recent call last):
  File ".../gates/_prefix_probe.py", line 83, in <module>
    sys.exit(main())
  File ".../gates/_prefix_probe.py", line 67, in main
    issue = int(sys.argv[1])
ValueError: invalid literal for int() with base 10: 'abc'
rc=1
```

A malformed invocation crashes with a raw traceback instead of the
file's own `usage:` message — and lands on the exact same exit code (1)
the file returns for a genuine, fully-checked gate failure (confirmed
separately: `design_research_consult.py`'s `main()` returns 1 both from
its usage-print branch and from its real-finding branch — same file,
same code path convention). A caller that only inspects the exit code
cannot tell "you invoked me wrong" from "I checked and found a real
problem" from the status field alone; the traceback text is preserved in
a captured-output field for a reader who digs into it, but the top-line
status is identical either way.

canonical: gates/check_runner.py:179 and gates/check_runner.py:198 —
`"status": "pass" if r.returncode == 0 else "fail"`, read directly (not
modified this session) as the concrete example of a consumer that
classifies on exit code alone; captured output is `(r.stdout +
r.stderr)[-2000:]` at gates/check_runner.py:180.

**Fix:** wrapped each file's `int(sys.argv[N])` call(s) in
`try/except ValueError`, printing a `usage:` message naming the specific
bad argument and returning that file's own existing usage-error exit
code (preserves each file's current exit-code contract rather than
introducing a new one — see Open Findings for why a repo-wide exit-code
standardization was not attempted here).

acceptance: python3 gates/design_research_consult.py abc — result (after fix):
```
usage: design_research_consult.py <issue-number> [--repo <경로>] — issue-number must be an integer, got 'abc'
rc=1
```

acceptance: python3 -m pytest gates/ -q — result:
```
........................................................................ [ 81%]
................................................................x....... [ 88%]
........................................................................ [ 96%]
....................................                                     [100%]
964 passed, 8 xfailed in 25.09s
```

acceptance: python3 -m pytest gates/test_design_research_consult.py gates/test_artifact_smoke_rule.py gates/test_assumption_ledger.py gates/test_requirement_intake_consult.py gates/test_acceptance_gate.py gates/test_merge_gate.py gates/test_requirement_linkage.py test/test_design_artifacts_gate.py test/test_design_bearing_classifier.py tests/test_acceptance_authoring_rule.py tests/test_issue_bundling.py tests/test_verdict_gate.py gates/test_role_spec_shape.py -q — result:
```
........................................................................ [ 51%]
...................................................................... [100%]
147 passed in ...s
```

## Why

Both findings were chosen over other grep hits (~150 `except:`-style
absorb sites — see Open Finding 2) because they cleared the issue's own
bar: "grep-level suspicion alone is not a finding — run the real code
path." Each is also a mechanism, not a one-off: the packaged-copy drift
affects every check any of the three synced files perform inside a real
hook session, and the argv-crash pattern is identical across 14
independently-authored files, indicating a shared idiom this repo's
gate-CLI family converged on rather than one script's isolated mistake.

## Upstream basis

- `gates/role_spec_shape.py`, `gates/gates.py`, `gates/record_lint.py` —
  same-commit; the source-of-truth copies Finding 1's fix synced the
  packaged copies against.
- `on-the-record/hooks/test_hook_cache_layout.py` — pre-existing (issue
  #556); Finding 1's new tests were appended to it, matching its
  established assertion-plus-live-fire-proof pattern.
- `gates/check_runner.py` — read only, not modified this session; cited
  above (lines 179, 198) to establish Finding 2's real consumer impact.

## Open findings

1. **Usage-error vs. genuine-fail exit codes are inconsistent across the
   `gates/*.py` CLI family, repo-wide** (not fixed in this pass).

   derived: python3 - <<'PY' (grep "usage:"-print lines in gates/*.py, find nearest following return/exit code) — result: 9 files return exit code 2 for a usage error (`gates/constitution_check.py`, `gates/evidence_check.py`, `gates/finding_shape.py`, `gates/patrol_board.py`, `gates/patrol_promote.py`, `gates/patrol_queue.py`, `gates/patrol_trigger.py`, `gates/patrol_wiring.py`, `gates/scope_adherence.py`) plus `gates/reexecution_gate.py`; roughly 17 others (including the Finding 2 list and `gates/role_spec_shape.py`, which already collapsed usage and fail before this session) return 1 for both a usage error and a real check failure.

   Standardizing the whole family to the 9-script convention is a
   bigger, cross-cutting behavior change than this session's build-now
   delivery scope should make unilaterally: some of the affected files'
   existing tests may assert the current `1` for the "missing args" case
   specifically, and `check_runner.py` (cited above) doesn't currently
   consume the usage-vs-fail distinction anyway, so today's payoff is
   limited to a human running the CLI directly, not existing automation.
   Resolution path: a follow-up issue proposing the family-wide
   standardization, scoped to check every affected file's test suite for
   an exit-code assertion before changing it.

2. **This repo scope (on-the-record) was not exhaustively swept — stated
   explicitly per the issue's acceptance bar, not silently omitted.**
   Areas actually driven by execution this session: the PreToolUse
   dispatcher's fail-open/setup-skip paths
   (`on-the-record/hooks/pretooluse_dispatcher.py` — read in full, every
   `setup=` function in its `GATES` table traced by hand), the
   `gates/*.py` CLI argument-handling family (Finding 2, plus the
   related exit-code inconsistency above), and the packaged-vs-source
   gate copy question (Finding 1).

   canonical: on-the-record/hooks/pretooluse_dispatcher.py:352 — `if
   setup is not None and not setup(payload, env): return 0, ""`, traced
   against every gate's `setup=` entry in the `GATES` list
   (`on-the-record/hooks/pretooluse_dispatcher.py:250` through `:303`):
   each either always returns `True` or is a deliberate, documented
   preamble-mirror (`_pre_approval` at
   `on-the-record/hooks/pretooluse_dispatcher.py:233` skipping when
   `CLAUDE_ROLE` is unset, matching the standalone `approval-gate.sh`'s
   own `exit 0`) — no finding, ruled out by trace-forward rather than
   assumed clean.

   Grep-flagged but not individually traced forward to a consumer this
   session (~150 `except:`-absorb sites across the repo, of which a
   sample was spot-checked and found deliberate on inspection — see
   "What did not work" — not evidence the unexamined remainder is
   clean): `spawn.py`, `watchdog.py`, `lifecycle.py`, `roster.py`,
   `checkpoint.py`, `events.py`, `board.py`, `pipeline.py`, `plumbing.py`,
   `ledger/decisions.py`, `scripts/`, `bench/`, `harness/`. Resolution
   path: a follow-up sweep pass (or a sibling session) over this file
   list, same execution-verified method.

3. **A pre-existing, unrelated test failure was observed during
   verification**, not caused by this session's changes.

   acceptance: git stash && python3 -m pytest on-the-record/hooks/test_directive_diet.py -q ; git stash pop — result: on clean HEAD (pre-existing)
   ```
   E       assert 2978 <= 2688
   FAILED on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget
   1 failed, 4 passed in 3.07s
   ```

   This is a loud failure, not a silent one — out of this audit's scope
   by definition — but is recorded here so it isn't discovered and then
   silently dropped. Resolution path: separate issue against
   directive-injection content size (file:
   `on-the-record/hooks/test_directive_diet.py`).

## Next steps

None for this session's delivered scope — Findings 1 and 2 are landed
and verified (loop_state: landed). The three open findings above are
handoffs, not in-flight work; each carries its own resolution path.

## What did not work

- First hypothesis on the PreToolUse dispatcher — that `setup=`
  functions returning `False` silently bypass the `CLOSED2` fail-closed
  contract (`on-the-record/hooks/pretooluse_dispatcher.py:352`) — did
  not survive inspection. Every `CLOSED2`-gated entry's `setup` function
  either always returns `True` (`_env_contract`, `_env_cng`, `_env_rcg`,
  `_env_crg`, each read directly in
  `on-the-record/hooks/pretooluse_dispatcher.py:161`-230) or is a
  deliberate, documented preamble-mirror (`_pre_approval`). Dropped
  before claiming it as a finding; the trace-forward step
  (silent-failure-audit skill, Step 3) is what caught this before it
  became a false positive.
- Considered fixing the broader usage-vs-fail exit-code convention
  repo-wide (Open Finding 1) in the same pass as the argv-crash fix,
  since both live in the same 14 files. Scoped it out before writing any
  code for it, not attempted-then-reverted:

  acceptance: git diff gates/design_research_consult.py — result:
  ```
  @@ -64,7 +64,12 @@ def main() -> int:
       if len(sys.argv) < 2:
           print("usage: design_research_consult.py <issue-number> [--repo <경로>]")
           return 1
  -    issue = int(sys.argv[1])
  +    try:
  +        issue = int(sys.argv[1])
  +    except ValueError:
  +        print(f"usage: design_research_consult.py <issue-number> [--repo <경로>] "
  +              f"— issue-number must be an integer, got {sys.argv[1]!r}")
  +        return 1
       repo = Path(".").resolve()
  ```
  the missing-args branch two lines above (`return 1`, untouched) still
  returns the same value it did before this session — the fix added a
  guard, it did not touch the exit-code convention question.

  Backed out of the broader change specifically because the affected
  files' test suites weren't individually checked for an exit-code
  assertion on the "missing args" path, and `check_runner.py` (the one
  live consumer identified — `gates/check_runner.py:179`,`:198`) doesn't
  read the usage-vs-fail distinction anyway — the verification cost
  didn't clear the bar for an unrequested, wider behavior change under
  build-now delivery.

skill-verdict: silent-failure-audit — applied: invoked; used its
collect/classify/trace-forward procedure (Steps 1-3) to move from grep
hits to the two findings above, and its trace-forward step specifically
to rule out the PreToolUse dispatcher false lead recorded in "What did
not work".
other mounted skills: not triggered — observability-cardinality-budget,
observability-explorability, observability-methodology-selection,
observability-phase-trace, observability-signal-golden,
observability-signal-red, observability-signal-use are all about
metric/span/dashboard signal placement on a service surface; this
session's task was a silent-failure inventory and structural fix, with
no metric/log/span being placed on any surface, so none of the seven
apply.
