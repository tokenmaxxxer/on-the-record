---
issue: 2219
role: conformance-review
loop_state: reported
upstream:
  - path: PR #2246 (https://github.com/tokenmaxxxer/on-the-record/pull/2246)
    sha: 56b5b4cebb19e83bddd8a30e032fa23516d91e02
  - path: on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log
    sha: same-commit
subject: PR #2246 vs issue #2219's frozen `## Acceptance` section
test: on-the-record/hooks/test_record_claim_guard.py (gate) + live re-run of on-the-record/hooks/record-claim-guard.sh
result: passed
assertedBy: builder-blind conformance-review session, issue-2219/conformance-review branch, never touched the code under review
---

# issue-2219 — conformance-review record

## What was done

Builder-blind review of PR #2246 against issue #2219's `## Acceptance` section. The PR's own pasted before/after transcript was not trusted as its own proof (it comes from an unlogged `/tmp` script per the PR's own record); every requirement below was instead independently re-derived from primary sources this session could authenticate directly.

```text
Requirement extraction (issue #2219 `## Acceptance`, one obligation per line):

R1 (scope-boundary) gate: on-the-record/hooks/test_record_claim_guard.py
   names the executable gate for this issue.
R2 (edge-case) empty state: an empty record file with no claims at all
   must pass all guards cleanly, producing no denial.
R3 (functional) provenance: executed-live -- re-run the guard against the
   exact record content that produced each of the two verbatim rejections
   quoted in the issue body, and paste real before/after guard output.
R4 (error-handling) same provenance line, second clause -- a genuinely
   unevidenced claim must still be refused after the fix, shown.

Verification method per requirement:
R1: Test (existing suite, reused).
R2: Test (existing t_2219_empty_record_denies_nothing) plus an
    independent Demonstration -- the deployed hook invoked directly,
    bypassing the test file.
R3: Test, via independently reconstructed fixtures -- the two record
    fragments were extracted straight from the raw JSONL session log's
    own Write tool-call payloads (not from the PR's uncommitted script)
    and replayed as literal PreToolUse payloads against two worktrees.
R4: Test -- an unevidenced claim authored independently of the PR's own
    control case, replayed live.
```

### R1 — gate suite, re-run at PR#2246 HEAD (independently, not trusted from the PR body)

acceptance: `python3 -m pytest on-the-record/hooks/test_record_claim_guard.py -q` (PR#2246 worktree @56b5b4ce) — result:
```
...........................                                              [100%]
27 passed in 1.24s
```
derived: same command re-run against `gates/test_record_lint.py` at the same commit — result:
```
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 24.24s
```
Both numbers land where the PR body claims, cross-checked independently rather than copied.

### R2 — empty state, fired directly at the deployed hook (not only its test)

acceptance: `echo '{"file_path":".../docs/issue-9999/reports/x.md","content":""}' | ORCHESTRATE_OFF= bash on-the-record/hooks/record-claim-guard.sh` (PR#2246 worktree) — result:
```
EXIT=0
(stderr empty)
```

### R3 — provenance, independently reconstructed before/after

```text
Extracted from the raw log (on-the-record-issue-2208-implementation.session.
20260824T231045.1590418.log), not from the PR's own /tmp script:

repro1 (#870): full content of the Write tool_use at JSONL line 683
  (target docs/issue-2208/reports/implementation.md) -- carries the
  sentence quoted in issue #2219: "acceptance: diff of the two fenced
  runs above -- result: both negative cases read `completed`...".
repro2 (#333/#793): full content of the Write tool_use at JSONL line 622
  (an earlier draft of the same target file) -- carries the sentence
  quoted in issue #2219, soft-wrapped: "`fail-open`, with the full suite
  still passing 9/9."

Each was replayed as a literal {"tool_name":"Write","tool_input":
{"file_path": <original absolute path>, "content": <extracted text>}}
PreToolUse payload through the real record-claim-guard.sh, once on a
`main`@c40bef01 worktree (BEFORE) and once on the PR#2246@56b5b4ce
worktree (AFTER).
```

acceptance: replay of repro1 and repro2 through `on-the-record/hooks/record-claim-guard.sh`, BEFORE (`main`@c40bef01bb05c7a765580b7a1a912a3c656961cb) then AFTER (PR#2246@56b5b4cebb19e83bddd8a30e032fa23516d91e02) — result:
```
BEFORE / repro1: rc=2, stderr quotes issue #870, text ends
  "...both negative cases read `completed` in both runs, so neither
  changed outcome; ..." -- byte-identical to issue #2219's own quote.
BEFORE / repro2: rc=2, stderr quotes issue #333, text
  "`fail-open`, with the full suite still passing 9/9." -- byte-identical
  to issue #2219's own quote.

AFTER / repro1: rc=0, stderr empty.
AFTER / repro2: rc=2, but the denied text is now a DIFFERENT sentence
  from the same file (the "Fixed" section, item 2's first-pass note) --
  the originally-quoted "`fail-open`... still passing 9/9." sentence is
  absent from the AFTER denial entirely.

Note on root resolution: this hook's #330/#791/#1085 side checks walk up
from each payload's own file_path to the nearest .git directory. The
extracted payloads carried the session's original absolute path, so
this located the real leftover session workspace still on disk rather
than a synthetic fixture -- which is why the AFTER/repro1 run above
came back fully clean instead of tripping unrelated-repo path noise the
way the PR's own /tmp-rooted script did.
```

R3 stands verified: both verbatim rejections quoted in issue #2219 reproduce exactly against pre-fix code, and neither denies for the same reason against PR #2246.

### R4 — unevidenced claim still refused (control authored independently of the PR's own example)

acceptance: replay of an independently-authored unevidenced claim through `record-claim-guard.sh` at PR#2246@56b5b4ce — result:
```
claim text: "We found 4 of 12 findings to be genuine. The fix is
complete and tests pass." -- no fence, no derived:/canonical: tag.

rc=2
record-claim-guard: issue #333 (bare count), issue #793 (canonical
source), and issue #870 (outcome claim) all fire, each denial ending in
a would-pass sentence naming the shape that would satisfy it.
```
Enforcement is not weakened by this fix.

### Requirement blocks

---
requirement: R1 — the named gate suite is green at PR#2246 HEAD
spec_ref: issue #2219 `## Acceptance`, `gate:` line
verdict: Present
evidence: independent pytest re-run above, PR#2246@56b5b4cebb19e83bddd8a30e032fa23516d91e02.
rationale: gate-named suite is green end to end, re-run rather than trusted from the PR body.
---
requirement: R2 — empty record file produces no denial
spec_ref: issue #2219 `## Acceptance`, `empty state:` line
verdict: Present
evidence: direct hook invocation above plus on-the-record/hooks/test_record_claim_guard.py, function t_2219_empty_record_denies_nothing.
rationale: both a live direct call to the deployed hook and its pinned regression test agree on zero denials for empty content.
---
requirement: R3 — live re-run against the exact content behind both verbatim rejections, real before/after shown
spec_ref: issue #2219 `## Acceptance`, `provenance: executed-live`, first clause
verdict: Present
evidence: replay transcript above, sourced from on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log JSONL lines 622 and 683, against `main`@c40bef01bb05c7a765580b7a1a912a3c656961cb and PR#2246@56b5b4cebb19e83bddd8a30e032fa23516d91e02.
rationale: independently reconstructed from the primary log rather than the PR's own uncommitted script; BEFORE reproduces both quotes exactly, AFTER shows both no longer denied for that reason.
---
requirement: R4 — a genuinely unevidenced claim is still refused
spec_ref: issue #2219 `## Acceptance`, `provenance:` line, second clause
verdict: Present
evidence: replay transcript above, independently-authored control content at PR#2246@56b5b4cebb19e83bddd8a30e032fa23516d91e02.
rationale: control case constructed independently of the PR's own example, not a re-run of the PR's fixture, and still denied on all three rules.
---

## Why

A builder-blind review does not accept the builder's own transcript as proof of itself, so every Acceptance clause was re-derived from sources checkable independently: the raw session log's actual tool-call payloads, a `main`-vs-PR worktree pair, and direct hook invocation rather than only the test suite. Where independent reconstruction and the PR's own claimed numbers overlapped, they agreed — the PR's evidence held up under independent replay even though it was not directly trusted going in.

## What did not work

```text
First attempt at locating the R3/#333 repro grabbed the wrong tool-call:
an Edit at JSONL line 483 whose denied fragment happened to share a
trailing phrase ("...9/9 passed, unchanged.") with the real repro but
was not the sentence issue #2219 quotes verbatim. Caught this by
comparing the replayed stderr against the issue body's exact quote
(no match), then re-searched the log scoped to the phrase "still
passing 9/9", which resolved to the Write at JSONL line 622 -- its
denial matches the issue's quote character for character. R3 above is
built from the corrected fixture; the wrong Edit-based one is not
cited anywhere in this record.
```

## Upstream basis

canonical: issue #2219 body, read this session via `gh issue view 2219` — denial counts, both verbatim rejection quotes, and the frozen `## Acceptance` section.

- PR #2246, HEAD `56b5b4cebb19e83bddd8a30e032fa23516d91e02`, checked out this session at a `git worktree`.
- `main` at `c40bef01bb05c7a765580b7a1a912a3c656961cb`, checked out this session at a second `git worktree` as the pre-fix baseline.
- on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log, read this session (JSONL lines 483-485, 621-623, 682-685).
- on-the-record/directive/acceptance-format.md, read this session to check the `gate:`/`empty state:`/`provenance:` label shape against this repo's own documented convention.

## Open findings

None. All four extracted Acceptance obligations verified Present independently.

resolution path: none — no open findings to resolve.

## Next steps

None — loop_state is terminal (`reported`).

## Skill verdicts

- skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2219's `gate:`/`empty state:`/`provenance:` block into R1-R4, one obligation per line, dimension-tagged.
- skill-verdict: conformance-review-verification-method-selection — applied: invoked; Test for all four, reusing the existing empty-state regression test per rule 4 instead of re-deriving a parallel manual check.
- skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present to R1-R4 after independent re-derivation (no prior review record existed to carry forward).
- skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every verdict cites JSONL line numbers plus the exact commit sha read for each worktree.
- skill-verdict: conformance-review-finding-record — applied: invoked; wrote the four requirement blocks above with the full field list, `spec_vs_built` omitted since no Incorrect/Absent verdict was assigned.
- skill-verdict: conformance-review-sampling-derivation — not-applicable: one PR, four Acceptance obligations, full enumeration is feasible.
- skill-verdict: conformance-review-severity-classification — not-applicable: scope was never extended into risk-weighting — there were no findings to weight.
- skill-verdict: implementation-audit — not-applicable: its two-session structural-independence precondition is already satisfied by the role-handoff contract (this session never built PR #2246); its generic spawn-a-second-evaluator procedure would duplicate the conformance-review skill family already in use here.
- skill-verdict: adversarial-review — not-applicable: per the skill's own gate, conformance against a frozen written Acceptance section is "a known, objective standard" case, routed to the standard-specific tool instead — which is what the conformance-review-* family already is.
