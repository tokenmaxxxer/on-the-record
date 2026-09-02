---
issue: 3073
role: silent-failure-audit+test-derivation-706474c0
author: silent-failure-audit+test-derivation-706474c0
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/hooks/hook_classification.json
    sha: same-commit
  - path: on-the-record/hooks/test_hook_classification.py
    sha: same-commit
---

# issue-3073 — silent-failure-audit+test-derivation-706474c0 record

## What was done

Added the two missing `hook_classification.json` entries for
`gate-registration-post-guard.sh` (PR #2872's pre/post pair, both
`wrapped: true`), classified `observability`, each with its own
rationale. Also updated `test_registration_count_matches_the_issues_own_count`'s
hardcoded literal and comment, since that test checks `hooks.json`'s own
live registration count independently of the classification file, and
PR #2872 added two live registrations that the old literal never
accounted for:

derived: `git diff HEAD~1 -- on-the-record/hooks/test_hook_classification.py`
```
-        self.assertEqual(len(live), 12, live)
-        self.assertEqual(sum(1 for r in live if r[3]), 11, live)
+        self.assertEqual(len(live), 14, live)
+        self.assertEqual(sum(1 for r in live if r[3]), 13, live)
         self.assertEqual(sum(1 for r in live if not r[3]), 1, live)
```

Acceptance requirement met — checked: `python3 -m pytest on-the-record/hooks/test_hook_classification.py -q` — result: 6 passed

Acceptance requirement met — checked: `python3 -m pytest on-the-record/hooks/ -q` — result: 33 passed

Acceptance requirement met — checked: `bash -c "test $(grep -c gate-registration-post-guard on-the-record/hooks/hook_classification.json) -ge 1"` — result: pass, 2 matches found

## Why

Classified both registrations `observability`, not `invariant-injecting`,
despite `gate-registration-post-guard.sh` superficially resembling
`post-landing-obligation-gate.sh` (both write a state/record file from a
`PostToolUse` hook). The distinguishing test is `hook_classification.json`'s
own `_comment`: invariant-injecting means "the hook's absence leaves the
session running without a rule it establishes or enforces"; observability
means "the hook only reports/warns/records; its absence loses signal, not
a rule."

canonical: `on-the-record/hooks/gate-registration-post-guard.sh` lines 62-64 and 96-104 (read directly) — the header states the `post` mode is "pure side-effect, always exit 0" and "Cannot deny", and the `pre` mode only emits `hookSpecificOutput.additionalContext` — advisory text a session reads, not a decision any other gate consumes.

derived: `grep -rn "OTR_GRG_POST\|otr-grg-post" on-the-record/hooks --include="*.sh" --include="*.py"`
```
on-the-record/hooks/gate-registration-post-guard.sh:51:#           ${OTR_GRG_POST_STATE_DIR:-$TMPDIR/otr-grg-post}/<session_id>.json.
on-the-record/hooks/gate-registration-post-guard.sh:95:STATE_DIR="${OTR_GRG_POST_STATE_DIR:-${TMPDIR:-/tmp}/otr-grg-post}"
on-the-record/hooks/gate-registration-post-guard.sh:130:mode = os.environ.get("OTR_GRG_POST_MODE", "")
on-the-record/hooks/gate-registration-post-guard.sh:131:state_dir = os.environ.get("OTR_GRG_POST_STATE_DIR", "")
on-the-record/hooks/gate-registration-post-guard.sh:134:    e = json.loads(os.environ.get("OTR_GRG_POST_PAYLOAD", ""))
on-the-record/hooks/gate-registration-post-guard.sh:433:OTR_GRG_POST_PAYLOAD="$payload" OTR_GRG_POST_MODE="$MODE" OTR_GRG_POST_STATE_DIR="$STATE_DIR" \
on-the-record/hooks/test_gate_registration_post_guard.py:34:    env["OTR_GRG_POST_STATE_DIR"] = str(state_dir)
on-the-record/hooks/test_gate_registration_post_guard.py:49:        self._tmp = tempfile.TemporaryDirectory(prefix="otr-grg-post-test-")
on-the-record/hooks/test_gate_registration_post_guard.py:226:        env["OTR_GRG_POST_STATE_DIR"] = str(self.state_dir)
on-the-record/hooks/test_gate_registration_post_guard.py:281:        env["OTR_GRG_POST_STATE_DIR"] = str(self.state_dir)
```

Only the guard script itself and its own test fixture ever touch that
state dir — no other gate reads it, unlike `post-landing-obligation-gate.sh`'s
record, which canonical: `on-the-record/hooks/hook_classification.json` line 58 (its existing entry's own rationale) says "the northpole loop depends on." No decision anywhere else depends on this pair's state file; only a same-session nudge is lost if it's absent. The strong, deny-before-write guarantee for a missing registration row still lives entirely in `gate-registration-guard.sh`'s unchanged PreToolUse `--cached` check — this pair is explicitly the weaker, report-only half of that split (issue #2705, canonical: `on-the-record/hooks/gate-registration-post-guard.sh` lines 1-3 and 83-92), so classifying it as a rule-enforcer would misstate what it actually does.

Landing-gate audit (separate from the classification fix, requested by
the issue, not a gate built here): no gate in the documented merge
procedure would have caught this omission, matching the issue's own
account. canonical: `gates/check_runner.py` lines 2-9 (its own module
docstring, read directly) — it executes only the `## Acceptance` checks
declared in the issue being landed (issue #2705's own two criteria), not
`on-the-record/hooks/` as a whole. canonical: `gates/landing_readiness.py`
lines 33-52 (`classify()`, read directly) — `checks` there is `gh pr
checks`' external-CI summary string plus record/approval presence; this
repository ships no `.github/workflows/` (derived: `ls .github/workflows/`
— result: no such directory), so there is no CI job that would run the
hook suite either. `merge-allow-gate.sh` only auto-allows `gh pr merge`
once `landing_readiness` already reports READY (canonical: `on-the-record/hooks/merge-allow-gate.sh`
lines 1-27, its own header) and runs no tests itself. None of the three
gates that stand between a PR and `gh pr merge` ever execute
`on-the-record/hooks/` as a suite, so this class of omission — a hook
landing in `hooks.json` with no matching `hook_classification.json` row —
was structurally invisible to the merge procedure as documented.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 3073` output (state: OPEN) — failing commands,
cause (`grep -c gate-registration-post-guard` mismatch between
`hooks.json` and `hook_classification.json`), and the scope/must-not
clauses. Read `on-the-record/hooks/hooks.json`, `hook_classification.json`,
`test_hook_classification.py`, and `gate-registration-post-guard.sh`
directly from the working tree to derive the classification and the
count-literal fix.

## Open findings

None — the "any gate that would have caught this" question the issue
asked is answered above (none would have); building that gate is
explicitly out of this issue's scope per its own text.

## Next steps

None — record is terminal.

skill-verdict: silent-failure-audit — not-applicable: this issue's changes are hook_classification.json data entries and one test-literal update, no error-handling code (try/catch, I/O, network, validation) was written or modified
skill-verdict: test-derivation — not-applicable: the issue's own Acceptance section already ships as three concrete executable checks (pytest/grep commands); there was no prose requirement needing technique selection or a traceability matrix to derive
other mounted skills: not triggered
