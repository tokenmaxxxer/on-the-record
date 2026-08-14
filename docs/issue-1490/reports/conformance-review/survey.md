# Survey — conformance-review, issue #1490

## Scout skip record

Skipped. Skip condition: the spec (issue #1490's Requirements/Acceptance
list) leaves no design decision open for this role — extracting a
requirement list from stated Requirements 1-4 and the Acceptance
checklist is mechanical enumeration, not a direction choice a field
scan could inform.

## Board condition that spawned this session

canonical: `git log --oneline -5` and `gh pr view 1494 --json title,body,mergeCommit,commits`
(this session, see transcript). `issue-1490/implementation` landed
merge commit `befd0778` (PR #1494, merged 2026-08-14, per the PR's
`mergeCommit.oid`).

canonical: `find docs/issue-1490 -type f` (this session) — output
listed only `docs/issue-1490/proposals/parallel-test-suite.md` and
`docs/issue-1490/reports/implementation/survey.md`; no
conformance-review report path existed yet. The board condition for
this spawn (implementation commit landed, no conformance-review record
for that sha) held at session start.

## What actually landed at befd0778

derived: `git show befd0778 --stat`
```
docs/issue-1490/proposals/parallel-test-suite.md | 153 +++++++++++++++++++++++
docs/issue-1490/reports/implementation/survey.md |  98 +++++++++++++++
 2 files changed, 251 insertions(+)
```

canonical: `gh pr view 1494 --json body` (this session) — the PR body
states "Phase-1: survey + proposal for #1490 ... Awaiting approval ...
to proceed to phase-2 build." This is the implementation role's own
phase-1 output, not phase-2 delivery.

No code changed: `pytest.ini`, `conftest.py`, `requirements-dev.txt`,
and every `tests/*.py` file named in the implementation proposal's
`files:` frontmatter are untouched as of this sha.

canonical: this session's direct reads of the working tree —
`Read pytest.ini` shows only `[pytest]` / `python_functions` /
`norecursedirs`, no `addopts`, no `markers =`; `ls requirements-dev.txt`
returned "no such file"; `grep -rn "slow" pytest.ini conftest.py`
returned no match; `grep -c "pytest.mark.slow" tests/*.py` returned no
match in any file.

## Issue #1490 requirement list (extracted verbatim from issue body, `gh issue view 1490`, this session)

1. Parallelize the default run (pytest-xdist `-n auto`); enumerate and
   fix tests sharing mutable state first; document each isolation fix
   in the delivery record.
2. Mark slow lifecycle tests (real subprocess spawn/git clone) with a
   `slow` marker; default run excludes them; `--slow`/`-m slow` tier
   runs them; orchestrator regression policy names which tier is
   required per change class.
3. Default (non-slow, parallel) run target: under 5 minutes (300s) on
   this machine; before/after times to be recorded.
4. No test deleted or weakened — re-tiering and isolation only.

canonical: `gh issue view 1490` (this session) Acceptance section lists
4 checklist items, all rendered as `- [ ]` (unchecked) in that same
command's output:
- `-m "not slow"` parallel run, target <300s, to be measured and recorded.
- Both-tiers run, target test-ID set matching pre-change baseline, to
  be recorded as a diff.
- Per-test isolation fixes to be named in the delivery record.
- provenance/empty-state lines required.

## Status relative to the board's own approval flow

canonical: `gh issue view 1490 --json comments` (this session). The
comment thread shows `JiwonJung94` posted the exact string `APPROVE
issue-1490/implementation`. A later comment from the same watch relay
reports `pr-create-failed` with detail `No commits between main and
issue-1490/implementation`. The most recent comment in that same
`--json comments` output (`session-end: PR ...pull/1494 opened`) names
PR #1494 — the same phase-1-only PR whose merge commit is `befd0778`,
per `gh pr view 1494 --json mergeCommit` (this session) above; the
comment thread carries no reference to any other PR number for this
branch.

## Conclusion for this review

canonical: "What actually landed at befd0778" section above (this
document) — no file changes beyond the phase-1 proposal document exist
on `issue-1490/implementation` as of `befd0778`.

Given that, this session's proposal (see proposal file) is to hold this
role's verdict-writing step open rather than record verdicts against
not-yet-existing build output, and to re-enter this review once a
phase-2 implementation commit lands on the branch.
