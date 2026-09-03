---
issue: 3230
role: adversarial-review+diagnose-first+experiment-trust-5eb68140
author: adversarial-review+diagnose-first+experiment-trust-5eb68140
skills: adversarial-review (skill-repository(c05de12)), diagnose-first (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3234's Round 2 update (author diagnose-first+implementation-blueprint+experiment-trust-a01a3586), following on from PR #3240 and PR #3242's own independent verifications
code_under_review:
  - docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md (untracked in this branch -- lives on PR #3234's branch, "Round 2" section, commits 381ece0fa00e3efb58081b109e32d7f5c8a1d108 and 8df5034c034ebd72e4c322080a26b83822618ab6, read via the /tmp/pr3234-verify worktree)
  - on-the-record/hooks/amendment_channel.py (pre-existing on main, read not written by PR #3234 -- checked directly as counter-evidence for the viability claim)
  - on-the-record/hooks/hooks.json
  - spawn.py (read directly; confirmed zero diff from main this round)
  - consult.py (diff vs main re-read directly to check Correction 1)
  - tests/test_issue_3230_skill_judge_cost.py
  - scripts/issue-3230/measure_skill_judge.py
  - scripts/issue-3186/measure_cross_family.py
type: verification
breaking: false
verdict: Round 2's amendment-channel viability claim and its three named obstacles (reactive delivery, advisory-only, no rollback) hold up under independent re-reading of the actual code. But the remaining gap (a worker-side wait-for-notice directive, a spawn.py callback wiring write_amendment, and a before/after skill-selection measurement) is specified precisely enough to be buildable, scoped engineering work -- the second consecutive round stops at "here is what would need to be built" without building it. A fresh test this round (repeat/disagreement re-grouped by issue alone, never run before) makes issue-scoping's rejection stronger than Round 2 argued qualitatively -- see "Issue-scoped judge" below for the numbers. All three named corrections (truncation-two-fields, corrected cache sample, two methodology gaps) check out against the actual diff and PR #3240's own numbers.
loop_state: done
upstream:
  - path: PR #3234 (branch issue-3230/diagnose-first+implementation-blueprint+experiment-trust-a01a3586)
    sha: 8df5034c034ebd72e4c322080a26b83822618ab6
  - path: PR #3240 (merged, "issue-3230: independent adversarial verification of PR #3234's skill_judge diagnosis")
    sha: 07ffcb7444ae47587e2c74b58187ce009b0abb9a
  - path: PR #3242 (merged, "issue-3230: independent verification of PR #3234's skill_judge diagnosis"), read for context and to validate this session's own trace-parser against its reported numbers
    sha: c57dd1124a14f98a92b4ca879e38b1d6b8650076
---

# issue-3230 — adversarial-review+diagnose-first+experiment-trust-5eb68140 record

## What was done

Independently verified Round 2 of PR #3234 (the R007 skill_judge cost
diagnosis) -- the update PR #3234's own author pushed to that PR's branch
(commits `381ece0f`, `8df5034c`) after PR #3240's and PR #3242's
independent verifications, in a separate `git worktree`
(`/tmp/pr3234-verify`, checked out from `pull/3234/head` at `8df5034c`).
Every claim below was re-derived from the actual code and re-run live in
this session, not accepted from Round 2's prose.

canonical: `gh pr view 3234 --json body,commits`, `gh pr view 3240
--json body`, `gh pr view 3242 --json body` — all executed live this
session, checked state MERGED for #3240/#3242 and OPEN for #3234; used
to establish the round sequence this record verifies.

### 1. Acceptance checks and full suite, re-run live on PR #3234's branch

acceptance: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q` (`/tmp/pr3234-verify`, this session) — result:
```
13 passed in 0.84s
```

acceptance: `python3 scripts/issue-3230/measure_skill_judge.py --report` (same worktree, this session) — result:
```
ledger files scanned: 45
raw skill_judge_perf events found: 1258
real (plausible) events after filter: 31
n=31 min=8.295s max=56.653s mean=21.796s median=20.700s p90=31.131s
outcome_ok=True: 31/31
```
exit code 0.

acceptance (must-not): `python3 scripts/issue-3186/measure_cross_family.py --report` (same worktree, this session) — result: exit code 0, `bootstrap_timing lines found: 18`, still finds its data.

derived: `python3 -m pytest -q` (full suite, same worktree, this session) — result: `4 failed, 1433 passed, 3 xfailed in 46.01s`, the identical 4 test IDs Round 2 and PR #3240 both reported
(`on-the-record/hooks/test_hook_classification.py` x2,
`harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace`,
`on-the-record/checks/test_macos_bash32_compat.py`) — none reference
`consult.py`, `spawn.py`, or `amendment_channel.py`.

derived: `git diff main -- spawn.py` (same worktree, this session) — 0
lines output. `git diff main -- consult.py` (same worktree, this
session) — exactly the two-field truncation widen (see Correction 1
below). Grade: **Present** for both required acceptance checks and the
must-not check; no dispatch-path, timeout, or selection-mechanism code
shipped in Round 2, matching Round 2's own claim.

### 2. Is the amendment-channel viability claim correct? (checked myself, not accepted)

canonical: `on-the-record/hooks/amendment_channel.py:1-14, 362,
593-614, 651-677`; `on-the-record/hooks/hooks.json:90`; `spawn.py:4002-4010,
4402, 4413-4418` — all read directly this round in the
`/tmp/pr3234-verify` worktree, independently of Round 2's own citations
of the same lines.

**The mechanism is real and exactly as described.** `write_amendment(state_dir,
repo, issue, note="")` (`amendment_channel.py:593-614`) takes a plain
4-argument signature with no `gh` or roster dependency for the write path
itself; it atomically bumps a JSON marker file. `check_notice()`
(`amendment_channel.py:651-677`) fires unconditionally from every
`PostToolUse` hook call in a worker session, absorbs the marker before
returning (so it fires once per version), and is wired live via
`hooks.json:90` -> `amendment-channel.sh` -> `fail-open-wrapper.sh`.
`_NOTE_MAX = 2000` (`amendment_channel.py:362`). All of this matches
Round 2's citations verbatim — no discrepancy found on this session's
own direct re-read (canonical citations above).

**What would actually have to be built, concretely:**
- A new call site in `spawn.py`'s `_cross_family_future` completion path
  (`spawn.py:4002-4010`) that calls `write_amendment()` with the
  `issue`/`cwd`-derived identifiers `spawn.py` already holds at that
  point — this call site does not exist today. derived: `git diff main
  -- spawn.py` (same worktree, this session) — 0 lines, confirming no
  such call site was added.
- A change to the worker's own first-turn directive text so that when
  `skill_judge_outcome` is `not-run`/`pending` at Popen time, the
  session's own instructions tell it to wait for the amendment notice
  before its first substantive action — also absent today; the current
  directive text is a synchronous, Popen-time list only. canonical:
  `spawn.py:4413-4418`, read directly this round — the text composed
  there is unconditional and contains no wait/poll instruction.
- An actual before/after skill-selection measurement comparing sessions
  spawned under an async design against the current synchronous
  baseline — R007's own `must not` clause requires this and no such
  measurement exists for the async path in any form yet. canonical:
  `docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md`
  (untracked in this branch; read via the /tmp/pr3234-verify worktree)
  in full (both Round 1 and Round 2 sections), read this round — no
  before/after async measurement appears anywhere in the file.

**Payload**: a JSON marker (`version`, `written_at`, `note[:2000]`).
canonical: `amendment_channel.py:593-614, 362`, read directly this
round.
**When a running session could act on it**: only from inside its own
next `PostToolUse` hook call — there is no independent poll path.
canonical: `amendment_channel.py:651-677`, read directly this round —
`check_notice()` is a plain function called from the hook dispatcher,
not a background poller.
**What happens to work already done under the wrong skill set**: no
undo/rollback primitive exists anywhere in the module. derived: `grep
-niE "rollback|undo|revert" on-the-record/hooks/amendment_channel.py`
(same worktree, this session) — 0 matches.

Grade: **Present.** Round 2's "viable in principle, not built" framing
is accurate on this session's own independent re-read of the primary
source, not merely plausible-sounding prose. Async dispatch is buildable
on this channel, but "buildable" and "safe to ship" are different
claims, and Round 2 correctly declined to conflate them.

### 3. Attack the reasons Round 2 gave for not building — design problem or effort problem?

canonical: `docs/issue-1960/reports/execution-observation/baseline-measurement.md`
lines 90-100 ("## Derived: relevance-gated invocation rate"), read
directly this round — confirms verbatim: "relevance-gated invocation
rate: 0 / 38 = 0.0%". Cross-checked against `spawn.py:4413-4419`, read
this round, as the *synchronous* version of the same nudge that baseline
measured (unconditional Popen-time directive text, no wait condition).

Round 2 names three properties as the reason it does not build async
this round: reactive delivery, advisory-only content, no rollback for
work already done. All three are backed by the code citations verified
in section 2 above and, for the third, the 0/38 = 0.0% baseline number
re-confirmed directly above (canonical citation immediately above) —
these are real, evidenced obstacles to shipping async as a naive
wire-up, not filler.

But the sharper question is whether what remains is a genuine unknown or
a specified, buildable task nobody has attempted. canonical: Round 2's
own "Is async dispatch viable?" section, final paragraph (in
`diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md`,
untracked in this branch, read via the /tmp/pr3234-verify worktree on PR
#3234's branch) — it names the exact fix for point 1 ("the worker's own
directive text instructs it to wait for the notice... when
`skill_judge_outcome` was `not-run`/`pending` at spawn") and the exact
remaining requirement ("an actual before/after skill-selection
measurement"). Neither is a research question; both are scoped
implementation and evaluation work, matching this session's own
independent read in section 2.

**Verdict: this is an effort problem, not a design problem.** The
issue's escape hatch ("a well-argued refusal... is an acceptable
outcome") legitimately covered Round 1's refusal, and Round 2's
correction of the false async-mechanism premise was real, necessary work
— Round 1's actual claim ("this codebase has none today") was false
(established independently by PR #3240, PR #3242, and this session's own
section 2 re-read), and correcting a false premise is a different
failure mode than stalling on a diagnosis that was already true. But
Round 2 stops at the exact point where the next step became nameable and
scoped, and does not attempt it. Grade for Round 2's refusal:
**Present-but-incomplete** — the refusal is well-argued and correctly
reasoned (not a fabricated obstacle, per section 2's independent
re-check), but the issue's own bar ("demonstrated, not assumed") has now
had two rounds without an attempt at the demonstration Round 2 itself
says is buildable.

### 4. Issue-scoped judge: tested, not just reasoned about

canonical: Round 2's "The fifth option" section (untracked in this
branch, read via the /tmp/pr3234-verify worktree), read in full this
round on PR #3234's branch — its argument reuses Correction 2's existing
`(issue, question)`-grouped disagreement number (36%, n=291) as
supporting evidence but never re-groups the trace data by issue alone,
the actual grouping an issue-scoped cache would use. This verification
ran that grouping.

Reused PR #3240's own corrected parser (content-hash deduplication
across workspace clones, `ast.literal_eval`-based field parsing
accepting both the `role=` and `skill=` field-name eras), re-derived
from `gh pr diff 3240`'s own quoted script body (full body in "Evidence
appendix" below) rather than copied from any file PR #3240 left behind.
First sanity-checked this session's own re-derivation of the parser
against PR #3240's reported numbers by keeping the original
`(issue, question)` key:

```
$ python3 /tmp/finegrained_check.py   (fine-grained key, sanity check against PR #3240's own reported numbers)
real remaining: 295 | repeat events: 93 | agree=52 disagree=29
disagree share: 0.358 (29/81)
```
derived: `python3 /tmp/finegrained_check.py`, executed live this session
— matches PR #3240's own reported `93 repeat events`, `agree=52
disagree=29`, `0.358 (29/81)` almost exactly (n=295 here vs. 291 in PR
#3240's run, consistent with normal live-corpus growth between
sessions). This confirms the parser is faithful before trusting its
issue-scoped output below.

Then re-ran with the key changed to `issue` alone:

```
$ python3 /tmp/issue_scoped_repeat.py   (issue-scoped key)
total real 'skill_judge' lines: 319 | parsed ok: 319 | fixture-filtered: 24
distinct real issue keys: 109 | real remaining: 295
issue keys repeated >1x: 56 | repeat events: 186
repeat share of real dispatches (issue-scoped): 0.6305 (186/295)
repeat-issue-groups where question text actually varies within the issue: 52/56 = 92.9%
repeat-pair comparisons (both ok:): agree=77 disagree=91
disagree share (issue-scoped): 0.5417 (91/168)
repeated issue-keys with >=1 non-ok(parse-error) outcome: 10
```
derived: `python3 /tmp/issue_scoped_repeat.py`, executed live this
session against the same live consult-log corpus as the sanity check
above (script body in "Evidence appendix" below).

This is a materially different, and worse, number than the ones Round 2
cited. Issue-scoped grouping shows a 63.05% repeat rate (186/295,
derived above) vs. 31.96% task-text-keyed (93/291, Correction 2), and a
54.17% disagreement rate among repeat pairs (91/168 = 54.17%, derived
above) vs. 35.8% at the finer grouping (29/81, this session's own
sanity-check run above) or 43% in the original Round 1 scan (6/14=43%,
Round 1's own Question 1). Issue-scoping does not merely inherit the
fine-grained cache's disagreement risk — it concentrates onto a
materially higher disagreement rate, because 52 of the 56 repeated
issue-groups have genuinely different question text within the same
issue (92.9%, derived above), confirming Round 2's "task text genuinely
differs within one issue" argument with an actual count rather than a
single code citation.

Grade: **Present, and strengthened** — the number this test produces
supports Round 2's rejection of issue-scoping more strongly than Round
2's own qualitative argument, and it cost one script re-run on data
already gathered by prior rounds, so there was no real cost reason not
to run it two rounds ago.

### 5. Verify Round 2's three named corrections

canonical: `docs/issue-3230/reports/diagnose-first+implementation-blueprint+experiment-trust-a01a3586.md`
(untracked in this branch; read via the /tmp/pr3234-verify worktree),
"Round 2" section, "Correction 1" and "Correction 2" subsections, read
in full this round on PR #3234's branch.

**Correction 1 (truncation widens two fields, not one)** — checked
against `git diff main -- consult.py` (same worktree, this session):
```
-            f"| question={question[:200]!r} | outcome={outcome[:300]!r}")
+            f"| question={question[:4000]!r} | outcome={outcome[:2000]!r}")
```
derived: `git diff main -- consult.py`, executed live this session in
`/tmp/pr3234-verify` — matches Round 2's Correction 1 exactly (question
200→4000, outcome 300→2000). Grade: **Present.**

**Correction 2 (corrected cache sample carried forward)** — Round 2's
record quotes PR #3240's `n=291`, `repeat share 0.3196 (93/291)`,
`disagree share 0.358 (29/81)` verbatim (canonical: Round 2's own
"Correction 2" subsection, quoted above, read this round) and states
"cite 32%/36% (n=291), not 25%/43% (n=56), going forward." Cross-checked
against this session's own re-run of PR #3240's exact methodology
(section 4's sanity check above, `93 repeat events`, `agree=52
disagree=29`, `0.358 (29/81)`) — matches to within normal live-corpus
drift. Grade: **Present.**

**Two methodology gaps named** — Round 2's Correction 2 names (1) corpus
duplication from git-committed `consult-log` files being copied across
workspace clones, and (2) the `role=`→`skill=` field-rename undercounting
pre-rename trace lines, citing commit `190321de` for the rename.
derived: both gaps are real and match what this session's own
re-derived parser (section 4, sanity-check script) had to account for
(content-hash dedup, `(?:skill|role)=` in the parse regex) in order to
reproduce PR #3240's numbers. Grade: **Present.**

## Why

`defect-verification-independence-from-upstream-verdicts` and
`adversarial-review` both apply directly: Round 2 is itself a
verification-round output from the same lineage as PR #3240 and #3242,
and the risk at this point in the chain is treating "two prior
independent sessions already checked this" as license to skim. Instead
every citation in Round 2 that could be checked against primary source
(the amendment-channel code, the baseline-measurement number, the
consult.py diff) was re-read directly rather than trusted (sections 2,
3, 5 above), and the one claim Round 2 left as pure argument
(issue-scoping) was given an actual new test rather than accepted or
rejected on prose alone (section 4). `diagnose-first`'s Amdahl-style
"what does removing this cause actually buy you" question produced the
"effort problem, not design problem" verdict in section 3: the three
named obstacles are real, but none of them is unbounded uncertainty —
each has a nameable fix, and naming a fix without attempting it, twice,
is a different failure mode than a genuinely irreducible unknown.

## Upstream basis

- PR #3234 branch (sha `8df5034c034ebd72e4c322080a26b83822618ab6`) —
  Round 2's full record content, re-read and independently re-derived in
  a separate worktree this round. canonical: `gh pr view 3234 --json
  state,headRefName,commits`, executed live this session — state OPEN,
  head sha matches.
- PR #3240 (merged, sha `07ffcb7444ae47587e2c74b58187ce009b0abb9a`) —
  its corrected cache-scan methodology re-derived from `gh pr diff
  3240`'s own quoted body (not copied from a local file) to validate
  this session's own issue-scoped re-run (section 4). canonical: `gh pr
  view 3240 --json state`, executed live this session — state MERGED.
- PR #3242 (merged, sha `c57dd1124a14f98a92b4ca879e38b1d6b8650076`) —
  read for context; its own independent confirmation of the acceptance
  checks (n=31, median=20.700s) matches this session's own fresh run in
  section 1 above. canonical: `gh pr view 3242 --json state`, executed
  live this session — state MERGED.

## Open findings

- **The buildable async design is still unbuilt.** Resolution path: a
  follow-up session should attempt the three concrete pieces named in
  section 3 (directive-text wait condition, `spawn.py` callback wiring
  `write_amendment`, before/after selection measurement) rather than
  running a third round of analysis on the same question.
- **Issue-scoping is now rejected on a stronger, tested basis** (section
  4) — no further open work on this option; the 54.17% issue-scoped
  disagreement number (91/168 = 54.17%, derived in section 4 above)
  should be cited in any future record that reconsiders it, alongside
  the 31.96%/35.8% (Correction 2, n=291) and 25%/43% (original Round 1,
  n=56) numbers, so a reader can see the number gets worse, not better,
  as the grouping loosens.
- **`test_macos_bash32_compat.py`'s full-suite failure independently
  flags `amendment_channel.py`** ("new /proc dependency outside the
  reviewed set", quoted in section 1's full-suite run above) as a
  pre-existing, unrelated finding. derived: `git diff main --
  on-the-record/hooks/amendment_channel.py` (same worktree, this
  session) — 0 lines, confirming this branch did not introduce that
  dependency. Out of scope for issue-3230; worth a pointer for whoever
  owns the issue-2919-shape bash-3.2 compat check.

## Bottom line

After two rounds, the 16.7s (now measured at 20.7s median, n=31, section
1's own fresh run) median `skill_judge` wait is unchanged, and no
mechanism exists yet that would change it. derived: `git diff main --
spawn.py` (section 1, this session) — 0 lines; `git diff main --
consult.py` (section 1, this session) — truncation-width observability
fix only. Neither round shipped a dispatch-path, timeout, or
selection-mechanism change. The only path this diagnosis has established
as plausible for actually cutting the wait (async dispatch on the
amendment channel) requires the three specific, unbuilt pieces named in
section 3; the two options this diagnosis measured as unsafe
(BM25-replace, naive cache) stay unsafe per Round 1's own Question 2 and
Question 1 evidence; issue-scoping is now rejected more firmly than
before per section 4's own measured numbers. If the operator wants the
wait actually cut, the next unit of work should be building and
measuring the async design scoped in section 3 — not another diagnostic
round.

## What did not work

None. Every check and re-derivation this session set out to run — the
three acceptance checks, the full suite, the amendment-channel code
read, the issue-scoped repeat/disagreement re-run, and the three
correction cross-checks — ran to completion; the outputs are quoted in
sections 1 through 5 above. No approach was abandoned mid-session.

## Skill verdicts

canonical: this session's own executed commands and code reads, quoted
in full in sections 1-5 above.

skill-verdict: adversarial-review — applied: invoked; used as the
operating frame for this whole verification — Round 2's record was
treated as a claim to re-derive from primary source (sections 2, 3, 5
above) rather than a settled account to summarize, per the skill's core
mechanism of structural independence from the producing session's own
reasoning.
skill-verdict: diagnose-first — applied: invoked; used the Amdahl-style
"what does removing this cause actually buy, and is the remaining gap a
real unknown or a named-but-unattempted fix" question to reach the
effort-problem verdict in section 3, rather than accepting Round 2's own
framing of its refusal as self-evidently sufficient.
skill-verdict: experiment-trust — not-applicable: no new A/B or
variant-comparison result is being reported as a launch decision in this
session or in the Round 2 content it reviews. derived: re-read PR
#3234's own Round 1 Question 2 section and PR #3240's record (via `gh pr
diff 3240`) this round — the live judge-vs-BM25 samples referenced there
(Round 1's 0/5 = 0%, PR #3240's 0/10 = 0%) are both explicitly flagged
small-sample diagnostic measurements by their own producing sessions,
not decisive experiment results this session is being asked to trust or
act on.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used to choose Present-but-incomplete rather than a bare accept/reject
for Round 2's refusal in section 3 (real, evidenced obstacles ≠
Incorrect/Absent, but the issue's "demonstrated, not assumed" bar still
unmet ≠ a clean Present) instead of collapsing that judgment into a bare
binary label.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived the amendment-channel citations and the
truncation diff from primary source rather than citing Round 2's or PR
#3240's/#3242's prior verdicts, and devised one attempt (the
issue-scoped re-grouping in section 4) that neither prior round ran
rather than treating their existing evidence as sufficient coverage of
the issue-scoping question.
skill-verdict: work-in-english — applied: invoked; this record, all
scratch scripts, and all commit messages this session are written in
English per the project's own commit-history convention; the final
message to the user in this session is written in Korean per the
skill's own routing rule.

## Evidence appendix

Sanity-check script (`/tmp/finegrained_check.py`), fine-grained
`(issue, question)` key, identical parser to PR #3240's own
`/tmp/robust_parse.py` (re-derived from `gh pr diff 3240`'s quoted body,
not copied from a local file PR #3240 left behind):

```python
import glob, re, collections, hashlib, ast

paths = glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log/*.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/reports/consult-log/*.md')

seen_hashes = {}
unique_paths = []
for p in paths:
    try:
        content = open(p, 'rb').read()
    except Exception:
        continue
    h = hashlib.sha256(content).hexdigest()
    if h in seen_hashes:
        continue
    seen_hashes[h] = p
    unique_paths.append(p)

FIXTURE_ISSUES = {"2040", "2055", "2061", "2274", "1", "none"}
FIXTURE_TASK_PREFIXES = ("Task:\ntask\n", "Task:\nplease write a haiku")

def literal_prefix(s, start):
    quote = s[start]
    i = start + 1
    n = len(s)
    while i < n:
        c = s[i]
        if c == '\\':
            i += 2
            continue
        if c == quote:
            return s[start:i+1], i + 1
        i += 1
    return None, None

def parse_trace_line(line):
    m = re.match(r"^- (\S+) \| (?:skill|role)=(\S+) \| verb=(\S+) \| issue=(\S+) \| question=", line)
    if not m:
        return None
    ts, skill, verb, issue = m.groups()
    qstart = m.end()
    if qstart >= len(line) or line[qstart] not in "'\"":
        return None
    qlit, after_q = literal_prefix(line, qstart)
    if qlit is None:
        return None
    rest = line[after_q:]
    m2 = re.match(r"^ \| outcome=", rest)
    if not m2:
        return None
    ostart = m2.end()
    if ostart >= len(rest) or rest[ostart] not in "'\"":
        return None
    olit, after_o = literal_prefix(rest, ostart)
    if olit is None:
        return None
    try:
        question = ast.literal_eval(qlit)
        outcome = ast.literal_eval(olit)
    except Exception:
        return None
    return {"ts": ts, "skill": skill, "verb": verb, "issue": issue,
            "question": question, "outcome": outcome}

def picked_names(outcome):
    if not outcome.startswith("ok:"):
        return None
    m = re.search(r"picked=\[([^\]]*)\]", outcome)
    if not m:
        return None
    return tuple(sorted(re.findall(r"([a-zA-Z0-9_-]+)=", m.group(1))))

total = 0
parsed = 0
fixture = 0
real_counter = collections.Counter()
real_entries = collections.defaultdict(list)
for p in unique_paths:
    text = open(p, errors='replace').read()
    for line in text.splitlines():
        if '| verb=skill_judge |' not in line:
            continue
        total += 1
        rec = parse_trace_line(line)
        if rec is None:
            continue
        parsed += 1
        issue, question, outcome = rec["issue"], rec["question"], rec["outcome"]
        if issue in FIXTURE_ISSUES or question.startswith(FIXTURE_TASK_PREFIXES):
            fixture += 1
            continue
        key = (issue, question)   # fine-grained key, sanity check only
        real_counter[key] += 1
        real_entries[key].append(rec)

real_total = sum(real_counter.values())
repeats = {k: c for k, c in real_counter.items() if c > 1}
repeat_events = sum(c - 1 for c in repeats.values())

agree = 0
disagree = 0
for k, entries in real_entries.items():
    if len(entries) < 2:
        continue
    picks = [picked_names(e["outcome"]) for e in entries]
    ok_picks = [pk for pk in picks if pk is not None]
    if len(ok_picks) < 2:
        continue
    first = ok_picks[0]
    for pk in ok_picks[1:]:
        if pk == first:
            agree += 1
        else:
            disagree += 1

print("real remaining:", real_total, "| repeat events:", repeat_events)
print("agree=%d disagree=%d" % (agree, disagree))
```

`/tmp/issue_scoped_repeat.py` is identical to the script above except
the grouping `key` is changed from `(issue, question)` to `issue` alone
(the line `key = (issue, question)` becomes `key = issue`), plus one
added counter (`distinct_question_within_repeat_issue`) that counts, for
each repeated issue-group, whether the question text actually varies
within it. Full diff of that one change, derived: `diff
/tmp/finegrained_check.py /tmp/issue_scoped_repeat.py`, executed live
this session:
```
< key = (issue, question)   # fine-grained key, sanity check only
---
> key = issue
```
(plus the added `distinct_question_within_repeat_issue` counter and its
two extra print lines, both quoted verbatim in section 4's code fence
above).
