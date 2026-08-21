# Survey — issue #1821 (frozen migration order entry 5: approval-gate.sh)

## Current state of `on-the-record/hooks/approval-gate.sh`

canonical: `on-the-record/hooks/approval-gate.sh` (this branch, read live).

The hook already carries a *partial* dual-read from #1814:

- **Role**: prefers `.on-the-record/role.json` sidecar (`{"role":...,
  "issue":...}`) when present; falls back to the branch regex
  `^issue-(\d+)/([\w-]+)$` only when the sidecar is absent, unparseable,
  or missing the right keys (canonical:
  `on-the-record/hooks/approval-gate.sh`, section under the comment
  "subject issue number + role"). **When the sidecar resolves, the
  branch regex is never run at all** — the code path is `if issue is
  None: <parse branch>`, so sidecar-present short-circuits the branch
  parse entirely and there is no comparison between sidecar role and
  branch-parsed role today (canonical: same file, same section — there
  is only one `if issue is None:` guard and no `else` branch computing
  a branch-derived role for comparison). This is the gap requirement 2
  (mismatch fail-closed) needs to close: only one of the two values is
  ever computed on the sidecar-present path, so nothing exists yet to
  compare.
- **Approvals**: always does its own independent `gh issue view --json
  comments` call, then an exact-string needle scan (`APPROVE
  issue-%d/%s`) against `docs/specs/approvers.md`-listed logins, plus
  the issue #707 delegation-citation extension (canonical: same file,
  the `gh_json`/`needle`/`_delegation_valid` block). It does **not**
  read the #1818 structured approval record
  (`.git/gh-read-cache/issue-<n>-approvals.json`) anywhere in the file
  (canonical: same file — no reference to `gh-read-cache` or
  `_approval_record_path` appears in it) — this is the gap requirement
  1's approvals half needs to close.

## The #1814 sidecar (role carrier)

canonical: `spawn.py:7626-7639` (`_write_role_sidecar`), `spawn.py:7642`
(`issue_workspace` call site).

Written once, at workspace-spawn time, to `.on-the-record/role.json` at
the workspace root: `{"role": <str>, "issue": <int>}`. Fail-open by
design (write failure just means the sidecar is absent; consumers fall
back to branch regex). `approval-gate.sh` already reads this file at
`os.path.join(cwd, ".on-the-record", "role.json")` where `cwd` comes
from the PreToolUse payload's `cwd` field (falling back to
`os.getcwd()`). Two other hooks (`pr-preflight.sh`, `contract-guard.sh`)
read the identical sidecar shape — canonical:
`test/test_convention_equivalence.py:403-408`
(`BranchRoleFieldDualReadEquivalenceTest.test_hooks_read_role_json_sidecar_before_falling_back`),
which asserts all three hooks' source contains `.on-the-record` and
`role.json`.

## The #1818 structured approval record (approvals carrier)

canonical: `gates/ci.py:189-224` (`_read_approval_record`,
`_write_approval_record`, `_approved_roles_on_issue`); `spawn.py:1334-1339`
(`_approval_record_path`).

Path: `.git/gh-read-cache/issue-<n>-approvals.json`, a JSON object keyed
by role token: `{"<role>": {"actor": "<login>", "timestamp":
"<iso8601>"}}`. It is a write-through cache of the comment scan, not an
independent grant — canonical: `gates/ci.py:220-225`, the inline
docstring stating the record's role set is unioned with the comment
scan and the comment scan always still runs regardless of record
content. Only `gates/ci.py` reads/writes it today — `approval-gate.sh`
is a second, independent Python consumer (a standalone script embedded
in the shell hook via heredoc, not an importer of `gates.ci`) that has
never touched this file (canonical: grep of `gh-read-cache` across
`on-the-record/hooks/approval-gate.sh`, no match, this session).

Because the record is a cache of the comment scan itself (canonical:
`gates/ci.py:220-225`, cited above), a record hit for role `R` implies a
past comment scan found the matching APPROVE needle from an
approvers.md login — reading `record.get(role)` truthy is a strict
subset check of what `approval-gate.sh`'s own needle scan already
computes, never a broader/weaker one.

## Dependency / ordering facts

- canonical: `docs/issue-1792/reports/implementation.md:100-115`
  (§Migration order) — entry 5 is `approval-gate.sh`; entries 1-4 (board
  records, watch/roster, branch names via #1814, APPROVE grammar via
  #1818) are landed prerequisites. Entry 6 (rsb `_pr_approved`/`flows.py`)
  and the final-removal sub-issue (drop the regex/needle bodies) are
  both explicitly out of scope here (canonical: issue #1821 body,
  "Non-goals" list, `gh issue view 1821` this session).
- derived: `python3 -m pytest test/test_convention_equivalence.py -q`
  (this session), fenced output below:

```
$ python3 -m pytest test/test_convention_equivalence.py -q
bringing up nodes...
bringing up nodes...

................................                                        [100%]
32 passed in 0.86s
```

  including the existing `ApprovalGateEquivalenceTest` (canonical:
  `test/test_convention_equivalence.py:201-216`, this branch), which
  asserts hook file shape: fallback regex string, needle format string,
  delegation regex, and the `if role != branch_role:` branch-role fail-
  open line (canonical: `on-the-record/hooks/approval-gate.sh`, the
  line `if role != branch_role:` — reached only on the branch-regex
  path, where both values come from the same branch string, since
  sidecar-present never runs that comparison today per the "Current
  state" section above). #1821 requirement 2's new fail-closed
  behavior is a *different* comparison (sidecar role vs. branch-parsed
  role, only meaningful when both independently resolve), so the
  existing assertion's target line is untouched and the new behavior
  needs a new, additional assertion — additions-only.
- No test file covering live-fire approval-gate carrier combinations
  exists yet — canonical: `find test -iname '*approval*' -o -iname
  '*gate*'` this session returned only `test/test_approval_role_field.py`
  and `test/test_auto_approval_shadow_wiring.py`. The new carrier test
  file named in the issue's acceptance §2 (test_approval_gate_carriers.py,
  under test/) is planned phase-2 output; it does not exist in the
  working tree today.
- `docs/specs/approvers.md` (this workspace) lists two logins,
  canonical: `docs/specs/approvers.md`, this session's read
  (`JiwonJung94`, `jjongkwann`) — the existing hook membership check
  reads this file already; unaffected by this change.

## What must NOT change (trust-critical, per issue body)

- Enforcement semantics (what is blocked/allowed) stay identical; only
  the *source* of `{role, approvals}` data changes.
- Fallback must engage on ANY carrier anomaly — missing, unparseable, or
  (new) a resolved role-mismatch between sidecar and branch parse.
- A carrier substituting data must never let through something the
  scan-only path would refuse, nor refuse something the scan-only path
  would allow — except the one deliberate hardening the issue itself
  authorizes: sidecar-vs-branch mismatch becomes a hard refuse where
  today it silently falls through to "not this hook's target" (fail
  open, `sys.exit(0)`, not even a deny).

## Skip-condition check

Scouting (best-in-class-approval-gate-hook research) does not apply:
this is a mechanical migration of an already-frozen design (the
dual-read + mismatch-fail-closed shape is prescribed by the issue body
itself, entry 5 of a frozen migration order, consuming carriers exactly
as built by #1814/#1818 with "no new carrier" stated explicitly in the
issue). No open design decision remains for external scouting to
inform — this is the `assumptions-skip: mechanical` case the issue
itself declares.
