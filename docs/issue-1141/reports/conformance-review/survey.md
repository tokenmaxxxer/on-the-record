# Phase-1 survey: conformance review of issue-1141's implementation (PR #1152)

kind: survey

## Board condition

canonical: `gh pr view 1152 --json mergeCommit,baseRefName` and `find
docs -path "*reports/conformance-review.md"`, run this session — PR
#1152 (branch `issue-1141/implementation`) merged to `main` at commit
52f44f462a2cb24ce3b4401d34789cf0ea097a76; the find output lists no
issue-1141 entry. Per the marketplace conformance-review role spec's
board condition (issue-521), this satisfies the spawn condition.

## Target artifact and spec

- Spec: issue #1141 body (`gh issue view 1141`, read this session).
- Artifact under review: spawn.py (`_consult_cmd_and_env` +
  `consult_cmd()`), gates/test_consult_gate_lib_env.py,
  docs/issue-1141/reports/implementation.md.

## Requirement list (extracted verbatim from issue #1141 body)

derived: `gh issue view 1141`, run this session — `## Requirements`
section body:
```
1. Fix the generator: the rulebook/core checkout that consult sessions
   receive must include (or terse.sh must resolve) lib/gate-lib.sh —
   root-cause whether the core clone omits the lib directory, the path
   anchor is wrong for the runs/rulebooks layout, or the fetch is
   shallow/sparse.
2. A hook that cannot source its own lib must not hard-block the
   prompt with a bash error (fail-open or loud-skip for
   non-PreToolUse-gate hooks, per the gates-fail-closed scope decision
   which limited fail-closed to PreToolUse gates only).
3. Regression: a gate test asserting a consult completes in an
   environment shaped like runs/rulebooks (hermetic fixture).
```

## Acceptance checks

derived: `gh issue view 1141`, run this session — `## Acceptance`
section body:
```
- check: gates test spawning a consult against a fixture
  runs/rulebooks layout returns a verdict (or a loud skip), exits 0
  empty state: environments without a rulebooks checkout keep today's
  behavior
  provenance: executed-unit
- check: live re-run of the exact failed question from the raw file
  returns a verdict; trace line shows ok
  provenance: executed-live (at phase-2 delivery)
```

## Requirement-list completeness

Both fenced blocks above are the full, verbatim section bodies pasted
from the `gh issue view 1141` output cited above — nothing added or
dropped.
