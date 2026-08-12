---
status: proposed
files:
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/test_deliverable_guard.py
  - docs/product/priorities.md
---

## Request

Resolve the Stop-time deadlock: `product-capture-stopgate.sh` asks the
orchestrator session to record priority/requirements/philosophy/goals
statements into a product doc path, and `deliverable-guard.sh` denies
the orchestrator that exact write, so the turn can neither satisfy the
nudge nor drop it. Requirement: northpole req#5 (problems are not
pushed back to the human — the gate conflict must be resolved by the
role, not left as a recurring nudge the human has to notice and
intervene on). Pick exactly one gate to own the product-doc path, and
capture the one pending entry (the #745 close-out comment, deprioritized
`infrastructure/no-direct-requirement`) once that path is decided.

## Constraints

- Exactly one gate ends up owning the path — the acceptance criterion
  is a test showing a capture path no PreToolUse gate blocks, on which
  the stopgate's own cross-check also passes.
- `deliverable-guard.sh`'s existing behavior for every other
  deliverable-shaped path is unchanged — this only carves a narrower
  exception, never widens the general deny.
- consult (requirements-engineering, docs/issue-1111/reports/consult-log.md
  entry logged by this session) recommends the PreToolUse-exemption
  path over moving the Stop-side capture definition to GitHub comments,
  medium confidence, reasoning: moving completion evidence to an
  external API (GitHub) introduces network-reliability and near-match
  spoofing risk into a hook that currently only ever reads the local
  working tree.

## Rationale

**Chosen approach (Option A):** extend `deliverable-guard.sh`'s
existing exemption list — currently just
`n.endswith("docs/specs/approvers.md")` — with one more exact-suffix
check for `docs/product/*.md` (and, matching `product-capture-stopgate.sh`'s
own issue-scoped fallback, `docs/issue-<n>/product/*.md`). Rationale:
this is the same hook, the same code shape, and the same category of
justification ("orchestrator scribing") already used for
`approvers.md` — no new mechanism, no new trust surface, and the
consult above independently converges on it.

**Alternative considered and rejected (Option B):** change
`product-capture-stopgate.sh`'s completion check so an on-issue
`priority-record`-tagged GitHub comment counts as capture, instead of
its current `git diff`/`git log -p` check against the tracked file.
Rejected for three reasons found in the survey
(docs/issue-1111/reports/implementation/survey.md): (1) it requires a
new dependency inside a Stop hook — a `gh` API call (network,
authentication, rate limits) — where today's check is a local `git`
subprocess with none of that; (2) "capture" would now mean two
different things depending on which repo shape the branch matches (the
comment path for the fallback branch case, the tracked-file path
nowhere else), which the acceptance criterion's single unblocked path
requirement does not ask for; (3) it does not actually free the
orchestrator to write `docs/product/priorities.md` on any future turn
that isn't resolved purely by commenting — the deadlock returns the
next time a category needs a real structured entry in the file itself,
not just a one-off close-out note.

## What will be done

1. `on-the-record/hooks/deliverable-guard.sh`: replace the single
   `n.endswith("docs/specs/approvers.md")` check with a check against a
   small tuple of exempt suffixes:
   `("docs/specs/approvers.md", "docs/product/requirements.md",
   "docs/product/priorities.md", "docs/product/philosophy.md",
   "docs/product/goals.md")`, plus the issue-scoped equivalents
   `docs/issue-<n>/product/<cat>.md` via a regex matching
   `product-capture-stopgate.sh`'s own four-category vocabulary
   (`requirements|priorities|philosophy|goals`) under either
   `docs/product/` or `docs/issue-\d+/product/`. Comment above the
   check updated to state the product-capture pairing (mirrors the
   existing approvers.md comment style).
2. `on-the-record/hooks/test_deliverable_guard.py`: add cases —
   orchestrator write to `docs/product/priorities.md` is allowed; write
   to `docs/issue-123/product/priorities.md` is allowed on a
   `issue-123/<role>`-shaped repo; write to an unrelated
   `docs/product/other.md` (not one of the four categories) is still
   denied, so the exemption stays scoped to the stopgate's actual
   vocabulary and does not become a general `docs/product/*` bypass.
3. `docs/product/priorities.md`: create it (bootstrap header matches
   `product-capture-stopgate.sh`'s own bootstrap shape: `# Priorities`
   + `Append-only, newest entry last.`) and append the pending entry —
   the #745 close-out statement, dated 2026-08-12, deprioritized
   `infrastructure/no-direct-requirement` behind #1110, the 7-scenario
   harness re-measurement, and the user's fresh-session E2E test.

## Out of scope

- `gates/test_product_capture_ownership.py` as a literal new file path
  — this repo's existing convention keeps each hook's tests beside the
  hook under `on-the-record/hooks/test_*.py`
  (`test_deliverable_guard.py`, `test_product_capture_stopgate.py`
  already there); the new cases land in the existing
  `test_deliverable_guard.py` instead of a new `gates/`-rooted file,
  since `gates/` is this repo's separate Python package for board
  gates, not hook tests. The acceptance's substance (an orchestrator
  capture path no PreToolUse gate blocks, on which the stopgate's own
  check passes) is what phase-2 delivers; the file location follows
  existing convention over the issue text's literal path.
- Any change to `product-capture-stopgate.sh` itself (Option B, and any
  other stopgate-side change) — not needed once Option A removes the
  block on the write it is already asking for.
- Widening `deliverable-guard.sh`'s exemption beyond the four named
  category files.
- The companion consult-regression issue referenced in #1111's body —
  separate issue, not this one (and moot here: the consult call in
  this session succeeded).

## How you'll know it worked

- `python3 on-the-record/hooks/test_deliverable_guard.py` — all cases
  pass, including the three new ones, pasted output in the phase-2
  record.
- A live PreToolUse Write to `docs/product/priorities.md` from an
  orchestrator-shaped payload (no `CLAUDE_ROLE`) exits 0 instead of 2.
- `docs/product/priorities.md` exists on the branch with the #745 entry
  appended, and a Stop-time run of `product-capture-stopgate.sh` no
  longer nudges for the `priorities` category on a transcript that
  already flags it (since the file now carries an added line the
  hook's own `git diff`/`git log -p` check will see).
