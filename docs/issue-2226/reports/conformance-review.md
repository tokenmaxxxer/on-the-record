---
issue: 2226
role: conformance-review
loop_state: reported
upstream:
  - path: PR #2243 (branch issue-2226/implementation, GitHub)
    sha: 5b0b343c5d2556a54ad19f95dab2bb564508b879
subject: PR #2243 ("issue-2226: fix gates/ sibling-import collision under python3 -m gates.<X>") graded against issue #2226's frozen `## Acceptance` section — CHANGES-round re-review after the three previously-missed sites were fixed
test: independent re-execution of gates/test_record_lint.py and both invocation forms from a disposable git worktree at the PR's new head commit; independent re-derivation of the PR's own gates/-wide audit grep with a shape-complete pattern (indent/alias/trailing-comment); live functional execution (not just import) of the three newly-fixed entry points; a git-diff check that the shared-BASE-mutation hunter finding is pre-existing, not a regression
result: passed
assertedBy: builder-blind conformance-review session (branch issue-2226/conformance-review) — no access to PR #2243's builder session (issue-2226/implementation) or its rationale beyond what the PR body, diff, and implementation record state; verdicts below rest on the issue body, the PR diff, and code/tests read from the PR's own new head commit
---

# issue-2226 — conformance-review record

## What was done

Builder-blind grading of PR #2243 against issue #2226's frozen `## Acceptance`
section plus its Ask-section audit instruction.
canonical: gh issue view 2226
canonical: gh pr view 2243 --json title,body,files,commits

Issue #2226's Acceptance section is one `gate:` line, one `empty state:`
line (bundling two obligations — run to completion, and report nothing —
split per conformance-review-requirement-extraction rule 1), and one
`provenance:` line, plus an Ask-section instruction to audit the rest of
`gates/` for the same shape. Six checkable items total (A1 through A6
below). Full enumeration was feasible without sampling: the PR touches
four non-test files plus the gate script itself.

Five of six requirements verified Present. The sixth (A6, the Ask
section's audit instruction) verified Incorrect: three files in `gates/`
still carry the exact hazard the issue describes, and this session
independently reproduced the resulting failure in each — full detail in
the A6 finding block below, canonical citations inline there.

## Why

Verification method chosen per-requirement
(conformance-review-verification-method-selection): Test for A1/A2a/A2b/A3
(existing/re-run executable evidence, reused per rule 4 where an
executable test already existed, freshly executed where it didn't),
Inspection for A4 (a static presence check on the record artifact), and
Test for A6 (upgraded from a static grep-comparison to live reproduction).
Verdict-assignment rule 6 (re-check a plausible-false-positive
Absent/Incorrect once before finalizing) was applied to A6: each of the
three additional instances was independently reproduced or its
silent-swallow behavior demonstrated, not asserted from a code read
alone — see A6 below.

## Upstream basis

- Issue #2226 (GitHub) — canonical: gh issue view 2226 — the frozen
  `## Acceptance` section graded below, plus the Ask section's audit
  instruction.
- PR #2243 (branch `issue-2226/implementation`, GitHub) — canonical:
  gh pr view 2243 --json title,body,files,commits; head commit
  `26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a`. Not yet merged to `main`;
  its files were read via `git fetch origin pull/2243/head:pr-2243-review`
  (read-only ref, never checked out over this session's own tree) and
  `git show 26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a:<path>`, plus a
  disposable `git worktree add /tmp/pr2243-repro pr-2243-review` (removed
  after use) for executing the PR's code.

## Findings

---
requirement: "gate: `gates/test_record_lint.py`" — the named gate test file.
canonical: python3 -m pytest gates/test_record_lint.py -q (worktree at pr-2243-review head 26c128ce, this session — output below)
spec_ref: issue-2226 Acceptance, `gate:` line
dimension: functional behavior
verdict: Present
method: Test — re-executed this session from the disposable worktree at
  the PR's head commit, not reused from the PR's own pasted output
evidence: 26c128ce:gates/test_record_lint.py (full file, 1024 lines)
```
$ cd /tmp/pr2243-repro && python3 -m pytest gates/test_record_lint.py -q
....................................................................     [100%]
68 passed in 1.38s
```
canonical: python3 -m pytest gates/test_record_lint.py -q (worktree at pr-2243-review head 26c128ce, this session — output above)
derived: 68 passed, 0 failed, 0 skipped — read directly from the pytest summary line in the fenced output immediately above
canonical: python3 -m pytest gates/test_record_lint.py -q (same run, output above)
rationale: fresh execution from the PR's own head commit, independent of
  the record's own pasted output, reproduces the same hold.
---
requirement: "empty state: a repo with no `docs/issue-*/reports/*.md`
  records at all — the linter must run to completion" (first of two
  obligations bundled in the Acceptance line, split per
  requirement-extraction rule 1)
canonical: python3 -m gates.record_lint && python3 gates/record_lint.py (fresh git-init repo at /tmp/empty-repo with zero docs/issue-* tree, this session — output below)
spec_ref: issue-2226 Acceptance, `empty state:` line
dimension: edge-case
verdict: Present
method: Test — freshly constructed empty-state fixture, not reused from
  the PR's own pasted transcript
evidence: 26c128ce:gates/record_lint.py (whole-repo scan path, `main()`)
```
$ rm -rf /tmp/empty-repo && mkdir -p /tmp/empty-repo && cd /tmp/empty-repo \
  && git init -q && git commit -q --allow-empty -m init \
  && cp -r /tmp/pr2243-repro/gates ./gates
$ python3 -m gates.record_lint; echo exit:$?
record_lint: no records found under /tmp/empty-repo — 검사할 레코드가 없다.
exit:0
$ python3 gates/record_lint.py; echo exit:$?
record_lint: no records found under /tmp/empty-repo — 검사할 레코드가 없다.
exit:0
```
canonical: python3 -m gates.record_lint && python3 gates/record_lint.py (fresh empty repo at /tmp/empty-repo, this session — output above)
rationale: both invocation forms completed and returned exit 0 — no unhandled exception on either form, so the crash the issue reports does not occur here.
canonical: python3 -m gates.record_lint && python3 gates/record_lint.py (same empty-repo run, exit:0 both, output above)
---
requirement: "... the linter must run to completion and report nothing,
  under whichever invocation forms are supported after the fix." (second
  of the two bundled obligations: reports nothing)
canonical: python3 -m gates.record_lint && python3 gates/record_lint.py (same fresh empty repo as the item immediately above, this session — output below)
spec_ref: issue-2226 Acceptance, `empty state:` line
dimension: edge-case
verdict: Present
method: Test — same fixture and run as the item immediately above
evidence: same fixture as above
```
record_lint: no records found under /tmp/empty-repo — 검사할 레코드가 없다.
exit:0
```
canonical: python3 -m gates.record_lint && python3 gates/record_lint.py (same empty-repo run, output above)
rationale: both forms printed only the informational no-records notice and no violation/finding line — "report nothing" read as "report no violations," the linter's own domain vocabulary.
canonical: python3 -m gates.record_lint && python3 gates/record_lint.py (same empty-repo run, output above)
---
requirement: Both invocation forms (`python3 -m gates.record_lint`,
  `python3 gates/record_lint.py`) must behave as intended — either both
  work, or the unsupported one fails with a message naming the collision.
canonical: python3 -c "import runpy; runpy.run_module('gates.claims'/'gates.risk_report'/'gates.ci', run_name='__not_main__')" (worktree at pr-2243-review head 26c128ce, this session — output below)
spec_ref: issue-2226 Acceptance, `provenance:` line; Ask section, "Make
  both invocation forms work, or make the unsupported one fail with a
  message that names the actual problem."
dimension: functional behavior
verdict: Present
method: Test — reused the empty-state fixture above for `record_lint.py`
  itself, plus a fresh import-level check for the three sibling entry
  points the PR also touched
evidence: 26c128ce:gates/record_lint.py:28-55 (loads `gates/gates.py` via
  `importlib.util.spec_from_file_location` under a private
  `sys.modules["_on_the_record_gates_sibling_impl"]` key instead of a
  bare `import gates`); same fix shape at 26c128ce:gates/claims.py:35-50,
  26c128ce:gates/ci.py:40-58, 26c128ce:gates/risk_report.py:29-36
```
$ cd /tmp/pr2243-repro && python3 -c "
import runpy
for m in ('gates.claims', 'gates.risk_report', 'gates.ci'):
    try:
        runpy.run_module(m, run_name='__not_main__', alter_sys=False)
        print(m, 'import OK')
    except AttributeError as e:
        print(m, 'ATTRIBUTEERROR:', e)
"
gates.claims import OK
gates.risk_report import OK
gates.ci import OK
```
canonical: python3 -c "import runpy; runpy.run_module(...)" (worktree at pr-2243-review head 26c128ce, this session — output above)
rationale: scoped to the four files the PR actually touched — this clause is literally about those files' own invocation forms; the broader gates/-wide claim from the same Ask-section paragraph is a separate requirement (A6) with a different verdict.
canonical: same runpy check above, this session; A6 below for the gates/-wide claim
---
requirement: Provenance must be executed-live — the real output of both
  invocation forms, pasted after the change. "The current AttributeError
  above is the before-state."
canonical: git show 26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a:docs/issue-2226/reports/implementation.md (this session's own read, output below)
spec_ref: issue-2226 Acceptance, `provenance:` line
dimension: scope-boundary
verdict: Present
method: Inspection — a static presence check on the PR's own record
  artifact, cross-checked against this session's independent
  reproduction of the same scenario (A2a/A2b above)
evidence: 26c128ce:docs/issue-2226/reports/implementation.md:29
  (before-state AttributeError transcript), :192-225 (after-state, both
  invocation forms, empty-state and single-record-path runs)
```
$ git show 26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a:docs/issue-2226/reports/implementation.md | sed -n '202,215p'
$ python3 -m gates.record_lint "$D"
record_lint: no records found under /tmp/tmp.EAxRQMMdo4 — 검사할 레코드가 없다.
$ echo exit:$?
exit:0
$ python3 gates/record_lint.py "$D"
record_lint: no records found under /tmp/tmp.EAxRQMMdo4 — 검사할 레코드가 없다.
$ echo exit:$?
exit:0
```
canonical: git show 26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a:docs/issue-2226/reports/implementation.md (this session's own read, output above)
rationale: the pasted text matches, in message text and exit-code pattern, this session's own independent reproduction against a different empty-state fixture (A2a/A2b) — corroborated, not merely plausible-looking.
canonical: A2a/A2b empty-repo run above, this session; git show read above
---
requirement: "Audit the rest of `gates/` for the same
  `sys.path.insert` + `import <sibling>` shape while here."
canonical: grep -rn "import gates" gates/*.py (worktree at pr-2243-review head 26c128ce, this session — output below)
spec_ref: issue-2226 Ask section, final paragraph
dimension: scope-boundary
verdict: Incorrect
method: Test — the PR's own audit is a static grep result, but "no other
  instance hits this bug" is an execution claim; re-derived the grep past
  its exact-match anchor and reproduced the resulting failures
evidence: 26c128ce:docs/issue-2226/reports/implementation.md:58 (the
  audit command actually run: `grep -rln "^import gates$" gates/*.py`);
  26c128ce:gates/ui_evidence_gate.py:82 (function-local, 4-space-indented
  `import gates` inside `check_record`, reachable via
  26c128ce:gates/gates.py:1287 `ALL["ui_evidence_gate"]` ->
  26c128ce:gates/gates.py:1249-1269 `ui_evidence_gate_gate` ->
  `ui_evidence_gate.check_record`); 26c128ce:gates/roles_due.py:30-32
  (module-top-level `import gates as _gates`, the `as` alias breaks the
  exact-line match); 26c128ce:gates/skip_eligibility.py:26-28
  (module-top-level `import gates  # noqa: E402`, the trailing comment
  breaks the exact-line match)
```
$ cd /tmp/pr2243-repro && grep -rn "import gates" gates/*.py | grep -v "^gates/test_"
gates/ci.py:48:# instead of a bare `import gates`, which under `python3 -m gates.ci`
gates/record_lint.py:32:# package has no `__file__`. A bare `import gates` below would then hit
gates/claims.py:40:# instead of a bare `import gates`, which under `python3 -m gates.claims`
gates/risk_report.py:22:# instead of a bare `import gates`, which under `python3 -m gates.risk_report`
gates/risk_report.py:26:# so a bare `import gates` here only ever worked via direct-script
gates/roles_due.py:32:import gates as _gates  # changed_files(), record_frontmatter()
gates/skip_eligibility.py:28:import gates  # noqa: E402
gates/ui_evidence_gate.py:82:    import gates
```
canonical: grep -rn "import gates" gates/*.py (worktree at pr-2243-review head 26c128ce, this session — three real matches beyond the four fixed files' own explanatory comments, output above)
```
$ cd /tmp/pr2243-repro && cat > gates/_repro_probe.py <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util as _importlib_util
_GATES_IMPL_KEY = "_on_the_record_gates_sibling_impl"
if _GATES_IMPL_KEY not in sys.modules:
    _spec = _importlib_util.spec_from_file_location(
        _GATES_IMPL_KEY, str(Path(__file__).parent / "gates.py"))
    _impl = _importlib_util.module_from_spec(_spec)
    sys.modules[_GATES_IMPL_KEY] = _impl
    _spec.loader.exec_module(_impl)
gates = sys.modules[_GATES_IMPL_KEY]
try:
    bad = gates.check(["ui_evidence_gate"], Path("."), {})
    print("OK:", bad)
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)
EOF
$ python3 -m gates._repro_probe
EXCEPTION: AttributeError module 'gates' has no attribute 'record_frontmatter'
```
canonical: python3 -m gates._repro_probe (disposable probe module mirroring the four fixed files' own load pattern, worktree at pr-2243-review head 26c128ce, deleted after this run, not part of any commit, this session — output above)
```
$ cat > gates/_probe2.py <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import roles_due
try:
    r = roles_due.roles_due(Path("."))
    print("roles_due() returned:", r)
except Exception as e:
    print("roles_due() EXCEPTION:", type(e).__name__, e)
import skip_eligibility
try:
    d = skip_eligibility.classify_for_subject(Path("."), "issue-1")
    print("classify_for_subject() returned:", d)
except AttributeError as e:
    print("classify_for_subject() ATTRIBUTEERROR:", e)
EOF
$ python3 -m gates._probe2
roles_due() returned: []
classify_for_subject() ATTRIBUTEERROR: module 'gates' has no attribute 'BASE'
$ python3 -c "import sys; sys.path.insert(0,'gates'); import gates; print(hasattr(gates,'BASE'), hasattr(gates,'changed_files'))"
True True
```
canonical: python3 -m gates._probe2 (disposable probe, worktree at pr-2243-review head 26c128ce, deleted after this run, not part of any commit, this session — output above, including the control check on the last line confirming a correctly-resolved `gates` module has both attributes)
rationale: Incorrect, not Absent — the record's audit made an affirmative, falsifiable claim that this session's own re-derivation contradicts with three counterexamples, not merely an unaddressed gap.
canonical: gates._repro_probe / gates._probe2 runs above, this session
All three share one root cause with the four files the PR did fix (a bare `import <name>` where `<name>` equals the enclosing `gates/` directory's own package name) but were invisible to an exact-line-match grep for three different surface reasons.
canonical: grep -rn "import gates" gates/*.py output above, this session
`roles_due.py`'s failure mode is distinct from the other two: a bare `except Exception: return []` around the broken call silently swallows the AttributeError into an empty result rather than propagating it.
canonical: gates._probe2 run above ("roles_due() returned: []"), this session
spec_vs_built: Spec (Ask section) asked to audit gates/ for every instance of the shape and implicitly fix what's found ("while here").
canonical: 26c128ce:docs/issue-2226/reports/implementation.md:54-55 (the Ask-section-derived audit heading in the PR's own record)
Built: an exact-line-match grep, quoted in full above (`implementation.md:58`), that found and fixed 4 files matching `import gates` alone on its own line, but structurally cannot match an indented, aliased, or commented occurrence — three of which exist and are reproduced above in this same block.
canonical: grep -rn "import gates" gates/*.py plus gates._repro_probe / gates._probe2 runs above in this same finding block, this session
The audit's own stated rationale for scoping to those four files is true only because the grep that fed it had already excluded these three before the reasoning was applied to its results.
canonical: 26c128ce:docs/issue-2226/reports/implementation.md:72-76 (the audit's stated rationale), contradicted by the reproductions above in this same finding block
---

## CHANGES round — re-verification of PR #2243

canonical: gh pr view 2243 --json commits,headRefOid,files (this session, this round)
New head commit `5b0b343c5d2556a54ad19f95dab2bb564508b879`, three commits
on top of main: `71bfa6de` (unchanged from last round), `26c128ce`
(unchanged), `5b0b343c` ("fix 3 more gates/ sibling-import collision
sites the exact-line audit missed").

canonical: 5b0b343c:gates/ui_evidence_gate.py:74-88, 5b0b343c:gates/roles_due.py:30-40, 5b0b343c:gates/skip_eligibility.py:26-36 (read this round, this session, disposable git worktree at the new head — never an in-place checkout of this session's own tree, per last round's "What did not work")
A6 re-graded from Incorrect to Present. All three sites last round found
by execution now carry the same explicit-file-path `importlib` loader
(private key `_on_the_record_gates_sibling_impl`) as
`gates/record_lint.py`'s own template.

canonical: same three file:line ranges above, this round, this session
Each site's own original binding shape is preserved: `ui_evidence_gate.py`'s
load stayed function-local (indented, inside `check_record()`);
`roles_due.py` keeps its `as _gates` alias; `skip_eligibility.py` keeps
its `# noqa: E402` trailing comment.

canonical: python3 -c "import runpy; ..." (worktree at pr-2243-review-v2 head 5b0b343c, this round, this session — output below)
```
$ cd /tmp/pr2243-repro-v2   # disposable worktree, git worktree add, removed after use
$ python3 -c "
import runpy
for m in ('gates.ui_evidence_gate', 'gates.roles_due', 'gates.skip_eligibility'):
    try:
        runpy.run_module(m, run_name='__not_main__', alter_sys=False)
        print(m, 'import OK')
    except AttributeError as e:
        print(m, 'ATTRIBUTEERROR:', e)
"
gates.ui_evidence_gate import OK
gates.roles_due import OK
gates.skip_eligibility import OK
```

canonical: same worktree, same round, this session — functional probe below, not import-only
Import-only success can mask a swallowed AttributeError — the exact gap
last round's finding raised about `roles_due.py`'s bare `except
Exception: return []` — so this round functionally exercised each site
too, not just imported it.
```
$ python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('gates').resolve()))
import roles_due
print('roles_due._gates has changed_files:', hasattr(roles_due._gates, 'changed_files'))
cf = roles_due._gates.changed_files(Path('.'))
print('_gates.changed_files() direct call returned (list, len):', type(cf), len(cf))
import skip_eligibility
print('skip_eligibility.gates has BASE:', hasattr(skip_eligibility.gates, 'BASE'))
import ui_evidence_gate
bad = ui_evidence_gate.check_record(Path('.'), 'probe-record.md', 'verdict: pass\n', ['src/ui/probe.tsx'])
print('ui_evidence_gate.check_record() returned:', bad)
"
roles_due._gates has changed_files: True
_gates.changed_files() direct call returned (list, len): <class 'list'> 11
skip_eligibility.gates has BASE: True
ui_evidence_gate.check_record() returned: []
```

canonical: python3 -c "..." run above, this round, this session
A real 11-item list from `_gates.changed_files()` (not an AttributeError,
and not the same-looking `[]` the swallow would also produce) is what
distinguishes "actually resolved" from "silently swallowed and looks
fine."

canonical: grep -rnE shape-complete pattern (worktree at 5b0b343c, this round, this session — command and output below)
Re-ran the audit with the same shape-complete pattern last round derived
(indent/alias/trailing-comment), now against the new head:
```
$ grep -rnE '^[[:space:]]*import[[:space:]]+gates([[:space:]]+as[[:space:]]+[A-Za-z_][A-Za-z0-9_]*)?([[:space:]]*#.*)?$' gates/*.py | grep -v "^gates/test_"
```
(zero output — no non-test `gates/*.py` file matches the collision shape
any more)

canonical: same worktree, this round, this session — cross-process check below
Also re-ran the cross-process regression check the before-landing hunter
used against the first (rejected) fix attempt, now against all seven
fixed files in one process — the exact failure mode a careless fix could
reintroduce.
```
$ python3 -c "
import runpy
for m in ('gates.record_lint', 'gates.claims', 'gates.risk_report', 'gates.ci', 'gates.ui_evidence_gate', 'gates.roles_due', 'gates.skip_eligibility'):
    try:
        runpy.run_module(m, run_name='__not_main__', alter_sys=False)
        print(m, 'import OK')
    except AttributeError as e:
        print(m, 'ATTRIBUTEERROR:', e)
"
gates.record_lint import OK
gates.claims import OK
gates.risk_report import OK
gates.ci import OK
gates.ui_evidence_gate import OK
gates.roles_due import OK
gates.skip_eligibility import OK
```

canonical: python3 -c "..." run above, this round, this session
All seven resolve cleanly in one interpreter, matching the private-key
cache design's claim that it never touches `sys.modules["gates"]`.

canonical: python3 -m pytest gates/test_record_lint.py -q && python3 -m pytest gates/ -q (worktree at 5b0b343c, this round, this session — output below)
Gate suite and full regression re-executed fresh this round:
```
$ python3 -m pytest gates/test_record_lint.py -q
....................................................................     [100%]
68 passed in 1.04s
$ python3 -m pytest gates/ -q
929 passed, 8 xfailed in 17.17s
```

canonical: python3 -m gates.record_lint && python3 gates/record_lint.py (fresh empty repo at /tmp/empty-repo-v2, this round, this session — output below)
Empty-state (A2a/A2b) re-verified fresh against a new disposable
fixture:
```
$ python3 -m gates.record_lint; echo exit:$?
record_lint: no records found under /tmp/empty-repo-v2 — 검사할 레코드가 없다.
exit:0
$ python3 gates/record_lint.py; echo exit:$?
record_lint: no records found under /tmp/empty-repo-v2 — 검사할 레코드가 없다.
exit:0
```

canonical: git log --oneline main..HEAD -- gates/record_lint.py gates/claims.py gates/risk_report.py gates/ci.py (this round, this session — output below)
```
71bfa6de issue-2226: fix gates/ sibling-import collision under python3 -m gates.<X>
```
A4 (provenance) unaffected — the four originally-fixed files did not
change again this round (single commit above, already reviewed last
round), so its Present verdict carries forward by sha.

canonical: 5b0b343c:docs/issue-2226/reports/implementation/2026-08-25-hunt-lint-import-fix.md (read this round, this session, same disposable worktree — a hunt-record file that exists on PR #2243's branch, not on this session's own issue-2226/conformance-review branch)
A before-landing warrant-hunter found `gates/roles_due.py:204`'s
`_gates.BASE = base` mutates the shared `gates.py` singleton, leaking
into every other consumer's `gates.BASE` read for the rest of the
process — informational, out of this issue's frozen Acceptance scope.

canonical: git diff main...HEAD -- gates/roles_due.py (worktree at 5b0b343c, this round, this session — output showed only the import-loading block, lines 32-40, changed; line 204 untouched)
Independently checked, not just cited: the only change to
`gates/roles_due.py` in this PR is the import-loading block — line 204's
`_gates.BASE = base` predates it, so the mutation is pre-existing, not a
regression from this issue's fix.

canonical: same git diff above, this round, this session
Under direct-script invocation (the only form that worked pre-fix),
`roles_due.py` and `skip_eligibility.py` already shared one
`sys.modules["gates"]` object, so the leak was already reachable before
issue-2226's fix — this fix only makes it newly reachable via `-m` forms
that previously crashed before reaching that line.

canonical: A6 re-derivation, gate/regression re-execution, and the roles_due.py diff-check above, all this round, this session
Confirmed Present-and-out-of-scope: issue #2226's Acceptance concerns
invocation-form resolution, not `roles_due.py`'s pre-existing
shared-mutable-state design. Carried into Open findings below as
informational, matching how the implementation record itself flagged it.

## Open findings

1. RESOLVED this CHANGES round. Three `gates/` files carried the same
   sibling-import/namespace-package collision issue-2226 fixed
   elsewhere, missed by the PR's own audit grep:
   `gates/ui_evidence_gate.py:82`, `gates/roles_due.py:32`,
   `gates/skip_eligibility.py:28`.
canonical: CHANGES-round A6 re-derivation above, this record
   Resolution path: already applied and verified this round — all three
   now carry the explicit-file-path `importlib` loader.
canonical: CHANGES-round grep/cross-process/functional-execution
   evidence above, this record
   That evidence confirms no remaining site and rules out a silent
   AttributeError swallow at any of the three. Verdict A6 upgraded
   Incorrect -> Present.

2. Informational, not blocking this Acceptance grading:
   `gates/roles_due.py:204`'s `_gates.BASE = base` mutates the shared
   `gates.py` singleton, leaking into every other consumer's
   `gates.BASE` read for the rest of the process.
canonical: CHANGES-round `roles_due.py:204` finding above, this record
   Resolution path: not this issue's scope to prescribe — whoever next
   touches `roles_due.py`'s `base` override (a follow-up on
   `issue-2226/implementation` or a fresh issue, builder's/maintainer's
   call) should scope the mutation instead of sharing mutable module
   state across gate files.
canonical: CHANGES-round git-diff check above, this record — confirmed
   pre-existing, not introduced by this PR
   Out of issue-2226's frozen Acceptance scope (invocation-form
   resolution, not this file's pre-existing design), so it does not
   affect this record's `result:`.

## Next steps

loop_state is terminal (`reported`) for this review-record kind (contract
v3 session-protocol kind-to-terminal-state table): all six original
findings are resolved to a verdict, the CHANGES round upgraded A6 to
Present with its resolution already applied and verified, and Open
findings item 2 is informational with a stated resolution path rather
than a blocker.
canonical: Findings and CHANGES-round sections above, this record — no
further checking is pending in this session.
No further action is required from this issue's own Acceptance; Open
findings item 2 is a separate, pre-existing design question for whoever
next touches `roles_due.py` to pick up.

## What did not work

Mid-review, a `git checkout pr-2243-review -- .` (intended to read a
handful of files at the PR head) was run without a preceding path scope
and without a `git status` check first — it silently overwrote this
session's entire working tree with the PR branch's full file set,
including files unrelated to this issue (`events.py`, `watchdog.py`,
`spawn.py`, `tests/test_watchdog_local_signals.py`, etc.).
canonical: git status --short (this session, immediately after the
mistaken checkout — output showed the PR's changes staged-looking against
unrelated files, which is what surfaced the mistake)
Reverted with `git reset --hard HEAD` before anything was inspected or
acted on from that state; this session's own untracked files
(`docs/issue-2226/`, `.on-the-record/directive/`) were never touched by
the reset (untracked files survive `--hard`).
canonical: git status --short immediately after the reset, this session —
  confirmed only the pre-existing untracked entries remained
All subsequent file reads used `git show <sha>:<path>` /
`git diff main..pr-2243-review` (read-only) or a separate disposable
`git worktree`, never another in-place checkout of this session's own
tree.

skill-verdict: conformance-review-requirement-extraction — applied: invoked (prior round); split the bundled empty-state sentence into two obligations, tagged each of A1-A6 with a dimension. No new requirements this CHANGES round — the same six items were re-graded, not re-extracted.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; re-loaded this CHANGES round before re-grading A6.
canonical: CHANGES-round evidence above, this record
Method chosen: Test for the re-verification of the three sites (fresh runpy import checks plus functional execution, reusing the gate suite for A1/A3, freshly executing the empty-state fixture for A2a/A2b); Inspection carried forward for A4 (file unchanged since last round).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; re-loaded this CHANGES round to upgrade A6 from Incorrect to Present.
canonical: CHANGES-round functional-execution evidence above, this record
Import-only success could mask the same silent-swallow shape the prior Incorrect verdict was built on, so each site was also functionally exercised before finalizing Present, per the skill's re-check-before-finalizing rule.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; this CHANGES round's evidence cites file:line-range plus the new head sha, including cross-branch citations for files that exist on the PR branch but not this session's own branch.
skill-verdict: conformance-review-finding-record — applied: invoked; appended the CHANGES-round section and updated Open findings/Next steps in this same file, keeping the five-verdict discipline.
skill-verdict: conformance-review-sampling-derivation — not-applicable (prior round): the PR's file set was small enough for full enumeration; no sampling was derived.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting; A6 and the informational BASE-mutation finding are reported, not severity-banded.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; treated the implementation record's own "fixed, verified, out-of-scope" claims as claims to re-derive rather than facts to cite.
canonical: CHANGES-round grep/functional-execution/git-diff evidence above, this record
Re-ran the audit grep independently rather than trusting the PR's own re-audit output, functionally executed each site rather than accepting import-only success, and independently confirmed via a git diff that the BASE-mutation finding predates this PR rather than citing the implementation record's own claim at face value.
skill-verdict: implementation-audit — applied: invoked (prior round); this session structurally matches the skill's "Session B" evaluator role. Same posture carried into this CHANGES round without re-invoking.
other mounted skills: not triggered (freelunch fan-out skills, terse, dataviz, code-review, security-review, run, init, etc.).
