---
issue: 2876
role: silent-failure-audit-b01a1db4
author: silent-failure-audit-b01a1db4
skills: silent-failure-audit (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: gates/retirement_count.py, on-the-record/hooks/pr-preflight.sh, test/test_convention_equivalence.py, test/test_retirement_count.py
type: implementation-record
breaking: false
verdict: reshaped-substitute-site-fixed-forward, reader-check-derivation-established, disposition-gap-closed
loop_state: landed
upstream:
  - path: docs/issue-2876/reports/silent-failure-audit-133bcbf6.md
    sha: ed92f4113aecc0c20046726e37b02c9f05018d7c
  - path: gates/retirement_count.py
    sha: same-commit
  - path: on-the-record/hooks/pr-preflight.sh
    sha: same-commit
---

# issue-2876 — silent-failure-audit-b01a1db4 record

## What was done

canonical: `gh issue view 2876 --comments` and the round-2 spawn note (this session's own prompt), read before starting.

CORE_BUILD_NOW=1 was set (spawner env — checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"`, result: `CORE_BUILD_NOW=1`), so this delivered directly under contract v3 s19a — no phase-1 proposal round.

This is round 2 on PR #2881 (issue #2876), after two independent verifications (#2884, #2885) confirmed the substance and #2884 found a gap: `on-the-record/hooks/pr-preflight.sh:417` carries an unfixed copy of the identical reshaped-substitute defect PR #2881 fixed in `gates/flows.py::_plan_from_body` — the plan-step dict's value moved to the skill axis (`"skill"`/`"skills"`) but its key stayed `"roles"`. canonical: `gh pr view 2881 --json state,mergedAt`, this session, result: `state: OPEN, mergedAt: null` — PR #2881 is still open, unmerged, so this branch merges its head (`ed92f411`) rather than re-deriving its content, matching the round-2 precedent set by PR #2877/issue #2139 — canonical: `gh pr view 2877 --json baseRefName,headRefName,body`, this session, body states "This branch merges PR #2869's branch ... and adds both fixes on top" — and adds this round's fixes on top the same way.

1. **Fixed `on-the-record/hooks/pr-preflight.sh:416-417`** (`_plan_from_body`'s ported copy): `roles = [...]` / `{"step": step_n, "roles": roles, "done": done}` → `skills = [...]` / `{"step": step_n, "skills": skills, "done": done}`, matching `gates/flows.py`'s already-fixed shape. derived: `grep -n '\bplan\b' on-the-record/hooks/pr-preflight.sh` before the edit, this session, showed the only readers of the parsed `plan` list (`check_body()`) subscript `s["done"]`/`s["step"]` only — zero readers of the `roles`/`skills` key inside this file, so the rename has no in-file follow-on edit.
2. **Established why the round-1 reader-check missed it, and fixed the method, not just the instance**: the disposition search used to find readers of `["roles"]`/`.get("roles"`/`"roles":` was `grep ... --include=*.py .` (PR #2881's record, "site 1" reader accounting) — structurally blind to a `.sh` file by construction, not by an oversight of one extra flag (demonstrated below). `gates/retirement_count.py` gained a `--list-files` mode that prints its own `tracked_sources()` population (the same py/sh, docs/-excluded set the installed checker walks), so a future reader-check pipes through the checker's own declared coverage (`python3 gates/retirement_count.py --list-files | xargs grep -n <pattern>`) instead of hand-retyping an `--include` list that can silently narrow.
3. **Found what else was ported alongside it**: derived: swept `tracked_sources()`'s own population (not a hand `--include` list), this session, for every `_plan_from_body`/`_PLAN_STEP_RE`/`_ROLE_TRAILER_RE`/`_SKILL_TRAILER_RE` occurrence and every `["roles"]`/`.get("roles"`/`"roles":` occurrence repo-wide. Exactly one other port of `_plan_from_body` exists (`on-the-record/hooks/pr-preflight.sh`, fixed above); `on-the-record/hooks/plan-order-guard.sh` and `gates/pr_reference.py` both *import* `flows._plan_from_body` rather than porting it, and were already reading the fixed `p["skills"]` shape as of PR #2881's commit `94c3b3c1` (canonical: `git show 94c3b3c1 -- on-the-record/hooks/plan-order-guard.sh`, this session). No third copy exists.
4. **Added regression coverage**: a new test in `test/test_convention_equivalence.py` (`test_pr_preflight_plan_from_body_port_matches_flows`, in the `RsbStatusBoardEquivalenceTest` class) — a literal reproduction of the fixed port (module convention: hooks are heredoc'd shell+Python, not importable), pinned byte-for-byte against `flows._plan_from_body`'s golden output for the same body, plus a direct source-text assertion that `pr-preflight.sh` no longer contains `"roles": roles`. A new test in `test/test_retirement_count.py` (`ListFilesDerivesTheReaderCheckPopulationTest`) — proves `--list-files` includes a known `.sh` site and a known `.py` site, excludes `docs/` and the checker's own self-exclusion set. derived: `python3 -m pytest test/test_convention_equivalence.py -k plan_from_body test/test_retirement_count.py -q`, this session, result: `13 passed`.

## Why

### The reader-check's own blind spot was the same shape as the bug it was hunting

PR #2881's Part-3 reader accounting for site 1 (`_plan_from_body`) ran `grep -rn '\["roles"\]\|\.get(.roles.\|"roles":' --include=*.py .`. derived: reproduced verbatim this session on the pre-round-2 tree (`git show HEAD:on-the-record/hooks/pr-preflight.sh | grep -n '"roles"'` confirms line 417 carried it, and the same `--include=*.py .` grep on the working tree at that point returns nothing for it) — not because the pattern doesn't match the line, but because `--include=*.py` never opens a `.sh` path at all. derived: minimal reproduction this session:

```
$ echo 'ACTIVE = "roles"' > /tmp/probe.sh
$ grep -l '"roles"' --include=*.py /tmp/probe.sh; echo "exit=$?"
exit=1
```

A `grep --include` miss and a "the pattern doesn't occur here" miss produce the identical output (nothing, exit 1) — indistinguishable in the terminal, exactly the "negative result without ever reaching the thing it claims to cover" shape the issue names for the retirement check itself. The reader-check that audited the checker's own fix carried the same defect class as the fix.

Confirmed the counterfactual: derived: running the corrected checker's own derived population (`gates/retirement_count.py`'s `tracked_sources()`, py+sh, docs/-excluded) against the same reader pattern, on the pre-fix tree, this session, surfaces `pr-preflight.sh:417` directly — a search built from the checker's own coverage cannot silently narrow to fewer extensions than the checker itself claims to cover, because it's the same function, not a second hand-typed copy of the same intent.

### Why `tracked_sources()`'s own py/sh scope stays enumerated, not derived further

The round-2 note asks to establish what file types can carry these keys/readers "at all" and derive that rather than restate it, and to say so plainly if it can't be derived. It can't, beyond what's already true: `pr-preflight.sh` itself is proof that file extension does not reliably predict language in this repo — canonical: `on-the-record/hooks/pr-preflight.sh:1-35`, read this session, is a `.sh` file (`#!/usr/bin/env bash`) that embeds a ~760-line Python heredoc (`IFS='' read -r -d '' GUARD <<'PY' ... python3 -c "$GUARD"`), so "what extensions carry Python-shaped dict keys" has no clean answer derivable from extension alone; `.sh` files in `on-the-record/hooks/` routinely do this. The two extensions `tracked_sources()` walks are fixed by the issue's own acceptance criteria ("population: py/sh sources... docs/ excluded"), not computed by the function — that enumeration is stated plainly in a comment on `tracked_sources()` now, and is not silently extended to a third extension on suspicion. What *is* fixed is that any future search for readers/writers of a key derives its file list from that one function instead of re-typing its own guess at the boundary — the `--list-files` mode is the reusable interface for that, usable from Python (`import`) or the shell (pipe to `xargs grep`) alike, so the next reader-check has no reason to retype an `--include` list at all.

### The 3 new occurrences this round adds to the checker's own count are citations of the fix, not a live return of the retired axis

derived: `bash gates/retirement_count.sh` run on this branch's pre-round-2-edits state (`git stash`) vs. the round-2-edits-restored state (`git stash pop`), this session: `retirement_count: 1182 occurrence(s)` → `retirement_count: 1183 occurrence(s)`. Diffed the two site lists (`comm -13`/`comm -23` on sorted output, this session): exactly 2 lines left the set (`pr-preflight.sh:416-417`, the fixed defect) and 3 entered it, all new lines inside this round's own added test (`test/test_convention_equivalence.py`):

- Lines 408, 458: comments narrating this fix ("this port kept the `\"roles\"` key after...", "that reintroduces the `\"roles\"` key..."). Historical-citation by the classifier method PR #2881 established (ast/tokenize comment-range membership) — prose about a defect, not a live use of the retired axis.
- Line 463: `self.assertNotIn('"roles": roles', text)` — a code line, not inside a comment/docstring, so the classifier's own rule would put it in the live-candidate bucket. It is the same trade `tokenmaxxxer-core#361` and PR #2881's own self-exclusion rationale already accepted for `retirement_count.py`/its test fixtures: a regression guard that names the retired shape *in order to assert its continued absence* must spell it literally to do that job, and doing so is a citation of the defect it prevents, not a revival of it. Unlike `retirement_count.py`'s three-file self-exclusion, this one line is not added to `_SELF_EXCLUDED` — it is disposed here individually, the same per-site judgment call PR #2881's Part 2 used throughout, not folded into a growing allowlist.

All 3 are accounted for; no undisposed site remains in the delta this round introduced. This addresses the reporting gap #2884 flagged in PR #2881's own record — a checker's own re-run belongs in the disposition it lands with, not left for the next verifier to notice.

## What did not work

None — no approach was tried and abandoned during this round.

## Upstream basis

- `docs/issue-2876/reports/silent-failure-audit-133bcbf6.md` (sha `ed92f4113aecc0c20046726e37b02c9f05018d7c`, PR #2881's implementation record) — this round's `gates/retirement_count.py`/`tracked_sources()`/`_SELF_EXCLUDED` and the `_plan_from_body` rename in `gates/flows.py` are that PR's delivered baseline. canonical: `git log --oneline -1 origin/issue-2876/silent-failure-audit-133bcbf6` and `git merge --no-edit origin/issue-2876/silent-failure-audit-133bcbf6`, both run this session — merged into this branch rather than re-derived.
- `docs/issue-2876/reports/independent-verification-1.md` (#2884) and `-2.md` (#2885), already merged to `main`. canonical: `gh pr view 2884 --json files` and `gh pr view 2885 --json baseRefName,headRefName,mergedAt`, both run this session, confirm both merged. #2884 is the source of this round's fix target (`pr-preflight.sh:417`) and the disposition-reporting-gap note per the round-2 spawn instructions (this session's own prompt, quoting #2884's finding); #2885 confirmed the tokenizer/population/no-alias/docs-boundary substance this round did not re-litigate.

## Standing invariants — commands and their output (re-run this round)

**1. No return of the retired role axis in any reshaped form, measured with the corrected check.**
```
derived: bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1
```
result: `retirement_count: 1183 occurrence(s)` (this branch, post-round-2, run this session). Old case-sensitive `\brole\b` on the same tree:
```
derived: git ls-files "*.py" "*.sh" | grep -v '^docs/' | xargs grep -c '\brole\b' | awk -F: '{s+=$2} END{print s}'
```
result: `988`. The +1 net change from this round's pre-fix merge baseline (1182 → 1183) is fully disposed in "Why" above (−2 defect-site lines, +3 citation lines); no reshaped-substitute site remains — confirmed by re-running the derived reader-check pattern (`["roles"]`/`.get("roles"`/`"roles":`) over `tracked_sources()` post-fix, this session: 1 hit, `gates/model_routing.py:21`, a pre-existing Korean-prose comment citing already-removed code (`role in tier["roles"]`), unrelated to this round, unchanged by it.

**2. No new bug — collection scope stated, failing-test-NAME sets compared.**
```
derived: python3 -m pytest . -q    # repo root, not `pytest test/` -- run this session, this branch
```
result: `17 failed, 633 passed, 3 xfailed`.
```
derived: python3 -m pytest . -q    # run this session in a separate `git worktree add ... origin/main`
```
result: `17 failed, 621 passed, 3 xfailed`. derived: `diff` on the two sorted `FAILED ...` name lists (`grep '^FAILED'` from each run's output, sorted), this session, result: identical, 17/17 — no test moved from pass to fail or vice versa. The +12 passing (621→633) is PR #2881's own +10 (already merged into this branch) plus this round's own +2 new tests (one in each of the two files touched in "What was done" item 4).

**3. No overhead increase.**
```
derived: time bash gates/retirement_count.sh > /dev/null 2>&1
```
result: `real 0m0.184s`. Old grep baseline:
```
derived: time (grep -rn '\brole\b' --include=*.py --include=*.sh . 2>/dev/null | grep -v '^\./docs/' > /dev/null)
```
result: `real 0m0.033s`. Materially unchanged from PR #2881's own measurement (`0.179s` vs `0.032s`, cited in its record) — the new `--list-files` branch is an early-return, unreached and adds no cost on the default (no-argument) invocation path this timing exercises.

**4. Monitor/watch machinery unbroken and not quieter.**
```
derived: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q
```
result: `30 passed` (run this session). derived: `git status --short on-the-record/monitors/`, this session, result: empty — untouched by this round.

## Open findings

None new. The three open findings PR #2881's record already carries (the 83-site pending-migration baseline tracked by issue #2241; the `roles/*.json`/`PROTECTED_ROOT_DIRS` cross-repo-layout question; `retirement_count.sh` not wired into a blocking gate) are unchanged by this round and not re-litigated here — see `docs/issue-2876/reports/silent-failure-audit-133bcbf6.md`, "Open findings", for their resolution paths.

## Next steps

None — `loop_state: landed`. This branch merges PR #2881's head and adds the round-2 fixes; opening this as the PR carrying both, per the round-2 precedent (issue-2139/#2877 over #2869/#2873).

skill-verdict: silent-failure-audit — not-applicable: this round's work is a dict-key rename and a search-methodology fix, not classifying an I/O/network/parse operation's catch-block behavior — no fallible operation's failure path was the subject.
skill-verdict: work-in-english — invoked; loaded before writing this record and the PR body — commit messages, code comments, test names, and this record are English; the end-of-turn summary to the user is Korean per the skill's routing rule.
other mounted skills: not triggered (dataviz, keybindings-help, update-config, fewer-permission-prompts, loop, schedule, claude-api, run, init, security-review, code-review, simplify, freelunch:*) — no chart/settings/keybinding/scheduling/app-launch/security-review/generic-review/fan-out work matched any of their trigger conditions this round.
