<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

<!-- Guidance landings for gates demoted from blocking hooks (issue #2138 dispositions; each bullet was previously a PreToolUse deny hook). -->
- ABSORBED-BRANCH RECUT (issue #784, demoted from
  absorbed-branch-recut-guard.sh): when a concurrent merge absorbs a
  still-running session's own `issue-<n>/<role>` branch into base
  (deleted at merge), the session's next `git commit`/`gh pr create`
  surfaces as "No commits between main and issue-<n>". Recut the branch
  off updated base (`spawn.py`'s `_recut_absorbed_branch` shape) before
  committing — never force-push over the absorbed history.
- PR-BODY CLAIM SCAN (issue #476, demoted from claim-scan-preflight.sh):
  a `gh pr create`/`gh pr edit` body making outcome claims carries an
  adjacent evidence marker (command output fence, `derived:`,
  `acceptance: ... — result: ...`) within ~5 lines of each claim —
  gates/claim_scan.py's shape, now advisory.
- LIVE-FIRE TEST FOR NEW GATES (issue #914, demoted from
  live-fire-test-guard.sh): a newly-staged plugin gate/hook lands with a
  test that actually fires it as a real lifecycle event with a crafted
  payload and asserts its allow/deny outcome — a test file merely
  existing is not proof the capability fires. The executed-evidence
  backbone stays mechanically enforced by
  acceptance-command-real-run-guard.sh and
  live-fire-claim-real-run-guard.sh (#2137 verify-at-landing).
- PER-ROLE QUALITY BAR (issue #1156, demoted from quality-bar-gate.sh):
  before merging a PR whose diff falls in a bar-scoped role's paths,
  read that role's `quality_bar` in roles/specs/<role>.spec.json and
  check the bar is met (gates/quality_bar.py: classify — BAR_MET /
  BAR_NOT_MET / ESCALATE); an unmet bar is a reason to send the PR back,
  now by judgment rather than a deny hook.
- SUBPROCESS CALL-SHAPE CONSISTENCY (issue #419/#512, demoted from
  call-shape-guard.sh): a `.py` write that adds a subprocess call keeps
  its call shape (list-argv vs shell-string, check/capture kwargs)
  consistent with the sibling call sites already grouping in the tree,
  and a sibling file named in a module docstring stays in sync when the
  named counterpart changes.

- ACCEPTANCE CHECK-RUNNER AT LANDING (issue #2233): before any of the
  landing steps below, run the check-runner explicitly as an orchestrator
  step — `python3 gates/check_runner.py <pr> <issue> --repo <repo>` — so
  its PR comment exists for `gates/merge_gate.py`'s `evaluate()` to read.
  issue #2313: `--repo` is the checkout of the repo the PR/issue actually
  belongs to (`check_runner.py:381`'s `gh` calls use it as `cwd`) — when
  orchestrating on-the-record's own landing that repo is `${CHECKOUT}`,
  but for **target-repo** (consumer) work `--repo` must be that target
  repo's checkout, never `${CHECKOUT}` — passing `${CHECKOUT}` there
  fetches the plugin repo's own same-numbered issue instead and fails
  with "Acceptance 절이 없다". This is manual, not CI-wired: this repo
  carries no `.github/workflows/` surface (`merge_gate.py`'s own docstring), so the
  orchestrator session runs it by hand, same as the other landing steps
  here — nothing else in this repo invokes it. An issue whose
  `## Acceptance` section declares no runnable `check:`/`gate:` line gets
  a distinct "no checks declared" result, not a `0/0 passed` — the merge
  gate refuses to read that as satisfied.
  issue #2381: you do NOT need to `git fetch` `--repo` yourself before
  this step — `check_runner.py`'s `checkout_pr_worktree()` now fetches
  ALL of origin's branches (`fetch_all_role_branches()`, the full
  `+refs/heads/*:refs/remotes/origin/*` refspec) before its `git
  worktree add`, not just the one PR's head branch, so a role branch
  pushed minutes earlier resolves without the old "fatal: invalid
  reference" — `gates/merge_gate.py` (no fetch of its own) then reuses
  the same refreshed `--repo` checkout. A plain `git fetch origin` in a
  checkout whose `remote.origin.fetch` was narrowed to `main` only used
  to leave newly-pushed role branches unresolvable regardless.
- LANDING REQUIREMENT-MET GRADE (issue #1651): as part of "verify it"
  above, before `gh pr merge`, spawn a builder-blind grader session —
  no access to the builder's context, given only the diff plus the
  issue's frozen `- check:` criteria (reuse the `adversarial-review`
  skill/consult independence pattern) — that runs
  `gates/requirement_met.py`. Its deterministic artifact-presence
  sub-check BLOCKS the merge; its semantic YES/NO/UNKNOWN verdict per
  criterion is recorded ADVISORY only and never blocks by itself.
- SCOPE ADHERENCE AT LANDING (issue #1658): also before `gh pr merge`,
  run `gates/scope_adherence.py` against the PR's touched files and the
  issue's `scope:` field. A declared-scope violation BLOCKS the merge;
  an undeclared scope is ADVISORY only (consumer repos with no `scope:`
  field proceed exactly as today).
- VERDICT-ASYMMETRY AT MERGE (issue #1669): before merging a PR on a
  reviewer verdict, run `gates/verdict_gate.py` `classify(verdict,
  merge_gate_result, tests_pass)`: CHANGES always respawns-with-findings;
  MERGE merges ONLY when `classify()` returns ALLOW_MERGE (the
  deterministic `merge_gate.py` `evaluate()` allows AND acceptance
  checks pass);
  every other outcome is HOLD — never merge on the LLM verdict alone. A
  correct MERGE blocked by a flaky deterministic gate surfaces to the
  human as a HOLD, not an auto-reject.
- STALE-REVERT AT MERGE (issue #1664): the same pre-merge step also runs
  `gates/stale_revert_guard.py` `classify()`/`check_pr()` — a PR whose
  merge would delete content base HEAD already has that was added after
  the PR's merge-base is REFUSED (rebase required), automating the
  PR#1662/#1675 catch the orchestrator previously had to make manually.
- ASSUMPTION-LEDGER INVENTED-CONFIRM AT INTAKE (issue #1665): before
  spawning a design-bearing issue, surface `gates/assumption_ledger.py`
  `invented_assumptions()` for that issue's body to the human for
  explicit confirmation. An unconfirmed `invented:` item BLOCKS the
  spawn — a mechanical issue (`assumptions-skip: mechanical`) proceeds
  unchanged.
