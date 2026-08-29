---
issue: 2670
role: refactoring-legacy-seam-selection+silent-failure-audit-d6377c1c
author: refactoring-legacy-seam-selection+silent-failure-audit-d6377c1c
skills: refactoring-legacy-seam-selection (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: pipeline.py
    sha: same-commit
  - path: on-the-record/hooks/approval-gate.sh
    sha: same-commit
  - path: on-the-record/hooks/deviation-log-guard.sh
    sha: same-commit
  - path: spawn.py
    sha: same-commit
type: refactor
breaking: true
verdict: renames CLAUDE_ROLE to CLAUDE_SKILL, literal-token, both repos, write side and same-repo read side together (on-the-record) plus the companion core PR (tokenmaxxxer-core#348) for core's read side. 0 occurrences of CLAUDE_ROLE remain outside docs/ in either repo (was 60/22 files here, 200/44 files in core). No compatibility alias, no dual read, shipped in either PR. Test suites (pytest -m "not slow", tests/run-orchestrate-tests.sh, tests/test_stop_gate.sh here; core/hooks/tests/run-all.sh in core) report byte-identical pass/fail summaries before and after -- acceptance: `python3 -m pytest test/ -m "not slow" -q` (before, via git stash, vs after) -- result: identical 15-failure set both times (`diff` of sorted FAILED lines produced no output). The two-repo merge-order window this creates is disclosed, not eliminated -- see Open findings #1.
loop_state: landed
upstream:
  - path: https://github.com/tokenmaxxxer/on-the-record/issues/2670
    sha:
---

# issue-2670 — refactoring-legacy-seam-selection+silent-failure-audit-d6377c1c record

## What was done

Renamed the env var `CLAUDE_ROLE` to `CLAUDE_SKILL` everywhere outside `docs/` in both repos — the one env var #2600's first slice (PR #2668) found and deliberately deferred, because it is written by the spawner (`pipeline.py:722`) and read by the gates every spawned session, including the one doing the renaming, runs under.

**Name chosen: `CLAUDE_SKILL`.** Follows the precedent #2600's PR #2668 already set 7-for-7 on the sibling env vars in the same sweep: `MUSTER_ROLE_MODEL` -> `MUSTER_SKILL_MODEL`, `OTR_ROLE_BIND_STATE_DIR` -> `OTR_SKILL_BIND_STATE_DIR` (on-the-record), `PG_ROLE`/`HT_ROLE`/`TRAILER_GATE_ROLE`/`RF_ROLE`/`SOG_ROLE` -> `PG_SKILL`/`HT_SKILL`/`TRAILER_GATE_SKILL`/`RF_SKILL`/`SOG_SKILL` (core, `tokenmaxxxer-core#347`).
canonical: `gh pr view 2668` body, read live this session — "`MUSTER_ROLE_MODEL` -> `MUSTER_SKILL_MODEL`, `OTR_ROLE_BIND_STATE_DIR` -> `OTR_SKILL_BIND_STATE_DIR` here; `PG_ROLE`, `HT_ROLE`, `TRAILER_GATE_ROLE`, `RF_ROLE`, `SOG_ROLE` in the companion tokenmaxxxer-core PR".

Rejected alternative: a bespoke name (`CLAUDE_SUBJECT`, `CLAUDE_SESSION_SLUG`) that more precisely names the value's actual shape — a `+`-joined skill-name compound plus a lease-disambiguator hash (e.g. `refactoring-legacy-seam-selection+silent-failure-audit-d6377c1c`, this session's own `CLAUDE_ROLE`/`CLAUDE_SKILL` value), not a bare skill name. Rejected for consistency: the same imprecision already exists in `OTR_SKILL_BIND_STATE_DIR` (a state-dir path, not a skill) and `SOG_SKILL` (`survey-order-gate.sh:70` — exports it from `CLAUDE_ROLE` as a session-identity scoping key, not a skill selector), both landed under `#2600` without dispute. A seventh bespoke name where six prior sites already accepted the same imprecision under `SKILL` would fragment the vocabulary for no consumer-visible gain.

**Scope: the literal token only**, not the broader `role`-named identifier surface (`role_settings()`, `resolved_role_model()`, `role.json`, etc.) — those are #2139's relic-sweep scope per #2600's own Non-goals, not #2670's.
canonical: `gh issue view 2593` body, Non-goals section, read live this session — "Internal variable names never shown to a consumer (`CLAUDE_ROLE`, `board.py`'s local `roles` binding). They belong to the relic sweep (#2139) unless the design happens to touch them."

Confirmed no compound variant of the token exists in either repo:
derived: `grep -oE 'CLAUDE_ROLE[A-Z_]*' /tmp/otr_claude_role_lines.txt /tmp/core_claude_role_lines.txt | cut -d: -f2- | sort -u` — result: single line of output, `CLAUDE_ROLE` — so a global literal-string substitution is safe and mechanical, not a per-site judgment call.

**Counts, derived live this session, both repos, before any edit:**
derived: `git ls-files | grep -v '^docs/|^runs/|^skill-repository/' | xargs grep -l 'CLAUDE_ROLE' | wc -l` and the occurrence-count variant with `grep -o | wc -l`, run in each repo's checkout separately.
- on-the-record (excl. `docs/`, `runs/`, `skill-repository/`): 22 files, 60 occurrences.
- tokenmaxxxer-core (excl. `docs/`): 44 files, 200 occurrences.
- Total: 66 files, 260 occurrences. (The issue's own corrected count, from its most recent comment, is 65 files / 254 occurrences — the ~6-occurrence drift is time elapsed since that comment landed, not a methodology difference; both counts used `grep -rl`/`grep -ro` outside `docs/`.)

After the rename:
acceptance: `grep -rn 'CLAUDE_ROLE' --exclude-dir=.git --exclude-dir=docs .` in each repo — result:
```
0
```
in both repos (on-the-record checked at this record's own commit; core checked at `tokenmaxxxer-core#348`'s branch tip, commit `434cfdd`).

**Write side + same-repo read side, one commit.** `pipeline.py:722`'s `env = {"CLAUDE_ROLE": role, ...}` and every on-the-record hook that reads it (`on-the-record/hooks/approval-gate.sh`, `deviation-log-guard.sh`, plus the shell test harnesses that exercise them) land together in this PR's single commit — the issue's must-not ("do not rename the read side and the write side in separate PRs") read as a same-repo constraint, since no single commit can span two remotes. Core's read side (no writer of its own — it only ever reads whatever `pipeline.py` puts in the process environment) is `tokenmaxxxer-core#348`, opened this session against `tokenmaxxxer/tokenmaxxxer-core`.
canonical: `gh pr create --repo tokenmaxxxer/tokenmaxxxer-core ...` run live this session, stdout `https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/348` — the cross-repo PR-creation capability issue #2669/PR #2706 landed (merged, per `gh pr view 2706`, hours before this session started).

## Why

**Not-set branch enumerated before the rename** (acceptance bullet 4), read from `HEAD` (pre-rename) for every real read site — `os.environ.get/[...]`, `${CLAUDE_ROLE...}`, never comment-only mentions:

| file | line(s) | not-set behavior | why |
|---|---|---|---|
| on-the-record/hooks/approval-gate.sh | 62 | NO-OP, silent (`exit 0`, no stderr) | `[ -n "${CLAUDE_ROLE:-}" ] \|\| exit 0` — the issue's own opening citation; no log line, unlike this same file's other fail-open branches (a `gh`-lookup failure, further down the same file) which do write a stderr note |
| on-the-record/hooks/deviation-log-guard.sh | 166 | NO-OP, degraded scan path | `.get()`, never crashes; only reached when both the `.on-the-record/role.json` sidecar and the branch-regex parse already failed to name a role; worst case is `additionalContext`-advisory, can never block a Stop |
| on-the-record/hooks/session-role-bind.sh | — | N/A (out of scope) | no real read exists at `HEAD` — per issue #2538 ("role retirement stage 6B") this hook already stopped reading the role value and gates purely on `TOKENMAXXXER_SPAWNED` |
| core/hooks/approval-gate.sh | 85, 142 | CRASH-THEN-DENY | presence check is `OR(TOKENMAXXXER_SPAWNED, CLAUDE_ROLE)` (l.85) — `TOKENMAXXXER_SPAWNED` alone keeps this open; the next real read (`os.environ["CLAUDE_ROLE"].strip()`, l.142, bracket access) then `KeyError`s, uncaught, non-0/non-2 exit remapped to `exit 2` by the file's own `trap` |
| core/hooks/gh-guard.sh | 40, 91 | CRASH-THEN-DENY, same shape | same `OR(TOKENMAXXXER_SPAWNED, CLAUDE_ROLE)` presence gate, bracket-access `os.environ["CLAUDE_ROLE"].strip()`, a top-of-file `trap`, and a second explicit non-0/non-2 -> `exit 2` remap immediately before the final exit, later in the same file |
| core/hooks/directive.sh | 21, 28 | NO-OP, content bug not enforcement gap | `role="${CLAUDE_ROLE:-}"` then `OR(TOKENMAXXXER_SPAWNED, role)` — if `TOKENMAXXXER_SPAWNED` alone is set, prints the directive with an empty role name; this hook only ever `exit 0`s (SessionStart, informational), never denies |
| core/hooks/lib/role-directive.sh | 33, 38 | NO-OP, same content-bug shape as directive.sh | no deny path in this function at all |
| core/hooks/handbook-trigger-gate.sh | 28 | NO-OP, fully inert on enforcement | `role` is a cosmetic message prefix only; every `deny()` in this file is itself advisory `exit 0` (issue #282 DEMOTE) |
| core/hooks/proposal-shape-gate.sh | 14 | NO-OP, fully inert | literal default `${CLAUDE_ROLE:-proposal-shape}` feeds only the bash-level advisory `deny()` prefix; the real python judge hardcodes its own prefix independent of this var |
| core/hooks/record-fields-gate.sh | 66, 71 | NO-OP despite reading as a deny | this file's `deny()` is itself `exit 0` (issue #282 DEMOTE) — the "refused" stderr wording does not block the tool call |
| core/hooks/record-shape-gate.sh | 66 | NO-OP, completely inert | literal default `${CLAUDE_ROLE:-record-shape}`; not even passed into the python judge's env; used only as an advisory-`deny()` prefix that never differs from the judge's own hardcoded prefix |
| core/hooks/survey-order-gate.sh | 70 | NO-OP overall, changes which file is checked | absence makes the judge fall back to `docs/issue-<n>/reports/implementation/survey.md`; verdict path is advisory `exit 0` (issue #282 DEMOTE) regardless |
| core/hooks/trailer-gate.sh | 29 | NO-OP, cosmetic default only | falls back to literal `"trailer-gate"`; the Subject-trailer check is role-blind by design (own comment) and `deny()` is advisory `exit 0` (issue #282 DEMOTE) except unrelated internal-error crashes |
| core/hooks/board-gate.sh | 735, 819 | BIMODAL — real DENY for `docs/issue-<n>/` writes, NO-OP otherwise | `.get()`, never crashes; R3 is a genuine `sys.exit(2)`-shaped `deny("a write under docs/issue-<n>/ from a session with no CLAUDE_ROLE...")`, gated on the write target being under the issue tree — this is R3 doing its designed job (a non-role session may not write the board), not a rename hazard |

canonical: two rows re-verified independently this session against raw source, beyond the background research agent that produced the full table (agent prompt and full per-file findings on record in this session's transcript): `git show HEAD:core/hooks/gh-guard.sh` (confirming the `trap` + explicit `rc` check + bracket-access read, lines 30/40/91/175-178) and `git show HEAD:core/hooks/board-gate.sh` (confirming the `.get()` read and R3's `deny()` call, lines 735/812-820) — both commands run directly in this session, output inspected line-by-line, not taken on the agent's summary alone. The `on-the-record/hooks/approval-gate.sh` l.62 and `session-role-bind.sh` rows were read directly via the `Read` tool on those files at the start of this session, before any edit.

**Why "atomic" cannot mean simultaneous, and what it means instead.** Two independently-merged repos cannot land in the same git operation — there is no commit that spans both remotes, so a merge-order window between the two PRs is structurally unavoidable, in either order. The table above shows what that window actually does: `core/hooks/approval-gate.sh` and `core/hooks/gh-guard.sh`'s `TOKENMAXXXER_SPAWNED`-still-set-but-role-var-absent state is not the same as either file's designed not-set branch — it is a third, unintended state (a spawner that sets one of two paired vars but not the other), and it crashes to a hard `exit 2`, not the silent `exit 0` the issue's own opening paragraph warns about. That is a real, disclosed cost of this rename's sequencing (every Write/Edit and every `gh`/`git push`-to-main call denied, in both repos, for any session spawned in the gap) — but it is the honest consequence of the issue's own must-not (no alias, no dual read), not a gap this record is hiding. A dual-read shim would close the window; the issue explicitly forbids shipping one. The two PRs are cross-linked (this PR's body links `tokenmaxxxer-core#348`; that PR's body links back) with the window and its blast radius named in both, so whoever merges them can choose to do so back-to-back rather than discover the window by hitting it.

## What did not work

None.

## Rationale for deviations

**"Spawn a session end to end and show it reaching a PR" was not performed as a live nested Claude Code session.**
canonical: `docs/handbooks/northpole-harness.md` and `harness/README.md`, read live this session — the harness's own steady-state scenario documents "Launching a live Claude Code session is an integration point the operator wires themselves" (README.md, driver.py section) and needs a throwaway private fixture-host repo plus a scoped `NORTHPOLE_HARNESS_GH_TOKEN`, neither present nor appropriate to provision from inside this headless delivery turn.

Launching a second, independently-billed, autonomous agentic session with real GitHub side effects is a materially different, riskier action than this session's own `CORE_BUILD_NOW=1` delivery authorization covers — that authorization is for this session's own direct delivery, not for spawning further paid sessions with external side effects, and no user is reachable mid-turn to confirm one.

What was executed instead, as the closest safe, citable substitute:

acceptance: `python3 -c "import inspect, pipeline; print(inspect.getsource(pipeline.spawn_cmd))"` (env-dict slice) — result:
```
env = {"CLAUDE_SKILL": role, "TOKENMAXXXER_SPAWNED": "1",
```
the literal code path a real spawn would execute, not a description of it.

acceptance: `bash tests/run-orchestrate-tests.sh`, run before (`git stash`) and after this rename — result, identical both times:
```
FAIL   directive-injects                  want=inject got=none
FAIL   guard-docs-in-board                want=deny got=allow
FAIL   guard-src-in-board                 want=deny got=allow
FAIL   guard-tests-in-board               want=deny got=allow
FAIL   guard-nonboard-repo                want=deny got=allow
FAIL   guard-scratch-not-exempt           want=deny got=allow
FAIL   guard-missing-file-path            want=deny got=allow
== 6 passed, 7 failed ==
```
This suite exercises `on-the-record/hooks/directive.sh` and `deliverable-guard.sh` with `CLAUDE_SKILL` unset vs. `CLAUDE_SKILL=qa` set (`directive-silent-for-roles`, `guard-approvers-ok` both pass, both runs) — the pass/refuse pair on those two gates, byte-identical pre/post rename; the 7 `FAIL` lines above are pre-existing, unrelated to `CLAUDE_ROLE`/`CLAUDE_SKILL`.

acceptance: `bash tests/test_stop_gate.sh`, run before and after — result, identical both times:
```
FAIL   missing-risk-clause-caught         want=risk/tradeoff statement got=
pass=3 fail=1
```
`role-session-passthrough` (CLAUDE_SKILL set) and the CLAUDE_SKILL-unset case both pass, both runs — a second pass/refuse pair, on `stop-gate.sh`, byte-identical pre/post rename.

acceptance: `bash core/hooks/tests/run-all.sh`, run before (`git stash`) and after this rename in the core checkout, each run's `pass=N fail=N`/`N passed, N failed` summary lines extracted and diffed — result:
```
IDENTICAL SUMMARY LINES
```
(`diff` of the two summary-line sets produced no output; includes `run-approval-gate-tests.sh` (143 passed / 2 failed both times), `run-gh-guard-tests.sh` (65 passed / 2 failed both times), `run-board-gate-tests.sh` (54 passed / 0 failed both times), `run-role-gates-tests.sh` (83 passed / 0 failed both times) — the three gates named in the Why table above, all covered by this suite's own pass/refuse fixtures, all unchanged.)

This is disclosed as a deviation from the literal bullet, not omitted.

**The merge-order window (Why, last paragraph) is a second disclosed deviation** from a naive reading of "atomic" as "no window at all" — it is the necessary consequence of honoring the issue's own must-not (no alias, no dual read) across two repos that cannot merge in one operation. Mitigation is operational, not code: merge both PRs back-to-back, no session spawned in between.

## Upstream basis

- Issue #2670 itself (this record's subject), including its follow-up comment correcting the size to 254 occurrences / 65 files.
  canonical: `gh issue view 2670 --comments`, read live this session.
- `#2600` (retire the word itself) and its first slice, `PR #2668`.
  canonical: `gh issue view 2600` and `gh pr view 2668 --json body,title`, read live this session — source of the 7-for-7 `ROLE`->`SKILL` naming precedent this record reuses, and of the reasoning `CLAUDE_ROLE` was originally deferred (`pipeline.py:722` sets it into the deferring session's own process environment).
- `#2593` (the role axis survived as 'record kind').
  canonical: `gh issue view 2593`, read live this session — confirms `CLAUDE_ROLE` was an explicit Non-goal there, i.e. this rename's narrow scope is consistent with, not a re-litigation of, that boundary.
- `#2669` / `PR #2706` (merged before this session started) — the cross-repo `gh pr create` capability this session used to open `tokenmaxxxer-core#348` directly, rather than pushing a branch and asking a human to open it.
  canonical: `gh pr view 2706 --json body,files`, read live this session, plus this session's own `gh pr create --repo tokenmaxxxer/tokenmaxxxer-core ...` call succeeding (see What was done).

## Open findings

1. **The merge-order window is disclosed, not closed** — see Why and Rationale for deviations above.
   canonical: same table and paragraph, `## Why`, this record.
   Resolution path: whoever merges `tokenmaxxxer-core#348` and this PR should merge them back-to-back, with no session spawn in between; this is an operational note in both PR bodies, not a code change, since no code-level fix exists that doesn't reintroduce the alias/dual-read the issue forbids.
2. **Cross-repo PR creation, executed live.**
   acceptance: `gh pr create --repo tokenmaxxxer/tokenmaxxxer-core --title ... --body-file ... --base main --head issue-2670/...` — result:
   ```
   https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/348
   ```
   Confirms issue #2669/PR #2706's fix (merged hours before this session started) works for a legitimate cross-repo delivery, not just the adversarial-denial cases that PR's own tests covered. No further action needed; noted as a positive finding since this is the first real-world use of that capability outside its own test suite.
3. **A live nested spawn-to-PR was not executed** — see Rationale for deviations. No further action from this record; a future session with an explicitly provisioned fixture host/token and operator sign-off on launching a second paid session could close this, but that is a distinct authorization this session did not have.

## Next steps

None — `loop_state: landed`. Both PRs (`tokenmaxxxer/on-the-record`, this one; `tokenmaxxxer/tokenmaxxxer-core#348`) are open; the issue closes only once both merge, per the `Part of #2670` / `Advances #2670` trailer convention for intentional partial delivery.

## Skill verdicts

skill-verdict: refactoring-legacy-seam-selection — applied: invoked; rule 7 (read the surrounding legacy code for hidden rules before choosing a seam) drove reading every gate's actual not-set-branch code rather than assuming from file/variable names what each one does (e.g. most core gates' `deny()` calls are advisory `exit 0` under issue #282's DEMOTE, discovered only by reading, not assumable); rule 6 (narrow the seam to the smallest enclosing scope) drove keeping this rename to the literal `CLAUDE_ROLE` token only, not the broader `role`-named identifier surface (`role_settings()`, `role.json`, etc.) that #2600/#2593 already carved out as separate scope.

skill-verdict: silent-failure-audit — applied: invoked; the skill's Handled/Silently-Absorbed/Unreachable classification is exactly the frame the acceptance's "not-set branch of every gate" bullet needed — e.g. `on-the-record/hooks/approval-gate.sh:62`'s bare `exit 0` on CLAUDE_ROLE-absence is a Silently Absorbed pattern (no log, unlike this same file's other fail-open branches which do write a stderr note), while `core/hooks/gh-guard.sh`'s crash-then-deny is closer to Unreachable-that-actually-triggers under the specific mid-rename state this record's sequencing analysis depends on.

skill-verdict: work-in-english — applied: invoked; every commit message, both PR bodies, this record, and both cross-repo/issue comments were written in English throughout this session, consistent with the skill's routing rule (repo-bound exhaust to English) — the only Korean in this delivery is the final user-facing summary, per the skill's own split.
