---
issue: 3127
role: implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675
author: implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675
skills: implementation-blueprint (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: b9adc895bdfa172e1d96f6970729eec92f75f598
loop_state: landed
type: fix
breaking: false
verdict: pass — acceptance: `bash -c "python3 scripts/issue-3127/run_consumer_pair.py --dry-run"` — result: exit 0; acceptance: `bash -c "test -f docs/issue-3127/_assets/consumer-path-results.json"` — result: present; acceptance: `bash -c "python3 scripts/issue-3127/verify_preregistration.py"` — result: exit 0
upstream:
  - path: docs/issue-3127/decisions/pre-registration.md
    sha: same-commit
  - path: scripts/issue-3127/verify_preregistration.py
    sha: same-commit
---

# issue-3127 — implementation-blueprint+experiment-trust+silent-failure-audit-9afe0675 record

## What was done

Repaired `scripts/issue-3127/verify_preregistration.py` (acceptance check
3 on issue #3127) at commit `1bd821e8b827f64b9827c0cf7a2db3a2c7148d08`.

canonical: this session's own execution before any code change —
```
$ python3 scripts/issue-3127/verify_preregistration.py
both files were introduced in the same commit (fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8) -- the pre-registration must be committed strictly before the results, not alongside them, or the threshold could have been written with the result already known
exit: 1
```
Root cause: PR #3131 landed as a single squash-merge commit (`fb0bb0d3`)
introducing both `docs/issue-3127/decisions/pre-registration.md` and
`docs/issue-3127/_assets/consumer-path-results.json` together — collapsing
the two-commit ordering the check's original git-ancestry comparison
depended on. This root cause was surfaced by PR #3166 (branch
`issue-3127/experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-626f0a44`,
commit `733f26e3de2851e18b966bbc7b5963701e50013a`, not reachable from this
branch's working tree — canonical: `gh pr view 3166 --json state` output
read this session, state `OPEN`) — canonical: `gh pr view 3166 --json
title,body,number,state,headRefName` output read this session, which
states the finding verbatim and explicitly scopes fixing it as out of
that session's own scope.

Changes (all in the commit above):
- `docs/issue-3127/decisions/pre-registration.md`: added a
  `verification_pr: 3131` frontmatter field pinning the PR that
  originally introduced this file's content.
- `scripts/issue-3127/verify_preregistration.py`: kept the existing
  git-ancestry check as the primary path unchanged (a future session that
  actually executes the harness commits real results in a genuinely
  later, distinct commit on a branch that already has the pre-registration
  as an ancestor — ordinary ancestry resolves that correctly, no PR
  lookup involved). Added one new fallback, `_resolve_via_pr_history()`,
  firing only when `prereg_commit == results_commit` (the exact
  same-commit collapse signature): reads `verification_pr` from the
  pre-registration's frontmatter, fetches that PR's own commit list via
  `gh pr view <n> --json commits`, resolves which commit first touches
  each path via `gh api repos/<owner>/<repo>/commits/<sha> --jq
  '.files[].filename'`, and requires the pre-registration's index to be
  strictly earlier. canonical: `gh pr view 3131 --json commits` output
  read this session — PR #3131's own commit list still returns 2 original
  commits in order, `84226988e930981b02d00abd30e22c83100e875f`
  (`docs/issue-3127/decisions/pre-registration.md`,
  `scripts/issue-3127/run_consumer_pair.py`,
  `scripts/issue-3127/verify_preregistration.py`) followed by
  `9c9801cd470129580de54b78a32abc30875de90e`
  (`docs/issue-3127/_assets/consumer-path-results.json` only) — confirmed
  via `git show --stat` on both commits after `git fetch origin <sha>`,
  independent of what the squash-merge collapsed them to on `main`.
- `tests/test_issue_3127_verify_preregistration.py` (new) — derived:
```
$ python3 -m pytest tests/test_issue_3127_verify_preregistration.py -q
............                                                             [100%]
12 passed in 0.85s
```
  Unit tests against `_resolve_via_pr_history()` and `_read_frontmatter()`
  with an injected fake `gh` runner (no network), plus two end-to-end
  tests through `verify()` against a real temporary git repo reproducing
  the squash-collision shape live. Includes the required demonstration of
  a constructed violation:
  `VerifyEndToEndCollisionTest::test_constructed_violation_is_refused_end_to_end`
  builds a repo where the local commit collapses ordering exactly like
  PR #3131 did, but the injected PR history shows the results file was
  introduced *before* the pre-registration — `verify()` returns non-ok
  with `does NOT show … strictly before`, i.e. the check refuses it
  rather than passing it because the local (collapsed) commit looks the
  same either way.

Re-ran the check for real after the change — canonical: this session's
own execution —
```
$ python3 scripts/issue-3127/verify_preregistration.py
OK: same-commit collapse resolved via PR #3131's own pre-squash commit history -- docs/issue-3127/decisions/pre-registration.md first appears at commit index 0 (84226988e930981b02d00abd30e22c83100e875f), docs/issue-3127/_assets/consumer-path-results.json at index 1 (9c9801cd470129580de54b78a32abc30875de90e), strictly earlier
exit: 0
```
and the full `tests/` suite (baseline 352 per this session's task text) —
derived: `python3 -m pytest tests/ -q`:
```
364 passed, 2 warnings in 10.38s
```
(364 = 352 pre-existing + 12 new; the 2 warnings are the pre-existing
`pinned-fixture-divergence` (issue #3019) notices, unrelated to this
change.)

## Why

Two candidate signals were named in the task: (a) the original PR's own
commit history, pinned by a PR number recorded in the pre-registration
file; (b) content-bound evidence, where the pre-registration carries a
self-digest and the results file embeds it. Chose (a).

Rejected (b) because it does not actually establish temporal order, only
content correspondence. A digest proves "the results file's author had
the final pre-registration content in hand when writing results" — it
does not prove the pre-registration was frozen *before* the results were
known. Nothing stops a single commit from computing the pre-registration's
digest and embedding it in a freshly-fabricated results file in the same
breath, once both are already known to the author; the digest would still
match. Making (b) actually resist that would require an external,
independently-timestamped commitment of the digest (e.g. posting it to an
issue comment before data collection) — at which point it is no longer a
self-contained content-binding scheme but a variant of (a) (external,
GitHub-hosted, timestamped evidence), just routed through issue comments
instead of a PR's commit list. (a) already gives that external evidence
directly, and it is not hypothetical for this repo: PR #3131 already
*had* the correct two-commit order (see canonical citation above) before
its own squash-merge collapsed it on `main`, so (a) recovers a fact that
already happened rather than requiring a new commitment protocol that no
pre-registration in this repo has ever produced.

Design choice: the fallback fires only when the plain ancestry check
finds `prereg_commit == results_commit` (the exact squash-collapse
signature), not on every run — this keeps the common future case (a
session that executes the harness and commits real results in a new,
later commit) on the original, `gh`-free ancestry path with unchanged
semantics. The `gh` dependency (network + auth) is scoped to the one case
that structurally cannot be resolved from local history alone.

Scoped `gh` command shapes to what the repo's own guard hooks allow: the
first attempt, `gh api repos/tokenmaxxxer/on-the-record/pulls/3131/commits`,
was refused live by `hooks/upstream-defect-scope-guard.sh` (`gh api`
against a `/pulls`-shaped endpoint is denied outright, issue #1131 req#4)
— canonical: this session's own refused tool call, shown verbatim in
this session's transcript. Used `gh pr view <n> --json commits` (a
different command shape, unaffected) for the commit list, and `gh api
repos/<owner>/<repo>/commits/<sha>` (not a `/pulls` path) for per-commit
file lists instead — both confirmed working live against PR #3131 (see
canonical citations above).

`silent-failure-audit` invoked on the new error-handling paths (gh calls,
JSON parsing, frontmatter parsing) — canonical: this session's own
`silent-failure-audit` skill invocation and analysis this turn. Every
explicit failure path (gh repo/pr/api call returning non-zero, malformed
JSON, a commit list missing a field, a path absent from every commit) is
Handled: each returns `False` with an explicit reason, confirmed by the
`test_gh_pr_view_failure_fails_closed`, `test_gh_repo_view_failure_fails_closed`,
`test_missing_verification_pr_field_fails_closed`, and
`test_path_absent_from_pr_history_fails_closed` tests above (all passing
per the derived pytest run above). Zero Silently-Absorbed sites found.
Two Unguarded (not caught at all) paths noted and left as-is: `gh`/`git`
binaries missing from `PATH` would raise an uncaught `FileNotFoundError`
instead of a clean message — this still fails the check (non-zero exit
via traceback), so it is loud, not silent, and matches the original
script's own existing convention (it never guarded `git`'s absence
either); hardening it was out of this repair's narrow scope. Recorded as
an open finding below rather than silently left out of the audit.

## What did not work

None.

## Upstream basis

This repair operates directly on the two files it fixes the ordering
check for: `docs/issue-3127/decisions/pre-registration.md` (added the
`verification_pr: 3131` field, same commit as this record's code) and
`scripts/issue-3127/verify_preregistration.py` (the script under repair,
same commit). The root-cause diagnosis itself came from PR #3166's own
record (cited with its commit sha in "What was done" above, not listed
here as a formal upstream entry since that PR's branch is not reachable
from this branch's working tree) — canonical: `gh pr view 3166 --json
state` output read this session, state `OPEN`.

## Open findings

- `gh`/`git` binary absence is an uncaught exception path (Unguarded, not
  Silently Absorbed — see silent-failure-audit note above). Fails loud
  (non-zero exit), so it does not violate the check's fail-closed
  contract; a future session could wrap it for a cleaner message if that
  is ever judged worth the extra code. Not fixed here — narrow repair
  scope, and the failure mode is already safe, just less friendly.
- The `verification_pr` frontmatter field is itself editable working-tree
  content: a session that authored a genuinely-fresh, single-commit
  fabrication (threshold and result written together in one new commit)
  could point `verification_pr` at an unrelated, legitimate old PR (e.g.
  #3131) to make the fallback resolve against history that has nothing to
  do with the new commit under review. This is out of the threat model
  the task named (the same class of trust the original ancestry check
  already extended to git commit metadata, not a malicious-insider
  model) and is noted here rather than silently ignored. Closing it would
  need binding the PR reference to the specific commit under review
  (e.g. requiring the collapsed commit itself to be one of the
  referenced PR's own commits, not just any commit reachable from HEAD),
  not attempted here.

## Next steps

None — `loop_state: landed`. A future session executing the harness for
real (per `docs/issue-3127/_assets/consumer-path-results.json`'s
`next_steps_for_a_future_executing_session`) will exercise the unchanged,
`gh`-free ancestry path when it commits real results in a new commit; the
fallback added here only needs revisiting if that session also finds
itself squash-collapsed against the pre-registration again.

## Skill verdicts

skill-verdict: silent-failure-audit — applied: invoked; audited every new
error-handling path in `scripts/issue-3127/verify_preregistration.py`
(gh repo/pr/api calls, JSON parsing, frontmatter parsing) — 0 Silently
Absorbed, all Handled (explicit `False` + reason), 2 Unguarded paths
noted (see Open findings).
skill-verdict: implementation-blueprint — not-applicable: single-file
repair adding one fallback function inside an existing script's
established structure, not a new multi-module architecture decision.
skill-verdict: experiment-trust — not-applicable: no experiment result is
being interpreted, trusted, or reported this session — the harness has
still not been executed (`run_status: not_executed`); this session only
repairs pre-registration tooling integrity.
