---
issue: 2139
role: adversarial-review-6cda09d1
author: adversarial-review-6cda09d1
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # this record independently verifies PR #2869's own deliverable
loop_state: landed
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/2869
    sha: 190321de059bf8b12de9cb2f943e8f8233f51ad2
---

# issue-2139 — adversarial-review-6cda09d1 record

## What was done

Independent verification of PR #2869 (issue #2139's relic-sweep batch), re-derived rather than restated. Fetched the PR head (`git fetch origin pull/2869/head:pr2869-check`) into a worktree at `/tmp/pr2869-worktree`, diffed it against my own `origin/main` checkout, and attacked the PR's central claim — "every change is mechanical and behavior-preserving" — at the five weak points named in the task: renamed trace fields, test-assertion completeness, keyword-passed renamed params, the directive-prose site, and the two role-noun survivals, plus a direct trace of the PR's own reported (not-fixed) `roster_kill()` finding and a re-run of all four invariants.

canonical: `gh pr view 2869 --repo tokenmaxxxer/on-the-record --json title,body,files,commits,url,headRefName,baseRefName` — read this turn (state OPEN, mergedAt null, head 0562882d on 190321de).

**1. Trace-field consumer sweep — found ONE real, reachable consumer the PR's own test-fix pass missed.**
`_append_panel_turn()` (consult.py:1608) writes `f"- {ts} | skill={skill} | ..."` (was `role={skill}`) to `docs/issue-<n>/reports/panel/<slug>.md`. `harness/fixture-concurrent-judgment/test_panel.py:51-52` asserts the OLD literal shape (`assert "role=qa" in text`, `assert "role=review" in text`) against exactly that file's content, and was NOT among the two test files this PR fixed (`test/test_consult_trace_commit.py`, `test/test_ps_live_reliability.py`).

derived: reproduced directly —
```
$ cd on-the-record (origin/main, pre-PR) && python3 -m pytest harness/fixture-concurrent-judgment/test_panel.py -q
2 passed in 0.79s
$ cd /tmp/pr2869-worktree (PR #2869 head) && python3 -m pytest harness/fixture-concurrent-judgment/test_panel.py -q
FAILED harness/fixture-concurrent-judgment/test_panel.py::test_panel_live_exchange_records_position_rebuttal_and_verdict
1 failed, 1 passed in 0.79s
AssertionError: assert 'role=qa' in "...skill=qa | position | ..."
```
The reason the PR's own Invariant 2 (`python3 -m pytest test/ -q`, both trees: `15 failed, 441 passed, 3 xfailed`) never caught this: `harness/` is outside `test/`, and pytest's own collector confirms it —
```
$ python3 -m pytest --collect-only -q test/ 2>&1 | grep -i panel
(no output)
```
— and no gate/hook in this repo runs `pytest harness/` either (`grep -rn "harness/" gates/*.py on-the-record/hooks/*.sh` — no hit; this repo has no GitHub Actions per the issue's own "Actions abolition 2026-08-08" context), so this regression is currently unguarded by anything but a human reading this record. This falsifies the PR's "no new bug" claim as stated (identical failing-test-NAME-SETS) for the true test population; it only holds for the `test/`-scoped subset the PR chose to compare.

For the other two renamed trace-field writers (`_append_consult_trace`, `_append_judge_trace`, both consult.py), I traced every reader: `_judge_skills_run_today()` (consult.py) anchors on `merge=`/`verb=judge`, unaffected by the `role=`→`skill=` swap — confirmed by reading its body directly (`needle = f"| merge={merge_sha} "`, no `role=`/`skill=` reference). `on-the-record/hooks/pr-preflight.sh:334`'s `_MACHINE_BODY_RE` regex carries a `role=` alternative that `docs/issue-1310/reports/implementation/survey.md:70-71` and `docs/issue-1310/proposals/machine-comment-cursor.md:82` document as a deliberate fallback for the consult-trace line shape "in case that shape is ever relayed into an issue comment body" — currently dormant (no live poster relays these lines into GitHub comments; traced every `gh api .../comments` call site in relay.py/spawn.py, none constructs a trace-shaped body). This is a real but currently-inert consumer that PR #2869 did not update, correctly out of its own stated scope (hooks/ is issue #2138's territory, and the PR explicitly says so) — but it is a NEW staleness this PR introduces relative to that fallback pattern's own design doc, worth naming for whoever runs #2138's sweep next, since it wasn't stale before this PR landed.

**2. Renamed-parameter-by-keyword sweep — PR's claim holds.**
`_commit_consult_trace(role→skill)`: all 3 production call sites (consult.py:584, 1081, 1194) pass positionally — confirmed by direct grep/read. No caller anywhere in `/home/jwjung/tokenmaxxxer-core` imports or calls this function (`grep -rln "_commit_consult_trace\|resolve_role_family_source\|resolve_skill_family_source" /home/jwjung/tokenmaxxxer-core --include=*.py` — no hit; on-the-record and tokenmaxxxer-core are separate repos with no Python import relationship between them). The only keyword-argument callers anywhere were the two test files the PR already fixed.

**3. Directive-prose site (`on-the-record/directive/delegation-loops.md`) — byte count confirmed, meaning confirmed unchanged-or-improved.**
```
$ wc -c on-the-record/directive/delegation-loops.md            # origin/main
7986 on-the-record/directive/delegation-loops.md
$ wc -c /tmp/pr2869-worktree/on-the-record/directive/delegation-loops.md
7983 on-the-record/directive/delegation-loops.md
```
Matches the PR's claimed 7986→7983 exactly. Two hunks: (a) "rulebook loaded"→"skill loaded" — mechanical vocabulary swap, no instruction-shape change. (b) the invocation example `spawn.py spawn <skill> "<task>" --issue <n> --background` → `spawn.py --skills <skill> "<task>" --issue <n> --no-wait` — I confirmed via `python3 spawn.py --help` that the OLD form is not just non-current but non-existent: the positional-role spawn form is explicitly retired ("역할-포지셔널 스폰(spawn.py implementation \"<일>\")은 은퇴했다"), there is no bare `spawn` subcommand, and `--background` is not a defined flag anywhere in the argparse setup. `--no-wait` (spawn.py:2101-2102) is real and its help text — "fork 직후 _await_bounded 없이 즉시 리턴한다 — 재개 명령(spawn.py watch)을 찍는다" — matches exactly what the old text described ("fork and return immediately, print the resume command"). This directive text is injected into spawned sessions and executed literally; the old example would have caused a session following it to hit a CLI usage error. The rewrite is a genuine behavior-relevant correctness fix, not pure wording — but the PR discloses this itself (its own body: "fictional ... invocation example rewritten to the real dispatch shape"), so this is not a mischaracterization, just a note that "mechanical" undersells this one hunk slightly.

**4. Two role-noun survivals — both legitimate, not a return of the retired axis.**
`"role-handoff contract v3"` (gates/ci.py, line unchanged by the diff on both sides) names the CURRENT, live protocol name — not historical. Confirmed directly: this very verification session is operating under it right now.
canonical: this session's own SessionStart hook output, first line: `[core] Interaction protocol for role adversarial-review-6cda09d1 (role-handoff contract v3). INVARIANTS: ...` — read at session start, this turn's context.
It cannot be phrased without the noun while still identifying the same thing — "role-handoff" is the contract's actual proper name, used identically in this session's own live directive stack, not a stale synonym for something now called differently.

`docs/reports/2026-07-29-hunt-muster-role-model-build.md` (spawn.py:2665's comment, cited text unchanged by this PR's diff — only the adjacent function-name reference on the same line, `resolved_role_model()`→`resolved_skill_model()`, was touched): this exact filename does NOT exist in the tree — untracked, no such path was ever committed under this name.
derived: `git ls-files | grep -i "hunt-muster-role-model-build\|role-model-build"` — no output. Closest actual file: `docs/reports/2026-07-29-hunt-role-model-builtin-sonnet-default.md` (found via `git ls-files | grep "2026-07-29"`); different content, so this is not simply a rename I can redirect the citation to.
This is a pre-existing broken citation, NOT introduced or left behind by PR #2869's own scope decision — the diff shows this exact path string is identical on both the `-` and `+` side of that hunk (only "resolved_role_model" changed). Since it predates and is untouched by this PR, it is out of scope for judging THIS PR's "mechanical and behavior-preserving" claim; noting it only as an aside for a future pass, not as a finding against this delivery.

**5. `lifecycle.py:436,566-581` `roster_kill()` lease-suffix mismatch — REAL and REACHABLE, not "unestablished."**
The PR's own record calls this "unestablished... needs someone to trace `a.task`'s actual value at `spawn.py:2534`." I traced it and reproduced it directly.

`roster_kill(issue, skill)` (lifecycle.py:566-581) builds `key = f"issue-{issue}/{skill}"` — no lease suffix. The live roster is keyed differently: at spawn time (spawn.py:2229, the `--skills` path — the ONLY spawn path; the bare-role positional form is retired per `--help` above), `a.role = f"{skill_slug}-{disambiguator}"` where `disambiguator = new_lease_disambiguator()` (8 hex chars, roster.py:266-275); then spawn.py:4272 registers `roster_key = lease_key(issue, skill)` using that SAME already-suffixed `skill` value. So every live roster entry's key is `issue-<n>/<skill>-<8-hex-lease>`, never the bare `issue-<n>/<skill>`. `spawn.py:2534` (`kill` dispatch: `return roster_kill(a.issue, a.task)`) passes `a.task` straight through with no transformation — whatever string the operator typed after `spawn.py kill`.

derived: reproduced directly in the PR-head worktree (`/tmp/pr2869-worktree`) —
```
$ python3 -c "
import spawn, lifecycle, subprocess, time
issue = 99997; skill_slug = 'implementation'
disambiguator = spawn.new_lease_disambiguator()
live_skill = f'{skill_slug}-{disambiguator}'
roster_key = spawn.lease_key(issue, live_skill)
proc = subprocess.Popen(['sleep','60']); time.sleep(0.2)
spawn.roster_register(roster_key, {'pid': proc.pid, 'work': '/tmp/x', 'skill': live_skill, 'issue': issue})
print('Attempt A (bare skill, matches CLI usage text <역할>):')
rc = lifecycle.roster_kill(issue, skill_slug)
print('exit', rc, 'proc alive:', proc.poll() is None)
print('Attempt B (full lease-suffixed segment, matches roster_ps output):')
rc2 = lifecycle.roster_kill(issue, live_skill); time.sleep(0.3)
print('exit', rc2, 'proc alive:', proc.poll() is None)
"
로스터에 없다: issue-99997/implementation
Attempt A (bare skill, matches CLI usage text <역할>):
exit 1 proc alive: True
Attempt B (full lease-suffixed segment, matches roster_ps output):
종료 신호를 보냈다: issue-99997/implementation-156ce32b (pid ...). ...
exit 0 proc alive: False
```
Attempt A (the CLI's own usage string reads `사용법: spawn.py kill <역할> --issue <n>` — "role", suggesting a bare skill name) silently fails to find the live entry and does not kill the target. Attempt B (passing the exact `<skill>-<lease>` string `roster_ps`/`_format_roster_row` actually prints) succeeds. `grep -rln "roster_kill\|spawn.py kill" test/` returns nothing — zero test coverage over this path in either direction. So this is not "roster_kill can never work" (it works if the caller already knows to pass the full lease-suffixed key) but it IS a genuine silent-failure trap exactly matching the shape the task named: an operator following the command's own `<역할>`-shaped usage text, or old muscle memory from before issue #2432 introduced the lease suffix, gets a "로스터에 없다" with no indication a live, matching-by-skill-name session exists and was simply missed by key shape. This should be escalated from "unestablished, deferred" to "established, reproduced, needs a fix" (either accept a bare skill and search/disambiguate roster entries by prefix, or fail loudly with a "found N candidates, specify the full lease key" message instead of a flat "not in roster").

**6. Four standing invariants — re-run independently, not trusted from the PR's own report.**
```
Invariant 1 (role-axis count decreased) — derived:
  grep -rln '역할\|\brole\b' --include=*.py --include=*.md . | grep -vE '/(test|docs)/' \
    | xargs -I{} grep -c '역할\|\brole\b' {} | awk -F: '{sum+=$1} END {print sum}'
  my measurement: origin/main (this checkout) 19019 -> PR head 18980 (decreased by 39)
  PR's own reported numbers: 18994 -> 18938 (decreased by 56)
  Direction agrees (decreased) in both measurements; the absolute numbers differ, most
  likely because my origin/main has advanced past the commit the PR actually branched
  from/measured against (unrelated commits landing on main between the PR's authoring
  time and this verification) -- not attributable to an error in the PR's own diff,
  which I read in full above and confirms only wording/label/docstring/log-string edits.

Invariant 2 (no new bug, test/-scoped) — derived:
  python3 -m pytest test/ -q, both trees: 15 failed, 441 passed, 3 xfailed (identical counts)
  `diff` of sorted `FAILED ...` line sets between origin/main and PR head: empty (SETS IDENTICAL)
  -- confirmed myself, not restated from the PR's own claim. BUT see finding 1 above:
  this invariant's own SCOPE (`test/` only) is why it did not catch the harness/ regression --
  the true test population is not identical before/after.

Invariant 3 (no overhead increase) — see finding 3 above: 7986 -> 7983 bytes, confirmed exactly.

Invariant 4 (monitor/watch unbroken, not quieter) — derived:
  python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py -q
  both trees: 10 passed, 0 failed -- confirmed myself. `git diff watchdog.py` between the
  trees shows only string-literal changes inside four existing print() call sites
  (lines 579, 1053/1072-1078 region, 1617 in the diff) -- no print/sys.exit call site
  added, removed, or made conditional; matches the PR's own claim.
```

## Why

The task named five specific attack surfaces because a "wording-only" claim is exactly the kind of claim that hides real breakage: renamed identifiers/strings that are read back by code (trace fields, parsed error text) fail silently rather than loudly, and a test suite scoped narrower than the code being changed reports a false "no new bug." I prioritized reproducing rather than reasoning in the abstract — every claim above that could be executed, was (both the PR's own invariants and my own counter-checks), because "the diff *looks* mechanical" and "the diff *is* behavior-preserving" are different claims, and only the second one is what the PR's warrant rests on.

## What did not work

None.

## Upstream basis

canonical: `gh pr view 2869 --repo tokenmaxxxer/on-the-record --json ...` and `gh pr diff 2869` — read this session; `gh issue view 2139` — read this session.

- PR #2869 (`https://github.com/tokenmaxxxer/on-the-record/pull/2869`), head commit `190321de059bf8b12de9cb2f943e8f8233f51ad2` plus two follow-up commits on the same branch (`4fb76e4c50ea48745e234d3da6d83bce9d908919`, `0562882dbdfcac518e98866f3ba5ddb0cfc07cdd`) — read via `gh pr view`/`gh pr diff` this session, and independently re-executed via a `git fetch origin pull/2869/head` + `git worktree add` checkout at `/tmp/pr2869-worktree` (cleaned up via `git worktree remove --force` / `git branch -D` before this record was written).
- Issue #2139 (`gh issue view 2139`, read this session).
- `/home/jwjung/tokenmaxxxer-core` (local checkout, path from `$CLAUDE_PLUGIN_ROOT_CORE`'s sibling layout) — derived: `grep -rln "_commit_consult_trace\|resolve_role_family_source\|resolve_skill_family_source" /home/jwjung/tokenmaxxxer-core --include=*.py` — no output (no cross-repo Python caller of the renamed `consult.py` parameter or function).

## Open findings

1. `harness/fixture-concurrent-judgment/test_panel.py::test_panel_live_exchange_records_position_rebuttal_and_verdict` — reproduced failure on PR #2869's head (see "What was done" §1). Resolution path: the fix is the same shape as the two test files PR #2869 already touched — update the two `"role=qa"`/`"role=review"` assertions to `"skill=qa"`/`"skill=review"`. Recommended as a small follow-up commit on the PR's own branch before merge (it is the PR's own regression, in the PR's own write-set family, not a new scope item), or, if the user prefers, filed as a fast-follow issue referencing PR #2869.
2. `lifecycle.py:566-581` `roster_kill()` lease-suffix mismatch — established and reproduced this session (see "What was done" §5), upgrading the PR's own "unestablished" characterization. Resolution path: either (a) have `roster_kill()` search roster keys by `issue-<n>/` prefix + skill-name match when no exact key hits, disambiguating/erroring on >1 match, or (b) change the `kill` subcommand's usage text and CLI contract to explicitly require the full lease-suffixed segment as shown by `roster_ps`, and have it fail loudly (not "로스터에 없다") when given a bare skill name that partially matches a live entry. This is the user's call to file (per this session's own gh-guard constraint, same as PR #2869's own three deferred findings) — not fixed here, since fixing it is out of this review's own scope (verification, not implementation).
3. `on-the-record/hooks/pr-preflight.sh`'s `_MACHINE_BODY_RE` `role=` fallback regex is now stale relative to consult.py's renamed trace format (see "What was done" §1) — currently no live harm (the fallback path it guards is dormant), but worth folding into issue #2138's hooks sweep now that it's no longer consistent with the format it was designed to recognize.
4. `docs/reports/2026-07-29-hunt-muster-role-model-build.md`, cited (as an already-untracked/nonexistent path — this citation predates PR #2869 and this PR's own diff leaves that filename string byte-identical, only touching the adjacent function-name reference on the same line) in `spawn.py:2665`'s comment, does not exist under that name (see "What was done" §4) — pre-existing, not this PR's doing; noted only so it doesn't get lost.

## Next steps

None from this record's own side — this is a terminal verification record (`loop_state: landed`). Findings 1-4 above are handed back to the user/maintainer to route (fix directly, file as follow-up issues, or fold into #2138 as noted).

skill-verdict: adversarial-review — applied: invoked; used as the operating frame for this whole session (structurally independent evaluator session receiving only PR #2869's diff/record, incentivized to find everything wrong with its "mechanical and behavior-preserving" claim rather than restate it)
other mounted skills: not triggered
