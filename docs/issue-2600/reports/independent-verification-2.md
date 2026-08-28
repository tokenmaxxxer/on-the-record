---
issue: 2600
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md
    sha: 670b5573ff7193cda0fad5c2d558c5f0231cf435
---

# issue-2600 — independent-verification-2 record

## What was done

Independently verified PR #2668 (`issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88`,
branch head `670b5573`), the first slice of #2600's sweep, covering both
repos' env-var-kind rename and the on-the-record-side per-kind occurrence
map. Read the PR body and the subject's own record, then independently
reproduced every acceptance/derived claim rather than trusting the citations.

**on-the-record half** (diff vs `origin/main`, reproduced via a disposable
detached worktree, never the session's own tracked tree):
- `git diff origin/main...FETCH_HEAD --stat` matches the PR's claimed
  file list (18 files, `+243/-32`): `gates/model_routing.py`, `pipeline.py`,
  `spawn.py`, `test/test_spawn_model_override.py`, 12 hooks under
  `on-the-record/hooks/`, plus two new record files under
  `docs/issue-2600/`.
- Read the actual diff for `pipeline.py`, `spawn.py`,
  `gates/model_routing.py`, `on-the-record/hooks/session-role-bind.sh`,
  `test/test_spawn_model_override.py`: every `MUSTER_ROLE_MODEL` ->
  `MUSTER_SKILL_MODEL` and `OTR_ROLE_BIND_STATE_DIR` ->
  `OTR_SKILL_BIND_STATE_DIR` site is a straight rename, no compat alias, no
  behavior-shaped line changed.
- acceptance: `grep -rn 'MUSTER_ROLE_MODEL\|OTR_ROLE_BIND_STATE_DIR'
  --exclude-dir=.git --exclude-dir=docs .` in the worktree — result:
  ```
  (no output, exit 1 — 0 matches)
  ```
- acceptance: `python3 -m pytest test/test_spawn_model_override.py -q` —
  result:
  ```
  6 passed in 1.20s
  ```
- acceptance: `python3 -m pytest test/test_convention_equivalence.py -q` —
  result:
  ```
  2 failed, 31 passed in 0.95s
  ```
  matches the PR's claimed "2 failed / 31 passed, identical before/after."
  Failing tests: `BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim`
  and `ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`
  — both are byte-verbatim regex-pinning assertions unrelated to any
  `MUSTER_ROLE_MODEL`/`OTR_ROLE_BIND_STATE_DIR` site, consistent with the
  record's "pre-existing on main" claim.
- Live hook demonstration, reproduced independently in the worktree
  (not copied from the record):
  ```
  echo '{"session_id":"writer-demo"}' | TOKENMAXXXER_SPAWNED=1 \
    OTR_SKILL_BIND_STATE_DIR=<tmpdir> bash on-the-record/hooks/session-role-bind.sh
  -> exit 0; <tmpdir>/writer-demo.json = {"spawned": true}

  echo '<Write payload, session_id=writer-demo, file_path=/tmp/foo.py>' | \
    OTR_SKILL_BIND_STATE_DIR=<tmpdir> bash on-the-record/hooks/deliverable-guard.sh
  -> exit 0 (allowed)
  ```
  Confirms the renamed env var actually carries the writer -> reader
  snapshot end to end, both sides.
- `echo CLAUDE_ROLE | grep -oiE '\brole\b'` — result: no output, exit 1.
  Confirms the record's "the issue's own acceptance regex undercounts
  compound identifiers" methodology note independently.

**tokenmaxxxer-core half** — the record documents the commit as pushed but
un-PR'd (blocked by this session's own `upstream-defect-scope-guard.sh`).
Cloned `tokenmaxxxer/tokenmaxxxer-core` fresh into a scratch directory
(outside this session's tracked tree) to check it independently rather than
trust the PR body's citation:
- canonical: `gh api repos/tokenmaxxxer/tokenmaxxxer-core/commits/79983f8`
  — commit exists, message matches the PR body's summary verbatim.
- canonical: `gh api ".../compare/main...issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88"`
  — 5 files changed: `core/hooks/{handbook-trigger-gate,record-fields-gate,survey-order-gate,trailer-gate}.sh`,
  `core/hooks/pretooluse_dispatcher.py`. Read every patch hunk: `PG_ROLE`,
  `HT_ROLE`, `TRAILER_GATE_ROLE`, `RF_ROLE`, `SOG_ROLE` are renamed to
  their `_SKILL` equivalents on both the writer side
  (`pretooluse_dispatcher.py`) and every reader side, no compat alias
  left on any of the five.
- Ran the three test suites the record cites, both on the PR commit and
  (via `git checkout main`) on core's own `main`, to check the
  "identical pre-existing pass/fail counts" claim rather than take it on
  faith:
  ```
  core/hooks/tests/run-survey-order-gate-tests.sh   -> 7 passed, 0 failed (both)
  test/hooks/test_trailer_gate.sh                    -> 5 passed, 5 failed (both, same 5 named failures)
  test/hooks/test_handbook_trigger_gate.sh           -> 3 passed, 3 failed (both, same 3 named failures)
  ```
  All three match the record's claimed counts exactly, and the failure
  sets are identical between the PR commit and unmodified `main` —
  confirms this slice introduced no regression in core either.
- `docs/` diff: `git diff --stat origin/main...FETCH_HEAD -- docs/` in
  on-the-record shows only the two new record files under
  `docs/issue-2600/reports/` (additions, no existing record touched); the
  core-side commit (`git show --stat 79983f8`) touches no `docs/` path at
  all. Both match the issue's "historical records are untouched"
  acceptance line.
- Read `on-the-record/hooks/upstream-defect-scope-guard.sh` in full to
  check the record's Open finding #3 (no session-side workaround exists
  for opening the core PR). Its `in_scope()` denies whenever the
  extracted target repo differs from this session's own git-origin
  repo, regardless of `cd`, which does structurally deny
  `gh pr create --repo tokenmaxxxer/tokenmaxxxer-core` from an
  on-the-record-origin session. The claim holds.

## Why

Verify-at-landing (contract v3 s19a/handbook) means a deliverable record
is only as good as its citations reproducing; this subject's deliverable
touches 18 files across two repos and asserts several test-count and
live-hook claims, so the highest-value independent check was to
re-derive every number rather than spot-check one. Used a disposable
detached worktree and a fresh scratch clone of the companion repo instead
of the session's own tracked tree, specifically so re-running the PR's
own commands could not accidentally leave stray build/test artifacts in
this verification session's own commit.

## What did not work

An early `git checkout FETCH_HEAD -- .` followed by `git clean -fd`
against this session's own tracked working tree (before switching to a
disposable worktree) staged the subject's entire diff into this session's
index and, because `git clean -fd` also swept up this record's own
still-untracked skeleton file (untracked at that point since it had never
been committed), deleted it. Caught immediately via `git status`,
recovered with `git reset --hard HEAD` (discarding the staged subject
diff, which this session had not committed) and a `Write` of the
skeleton's original content reconstructed from the earlier `Read`. All
acceptance reproduction after that point used `git worktree add --detach`
(this repo) and a `gh repo clone` into `/tmp` (the core repo) instead,
neither of which can touch this session's own tracked tree or its own
record.

## Upstream basis

`docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md`
(untracked/unmerged on `main` as of this record — the path exists only on
branch `issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88`)
at `670b5573ff7193cda0fad5c2d558c5f0231cf435` (PR #2668's branch head,
on-the-record); the companion commit `79983f80dff68f2bf4fdaf3165e18a8efdef55a0`
on `tokenmaxxxer/tokenmaxxxer-core` branch
`issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88`
(pushed, not yet PR'd — see the subject record's own Open finding #3).
canonical: `git fetch origin issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88 && git show FETCH_HEAD:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md`
(fetch/show succeeded) and `gh pr view 2668` reporting `state: OPEN` —
confirms the branch is pushed and reviewable but not yet merged.

## Open findings

None found beyond what the subject's own record already surfaces.
canonical: `git show FETCH_HEAD:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md`
(same fetch as Upstream basis, path untracked/unmerged on `main`) — its
own Open findings #1 (`CLAUDE_ROLE` deferral) and #3 (core PR blocked by
`upstream-defect-scope-guard.sh`) are both independently confirmed above
(the `CLAUDE_ROLE` regex-miss reproduction, and the
`upstream-defect-scope-guard.sh` read-through), not merely re-cited.
This slice is an intentional partial delivery against #2600.
canonical: `gh issue view 2600` — the issue's latest comment partitions
the sweep into slices; this PR's own body says "First slice of #2600."
It does not claim to close #2600, and the PR trailer says
`Advances #2600` accordingly — not itself an open finding, just noted so
this verification record doesn't read as endorsing a false completion
claim.

## Next steps

None for this record — terminal. The subject's own "Next steps" (opening
the core PR from a core-homed session or the operator, and the remaining
slices per the partition) stand as stated in its own record.

skill-verdict: work-in-english — applied: invoked; this record, all
derived/acceptance blocks, and internal reasoning are in English; only
the final chat summary to the user will be in Korean.
other mounted skills: not triggered — observability-phase-trace (no
observability-methodology surface here), defect-verification-severity-band-assignment
(no reproduced defect to band — this is a deliverable-claims audit, not a
defect verification), issue-retrospective-timeline-comprehensibility-and-subtraction-rules
(not a cross-role retrospective), verify-finding-record (not a
`defect-verification.md` reproduction-outcome record), test-depth-audit
(the check here was whether cited test counts reproduce, not a
genuine/execution-only/mock-dominated classification of the suites
themselves).
