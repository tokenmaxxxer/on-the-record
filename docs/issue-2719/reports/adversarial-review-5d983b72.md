---
issue: 2719
role: adversarial-review-5d983b72
author: adversarial-review-5d983b72
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2721's deliverable
loop_state: landed
code_under_review: dfbfaaa79f4bd8076c4b8c09fb56df8788bf4d69
type: verification
breaking: false
verdict: CONFIRMED — all three dispositions, the direction-of-effect ruling on site 1, and the enumeration hold under independent re-testing; one minor citation-accuracy defect (a "byte-identical" diff claim is not literally reproducible, though the underlying values are equal)
upstream:
  - path: docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md
    sha: dfbfaaa79f4bd8076c4b8c09fb56df8788bf4d69  # untracked on this branch (issue-2719/adversarial-review-5d983b72) — lives on PR #2721's branch at this commit; canonical: `gh pr diff 2721`, read live
---

# issue-2719 — adversarial-review-5d983b72 record

## What was done

Independently re-verified PR #2721 (`dfbfaaa79f4bd8076c4b8c09fb56df8788bf4d69`,
canonical: `gh pr view 2721 --repo tokenmaxxxer/on-the-record`, read live)
against its own subject record, re-deriving every claim from the PR head
rather than citing the subject's prose. Checked out the PR head in an
isolated worktree — derived: `git fetch origin pull/2721/head:pr-2721-verify
&& git worktree add /tmp/pr2721-verify pr-2721-verify` — and ran all
commands below against that checkout, not the subject's transcript.

**1. Site 1 (`upstream-defect-scope-guard.sh`, kept) — the ruling's premise
tested directly, not read.** The operator's ruling (canonical: `gh issue
view 2719 --comments`, read live) rests on three parts: (a) the check adds
a denial rather than an exemption, (b) removing it demonstrably widens the
gate, (c) the name is the file's own subject, not one of several it
dispatches on. I tested (a)+(b) by patching a copy of the hook to force
`channel_role_active = False` (simulating removal of `CHANNEL_SKILL`) and
running it against a channel session (`MUSTER_SKILLS=upstream-defect-report`)
attempting two PR-creation shapes condition (b) is claimed unable to
cover — derived:
```
$ env MUSTER_SKILLS=upstream-defect-report /tmp/upstream-defect-scope-guard-simulated-removal.sh < payload_targetless.json; echo rc=$?
rc=0
$ env MUSTER_SKILLS=upstream-defect-report /tmp/upstream-defect-scope-guard-simulated-removal.sh < payload_ownorigin.json; echo rc=$?
rc=0
```
(payloads: `{"tool_input":{"command":"gh pr create --title x --body y"}}`
[target-less] and `{"tool_input":{"command":"gh pr create --repo
tokenmaxxxer/on-the-record --title x"}}` [own-origin, cwd =
tokenmaxxxer/on-the-record's own checkout]). Both return `rc=0` (allow) —
with the identity check removed, a channel session's target-less and
own-origin PR-creation attempts are silently allowed. Confirmed against
the real (unpatched) file too: same two payloads with `MUSTER_SKILLS`
unset (a non-channel session, i.e. condition (b) operating alone) also
return `rc=0` for both shapes — derived:
```
$ env -u MUSTER_SKILLS on-the-record/hooks/upstream-defect-scope-guard.sh < payload_targetless.json; echo rc=$?
rc=0
$ env -u MUSTER_SKILLS on-the-record/hooks/upstream-defect-scope-guard.sh < payload_ownorigin.json; echo rc=$?
rc=0
```
This is a direct test of the premise the task asked me to check hardest:
condition (b) genuinely cannot cover a channel session's own-origin or
target-less PR-creation attempt — the ruling's premise is TRUE, not false,
per this executed reproduction. Part (c): derived: `grep -n CHANNEL_SKILL
on-the-record/hooks/upstream-defect-scope-guard.sh` shows exactly one
definition and one use site (`channel_role_active = CHANNEL_SKILL in
mounted`) — a single named subject, not a dispatch table (unlike the
`("secure-coding", "release-engineering")` tuple removed from site 2).
Part (a) is directly visible in the code: `if channel_role_active: return
True` is an early-return branch of `in_scope`'s OR — an added denial, not
a carve-out narrowing an existing deny (the `OBSERVER_ROLES` shape it is
being distinguished from). Also confirmed the diff is comment-only, as
claimed — derived: `git show d329e9b9 -- on-the-record/hooks/upstream-defect-scope-guard.sh
| grep -E '^[+-]' | grep -v '^+++\|^---' | grep -vE '^\+#|^-#|^\+$'` → no
output. All three parts of the ruling's own test hold under this executed
reproduction; this PR should not be sent back on this ground.

**2. Site 2 (`merge-allow-gate.sh`, capability removed) — exercised on an
allow and a refuse/withhold payload, before and after, with my own
fixture.** Built a throwaway git repo (`/tmp/mag-fixture/repo`, branch
`issue-4242/secure-coding`, one commit touching `auth/login.py`, a stub
`gates/landing_readiness.py` printing `PR #42: READY`) independent of the
subject's own fixture, and ran both `git show d329e9b9^:...` (BEFORE) and
the current tree (AFTER) against it — derived:
```
BEFORE (record absent, secure-coding mounted, auth touched): rc=0, no output   (withheld)
AFTER  (same payload):                                        {"hookSpecificOutput":{...,"permissionDecision":"allow",...}}  rc=0
BEFORE, record PRESENT: same allow JSON as AFTER               (unaffected either way — matches record)
AFTER,  record PRESENT: same allow JSON
BEFORE, MUSTER_SKILLS unset: same allow JSON                   (unaffected either way — matches record)
AFTER,  MUSTER_SKILLS unset: same allow JSON
```
Matches the subject record's three-payload-shape claim exactly (canonical:
my own executed reproduction above, not the subject's transcript). Diff
matches the described shape — derived: `git show d329e9b9 --stat --
on-the-record/hooks/merge-allow-gate.sh` → `1 file changed, 43
insertions(+), 83 deletions(-)`; derived: `grep -nE
'secure-coding|release-engineering' on-the-record/hooks/merge-allow-gate.sh`
(post-change) shows only `#`-comment lines (10 hits, all in the
removal-documentation block) — the 2-name tuple and its
`TRIGGER_PATH_PATTERNS` dispatch table are gone from running code, not
relocated.

Asymmetric-loss claim, re-derived: the claim is that `quality-bar-gate.sh`
independently backstops secure-coding. Confirmed the backstop is real
(canonical: `on-the-record/hooks/quality-bar-gate.sh` lines 1-13, read
directly — its header states it emits a hard `deny`, unlike this hook's
allow-only posture) and that its `secure-coding` trigger-pattern *values*
match the removed list — derived (parsed both lists as Python lists and
compared):
```
removed list (merge-allow-gate.sh, pre-change):  ['**/auth/**','**/*credential*','**/*permission*','**/*secret*','**/*password*','**/*login*','**/*input*','**/*sanitiz*','**/*validat*']
quality-bar-gate.sh "secure-coding" list (current): [same 9 entries]
VALUES EQUAL: True
```
**Citation defect found:** the subject record's exact reproduction command
(`diff <(git show d329e9b9^:...merge-allow-gate.sh | sed -n '261,263p')
<(sed -n '240,242p' on-the-record/hooks/quality-bar-gate.sh)`) does **not**
produce "no output — identical" as claimed — derived: ran that literal
command against the PR head, got a 6-line diff (`1,3c1,3`, `EXIT=1`),
because the two lists are indented differently (8 spaces, nested in a
function, vs 4 spaces, top-level). The values are equal (confirmed above
via the Python-list comparison) so the asymmetric-loss *conclusion* is not
undermined, but the record's own "byte-identical"/"no output" phrasing
(the removal comment landed in `merge-allow-gate.sh` itself also asserts
"is byte-identical to the list removed here") does not survive a literal
re-run of its own cited command. Flagged as an open finding below, not
blocking.

**3. Site 3 (`board.py`, path-only signal) — exercised directly, before
and after, plus the disclosed-widening claim re-derived independently.**
derived (loaded `git show d329e9b9^:board.py` as a separate module
alongside the current `board.ownership_report()`, called both on the same
three `(role, path)` triples):
```
AFTER:  technical-feasibility/spikes: []           coding/spikes: []                                          coding/unrelated: [flagged]
BEFORE: technical-feasibility/spikes: []           coding/spikes: [flagged]                                   coding/unrelated: [flagged]
```
Matches the record's before/after claim exactly: the disclosed widening
(`coding` writing to `spikes/` no longer flagged) is real and is the only
behavior that changed; the historically-exempted case and the
unrelated-path case are both unchanged. Re-derived the zero-real-writes
claim independently — derived: `git log --all --diff-filter=A --
'docs/issue-*/reports/spikes/*' 'docs/issue-*/reports/postmortems/*'` → no
output, exit 0 — confirms no commit in this repo's history has ever added
a file under either subdirectory, so the widening reclassifies no real
write. Test suite — derived: `python3 -m pytest
test/test_board_ownership_report.py -q` → `6 passed in 0.78s`.

**4. Enumeration — re-run with my own command, not the subject's cited
output.** Ran the identical primary regex the subject used, against the
PR head — derived:
```
$ grep -rnE '\brole\s*==\s*"|\brole\s+in\s*\(|\bskill\s*==\s*"|\bskill\s+in\s*\(|MUSTER_SKILLS.*in\s*\(|in\s*\("[a-z-]+",\s*"[a-z-]+"\)|ROLES\s*=|_ROLES\s*=' \
    --include='*.py' --include='*.sh' . | grep -v -E '/(test|tests)/|docs/|\.md:'
```
Hits: `board.py:587` (the `("product-discovery", "technical-feasibility")`
tie-break — confirms the claimed 4th site is real, unfixed, and unchanged
by this PR — canonical: `sed -n '575,589p' board.py`, read directly) and
`board.py:892` (a comment, prose not code — correctly excluded by the
subject). Every other hit is CLI-verb dispatch (`spawn.py`'s `a.role ==
"init"`/`"ps"`/etc.) or stdlib-shaped non-identity tuples
(`("--all","--mirror")`, `("insert","replace")`, `("sessions","ledger")`)
— none is a skill/role identity gate. Ran a second, broader sweep of my
own (skill-name literals in any context, not just the subject's regex
shape) across all non-test/non-docs `.py`/`.sh` files and manually
inspected every additional hit (`gates/skip_eligibility.py`,
`gates/spawn_on_pr.py`, `harness/run_smoke.py`, `gates/gates.py`,
`scripts/measure_skill_reflection.py`) — derived: all are either comments
documenting already-removed code, test-fixture data, or CLI-argument
literals (`spawn.py consult implementation <prompt>`); none is a live
gate decision. Confirms no additional live site exists beyond the four
already named. `quality-bar-gate.sh`'s `_TRIGGER_PATH_PATTERNS` dict
independently confirmed absent from the primary regex's hits — derived:
`grep` of that regex against just that file → exit 1, no match — matches
the subject's claim that it needed a second, dict-shaped sweep to surface
it.

tokenmaxxxer-core, from a fresh clone (not the subject's) — derived: `git
clone --depth 1 https://github.com/tokenmaxxxer/tokenmaxxxer-core.git
/tmp/core-verify`, same primary regex → only two hits, both inside
`core/hooks/approval-gate.sh`'s own `#`-comment block documenting the
`OBSERVER_ROLES` removal (core#343, merged) — zero live hits, matching the
subject's claim.

**5. `core#343` precedent, re-checked.** canonical: `gh pr view 345 --repo
tokenmaxxxer/tokenmaxxxer-core` → merged; `gh pr diff 345` shows
`OBSERVER_ROLES = ("execution-observation", "conformance-review")` was a
closed-issue *exemption* (`if issue_state != "OPEN" and role in
OBSERVER_ROLES:` lifted a stricter default), so removing it makes the
gate deny strictly more — confirms the direction-of-effect distinction
the site-1 ruling and site-2 removal both lean on is drawn from a real,
correctly-characterized precedent, not an invented one.

**6. Full test suite before/after — re-derived against actual
`origin/main`, not the subject's number alone.** derived: `python3 -m
pytest -q` on the PR head → `16 failed, 531 passed, 6 xfailed` (matches
subject). Reverting only the 3 changed files to `d329e9b9^` while leaving
the new test file in place gives `17 failed, 530 passed, 6 xfailed`
— derived: `python3 -m pytest -q` after `git checkout d329e9b9^ -- board.py
on-the-record/hooks/merge-allow-gate.sh on-the-record/hooks/upstream-defect-scope-guard.sh`
— one more failure than the subject's stated "before" count, because the
new regression test
(`test_other_role_writing_alt_subdir_now_unflagged_disclosed_widening`)
necessarily fails against the un-patched `board.py` (that is what a
regression test is for). Checking out true `origin/main`
(`ca6d6a9344867b8cf7b15c4b84aef773c1a4895a`, 3 commits ahead of this PR's
merge-base `39890acfa432b88e665de3f037d65d9bb129c175` — derived: `git
merge-base HEAD origin/main`) and running the suite there gives `16
failed, 525 passed, 6 xfailed` — derived: `python3 -m pytest -q` on
`origin/main` — and `diff` against the PR-head failure-name list shows no
output — derived: `diff /tmp/originmain_failed_names.txt
/tmp/AFTER_failed_names.txt`, exit 0 — i.e. the same 16 failing test names
(derived above, both lists) appear on `origin/main` and on the PR head.
So the subject's stated numbers (16 failed/525 passed before, 16
failed/531 passed after, same names, +6 new — all derived above) hold
exactly when "before" means the real `origin/main` baseline the
acceptance criterion asks for; my own initial partial-revert reproduction
(17 failed/530 passed, derived above) was measuring a different,
non-canonical baseline and is not itself a defect in the subject's claim.

## Why

Chose to test the site-1 ruling by direct code exercise (simulated
removal + real-file exercise on adversarial payloads) rather than reading
the `in_scope` logic and reasoning about it on paper, because the task
named this as the judgment to check hardest and the operator's own ruling
states a testable premise ("condition (b) ... provably cannot cover
..."). A premise stated as provable should be tested, not re-derived by
inspection alone. For sites 2 and 3, built independent fixtures (not
reused from the subject's own transcript) so a bug specific to the
subject's fixture construction could not silently reproduce as false
agreement in my own run — canonical: my fixtures live at
`/tmp/mag-fixture/repo` (site 2) and the direct `board.ownership_report()`
calls above (site 3), both built from scratch this session. For the
enumeration, re-ran the subject's exact regex to check their arithmetic,
plus a broader, independently-designed sweep to check their regex's blind
spots — both converged on the same four-site population in on-the-record
and zero in tokenmaxxxer-core (both derived in "What was done" item 4),
which is stronger evidence of completeness than either sweep alone.

## What did not work

None.

## Upstream basis

- `docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md` — untracked on this branch (`issue-2719/adversarial-review-5d983b72`); lives on PR #2721's branch at commit `dfbfaaa79f4bd8076c4b8c09fb56df8788bf4d69` — canonical: `gh pr diff 2721 --repo tokenmaxxxer/on-the-record`, read live. The subject deliverable under verification; every claim in it was re-derived independently above rather than restated.
- PR #2721, commit `dfbfaaa79f4bd8076c4b8c09fb56df8788bf4d69` (external, canonical: `gh pr view 2721 --repo tokenmaxxxer/on-the-record`, read live) — the code under review.
- Issue #2719's operator-ruling comment (canonical: `gh issue view 2719 --comments`, read live, posted 2026-08-29) — the site-1 disposition tested above.
- `tokenmaxxxer/tokenmaxxxer-core` PR #345 (external, canonical: `gh pr diff 345 --repo tokenmaxxxer/tokenmaxxxer-core`, read live) — the `OBSERVER_ROLES` precedent re-checked in "What was done" item 5.

## Open findings

1. `on-the-record/hooks/merge-allow-gate.sh`'s in-repo comment and the
   subject record both assert the removed `secure-coding` trigger-pattern
   list is "byte-identical" to `quality-bar-gate.sh`'s own list, and cite
   a specific `diff` command as proof ("no output — identical"). Re-run
   verbatim (canonical: my own execution of that exact command against
   the PR head, "What was done" item 2), that command produces a
   non-empty diff (indentation differs: 8-space nested vs. 4-space
   top-level). The list *values* are equal (independently confirmed via
   a parsed Python-list comparison — same item 2), so the asymmetric-loss
   engineering conclusion is not affected, but the "byte-identical"
   phrasing and its cited command are not literally accurate. Resolution
   path: a follow-up correction to the in-repo comment's wording (say
   "identical values" rather than "byte-identical", or fix the cited
   command to strip leading whitespace before diffing) — cosmetic, not a
   reason to withhold merge.
2. `board.py:587`'s `_front_role` tie-break (the 4th hardcoded closed-set
   site the subject's enumeration surfaced but did not fix) and
   `quality-bar-gate.sh`'s `_TRIGGER_PATH_PATTERNS` (the borderline
   dict-shaped table) are both real and both correctly left out of this
   PR's scope — re-confirmed present and unchanged in the PR head above
   (item 4). No action needed from this verification; they are the
   subject's own named follow-ups.

## Next steps

None. `loop_state` is `landed`: PR #2721's three dispositions, its
enumeration, and its test-suite claim were all independently re-derived
above (see "What was done" items 1-6, each with its own `derived:`
command and output) and hold; only one open finding survived scrutiny (a
cosmetic citation-accuracy defect in a "byte-identical" claim, item 1
above), and it does not change the disposition of any site. The central
contested judgment — that condition (b) of `in_scope` cannot cover a
channel session's own-origin or target-less PR-creation attempt, so
removing `CHANNEL_SKILL` would widen the gate — was tested directly in
item 1 above and held; this PR should not be sent back on that ground.

## Skill verdicts

- skill-verdict: adversarial-review — applied: invoked; treated PR #2721 as the artifact under evaluation and re-derived every claim (the site-1 ruling's premise, the site-2/site-3 before/after behavior, the enumeration, and the test-suite counts) from the PR head and fresh fixtures rather than citing the subject's own transcript, per the skill's structural-independence requirement — canonical: the executed reproductions in "What was done" items 1-6 above. Found one real defect (the "byte-identical" diff claim does not reproduce as stated, item 2/open-finding 1) that the subject's own self-review did not catch.
- other mounted skills: not triggered — `defect-verification-independence-from-upstream-verdicts` and `work-in-english` guidance were followed in spirit (independent re-derivation throughout; this record and all commands are in English) but neither skill was invoked via the Skill tool this session.
