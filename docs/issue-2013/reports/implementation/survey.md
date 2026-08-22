---
subject: issue-2013
kind: survey
---

# Survey — issue #2013: design-artifact existence core gate (artifact-gate phase 2)

## Scope surveyed

`on-the-record/hooks/`, `gates/`, `spawn.py`, `tests/`, `test/`, `docs/` — the
write set the issue names.

## Upstream: the classifier (#2012, PR #2018, merged)

canonical: read gates/design_bearing_classifier.py in full this session.

`gates/design_bearing_classifier.py` exposes a `check_issue_body(issue,
body)` function returning `{design_bearing, evidence, override}`. It scores
keyword overlap against a fixed vocabulary (threshold 3) and honors a
closed-vocabulary `design-bearing-override: yes|no` body tag. Its own
docstring states it produces a design-bearing verdict only; issue #2013's
own text states separately that "the classifier only proposes the default
set" while "the required artifact set is declared per issue in the issue
body (a `design-artifacts:` line)."

canonical: `grep -rn "design-artifacts" --include=*.py --include=*.md --include=*.sh .` run this session, zero matches.

No `design-artifacts:` tag, parser, or default-set proposer exists in the
repo yet — #2013 introduces this contract, it does not wire an existing one.

## The proposal-shape-gate pattern named by the issue as the model

canonical: read gates/design_research_consult.py in full this session; the
sibling `proposal-shape-gate.sh` is quoted directly in this session's own
`<proposal-shape-directive>` system context (its section list/order),
because that file ships with the orchestrating core plugin, not inside this
repo's own tree.

Two instances embody the pattern the issue names: the core plugin's
proposal-shape-gate.sh (a PreToolUse gate on file writes checking a
document's required-section shape, never free-text content) and
`gates/design_research_consult.py`'s `check_issue_body` function (a
two-branch existence check: a `design-research: <ref>` tag takes one
branch, a `design-research-skip: mechanical` closed-vocabulary tag takes the
other, absence of both takes a fixed-message refusal branch — no semantic
judgment of referenced content). The shared shape: the gate reads a declared
contract (tag or section list) and checks existence/presence, never content
quality — matching #2013's own frozen-principle wording verbatim.

## The enforcement point: `gh pr create`, not file write

`design-artifacts:` names files that must exist before a PR opens — a `gh pr
create` intercept, not a file-write intercept.

canonical: read on-the-record/hooks/pr-preflight.sh in full this session
(555 lines).

`on-the-record/hooks/pr-preflight.sh` is the existing sibling for that
enforcement point: a zero-install PreToolUse Bash hook intercepting `gh pr
create|edit`, extracting `--body`/`--body-file` from the command line,
resolving the subject issue+role from `.on-the-record/role.json` or the
branch name, with a `deny(msg, hint)` helper that exits 2 with an actionable
stderr message. Its `phase2` branch already fetches the issue body via
`gh_json("issue", "view", ...)`; the `phase1` branch does not need it today.
It has no filesystem-existence check today — that is new.

canonical: read on-the-record/hooks/design-rationale-guard.sh header comment
this session.

`design-rationale-guard.sh`'s own header states it fails closed on genuine
error, in explicit contrast to `pr-preflight.sh`, whose header states a
fail-open policy on any parse failure, missing tool, or non-matching
command. #2013's Acceptance text — "a mechanical issue (no declaration) is
entirely unaffected — byte-identical gate behavior" — matches the fail-open
posture: an absent declaration must stay inert rather than block on gh or
network trouble.

## No existing `docs/issue-<n>/design/` convention

canonical: `grep -rln "docs/issue-.*design" docs` run this session.

All hits are unrelated paths (`reports/product-discovery`,
`reports/architecture`, etc.); no directory literally named
`docs/issue-<n>/design/` is in current use anywhere in the tree. The issue's
`docs/issue-<n>/design/` is therefore a new path convention this gate
introduces.

## Test conventions observed

canonical: `grep -n "^def test" on-the-record/hooks/test_pr_preflight.py`
run this session (824-line file; function names scanned, not full bodies).

`test_pr_preflight.py`'s own file-header comments state its ported-logic
tests duplicate the hook's Python as plain functions and assert against that
duplication directly, rather than shelling out to the `.sh` file per test.

canonical: `find . -iname "*design_bearing*test*" -o -iname "test*design_bearing*"` run this session.

Two test files exist for the upstream classifier:
`gates/test_design_bearing_classifier_live_fire.py` and
`test/test_design_bearing_classifier.py` — one unit-shaped
(network-free, exercising the pure function), one live-fire/integration
shaped. #2013's Acceptance text names three required paths (missing files
refused, present files accepted, undeclared issue untouched); this
unit/live-fire split is the template to follow for covering them.

## Alternatives visible from this survey (for the proposal's Rationale)

- New standalone script under `gates/` invoked by `pr-preflight.sh`, versus
  an inline port directly into `pr-preflight.sh` — mirroring how
  `check_body`/`_plan_from_body` are already ported inline there rather than
  imported, per that file's own documented zero-install rationale: a
  consumer repo ships only `on-the-record/hooks/`, not necessarily a
  `gates/` checkout.
- A filesystem existence probe at PR-create time against the current working
  tree, versus trusting a session-written manifest/sidecar (e.g. extending
  `.on-the-record/role.json`) that records which artifacts a session
  produced — the former checks ground truth directly; the latter would
  trust self-reported state, in tension with the "checks existence, never
  interprets" frozen principle, since a self-reported manifest is a claim
  rather than a fact.
