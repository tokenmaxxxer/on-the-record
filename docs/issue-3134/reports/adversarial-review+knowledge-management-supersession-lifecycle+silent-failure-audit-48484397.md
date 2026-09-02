---
issue: 3134
role: adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397
author: adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397
skills: adversarial-review (skill-repository(c05de12)), knowledge-management-supersession-lifecycle (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of the #3134 repair round's own deliverable (PR #3143, repair commit 1eb52701)
code_under_review: 1eb5270110d142554d914845bcaf4fe09ac97cbe
type: defect-verification-record
breaking: false
verdict: Mixed. All 4 literal acceptance checks Present. Must-not 2
  (write-set isolation) and must-not 3 (no retrofit) Present. The two
  PR #3146 findings this round targeted are now literally Present at the
  mechanical/probe level -- discoverability (backlink lives in A's own
  content, confirmed on an independently-built fixture) and must-not 1
  (check() invoked from a real hook, registered, tested against the real
  tree). BUT one new, more severe finding: Incorrect on the "who writes
  it, when" resolution actually shipped. The design narrative says a
  landing-time gate refusing to MERGE was Adopted; what is wired is a
  COMMIT-time PreToolUse hook that denies the correcting session's own
  first, legitimate commit of its own record, reproduced live end to
  end, with no automated caller of the landing step anywhere in the
  repo. See "Open findings" below for the full argument and evidence.
loop_state: landed
upstream:
  - path: PR #3143 (github.com/tokenmaxxxer/on-the-record/pull/3143),
      repair-round commit 1eb5270110d142554d914845bcaf4fe09ac97cbe on
      top of PR #3143's original two commits -- fetched read-only this
      session, checked out into a disposable worktree at
      /tmp/pr3143-worktree (outside this repo's own working tree, never
      merged, never edited, removed via `git worktree remove --force`
      before this record's own commit). Every PR-3143-only file named
      below (amends.py, amends_backlink.py, gates/amends_index.py,
      on-the-record/hooks/amends-index-preflight.sh, the two probe
      scripts, the three new test modules, and the repair round's own
      95735310 delivery record) is untracked on this session's own
      branch -- reachable only through that commit's git object
      history, not present in this working tree. Referenced below by
      plain filename (not markdown code-span) for exactly this reason.
    sha: 1eb5270110d142554d914845bcaf4fe09ac97cbe
  - path: docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md
      (PR #3146) -- the independent verification this repair round was
      spawned to address; read first, per the spawning task's own
      instruction
    sha: 4671de88e50c26cc66e119a11d48736c1c743703
  - path: docs/issue-3134/reports/implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310.md
      (repair round's own delivery record; untracked on this branch,
      only reachable via PR #3143's own branch/commit history) --
      read after this session had already formed its own verdict on the
      code, per adversarial-review's blindness requirement
    sha: aacd119ba1433c85b990ddb9cf74306f97d310df
---

# issue-3134 — adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397 record

## What was done

canonical: `gh pr view 3143 --json title,body,state,baseRefName,headRefName,mergeable,commits`
(read this session, full commit list including the repair-round commit
message and PR #3146's own commit message). Independent, builder-blind
verification of the #3134 repair round against PR #3146's two findings
and the issue's own reader-invariant text, acting as a reader with only
the merged tree at every point that mattered.

Fetched PR #3143's branch and checked it out into a disposable worktree
at /tmp/pr3143-worktree (never edited, PR #3143 itself never touched or
merged; worktree removed at the end of this session -- derived: `git
worktree remove /tmp/pr3143-worktree --force` -- result: removed, `git
worktree list` afterward shows only this session's own working
directory). Every PR-3143-only file discussed below (amends.py,
amends_backlink.py, gates/amends_index.py,
on-the-record/hooks/amends-index-preflight.sh,
gates/probe_amends_is_discoverable.py, gates/probe_amends_fails_closed.py,
tests/test_amends_resolution.py, tests/test_amends_backlink.py,
tests/test_amends_index_wiring.py) lives only in that now-removed
worktree, untracked on this session's own branch -- see frontmatter
upstream note; each is named below in plain text, without a markdown
code-span, for exactly that reason; read in full there before forming
any verdict.

Acceptance check 1, python3 -m pytest tests/test_amends_resolution.py -q:
derived: ran in /tmp/pr3143-worktree -- result: 19 passed in 0.86s. Read
amends.py's resolve_amendments() (its full docstring and body) before
running anything. Grade: Present.

Acceptance check 2, python3 gates/probe_amends_is_discoverable.py:
derived: ran in /tmp/pr3143-worktree -- result: exit 0, three reader
routes printed as confirmed. Read the probe (rewritten this round) in
full: it now builds a landed fixture (post apply_backlinks()) and
asserts opening the target directly, grepping the wrong claim's own
text, and following an inbound link all surface the marker -- a real
change from the index-only fixture PR #3146 graded Absent.

Per the task's explicit instruction, this session built its own,
independently-authored fixture (different paths and content from the
probe's own), not the probe's fixture graded against itself -- written
to /tmp/reader_route_test.py via the Write tool (a heredoc `python3 -
<<'PYEOF'` attempt was refused first by board-gate as an
"un-analyzable write-capable shape"; see "What did not work"), then run
as a plain invocation. derived: `python3 /tmp/reader_route_test.py` --
result (fixture paths below are this script's own invented,
never-written-to-disk-in-this-repo strings, not repo paths; the marker
quoting below is normalized from the script's raw stdout, which used
markdown backticks around the corrector path, to plain quotes, so this
citation itself does not trip the path-reach check on a fixture string):
```
=== MERGED A CONTENT (as a reader would see, no PR body/comments/git log) ===
---
issue: 777
role: target-record
---

# issue-777 record

## Summary

All good here.

## Limitation

> **Amended** by "docs/issue-888/reports/corrector-record.md": X actually happens under condition Y; verified independently

The claim in this section is wrong: X never happens.

=== END ===
marker line: '> **Amended** by "docs/issue-888/reports/corrector-record.md": X actually happens under condition Y; verified independently'
heading at 11 marker at 13
wrong claim at line 15 marker at 13 distance 2
Does marker line ITSELF contain the section name 'Limitation'? False
Does marker line contain the reason (visible w/o consulting corrector file)? True
Summary section content near it: ['## Summary', '', 'All good here.']
No 'Amended' marker injected into Summary section: True
ALL READER-ROUTE ASSERTIONS PASSED (custom fixture, independent of the PR's own probe)
```
Route 1 (open A directly): the marker is physically present in A's own
body, directly under the heading it amends -- not only in the generated
index; no second file was opened to produce the transcript above. Route
2 (grep the wrong claim): the marker sits 2 lines from the wrong claim's
own text (derived from the transcript above: "wrong claim at line 15
marker at 13 distance 2"). The rest of the record (Summary section) is
byte-identical to its pre-landing content, confirming section grain:
only the amended section changed. One caveat: the marker line itself
does not restate the word "Limitation" -- it identifies the section
only by physical position directly under that heading (see "Open
findings" item 2 for why this is minor, not blocking). Grade: Present.

Acceptance check 3, python3 gates/probe_amends_fails_closed.py: derived:
ran in /tmp/pr3143-worktree -- result: exit 0, `ok`, with the probe's
own per-case output confirming a dangling target, a missing section
anchor, two conflicting correctors, and a 2-edge cycle each fail closed
rather than picking a winner. Grade: Present.

Acceptance check 4, python3 -m pytest tests/ -q: derived: ran in
/tmp/pr3143-worktree -- result: 323 passed, 2 warnings in 10.23s. Also
ran the task's named secondary check, python3 -m pytest test/ -q:
derived: ran in /tmp/pr3143-worktree -- result: 563 passed, 3 xfailed in
31.94s, 0 failed. The task described a 15-pre-existing-failures baseline
for that secondary suite; this branch shows 0 because it was merged
forward onto current main after issue #3091's fix landed there (per
this session's own `git log --oneline -5` at session start showing
67913ead/997a824c/d782be05/ec1fb3ca/102ab58d as the tip, none of which
is PR #3143's own base commit) -- same explanation the repair round's
own delivery record gives for the same delta, independently reproduced
here rather than copied. Grade: Present.

"Who writes it, when" -- tested directly, not read from the docstring.
The task named this as the central tension: a correcting session cannot
write the backlink (board-gate forbids writing a foreign record), so who
does, and when? canonical: this session's own PreToolUse hook-error
transcripts (three refusals, quoted below), produced by this session's
own Write/Bash tool calls this turn, not summarized from any other
source.

1. Attempted to write under a foreign, unrelated issue's report tree
   from this session (the exact issue number is only in "What did not
   work" below; irrelevant to the point being tested). Refused:
   ```
   board-gate: writing docs/issue-999/ requires branch issue-999/... (current:
   issue-3134/adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397),
   and issue #3134's body declares no matching `maintenance-targets:` entry
   for issue-999. Every skill output reaches main only through a PR the
   human merges -- never a direct write from another branch.
   ```
2. Attempted a scratch write inside this session's own issue-3134
   reports tree but outside its own role subtree. Refused:
   ```
   board-gate: docs/issue-3134/reports/_sim belongs to another skill.
   adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397
   writes only adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397.md,
   adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397/** --
   never a foreign record.
   ```
   Both refusals confirm a correcting session cannot be the writer,
   independent of and in addition to the module docstrings' own claim to
   that effect -- tested live, not merely trusted.
3. Built the target+corrector pair legitimately, inside this session's
   own role subtree this time (a _sim/ scratch directory under this
   session's own reports subtree, untracked, via the Write tool after a
   heredoc attempt was refused -- see "What did not work"), reproducing
   exactly the shape a real correcting session's own first commit
   produces: a new record with an amends: field, whose target has no
   backlink yet because nothing has landed. Then invoked the actual
   shell hook -- amends-index-preflight.sh, PR-3143-only, in
   /tmp/pr3143-worktree, untracked on this branch -- with a realistic
   simulated PreToolUse payload via a standalone script at
   /tmp/hook_probe.sh. derived: `bash /tmp/hook_probe.sh` -- result:
   ```
   amends-index-preflight: would land an unlinked amends: edge:
     - docs/specs/amends-index.md is stale -- it does not match what the tree's amends: edges resolve to -- run "python3 gates/amends_index.py --update" and commit the result in the same change.
     - unlinked amendment: docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397/_sim/sim-target.md#limitation (amended by docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+silent-failure-audit-48484397/_sim/sim-corrector.md) has no backlink in its target's own content -- a reader who opens the target directly would miss the correction. This is a LANDING-STEP action, not something the correcting session can do itself: run "python3 gates/amends_index.py --apply-backlinks" against the merged tree and commit the result.
   HOOK EXIT CODE: 2
   ```
   Exit 2 is a deny. The sim-target.md/sim-corrector.md paths named in
   that transcript existed only inside /tmp/pr3143-worktree, inside this
   session's own role subtree there, never staged, never committed, and
   are gone along with that removed worktree. This is the hook denying
   the correcting session's own commit of its own record -- the one
   action write-set isolation was supposed to leave open -- not a
   hypothetical foreign-tree write.
4. Searched the whole tree for any automated caller of the landing step.
   derived: `grep -rln "apply-backlinks\|amends_index\|amends-index" --include="*.yml" --include="*.yaml" .`
   in /tmp/pr3143-worktree -- result: no matches, and no `.github/workflows`
   directory exists in that repo checkout at all. derived: `grep -n
   "amends" gates/ci.py` in /tmp/pr3143-worktree -- result: no matches.
   derived: `grep -n "amends" on-the-record/hooks/merge-allow-gate.sh` in
   /tmp/pr3143-worktree -- result: no matches (merge-allow-gate.sh, this
   repo's own `gh pr merge`-time gate, per its registration in
   on-the-record/hooks/pretooluse_dispatcher.py -- a file that does
   exist on this branch and was read here for that registration --
   never imports or calls amends_index). The only caller of
   write_backlinks()/--apply-backlinks anywhere in the PR-3143 tree is
   the CLI's own main() plus the tests and probe.

Conclusion, and why this is Incorrect rather than Present: canonical:
the repair round's own delivery record (95735310, untracked on this
branch, cited in frontmatter upstream, read in full this session) states
the resolution "Adopted" was "a backlink applied by the LANDING step...
after the correcting PR lands, gated so an amends: edge cannot be called
linked until it happens" -- a description of a merge-time gate. What
items 3-4 above show, live, is a commit-time gate with no automated
landing step to ever satisfy it: it denies the correcting session's own
necessary commit unconditionally, and since amends_index.py's check()
scans the whole docs/issue-*/reports/**/*.md glob rather than the
staged diff, any single unresolved edge anywhere blocks every future
report-touching commit by any session on any issue, repo-wide, until a
human manually runs the CLI -- which nothing currently triggers. Grade:
Incorrect.

Must-not 2 (board-gate write-set isolation unchanged). The two refusals
quoted in items 1-2 above are themselves this check: an unrelated
cross-session write attempt and a same-issue, foreign-subtree write
attempt were both refused live, at file-subtree grain, exactly matching
PR #3146's own must-not-2 finding. Grade: Present.

Must-not 1, four literal sub-claims, each re-checked independently.
canonical: docs/specs/enforcement-boundary.md lines 117-119 and 131
(read in full this session, on this session's own branch -- this file
exists here, unlike the amends-*.py files) and
docs/specs/generated-paths.md line 72 (same, also exists on this
branch).
- amends_index.py's check() invoked from a real hook, following its
  stated precedent, spec-index-preflight.sh (which does exist on this
  branch at on-the-record/hooks/spec-index-preflight.sh and was read in
  full for comparison) -- confirmed: amends-index-preflight.sh
  (PR-3143-only) is registered in on-the-record/hooks/pretooluse_dispatcher.py's
  GATES list (that dispatcher file exists on this branch and was read
  here), and its body literally calls amends_index.check(Path(cwd))
  (read in full, PR-3143-only). Grade: Present.
- Three gates/*.py files registered in docs/specs/enforcement-boundary.md
  -- confirmed at lines 117 (amends_index.py), 118
  (probe_amends_fails_closed.py), 119 (probe_amends_is_discoverable.py).
  Grade: Present.
- A test runs check() against the real repo tree -- confirmed:
  tests/test_amends_index_wiring.py (PR-3143-only, read in full) has a
  RealTreeSelfConsistencyTest calling amends_index.check(ROOT) directly
  against the checkout's own real filesystem, plus a
  RealTreeUnlinkedAmendmentTest that copies the real tree to a temp dir
  and injects an unlinked edge. derived: `python3 -m pytest
  tests/test_amends_index_wiring.py -q` in /tmp/pr3143-worktree --
  result: 3 passed. Grade: Present.
- Plant an unlinked amendment, confirm the wired check refuses -- done
  twice, independently of the shipped test: once via the bare Python
  check() call against this session's own hand-built sim files (derived:
  `python3 gates/amends_index.py` in /tmp/pr3143-worktree against the
  sim files described in item 3 above -- result: "gate blocked:" with
  the same two reasons quoted there, exit 1), once via the actual shell
  hook (item 3's transcript, exit 2). Grade: Present -- but see the "who
  writes it, when" conclusion above for why this literal success is
  itself the larger defect: the check refuses the correcting session's
  own legitimate commit, not only a genuinely malformed one.

Must-not 3 (no study-companion retrofit). derived: `git log --oneline
--all -- "docs/issue-10/reports/research-evidence-discipline+silent-failure-audit-3b9228ee.md"`
and `git log --oneline --all -- "docs/issue-15/*"`, both run in
/tmp/pr3143-worktree -- result: empty output for both, confirming
neither path has ever existed in this repo's git history on any branch.
There is nothing to retrofit and nothing was retrofitted. Grade:
Present.

Study-companion PR-11 case: canonical: the acceptance-check-2 transcript
above (this session's own /tmp/reader_route_test.py run) is the evidence
this grade rests on, not a separate claim. Question graded: does the
shape express a one-section correction with the rest of the record
staying authoritative? The real docs/issue-10 and docs/issue-15 records
do not exist in this repo (confirmed above, must-not 3), so this is
graded on the mechanism against that independently-built fixture: the
target's Summary section was confirmed byte-identical before and after
apply_backlinks() (transcript line: "Summary section content near it:
['## Summary', '', 'All good here.']"), and only the Limitation section
gained the marker line -- section grain preserved, matching what
supersedes: cannot do (mark only one section, not the whole record,
non-authoritative). Grade: Present.

Silent-failure audit (silent-failure-audit skill, applied). canonical:
on-the-record/hooks/amends-index-preflight.sh (PR-3143-only, read in
full) and amends_backlink.py's insert_backlink() (PR-3143-only, read in
full). Four except/fail-open sites in the hook (JSON payload parse,
shlex tokenization, the git diff --cached subprocess call, the import
amends_index statement) each exit 0 on an environment gap the hook
cannot form an opinion about -- classified Handled, matching
on-the-record/hooks/spec-index-preflight.sh's own stated fail-open
contract (read in full on this branch, lines 16-22, for the comparison).
insert_backlink()'s ValueError on a missing anchor is uncaught by
design, a caller-contract violation per its own docstring -- classified
Handled (fails closed intentionally, not silently absorbed). No
Silently-Absorbed site found in either file.

## Why

The task named a specific tension to test, not just re-run the four
mechanical acceptance commands: "writing a backlink into A is writing
into a foreign record, which board-gate forbids and must keep
forbidding. Who writes the backlink, and when?" The repair round's own
design narrative treats this as settled (a landing-time merge gate,
"Adopted"). A settled design is exactly where adversarial review should
apply pressure by executing the mechanism rather than reading its
docstring: a design narrative and a GATES registry entry's actual
trigger condition are two different sources of truth that can silently
diverge, which is what happened here -- docs/specs/enforcement-boundary.md's
own row correctly says "commit-time" (read on this branch, line 117),
but the design narrative describes a merge-time gate. canonical: the
repair round's own delivery record's "What did not work" section
(95735310, untracked on this branch, read in full this session) only
reproduces write-set isolation on scratch files with no amends: field,
never a real corrector-plus-unlinked-target pair run through the actual
hook -- so nobody along the chain ran the hook against the one scenario
that matters before this review did.

The knowledge-management-supersession-lifecycle skill was checked
against this task and judged not applicable: this task verifies a
supersession-adjacent mechanism (amends: vs supersedes:), but at no
point does this session itself decide whether to mark a
knowledge-library entry superseded or deprecated -- that decision
belongs to a future correcting session using the mechanism, not to this
verification.

## What did not work

- A `python3 - <<'PYEOF' ... PYEOF` heredoc, to build the first version
  of the independent reader-route fixture, was refused by board-gate:
  "a Bash call carries an un-analyzable write-capable shape." Rewrote
  the same script as a plain file via the Write tool at
  /tmp/reader_route_test.py and ran it as `python3 /tmp/reader_route_test.py`,
  which board-gate accepted.
- canonical: the transcript in "What was done" item 1 above is the same
  target this bullet describes trying to reach. A `cat > ... <<'EOF'`
  attempt against that foreign issue's report tree (chosen to be
  obviously outside this session's write set, for the must-not-2 test)
  was refused by board-gate for the un-analyzable heredoc shape before
  board-gate's own foreign-branch check could even run against it.
  Retried the same target as a plain Bash command with no heredoc --
  refused again, this time for the actual write-set reason; not a
  blocker to work around, the refusal itself was the point.
- The same heredoc shape, this time targeting this session's own
  _sim/ scratch subtree under its own reports subtree, was refused for
  the same "un-analyzable write-capable shape" reason. Rewrote both sim
  files via the Write tool instead, which succeeded inside this
  session's own role subtree.
- All simulation files (the sim-target/sim-corrector pair, the
  reader-route script, the hook-probe script) were created only inside
  the disposable /tmp/pr3143-worktree or directly under /tmp/; none
  were ever staged or committed on this branch, and the worktree was
  removed before this record's own commit -- derived: `git worktree
  list` after removal, result quoted in "What was done" above.

## Upstream basis

See frontmatter `upstream:`.

## Open findings

1. [Incorrect, primary finding] canonical: the live hook-refusal
   transcript and the CI/merge-gate grep results in "What was done"
   item 3-4 above are the evidence this finding rests on. The "who
   writes it, when" resolution actually shipped is a commit-time
   PreToolUse hook (amends-index-preflight.sh, PR-3143-only), not the
   merge-time gate the design narrative and the repair round's own
   delivery record describe as Adopted. It unconditionally denies a
   correcting session's own first, legitimate commit of its own amends:
   -carrying record (reproduced live above), and because
   amends_index.py's check() scans the whole
   docs/issue-*/reports/**/*.md tree rather than the staged diff, any
   single unresolved unlinked edge anywhere blocks every future
   report-touching commit repo-wide, by any session, on any issue, until
   a human manually runs `python3 gates/amends_index.py --apply-backlinks`,
   which nothing in this repo currently triggers automatically (no CI
   workflow directory exists; merge-allow-gate.sh never calls into
   amends_index, confirmed above). Resolution path: either (a) wire the
   actual merge-time check onto merge-allow-gate.sh's gh-pr-merge
   trigger (matching the orchestrator-identity distinction
   amends_backlink.py's own docstring already names by pointing at
   TOKENMAXXXER_SPAWNED but never connects to), and have the
   commit-time hook check only that this commit's own newly-introduced
   edges are exempt pre-landing (since by construction they cannot be
   linked yet); or (b) automate the --apply-backlinks step as part of
   whatever process actually merges a PR, so the invariant the
   commit-time hook checks is achievable before the correcting session's
   commit is asked to satisfy it. This is not a nice-to-have: as wired,
   the amends: primitive cannot be used by the workflow it was built
   for.
2. Minor, non-blocking: the backlink marker text does not restate the
   section name/anchor itself -- it identifies the section only by
   physical position under the heading (see acceptance check 2 above).
   Sufficient for every reader route the issue and
   gates/probe_amends_is_discoverable.py actually test; would not
   disambiguate two amended sections in the same file from an isolated
   grep hit on "Amended" with no surrounding context. Not required by
   the issue's acceptance bar; noted for a future round if a record ever
   needs two amended sections at once.

amendments-reconciled: issuecomment-5508663646 — landed mid-session,
after this session's own worktree analysis of PR #3143 was already
underway. It closes issue #3134, states PR #3143 landed on `main` (commit
`1eb52701` reachable via merge `92b6ec9b`), and cites a second
independent verification, PR #3157, graded all four checks and all
three must-nots Present with no open finding. derived: `git ls-tree -r
origin/main --name-only | grep -i amends` -- result: amends.py,
amends_backlink.py, docs/specs/amends-index.md, gates/amends_index.py,
gates/probe_amends_fails_closed.py, gates/probe_amends_is_discoverable.py,
on-the-record/hooks/amends-index-preflight.sh,
tests/test_amends_backlink.py, tests/test_amends_index_wiring.py,
tests/test_amends_resolution.py -- confirming the repair-round code this
record reviews is now live on `main`, not merely on an open PR branch.
Read PR #3157's own record in full (via `git show origin/main:docs/issue-3134/reports/independent-verification-1.md`
-- that path landed on `main` after this session's own branch point,
untracked here, after this session had already formed its own verdict)
-- its must-not-2 reproduction wrote a fake corrector record into a
foreign issue's tree and had the write itself refused (the same
write-set-isolation shape this record's own item 1-2 above reproduce),
and its check()-fails-closed reproduction called `amends_index.check()`
directly against a from-scratch fixture -- but neither invoked the
actual shell hook (amends-index-preflight.sh) with a payload simulating
a real correcting session's own commit of its own unlinked amends:
record, which is exactly the scenario this record's own item 3 above
reproduces and where the Incorrect finding lives. Both prior sessions
therefore confirmed the same fail-closed behavior this record confirms,
without recognizing that the same behavior fires before landing,
against the correcting session's own necessary commit, not only against
a genuinely bad state. This record's verdict stands: Incorrect on the
primary finding, not overturned by the closure comment or by PR #3157's
Present grade, because neither tested the specific scenario the
Incorrect finding rests on. Classified INLINE-FIX per
docs/handbooks/deviation-loop.md: this line was added inside this
session's own frozen write set (this record only), and does not change
the verdict already reached before the comment landed -- it corroborates
that the code is live on `main` and that the closure's own cited
verification did not test this scenario, rather than requiring a
different verdict.

## Next steps

None from this session beyond what is stated in "Open findings" above --
issue #3134 is already closed (see amendments-reconciled above), and
this record's own PR (against the already-closed issue) uses an
Advances trailer rather than Closes, per pr-preflight.sh's own escape
hatch for a PR that does not itself close the issue it references. The
practical next step this record recommends is that finding 1 above be
raised as its own follow-up (a new issue or a re-opened #3134), since
the code it describes is confirmed live on `main`, not merely on an open
PR branch. canonical: this session's own tool-call history
this turn contains no `gh pr merge`, `gh pr edit`, or `gh pr review` call
against PR #3143 -- PR #3143 was not merged, edited, or approved by this
session. Finding 1 above needs a disposition decision (which of the two
resolution paths, or a different one) before the next round; finding 2
needs no action unless a future record amends more than one section of
the same target.

skill-verdict: adversarial-review — applied: invoked; formed this
session's own verdict on the code and an independently-built fixture
before reading the repair round's own "Why" section, per the skill's
blindness requirement
skill-verdict: silent-failure-audit — applied: invoked; audited all
error-handling sites in amends-index-preflight.sh and
amends_backlink.insert_backlink, classified Handled, no Silently
Absorbed found (see "What was done" above)
skill-verdict: knowledge-management-supersession-lifecycle — not-applicable:
this session verifies the amends:/supersedes: mechanism itself, it does
not decide to mark any knowledge-library entry superseded or deprecated
other mounted skills: implementation-audit and work-in-english were
configured for this task (task-text match); implementation-audit's
Present/Surface/Absent/Incorrect/Unverifiable taxonomy structured every
grading decision above without a separate Skill-tool invocation gap
required for a task-configured (non-mounted-for-invocation) skill;
work-in-english's routing (record in English, this session's final
user-facing summary in Korean) was followed throughout
