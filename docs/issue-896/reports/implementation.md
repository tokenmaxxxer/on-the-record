---
code_under_review:
  - on-the-record/hooks/test-authoring-invariant-guard.sh
  - on-the-record/hooks/test_test_authoring_invariant_guard.py
  - on-the-record/hooks/hooks.json
  - gates/roles_due.py
  - gates/test_roles_due.py
  - roles/specs/security-threat-model.spec.json
  - roles/specs/accessibility.spec.json
  - roles/specs/execution-observation.spec.json
  - roles/specs/conformance-review.spec.json
  - roles/specs/interaction-design.spec.json
  - spawn.py
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
type: feature
breaking: false
canonical: python3 -m pytest gates/ on-the-record/hooks/ -q
verdict: pass
loop_state: landed
---

# issue-896 implementation record (step 2, invariant-first reframe)

## What was done
Per the operator's REFRAME comment on #896 (invariant-first, supersedes
the issue body's spawn-when framing):

1. `on-the-record/hooks/test-authoring-invariant-guard.sh` — a standing,
   always-on `PreToolUse`+`Bash` gate on `git commit`: denies a commit
   that changes a code path with no test path changed in the same set,
   unless the commit message carries a reasoned `Test-N/A: <reason>`
   trailer (the explicit N/A escape). No spawn, no cost decision.
2. `gates/roles_due.py` + `spawn.py roles-due` — the board_condition
   evaluator for the JUDGMENT residue only (test-authoring's own bar
   moved to the standing invariant above, so it is deliberately excluded
   from this evaluator's roster). Reads a `use_when.trigger` block (path
   globs + optional content regexes + `record_absent_for`) added to five
   role specs whose Korean `use_when` already carried a parenthetical
   English `board_condition`: `security-threat-model`, `accessibility`,
   `execution-observation`, `conformance-review`, `interaction-design`.
   Surfaced-only, never blocks, matches `flows.py`'s existing repo-local
   reporting class.
3. Registered both new mechanisms in `docs/specs/enforcement-boundary.md`
   / `docs/specs/generated-paths.md` (mechanical registration this repo's
   own `gate-registration-guard.sh`/`test_boundary.py`/
   `test_generated_paths.py` require) and in `on-the-record/hooks/hooks.json`.

## Why
canonical: gh issue view 896 --comments (REFRAME comment, read this session)
The REFRAME states the pre-existing spawn-when framing is cost-biased and
gets skipped under token pressure; the fix is to encode each load-bearing
expertise's non-negotiable bar as an always-on gate (standing invariant)
and reserve the expensive role spawn for genuine judgment. test-authoring
was named as the highest-value universal invariant not yet enforced.

## Upstream
Basis: docs/issue-896/proposals/2026-08-12-step2-invariant-and-evaluator.md
(this phase's own proposal), building on the already-landed phase-1
design at docs/issue-896/proposals/2026-08-12-role-activation-evaluator-and-enforcement.md
canonical: docs/issue-896/proposals/2026-08-12-role-activation-evaluator-and-enforcement.md (read this session, present in the working tree)

## Rationale for deviations
The phase-1-of-this-phase proposal named seven roles for `roles-due`
triggers (`security-threat-model`, `accessibility`, `product-discovery`,
`interaction-design`, `defect-verification`, `execution-observation`,
`conformance-review`). While authoring the `trigger` blocks it became
clear two of the seven — `product-discovery` ("an issue's requirement is
still at problem/hypothesis level") and `defect-verification` ("a
record's result is disputed by another comment on the same commit sha")
— describe issue-level/comment-level state, not anything a diff-path or
diff-content pattern can approximate honestly. A fabricated path/content
trigger for either would have been decoration, not a real predicate.
Both are dropped from this round and listed under Next steps below
instead of guessed at; the other five shipped as planned.

## Doc placement
- `docs/specs/enforcement-boundary.md` — registered `roles_due.py` and
  `test-authoring-invariant-guard.sh` (mechanism-registration ladder rung,
  same commit as the code).
- `docs/specs/generated-paths.md` — registered
  `test-authoring-invariant-guard.sh` (n/a, read-only, no write call).
- No env var, dependency, or migration was introduced — no handbook entry
  needed.

## What did not work
`gates/roles_due.py`'s first attempt used `fnmatch.fnmatch(path, pat)`
alone against patterns like `**/auth/**`. Expected: this to match a
repo-root path like `auth/login.py`. Actual: `fnmatch` has no
recursive-glob semantics — a leading `**/` in the pattern requires a
literal `/` character to already precede the matched segment, so a
root-level path with no leading `/` never matched, and
`gates/test_roles_due.py`'s "matching path with no record -> due" case
failed with an empty result. Fixed by also trying the pattern with its
leading `**/`/`*/` stripped.
`derived: python3 gates/test_roles_due.py` — before the fix, one of the
five cases in that file failed; after the fix, the rerun in Verification
run below shows all five green.

## Next steps
- Decompose `product-discovery` and `defect-verification`'s
  `board_condition` into triggers once a diff-derivable (or board-comment-
  derivable) predicate is designed — dropped from this round, see
  Rationale for deviations above.
- Decompose the remaining ~36 role specs' `use_when.board_condition` into
  structured triggers (out of scope both here and in the already-landed
  phase-1 proposal).
- Wire `roles-due` into `spawn.py status`'s automatic output, or promote
  any of the five surfaced roles to hard-gated, once real due/N-A data
  accumulates (phase-1 proposal's own ITWWS).
- The #776 harness scenario proving activation (phase-1 proposal section
  4) — a separate, later step per the issue's own execution plan.

## Open findings
canonical: python3 -m pytest gates/ on-the-record/hooks/ -q (executed this session; no open finding recorded against this diff)
None open yet. A warrant-hunter round runs before landing per the
warrant-directive; a finding from it gets a `closed_checks:` entry here
or an update to Next steps before merge.
Resolution path: append the finding and its disposition to this record
before the PR merges.

## Verification run
`derived: python3 -m pytest gates/ on-the-record/hooks/ -q`
```
703 passed, 1 xfailed in 35.59s
```
canonical: python3 -m pytest gates/ on-the-record/hooks/ -q (executed this session, output pasted above verbatim)

`derived: python3 spawn.py roles-due -C .`
```
[roles-due] 판단(judgment) 잔여 — 조건이 걸렸고 아직 기록 없음:
  - accessibility (issue-896): path matched '**/interaction*': roles/specs/interaction-design.spec.json
  - conformance-review (issue-896): path matched '**/*.py': gates/roles_due.py
  - execution-observation (issue-896): path matched '**/*.py': gates/roles_due.py
  - security-threat-model (issue-896): content matched 'trust boundary' in roles/specs/security-threat-model.spec.json
```
canonical: python3 spawn.py roles-due -C . (executed this session, output pasted above verbatim)
