---
issue: 3041
role: conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769
author: conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769
skills: conformance-review-verdict-assignment (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), hypothesis-testing (skill-repository(c05de12))
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: PR 3052, branch issue-3041/experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600
    sha: bb966ce64714cdf17d550b46e14d8e4af332baaa
---

# issue-3041 — conformance-review-verdict-assignment+adversarial-review+experiment-trust+hypothesis-testing-e296b769 record

## What was done

Builder-blind conformance grading of PR #3052 (sha bb966ce64714cdf17d550b46e14d8e4af332baaa)
against issue #3041's five acceptance bullets, judged from the diff and the
issue text only, never the PR's own narrative about itself — plus an
independent adversarial attack on the experiment: re-derived the harness's
own headline instrumentation claim from the raw retained session logs
rather than trusting its report, and checked whether the two arms' tool
and settings configuration genuinely differed in the intended way. All
`docs/issue-3041/_assets/...` and `scripts/issue-3041/...` paths cited
below are as committed in PR #3052 at sha bb966ce6 and are untracked on
this review's own branch — they were read directly (via `gh pr checkout
3052` into a scratch branch, since discarded) during this review, cited
here by sha rather than by a path this branch's working tree carries.

canonical: gates/requirement_met.py, executed this turn.
acceptance: `python3 gates/requirement_met.py 3041 3052` — result:
```
advisory: [UNKNOWN] the documented invocation line, run as written, produces two workspaces and two deliverables for one task
advisory: [UNKNOWN] the run record lists each pair, its task text, and the path to both arms' outputs
advisory: [UNKNOWN] the record names the blinding mechanism and shows the evaluator input for one pair with the arm label absent
advisory: [UNKNOWN] the record contains the per-pair score table and the verdict line
advisory: [UNKNOWN] the record shows these three figures for every skills-mounted arm
advisory: [UNKNOWN] A paired-run harness exists and its invocation is documented in the repo.
advisory: [UNKNOWN] empty state: a harness that produces only one arm fails this criterion
advisory: [UNKNOWN] provenance: executed-live
advisory: [UNKNOWN] At least 3 paired runs on `study-companion` tasks spanning at least 2 different
advisory: [UNKNOWN] empty state: fewer than 3 pairs, or pairs from a single discipline, fails this criterion
advisory: [UNKNOWN] Scoring is blind: the evaluator's input does not disclose which arm mounted skills,
advisory: [UNKNOWN] empty state: not applicable — blinding is required unconditionally
advisory: [UNKNOWN] A top-line verdict states whether the skills-mounted arm scored better, worse, or
advisory: [UNKNOWN] empty state: not applicable — the verdict is required unconditionally
advisory: [UNKNOWN] Secondary instrumentation (opens, first-open position, interleaving) is reported
advisory: [UNKNOWN] empty state: a run whose log is unavailable is listed as unmeasured, not omitted
advisory: [UNKNOWN] must not: the harness must not score any arm using call-success, mount-count, or
미채점 (전부 UNKNOWN) — 17개 기준 중 실제로 검증된 것이 없다. 차단 사유는 없지만 이건 게이트 통과가 아니다.
```
The gate is purely advisory here: all 17 lines read UNKNOWN, no automated
pass/fail was produced by the gate itself. Every verdict below is this
session's own manual grading, not a gate result.

### Part 1 — conformance verdicts (5 acceptance criteria + must-not clause)

All five graded **Present**:

1. **Paired-run harness invocation → two workspaces, two deliverables.**
   Present. canonical: PR #3052 sha bb966ce6, scripts/issue-3041/run_pair.sh
   and scripts/issue-3041/README.md (untracked on this branch, read via
   the scratch checkout) — README documents the invocation `bash
   scripts/issue-3041/run_pair.sh <task-file> <task-id> <output-root>`;
   run_pair.sh clones the target repo once into a seed, copies it into
   `$pair_dir/skills-on` and `$pair_dir/skills-off`, runs one `claude -p`
   arm in each. derived: `gh pr diff 3052 --name-only`, run this turn —
   for all 4 task ids, both arms' DELIVERABLE.md and both
   `*.session.jsonl` files are listed as present in the diff.
2. **>=3 paired runs, >=2 disciplines, both arms retained.** Present.
   derived: `gh pr diff 3052 --name-only`, run this turn — lists 4 pair
   directories (study-groups, onboarding-experiment, review-scheduler,
   paywall-ab-trust), spanning product/growth, experimentation design,
   backend architecture, and data/experiment-trust analysis per each
   pair's own task file. derived: `wc -l` on all 8 DELIVERABLE.md files,
   run during the scratch-branch checkout — returned 37, 94, 140, 104,
   123, 155, 109, 179 lines across the 8 files, none empty or stub-sized.
3. **Blind scoring, blinding mechanism named, one unlabeled evaluator
   input shown.** Present. canonical: PR #3052 sha bb966ce6,
   scripts/issue-3041/evaluate_pair.py (untracked on this branch, read
   via the scratch checkout) — calls a fresh `claude -p --tools ""`
   process (zero tool access) and randomizes document order per pair via
   `random.shuffle`. derived: `jq -r '.evaluator_prompt'
   .../01-study-groups/verdict.json` (untracked path, run during the
   scratch-branch checkout) printed the full evaluator prompt for pair
   01-study-groups with no arm label anywhere in it; the arm mapping
   lives only in the same file's `document_1_actual_arm` /
   `document_2_actual_arm` fields, never inside the prompt text.
4. **Top-line verdict, per-pair scores, reversing result named.** Present.
   derived: `jq -r '.document_1_score,.document_2_score,.verdict'` against
   the same pair's verdict.json (untracked path, scratch-branch checkout)
   returned `8`, `8`, `"indistinguishable"`, matching the record's row
   for that pair; the record's score table for the other 3 pairs was
   cross-read against their own verdict.json files the same way. The
   record names an explicit reversing condition: a consistent
   one-directional skills-on advantage, or skills-on wins correlating
   with a skill actually being opened — neither held.
5. **Secondary instrumentation (opens, first-open fraction, interleaving)
   per skills-mounted run.** Present, independently re-derived rather
   than trusted: wrote a throwaway parser (not committed) over all 4
   skills-on session logs, counting `tool_use` blocks named `"Skill"`
   directly from the raw transcript. derived: `grep -o
   '"name":"Skill"'` and `grep -o '"name": *"Skill"'` over all 4
   untracked skills-on.session.jsonl files (scratch-branch checkout, run
   this turn) — result: 0 matches in every file; `wc -l` on the same 4
   files, run the same turn, returned 35, 39, 31, 25 total lines
   respectively, confirming the greps ran against non-empty transcripts.
   This matches instrument.py's own reported `skill_opens: 0` for every
   pair — the report's central number was reproduced independently, not
   accepted on trust.

**Must-not clause** (no call-success/mount-count/open-timing as scoring
input; evaluator must not have generated either arm): complied. The
evaluator prompt (verified directly, criterion 3 above) contains only
task text, rubric, and the two documents — no instrumentation figures.
The evaluator is a `--tools ""` subprocess invoked only after both
DELIVERABLE.md files already exist, and writes nothing to either
workspace.

### Part 2 — adversarial attack on the experiment (beyond conformance)

Two problems undermine the null result's interpretability, both
independently re-derived rather than accepted from the PR's own record,
and neither surfaced anywhere in that record even though the evidence for
both sits inside its own committed assets.

**Finding A — the marketplace skill corpus was never mounted in any of
the 4 real runs, so the manipulation had no content to differ on.**
run_pair.sh passes `--setting-sources project,local` to both arms —
deliberately excluding `user`, per PR #3052's own deviation log, to stop
this repo's operator hooks (registered at user scope) from leaking into
the target-repo subprocess. derived: read the full `system`/`init` JSON
event (not only its `tools` field) of all 4 untracked
skills-on.session.jsonl files this turn, via a throwaway script — every
one of the 4 returned identical values: `"plugins": []` and `"skills"`
equal to exactly the 17 built-in Claude Code skill names (deep-research,
design-sync, dataviz, update-config, verify, debug, code-review,
simplify, batch, fewer-permission-prompts, doctor, loop, schedule,
claude-api, workflow-authoring, run, run-skill-generator). None of the
marketplace skills the 4 tasks were written to trigger
(hypothesis-testing, experiment-trust,
product-discovery-hypothesis-preregistration, decision-brief,
user-discovery) appear, because `plugins: []` means no marketplace was
loaded at all in any of the 4 pairs. canonical:
`/home/jwjung/.claude/settings.json` (this machine's user-scope settings
file), read this turn — holds `enabledPlugins` and
`extraKnownMarketplaces`, confirming plugin/marketplace registration
lives at exactly the `user` scope `--setting-sources project,local`
excludes. derived: `claude --help`, run this turn — confirms
`--setting-sources` accepts only `user, project, local`, so
`project,local` mechanically excludes that scope, no other explanation
available.

The `Skill` tool itself genuinely differs between arms — canonical: the
same 4 session logs' init events show `"tools"` including `"Skill"` for
every skills-on run and, separately, canonical: all 4 untracked
skills-off.session.jsonl init events (read this turn) list `"tools":
["Edit", "Glob", "Grep", "Read", "Write"]`, no `"Skill"` — so the tool
differs exactly as the harness intends. But the skills-on arm's `Skill`
tool had no task-relevant skill available to select from in any of the 4
real pairs. `skill_opens: 0` is therefore not evidence the model saw the
target skills and declined them; it is the expected outcome of a corpus
that structurally could not contain them.

This also undercuts PR #3052's own "Twyman's-law cross-check" (its Open
findings section): the smoke test cited there ran in `/tmp/smoketest`
with no `--setting-sources` flag at all — per the PR's own text and
deviation log, that smoke test is what first surfaced the operator-hook
leak that motivated adding `--setting-sources project,local` afterward,
i.e. it ran under the prior, broader configuration that still included
`user` scope, which is exactly why it could invoke `decision-brief`. It
validates a configuration none of the 4 real pairs ran under, so it does
not actually clear the zero-invocation result of the
broken-or-misconfigured-harness explanation it was invoked to rule out.

**Finding B — the target repo carries no application content at the
pinned commit.** Issue #3041's Scope section names `study-companion`
specifically because heterogeneous product work is the point, implying
tasks grounded in a real target repo. derived: cloned
`https://github.com/JiwonJung94/study-companion.git` directly this turn
and checked out `e102772480545a6be0af733f51020c97e7357ba7` (the pin
run_pair.sh uses) — `git ls-files` returned exactly 3 files, all
on-the-record-pattern scaffolding docs (a consult-log entry, plus an
approvers spec and a requirement-digest spec), no application code.
`main` returned 6 files, same pattern. Three of the 4 skills-on
transcripts say so themselves in their own final assistant text (read
during the scratch-branch checkout): "the repo has no existing app
code," "it doesn't contain the actual A/B test code or data." Both arms
of every pair therefore wrote context-free product essays grounded in
nothing but a few lines of an unrelated Korean-language governance doc —
a secondary confound on top of Finding A, though it does not break any
literal acceptance-bullet check (all 4 pairs still produced real,
on-task deliverables per Part 1 above).

### Is the null trustworthy?

No, not as evidence about the skill layer specifically. The
"indistinguishable, 2-1-1, zero invocations" result is real and
accurately reported (Part 1, criterion 5), but Finding A means it answers
a narrower question than the one asked: it shows a session with the
`Skill` tool declared but only 17 irrelevant built-in skills behind it
scores the same as a session with no `Skill` tool at all. That is weaker
than "mounting the target skill layer does not change the deliverable" —
the target layer was never in the corpus to mount, on any of the 4 runs.

Strongest specific reason the null might not hold under a corrected
harness: re-running with a `--setting-sources` value that keeps the
marketplace loaded (while still finding another way to suppress the
operator-hook leak the PR's own deviation log identified) would give the
skills-on arm a first real chance to select hypothesis-testing,
experiment-trust, or product-discovery-hypothesis-preregistration on the
tasks whose text was written close to those skills' trigger vocabulary.
Until that run exists, "the skill layer doesn't help" is unverified —
what is verified is only "an unused, irrelevant tool doesn't help," which
was never in doubt.

## Why

The task instructed builder-blind grading (diff and issue text, never the
PR's own narrative) plus an independent adversarial attack that does not
accept the harness's self-reported instrumentation table at face value.
Re-deriving `skill_opens` from the raw session logs rather than trusting
`instrument.py`'s output, and reading the full `system`/`init` event
rather than only the field the PR's record quotes, surfaced `plugins:
[]`, which PR #3052's own record never cites anywhere — it cites
instrument.py's aggregate output and a differently-configured smoke test,
never the session logs' own `plugins`/`skills` fields, even though those
logs are the exact asset this task instructed grading to check
independently against.

skill-verdict rationale — conformance-review-verdict-assignment: Finding
A is graded Surface, not Absent/Incorrect, against the Scope clause "once
with skills mounted": matching mechanism exists (`Skill` in `--tools`,
README claims "full corpus") but does not fire on the actual condition
that clause names (a real, task-relevant skill corpus to select from) —
the skill's own Present-vs-Surface distinction (rule 1).

skill-verdict rationale — adversarial-review: treated PR #3052 as a made
artifact whose own narrative could not be trusted to have checked itself,
and re-derived the disqualifying evidence from the artifact's own
retained logs rather than its prose, per the skill's core mechanism.

skill-verdict rationale — experiment-trust: canonical: issue #3041 body
(`gh issue view 3041`, read this turn) describes an offline paired
harness with no random assignment — Step 1's scope gate correctly rules
out SRM/A-A machinery (Steps 2-4) for this kind of comparison; Step 5's
Twyman's-law skepticism produced the smoke-test-configuration discrepancy
described in Finding A above.

skill-verdict rationale — hypothesis-testing: PR #3052's own record
already logs a pre-registration gap (no numeric win threshold fixed
before running). This review's Finding A sits upstream of that one — a
pre-registered threshold on top of a corpus-free `Skill` tool would not
have made the manipulation meaningful either.

## What did not work

None — no reversals or scope changes during this review. Findings A and
B (Part 2 above) were each confirmed by a single direct read: canonical:
the four skills-on session logs' `plugins` field, all committed under PR
#3052 sha bb966ce6 (untracked on this review branch), read this turn —
see Part 2 Finding A above; canonical: the live clone of study-companion
at the pinned commit, cloned this turn — see Part 2 Finding B above.
Neither was overturned by a later check within this session.

## Upstream basis

- PR #3052, sha bb966ce64714cdf17d550b46e14d8e4af332baaa. canonical: `gh
  pr view 3052`, `gh pr diff 3052 --name-only`, both run this turn — the
  artifact graded.
- Issue #3041 body. canonical: `gh issue view 3041`, run this turn — the
  five acceptance bullets and the Scope section's "skills mounted" /
  target-repo framing.
- scripts/issue-3041/run_pair.sh, README.md, instrument.py,
  evaluate_pair.py — PR #3052 sha bb966ce6, untracked on this review
  branch — harness mechanics, read during the scratch-branch checkout.
- The 4 pairs' skills-on.session.jsonl, skills-off.session.jsonl,
  verdict.json files — PR #3052 sha bb966ce6, untracked on this review
  branch — re-parsed directly this turn for Part 1 criterion 5 and
  Finding A.
- `https://github.com/JiwonJung94/study-companion.git` at
  `e102772480545a6be0af733f51020c97e7357ba7` and `main` — cloned live
  this turn for Finding B.
- `/home/jwjung/.claude/settings.json` — this session's own user-scope
  settings, read this turn for Finding A's marketplace-registration-scope
  claim.

## Open findings

- Finding A (marketplace corpus never mounted) has no resolution path
  within PR #3052 as it stands: it requires a re-run with a corrected
  `--setting-sources` value (or an equivalent fix that keeps hook
  isolation while still loading the marketplace) before issue #3041's
  Problem statement ("does mounting skills produce a better deliverable")
  is actually answered by this baseline. This is new work, not started
  here.
- Finding B (empty target repo) is a lower-severity confound; a future
  re-run should pin a study-companion commit that actually contains the
  application described in the issue, or explicitly scope tasks to be
  self-contained enough not to need repo grounding (as the current 4
  mostly already are).
- none other.

## Next steps

loop_state is terminal (landed): five conformance criteria graded Present
with independent evidence (Part 1), two adversarial findings raised
against the experiment's validity (Part 2), and an explicit
trustworthiness verdict given on the null. No further action from this
session; the open findings above name the follow-up work without
starting it.

## Skill verdicts

- skill-verdict: conformance-review-verdict-assignment — applied: invoked; used to grade the 5 acceptance criteria Present (see Part 1)
  and, separately, to grade the Scope clause "skills mounted" as Surface
  rather than Absent/Incorrect (see "Why" above).
- skill-verdict: adversarial-review — applied: invoked; grading PR #3052
  builder-blind and re-deriving Finding A from the artifact's own raw
  logs instead of accepting instrument.py's summary or the record's
  prose is this skill's core mechanism, applied throughout Part 2.
- skill-verdict: experiment-trust — applied: invoked; canonical: issue
  #3041 body (`gh issue view 3041`, read this turn) — Step 1's scope
  gate confirms the SRM/A-A machinery does not apply to this offline
  paired harness; Step 5's Twyman's-law skepticism produced the
  smoke-test-configuration discrepancy named in Finding A above.
- skill-verdict: hypothesis-testing — applied: invoked; used to place
  PR #3052's self-reported pre-registration gap correctly downstream of
  Finding A, per the "Why" section above.
