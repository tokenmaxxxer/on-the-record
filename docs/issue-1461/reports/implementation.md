---
code_under_review:
  - on-the-record/hooks/pr-base-guard.sh
  - on-the-record/hooks/hooks.json
  - tests/test_pr_base_guard.py
  - on-the-record/hooks/test_pr_base_guard_hook.py
  - docs/specs/generated-paths.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/acceptance-commands.md
  - docs/specs/reconciled-index.md
type: feature
breaking: false
# canonical: acceptance: `python3 -m pytest tests/test_pr_base_guard.py -v` — result: PASS
verdict: pass
loop_state: landed
---

## What was done

Added `on-the-record/hooks/pr-base-guard.sh`, a `PreToolUse`+`Bash` hook
joining `pr-preflight.sh`'s matcher group on `gh pr create` / REST `gh api
.../pulls` create calls. It extracts `--base` (or REST `base=`), resolves
the repo's default branch via `gh repo view --json defaultBranchRef`, and
refuses (exit 2) a role-workspace PR create whose `--base` differs from
the default branch, unless the subject issue's body explicitly names that
base (a `base ... <value>` pattern within 40 chars).

canonical: on-the-record/hooks/pr-base-guard.sh:118-127

```python
default_branch = gh_text("repo", "view", "--json", "defaultBranchRef",
                          "-q", ".defaultBranchRef.name")
if not default_branch:
    deny(
        f"repo 기본 브랜치를 확인할 수 없다 — '{base}'를(을) --base로 쓰는 "
        f"PR 생성을 안전하게 검증할 수 없어 거부한다(fail-closed).",
        "`gh repo view --json defaultBranchRef`가 성공해야 한다",
    )
```

When the default-branch lookup itself fails, the code path above refuses
the commit rather than letting a non-default base through unverified —
the one deliberate exit-2 path on a lookup error in an otherwise
permissive matcher group, per requirement 3.

Registered in `hooks.json` alongside `pr-preflight.sh`; registered in
`docs/specs/generated-paths.md` (n/a row — reads/validates only, no write
call) and `docs/specs/enforcement-boundary.md` (contract row);
`docs/specs/acceptance-commands.md` records this delivery's acceptance
command; `docs/specs/reconciled-index.md` regenerated via `python3
gates/spec_index.py --update` in the same commit.

canonical: on-the-record/hooks/hooks.json (commit 201889d8, `git show 201889d8 --stat`)

Two test files were added per this repo's live-fire-test-guard
requirement: `tests/test_pr_base_guard.py` at the Acceptance-named path,
and `on-the-record/hooks/test_pr_base_guard_hook.py` (identical cases,
`HOOKS_DIR`-relative) since `live-fire-test-guard.sh` requires the
co-located slug path for a newly-staged `on-the-record/hooks/*.sh` module.
Both drive the real hook end-to-end via subprocess+stdin against a stub
`gh`, matching `on-the-record/hooks/test_pr_preflight.py`'s existing
pattern.

## Investigation note (root cause, Acceptance requirement)

canonical: `~/.tokenmaxxxer/work/on-the-record-issue-1202-execution-observation.watcher.log` line 14

```
14:[watch] [session pid=2100078 ts=1786685664.444088] progress: {'kind': 'tool_use', 'detail': 'gh pr create --base issue-247/conformance-review --head issu 실행'}
```

canonical: `~/.tokenmaxxxer/work/on-the-record-issue-1202-execution-observation.session.20260814T152156.369.log` line 20 (session transcript, `tool_use` Bash entry, a respawn of the same role ~41 minutes before the create above)

```
git status && echo --- && git log --oneline main..HEAD 2>&1 | head; git log --oneline issue-247/conformance-review..HEAD; echo --- ; gh pr list --head issue-1202/execution-observation --state all 2>&1
```

canonical: `~/.tokenmaxxxer/work/on-the-record-issue-1202-execution-observation.session.20260814T143531.2100075.log` line 25 (an earlier respawn of the same role, same pattern)

```
git log --oneline origin/issue-247/conformance-review..HEAD 2>&1 | head; echo ---; git ls-remote --heads origin issue-1202/execution-observation
```

derived: `grep -rn "pr create" spawn.py gates/ on-the-record/` (repo root)

```
$ grep -rn "pr create" spawn.py gates/ on-the-record/
(no output — the command produced zero matches)
```

No script in `spawn.py`/`gates/`/`on-the-record/` constructs or suggests a
`--base` value for a role session — the grep above (zero matches) rules
out a stale-state read from any orchestrator-provided value. Across two
respawned sessions of the same issue-1202/execution-observation role (the
15:21 and 14:35 session logs cited above), the model repeatedly ran `git
log ... issue-247/conformance-review..HEAD` as an ad-hoc "what's new
since that branch" diff check — `issue-247/conformance-review` is a
comparison ref the model itself chose to eyeball its own progress
against, not a value read from a board, roster, or config file (no such
lookup precedes it in either log). Roughly 40 minutes later, in the
actual `gh pr create` call the watcher log captured (line 14 above), the
same branch name that had been sitting in the model's own conversation
context as a comparison target got reused as `--base` instead of the
repo's real default branch. This is consistent with unconstrained model
choice via in-session context bleed, not a stale-state read from tooling
— the defect this delivery closes is the absence of authoring-time
enforcement, not a wrong value computed anywhere.

## Why

Issue #1461: a role session issuing `gh pr create --base <another issue's
role branch>` risks silently merging a verification record into an
unrelated branch, corrupting it and hiding the record from `main`. The
create in the observed incident hit a rate limit before landing; this
gate makes the class of mistake refused at authoring time regardless of
luck.

## Upstream

basis: #1461 (`gh issue view 1461`, operator-lifted hold + `APPROVE
issue-1461/implementation` comment, 2026-08-14)

## What did not work

None.

## Acceptance verification

canonical: acceptance: `python3 -m pytest tests/test_pr_base_guard.py -v` — result: PASS
acceptance: `python3 -m pytest tests/test_pr_base_guard.py -v` — result: PASS

```
tests/test_pr_base_guard.py::test_rejects_nonmain_base PASSED
tests/test_pr_base_guard.py::test_allows_default_base PASSED
tests/test_pr_base_guard.py::test_allows_no_base_flag PASSED
tests/test_pr_base_guard.py::test_fail_closed_on_unknown_default PASSED
tests/test_pr_base_guard.py::test_allows_alternate_base_named_in_issue_body PASSED
tests/test_pr_base_guard.py::test_rejects_rest_pulls_create_nonmain_base PASSED
tests/test_pr_base_guard.py::test_ignores_non_role_workspace_branch PASSED
7 passed in 0.54s
```

live-fire: `on-the-record/hooks/pr-base-guard.sh` — result: allow

The three Acceptance-named tests (`test_rejects_nonmain_base`,
`test_allows_default_base`, `test_fail_closed_on_unknown_default`) are
all included in the pasted output above, alongside four supporting cases.

## Open findings

None.

## Doc-placement ladder

- [x] `docs/specs/generated-paths.md` — new hook row (n/a classification)
- [x] `docs/specs/enforcement-boundary.md` — new hook contract row
- [x] `docs/specs/acceptance-commands.md` — acceptance command registered
- [x] `docs/specs/reconciled-index.md` — regenerated via `gates/spec_index.py --update`
- [x] `docs/issue-1461/proposals/2026-08-14-pr-base-guard.md` — phase-1 proposal (approved, `## Accumulation` filled)
