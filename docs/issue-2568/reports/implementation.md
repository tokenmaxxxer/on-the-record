---
issue: 2568
role: implementation
author: implementation
loop_state: done
upstream: []
code_under_review:
  - on-the-record/hooks/quality-bar-gate.sh
type: fix
breaking: none
verdict: pass
---

# issue-2568 — implementation record

## What was done

`on-the-record/hooks/quality-bar-gate.sh` no longer derives a record path
from a role name. Previously it looped `BAR_ROLES` (the 7 domain names) and
read `docs/issue-<n>/reports/<role>.md` for each — a file that can never
exist under slug-named records (#2555). It now resolves the PR's branch
(`headRefName`) with `re.match(r"^issue-(\d+)/(.+)$", head_ref)` once, takes
group 2 as `slug`, and reads the single record at
`docs/issue-<n>/reports/<slug>.md` once for the whole PR — canonical:
on-the-record/hooks/quality-bar-gate.sh:224-226,253 (this session's own
edit, read back after applying it). `BAR_ROLES` keeps exactly one job: it
still drives `role_patterns`/`quality_bar.bar_scoped_roles(pr_files,
role_patterns)` to classify which of the 7 quality domains the PR's changed
paths implicate — canonical: on-the-record/hooks/quality-bar-gate.sh:236
(`for role in BAR_ROLES:`, feeding `role_patterns`, never `record_path`).
Build-now bypass (CORE_BUILD_NOW=1) applied — delivered directly on
`issue-2568/implementation` without a phase-1 proposal PR.

skill-verdict: work-in-english — applied: invoked; used for the session's
own commit message/PR body language routing (Korean summary reserved for
the final user-facing message; all repo-bound text in English).

## Why

The gate's purpose (issue #2568 body) needs no role names — only (a) which
quality domains a PR's changed paths implicate and (b) the verdict from the
record the PR's own session actually wrote. Branch-cutting (`spawn.py`'s
`_checkout_named_branch`, called for both legacy role sessions and slug
sessions alike) always names the branch `issue-<n>/<role-or-slug>`, and the
record-skeleton line (`spawn.py:3082`) always writes that identical value
into the record's own filename — so the branch's own second path segment is
already the record's filename stem, with no new role→slug lookup table
needed or introduced. Verified live against this very session: its own
branch is `issue-2568/implementation` and its own record path is this
file's own path (the identical `implementation` segment appears in both) —
derived: `git branch --show-current` — result: `issue-2568/implementation`.

Rejected alternative: keep a fixed glob over every file directly in
`docs/issue-<n>/reports/` (the shape `delegated-judgment-gate.sh`'s
`changed_role_record_paths` already uses: `re.compile(rf"^docs/issue-
{issue}/reports/[^/]+\.md$")`). Rejected because a PR can touch, or leave
in the tree, record files from earlier/unrelated sessions on the same
issue; a PR has exactly one branch and should be judged against exactly the
one record its own session wrote, not "any record file present in the
directory."

## What did not work

None.

## Upstream basis

No phase-1 proposal exists for this delivery — the spawning task carried
CORE_BUILD_NOW=1 (build-now bypass, contract v3 s19a), so the proposal
round was skipped per the standing directive; the issue body itself (`gh
issue view 2568`) is the only upstream input, and there is no prior
docs/issue-2568/ path to cite.

## Open findings

None for this gate. Noted but out of this issue's stated scope: `role`
in `on-the-record/hooks/delegated-judgment-gate.sh`'s own
`role_record_path()` helper still builds `docs/issue-<n>/reports/<role>.md`
the same role-keyed way `quality-bar-gate.sh` used to — the spawning task
named only `quality-bar-gate.sh` and told this session explicitly to leave
`approval-gate.sh`'s `OBSERVER_ROLES` alone; `delegated-judgment-gate.sh`
was not named and is not touched here.

## Acceptance evidence (executed live, scratch fixture outside the repo)

Fixture (all paths below are untracked scratch fixtures outside this
checkout — none are part of this repo's git history): a throwaway git repo
at `/tmp/qbg-verify/fixture-repo` containing an untracked scratch record
`docs/issue-99999/reports/testslug.md` and PR-files entries naming an
untracked scratch stub `src/foo.py` (never created as a real file — only
named in the fake `gh pr view` JSON's `files[].path`), plus a fake `gh` on
`PATH` answering `gh pr view <n> --json files,headRefName,author` from a
canned JSON file. `TOKENMAXXXER_CHECKOUT` pointed at this real checkout, so
`gates/quality_bar.py` and `spawn_roles.json` are the real, unmodified ones
under review; only the PR metadata and the record file are fixtures.

**check 1 — bar-met record permits, scoping shown to have fired first:**
running a debug copy of the gate (identical logic, one added
`sys.stderr.write` of `scoped_roles` right after the `bar_scoped_roles`
call, immediately before the record read — untracked scratch file
`/tmp/qbg-verify/quality-bar-gate.debug.sh`) against untracked fixture PR
#101 (files: untracked stub path `src/foo.py`, `headRefName:
issue-99999/testslug`, fixture record's last `quality_bar_verdict:` line =
`bar-met`) —

acceptance: `bash /tmp/qbg-verify/quality-bar-gate.debug.sh <
/tmp/qbg-verify/payloads/stdin_a.json; echo EXIT:$?` — result:
```
DEBUG scoped_roles=['test-authoring'] issue='99999' slug='testslug'
EXIT:0
```
`scoped_roles=['test-authoring']` (non-empty, matched via `src/**` in
`spawn_roles.json`'s real `test-authoring.record_spec`) proves the domain
scoping ran before the record read; exit 0 with no `hookSpecificOutput`
denial is the permit.

**check 2 — the same PR with a bar-not-met record still denies:** flipped
only the untracked fixture record's `quality_bar_verdict:` line to
`bar-not-met` (new commit in the untracked fixture repo, same file, same
PR/branch/slug) —

acceptance: `bash on-the-record/hooks/quality-bar-gate.sh <
/tmp/qbg-verify/payloads/stdin_a.json; echo EXIT:$?` — result:
```
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "quality-bar-gate: PR #101 has a bar-scoped role that has not met its quality_bar (issue #1156) — test-authoring: BAR_NOT_MET (bar-not-met verdict recorded)"}}
EXIT:2
```

**check 3 — a PR touching those paths whose session wrote no record still
denies:** untracked fixture PR #102 (same untracked stub `src/foo.py`,
`headRefName: issue-99998/noslug` — the untracked path
`docs/issue-99998/reports/noslug.md` was never created anywhere in the
fixture, i.e. absent/untracked by construction) —

acceptance: `bash on-the-record/hooks/quality-bar-gate.sh <
/tmp/qbg-verify/payloads/stdin_c.json; echo EXIT:$?` — result:
```
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "quality-bar-gate: PR #102 has a bar-scoped role that has not met its quality_bar (issue #1156) — test-authoring: BAR_NOT_MET (no bar-met record)"}}
EXIT:2
```
Today's fail-closed posture on an absent record is preserved (not turned
into a pass) while the resolution path changed.

**check 4 (issue body's "empty state" note) — a PR touching none of the
path patterns still exits NO_BAR_SCOPED:** untracked fixture PR #103
(`files: [README.md]`, same `headRefName: issue-99998/noslug`) —

acceptance: `bash on-the-record/hooks/quality-bar-gate.sh <
/tmp/qbg-verify/payloads/stdin_empty.json; echo EXIT:$?` — result:
```
EXIT:0
```
(no stdout — silent permit, same as today's NO_BAR_SCOPED shape.)

**check 5 — `BAR_ROLES`' remaining use is path→domain classification
only, no record path derived from a role name:**

acceptance: `grep -n "BAR_ROLES\|record_path"
on-the-record/hooks/quality-bar-gate.sh` — result:
```
33:# explicit bar-not-met). BAR_ROLES below is used ONLY to classify which
124:BAR_ROLES = [
236:for role in BAR_ROLES:
250:# resolved once here, not per bar-scoped domain. `scoped_roles` (BAR_ROLES
253:record_path = os.path.join(run_cwd, "docs", "issue-%s" % issue, "reports", slug + ".md")
258:if os.path.isfile(record_path):
260:        text = open(record_path, encoding="utf-8", errors="ignore").read()
271:    log = _run(["git", "log", "-1", "--format=%an", "--", record_path], cwd=run_cwd)
```
Line 236 is `BAR_ROLES`' only remaining reachable use (building
`role_patterns` for `bar_scoped_roles`); line 253's `record_path` is built
from `slug` (from `head_ref`), not from `role`/`BAR_ROLES`.

Additionally: `bash -n on-the-record/hooks/quality-bar-gate.sh` — result:
exit 0 (bash syntax valid); the four live runs above (checks 1-4) each
completed by executing the embedded `python3 -c "$GUARD"` body to a normal
exit, which is itself a live syntax/runtime proof of the Python heredoc.

## Next steps

None — issue #2568's four acceptance checks and its empty-state note are
all demonstrated above; `approval-gate.sh`'s `OBSERVER_ROLES` was not
touched, per the issue's explicit non-goal.
