---
status: proposed
files:
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/test_deliverable_guard.py
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - docs/reports/product/priorities.md
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
- A third gate is in play beyond the two named in the issue:
  `runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh`
  (contract v3 s10, R1) refuses any `docs/` write whose first segment
  is not `README.md`, one of six standing buckets (`_assets`,
  `decisions`, `handbooks`, `proposals`, `reports`, `specs`), or a
  `docs/issue-<n>/` tree. `docs/product/` is none of these — it is a
  seventh, unrecognized bucket — so it is refused by board-gate.sh
  before `deliverable-guard.sh`'s exemption is ever reached, regardless
  of what this proposal does to `deliverable-guard.sh`. This finding
  came from the after-proposal hunt (see Open findings below), and
  drove the write-set revision from the original draft (`docs/product/`
  as target) to the one above (`docs/reports/product/` as target).
  `board-gate.sh` lives in a separately-pulled core rulebook
  (`runs/` is gitignored in this repo, confirmed: `.gitignore:1:
  runs/`) — it is not this repo's own source and is out of scope to
  edit from an on-the-record issue branch.
- consult (requirements-engineering, docs/issue-1111/reports/consult-log.md
  entry logged by this session) recommends the PreToolUse-exemption
  path over moving the Stop-side capture definition to GitHub comments,
  medium confidence, reasoning: moving completion evidence to an
  external API (GitHub) introduces network-reliability and near-match
  spoofing risk into a hook that currently only ever reads the local
  working tree. This recommendation is unaffected by the board-gate
  finding — it concerns the `deliverable-guard.sh` vs. `product-capture-
  stopgate.sh` question only, not the target path within docs/.

## Rationale

**Chosen approach (Option A, revised for the board-gate finding):**
extend `deliverable-guard.sh`'s existing exemption list — currently
just `n.endswith("docs/specs/approvers.md")` — with one more
exact-suffix check for the product-capture files, AND retarget
`product-capture-stopgate.sh`'s own write path from the unrecognized
`docs/product/<cat>.md` bucket to `docs/reports/product/<cat>.md` —
nested inside the `reports` bucket board-gate.sh already admits at R1.
Rationale: this is the same hook, the same code shape, and the same
category of justification ("orchestrator scribing") already used for
`approvers.md` on the deliverable-guard side, and it resolves the
board-gate conflict without touching board-gate.sh itself, by landing
inside a bucket board-gate.sh already recognizes — `reports` is
already this repo's home for measurement/log-shaped output, which a
running priorities/requirements/philosophy/goals log is.

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
orchestrator to write a structured product doc on any future turn that
isn't resolved purely by commenting — the deadlock returns the next
time a category needs a real entry in the file itself, not just a
one-off close-out note; and it does nothing about the board-gate
conflict either, since board-gate denies the write regardless of what
Stop-side check would have accepted it.

**Alternative considered and rejected (new `product` bucket in
board-gate.sh):** widen board-gate.sh's own six-bucket tuple to seven,
adding `product`. Rejected because `board-gate.sh` is sourced from a
separately-pulled core rulebook outside this repo's own tree (`runs/`
is gitignored here) — this issue's branch cannot durably carry that
edit, and widening contract v3 s10's bucket list is a decision for
that other project, not a side effect of resolving #1111.

## What will be done

1. `on-the-record/hooks/product-capture-stopgate.sh`: change the two
   `rel` path templates from `docs/issue-{issue_n}/product/{cat}.md` /
   `docs/product/{cat}.md` to `docs/issue-{issue_n}/reports/product/{cat}.md`
   / `docs/reports/product/{cat}.md` — both already inside the
   `reports` bucket board-gate.sh's R1 admits (issue-scoped under
   `docs/issue-<n>/reports/`, non-issue-scoped under `docs/reports/`).
   No other logic in the hook changes — same bootstrap-on-first-flag,
   same git-diff/git-log-p cross-check, same category vocabulary.
2. `on-the-record/hooks/test_product_capture_stopgate.py`: update any
   assertions hard-coding the old `docs/product/...` path to the new
   `docs/reports/product/...` path.
3. `on-the-record/hooks/deliverable-guard.sh`: replace the single
   `n.endswith("docs/specs/approvers.md")` check with a check against a
   small tuple of exempt suffixes:
   `("docs/specs/approvers.md", "docs/reports/product/requirements.md",
   "docs/reports/product/priorities.md",
   "docs/reports/product/philosophy.md", "docs/reports/product/goals.md")`,
   plus the issue-scoped equivalents
   `docs/issue-<n>/reports/product/<cat>.md` via a regex matching
   `product-capture-stopgate.sh`'s own four-category vocabulary
   (`requirements|priorities|philosophy|goals`) under either
   `docs/reports/product/` or `docs/issue-\d+/reports/product/`.
   Comment above the check updated to state the product-capture
   pairing (mirrors the existing approvers.md comment style).
4. `on-the-record/hooks/test_deliverable_guard.py`: add cases —
   orchestrator write to `docs/reports/product/priorities.md` is
   allowed; write to `docs/issue-123/reports/product/priorities.md` is
   allowed on an `issue-123/<role>`-shaped repo; write to an unrelated
   `docs/reports/product/other.md` (not one of the four categories) is
   still denied, so the exemption stays scoped to the stopgate's actual
   vocabulary and does not become a general `docs/reports/product/*`
   bypass, nor a general `docs/reports/*` bypass.
5. `docs/reports/product/priorities.md`: create it (bootstrap header
   matches `product-capture-stopgate.sh`'s own bootstrap shape:
   `# Priorities` + `Append-only, newest entry last.`) and append the
   pending entry — the #745 close-out statement, dated 2026-08-12,
   deprioritized `infrastructure/no-direct-requirement` behind #1110,
   the 7-scenario harness re-measurement, and the user's fresh-session
   E2E test.

## Out of scope

- `gates/test_product_capture_ownership.py` as a literal new file path
  — this repo's existing convention keeps each hook's tests beside the
  hook under `on-the-record/hooks/test_*.py`
  (`test_deliverable_guard.py`, `test_product_capture_stopgate.py`
  already there); the new cases land in those existing files instead of
  a new `gates/`-rooted file, since `gates/` is this repo's separate
  Python package for board gates, not hook tests. The acceptance's
  substance (an orchestrator capture path no PreToolUse gate blocks, on
  which the stopgate's own check passes) is what phase-2 delivers; the
  file location follows existing convention over the issue text's
  literal path.
- Editing `board-gate.sh` or contract v3 s10's bucket list — that lives
  outside this repo (see Constraints and Rationale above).
- Widening `deliverable-guard.sh`'s exemption beyond the four named
  category files.
- The companion consult-regression issue referenced in #1111's body —
  separate issue, not this one (and moot here: the consult call in
  this session succeeded).

## How you'll know it worked

- `python3 on-the-record/hooks/test_deliverable_guard.py` and
  `python3 on-the-record/hooks/test_product_capture_stopgate.py` — all
  cases pass, including the new ones, pasted output in the phase-2
  record.
- A live PreToolUse Write to `docs/reports/product/priorities.md` from
  an orchestrator-shaped payload (no `CLAUDE_ROLE`) exits 0 instead of
  2, and is not separately refused by board-gate.sh (already true by
  construction — `reports` is one of its six admitted buckets).
- `docs/reports/product/priorities.md` exists on the branch with the
  #745 entry appended, and a Stop-time run of
  `product-capture-stopgate.sh` no longer nudges for the `priorities`
  category on a transcript that already flags it (since the file now
  carries an added line the hook's own `git diff`/`git log -p` check
  will see).

## Open findings (after-proposal hunt)

canonical: docs/issue-1111/reports/implementation/hunt-product-capture-ownership.md
The hunt (stance 4, after-proposal) found that `board-gate.sh`
(contract v3 s10, R1) refuses any write under `docs/product/...` as
outside its six standing buckets, independent of and prior to whatever
`deliverable-guard.sh` decides — the original draft's write set
(`docs/product/priorities.md` as the target) would have been refused
by this separate gate even after `deliverable-guard.sh`'s exemption
landed. Resolved in this revision by retargeting both
`product-capture-stopgate.sh`'s write path and
`deliverable-guard.sh`'s exemption to `docs/reports/product/<cat>.md`
— already inside the `reports` bucket board-gate.sh admits — instead
of attempting to widen board-gate.sh itself, which is out of this
repo's own tree.

## Accumulation

This adds one more exempt-path family to `deliverable-guard.sh`'s
existing single-entry exemption list (now: `approvers.md`, plus the
four product-capture categories under `docs/reports/product/` and
`docs/issue-<n>/reports/product/`) and relocates
`product-capture-stopgate.sh`'s write target one directory level
deeper (into the `reports` bucket) with no change to its category
vocabulary or cross-check logic. If a future category needs the same
treatment, it is one more suffix in the same tuple and one more regex
alternative — no new code path. If board-gate.sh's bucket list is
ever widened upstream (a decision for the core rulebook project, not
this one), `docs/reports/product/` still remains valid — it needs no
follow-up here.
