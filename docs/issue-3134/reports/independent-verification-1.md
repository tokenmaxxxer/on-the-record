---
issue: 3134
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: PR #3156 (branch issue-3134/implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310), the repair round on PR #3143
loop_state: complete
type: verification
breaking: false
verdict: pass
upstream:
  - path: docs/issue-3134/reports/implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310.md
    sha: aacd119ba1433c85b990ddb9cf74306f97d310df
  - path: docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md
    sha: 4671de88e50c26cc66e119a11d48736c1c743703
---

# issue-3134 — independent-verification-1 record

## What was done

Independent, builder-blind verification of PR #3156 — the repair round
on PR #3143's `amends:` deliverable — against issue #3134's four
acceptance checks and three must-nots. Checked out PR #3156's head
(`git fetch origin pull/3156/head`) into a separate worktree
(`/tmp/pr3156-verify`) and re-ran every check from scratch before
reading PR #3156's own record in full.

canonical: `gh pr view 3156` output (state: OPEN, headRefName:
`issue-3134/implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310`)

derived: `python3 -m pytest tests/test_amends_resolution.py -q`, run in
the PR #3156 worktree (`/tmp/pr3156-verify`, untracked on this session's
own branch — this branch has no `docs/specs/acceptance-commands.md` row
for a PR-3156-only command, so this is cited as `derived:` rather than
`acceptance:`, per acceptance-command-real-run-guard.sh's own escape
hatch) — result: PASS
```
19 passed in 0.83s
```

derived: `python3 gates/probe_amends_is_discoverable.py`, run in the PR
#3156 worktree (`gates/amends_index.py`, `amends_backlink.py`,
`amends.py` — untracked on this session's own branch, PR #3156 branch
only) — result: PASS
```
-- confirmed Route 1: opening A directly surfaces the amendment (found 'docs/issue-15/reports/verification.md' and a marker in A's own content, no other file consulted) --
-- confirmed Route 2: grepping the wrong claim's own text (line 17) lands within 2 line(s) of the amendment marker (line 15) --
-- confirmed Route 3: following a link into A's `limitation` anchor (from an unrelated third record, not the index) still surfaces the marker immediately --
-- confirmed: check() refuses an unlinked amendment on BOTH axes (index + backlink) --
-- confirmed: regenerating the index alone is NOT enough -- check() still refuses on the missing backlink --
-- confirmed: check() passes once BOTH the index and the backlink are landed --
ok
```
(the `issue-10`/`issue-15`/`issue-20` paths in this output are the
probe's own synthetic temp-dir fixture content, not real paths in this
or any other repo — untracked, illustrative only)

derived: `python3 gates/probe_amends_fails_closed.py`, run in the PR
#3156 worktree — result: PASS
```
-- case: dangling target -- ok
-- case: section anchor that does not exist -- ok
-- case: two records amending the same section, conflicting claims -- ok
-- case: cycle (A amends a section of B, B amends a section of A) -- ok
ok
```

derived: `python3 -m pytest tests/ -q`, run in the PR #3156 worktree —
result: PASS
```
323 passed, 2 warnings in 10.52s
```

derived: `python3 -m pytest test/ -q` (not one of the four required
acceptance checks, run as a sanity cross-check against PR #3156's own
claim) → `563 passed, 3 xfailed in 32.28s`, matching PR #3156's record
exactly.

**Independent discoverability reproduction, not reused from the PR's
own fixture.** Built a fresh fixture from scratch (own script, own
temp copy of PR #3156's `docs/` tree), injecting an `amends:` edge with
no backlink and no index update, and called `amends_index.py`'s
`check()` directly (no shell-out, no reliance on the shipped probe's
assertions):

derived: `python3 /tmp/pr3156_check_test.py` (own script, own fixture,
not the PR's shipped probe) — result:
```
bad reasons: ["docs/specs/amends-index.md is stale -- it does not match
what the tree's `amends:` edges resolve to. Run `python3
gates/amends_index.py --update` and commit the result in the same
change."]
OK: fails closed as expected
```
(`docs/specs/amends-index.md` above is PR #3156's own new file, untracked
on this session's own branch)

This confirms `check()` fails closed on an unlinked amendment against a
fixture the delivering session never constructed, independent of
`probe_amends_is_discoverable.py`'s own assertions.

**Must-not 1 (wiring) — Present, verified by direct inspection, not
citation.** `on-the-record/hooks/pretooluse_dispatcher.py`'s `GATES`
list carries an `amends-index-preflight.sh` entry:

derived: `grep -n "amends" on-the-record/hooks/pretooluse_dispatcher.py`
on PR #3156's worktree — result:
```
5:round adds amends-index-preflight.sh as a 21st) used to run as separate
282:    dict(script="amends-index-preflight.sh", tools=BASH_TOOLS,
```
(`amends-index-preflight.sh` — untracked on this session's own branch,
PR #3156 branch only) — following the same dispatch shape as
`spec-index-preflight.sh`. `docs/specs/enforcement-boundary.md` and
`docs/specs/generated-paths.md` (both already tracked on this branch,
modified not added by PR #3156) each carry rows for `amends_index.py`,
the two probes, and the new hook. A test module (untracked on this
branch, PR #3156 branch only) runs `check()` against the real `ROOT`
tree and against a real on-disk temp copy with an injected unlinked
amendment — not a synthetic in-memory dict, closing exactly the gap PR
#3146 named.

**Must-not 2 (board-gate write-set isolation) — Present, reproduced
live in this session, not merely re-cited.** Attempted to write a fake
corrector record into a foreign issue's report directory (untracked —
outside this session's own write set, the write was refused before any
file was created) while working inside the PR #3156 worktree; the
harness's own board-gate refused it:

canonical: this session's own PreToolUse hook error transcript (this
turn) — result:
```
board-gate: writing docs/issue-9999/ requires branch
issue-9999/independent-verification-1 (current:
issue-3134/independent-verification-1), and issue #3134's body declares
no matching `maintenance-targets:` entry for issue-9999. Every skill
output reaches main only through a PR the human merges — never a direct
write from another branch. (contract v3 s10)
```
This independently confirms the constraint the PR's backlink module is
built around: a landing-step identity, not the correcting session, must
write the target's backlink.

**Must-not 3 (no study-companion retrofit) — Present.**

derived: `git diff --name-only main...HEAD` on PR #3156's worktree —
result: no path under a study-companion issue tree (untracked here —
study-companion is a separate repository from the issue text's own
citation, not present in this repo at all) appears in the diff; the
generated index file added by PR #3156 (untracked on this branch) shows
zero live amendments in its own content (`| (none) | | |`), consistent
with the must-not.

Citations checked, not trusted on sight: the PR's backlink module cites
`docs/issue-3050/reports/independent-verification-1.md` (tracked on
this branch already) as a prior live board-gate exercise —
`git ls-files` confirms that path exists and is committed.

## Why

canonical: this session's own acceptance-check and reproduction output
above (`## What was done`) — the two findings PR #3146 held (check 2
Absent, must-not 1 Surface) are what this verification weighted above
the four checks' mechanical pass/fail, and both are shown resolved by a
real mechanism above, not by a narrower probe.

PR #3143's original delivery was held after PR #3146's independent
verification graded check 2 (discoverability) Absent — the probe tested
"consulting the generated index," not "opening the amended record" —
and must-not 1 Surface — `check()` existed but nothing invoked it at
commit time. Issue #3134's own text names discoverability enforcement
(not the `amends:` field itself) as the primary requirement, so this
verification weighted the two held findings above the mechanical pass
of the four acceptance checks: re-running the checks alone would not by
itself distinguish a genuine fix from a probe that was loosened to pass
— derived: the independent, from-scratch `check()` fixture reproduction
above (`/tmp/pr3156_check_test.py`) and the live board-gate refusal
above are both routes the delivering session did not construct, and
both reaffirm the same result the shipped probe reports.

Every check was re-run independently rather than trusted from PR
#3156's own record, and the two prior findings were re-tested by a
route the delivering session did not itself construct (a from-scratch
`check()` fixture, and a live write-set-isolation attempt against a
genuinely foreign issue path) specifically because both prior findings
in this issue's history were "the probe measures something weaker than
its name claims" — the same failure mode a verification that only
re-runs the shipped probe cannot catch.

The result: both previously-held findings are resolved by a real
mechanism (landing-step backlink insertion + fail-closed `check()` on
two independent axes + live commit-time wiring), not by narrowing what
the probe checks. The design correctly does not attempt to relax
write-set isolation — it moves who performs the write to a landing-step
identity outside any spawned session's write set, which is the shape
the original issue's consult asked for.

## What did not work

derived: this session's own Bash/Write tool transcript (this turn) —
every acceptance command and every independent reproduction above
executed successfully on the first attempt; the only refusal
encountered (the board-gate denial reproduced under must-not 2 above)
was itself the intended test, not an obstacle to this verification's
own work.

None — this verification's own checks and reproductions all ran
without deviation from the planned approach.

## Upstream basis

- `docs/issue-3134/reports/implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310.md`
  (sha `aacd119ba1433c85b990ddb9cf74306f97d310df`, PR #3156, untracked on
  this session's own branch) — the repair round's own delivery record,
  read only after this session's own checks and reproductions were
  complete.
- `docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md`
  (sha `4671de88e50c26cc66e119a11d48736c1c743703`, PR #3146, merged to
  `main`, tracked on this branch) — the prior independent verification
  whose two held findings (check 2 Absent, must-not 1 Surface) this
  round exists to resolve.

canonical: `gh pr view 3156 --json commits` — commit `aacd119b`
("issue-3134: repair-round record for the amends discoverability +
wiring fix") is the record cited above.

## Open findings

None.

derived: the acceptance-check and reproduction output under `## What
was done` above — all four acceptance checks Present (independently
reproduced from a fresh worktree and, for check 2, a fresh from-scratch
fixture); all three must-nots Present (wiring confirmed by direct grep
of the dispatcher source, write-set isolation reproduced live via this
session's own refused write attempt, no-retrofit confirmed by
`git diff --name-only`). This session did not merge, edit, or approve
PR #3156.

## Next steps

derived: the `## Open findings` section above (this record, this turn)
— no open finding remains to drive a next step.

None. Applying the resolved mechanism to the actual study-companion PR
pair referenced in issue #3134's own text remains explicitly out of
scope per issue #3134's own must-not 3 and is a separate decision, as
PR #3156's own record also notes.

skill-verdict: work-in-english — applied: invoked; commit messages, PR body, and this record body written in English per the skill, with this Korean-facing summary reserved for the final chat reply.
other mounted skills: not triggered
