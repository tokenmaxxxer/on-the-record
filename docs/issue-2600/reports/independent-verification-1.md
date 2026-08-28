---
issue: 2600
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md
    sha: 670b5573ff7193cda0fad5c2d558c5f0231cf435
---

# issue-2600 — independent-verification-1 record

## What was done

Independently audited PR #2668 (`tokenmaxxxer/on-the-record`, branch
`issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88`,
"per-kind occurrence map + retire ROLE-named env vars") — the only open PR
against issue #2600. Re-derived every numeric/acceptance claim in its
record by re-executing the same commands myself against the checked-out
PR branch and a fresh clone of each repo's current `origin/main`, rather
than trusting the record's own transcript.

canonical: `gh pr view 2668` — the subject record lives at
`670b5573ff7193cda0fad5c2d558c5f0231cf435:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md`
(untracked in this branch's own working tree — this branch is cut from
`origin/main` and PR #2668 is unmerged; read via `git show <sha>:<path>`).
derived: `git cat-file -e 670b5573ff7193cda0fad5c2d558c5f0231cf435:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md && echo ok`
```
ok
```

**On-the-record repo, re-run against the PR branch** (`gh pr checkout 2668`, sha `670b557`):

Old env-var names gone —
derived: `grep -rn 'MUSTER_ROLE_MODEL\|OTR_ROLE_BIND_STATE_DIR' --exclude-dir=.git --exclude-dir=docs . | wc -l`
```
0
```
matches the record's claim of 0. New names `MUSTER_SKILL_MODEL`/`OTR_SKILL_BIND_STATE_DIR` present in the same files (`pipeline.py`, `spawn.py`, `gates/model_routing.py`, `test/test_spawn_model_override.py`, `session-role-bind.sh` + 11 reader hooks) the record's table names — spot-checked via `grep -rln`.

Acceptance-check regex count —
derived: `grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' . | wc -l`
```
2377
```
matches the record's claimed 2377 exactly.

`CLAUDE_ROLE` file count —
derived: `grep -rl "CLAUDE_ROLE" --exclude-dir=.git --exclude-dir=docs . | wc -l`
```
21
```
matches the record's claimed 21.

acceptance: `python3 -m pytest test/test_spawn_model_override.py -q` — result:
```
6 passed in 0.85s
```
matches the record's claimed "6 passed".

acceptance: `python3 -m pytest test/test_convention_equivalence.py -q` — result:
```
FAILED test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
FAILED test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
2 failed, 31 passed in 0.88s
```
matches the record's claimed "2 failed, 31 passed", same two test names. Re-ran the identical suite against a **fresh clone of on-the-record's own `origin/main`** (independent of the PR branch, to check the record's "pre-existing on main" claim rather than trust its transcript) —
acceptance: `git clone --branch main https://github.com/tokenmaxxxer/on-the-record.git /tmp/otr-main-check2 && cd /tmp/otr-main-check2 && python3 -m pytest test/test_convention_equivalence.py -q` — result:
```
main sha: d3ef7b8d
FAILED test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
FAILED test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
2 failed, 31 passed in 0.87s
```
identical failures, confirming these 2 are pre-existing on `main` and not introduced by the rename.

`pipeline.py:722` (basis for the `CLAUDE_ROLE` deferral) —
canonical: `sed -n '722p' pipeline.py` on the PR branch
```
env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1",
```
confirms the record's citation.

`upstream-defect-scope-guard.sh` (basis for Open finding #3, why the core PR couldn't be opened from this session) —
canonical: `sed -n '88,112p' on-the-record/hooks/upstream-defect-scope-guard.sh` — `origin_repo()` resolves the target repo from the PreToolUse payload's `cwd` field (`e.get("cwd")`), not the shell's live working directory, and `in_scope()` denies whenever the extracted `--repo`/`GH_REPO` target differs from that resolved origin. This structurally matches the record's claim that a `cd <core-checkout> && gh pr create --repo ...` retry cannot escape the denial.

#2593/#2664 citations (basis for the `CLAUDE_ROLE` non-goal claim) —
canonical: `gh issue view 2593` body, Non-goals section:
```
- Internal variable names never shown to a consumer (`CLAUDE_ROLE`, `board.py`'s local `roles` binding). They belong to the relic sweep (#2139) unless the design happens to touch them.
```
canonical: `gh pr view 2664 --repo tokenmaxxxer/on-the-record` body confirms the landed #2593 design ("name-free deliverable resolution") introduced no replacement noun for `role`/`CLAUDE_ROLE`.

**tokenmaxxxer-core repo, re-run against a fresh clone** (`git clone https://github.com/tokenmaxxxer/tokenmaxxxer-core.git`, both `origin/main` and the pushed branch):

Branch exists, sha matches —
derived: `git ls-remote https://github.com/tokenmaxxxer/tokenmaxxxer-core.git 'refs/heads/issue-2600/*'`
```
79983f80dff68f2bf4fdaf3165e18a8efdef55a0	refs/heads/issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88
```
matches the record's cited sha `79983f8` exactly, and is built on core's current `origin/main` tip (`b2f7b9d`, issue #343/#345 — two commits ahead of what the record's own transcript would have seen), confirmed via `git log --oneline -5` on the branch.

Old env-var names gone —
derived: `grep -rn 'PG_ROLE\|HT_ROLE\|TRAILER_GATE_ROLE\|RF_ROLE\|SOG_ROLE' --exclude-dir=.git --exclude-dir=docs . | wc -l` on the branch
```
0
```
new names (`PG_SKILL`, `HT_SKILL`, `TRAILER_GATE_SKILL`, `RF_SKILL`, `SOG_SKILL`) present in the exact files the record's table names, confirmed via `grep -rln`.

Acceptance-check regex count —
derived: `grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' . | wc -l`
```
933
```
matches the record's claimed 933 exactly.

acceptance: `bash core/hooks/tests/run-survey-order-gate-tests.sh` on the branch — result:
```
survey-order-gate: 7 passed, 0 failed
```
matches the record's claimed "7 passed, 0 failed".

acceptance: `bash test/hooks/test_trailer_gate.sh` on the branch — result:
```
ok     heredoc-cat-with-trailer           allow
FAIL   heredoc-source-text-only-trailer   want=deny got=allow
FAIL   cat-with-file-operand              want=deny got=allow
FAIL   echo-with-flag-denied              want=deny got=allow
ok     printf-with-trailer                allow
FAIL   disallowed-command-in-substitution want=deny got=allow
ok     plain-message-with-trailer         allow
FAIL   plain-message-without-trailer      want=deny got=allow
ok     no-unexpanded-dollar-brace         pass
ok     shadowed-cat-not-trusted           allow, resolution bypassed shadow (1 unrelated invocation)
-- trailer-gate: 5 passed, 5 failed --
```
matches the record's claimed "5 passed, 5 failed". Re-ran the identical script against core's `origin/main` (checked out via `git checkout origin/main` in the same clone) — result:
```
-- trailer-gate: 5 passed, 5 failed --
```
identical output, confirming pre-existing on `main`.

acceptance: `bash test/hooks/test_handbook_trigger_gate.sh` on the branch — result:
```
ok     addcommit-handbook-satisfies       allow
FAIL   bare-commit-no-handbook            want=deny got=allow
FAIL   addcommit-unresolvable-pathspec    want=deny got=allow
ok     addcommit-unresolvable-pathspec-message distinguishable
FAIL   addcommit-dash-named-pathspec-still-denied want=deny got=allow
ok     no-unexpanded-dollar-brace         pass
-- handbook-trigger-gate: 3 passed, 3 failed --
```
matches the record's claimed "3 passed, 3 failed". Re-ran against `origin/main` — result:
```
-- handbook-trigger-gate: 3 passed, 3 failed --
```
identical, confirming pre-existing.

`docs/` scope check —
derived: `git diff --stat origin/main -- docs/` on the core branch
```
(empty — no output)
```
no `docs/` files touched at all on the core side. On the on-the-record side —
derived: `gh pr diff 2668 --name-only | grep '^docs/'`
```
docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md
docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88/deviation-log/20260828T011710671962-9a4befbd0a62729c.md
```
both are new files under the subject's own record area, not edits to any existing `docs/` file — consistent with the acceptance bullet's "historical records untouched" (new records are expected of every session, not a violation).

No discrepancy found between the subject record's stated derivations/acceptance results and this independent re-execution — all counts and test-suite results matched exactly.

## Why

Per contract v3 (verify-at-landing) and `docs/handbooks/observer-verification.md`, issue #2600 needs `REQUIRED_INDEPENDENT_VERIFICATIONS = 2` records whose `author:` differs from the subject's own author and which self-declare `verifies_subject: true`. PR #2668's record carries unusually dense derived/acceptance evidence (per-kind occurrence counts, seven env-var renames each demonstrated live, a cross-repo push blocked from PR-creation by a structural tool guard); independently re-running every quoted command against the actual checked-out trees — rather than reading the transcript — is the only way this verification could catch a stale, cherry-picked, or fabricated number.

## What did not work

None.

## Upstream basis

`670b5573ff7193cda0fad5c2d558c5f0231cf435:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md` (untracked in this branch's own working tree — this branch is cut from `origin/main` and PR #2668 is unmerged; the path exists only at that commit, not on `main`), on `tokenmaxxxer/on-the-record`, plus its companion commit `79983f80dff68f2bf4fdaf3165e18a8efdef55a0` pushed to `tokenmaxxxer/tokenmaxxxer-core` branch `issue-2600/silent-failure-audit+architecture-interface-contract-shape-98ea4d88`.
derived: `git cat-file -e 670b5573ff7193cda0fad5c2d558c5f0231cf435:docs/issue-2600/reports/silent-failure-audit+architecture-interface-contract-shape-98ea4d88.md && echo ok`
```
ok
```
Both shas independently confirmed to exist and match the record's own citations in the "What was done" section above.

## Open findings

None from this audit. The subject record's own three Open findings — #1 `CLAUDE_ROLE` deferred pending a Published Language decision, #2 the persisted-key kind deliberately left out of scope, #3 the core-side PR blocked by `upstream-defect-scope-guard.sh` and needing an operator or core-homed session to open it — are the subject's own, independently confirmed accurate above rather than disputed here.

Scope note: issue #2600 itself remains open. PR #2668's own body carries `Advances #2600`, not `Closes` —
canonical: `gh pr view 2668 --json body -q .body` (trailer line, read live this session): `Advances #2600`.
Further slices (comment/docstring, prompt-text, identifier kinds; the `CLAUDE_ROLE` decision; opening the core PR) are named in the subject's own Next steps and are not covered by this verification. This record certifies the claims made *by PR #2668*, not that issue #2600's full scope is delivered.

## Next steps

None for this record — terminal.

skill-verdict: work-in-english — applied: invoked; this record, all Bash commands run during this audit, and this record's own prose are in English; only the final chat summary to the user is in Korean.
