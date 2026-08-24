# Deviation log — issue-2208 (conformance-review role)

- 2026-08-25T00:30:00Z | inline | proceeded from phase-1 straight into
  phase-2 in the same session, rather than stopping after the phase-1
  PR for a later session (the role-handoff contract's two-session
  default).
canonical: `gh issue view 2208 --json comments -q '.comments[] | .author.login+": "+.body'`, executed this session — result:
```
JiwonJung94: APPROVE issue-2208/conformance-review
```
Reason for the deviation: this exact comment already existed on the
issue, from an approvers.md-listed account, before this session's own
phase-1 commit landed — the contract's approval boundary was already
satisfied at the moment phase-1 finished, so continuing into phase-2 in
the same turn matched the contract's own approval-boundary rule rather
than departing from it; recorded here because the default expectation
(a separate later session for phase-2) did not hold this time.

- 2026-08-25T00:35:00Z | inline | this session's early writes to
  docs/issue-2208/reports/conformance-review/survey.md were repeatedly
  denied by record-claim-guard.sh before landing clean.
canonical: this session's own tool-call history — result:
```
several record-claim-guard denials (bare-count/canonical/outcome-claim
shape) against a locally-tested draft that had been linted clean against
the wrong copy of the checker — repo-root gates/record_lint.py, a newer
copy with word-sense exemptions the plugin-bundled
on-the-record/gates/record_lint.py (the one the hook actually runs)
lacks
```
What was expected vs. what happened: expected the repo-root
gates/record_lint.py to be the live checker (it is the one importable
via `sys.path.insert(0, 'gates')` from the repo root); the hook actually
resolves on-the-record/gates/record_lint.py first. Fixed by re-testing
drafts against on-the-record/gates/record_lint.py directly before every
write for the rest of the session — recorded as a hunt finding too
(docs/issue-2208/reports/conformance-review/2026-08-25-hunt-conformance-review.md,
after-proposal section) since the version divergence itself is a real
repo-scoping gap, not just a one-off mistake this session made.

- 2026-08-25T15:45:00Z | inline | pushed the branch's one remaining
unpushed commit (958c0a47, already committed by the prior session) and
left two working-tree items uncommitted.
canonical: `git push origin issue-2208/conformance-review`, executed
this session — result: `97b1c90b..958c0a47  issue-2208/conformance-review -> issue-2208/conformance-review`.
canonical: `git status -sb`, executed this session — result:
```
## issue-2208/conformance-review...origin/issue-2208/conformance-review
 M .orchestrate-hook-fires.log
?? .on-the-record/directive/
```
Reason for the deviation: `.orchestrate-hook-fires.log` is repo-root hook
telemetry modified by this session's own hook fires, no docs/issue-2208
content; `.on-the-record/directive/` is untracked local directive-cache
output, the same shape as the already-untracked `.on-the-record/role.json`.
Role-handoff contract v3 scopes this role's writes to
docs/issue-2208/reports/conformance-review.md and explicitly warns
against a blanket `git add -A/.`; neither stray item is docs/issue-2208
content or a deliverable this role owns, so committing them would exceed
write_scope on a guess rather than a call this role's task actually
required.
