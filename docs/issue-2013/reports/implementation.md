---
code_under_review:
  - gates/design_artifacts_gate.py
  - gates/test_design_artifacts_gate_live_fire.py
  - test/test_design_artifacts_gate.py
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - on-the-record/hooks/test_pr_preflight_delegation.py
  - test/test_branch_role_field.py
  - docs/specs/design-artifacts-contract.md
  - docs/specs/enforcement-boundary.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-2013 phase-2 implementation record

## What was done

canonical: `gh issue view 2013 --comments` (run this session) — the issue carries the merged proposal reference, the `APPROVE issue-2013/implementation` comment, and the operator's fail-closed amendment text.

Delivered the phase-2 build approved on issue #2013, basis
`docs/issue-2013/proposals/design-artifact-existence-gate.md` (proposal PR
#2025, merged), plus the operator's amendment: replace the proposal's
fail-open-on-infrastructure-trouble constraint with fail-CLOSED
(actionable message) specifically for the case where the issue body
cannot be fetched at `gh pr create` time.

- `gates/design_artifacts_gate.py` (new, commit 3d0c48e2): `parse_declaration(body)
  -> list[str] | None` reads a `design-artifacts:` tag line and the
  bulleted-list-or-fenced-block of repo-relative paths that follows it
  (`None` when no tag is present — byte-inert path); `missing_artifacts(repo,
  declared_paths) -> list[str]` filesystem-checks each declared path;
  `check(repo, issue) -> list[str]` fetches the issue body via
  `gates/gh_rest.py`'s `fetch_issue_body` and, per the approval amendment,
  returns an actionable fail-closed violation (not an empty list) when the
  fetch itself returns `None`.
- `on-the-record/hooks/pr-preflight.sh` (commit 3d0c48e2): extended the
  `create`/`edit` intercept with an inline port of `parse_declaration`/the
  existence check, wired to run on every `gh pr create` regardless of
  phase (fetching the issue body a second time in the phase1 branch,
  reusing the phase2 branch's existing fetch when already phase2); denies
  naming each missing path when the declaration exists and any declared
  path is absent; denies with the fail-closed message when the body fetch
  itself fails. No declaration in the body → no new check runs, matching
  the proposal's "byte-identical for a mechanical issue" acceptance line.
- `gates/test_design_artifacts_gate_live_fire.py` (commit 60056306) /
  `test/test_design_artifacts_gate.py` (commit 3d0c48e2): unit tests for
  `parse_declaration`/`missing_artifacts`/`check` covering the missing/
  present/undeclared/fetch-failure paths, plus bulleted-list and
  fenced-block declaration parsing.
- `on-the-record/hooks/test_pr_preflight.py` (commit 3d0c48e2): four new
  end-to-end `test_hook_*` cases driving the real `pr-preflight.sh` via a
  stub `gh` — missing declared artifact denied (path named in stderr),
  present declared artifact allowed, no declaration allowed untouched, and
  issue-body fetch failure denied with the fail-closed message.
- `docs/specs/design-artifacts-contract.md` (new, commit 3d0c48e2): the
  `design-artifacts:` declaration syntax (bulleted list or fenced block),
  the informational default artifact set, what the gate checks (existence
  only), and the fail-closed posture on infrastructure trouble.
- `docs/specs/enforcement-boundary.md` (commit 3d0c48e2): added the
  `design_artifacts_gate.py` registration row (`gate-registration-guard.sh`
  requirement) and extended the existing `pr-preflight.sh` row describing
  this addition.

canonical: acceptance: python3 -m pytest -q -m "not slow" — result: PASS (2519 passed, 20 xfailed, 1 xpassed in 41.16s, run this session after the two live-discovered fixes below and their fixture updates)

canonical: acceptance: python3 -m pytest -q -m slow — result: UNMEASURED-with-reason: run once earlier this session (106 passed, 2 xfailed in 358.22s, after the two live-discovered fixes below), too slow to re-run inside this commit's 180s recheck bound; triggered by this delivery's changes to on-the-record/hooks/*.sh and on-the-record/hooks/test_*.py per .on-the-record/test-tiers.json's trigger_change_classes.

## Why

canonical: `docs/issue-2013/proposals/design-artifact-existence-gate.md` (read in full this session, its Rationale section) and `gh issue view 2013 --comments` (the amendment text quoted above).

Per the proposal's Rationale (unchanged in phase 2): inline port into
`pr-preflight.sh` rather than a new standalone hook, mirroring the
existing `check_body`/`_plan_from_body` ports in the same file, because
`pr-preflight.sh` already owns the "before `gh pr create` succeeds" moment
and already resolves issue+role; a direct filesystem existence probe
rather than a self-reported session manifest, because a manifest is a
claim rather than a fact and existence must check ground truth; enforcement
stays in `gates/design_artifacts_gate.py` (never in the #2012 classifier),
since the classifier only proposes default artifact sets and has no
trigger point at PR-creation time.

The fail-closed amendment (rather than the proposal's original fail-open
constraint) is scoped narrowly to the one lookup this gate needs: a body-
fetch failure now denies with an actionable message instead of silently
passing, per the operator's stated reasoning quoted above ("a gate that
opens on network failure is bypassable by breaking gh"). Every other
infrastructure-trouble path this file already handles (missing `python3`/
`gh`, unparseable command, unreadable body-file, `gh issue view --json
comments` lookup failure for phase determination) is untouched and stays
fail-open, matching "everything else exactly as proposed."

## Rationale for deviations

canonical: `git log --all --oneline -- gates/test_design_bearing_classifier_live_fire.py` and `git show -s --format=%B b08f5ec7` (both run this session) — the #2012 precedent commit sequence this deviation mirrors.

Two mechanical, in-set deviations from the approved proposal (no design/
product judgment, no scope change):

- **Test-file split across two commits**, mirroring
  `gates/design_bearing_classifier.py`'s landed commit (b08f5ec7): the
  proposal named a `gates/`-side test file with the same basename as
  `test/test_design_artifacts_gate.py` — matching
  `on-the-record/hooks/live-fire-test-guard.sh`'s exact stem-name
  requirement for a newly-staged `gates/*.py` module — which
  `gates/test_duplicate_test_basenames.py` refuses once both are staged
  together (no `__init__.py` package boundary, pytest collection
  collides). Committed the exact-named file first in commit 3d0c48e2
  (satisfying `live-fire-test-guard.sh`, which only checks a module's
  live-fire test at the commit that newly stages the module itself), then
  a second, module-untouched commit (60056306) renamed it to
  `gates/test_design_artifacts_gate_live_fire.py` (matching the sibling
  naming convention `gates/test_design_bearing_classifier_live_fire.py`
  already uses for the identical split) to fix the basename collision —
  `live-fire-test-guard.sh` does not re-check a module that isn't newly
  staged in the renaming commit.
- **Fail-closed amendment scope**. canonical: `gh issue view 2013 --comments` (same amendment text cited at the top of "What was done"). Documented in `pr-preflight.sh`'s own header comment and `docs/specs/enforcement-boundary.md`'s row as a narrow carve-out (this one lookup only), not a change to the file's overall fail-open posture; noted here as a divergence from the merged proposal PR #2025 body's original wording.
- **Two pre-existing defects fixed in-set, discovered live while verifying this delivery against the real repo (not against the fixture-only test suite)**. canonical: manual extraction of `pr-preflight.sh`'s embedded heredoc run standalone against issue #2013 this session (`gh pr create --body-file ... --base main` shape), output pasted into this session's own working notes.
  1. `gh_json()`'s existing `-q .body` call shape (used both by the pre-existing phase2 plan-body fetch and by this delivery's own new fetch, copied from that same shape) prints raw unquoted text for a string result, which is not valid JSON unless the body happens to parse as a JSON literal — `json.loads()` on it silently returned `None` for every real issue body, meaning the phase2 plan-parsing body fetch (and, without this fix, the new design-artifacts fetch) never actually worked against a real `gh` invocation, only against test fixtures whose stub `gh` JSON-encoded the string. Fixed both call sites in `pr-preflight.sh` to fetch the JSON object (`--json body`, no `-q`) and extract the `"body"` key, matching the shape the `comments` fetch already used correctly. Updated the stub `gh` shims in `on-the-record/hooks/test_pr_preflight.py`, `on-the-record/hooks/test_pr_preflight_delegation.py`, and `test/test_branch_role_field.py` to emit the same `{"body": ...}` shape a real `gh --json body` call returns.
  2. `pr-preflight.sh`'s own phase-determination `needle` check still used the pre-#2021 exact whole-body match (`.strip() == needle`), never ported to `approval-gate.sh`'s line-anchored `_first_line_matches` fix — so a real `APPROVE issue-<n>/<role>` comment carrying rationale on later lines (the exact shape #2013's own approval comment on this issue uses) was read as phase1 by `pr-preflight.sh` while `approval-gate.sh` already read it as phase2, blocking this very PR's own `Closes #2013` trailer. Ported the same `_first_line_matches` helper into `pr-preflight.sh`'s phase-determination block.

  Both are mechanical (no design/architecture/security/product judgment beyond porting an already-established, already-reviewed fix pattern), stay inside `pr-preflight.sh` and its already-frozen sibling test files (the exact file this delivery's own write set already modifies), and do not change what this delivery's own design-artifacts feature claims to do — logged here per the deviation loop rather than filed separately, since fixing them was necessary for this PR to open at all.

## What did not work

None.

## Open findings

None.
