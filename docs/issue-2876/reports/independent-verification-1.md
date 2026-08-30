---
issue: 2876
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: 6b7d78df:gates/retirement_count.py, 6b7d78df:gates/retirement_count.sh, 94c3b3c1:gates/flows.py, 94c3b3c1:gates/patrol_board.py, 94c3b3c1:on-the-record/hooks/plan-order-guard.sh, 94c3b3c1:test/test_convention_equivalence.py, 12f5b855:test/test_retirement_count.py, 6b7d78df:docs/specs/enforcement-boundary.md
type: verification-record
breaking: false
verdict: core-deliverable-verified, one-unaccounted-reshaped-substitute-site-found
loop_state: landed
upstream:
  - path: PR #2881 (issue-2876/silent-failure-audit-133bcbf6)
    sha: 6b7d78df2425e745381d7ffa29329d5a8daa304c
  - path: 6b7d78df:docs/issue-2876/reports/silent-failure-audit-133bcbf6.md
    sha: d1909ff50f859eda2981f67e5dbbda1d5b4952ca
---

# issue-2876 — independent-verification-1 record

## What was done

canonical: `gh pr view 2881 --json body,commits,files` — read the PR body and
all 5 commits before checking out its branch.

Checked out PR #2881's branch tip into a worktree at
`/tmp/verify-2876` — derived: `git worktree add /tmp/verify-2876
issue-2876-impl-review` where `issue-2876-impl-review` tracks
`origin/issue-2876/silent-failure-audit-133bcbf6` — result: `HEAD의 현재
위치는 ed92f411입니다`. Confirmed the branch rebases cleanly on current
`main`: derived: `git log --oneline HEAD ^origin/main` from that worktree
— result: exactly the branch's own 6 commits, `main` not behind.

Independently re-derived the record's headline evidence rather than trust
the pasted numbers:

1. **The tokenizer.** canonical: read `6b7d78df:gates/retirement_count.py`
   in full this session. Traced `_LETTER_RUN`/`_SUBWORD` by hand against
   `user_role`, `roles`, `RoleModel`, `ROLE`, `role-handoff`, `IRole`.
   derived: `python3 -c "from gates.retirement_count import line_hits;
   print(line_hits('        steps.append({\"step\": step_n, \"roles\":
   roles, \"done\": done})'))"` run in the worktree this session — result:
   `True` — matches my hand trace that a bare `"roles"` token is caught.
2. **The headline counts.** derived: `git ls-files "*.py" "*.sh" | grep -v
   '^docs/' | xargs grep -c '\brole\b' | awk -F: '{s+=$2} END{print s}'`,
   run in the worktree this session — result: `985` (record claims `985`).
   derived: `bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1`, run
   in the worktree this session — result: `retirement_count: 1179
   occurrence(s)` (record claims `1179`).
3. **The 6 reshaped-substitute renames.** canonical: `git show 94c3b3c1`
   (this session) shows `gates/flows.py`, `gates/patrol_board.py`,
   `on-the-record/hooks/plan-order-guard.sh`, and
   `test/test_convention_equivalence.py` all renaming `"roles"`→`"skills"`
   / `_ROLE_TRAILER_RE`→`_SKILL_TRAILER_RE` in lockstep (5 issue-named
   sites + 1 audit-found site + both dependent readers). derived: `grep -rn
   '\["roles"\]\|\.get(.roles.\|"roles":\|_ROLE_TRAILER_RE' --include=*.py
   --include=*.sh .`, run in the worktree this session (repo-wide, both
   extensions, unlike one of the record's own greps which was
   `--include=*.py` only) — result: exactly 2 hits: a comment mentioning
   `tier["roles"]` in `gates/model_routing.py:21` (historical-citation,
   correctly out of scope), and one live hit detailed below.
4. **No new bug.** derived: `python3 -m pytest . -q` on the worktree
   (branch tip `ed92f411`) — result: `16 failed, 605 passed, 3 xfailed`.
   derived: the same command run in a second worktree checked out at `main`
   (`d514d2c7`) this session — result: `16 failed, 595 passed, 3 xfailed`.
   Compared the two runs' `short test summary info` FAILED-name blocks by
   reading both in full this session — byte-identical 16-name sets in both.
   derived: `python3 -m pytest test/test_retirement_count.py -q`, run in
   the worktree this session — result: `10 passed in 0.83s`, which is
   exactly the 605-minus-595 delta (605 - 595 = 10).
5. **`docs/` untouched** except one row. canonical: `git show 6b7d78df --
   docs/specs/enforcement-boundary.md`, read this session — confirms the
   only `docs/` change is a tooling-registry row about the new checker, not
   an edit to any historical record.

**Gap found: `pr-preflight.sh` carries the identical unfixed defect, and
the implementation record never dispositions it.**

canonical: read `on-the-record/hooks/pr-preflight.sh` lines 381-417 in the
worktree this session. Line 381 is a comment reading `# --- plan parsing
(ported from gates/flows.py::_plan_from_body) ---`; line 417 reads
`steps.append({"step": step_n, "roles": roles, "done": done})` where
`roles` (line 416) is `[r.strip() for r in mm.group(3).split("‖")]` — skill
names, stored under the retired-axis key `"roles"`. This is the exact same
"value moved to the skill axis, key stayed on the role axis" shape as the 6
sites `94c3b3c1` fixed in `gates/flows.py`/`gates/patrol_board.py`.

canonical: `git blame -L 417,417 on-the-record/hooks/pr-preflight.sh`, run
in the worktree this session — result: attributed to `dd27b08ee`
(2026-08-08), which predates both retirement commits the implementation
record names as the defect's source (`e1b35a53`, `e1f390ab`, both later
than 2026-08-08). By the implementation record's own classification rule
(touched by a flagged retirement commit ⇒ fix now; else ⇒ pre-existing,
tracked by #2241) this site would correctly land in the pre-existing
bucket, not the fix-now bucket — so non-renaming is defensible on its own.

derived: `grep -n '\["roles"\]' on-the-record/hooks/pr-preflight.sh`, run
in the worktree this session — result: 0 hits outside the one `.append`
write site itself; canonical: read `check_body()` (line 714 onward) in
full this session — it subscripts only `s["step"]` and the completion-flag
key, never the `"roles"` key. So this key is currently write-only, not a
live functional bug on its own.

The actual defect is that this site is **entirely absent from the
implementation record's disposition** — not counted among its 6
reshaped-substitute fixes, not named among its 83-bucket representative
examples, not mentioned anywhere — despite the record's own text claiming
"every reader found repo-wide" and "every one of the 217 delta lines
received an individual category." canonical: read
`6b7d78df:docs/issue-2876/reports/silent-failure-audit-133bcbf6.md`,
"Part 3" section, this session — its repo-wide reader-check for this exact
defect shape is quoted verbatim as `grep -rn '\["roles"\]\|\.get(.roles.\|
"roles":' --include=*.py .` — `--include=*.py` cannot match a line inside
a `.sh` file, so this site was structurally outside that grep's reach.
derived: `python3 gates/retirement_count.py 2>/dev/null | grep -n
pr-preflight`, run in the worktree this session — result: a non-empty
match list including line 417, confirming the corrected checker itself
does surface this site (it is part of the 1179 total), so it was available
to be dispositioned by the record and was not.

## Why

The subject's acceptance criteria require a per-site disposition for every
site the corrected command finds — not that every live-candidate be fixed,
but that every one be individually labelled and reasoned about. This issue
is specifically about checks whose blind spots hide behind an
unremarked-on scope restriction, so re-running the record's own
reader-accounting greps with the restriction removed (`.sh` included, not
just `.py`) was the most direct way to test whether the record's own audit
had the same shape of gap it was built to catch. It did, once.

## What did not work

None.

## Upstream basis

- PR #2881 (`issue-2876/silent-failure-audit-133bcbf6`), sha
  `6b7d78df2425e745381d7ffa29329d5a8daa304c` through `ed92f4113aecc0c20046726e37b02c9f05018d7c`
  — checked out in a worktree this session, verified rebased cleanly on
  `main` `d514d2c7`.
- `6b7d78df:docs/issue-2876/reports/silent-failure-audit-133bcbf6.md`, sha
  `d1909ff50f859eda2981f67e5dbbda1d5b4952ca`.

## Open findings

1. **`on-the-record/hooks/pr-preflight.sh:417`'s `"roles"` key** (holding
   skill names, ported from the pre-fix `gates/flows.py`'s
   `_plan_from_body`) is a live reshaped-substitute-shaped site the
   corrected checker finds — derived: `python3 gates/retirement_count.py
   2>/dev/null | grep -n pr-preflight`, run in the worktree this session,
   non-empty result including line 417 — but the implementation record's
   disposition never names it, in either its 6-site fixed group or its
   83-site pre-existing group. It is currently write-only (per the
   `check_body()` read cited in "What was done" above), so this specific
   gap is not itself a functional regression. Resolution path: a follow-up
   to PR #2881 either renames it forward alongside its 6 siblings (same
   shape; `check_body()`'s reads leave it with zero external readers to
   update), or the implementation record is amended to add it explicitly
   to the pre-existing/out-of-scope bucket with the same
   `git blame`-predates-both-flagged-commits reasoning used for its
   siblings there. Either action would close the gap between the record's
   completeness claim and its actual reach; leaving it silently absent
   does not.

## Next steps

None — `loop_state: landed`.

skill-verdict: work-in-english — applied: invoked; wrote this record and
all git/gh interaction in English per the skill, reserving Korean for the
final chat summary to the user.
other mounted skills: not triggered — this was a read/audit/record task
(no chart, no config change, no code-review-tool invocation, no fan-out).
