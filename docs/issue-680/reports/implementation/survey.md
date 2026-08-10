# Survey — issue #680 (returned-PR spawn gate)

## Scope of change

`spawn.py`'s `main()`/spawn path (`spawn_cmd`, invoked from `spawn`
subcommand around line 3560-3660) is where `--issue N` spawns are
dispatched. A new gate function must run before the actual spawn (fork)
happens, refuse on unresolved returned PRs, and be bypassable with
`--despite-returned`.

## Existing primitives to reuse (no new dependency)

- `_repo_slug(root)` (spawn.py:1063) — `gh repo view --json
  nameWithOwner` for the target repo slug.
- `gh pr list --head <branch> --state open ...` pattern used repeatedly
  (spawn.py:1075-1122, :2486, :4109) — existing convention for reading
  open PRs by branch; for this gate we need **all** open PRs across
  `issue-*/**` branches, so `--state open --json number,headRefName,body`
  without `--head` is the right shape (new call shape, same tool).
- `_pr_comments` (spawn.py ~1150, name confirmed via the docstring at
  1140-1166) returns `(comments, ok)` — the `ok` flag is exactly the
  "did the gh call itself fail" signal issue #680 asks the fail-open/
  fail-closed decision to hinge on. This is the precedent to follow for
  the new gate's gh-failure return shape.
- `_ci._approved_roles_on_issue(root, issue)` (referenced at spawn.py
  :1035, defined in `gates/ci.py`) — the existing phase predicate: an
  `APPROVE issue-<n>/<role>` comment from an approvers.md account means
  phase-2 has started for that issue. Reusable as-is to classify a given
  issue as phase-1-still-open vs phase-2-in-progress, and (combined with
  merge/close state) to decide "dispositioned" per PR.
- `ledger_write(entry: dict)` (spawn.py:3213) — appends to
  `runs/ledger.jsonl`; the override-bypass event required by acceptance
  criteria writes through this, same as other ledger events in the file
  (e.g. spawn_cmd's own entries around :4674).

## Disposition rule (from the issue text)

A PR on an `issue-*/**` branch is **dispositioned** when either:
- it is a phase-1 proposal PR and carries an approval token
  (`APPROVE issue-<n>/<role>` from an approvers.md login) — reuse
  `_ci._approved_roles_on_issue`, OR
- it is a phase-2 delivery PR and has been merged or closed (i.e. is no
  longer `open` in `gh pr list --state open`).

Since `gh pr list --state open` only returns PRs still open, "merged or
closed" is trivially satisfied by absence from that open-PR list — the
gate only needs to inspect currently-open PRs and, for each, run the
phase-1 approval check. An open, unapproved PR is a blocker; an open,
approved PR (phase-1 done, phase-2 presumably in flight) is not a
blocker under this rule since the issue's own acceptance criteria only
lists "no merge/close" as the phase-2 disposition failure — approval is
what phase-1 needs, merge/close is what phase-2 needs, and both are
independently checkable from `gh pr list` + the comment predicate.

## Precedent for the fail-open/fail-closed decision

`contract-guard.sh` (on-the-record/hooks/contract-guard.sh:19-27) already
states and justifies a fail-open rule for a `gh` lookup failure at a
gate point: "a lookup failure here is reported and passed through rather
than blocking an unrelated command... What must never happen is silently
approving [an action] this script positively determined violates the
contract." That script gates `gh pr merge` (expensive, rare, deliberate);
this gate runs on *every* `spawn.py ... --issue N` invocation (frequent,
routine), so blocking every spawn on `gh` flakiness would make spawn.py
itself unusable during any network hiccup — a materially worse
availability cost than contract-guard's single-merge case. This is the
input the proposal's Rationale section decides from.

## Write set implied

- `spawn.py` — new gate function + wiring into the spawn dispatch path +
  `--despite-returned` flag + `positive_int`-style arg registration.
- `test_spawn.py` — `ReturnedPrGate`-prefixed test cases per the issue's
  named `pytest -k` filter, with mocked `gh` output (existing test file
  already mocks `subprocess.run` for `gh` calls elsewhere — pattern to
  follow, not invent).

No new environment variable, no new dependency, no schema/migration —
confirmed by the primitives audit above; nothing beyond `gh` (already a
runtime requirement of spawn.py) is needed.

## Scout skip record

Issue #680 is an internal orchestration/CLI-gating change with no
product-facing surface (no UI, no end-user-visible category to compare
against best-in-class exemplars) — it is infra plumbing inside this
repo's own `spawn.py` tool. The scout directive's second skip condition
("the spec leaves no design decision open") does not fully apply — one
design decision (fail-open vs fail-closed) is explicitly left to phase-1
per the issue text — but that decision is resolved by internal precedent
already in this repository (`contract-guard.sh`'s stated rationale, found
above), not by external market research: there is no comparable
best-in-class external product to scout for "how should a CLI gate its
own spawn action on unprocessed PRs." Scouting is skipped; the fail-open
rationale is instead derived from the survey above.
