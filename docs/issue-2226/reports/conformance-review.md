---
issue: 2226
role: conformance-review
loop_state: reported
upstream:
  - path: PR #2243 (branch issue-2226/implementation, GitHub)
    sha: 26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a
subject: PR #2243 ("issue-2226: fix gates/ sibling-import collision under python3 -m gates.<X>") graded against issue #2226's frozen `## Acceptance` section
test: independent re-execution of gates/test_record_lint.py and both invocation forms from a git worktree at the PR's head commit; independent re-derivation of the PR's own gates/-wide audit grep, widened past its exact-match anchor
result: failed
assertedBy: builder-blind conformance-review session (branch issue-2226/conformance-review) — no access to PR #2243's builder session (issue-2226/implementation) or its rationale beyond what the PR body and diff state; verdicts below rest on the issue body, the PR diff, and code/tests read from the PR's own head commit
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

## Open findings

1. Three `gates/` files carry the same sibling-import/namespace-package
   collision issue-2226 fixed elsewhere, missed by the PR's own audit
   grep: `gates/ui_evidence_gate.py:82`, `gates/roles_due.py:32`,
   `gates/skip_eligibility.py:28`.
canonical: A6 finding above, this record — reproductions for each file
   Resolution path: apply the same explicit-file-path-load fix already
   used in the four PR-fixed files (`gates/record_lint.py:28-55` is the
   template) to each of the three, or restructure each to receive `gates`
   as a parameter from a caller that already holds a correctly-resolved
   reference instead of importing it itself. `roles_due.py`'s
   silent-swallow behavior around the broken call is a second, narrower
   issue worth fixing independently of which import-fix shape is chosen
   (the `except Exception: return []` should not treat "my own dependency
   failed to resolve" the same as "the diff is unreadable"). This record
   does not prescribe which fix to take — reporting, not patching, is
   this skill's scope. Owner: a follow-up on `issue-2226/implementation`
   or a fresh issue, builder's/maintainer's call.
canonical: A6 finding above, this record — roles_due() probe output

## Next steps

loop_state is terminal (`reported`) for this review-record kind (contract
v3 session-protocol kind-to-terminal-state table): the six findings above
are all resolved to a verdict, and the one Incorrect verdict has a stated
resolution path in Open findings item 1.
canonical: Findings and Open findings sections above, this record — no
further checking is pending in this session.
The open finding itself needs a human/builder decision on where the fix
lands (reopen issue-2226, or a new issue) — not this session's call.

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

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the bundled empty-state sentence into two obligations (rule 1), tagged each of A1-A6 with a dimension (rule 6), kept A3's disjunction as one conditional item rather than merging it into A6 (rule 5).
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Test for A1/A2a/A2b/A3/A6 (reused the existing gate suite where it existed, freshly executed where it didn't), Inspection for A4 (a static provenance-presence check on the record artifact).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; Incorrect (not Absent) for A6 since the record's own completeness claim is contradicted by reproducible counterexamples rather than merely unaddressed; re-checked each of the three counterexamples once (rule 6) before finalizing rather than asserting from a single grep read.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every finding cites file:line-range plus the PR head sha (26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a) or the exact command that produced the evidence.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote six `---`-delimited requirement blocks with the full field list, `spec_vs_built` only on the one Incorrect verdict.
skill-verdict: conformance-review-sampling-derivation — not-applicable: the PR's file set (4 non-test files + 1 gate script) was small enough for full enumeration; no sampling was derived.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting; A6 and its open finding are reported, not severity-banded.
skill-verdict: implementation-audit — applied: invoked; this session already structurally matches the skill's "Session B" evaluator role (a separate conformance-review session with no access to the builder's implementation session's own reasoning), so its Present/Surface/Absent/Incorrect/Unverifiable discipline and its "don't assert Present from a code read alone" posture were applied directly to A6 rather than re-running the skill's own two-session setup from scratch — the claim-extraction step (its "Session A, Step 1") is already what conformance-review-requirement-extraction produced from the issue body.
other mounted skills: not triggered (freelunch fan-out skills, terse, dataviz, code-review, security-review, run, init, etc. — none matched a trigger beyond the conformance-review family and implementation-audit already invoked above).
