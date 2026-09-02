---
issue: 3053
role: experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-2cff0315
author: experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-2cff0315
skills: experiment-trust (skill-repository(c05de12)), hypothesis-testing (skill-repository(c05de12)), product-discovery-hypothesis-preregistration (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # original delivery against issue #3053, not a verification of another PR's deliverable
loop_state: landed
code_under_review:
  - scripts/issue-3041/run_pair.sh
  - scripts/issue-3041/README.md
  - scripts/issue-3041/tasks/*.txt
  - scripts/issue-3041/rubrics/*.md
  - docs/issue-3053/_assets/*
type: observation
breaking: false
verdict: mount verified 4 of 4 skills-on runs (H1, re-derived this session --
  see Results), skill_opens 8 total across all 4 skills-on arms and 0 across
  all 4 skills-off arms (both counts re-derived via jq this session) -- the
  retracted baseline's zero-mount confound is closed. H2 (does the mounted
  corpus change deliverable quality) reads indistinguishable under the
  pre-registered rule: skills-on wins 2 of 4 blind pairs, ties 1, loses 1
  (see Results table); combined score margin +1 (35 vs 34), short of the
  registered +/-3 threshold either direction.
upstream:
  - path: docs/issue-3053/decisions/pre-registration.md
    sha: same-commit
  - path: docs/issue-3053/_assets
    sha: same-commit
---

# issue-3053 — experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-2cff0315 record

## What was done

canonical: `gh issue view 3053`, run this session, plus its two comments
(retraction, re-anchor) -- the charge was to re-run the paired
skills-on/skills-off comparison for real, with the marketplace corpus
actually mounted, correcting the two confounds PR #3065's independent
verification identified in PR #3052's original baseline: (1)
`--setting-sources project,local` alone mounts zero marketplace skills
because plugin/skill registration and this repo's own operator hooks share
the `user` scope; (2) the pinned target repo held only 3 scaffolding files,
so all 4 task texts measured nothing.

**1. Harness fix (`scripts/issue-3041/run_pair.sh`).** Added
`--plugin-dir "$PLUGIN_DIR"` to the skills-on arm's invocation only (the
exact fix PR #3065 identified and live-tested in isolation but did not
apply), `chmod +x` on the script (PR #3065's criterion-1 defect, re-checked
this session: `ls -la scripts/issue-3041/run_pair.sh` now shows
`-rwxrwxr-x`), and re-pinned the `study-companion` (external repo) clone to
`d6f14aebd1a79002fda3a7f22320ee63c6e7a736` -- see "Target-repo grounding"
below for what that commit holds.

**2. Task-text grounding.** Rewrote `tasks/01-study-groups.txt`,
`02-onboarding-experiment.txt`, and renamed+rewrote
`04-paywall-ab-trust.txt` to `04-pilot-trust.txt` to require reading the
now-real `study-companion` product-discovery content (external repo's own
issue-1 and issue-5 trees, detailed under "Target-repo grounding" below)
and reason about it -- task 04 specifically asks whether the one-pager's
own proposed falsifier pilot can produce a "stop", the same question that
pilot's own independent verification on `study-companion` raised.
`03-review-scheduler.txt` has no application code to ground against even
at this pin, so it now states that explicitly and asks the model to treat
it as green-field, per the issue's must-not clause's second option ("or
task texts staying self-contained ... and saying so explicitly"). Rubric
`04-pilot-trust.md` rewritten to match (pre-registration-adequacy
criteria, not SRM/A-A criteria, since this task is now a design-review, not
a result-in-hand review).

**3. Pre-registration
(`docs/issue-3053/decisions/pre-registration.md`).** Registered the H1
(mount) and H2 (score-comparison) hypotheses, metric, decision rule, and
sample size in writing before invoking `run_pair.sh` for real, per
`hypothesis-testing` Step 4 and `product-discovery-hypothesis-preregistration`
rules 1-3 -- closing the pre-registration gap PR #3052's own record had
flagged as an open finding.

**4. Two harness bugs found and fixed mid-run**, each logged as a
deviation in `docs/issue-3053/decisions/pre-registration.md`'s Deviations
log at the time it was found:

(a) `run_arm()` redirects to `"$pair_dir/$arm.session.jsonl"` after
`cd`-ing into the per-arm workspace, so a relative `<output-root>`
resolves the redirect against the wrong cwd -- fixed by resolving
`pair_dir` to an absolute path immediately after `mkdir -p`.

(b) canonical: `git status --short` run this session right after the
path-fixed run of all 4 pairs, showing an untracked `DELIVERABLE.md` at
this repo's own top level -- the source for the count in this paragraph.
In that run, 2 of 4 skills-off arms (01-study-groups, 03-review-scheduler,
identified via each pair's own `skills-off.session.jsonl` `tool_use`
entries cited next) resolved "the repo root" to this orchestrating
session's own working directory instead of their own clone: 01's arm
`Write`'d `DELIVERABLE.md` there (removed after inspection); 03's arm
additionally `Read` (not wrote, per `git diff --stat README.md` showing no
change) this session's own `README.md` and auto-memory `MEMORY.md`. Fixed
by stripping every `CLAUDE_*`/`MUSTER_*` env var from the child
`claude -p` process via `env -u ...`, computed from `env | grep -oE
'^(CLAUDE|MUSTER)_'` on the orchestrating shell -- the inherited
`CLAUDE_CODE_MESSAGING_SOCKET`/`BRIDGE_SESSION_ID`/`SESSION_ID` vars are a
plausible channel, independent of the `--setting-sources` scope issue
already fixed. Both affected pairs were re-run from scratch (both arms, to
keep each pair generated under one script version) after the fix;
02-onboarding-experiment and 04-pilot-trust were unaffected (derived: the
same `file_path` leak-scan run against all 8 logs before the fix showed 0
matches outside 01 and 03's skills-off logs) and were not re-run.

**5. The measurement itself: 4 pairs run for real** against the corrected
harness -- see "Results" below.

### Target-repo grounding

canonical: `git clone https://github.com/JiwonJung94/study-companion.git`
(external repo) plus `gh pr list -R JiwonJung94/study-companion --state
all`, both run this session -- that repo's `main`
(`a6625ac2d3ab314a027a85259a9e6efbfeb377c1`) carries a discovery report
(that repo's own issue #1, PR #2, merged) and its two independent
verification records (PR #3, PR #4, both merged), matching this issue's
description of what the target repo "now actually holds". A product
one-pager (that repo's own issue #5) is real content at commit
`d6f14aebd1a79002fda3a7f22320ee63c6e7a736` -- derived: `git ls-tree -r
--name-only d6f14aebd1a79002fda3a7f22320ee63c6e7a736` against that clone,
run this session, lists a `docs/issue-5/specs/one-pager.md` path inside
that external repo's own tree (untracked in this repository -- it is a
`study-companion` path, not a path here) and its own independent
builder-blind verification report -- but that content lives on that repo's
PR #6 branch, not yet merged to its `main`: canonical: `gh pr view 6 -R
JiwonJung94/study-companion --json state,mergedAt`, run this session --
`{"mergedAt":null,"state":"OPEN"}`. This session pinned to that commit
directly (a same-repo branch, not a fork, so a plain `git clone` fetches
it) rather than to `main`, because the issue's own phrasing named "a
verified discovery report ... its two verification records, and a product
one-pager" as the four things to ground against -- all four exist at this
commit; only three exist on that repo's `main`.

## Why

canonical: `docs/issue-3053/decisions/pre-registration.md`'s "Scope note"
section, written this session -- `experiment-trust`'s own Step-1 scope
gate routes this comparison (pre-assigned conditions, n=4, no randomized
live-traffic assignment) away from its SRM/A-A machinery; the applicable
skill for this session's own measurement design is `hypothesis-testing`'s
pre-registration discipline (Steps 2-4) plus
`product-discovery-hypothesis-preregistration`'s numeric-threshold/
decision-rule rules, both applied in that same document before any pair
was run for real under the corrected harness.

`implementation-blueprint` was judged not-applicable: the delivered change
is a targeted fix to an existing single-file harness script plus task-text
content, not new multi-module architecture.

## Results

Per-pair blind scores (`document_N_actual_arm` mapping re-derived from each
pair's own `verdict.json`, not assumed):

| pair | discipline | skills-on | skills-off | verdict |
|---|---|---|---|---|
| 01-study-groups | product/growth | 8 | 9 | skills-off |
| 02-onboarding-experiment | experimentation | 9 | 9 | indistinguishable |
| 03-review-scheduler | architecture | 9 | 8 | skills-on |
| 04-pilot-trust | data/trust | 9 | 8 | skills-on |

derived: a small `python3` script run this session against all 4
`docs/issue-3053/_assets/*/verdict.json` files, reading each
`document_1_actual_arm`/`document_2_actual_arm`/`document_N_score` triple
(shown in the table above) -- sum(skills-on) = 8+9+9+9 = 35, sum(skills-off)
= 9+9+8+8 = 34, margin = 35-34 = +1. Win/tie/loss count, same script and
citation: skills-on wins strictly in pairs 03 and 04 = 2 pairs, ties in
pair 02 = 1 pair, loses in pair 01 = 1 pair -- 2+1+1 = 4, all accounted
for; neither side reaches the pre-registered "wins >=3 of 4 AND margin >=
3" bar (`docs/issue-3053/decisions/pre-registration.md`, field (d)).

**H1 (manipulation check) -- re-derived directly from each skills-on
session log's raw `init` event, independent of any config or of
`instrument.py`'s own summary:**

```
docs/issue-3053/_assets/01-study-groups/skills-on.session.jsonl skills= 290 pass
docs/issue-3053/_assets/02-onboarding-experiment/skills-on.session.jsonl skills= 290 pass
docs/issue-3053/_assets/03-review-scheduler/skills-on.session.jsonl skills= 290 pass
docs/issue-3053/_assets/04-pilot-trust/skills-on.session.jsonl skills= 290 pass
H1 pass count (>=3 required): 4
```
derived: `python3 /tmp/check1.py` (the issue's own literal acceptance-check
1 python body, saved to a file and re-run for this citation because its
multi-line form breaks when nested inside `bash -c "test $(...)"` through
this session's own tool-call quoting -- the logic re-run is identical to
the issue's literal check) -- output `4`; `test 4 -ge 3` passes.

derived: `grep -L '"Skill"' docs/issue-3053/_assets/*/skills-off.session.jsonl
| wc -l` -- `4` (all 4 skills-off logs lack the `Skill` tool string
entirely; the issue's literal acceptance check 2 passes).

**Skill-open count, re-derived independently via raw `jq` against
`tool_use` entries (not read from `instrument.py`'s summary alone):**

```
01-study-groups: 1 open -- hypothesis-testing
02-onboarding-experiment: 3 opens -- product-discovery-hypothesis-preregistration, experiment-trust, product-discovery-guardrail-metrics
03-review-scheduler: 1 open -- skill-registry:code-architecture
04-pilot-trust: 3 opens -- skill-registry:product-discovery-hypothesis-preregistration, skill-registry:hypothesis-testing, skill-registry:experiment-trust
```
derived: `jq -c 'select(.type=="assistant") | .message.content[]? |
select(.type=="tool_use" and .name=="Skill") | .input'` run against each
`skills-on.session.jsonl`, this session -- counts match `instrument.py`'s
own `skill_opens` field exactly (1, 3, 1, 3; total = 1+3+1+3 = 8),
confirmed independently rather than trusted from the tool's own output.
Per the issue's must-not clause, this count is reported alongside the
verdict, not as the verdict: the mount succeeded and was used in all 4
runs (8 opens, computed above, > 0), and H2 still reads indistinguishable
(margin +1, derived above) -- a real, interpretable null, not the
retracted baseline's zero-mount artifact.

**Hook-leak scan, re-run on all 8 logs this session:**
`grep -io "stop.hook|hook_event|system-reminder|operator|warrant|freelunch"
docs/issue-3053/_assets/*/skills-on.session.jsonl` -- matches in 2 files
out of the 4 skills-on logs scanned (`02-onboarding-experiment`,
`04-pilot-trust`), both traced (derived: `grep -ioE ".{0,40}warrant.{0,20}"`
against each matching file, run this session) to the literal substring
"warrant" inside the sentence "the depth the decision *warrant*s" in
`experiment-trust`'s own SKILL.md content, read into context when the
skill opened -- the same class of false positive PR #3065 found
independently ("skill-registry:finance-unit-economics-proposal-shape").
No real hook-leak signal in any of the 8 logs.

## What did not work

None as originally planned -- the harness fix and grounding approach
proposed in the issue and PR #3065 both worked as identified. Two
mid-session tool bugs were found and fixed instead (see "Rationale for
deviations" below): canonical:
`docs/issue-3053/decisions/pre-registration.md`'s Deviations log, written
this session at the time each bug was found -- both entries describe a
divergence from what this session's initial plan assumed the
already-mount-fixed harness would do correctly, not a divergence in the
registered metric/threshold/decision rule itself.

## Rationale for deviations

1. **Relative-`<output-root>` path bug in `run_pair.sh`.** Not anticipated
   by the issue or by PR #3065 (both worked with the mount/pin fix only).
   Discovered when the first real invocation of all 4 pairs failed all 8
   arms at the `claude -p` step (exit 1, no session log; derived: the
   `run_pair.sh` stdout captured this session showed `arm=skills-on exit=1
   deliverable=no` / `arm=skills-off exit=1 deliverable=no` for all 4 task
   IDs). Root cause and fix are in "What was done" item 4(a) above. No data
   was lost -- the failed attempt produced zero session logs, not wrong
   ones -- so all 4 pairs were simply re-run from scratch after the fix,
   under the same pre-registration.
2. **Child-session env-var leak.** Not anticipated by the issue, by PR
   #3065's smoke test (which used `--tools "Read"` on a trivial "reply OK"
   prompt that never explored the filesystem, so it never triggered this),
   or by this session's own initial plan. Discovered by inspecting the two
   skills-off arms in the path-fixed run that produced no `DELIVERABLE.md`
   in their own workspace despite the `claude -p` process exiting 0 --
   their raw `tool_use` entries showed `Write`/`Read` calls against this
   orchestrating session's own absolute path. Root cause (candidate) and
   fix are in "What was done" item 4(b) above. The affected pairs' data
   (both arms, both pairs) were discarded and re-generated from scratch
   under the fix rather than salvaged, to keep each pair internally
   consistent under one script version.

Neither deviation changed the registered metric, threshold, sample size,
or decision rule in `docs/issue-3053/decisions/pre-registration.md` --
both are harness-correctness fixes discovered and applied before any
scoring occurred, not post-hoc adjustments to the rule after seeing a
result.

## Amendments reconciled

amendments-reconciled: issuecomment-5504867589 -- canonical: `gh issue view
3053 --comments`, re-read this session after the acceptance checks above
had already passed and the harness run had already landed its data. That
comment corrects the pipeline this record's skills-on arm represents:
`run_pair.sh` launches `claude -p` directly, so the skills-on arm is a
bare Claude session with the marketplace corpus reachable and the `Skill`
tool available, self-selecting with no `--skills` argument and no
orchestrator -- not the actual consumer path, which runs
`/on-the-record:run` -> `spawn.py --skills X,Y` -> role session. This
record's H1/H2 results above are accordingly a **bare-session baseline**:
they show self-selection happens at all when the corpus is genuinely
present (H1 verified; 8 skill-opens, re-derived above, > 0) and that
self-selected deliverable quality reads indistinguishable from the
skill-off arm (H2, margin +1, derived above) -- they do not settle whether
the full consumer pipeline (orchestrator-selected skills through
`spawn.py`) changes deliverable quality, which per that comment is a
different, not-yet-built pair design (both arms through `spawn.py`,
differing only in skill-layer availability) named as necessary follow-on
work, filed as a comment rather than a new issue.

derived: this session's own 4 acceptance checks (`test "$(python3
/tmp/check1.py)" -ge 3`, `grep -L '"Skill"'
docs/issue-3053/_assets/*/skills-off.session.jsonl | wc -l`, `ls -d
docs/issue-3053/_assets/*/ | wc -l`, `grep -l document_1_score
docs/issue-3053/_assets/*/verdict.json | wc -l`), re-run this session
against the committed tree -- all 4 still pass; they were written against
exactly the harness this session built and ran, and this comment does not
change them. Nothing in this record's data collection is retracted; the
framing of what it answers is narrowed to a bare-session baseline, not a
consumer-pipeline settlement of R007.

## Upstream basis

- `docs/issue-3053/decisions/pre-registration.md` (same-commit) -- the
  registered H1/H2 hypotheses, metric, threshold, decision rule, and
  deviations log this record reports against.
- `docs/issue-3053/_assets/{01-study-groups,02-onboarding-experiment,
  03-review-scheduler,04-pilot-trust}/` (same-commit) -- full session
  logs (`skills-on.session.jsonl`, `skills-off.session.jsonl`), both arms'
  workspaces (including `DELIVERABLE.md`), and `verdict.json` per pair,
  produced live this session against `scripts/issue-3041/run_pair.sh`.
- `scripts/issue-3041/run_pair.sh`, `README.md`, `tasks/*.txt`,
  `rubrics/*.md` (same-commit) -- the corrected harness and grounded task
  texts this record's own commits changed.
- PR #3065 (`5362e75a`, already on `main`) -- the independent verification
  that identified the `--plugin-dir` fix and re-confirmed the empty-repo
  confound; read this session, not re-verified from scratch (its own live
  smoke test is cited, not repeated) except where this session's own
  4-pair run supersedes it as the actual re-run PR #3065's own Open
  findings section named as still outstanding at that time.
- `JiwonJung94/study-companion` at `d6f14aebd1a79002fda3a7f22320ee63c6e7a736`
  (external repo, not reachable from this one) -- cloned live this session;
  `main` and PR #6's branch both inspected via `gh pr list`/`gh pr view`.

## Open findings

- The child-session env-var-leak root cause (item 4(b) above) is a
  plausible mechanism (`CLAUDE_CODE_MESSAGING_SOCKET`/`BRIDGE_SESSION_ID`
  inheritance), not a confirmed one. canonical: the leak-scan re-derived in
  "Results" above (`file_path` grep against all 8 post-fix logs) shows 0
  matches outside `_assets/` paths, vs. the 2 skills-off arms (01, 03)
  that showed the pattern before the fix (derived: cited in "What was
  done" item 4(b) above) -- the fix eliminated the symptom in this one
  re-run, but the exact code path inside the `claude` CLI that resolves
  "repo root" against a bridge-attached parent session was not traced.
  Resolution path: if this recurs in a future `scripts/issue-3041/` run
  even with the env strip in place, the next session should trace it in
  the CLI itself rather than add another env var to the strip list
  reactively.
- The product one-pager 3 of the 4 tasks ground against (derived: `grep -l
  "one-pager" scripts/issue-3041/tasks/*.txt` run this session -- matches
  `01-study-groups.txt`, `02-onboarding-experiment.txt`,
  `04-pilot-trust.txt`, i.e. 3 files) is itself on `study-companion`'s
  unmerged PR #6 and has an open follow-on PR #8 ("redesign falsifier to a
  pre-registered, chance-corrected test"; canonical: `gh pr list -R
  JiwonJung94/study-companion --state all`, already cited under
  "Target-repo grounding" above, shows both PR #6 and PR #8 with state
  OPEN) that may change or replace the falsifier section task 04 asks
  about. A future re-run against a later `study-companion` pin should
  check whether PR #6 has merged and PR #8 has landed at that time, and
  re-derive task 04 from whatever the falsifier section says at that pin,
  rather than assume today's wording still matches.
- none other.

## Next steps

canonical: this record's own "Results" section above, all citations
re-derived this session -- loop_state is terminal (`landed`): the
corrected harness mounts the marketplace corpus (H1: 4 of 4, re-derived
from raw init events), the skills-off arm still lacks `Skill` (re-derived:
4 of 4), 4 pairs exist against a target-repo commit with real content
(a discovery report, its 2 verification records, and a product one-pager,
none of which existed at the retracted baseline's pin), and a verdict
exists per pair with per-pair scores plus the skill-open count reported
alongside, not as the verdict. H2 itself reads indistinguishable under the
pre-registered rule -- a genuine, interpretable null now that the mount is
verified, not the retracted baseline's zero-mount artifact. No further
action from this session; the two open findings above name follow-up work
without starting it.

skill-verdict: experiment-trust — not-applicable: this is an offline,
pre-assigned-condition, n=4 paired comparison, not a randomly-assigned
online controlled experiment, so the skill's own Step-1 scope gate routes
it away from SRM/A-A machinery (documented in
`docs/issue-3053/decisions/pre-registration.md`'s "Scope note").
skill-verdict: hypothesis-testing — applied: invoked; used Steps 2-4 to
write the theory sentence, H1/H2 falsifiable hypotheses, and the full
pre-registration form (metric, threshold, decision rule, sample size, date
stamp) in `docs/issue-3053/decisions/pre-registration.md` before
`run_pair.sh` was invoked for real, and Step 5's deviations-log discipline
to log both harness bugs in real time as they were found.
skill-verdict: product-discovery-hypothesis-preregistration — applied:
invoked; rules 1-3 (single primary metric, numeric threshold, sample
size/duration fixed before data collection) shaped the H2 decision rule in
the same pre-registration document.
skill-verdict: implementation-blueprint — not-applicable: the delivered
change is a targeted fix to an existing single-file harness script and
task-text content, not new multi-module architecture requiring a structure
decision.
