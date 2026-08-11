---
status: approved
files:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - docs/issue-854/reports/implementation/survey.md
  - docs/issue-854/reports/implementation/resolution.md
  - docs/issue-854/proposals/2026-08-12-heredoc-aware-body-extraction.md
---

Note (this session): `docs/issue-854/reports/implementation.md` — the
phase-2 record path — is mechanically blocked by
`on-the-record/hooks/approval-gate.sh` (`CLAUDE_ROLE=implementation`,
branch `issue-854/implementation`, no `APPROVE issue-854/implementation`
comment on the issue yet). `approval-gate.sh`'s own scope is exactly the
role's record file plus `src/`/`test(s)/` paths — it does not gate
`on-the-record/hooks/*.sh` or its tests — so this session's actual fix is
committed in the same PR; the write-up that would otherwise live in
`implementation.md` lives at
`docs/issue-854/reports/implementation/resolution.md` instead, a
phase-1-legal path, matching the precedent issue #876's own PR (`664be7d`)
set for this exact situation. This PR's body carries a plain `#854`
reference, no `Closes`.

# Proposal — issue #854, implementation

## Request

Issue #854: `pr-preflight.sh`'s phase-1 closing-keyword refusal (issue
#741 round 2) never fired for PR #844, letting it auto-close issue #839 on
merge before phase-2 code landed. Reproduce the failure with the actual
command shapes the incidents used (not static reasoning), find the real
cause, judge whether `gh`-lookup fail-open should stay for this check, and
leave a regression test behind for whatever failure shape is confirmed.

## Constraints

- Reproduce first — the issue explicitly forbids concluding from static
  reasoning alone.
- Write set: `on-the-record/hooks/pr-preflight.sh`, its test file, and
  `docs/issue-854/` only. `gate-registration-guard.sh`,
  `role-axis-completeness-guard.sh`, and `spec-index-preflight.sh` are
  owned by a concurrent session and must not be touched.
- Verification: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
  on the branch and on `origin/main`, failure-set diff pasted into the
  record.
- This PR's body carries a plain `#854` reference only — no
  `Closes`/`Fixes`/`Resolves`.

## Rationale

Considered treating "phase misjudged as phase2" (the issue's first "남은
후보") as the live hypothesis and fixing the phase-determination logic.
Rejected: the survey's Finding 1 shows neither incident's `Closes` text
ever passed through a `gh pr create`/`edit` Bash-tool call at all — the
human account edited each PR's body directly (GraphQL `userContentEdits`
attributes both edits to `jjongkwann`, not a role session's login, seconds
before each PR's own human-initiated merge) and no session log anywhere
under `/Users/jk/.tokenmaxxxer/work/` shows a `gh pr edit` call for either
PR. Phase determination is never reached when the hook is never invoked in
the first place; "fixing" it would not have changed either incident's
outcome.

Considered treating `gh`-lookup fail-open as the cause and hardening it
(fail-closed on lookup failure, or caching the last-known phase).
Rejected on the same evidence: the one real `gh pr create` call that did
run in-session (issue-839, session log line 529) completed cleanly with a
correct `exit 0`, meaning its own `gh issue view` call inside the hook
succeeded — there is no observed `gh` failure anywhere near either
incident to harden against. Changing this policy would trade a real,
narrow, already-mitigated risk (a transient `gh` outage silently passing
one PR-body check) for a broad one (fail-closed blocks *every* `gh pr
create`/`edit` call session-wide on any `gh` hiccup, including in
unrelated repos/branches) to fix a cause that reproduction ruled out.
Fail-open stays as-is for this check.

Considered stopping at Finding 1 and reporting "no fix possible — the
incident happened outside the hook's reach, closing this issue as
won't-fix". Rejected: reproducing with PR #844's actual body (not the
issue's own short reconstructed test string) surfaced a second, real,
independently-reproducible defect (Finding 2) in the same code path — the
naive quote-balance `--body` regex truncates at the first literal `"`
inside a heredoc body, which is the dominant real-world `gh pr create
--body "$(cat <<'EOF' ...)"` shape used by every session sampled. Leaving
this unfixed would mean a *future* in-session `gh pr edit`/`create` call
carrying this exact shape still bypasses the phase-1 refusal, even though
it is a case the hook is supposed to (and structurally can) catch. Fixing
it is in scope for this issue's own investigation, not a widening of it.

## Accumulation

`pr-preflight.sh` already inline-ports several checks (`check_body`,
`_plan_from_body`, the phase-1 closing-keyword refusal) rather than
importing `gates/pr_reference.py`/`gates/flows.py`, for the same
no-guaranteed-checkout reason `docs/issue-876/proposals/2026-08-11-port-shlex-trigger-fix-to-sibling-guards.md`
recorded for its own family of hooks. This change adds one more
inline-ported regex (the heredoc-aware `--body` matcher) to that same
file, alongside the existing quote-balance fallback — not a new
occurrence of a check duplicated *across* files, since `pr-preflight.sh`
is the only hook that ever parses a `--body` argument off a `gh pr`
command line (`contract-guard.sh` reads an existing PR via `gh pr view`
instead, per this file's own header comment). If a second hook ever needs
the same heredoc-aware extraction, the shared-helper question gets the
same treatment issue #876 gave the `git commit` trigger check: judged and
decided with evidence in that hook's own proposal, not defaulted into a
shared module, because `hooks.json` invokes every hook via
`${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh` with no guaranteed consumer-repo
`gates/` checkout at invocation time. A third or later occurrence, or any
growth in this snippet's own size past what one hook-header comment can
explain, is the signal to revisit — not a reason to extract one now for a
single call site.

## What will be done

1. Replace the naive quote-balance `--body` extraction with a heredoc-aware
   match tried first (`--body "$(cat <<'EOF' ...\nEOF\n)"`, capturing the
   heredoc content directly via its own delimiter lines), falling back to
   the existing quote-balance regex for non-heredoc `--body "literal"` /
   `--body 'literal'` forms. `--body-file` is unaffected (already reads a
   literal path).
2. Add regression tests to `on-the-record/hooks/test_pr_preflight.py`
   driving the real hook end-to-end: PR #844's actual `gh pr create`
   command (byte-for-byte from the session log) must still pass with no
   closing keyword present; the same real body turned into a `gh pr edit
   844` call with `Closes #839` appended after its existing embedded quote
   must now be denied; plus two minimal synthetic cases pinning the same
   defect class independent of issue #839's specifics.
3. Run the new and existing `on-the-record/hooks/test_pr_preflight.py`
   cases, then `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
   in two isolated `git worktree` checkouts (this branch's tip,
   `origin/main`) and diff the failure sets.
4. Dispatch one before-landing `warrant:warrant-hunter`, wait for and
   consume its result in this same turn (contract v3 s22 — headless
   single-shot).
5. Write `docs/issue-854/reports/implementation/resolution.md` recording
   the fix, the fail-open judgment, the hunt, and the verification
   transcripts.

## Out of scope

- Any general shell-parsing rewrite of `--body` extraction — the fix is
  scoped to the one real-world idiom (heredoc-wrapped `$(cat <<'EOF' ...
  )")`) every sampled command actually uses, matching this file's existing
  inline-port convention rather than introducing a new general design.
- Defending against a PR-body edit made directly on github.com's web UI,
  or any `gh`/API call run outside a hooked Claude Code session — a local
  `PreToolUse` hook has no mechanism to observe either, and #460/#741
  already settled that server-side (GitHub Actions) enforcement for this
  repo's checks was retired, not reinstated.
- `gates/ci.py::_phase1_mismatch` — frozen per the issue.
- Auto-reverting a prematurely closed issue — the issue's own scope line.
- `retry-loop-bound.sh` / `impact-guard.sh` — the issue's own scope line.
- `gate-registration-guard.sh`, `role-axis-completeness-guard.sh`,
  `spec-index-preflight.sh` — owned by a concurrent session.

## How you'll know it worked

- A test built from PR #844's real `gh pr create --body "$(cat <<'EOF'
  ... EOF)"` payload, with `Closes #839` appended after the body's own
  embedded quote, asserts `exit 2` from the live hook on a phase-1
  (no-approval) branch.
- The same real payload, unmodified (no closing keyword), still asserts
  `exit 0`.
- `python3 -m pytest on-the-record/hooks/ -q` passes in full, including
  the new cases.
- The branch-vs-`origin/main` worktree comparison of
  `gates/ tests/ on-the-record/hooks/` shows the branch's failure set is
  empty and not a superset of `origin/main`'s, with no failure introduced.
