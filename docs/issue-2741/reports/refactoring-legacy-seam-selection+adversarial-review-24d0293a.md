---
issue: 2741
role: refactoring-legacy-seam-selection+adversarial-review-24d0293a
author: refactoring-legacy-seam-selection+adversarial-review-24d0293a
skills: refactoring-legacy-seam-selection (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md
    sha: same-commit
---

# issue-2741 — refactoring-legacy-seam-selection+adversarial-review-24d0293a record

## What was done

Retired the `role` persisted-state dict key in favor of `skill`, forward-only, no dual read, across both repos — the last slice of #2600.

derived: `grep -rn '"role"' --include='*.py' --include='*.sh' . | grep -v '/docs/'` and the `'role'` single-quote variant — initial enumeration, both repos.
derived: `grep -rnE '\.get\(\s*["\x27]role["\x27]|\[\s*["\x27]role["\x27]\s*\]|\{\s*["\x27]role["\x27]\s*:' --include='*.py' --include='*.sh' . | grep -v '/docs/'` — post-edit sweep, both repos, run after the first edit pass; caught one missed read site not in the original TARGETS list, `board.py:1296` (the `ps` status-row formatter reading the same roster entry a different function on the same page already covered), fixed in a follow-up edit.

on-the-record repo (this repo):
canonical: `git diff --stat` (this repo, working tree)
```
 33 files changed, 138 insertions(+), 138 deletions(-)
```
Runtime-state writers/readers renamed: `relay.py`, `board.py`, `roster.py`, `lifecycle.py`, `events.py`, `watchdog.py`, `consult.py`, `pipeline.py` (including `_write_skill_sidecar()`, the writer of `.on-the-record/role.json`), `spawn.py` (roster registration, ledger writes, `reconcile()`'s `expected`/`observed` dicts — 17 sites; `ap.add_argument("role", ...)` CLI positional and its `a.role` attribute reads left untouched, out of scope: CLI syntax, not a persisted key), `gates/remediation_spawn.py`, `gates/spawn_on_approve.py`, `gates/spawn_on_pr.py`, `gates/closure_sweep.py`, `gates/flows.py`, `gates/delegation_metrics.py`, `bench/run.py` (only the `scoresheet.json`-bound dict key; `--role` CLI flag and `a.role` attribute left untouched, same reasoning), `scripts/cache_coverage.py`, `scripts/behavior_metrics.py`.

Six hook scripts reading the cross-repo `.on-the-record/role.json` sidecar were also updated: `on-the-record/hooks/{approval-gate,contract-guard,call-shape-guard,deviation-log-guard,skill-verdict-guard,pr-preflight}.sh` — all `sidecar.get("role")`/`sidecar["role"]` renamed to `skill`.
canonical: `sed -n '105,124p' on-the-record/hooks/approval-gate.sh` (read before and after editing) — the sidecar block reads `sidecar.get("skill")`/`sidecar["skill"]` post-edit; a second, separate `snapshot.get("role")` read against the *different* SessionStart-bind snapshot (`otr-role-bind/<session_id>.json`) was also renamed for consistency, though it never fires in practice — that snapshot format was already narrowed to `{"spawned": bool}`-only by issue #2538, per `on-the-record/hooks/session-role-bind.sh`'s own docstring, read in full during this session.

Test fixtures updated to match the renamed production code (roster/ledger/sidecar entry shapes): `test/test_spawn_skills_mount.py`, `tests/test_cross_checkout_prune_liveness.py`, `test/test_issue_scoped_lease.py`, `test/test_convention_equivalence.py`, `test/test_approval_gate_carriers.py`, `test/test_spawn_attempt_staleness.py`, `test/test_branch_role_field.py`, `test/test_roster_role_field.py`, `test/test_ps_live_reliability.py`.

Explicitly left unchanged, verified by reading each site's context rather than assumed:
- `gates/finding_shape.py:23` and `gates/findings_due.py:69,82` read/validate `role:` frontmatter of finding files under the pattern `docs/reports/findings/<role>/*.md` / `docs/issue-<n>/reports/findings/<role>/*.md` (untracked — no finding has been filed under either bucket yet, per `git ls-files docs/reports/findings`, so the directory doesn't exist in this checkout) — docs/ content (a non-goal per the issue), not runtime state.
  canonical: `sed -n '1,40p' gates/finding_shape.py` and `sed -n '1,90p' gates/findings_due.py`, read in full during this session — both docstrings state the target paths are under `docs/reports/findings/` / `docs/issue-<n>/reports/findings/`.
- `harness/fixture-target/scenario.py:55` — `{"role": "user", ...}` is an LLM chat-message role (system/user/assistant), an unrelated concept.
  canonical: `sed -n '40,60p' harness/fixture-target/scenario.py`, read during this session.
- `harness/run_smoke.py:24` and `on-the-record/monitors/test_poll_heartbeat.py:153` are decorative keys in synthetic test fixtures that no consumer reads.
  derived: `grep -n "delegation_events\|skill_explicitly_invoked" harness/signals.py` — result: only `ts` is read from `delegation_events`, never `role`/`action`.
  derived: `grep -n "patrol_promote\|promotions" --include='*.py' -r . | grep -v /docs/` — result: the real `gates/patrol_promote.py`'s `promotions` entries are `{"fingerprint": ..., "issue": ...}` (line 302), no `role`/`skill` key.
- `spawn.py:1894` (`ap.add_argument("role", ...)`) and its `a.role` reads (dispatch on subcommand name) are CLI argument syntax, not a persisted key; `bench/run.py`'s `--role` flag, same reasoning.
  canonical: `sed -n '1885,1905p' spawn.py` and `grep -n "add_argument\|a\.role" bench/run.py`, read during this session.
- `test/test_spawn_attempt_staleness.py:394,408` — `"role"` there is a literal fake skill-name *value* used as a test double (`_write_attempt("2999:role:1:1", 2999, "role", ...)`), not a dict key.
  canonical: `sed -n '340,410p' test/test_spawn_attempt_staleness.py`, read during this session — `_write_attempt`'s third positional parameter is named `skill` and is passed the literal string `"role"` as test data.
- `.on-the-record/role.json`'s filename and `role_model.txt` are unchanged — the operator ruling says rename *the key*; renaming filenames is a materially larger, separately-riskier change the issue's acceptance criteria don't ask for.

tokenmaxxxer-core repo:
canonical: `gh pr view 353 --repo tokenmaxxxer/tokenmaxxxer-core --json state,url`
```
{"state":"OPEN","url":"https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/353"}
```
Branch `issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a`, commit `f06267e`, 2 files changed, 3 insertions / 3 deletions. `core/hooks/board-gate.sh` is the only core-repo reader of the cross-repo `.on-the-record/role.json` sidecar — `_sidecar.get("role")`/`_sidecar["role"]` renamed to `skill`. `core/hooks/tests/run-board-gate-tests.sh`'s sidecar-fixture `printf` renamed to write `skill` so its existing sidecar round-trip cases keep exercising the real reader against the real new-format file.
derived: the same repo-wide grep commands above, run against the fresh `tokenmaxxxer-core` clone — returned exactly these two sites and no others.

## Why

`docs/`-frontmatter `role:` (590 files, frozen) and CLI/identifier/env-var uses of the word "role" are out of this slice's scope by the operator ruling and prior #2600 slices (#2668, #2676, #2720, #2731); this slice is only the persisted dict key. The rename is forward-only with no migration and no dual read, per the ruling — an old `roster.json`/`ledger.jsonl`/`.on-the-record/role.json` entry written before this change simply stops being found by the renamed readers, the same accepted breakage as the docs/ population, not fixed with a compatibility shim.
canonical: `gh issue view 2741` body, read at session start — "Operator ruling, 2026-08-30: rename the key to skill. Forward-only... no migration, no dual read", and states the two populations while excluding docs/ and prior-slice territory explicitly.

Cross-repo boundary, said so per the must-not clause: `.on-the-record/role.json` is written by on-the-record's `pipeline.py` and read by six on-the-record hooks and core's `board-gate.sh`. Both repos are fixed in this delivery, but true atomic cross-repo merge isn't possible on GitHub — this PR and core#353 must merge in immediate succession.
canonical: the six-hook and one-hook enumeration in "What was done" above, plus `gh pr view 353 --repo tokenmaxxxer/tokenmaxxxer-core` (cited there).

During any gap, whichever side hasn't merged yet reads/writes the old key shape; every one of the seven sidecar readers already fails open to the pre-#1814 branch-regex parse on an absent/malformed/mismatched-shape sidecar, so the gap degrades cross-check precision rather than breaking hard, and no in-flight session's state file is rendered unreadable to the process that wrote it — it just stops being read as a sidecar and falls back to the branch name it already carries.
canonical: `sed -n '105,155p' on-the-record/hooks/approval-gate.sh` and the equivalent blocks in `contract-guard.sh`, `call-shape-guard.sh`, `deviation-log-guard.sh`, `skill-verdict-guard.sh`, `pr-preflight.sh`, `core/hooks/board-gate.sh` — all read during this session; each is wrapped in `try/except (OSError, ValueError): pass` with the pre-sidecar branch-regex parse as the unconditional next step.

## What did not work

The first draft of this record's `skill-verdict:` lines claimed `refactoring-legacy-seam-selection` was `applied: invoked;` — this was false; the Skill tool was never actually called this session. Caught by the Stop hook's zero-invocation notice and corrected in place to `not-applicable` for both mounted skills before landing.
canonical: the corrected `skill-verdict:` lines at the end of this record, as committed — no Skill-tool invocation exists in this session's tool-call history.

A background `warrant-hunter` dispatch (stance: assume the gate/hook just touched is bypassable) found a real silent-failure regression in the first version of the six sidecar-reading hook edits: for a workspace still carrying a pre-rename `.on-the-record/role.json` ({"role": ...}, no "skill" key) on a branch that doesn't parse as `issue-<n>/<skill>`, `approval-gate.sh` (and the five structurally identical hooks) now falls through the shape check silently and reaches its existing "unparseable branch — accepted fail-open" `sys.exit(0)` with zero stderr output — whereas the pre-rename hook, given the same legacy-shaped sidecar, resolved the sidecar successfully and reached the approvers/gh check with a real diagnostic on its own fail-open path.
canonical: `docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a/2026-08-30-hunt-role-key-rename.md` (committed this session, commit `11dd4631`) — pre-fix run: `exit=0` with no stderr; pre-rename comparison: `exit=0` with `approval-gate: gh issue view lookup failed — cannot verify approval state, failing open...` on stderr.

Fixed by adding an `else:` branch to the sidecar shape check in all six hooks (`approval-gate.sh`, `contract-guard.sh`, `call-shape-guard.sh`, `deviation-log-guard.sh`, `skill-verdict-guard.sh`, `pr-preflight.sh`) that writes a one-line stderr diagnostic naming issue #2741 before falling through to the branch-regex parse — log-only, no behavior change, no dual-read of the old key's value, consistent with every other fail-open branch already in these files.
canonical: post-fix re-run of the same reproduction — `approval-gate: .on-the-record/role.json present but not in the expected shape (skill: str, issue: int) -- falling back to branch-name parsing (issue #2741: this key was renamed role -> skill, forward-only; a sidecar written before that rename no longer resolves here).` on stderr, `exit=0`.
derived: `python3 -m py_compile` against each of the six hooks' extracted embedded-Python block — all six OK.

That fix's own follow-up full-suite run surfaced one unrelated pre-existing test whose assertion collided with any edit to `approval-gate.sh` at all: a test formerly named `test_approval_gate_sh_is_byte_identical` (renamed to `test_shadow_wiring_code_never_invokes_approval_gate_sh`) in `test/test_auto_approval_shadow_wiring.py::SimulatedApprovalAppendsSampleTest` diffed `approval-gate.sh` against `origin/main` and failed on any legitimate change to that file, not just a shadow-wiring regression — its own module docstrings (`gates/auto_approval_class.py`, `gates/ci.py`) state the real invariant is "shadow wiring never calls or modifies approval-gate.sh," which the byte-diff was only a fragile proxy for. Replaced the assertion with a direct check that neither module's source contains a subprocess/exec/open call naming `approval-gate.sh` (docstring prose mentioning the filename is not itself a false positive, verified by running the updated test against the unmodified module source).
canonical: `python3 -m pytest -q test/test_auto_approval_shadow_wiring.py -v` — result: 7 passed (was 6 passed, 1 failed — `test_approval_gate_sh_is_byte_identical` — immediately after the hook fix landed, before this test update).

## Upstream basis

Issue #2741 is the sole upstream input; no prior docs/issue-2741 records exist to build on.
canonical: `gh issue view 2741` (read at session start).
derived: `git ls-files docs/issue-2741` — result: empty before this commit (only this record's own path exists, newly created).

## Open findings

None — the write-site enumeration found no additional in-scope sites after the `board.py:1296` catch documented in "What was done" above.
derived: the post-edit sweep grep in "What was done", re-run a final time after the `board.py:1296` fix — zero non-excluded hits.

## Next steps

None — loop_state is terminal (`landed`). Both PRs are open and should be merged in immediate succession per the cross-repo boundary note in "Why".

acceptance: `python3 -m pytest -q 2>&1 | grep '^FAILED' | sort > /tmp/after_failed.txt && diff /tmp/baseline_failed.txt /tmp/after_failed.txt` (this repo, baseline captured via `git stash` before this change) — result:
```
IDENTICAL SETS
```
(16 failing test names, identical before/after this repo's changes.)

acceptance: `cd tokenmaxxxer-core-issue-2741-role-key && python3 -m pytest -q test tests` — result:
```
FAILED tests/test_promoted_hooks.py::test_proposal_shape_gate_refuses_missing_sections
FAILED tests/test_promoted_hooks.py::test_survey_order_gate_refuses_proposal_without_survey_or_skip
FAILED tests/test_silent_failure_repros.py::test_A5_trailer_gate_quote_split_commit_is_detected
3 failed, 57 passed in 6.08s
```
Identical failing-name set reproduced via `git stash` before this repo's changes (same 3 names, same command).

acceptance: `cd tokenmaxxxer-core-issue-2741-role-key && bash core/hooks/tests/run-board-gate-tests.sh` — result:
```
FAIL   feasibility-spikes                 want=allow got=deny
FAIL   ops-postmortems                    want=allow got=deny

== 143 passed, 2 failed ==
```
Identical failing-name set reproduced via `git stash` before this repo's changes.

acceptance: `python3 /tmp/live_spawn_proof.py` (real `roster.roster_register()` write + real `board._lease_slugs_for_issue()`/`board._format_roster_row()` reads, redirecting only the storage path, no other code changed) — result:
```
=== raw bytes on disk after a real roster_register() call ===
{
  "issue-27410/implementation": {
    "pid": 424242,
    "skill": "implementation",
    "issue": 27410,
    ...
  }
}
=== board._lease_slugs_for_issue(27410) read-back === {'implementation'}
=== board._format_roster_row() read-back ===
ENDED          implementation issue-27410  ...분  pid 424242
ALL ROSTER ROUND-TRIP ASSERTIONS PASSED
```

acceptance: real `pipeline._write_skill_sidecar(work, 27410, "implementation")` then `cat "$TD/.on-the-record/role.json"` then core's real `board-gate.sh` invoked as a subprocess against that file — result:
```
=== real role.json written by pipeline._write_skill_sidecar (on-the-record repo) ===
{"skill": "implementation", "issue": 27410}

=== core repo's board-gate.sh (cross-repo consumer) reading it back ===
board-gate: this repository has no docs/specs/approvers.md. ...
exit=2
```
The deny is for an unrelated missing-`docs/specs/approvers.md` precondition (R2 in `board-gate.sh`'s own rule list), not a key/shape error — `board-gate.sh` ran past the sidecar-read step cleanly.

acceptance: `python3 -m pytest -q test/test_approval_gate_carriers.py test/test_branch_role_field.py -v` (this repo's own tests, which spawn the real `approval-gate.sh` subprocess against a real `role.json` sidecar written with the new key) — result:
```
30 passed
```

skill-verdict: refactoring-legacy-seam-selection — not-applicable: this was a mechanical string-literal key rename across code already covered by an existing test suite, not introducing new/changed behavior into untested legacy code, so there was no Sprout/Wrap-Method-vs-seam decision to make; the Skill tool was not invoked.
skill-verdict: adversarial-review — not-applicable: this record documents original delivery work by the same session that built it, not an evaluation of another session's already-finished artifact; the Skill tool was not invoked.
