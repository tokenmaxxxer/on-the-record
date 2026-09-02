---
issue: 3134
role: adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a
author: adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a
skills: adversarial-review (skill-repository(c05de12)), knowledge-management-supersession-lifecycle (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3143's own deliverable against issue #3134
code_under_review: 52c981f5dd0fd06ab4d73447c8d90a3e50d77595
type: defect-verification-record
breaking: false
verdict: Mixed, worse than the delivering session's own claimed 4/4. Check 1
  (tests/test_amends_resolution.py) Present. Check 3
  (probe_amends_fails_closed.py) Present. Check 4 (pytest tests/) Present.
  Check 2 (probe_amends_is_discoverable.py) Absent -- the probe redefines
  "reaching A" as "consulting the generated index" rather than "opening A";
  an independently-built, on-disk copy of its own fixture tree shows a
  reader who opens the amended record directly gets zero signal. Must-not 1
  (ship the field without discoverability enforcement) Surface -- the
  enforcement script works when invoked, but nothing forces it to be
  invoked (no pre-commit hook, no enforcement-boundary.md registration, no
  pytest coverage of the real tree). Must-not 2 (board-gate write-set
  isolation) Present, verified live. Must-not 3 (no study-companion
  retrofit) Present. The PR #11 disposition case is Surface: correct
  section-grained data model, no reader-facing effect yet.
loop_state: landed
upstream:
  - path: PR #3143 (github.com/tokenmaxxxer/on-the-record/pull/3143), head
      commit 52c981f5 -- fetched read-only this session, checked out into a
      disposable worktree at /tmp/pr3143-review (outside this repo's own
      working tree, never merged, never edited); the files it introduces
      (amends.py, gates/amends_index.py, gates/probe_amends_fails_closed.py,
      gates/probe_amends_is_discoverable.py, tests/test_amends_resolution.py,
      docs/specs/amends-index.md) are therefore reachable in this repo's git
      object history via that commit but untracked on this session's own
      branch -- every such path cited below is a PR #3143 path, not a path
      on this branch
    sha: 52c981f5dd0fd06ab4d73447c8d90a3e50d77595
  - path: main (baseline for the full-suite comparison and the board-gate
      write-set-isolation probe)
    sha: 02c3c8cb58444ed0deb53f65fcd831f1eb71b28b
---

# issue-3134 — adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a record

## What was done

Independent, builder-blind verification of PR #3143 against issue #3134.
canonical: `gh issue view 3134 --repo tokenmaxxxer/on-the-record` (issue
body + 1 comment, read this session) and `gh pr view 3143 --repo
tokenmaxxxer/on-the-record --json title,body,state,headRefName,files,commits`
(read this session). The delivering session ended errored on a 429 session
limit after opening the PR; its own record claims 4/4 acceptance and all
three must-nots satisfied. Per [[defect-verification-independence-from-upstream-verdicts]]
rule 1 and rule 3, this session re-ran all four checks and all three
must-nots from a fresh worktree before reading that record's verdict, then
read the record only to compare.

Fetched the PR branch and checked it out into a disposable worktree at
/tmp/pr3143-review (never edited; PR #3143 itself was not touched, not
merged). All PR-3143 paths below (amends.py, gates/amends_index.py,
gates/probe_amends_fails_closed.py, gates/probe_amends_is_discoverable.py,
tests/test_amends_resolution.py, docs/specs/amends-index.md) live only in
that worktree, not on this branch -- see frontmatter upstream note.

**Acceptance check 1 -- python3 -m pytest tests/test_amends_resolution.py -q.**
derived: ran in /tmp/pr3143-review -- result: 19 passed. Read amends.py
(265 lines) and tests/test_amends_resolution.py (189 lines) in full. Per
[[defect-verification-independence-from-upstream-verdicts]] rule 2, wrote
7 self-authored edge cases beyond the shipped fixtures and ran them
against the same amends.resolve_amendments() -- derived: `python3
my_own_edge_cases.py` in /tmp/reader-test (script written and run this
session) -- result: all 7 `PASS`:
  - a 3-hop cycle (A amends B, B amends C, C amends A) -- all 3 edges
    excluded from `amended`, reported under `cycles`
  - self-amendment (A claims to amend its own section) -- excluded,
    reported as a 1-node cycle
  - `amends: path` with no `#anchor` -- parses as no field at all (this
    is supersedes:'s job, not a smaller amends:)
  - a `./`-prefixed target path -- normalizes to match the stored key,
    mirroring supersession.py's own normalization contract
  - a 3-way conflict (three correctors on the same target#section) --
    all three listed, none wins by default
  - one corrector amending two different sections of the same target --
    both land independently in `amended`
  - the reader-only-needs-content contract (no filesystem/git access)
Grade: **Present**.

**Acceptance check 2 -- python3 gates/probe_amends_is_discoverable.py.**
derived: ran in /tmp/pr3143-review -- result: exit 0, `ok`. Read the probe
(191 lines) in full. It builds a synthetic tree (record A = a
study-companion-shaped record with a wrong "Limitation" section, record B
= a corrector naming `amends: A#limitation`), asserts
resolve_amendments() resolves it, then asserts the generated index
(amends_index.render_index()) contains a row naming the amendment, and
that amends_index.check() refuses when that index is absent or stale. All
of that is true and independently reconfirmed below. But the issue's own
acceptance text is stricter than what the probe checks: "a reader with
only the merged tree ... **reaching A** cannot miss the amendment" -- and
the probe's own module docstring (lines 20-32) states "A's own raw
content, read in isolation, carries no signal that it has been amended"
as the *expected, confirmed* outcome, not a failure. The probe
substitutes "reaching the generated index" for "reaching A."

Per the task's explicit instruction, this session built the identical
tree as real files on disk (not the probe's in-memory dict), in a scratch
directory outside this repo (/tmp/reader-test/fixture-tree/, git-untracked,
no relation to this branch's write set): a target record shaped like
docs/issue-10/reports/coding.md (substance matching the probe's own
`TARGET_CONTENT`) and a corrector shaped like
docs/issue-15/reports/verification.md carrying
`amends: docs/issue-10/reports/coding.md#limitation  # ...`, then ran
`gates/amends_index.py --update` against that scratch tree to generate a
real amends-index.md -- and acted as a reader with only that merged tree,
trying the routes named in the task:
  - **Open A directly**: `cat` on the target record's full content --
    derived: ran this session -- result: no mention of an amendment, no
    marker, no pointer anywhere in its bytes; a follow-up
    `grep -i "amend"` against that same file -- derived: ran this session
    -- result: no match.
  - **Grep for a claim in A**: a repo-wide grep for a phrase from A's own
    wrong claim ("scoring function") surfaces both A and B in this
    specific fixture -- but only because the corrector's `reason` text
    happens to reuse those words from A. That overlap is incidental to
    this crafted example, not something amends.py or amends_index.py
    guarantees; a corrector using different vocabulary (e.g. "the metric
    conflates recall with comprehension") would produce no such grep hit.
    Not a route the mechanism itself secures.
  - **Follow a link into A**: a repo-wide grep for A's own path returns
    only B and the generated index -- nothing else in the tree points at
    A, and nothing routes a reader who has not yet found the index toward
    it.
  - Confirmed separately (script `check_my_tree.py`, written and run this
    session): amends_index.check() correctly refuses with the index
    deleted ("...missing, but the tree has live amends: edges..."), and
    with it tampered/stale ("...is stale..."), and passes once
    regenerated -- the enforcement mechanism itself is functionally
    correct in isolation (see must-not 1 below for whether anything
    actually invokes it).

Conclusion: a reader who opens the amended record -- the literal act the
issue's acceptance text names ("landing on the amended record") -- meets
nothing. Only a reader who already knows, independent of anything in the
record or linked from it, that a separate generated index exists and must
be cross-checked before trusting any record's prose, would find the
amendment. That is exactly the failure mode the issue's own consult
warned about ("without that enforcement, amends: is just today's problem
with an extra layer") -- the index is reachable from the merged tree in
the sense that it is a checked-in file, but it is not reachable *from A*,
which is what "reaching A cannot miss the amendment" actually requires.
Notably, the delivering session's own record makes exactly this argument
against the *rejected* alternative -- a reader who never opens the
corrector's record has no path to the correction at all -- without
recognizing that its own chosen index has the identical property: a
reader who never opens the index has no path to the correction either,
and nothing in A, or in the act of opening A, prompts them to look.
Grade: **Absent**.

**Acceptance check 3 -- python3 gates/probe_amends_fails_closed.py.**
derived: ran in /tmp/pr3143-review -- result: exit 0, `ok`, with the
probe's own output reporting `ok` for each of its four named cases
(dangling target, missing section anchor, conflicting correctors, cycle).
Those four cases overlap the 7 independently-authored cases already run
under check 1 above (same function, resolve_amendments()) -- derived:
`python3 my_own_edge_cases.py`, result above, all `PASS`. The ordering
guarantee (broken/missing_section excluded before conflict detection,
conflicts excluded before cycle detection) was read in amends.py's
resolve_amendments() docstring and confirmed against this session's own
3-way-conflict and 3-hop-cycle cases above, which do not cross-contaminate
each other's buckets. This mirrors supersession.resolve_authoritative()'s
contract as claimed. Grade: **Present**.

**Acceptance check 4 -- python3 -m pytest tests/ -q.** derived: ran in
/tmp/pr3143-review -- result: 273 passed, 2 warnings. The task description
named 254 as the expected green count; the higher number here is
consistent with `git log --oneline -5` on this branch showing #3141 and
#3142 as landed on main after PR #3143's own base commit -- canonical:
this session's own repo git-status context at session start listed
02c3c8cb, d4da990e, 73b614fd, b35391ea, a80cd550 as the 5 most recent main
commits, none of which is PR #3143's own base -- not a regression
introduced by this PR. Grade: **Present**.

Also ran `python3 -m pytest test/ -q` (the separate, pre-existing test/
tree) -- derived: ran in /tmp/pr3143-review -- result: 15 failed, 548
passed, 3 xfailed. Read the 15 failure names: 2 in
test_convention_equivalence.py, 1 in test_local_dependency_env.py, 6 in
test_spawn_cross_family_skill_selection.py, 2 in
test_spawn_artifact_skill_pairing.py, 4 in
test_spawn_skill_judge_haiku_timeout_overlap.py (2+1+6+2+4 = 15) -- all
about spawn/skill-selection/convention-equivalence machinery, none
importing or exercising amends.py, gates/amends_index.py, or
supersession.py. Matches the task's framing of "15 pre-existing failures
owned by #3091," reported separately from the tests/ green count, not
folded into a combined pass/fail number.

**Must-not 1 -- do not ship the frontmatter field without the
discoverability enforcement.** amends_index.py's check() is functionally
correct in isolation (verified above, independently, with a tampered and
a deleted index). But three things this session checked narrow "shipped
with enforcement" to a script that exists and works only if invoked, not
enforcement in the sense spec_index.py -- the PR's own stated precedent --
actually has in this repo:
  - `on-the-record/hooks/spec-index-preflight.sh` (this repo's own file,
    confirmed present at that path this session) is a real PreToolUse
    hook that denies `git commit` before it lands when a tracked spec
    file drifts from its index, ported inline specifically because (per
    its own docstring) spec_index.py alone "runs on the working tree
    after a commit has already landed." No equivalent hook referencing
    amends_index or amends.py exists anywhere under
    `on-the-record/hooks/` -- derived: `grep -rl "amends_index\|amends\.py"
    --include=*.sh --include=*.yml --include=*.yaml .` in the PR
    worktree -- result: no matches.
  - `on-the-record/hooks/gate-registration-guard.sh` (this repo's own
    file, confirmed present at that path this session) denies a `git
    commit` staging a new gates/*.py file (excluding test_*.py) with no
    matching row in `docs/specs/enforcement-boundary.md` (this repo's own
    file, confirmed present at that path this session). This PR adds
    three such files. derived: `grep -in "amends"
    docs/specs/enforcement-boundary.md` in the PR worktree -- result: no
    matches, and `git diff main...HEAD -- docs/specs/enforcement-boundary.md`
    in the PR worktree -- result: empty, the file was not touched. For
    contrast, this repo's own precedent for the analogous #3050 probe,
    probe_supersession_marker.py, does have a row, at
    docs/specs/enforcement-boundary.md line 115 (read this session,
    present in this repo's own checkout), explicitly stating it is
    manually invoked and not wired into any hook -- a documented,
    accepted gap. This PR's three new files have no row at all,
    documented or not.
  - tests/test_amends_resolution.py (read in full, 189 lines) only calls
    amends.resolve_amendments() against synthetic in-memory dicts; it
    never calls amends_index.check() against the real docs/specs/amends-index.md
    and the real docs/issue-*/reports/ tree, so nothing in the pytest
    suite that actually runs would catch a real amendment landing without
    a regenerated index.
  Net: the letter of the must-not (a script exists, and it is not a
  no-op) is satisfied; the substance the must-not exists to protect --
  "a field nobody is required to link to" not reproducing "today's
  problem with more machinery" -- is not, because nothing in this repo's
  actual gate/hook pipeline requires anyone to link it. Grade:
  **Surface**.

**Must-not 2 -- do not relax board-gate's write-set isolation.**
`git diff main...HEAD -- '*board-gate*'` in the PR worktree -- derived:
ran this session -- result: empty output, the file is untouched. Beyond
the diff, this session constructed a live cross-session write from this
session (issue-3134) into an existing foreign record at
docs/issue-3050/reports/independent-verification-1.md (present in this
repo's own checkout, confirmed by Read this session) -- an Edit tool call
attempting to add a probe line to its frontmatter. canonical: the
PreToolUse hook refusal, this session's own turn, verbatim: "board-gate:
writing docs/issue-3050/ requires branch issue-3050/... (current:
issue-3134/...), and issue #3134's body declares no matching
`maintenance-targets:` entry for issue-3050. ... (contract v3 s10)".
Refused exactly as supersession.py's own module docstring describes the
boundary. Grade: **Present**.

**Must-not 3 -- do not retrofit the two existing study-companion
verification records into amends: edges.** `gh pr view 3143 --json files`
-- derived: ran this session -- result: exactly nine changed files
listed (9 = amends.py + 2 handbook files + this PR's own report + the
index + 3 gates files + the tests file): amends.py,
docs/handbooks/record-authoring.md, docs/handbooks/record-contract.md,
this PR's own docs/issue-3134/reports/ record, docs/specs/amends-index.md,
gates/amends_index.py, gates/probe_amends_fails_closed.py,
gates/probe_amends_is_discoverable.py, tests/test_amends_resolution.py --
no file under docs/issue-10/ or docs/issue-15/ appears in that list.
Grade: **Present**.

**The case this was built for -- study-companion PR #11's Limitation
section.** Per [[knowledge-management-supersession-lifecycle]] rule 11 (a
change is a supersession if the original reasoning no longer holds, a
plain edit/annotation if it still holds), what issue #3134 asked for is
neither -- a third shape: "this section's reasoning is wrong, the rest of
the record's reasoning still holds." Structurally, amends.py's data model
gets this right: resolve_amendments() marks only
`{target: {section: corrector}}`, leaving every other section of the
target un-mentioned and therefore, unlike supersedes:, never marked
non-authoritative -- a real, section-grained result distinct from
whole-record supersession, confirmed in this session's own resolver runs
above. But per this session's discoverability finding (check 2), that
correct data model has no reader-facing effect yet for someone who lands
on PR #11's actual record and reads its Limitation section directly --
they get the same wrong axis, the same "scoring function is confirmed to
read the generated question" claim the issue says is false, with nothing
in the record or in the act of opening it suggesting otherwise. Not
"collapses to whole-record supersession" (the record does not become
non-authoritative, and the rest of it is still trusted, correctly) --
something arguably harder to notice: an amendment that exists in the
tree, resolves correctly when queried programmatically, and is invisible
to exactly the reader path the issue was written to close. Grade:
**Surface**.

## Why

[[defect-verification-independence-from-upstream-verdicts]] rule 1 (a
Present verdict is a claim to test, not a settled fact) and rule 9 (a
clean upstream record does not lower the number of self-devised attempts)
drove re-running all four checks from scratch on a fresh worktree before
reading the delivering session's record, and devising edge cases beyond
its shipped fixtures rather than treating a clean tests/ run as
sufficient -- derived: `python3 my_own_edge_cases.py` and
`check_my_tree.py`, both run this session, results reported under checks
1 and 2 above. [[adversarial-review]]'s blindness principle (evaluate the
artifact, not the builder's stated intent) drove building the
discoverability fixture on disk and reading it back as a naive reader
would, rather than accepting the probe's own framing of what "reaching A"
means. [[knowledge-management-supersession-lifecycle]] rule 11 framed the
PR #11 disposition question as a third lifecycle shape (section
correction) distinct from both supersession and plain edit, which is what
let the "structurally correct, reader-facing inert" split verdict on that
case be stated precisely instead of collapsed into a single pass/fail --
canonical: this session's own check-2 and PR-#11-disposition findings
above, both derived from commands run this session.

## What did not work

None -- every check and must-not was reproduced; the finding is that one
acceptance check and one must-not do not hold up under independent
reproduction, not that reproduction itself failed to run.

## Upstream basis

PR #3143, commit 52c981f5dd0fd06ab4d73447c8d90a3e50d77595 -- canonical:
`gh pr view 3143 --repo tokenmaxxxer/on-the-record --json ...`, read this
session; fetched read-only and checked out into a disposable worktree at
/tmp/pr3143-review, never committed to or merged -- derived:
`git worktree list`, run this session, showing that worktree at
52c981f5, detached HEAD. main at 02c3c8cb58444ed0deb53f65fcd831f1eb71b28b
as the board-gate refusal baseline -- canonical: this session's own repo
git-status context at session start. Fixture trees built this session at
/tmp/reader-test/ (outside this repo, git-untracked). Issue #3134 and PR
#3143, both read this session via `gh issue view 3134` and
`gh pr view 3143`.

## Open findings

- Acceptance check 2 (probe_amends_is_discoverable.py) grades Absent
  against this session's independent reconstruction of the reader test the
  issue's own text specifies, despite exiting 0 -- derived: the check-2
  section above, all commands run this session. Resolution path: the
  probe's assertion needs to move from "the generated index contains the
  row" to "something reachable from opening the amended record itself
  surfaces the amendment" -- e.g. a per-record convention that is itself
  gate-enforced on every record (not just amended ones), or a
  record-shape-directive-level requirement, not left to a reader's prior
  knowledge of the index convention.
- Must-not 1 grades Surface: amends_index.py needs the same
  PreToolUse/git-commit wiring spec-index-preflight.sh gives spec_index.py,
  plus a docs/specs/enforcement-boundary.md row for itself and the two new
  probes (even a "manually invoked, not wired in" row, matching
  probe_supersession_marker.py's own precedent, would be more honest than
  the current silence) -- derived: the must-not-1 section above, all
  commands run this session.
- The PR-#11-disposition case (Surface) will not resolve until the above
  two are fixed -- the shape is otherwise ready to carry the correction
  session's already-drafted text.

## Next steps

None from this session. verdict frontmatter and the grades above are this
session's terminal output -- canonical: the acceptance-check and
must-not sections above, each derived from a command run this session.
loop_state is landed. Next action belongs to whoever picks up the two
Open findings above, most likely a follow-up round on issue #3134 or a
new issue for the discoverability gap specifically.

skill-verdict: adversarial-review — applied: invoked; evaluated PR #3143's artifacts (amends.py, gates/amends_index.py, the two probes, the two handbook diffs) blind to the delivering session's own record until after independently forming a verdict, per the skill's core mechanism (session separation) and its Step 3 gate against answering "what was this supposed to do" -- re-derived the discoverability property from a freshly-built fixture tree rather than accepting the probe's own framing.

skill-verdict: knowledge-management-supersession-lifecycle — applied: invoked; rule 11's edit-vs-supersession-vs-something-else test framed the final "case this was built for" verdict as a third shape (section correction), distinct from both plain edit and whole-record supersession.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; rules 1, 2, 3, and 9 drove re-deriving every check and must-not from a fresh worktree before reading the delivering session's own claimed verdict, and devising self-authored edge cases beyond the ones shipped in the PR's own tests and probes.
