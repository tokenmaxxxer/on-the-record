---
status: proposed
files:
  - roles/specs/secure-coding.spec.json
  - gates/test_secure_coding_routing.py
  - docs/issue-1005/reports/implementation.md
---

# Proposal — issue #1005, secure-coding routing-gap fix

## Request

Per #993 phase-1 (docs/issue-993/proposals/product-discovery.md, merged
#1004): secure-coding's `board_condition` never fires under real
orchestration, so the role is structurally unreachable. Fix the routing
so security-relevant changes realistically route to it, with live-fire
proof that a seeded security-relevant change surfaces the role and an
unrelated change does not.

## Constraints

- The evaluator (`gates/roles_due.py`) already generalizes over any spec
  carrying a `use_when.trigger` block (canonical:
  docs/issue-1005/reports/implementation/survey.md, "What causes the
  gap") — no gate/hook code change is required, only the spec's own
  missing key.
- `roles/secure-coding.json`'s Korean `use_when` field is the
  human-readable board_condition source; `roles/specs/secure-coding.spec.json`
  is the machine-checkable counterpart the evaluator reads. Both already
  agree on wording; only the spec side needs the structured predicate.
- The `trigger` shape (`path_patterns`, `content_patterns`,
  `record_absent_for`) is fixed by `roles_due.py`'s own reader — not
  something this proposal can redesign.

## Rationale

Considered rewriting `board_condition`'s prose to be narrower/clearer
instead of adding a `trigger`. Rejected: the #993 audit already confirmed
the prose is accurate and matching commits already exist — the failure
is purely mechanical (the evaluator only reads `use_when.trigger`, and
secure-coding has none), so rewriting prose would leave the role exactly
as unreachable as before. Adding `trigger`, mirroring the sibling
security-threat-model.spec.json's already-working shape, fixes the
actual failure point.

## What will be done

1. Add `use_when.trigger` to `roles/specs/secure-coding.spec.json`:
   - `path_patterns`: patterns covering both halves of the stated
     condition — authentication surfaces (`**/auth/**`,
     `**/*credential*`, `**/*permission*`, `**/*secret*`,
     `**/*password*`, `**/*login*`) and input-handling surfaces
     (`**/*input*`, `**/*sanitiz*`, `**/*validat*`).
   - `content_patterns`: `["authenticate", "password", "credential",
     "sanitize", "validate input"]`.
   - `record_absent_for`: `"secure-coding"`.
2. Add `gates/test_secure_coding_routing.py`: builds a scratch git repo
   the same way `gates/test_roles_due.py` does, but loads the real
   `roles/specs/secure-coding.spec.json` from this working tree (not a
   synthetic spec) via `roles_due.load_triggered_specs`, then runs two
   cases against `roles_due.roles_due()`:
   - seeded security-relevant diff (e.g. a file under `auth/` or naming
     `credential`) with no existing secure-coding record -> secure-coding
     appears in the due list.
   - seeded unrelated diff (e.g. a `widget.py` touching neither pattern
     set) -> secure-coding does not appear.
3. Run the new test and the existing `gates/test_roles_due.py` once,
   pasting real output into the phase-2 record.

## Out of scope

- Any change to `gates/roles_due.py` itself — its trigger-reading logic
  already works and is unit-tested; this proposal only supplies
  secure-coding's missing input to it.
- Release-engineering's routing gap (#993 phase-1 noted it as a
  tentative second scope, pending write_scope check) — not touched here;
  a separate issue if pursued.
- issue-retrospective / knowledge-management's routing gaps — #993
  phase-1 deferred these pending commit-sha-level confirmation; not
  re-opened here.
- Wiring `roles_due.py`'s output into any enforcement gate (currently
  surfaced-only, per its own module docstring) — unchanged by this
  proposal.

## How you'll know it worked

`gates/test_secure_coding_routing.py` passes, asserting: (a) a scratch
repo diff seeded to match secure-coding's real `trigger` patterns and
carrying no secure-coding record shows `secure-coding` in
`roles_due.roles_due()`'s output; (b) a scratch repo diff seeded to an
unrelated file shows an empty due list. Both are pasted as real test
output into `docs/issue-1005/reports/implementation.md`.
