---
issue: 2741
role: adversarial-review-9917d82c
author: adversarial-review-9917d82c
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: on-the-record PR #2746 (76a76c928e290bd2d28ed47850b8ae7cd94aa9f6) + tokenmaxxxer-core PR #353 (ffaf0d90628309264ed17991104afeb63cc37bce)
type: verification
breaking: false
verdict: approve
loop_state: landed
upstream:
  - path: docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-bd0ced79.md
    sha: 76a76c928e290bd2d28ed47850b8ae7cd94aa9f6
---

# issue-2741 — adversarial-review-9917d82c record

## What was done

Independent verification of PR #2746 (on-the-record) and its companion tokenmaxxxer-core#353, the delivery that responds to PR #2743's CHANGES verdict and issue #2741's 2026-08-30 scope-correction comment. Read `gh issue view 2741 --comments` and `gh pr view 2743 --comments` first (per instruction), then re-derived every claim independently rather than trusting PR #2746's own record.

canonical: `gh issue view 2741 --json body` — full Ask/Acceptance/Non-goals text, read at session start.
canonical: `gh pr view 2743 --comments` — CHANGES ruling naming `relay.py:267`/`gates/flows.py:36` (trailer) and `gates/patrol_board.py`/`gates/patrol_promote.py` (labels) in scope.

**1. Write-site enumeration, re-derived with my own command (not the PR's).**
derived: `git worktree add /tmp/otr-pr2746 pr-2746-review && git worktree add /tmp/otr-main origin/main`, then `command grep -rnE '\.get\([\x27"]role[\x27"]|\[[\x27"]role[\x27"]\]|[\x27"]role[\x27"] *:' --include=*.py --include=*.sh . | grep -v /docs/` run against both trees. Bare-word `role` count outside docs/ (`--include=*.py --include=*.sh`): 1309 on `origin/main` → 1099 on the PR branch (both same command, same worktree pair). `on-the-record/directive` stays byte-identical at 53162 bytes both sides (`du -sb`).
derived: repo-wide sweep for the true in-scope population's remaining write/read sites, PR branch — result: zero. Every non-docs hit that DOES remain (`gates/findings_due.py:69`, `harness/run_smoke.py:24`, `harness/fixture-target/scenario.py:55`, `on-the-record/monitors/test_poll_heartbeat.py:153`) is one of the residuals both PR #2743's independent verifications (`adversarial-review-a7c51853.md`, `adversarial-review-6a02d514.md`) already vetted as out of scope (docs/-frontmatter population, LLM chat-message `role`, or decorative/no-consumer). One apparent extra hit, `runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh:865`, is this session's own local rulebook mount — `git check-ignore -v` confirms `runs/` is gitignored and `git ls-tree -r origin/main` shows 0 tracked files under it; not repo content, dismissed.

**2. Reverse direction / dual-read check.**
derived: `command grep -rnE '\.get\([\x27"]role[\x27"]\).*\.get\([\x27"]skill[\x27"]\)|...'` (both orderings) across the whole PR-branch tree — zero hits. `gates/flows.py` carries exactly one trailer regex (`_ROLE_TRAILER_RE = re.compile(r"^skill:\s*([a-z0-9-]+)\s*$")`), read directly from source, not the PR's demo.

**3. PR-body trailer round-trip, both halves read together.**
Read `relay.py:267` (`body = ... f"...\n\nskill: {skill}"`) and `gates/flows.py:33-48` (`_role_from_pr()` / `_ROLE_TRAILER_RE`) side by side from source. Single write, single read, no fallback alias.

**4. GitHub label rename + its reader.**
Read `gates/patrol_board.py:229` (`labels = f"{LABEL_BOARD},skill:{skill}"`, the `gh api -X GET ... -f labels=...` read-back query itself), `:332,337` (`gh label create`/`gh issue create --label skill:{skill}`), and `gates/patrol_promote.py:236,242`. Consistent `skill:{skill}` on every write and the one read-back call site; no other `--label role:`/`--label skill:` caller exists (`grep -rn -- '--label'`).

**5. Cross-repo fail-open, constructed (not read off the PR's demo).**
derived: extracted the exact shape-check condition from `origin/main`'s `core/hooks/board-gate.sh` (`isinstance(_sidecar.get("role"), str)`) and from PR-353's version (`isinstance(_sidecar.get("skill"), str)`), then ran both against synthetic sidecar dicts representing the two possible one-repo-merged intermediate states (on-the-record merged / core not yet; core merged / on-the-record not yet). Both directions resolve to `FAIL-OPEN (falls through to branch-regex parsing)`, no exception. Re-ran the check with the REAL scripts, not simulated logic: wrote `/tmp/roundtrip_check.py`/`roundtrip_check2.py`, called the real `pipeline._write_skill_sidecar()` to produce a genuine `{"skill": "implementation", "issue": 2741}` sidecar, then invoked the real `on-the-record/hooks/approval-gate.sh` subprocess (with `CLAUDE_SKILL` set, `tool_name: Write`, a `src/` path — the hook's own no-op gate requires this shape) against a hand-built pre-rename-format sidecar (`{"role": ...}`). Result: the real hook printed exactly `approval-gate: .on-the-record/role.json present but not in the expected shape (skill: str, issue: int) -- falling back to branch-name parsing (issue #2741: this key was renamed role -> skill, forward-only; a sidecar written before that rename no longer resolves here).` and exited 0 — fail-open confirmed live, not read off a comment.
derived: `bash core/hooks/tests/run-board-gate-tests.sh` in `/tmp/core-pr353` vs `/tmp/core-main` — both `143 passed, 2 failed` (2 pre-existing, unrelated `want=allow got=deny`), and the `corrupt-sidecar-falls-back` case passes on the PR side.

**6. docs/ untouched.**
derived: `git diff --stat origin/main HEAD -- docs/` on the PR branch — 3 files, all new, under the PR branch's `docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-bd0ced79` tree (that path lives only on PR #2746's branch, not this record's own working tree — untracked here); 203 insertions, 0 deletions, 0 modified existing files.

**7. The two contested-scope sites — adjudicated independently, one disagreement with the framing given to me.**
`gates/finding_shape.py:23` (`_REQUIRED_FRONTMATTER = ("role", ...)`) and `gates/findings_due.py:69` (`due.append({"role": skill, ...})`) both operate on `docs/reports/findings/<role>/<date>-<slug>.md` frontmatter/directory-name — this is exactly the issue's own population 1: "**Record frontmatter under `docs/` — 590 files**... Frozen history, never edited, so their key stays `role:` forever," reinforced by the Acceptance "must not" clause ("never edit, rename, or migrate anything under `docs/`") and Non-goals ("`docs/` content in either repo").
canonical: `gh issue view 2741 --json body` — read directly, quoted verbatim above.
This is the issue's own text, not the scope-correction ruling — the ruling only expanded population 2 (PR-body trailer, GitHub labels) to cover non-docs mediums; it never touched population 1. **I disagree with the "in scope" framing given for `finding_shape.py`** — both it and `findings_due.py` are population 1, correctly left untouched by PR #2746, and this matches both of PR #2743's independent verifications, which unanimously called the same two sites out of scope before the scope-correction even existed. `docs/reports/findings/` does not exist in this tree (confirmed: `find` errors "no such file or directory") and `docs/specs/enforcement-boundary.md:96` documents `finding_shape.py` as "not wired into any `PreToolUse`/`Stop` hook or `gates/ci.py` in this delivery" — genuinely inert on top of being out of scope.

**8. Failing-test sets, both repos, as sets of names.**
derived (on-the-record): `python3 -m pytest -q` in `/tmp/otr-pr2746` and `/tmp/otr-main`, `grep '^FAILED' | sort` each, `diff` — empty diff, 16 identical names both sides (`539 passed, 6 xfailed` both).
derived (core, pytest): same in `/tmp/core-pr353` (HEAD `ffaf0d90`) vs `/tmp/core-main` (HEAD `8f956226`, confirmed == `origin/main` tip via `git rev-parse`) — empty diff, 3 identical names (`test_proposal_shape_gate_refuses_missing_sections`, `test_survey_order_gate_refuses_proposal_without_survey_or_skip`, `test_A5_trailer_gate_quote_split_commit_is_detected`), `79 passed` both.
derived (core, board-gate shell suite): `143 passed, 2 failed` both sides, same 2 names (`feasibility-spikes`, `ops-postmortems`).

**9. No-bug sweep on the diff itself.**
derived: `git diff origin/main HEAD -- . ':!docs' ':!test' ':!tests'`, every `+`/`-` line filtered to those NOT containing `role`/`skill` — the only survivors are the new `else: sys.stderr.write(...)` diagnostic blocks (six on-the-record hooks) and one condition split in `contract-guard.sh` (and its siblings): the old code folded `sidecar["issue"] == issue` into the same `and`-chain as the shape check, so an issue-number mismatch (a normal, expected state — stale sidecar from a different issue) produced the same "shape mismatch" diagnostic as genuine corruption; the new code checks shape first, issue-match second, so the diagnostic fires only on real shape corruption. Verified this doesn't change resolved-`skill` behavior (both paths still fall through to branch-regex on non-match) and re-ran `corrupt-sidecar-falls-back` — passes. Not a defect; a precision improvement bundled into the same commit that had to touch this block anyway for the key rename.

**10. Four standing invariants, checked explicitly.**
- Role axis returning in reshaped form: no — zero dual-read/alias hits (item 2), word-count decreased consistently main→PR, no new wrapper/union key found.
- New bug: no — item 9's sweep plus full test-suite parity (item 8).
- Overhead (tokens/turns/context bytes/runtime): no increase — `on-the-record/directive` byte-identical (53162, item 1); PR touches no directive/prompt-assembly file; on-the-record suite runtime ~7s both sides; no new loops or expanded generated text found.
- Monitor/watch machinery: intact — `python3 -m pytest -q -k 'watch or monitor or poll_heartbeat'` → `45 passed, 0 failed` on the PR branch; `git diff --stat` shows zero files under `on-the-record/monitors/` touched; the only monitor-adjacent file in the diff, `watchdog.py`, is a single literal `e.get("role")`→`e.get("skill")` rename with the roster-events population it reads.

## Why

canonical: `gh issue view 2741 --json body,comments` — read at session start; the population-1/population-2 split and the "frozen forever" / "must not... under docs/" language quoted in item 7 above comes directly from this body text, not from the scope-correction comment.

The task's own framing warned that "the population is a key we WRITE and later PARSE BACK, whatever medium stores it — not a dict key in a .py file" was the orchestrator's prior defect, and told me to re-derive rather than restate. I read every write and read site from source myself, in both repos, and constructed the cross-repo fail-open scenario from the actual shape-check code rather than trusting either PR's own demonstration of it. Where the task handed me a specific disagreement to adjudicate (`gates/finding_shape.py`), I went to the issue's own body text rather than the ruling comment, and found the issue itself settles it: population 1 (docs/ frontmatter, 590 files) is explicitly frozen forever, independent of the population-2 medium correction. That text was decisive enough that I disagree with the "in scope" framing I was given for that one site.

## What did not work

None — every claim in PR #2746's own record either reproduced exactly under my own independently-constructed commands, or (for the two contested sites) resolved the same way under my own re-derivation from the issue's primary text.

## Upstream basis

- `gh issue view 2741` (Ask, Acceptance, Non-goals, and the 2026-08-30T17:26:02Z scope-correction comment) — read at session start.
- `gh pr view 2743 --comments` — the CHANGES ruling this PR executes.
- PR #2746, `https://github.com/tokenmaxxxer/on-the-record/pull/2746` (HEAD `76a76c92`) and its own record (path cited in frontmatter `upstream`, lives only on that PR's branch).
- core#353, `https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/353` (HEAD `ffaf0d90`).
- Both PR #2743 independent-verification records (`adversarial-review-a7c51853.md`, `adversarial-review-6a02d514.md`, both already committed in this repo's history) — read for the residual-site classification they already established, re-verified rather than assumed still true.

## Open findings

None. PR #2746 + core#353 correctly execute the scope-correction ruling, all four standing invariants hold, and the two sites flagged for my own adjudication are both correctly left untouched (disagreeing with the "in scope" framing for `gates/finding_shape.py` specifically — see item 7 above).

## Next steps

None — `loop_state` is terminal (`landed`). This is a verification-only delivery; PR #2746 and core#353 are ready to merge in immediate succession as their own records already note.

## Acceptance

acceptance: on-the-record failing-test-set parity — `python3 -m pytest -q 2>&1 | grep '^FAILED' | sort` in `/tmp/otr-pr2746` vs `/tmp/otr-main` (worktrees off `pr-2746-review` and `origin/main`) — result:
```
IDENTICAL SETS (16 names, 539 passed, 6 xfailed both sides)
```

acceptance: core pytest-suite parity — same command in `/tmp/core-pr353` (PR #353 HEAD `ffaf0d90`) vs `/tmp/core-main` (`origin/main`, confirmed `git rev-parse origin/main` == `8f956226`) — result:
```
IDENTICAL SETS (3 names, 79 passed both sides)
```

acceptance: core board-gate shell-test-suite parity — `bash core/hooks/tests/run-board-gate-tests.sh` both worktrees — result:
```
143 passed, 2 failed, both sides identical (same 2 pre-existing names); corrupt-sidecar-falls-back: PASS
```

acceptance: real round-trip, sidecar write+read — `python3 /tmp/roundtrip_check.py` (real `pipeline._write_skill_sidecar` + real `on-the-record/hooks/approval-gate.sh` subprocess) — result:
```
{"skill": "implementation", "issue": 2741}
rc= 0
```

acceptance: real fail-open, pre-rename-format sidecar against the real post-rename hook — `python3 /tmp/roundtrip_check2.py` — result:
```
stderr: approval-gate: .on-the-record/role.json present but not in the expected shape (skill: str, issue: int) -- falling back to branch-name parsing (issue #2741: this key was renamed role -> skill, forward-only; a sidecar written before that rename no longer resolves here).
rc= 0 (no crash/traceback = fail-open confirmed)
```

acceptance: docs/ untouched — `git diff --stat origin/main HEAD -- docs/` on the PR branch — result: 3 new files under PR #2746's own `docs/issue-2741/reports/` tree, 0 modified existing docs files.

acceptance: `on-the-record/directive` byte count, both sides — `du -sb on-the-record/directive` — result: `53162` both `origin/main` and the PR branch (byte-identical).

acceptance: monitor/watch machinery — `python3 -m pytest -q -k 'watch or monitor or poll_heartbeat'` on the PR branch — result: `45 passed in 3.83s`.

skill-verdict: adversarial-review — applied: invoked; this entire record is the skill's output — independent construction of every claim (write-site enumeration, both round-trips, cross-repo fail-open in both directions, both repos' failing-test-set diffs) rather than adopting PR #2746's own record or the task's given framing, including one explicit disagreement (item 7) with a framing I was handed.
canonical: `gh issue view 2741`, `gh pr view 2743 --comments`, `gh pr view 2746`, `gh pr view 353 --repo tokenmaxxxer/tokenmaxxxer-core` — all read at session start before forming any conclusion.
other mounted skills: not triggered (work-in-english — this record, all commit messages, and all commands/scripts are in English already, matching repo convention; no other project skill's trigger condition matched a verification-only task).
