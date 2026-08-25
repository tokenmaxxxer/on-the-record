---
status: proposed
subject: issue-2241
stage: 5
files:
  - gates/merge_gate.py
  - gates/spawn_on_pr.py
  - test/test_merge_gate_record_kind.py
  - docs/handbooks/observer-verification.md
---

# Stage 5 (last) — move the observer pair onto record-kind

## Request

Rewrite `gates/spawn_on_pr.py`'s `PR_TRIGGERED_ROLES = ("execution-observation",
"conformance-review")` and `gates/merge_gate.py`'s
`required_verification_missing()` to check for record-kind presence
(`kind: execution-observation`, `kind: conformance-review`, per stage
1's vocabulary) instead of matching role-named files on the board.

## Constraints

- **Ordered last, deliberately** — issue #2241's own text: this exact
  hardcode "is exactly what jammed merges tonight (#2233) and fed the
  #2238 runaway." This stage requires stages 1 (record-kind exists), 3
  (write-scope no longer role-gated), and 4 (naming stabilized) all
  landed and stable first.
- Record-kind must keep preventing self-verification (issue's own
  non-goal: "do not weaken independent verification... retiring roles
  is not a reason to accept self-verification") — the record-kind
  check alone is not suffient; author-identity (stage 1/3) must also
  differ between the artifact's author and the record-kind's author.
- Frozen decision `single-enforcement-surface`: stays in `gates/`
  (core), never moves to a skill-side check.

## Rationale

Chosen: `required_verification_missing()` checks for the presence of
two record-kind values on the subject's board entries, cross-referenced
against `author:` to confirm the record-kind was produced by a
different author than the artifact under review. Rejected alternative:
land this stage earlier — e.g. immediately after stage 1, once
record-kind exists in principle. Rejected explicitly per issue #2241's
own text: this is the precise hardcode point that jammed merges in
incident #2233 and fed the #2238 runaway; touching it before stages 2-4
are stable and proven reproduces both incidents. The staging order
itself is the risk mitigation here, not a technical dependency alone.

## What will be done

- `gates/spawn_on_pr.py`: `PR_TRIGGERED_ROLES` becomes
  `PR_TRIGGERED_RECORD_KINDS = ("execution-observation",
  "conformance-review")` (same two values — the survey found this
  narrowing itself, of 10 candidate roles to these 2 mechanically
  presence-checkable ones, is unrelated to the role→record-kind swap
  and stays as-is); `applicable_roles()` becomes
  `applicable_record_kinds()`, scanning board entries' `kind:` field
  instead of filename.
- `gates/merge_gate.py required_verification_missing()`: delegates to
  the renamed function; `_exempt_own_role`'s circularity-breaking logic
  is preserved, re-keyed on `author:` matching the subject's own author
  instead of branch-name matching.
- Self-verification guard: a record-kind match whose `author:` equals
  the subject artifact's own `author:` does not count toward
  satisfying `required_verification_missing()` — this is the
  mechanical enforcement of the non-goal above.
- `docs/handbooks/observer-verification.md` documents the rewritten
  check and the self-verification guard explicitly.

## Out of scope

- Changing which two kinds are required, or widening/narrowing the
  observer pair — that's a separate policy question from this issue's
  role→record-kind rewrite.
- Any change to branch naming (stage 4, already landed) or write-scope
  (stage 3, already landed).

## How you'll know it worked

- `test/test_merge_gate_record_kind.py`: a subject board with both
  required `kind:` values present (different authors) reports no
  missing verification; missing one reports it by record-kind name, not
  role name; a `kind:` match whose `author:` equals the subject's own
  author does not satisfy the requirement (self-verification guard
  proven).
- `_exempt_own_role`'s (renamed) circularity-breaking path still
  prevents an observer's own PR from blocking on its own missing
  record, re-verified under the new author-keyed logic.
- A live re-run of `required_verification_missing()` against this
  repo's current board produces the same missing-set as today's
  role-keyed version, for every subject where record-kind data already
  exists from stage 1 onward (parity check).

## Rollback

Revert `gates/merge_gate.py`/`gates/spawn_on_pr.py` to the role-matching
version; every record already carrying both `role:` and `kind:` (stage
1 onward is additive) remains correctly evaluated under the reverted
role-keyed check, so rollback does not strand any subject's
verification state.

## Accumulation

`gates/merge_gate.py` (4 existing call sites) and `gates/spawn_on_pr.py`
(2) each get a rename plus a re-keyed lookup, not new call sites. If
the observer pair ever needed to grow to N required record-kinds, the
existing tuple-and-presence-check shape already scales to N without
new inline branches — this stage does not change that shape, only what
the presence-check matches against.
