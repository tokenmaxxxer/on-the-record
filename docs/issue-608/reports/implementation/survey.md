# Issue #608 step 2 — current-state survey (implementation)

## Scope

Subject: issue-608, role implementation, step 2 (fix). Step 1
(`docs/issue-608/reports/execution-observation/fixture-measurement.md`,
PR #616, merged) confirmed Findings 1-2 against the unmodified
`on-the-record/hooks/` surface: no `PreToolUse` hook on `Write`/`Edit`/
`MultiEdit` ever checks phase-2 approval for a role session, and
`deliverable-guard.sh` fails open (silent allow) when `approvers.md` is
absent, for the one session type (orchestrator) it does check.

## Write set this step will touch

- on-the-record/hooks/approval-gate.sh (new file) — new `PreToolUse`
  hook, the missing enforcement step 1 recommended.
- on-the-record/hooks/test_approval_gate.py (new file) — pytest
  fixture-driven matrix (approvers present/absent x approved/unapproved),
  red before the fix exists, green after.
- `on-the-record/hooks/hooks.json` — wires the new hook into `PreToolUse`.
- `docs/specs/enforcement-boundary.md` — new row for the new hook (see
  above) under `on-the-record/hooks/*.sh (plugin-shipped)`, required by
  `gates/test_boundary.py`'s completeness check (confirmed live below).
- docs/issue-608/reports/implementation.md (new file, this role's own
  record) — phase-2 output, written once phase-2 opens.

No other file needs to move: the fix is additive (one new hook script,
its test, one `hooks.json` entry, one spec row) — nothing in the existing
seven hooks needs editing, since none of them currently touch
`Write`/`Edit`/`MultiEdit` approval checking at all (step 1, Finding 2).

## Existing patterns to reuse (not reinvent)

Read in full: `on-the-record/hooks/pr-preflight.sh` (210 lines) and
`on-the-record/hooks/deliverable-guard.sh` (87 lines).

- **Branch -> issue/role resolution**: `pr-preflight.sh:74-87` already
  parses `issue-(\d+)/([\w-]+)` off `git rev-parse --abbrev-ref HEAD`.
  Same regex, same source of truth (branch name), reusable verbatim.
- **`approvers.md` membership + `APPROVE issue-<n>/<role>` comment
  check**: `pr-preflight.sh:90-120` already reads
  `docs/specs/approvers.md` (one `- <login>` per line) and calls
  `gh issue view <n> --json comments` to test both approval paths named
  in the role-handoff contract: a PR-review Approve (two-account mode,
  not visible to a `PreToolUse` hook — no PR exists yet mid-session) and
  the exact-string `APPROVE issue-<n>/<role>` issue comment
  (single-account mode, the only one an issue-comment lookup can see).
  `contract-guard.sh` independently reimplements the same
  membership+comment check for `gh pr merge`. approval-gate.sh is the
  third caller of this same shape — porting it inline again (each
  existing hook already does; no shared helper module exists to import,
  since these ship as standalone zero-install scripts) matches the
  established pattern rather than introducing a new one.
- **`root is None or not os.path.isfile(approvers_path)` fail-open
  branch**: `deliverable-guard.sh:74-75` is exactly the branch step 1's
  Finding 1 flagged as wrong (silent allow instead of
  refuse-and-instruct). approval-gate.sh must not repeat this branch's
  shape for the absent-approvers case — bootstrap-offer instead of
  silent exit 0, per the issue's explicit acceptance line.
- **Deny-message and payload-parse shape**: both existing hooks share a
  `deny(msg)` helper writing to stderr and exiting 2, and a
  `try: json.loads(...) except ValueError` guard around the stdin
  payload. approval-gate.sh follows the same shape for consistency with
  the rest of the plugin's hook surface (a session reading any hook's
  denial message sees the same voice).

## What "phase-2 shaped write" means, concretely

Per role-handoff contract v3 s19 (session directive, confirmed against
`docs/specs/*` — no separate spec file states this beyond the directive
text already loaded into every role session): a role session's phase-2
writes are (a) `src/**` and `test/**` (or `tests/**`, matching
`deliverable-guard.sh`'s existing tree regex) paths under the acting
issue, and (b) the role's own record file at
docs/issue-<n>/reports/<role>.md (not the phase-1-legal
docs/issue-<n>/reports/<role>/*.md subdirectory used for surveys, nor
docs/issue-<n>/proposals/*.md). A write to any other docs/issue-<n>/
path (proposals, reports/<role>/ scout/survey files, decisions,
handbooks) is phase-1-legal regardless of approval state and must not be
blocked — blocking those would break the phase-1 flow this same fix is
supposed to protect, including this very survey/proposal pair.

## `docs/specs/enforcement-boundary.md` completeness check

Confirmed live: `gates/test_boundary.py` enumerates every
`on-the-record/hooks/*.sh` file and fails if one has no row in
`docs/specs/enforcement-boundary.md`. A new hook script with no matching
row will fail this check — the boundary-spec row is not optional polish,
it is required for the hooks-directory test suite to pass, confirming
the issue's "boundary-spec row in the same unit" requirement is
load-bearing, not just an issue-body preference.

```
$ grep -n "def test_" gates/test_boundary.py | head -5
```
(module enumerates `on-the-record/hooks/*.sh` against the spec table;
read directly, not re-pasted here — the file itself is the source of
truth for the exact assertion shape.)

## Alternative considered

**Extend `deliverable-guard.sh` in place** instead of adding a new
script: rejected. `deliverable-guard.sh` is orchestrator-scoped by
design (`[ -z "${CLAUDE_ROLE:-}" ] || { exit 0; }` at line 23 — it
explicitly no-ops for role sessions) and its existing test suite and
`docs/specs/enforcement-boundary.md` row describe that exact scope
("blocks orchestrator-authored deliverables"). Folding role-scoped
approval checking into it would invert its documented contract and
force every future reader of that file to hold two unrelated concerns
(orchestrator-authorship blocking vs. role-approval blocking) in one
script. A second, role-scoped hook keeps each script's blast radius
matching its one stated job — the same shape `pr-preflight.sh` already
chose over extending `contract-guard.sh` for a related-but-distinct
`gh pr` sub-check.
