# `design-artifacts:` declaration contract (issue #2013)

Companion to the #2012 design-bearing classifier: that classifier proposes
a default artifact set for a design-bearing issue, it does not enforce it.
This contract is what an issue body's `design-artifacts:` line means to
the enforcement gate — `gates/design_artifacts_gate.py`, ported inline
into `on-the-record/hooks/pr-preflight.sh`'s `gh pr create` intercept.

## Syntax

A `design-artifacts:` tag line on its own (optionally with a leading `-`
or `*` bullet marker, matching this repo's other closed-vocabulary tags),
followed immediately (blank lines allowed) by either:

- a bulleted list, one repo-relative path per line:

  ```
  design-artifacts:
  - docs/issue-2013/design/user-scenarios.md
  - docs/issue-2013/design/flow-diagram.md
  ```

- or a fenced block, one repo-relative path per line, no bullet prefix:

  ````
  design-artifacts:
  ```
  docs/issue-2013/design/user-scenarios.md
  docs/issue-2013/design/flow-diagram.md
  ```
  ````

No `design-artifacts:` tag anywhere in the body → the gate is byte-inert:
no fetch beyond what phase determination already does, no check, no
refusal. This is the default for a mechanical issue.

## Default artifact set (informational)

For a design-bearing issue with no more specific author judgment, the
#2012 classifier's own docstring/#2013's text names the minimum set: at
least one user-scenario document and one structural artifact
(information architecture, flow diagram, or storyboard) under
`docs/issue-<n>/design/`, plus an HTML demo file for UI-facing
deliverables. This document does not enforce that default — it is
documentation of shape for an author declaring the tag, not logic; the
gate checks only whatever paths a given issue actually declares.

## What the gate checks

Existence only, never content: each declared path is checked against the
current working tree at `gh pr create` time. Missing paths are named
explicitly in the refusal message. A declared path that exists — however
thin its content — passes; judging whether a produced artifact is good
(a real user scenario vs. a placeholder line) is explicitly out of this
gate's scope (docs/issue-2013/proposals/design-artifact-existence-gate.md
"Out of scope").

## Failure mode on infrastructure trouble

If the issue body itself cannot be fetched (`gh` missing, network
failure, non-2xx API response), the gate fails **closed**: it refuses PR
creation with an actionable message rather than silently passing, per the
issue-2013 approval-comment amendment (2026-08-22) to the original
proposal's fail-open constraint. This is a narrower posture than the rest
of `pr-preflight.sh`'s fail-open house style — scoped to this one lookup.
