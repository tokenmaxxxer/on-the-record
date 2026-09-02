---
issue: 3041
role: experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600
author: experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600
skills: experiment-trust (skill-repository(c05de12)), hypothesis-testing (skill-repository(c05de12)), product-discovery-hypothesis-preregistration (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: scripts/issue-3041/
type: harness+baseline-run
breaking: false
verdict: indistinguishable (2 skills-on wins, 1 skills-off win, 1 tie across 4 pairs; no skill was ever opened in any skills-mounted arm, so the split is run-to-run noise around a null effect, not evidence of a skill-layer benefit)
upstream:
  - path: scripts/issue-3041/README.md
    sha: ff869f0cfb0ade25299367e32deaadcccfe41067
---

# issue-3041 — experiment-trust+hypothesis-testing+product-discovery-hypothesis-preregistration+implementation-blueprint-5ef0c600 record

## What was done

Built a paired skills-on/skills-off comparison harness (`scripts/issue-3041/`)
and ran it 4 times against `JiwonJung94/study-companion` (the consumer
target repo named in the issue), producing a baseline.

**Harness.** `scripts/issue-3041/run_pair.sh <task-file> <task-id>
<output-root>`, documented in `scripts/issue-3041/README.md`. For one task
it clones the target repo once at a pinned commit
(`e102772480545a6be0af733f51020c97e7357ba7`), copies that clone into two
isolated workspaces, and runs `claude -p` in each with the same task text,
model (`sonnet`), permission mode, and non-Skill tool set:

- `skills-on`: default full skill corpus available (`~/.claude/skills`),
  `Skill` included in `--tools`.
- `skills-off`: `--disable-slash-commands`, `Skill` excluded from `--tools`.

Both arms get `--setting-sources project,local` so this repo's own operator
hooks (which are registered at the user settings level and would otherwise
fire inside the target-repo clone too, per a smoke test that surfaced a
stray "Stop hook" injection before this flag was added) don't leak into
either arm -- confirmed identical across arms, so it isn't a differential
confound.

check (acceptance bullet 1): ran as written --
```
bash scripts/issue-3041/run_pair.sh scripts/issue-3041/tasks/01-study-groups.txt 01-study-groups <output-root>
```
produced `<output-root>/01-study-groups/{skills-on,skills-off}/DELIVERABLE.md`
and `{skills-on,skills-off}.session.jsonl` -- two workspaces, two
deliverables, for one task. acceptance: `bash scripts/issue-3041/run_pair.sh
<task-file> <task-id> <output-root>` (run 4 times, once per pair below) —
result: `arm=skills-on exit=0 deliverable=yes` and `arm=skills-off exit=0
deliverable=yes` printed for all 4 pairs.

**4 paired runs, spanning 3 disciplines** (exceeds the 3-pairs/2-disciplines
floor). Both arms' deliverables and session logs are retained under
`docs/issue-3041/_assets/<task-id>/`:

| pair | discipline | task text (file) | skills-on output | skills-off output |
|---|---|---|---|---|
| 01-study-groups | product/growth decision | `scripts/issue-3041/tasks/01-study-groups.txt` | `docs/issue-3041/_assets/01-study-groups/skills-on/DELIVERABLE.md` | `docs/issue-3041/_assets/01-study-groups/skills-off/DELIVERABLE.md` |
| 02-onboarding-experiment | product experimentation design | `scripts/issue-3041/tasks/02-onboarding-experiment.txt` | `docs/issue-3041/_assets/02-onboarding-experiment/skills-on/DELIVERABLE.md` | `docs/issue-3041/_assets/02-onboarding-experiment/skills-off/DELIVERABLE.md` |
| 03-review-scheduler | backend/software architecture | `scripts/issue-3041/tasks/03-review-scheduler.txt` | `docs/issue-3041/_assets/03-review-scheduler/skills-on/DELIVERABLE.md` | `docs/issue-3041/_assets/03-review-scheduler/skills-off/DELIVERABLE.md` |
| 04-paywall-ab-trust | data/experiment-trust analysis | `scripts/issue-3041/tasks/04-paywall-ab-trust.txt` | `docs/issue-3041/_assets/04-paywall-ab-trust/skills-on/DELIVERABLE.md` | `docs/issue-3041/_assets/04-paywall-ab-trust/skills-off/DELIVERABLE.md` |

Full task text for each pair is in the linked `tasks/*.txt` file (also
reproduced in each pair's `verdict.json` under `task_file`/embedded in
`evaluator_prompt`).

**Blinding.** `scripts/issue-3041/evaluate_pair.py` calls a fresh `claude -p`
process with `--tools ""` (zero tool access -- it cannot inspect either
workspace, git history, or any path that would disclose which arm produced
which document) and never generated either deliverable itself. Which
deliverable is labeled "Document 1" vs "Document 2" is randomized per call
(`random.shuffle`) and the true mapping is recorded only in the script's own
output JSON (`document_1_actual_arm` / `document_2_actual_arm`), never shown
to the evaluator.

check (acceptance bullet 3): evaluator input for pair `01-study-groups`,
arm label absent (full prompt in
`docs/issue-3041/_assets/01-study-groups/verdict.json` under
`evaluator_prompt`; excerpted here, derived: `jq -r .evaluator_prompt
docs/issue-3041/_assets/01-study-groups/verdict.json`):

```
You are a blind evaluator. You did not write either document below, and you are not told which system, process, or person produced them.

TASK GIVEN TO BOTH WRITERS:
We're thinking about adding a feature where students can be matched into small study groups by course and exam date. Before the team invests further, write a short brief on whether this is worth building: what would need to be true for it to succeed, how we'd know quickly if it's not working, and what would make us stop or change direction.

SCORING RUBRIC (what a strong answer should contain):
A strong answer:
- States a clear go/kill/pivot/persist call that is genuinely still open (not a decision already made elsewhere in the brief).
- Names what would have to be true for the idea to work -- a condition specific enough that it could turn out false -- not just optimistic reasons to build it.
...

--- DOCUMENT 1 ---
[full deliverable text, no arm label]
--- END DOCUMENT 1 ---

--- DOCUMENT 2 ---
[full deliverable text, no arm label]
--- END DOCUMENT 2 ---
```

The evaluator is told the task and a rubric derived from what the task's
target methodology skill claims a good answer contains (`scripts/issue-3041/rubrics/*.md`,
paraphrased from each skill's own SKILL.md, e.g. `hypothesis-testing`'s
falsifiable-condition/decision-rule/stop-condition criteria for pair 01, or
`product-discovery-hypothesis-preregistration`'s metric/threshold/guardrail
criteria for pair 02). It is never given call-success, mount-count, or
open-timing, and it never generated either arm -- satisfying the issue's
`must not` bullet.

**Per-pair score table and verdict** (derived: `jq -r
'[.document_1_actual_arm,.evaluator_verdict.document_1_score,.document_2_actual_arm,.evaluator_verdict.document_2_score,.evaluator_verdict.verdict]|@tsv'
docs/issue-3041/_assets/<task>/verdict.json`, run against all 4 files):

| pair | skills-on score | skills-off score | verdict |
|---|---|---|---|
| 01-study-groups | 8 | 8 | indistinguishable |
| 02-onboarding-experiment | 9 | 8 | skills-on better |
| 03-review-scheduler | 8 | 9 | skills-off better |
| 04-paywall-ab-trust | 9 | 8 | skills-on better |

**Top-line verdict.** Indistinguishable. Of the 4 pairs above, skills-on
wins 2 (02, 04), skills-off wins 1 (03), and 1 ties (01) -- derived from the
score table directly above. A 1-point spread each time, no consistent
direction, and (see instrumentation below) the skills-on arm never actually
opened a skill in any of the 4 runs. The score variation reads as ordinary
run-to-run noise around a null skill-layer effect, not as a mounting
benefit, because the arm with skills available never used them: skills-on's
wins cannot be attributed to skill guidance it never invoked.
**What would have reversed this verdict:** a consistent, one-directional
skills-on advantage across pairs (not a 2-1-1 split), *or* skills-on wins
correlating with runs where a skill was actually opened (a positive
opens-vs-score relationship) -- either would indicate a real skill-mounting
effect rather than noise over an unused option. Neither held in this
4-pair sample.

**Secondary instrumentation**, from each skills-on arm's own transcript
(derived: `python3 scripts/issue-3041/instrument.py
docs/issue-3041/_assets/<task>/skills-on.session.jsonl`, run against all 4
logs):

| pair | total tool calls | skill opens | first-open fraction | 2+ skills interleaved? |
|---|---|---|---|---|
| 01-study-groups | 6 | 0 | n/a (no skill opened) | n/a (fewer than 2 distinct skills opened) |
| 02-onboarding-experiment | 7 | 0 | n/a (no skill opened) | n/a (fewer than 2 distinct skills opened) |
| 03-review-scheduler | 5 | 0 | n/a (no skill opened) | n/a (fewer than 2 distinct skills opened) |
| 04-paywall-ab-trust | 5 | 0 | n/a (no skill opened) | n/a (fewer than 2 distinct skills opened) |

Every skills-mounted arm's log was available and measured (`instrument.py`
prints `"status": "measured"` for all 4 -- derived: the command above, run
against each of the 4 `skills-on.session.jsonl` files) -- none is listed as
unmeasured, and none is omitted; the "n/a" cells are the measured value
(zero opens), not a missing measurement. This reproduces, inside a
controlled single-task setting, the issue's own opening complaint about
mounted skill slots going unopened (see issue body's cited 58% figure from
its own 40-session sample). With the full corpus available and no task-fit
problem ruled out in advance, `skill_opens` reads 0 in the table above
(derived: the "Secondary instrumentation" table, all 4 rows), including
pair 04-paywall-ab-trust, whose task text ("Can we trust this result...",
canonical: `scripts/issue-3041/tasks/04-paywall-ab-trust.txt`) paraphrases
`experiment-trust`'s own listed trigger phrase ("can we trust this
experiment", canonical: `experiment-trust` SKILL.md frontmatter
`description:` field).

**Register-sensitivity handling** (per the issue's second comment). All 4
task texts are written in one held-fixed "plain stakeholder request"
register -- avoiding the target skill's own jargon (no "falsifiable",
"pre-register", "decision rule", "guardrail metric", "archetype", "SRM") and
avoiding raw engineering register. This register is byte-identical between
the two arms of a given pair (same `--prompt`), so it cannot differentially
advantage skills-on over skills-off within a pair -- it can only affect
whether the skills-on arm's selector finds a fitting skill at all, which is
exactly what `instrument.py`'s `distinct_skills`/`skill_opens` fields
surface rather than hide. Pair 04 deliberately used near-verbatim trigger
wording for `experiment-trust` and still produced zero opens (see table
above), so the null-invocation result here is not an artifact of avoiding
trigger words -- see `scripts/issue-3041/README.md`'s "Task-text register"
section for the full rationale.

## Why

The issue asks whether mounting the skill layer changes the deliverable,
not whether it changes call-success or timing metrics -- and its own
comments raise register-sensitivity as an uncontrolled variable inside any
harness that writes its own task texts. The design choices above (isolated
clones from one pinned-commit seed, tool-set as the only differentiator
between arms, a `--tools ""` blind evaluator with randomized document
order, and a single held-fixed task-text register per pair) are aimed
squarely at making the skills-on/skills-off contrast the only thing that
can move the score, while still recording -- not suppressing -- the
selection-coverage question the issue's comments raised as a live
possibility.

## Upstream basis

- `scripts/issue-3041/README.md` (this commit) -- documented invocation,
  what's held constant, blinding mechanism, scoring inputs, and the
  register-handling rationale.
- `scripts/issue-3041/run_pair.sh`, `instrument.py`, `evaluate_pair.py` --
  the harness code (this commit).
- `scripts/issue-3041/tasks/*.txt`, `rubrics/*.md` -- the 4 task texts and
  their skill-derived rubrics (this commit).
- `docs/issue-3041/_assets/<task-id>/` -- both arms' deliverables, both
  arms' full stream-json session logs, and each pair's `verdict.json`
  (evaluator prompt, randomized-order mapping, and raw verdict) for all 4
  pairs (this commit).
- GitHub issue #3041 body and its two comments (canonical: `gh issue view
  3041 --json title,body,comments`) -- scope, acceptance criteria, and the
  register-sensitivity finding this record addresses directly.

## What did not work

- The first evaluator run (pair 04) crashed with a `JSONDecodeError`: the
  original `re.search(r"\{.*\}", text, re.DOTALL)` extraction was greedy
  across the entire response and could span past the first well-formed JSON
  object if any stray brace appeared later in the text. Fixed by replacing
  it with a balanced-brace scan (`_extract_json_object` in
  `evaluate_pair.py`) that returns the first object whose braces actually
  balance and parses as JSON, and by wrapping the fallback in a
  `{"error": "unparsed", "raw": ...}` object instead of letting the
  exception propagate -- the script no longer crashes without writing
  `verdict.json`. Re-ran pair 04's evaluation after the fix; it produced a
  valid verdict (see score table above).
- A quick unscoped smoke test (`claude -p` in `/tmp/smoketest` with no
  `--setting-sources` flag) surfaced this repo's own operator hooks
  ("Stop hook" text about invoking skills/writing deviation logs) leaking
  into a subprocess run outside this repo's directory, because those hooks
  are registered at the user settings level rather than scoped to this
  project. Added `--setting-sources project,local` to every harness and
  evaluator invocation before running the real pairs, to keep that
  contamination out of the recorded runs (equally for both arms, so it
  does not differentially confound the comparison).

## Open findings

amendments-reconciled: issuecomment-5502953791 (posted 2026-09-02T01:27:17Z,
after this session started; read via `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5502953791`)

- **Structural-vs-factual scoring gap, raised by issuecomment-5502953791.**
  That comment reports a separate paired study-companion run where a
  skills-mounted discovery artifact was structurally excellent (a
  ten-row evidence table with a scored verdict) but 3 of its citation rows
  did not survive an independent primary-source check (canonical:
  issuecomment-5502953791's citation table -- row 1 "94 studies /
  correlation ~.24-.27" vs. actual "115 studies / 502 effects / 15,889
  participants, weighted mean 0.178"; row 7 "Alshahrani et al." vs. actual
  "Abdul-Wahab, Salem, Yetilmezsoy & Fadlallah -- no such author on the
  paper"). The comment's conclusion: a rubric that only checks structural
  conformance (has a verdict, are claims tagged, is there a disconfirming
  section) would have scored that artifact near the top, and this issue's
  harness needs at least one axis a well-formed-but-unfounded artifact
  fails, checkable without trusting the artifact's own self-tags.
  **Reconciliation against this run's 4 pairs:** all 4 of `rubrics/*.md`
  here are structural-content checklists (does the brief name a
  threshold, a guardrail, a module boundary, an SRM-style check) and do
  not include a fact-verification axis. This is a real gap of the same
  shape the comment names, but it did not bite in this sample for a
  specific reason: none of the 4 task texts asked for citable external
  claims (no evidence tables, no cited studies/authors) the way the
  discovery-skill scenario in the comment did -- the closest task,
  04-paywall-ab-trust, asks for internal reasoning about one described
  test, not sourced claims a fabricated citation could hide inside.
  Spot-checked both arms' `DELIVERABLE.md` files for pair 04
  (`docs/issue-3041/_assets/04-paywall-ab-trust/skills-on/DELIVERABLE.md`
  and `docs/issue-3041/_assets/04-paywall-ab-trust/skills-off/DELIVERABLE.md`)
  and confirmed neither cites an external source or study. So this run's
  rubric gap did not silently launder a fabricated claim into a high
  score here, but the harness as designed has no defense if a future task
  (or a different skill) does invite citable claims. **Follow-up needed
  before that case**: add a rubric line the blind evaluator can check
  without trusting the deliverable's own hedging -- e.g. "does every
  factual claim attributed to an external source match a source that
  actually exists and says that" -- to any task whose target skill
  produces evidence tables or cited claims. Not added retroactively to
  the 4 rubrics here because doing so after seeing the scores would
  itself be the same post-hoc-threshold problem flagged in the
  pre-registration-gap finding below.
- **Pre-registration gap, surfaced by applying `hypothesis-testing` and
  `product-discovery-hypothesis-preregistration` to this record's own
  top-line claim.** Both skills' Step 4 / rule 1 require a numeric
  threshold and mechanical decision rule fixed in writing *before* data
  collection starts. This session fixed the test design (rubrics, blind
  evaluator, holding model/repo/task-text/tool-set constant) before
  running any pair, but did not write down in advance a numeric win
  criterion such as "call skills-on the winner if it wins N of 4 pairs
  with average margin >= M points." The "indistinguishable" verdict above
  was read off the score table after seeing it, using ordinary judgment
  about what a 2-1-1 split with zero invocations means, not a
  pre-committed rule applied mechanically. Per `hypothesis-testing`'s own
  Step 4 gate, this is a procedure violation to record rather than
  absorb silently: a threshold set after seeing the numbers cannot rule
  out that the same 2-1-1 split, differently narrated, would have been
  called a "skills-on edge" instead. It does not undermine the descriptive
  facts reported (the scores, the zero-open instrumentation) which are
  observations, not the verdict layer -- but a follow-up run should
  pre-register the win rule (e.g. in `scripts/issue-3041/README.md`)
  before collecting more pairs.
- **Twyman's-law cross-check on the zero-invocation finding**, applying
  `experiment-trust`'s Step 5 skepticism to this session's own surprising
  result (0 skill opens in every one of 4 skills-mounted arms, including a
  near-verbatim-trigger-wording pair, is itself an anomalous, too-clean
  result worth doubting before reporting). Independent check performed:
  before running any of the 4 real pairs, a smoke test in `/tmp/smoketest`
  used the same mechanism (default full skill corpus, `Skill` in
  `--tools`, `claude -p`) on a differently-worded prompt and did invoke a
  skill (`decision-brief`; canonical: `/tmp/smoketest/out2.jsonl` line 9,
  `tool_use` block `{"name": "Skill", "input": {"skill":
  "decision-brief"}}`, read directly during this session before the
  smoke-test directory was discarded). That cross-check shows Skill
  invocation is mechanically functional under this harness's
  configuration, so the 4-pair zero-invocation result is not an artifact
  of a broken or misconfigured harness -- it reflects the model's actual
  selection behavior on these 4 task texts.
- **`implementation-blueprint` classify confirms the harness's own
  structure.** Running the skill's own classifier on the harness (derived:
  `python3 /home/jwjung/skill-registry/skills/implementation-blueprint/scripts/prep.py
  classify --surface backend --external no --logic transform --asynchronous no`)
  returns `ARCHETYPE: pipeline` ("structure follows stages, not layers"),
  whose FAN-OUT PREP threshold is "5 or fewer units: build solo." The
  harness has 4 stages (clone/seed, per-arm `claude -p` invocation,
  instrumentation, blind evaluation) -- under the threshold, confirming
  the solo, 3-script-plus-clone-step layout chosen above rather than a
  fan-out build.
- `skill_opens` reads 0 for every skills-mounted arm across all 4 pairs
  (derived: the "Secondary instrumentation" table above, 4 rows, all 0),
  including pair 04-paywall-ab-trust despite near-verbatim trigger wording
  (see "Register-sensitivity handling" above). Consequence:
  `interleaved_2plus` never resolved to a concrete true/false value in this
  sample -- every row reads `n/a` (derived: the "Secondary instrumentation"
  table above, 4 rows, all `n/a`) because none of the runs had 2+ distinct
  skill opens to compare. Per acceptance bullet 5's empty-state clause,
  this is reported as a measured null (0 opens), not omitted or listed as
  unmeasured. Resolution path: this is the same population/coverage
  question the issue's own two comments are still debating (coverage gap
  vs. vocabulary-register mismatch vs. task difficulty not warranting the
  procedure). A follow-up with a larger pair count would be needed to get a
  sample with nonzero invocations to check `interleaved_2plus` against.
  Filed as a scope-boundary note here rather than a new issue, since this
  issue's own deliverable (the harness) already surfaces the gap rather
  than hiding it.
- none other.

## Next steps

loop_state is terminal (`landed`): the harness exists, is documented, and
was run 4 times producing a scored, instrumented baseline satisfying every
Acceptance bullet in issue #3041. No further action is required for this
issue; a natural follow-up (more pairs, to get a non-null-invocation
sample) is a new, separate unit of work and is named above as an open
finding rather than started here.

## Skill verdicts

Invoked via the Skill tool near the end of this session, after the harness
was built and all 4 pairs had already run, as an explicit audit pass
against this record's own top-line claim (rather than during the build --
see "Open findings" above for what that ordering cost: a pre-registration
gap that would not exist had these been invoked before running the pairs).

- skill-verdict: experiment-trust — applied: invoked; Step 5's
  Twyman's-law gate was applied to this record's own surprising result
  (0-of-4 skill invocations) and produced the independent cross-check
  logged under "Open findings" (canonical: the "Twyman's-law cross-check"
  bullet under `## Open findings` above, citing
  `/tmp/smoketest/out2.jsonl` line 9). Step 1's scope gate also confirms
  this offline paired comparison is not itself the kind of randomized
  online experiment the SRM/A-A machinery (Steps 2-4) applies to --
  correctly not attempted here.
- skill-verdict: hypothesis-testing — applied: invoked; its Step 4
  pre-registration gate is what surfaced the pre-registration gap now
  logged under "Open findings" (canonical: the "Pre-registration gap"
  bullet under `## Open findings` above) -- this session had fixed the
  test design before running, but not a numeric win threshold, which the
  skill classifies as a procedure violation to record rather than hide.
- skill-verdict: product-discovery-hypothesis-preregistration — applied:
  invoked; its rule 1 (numeric threshold + decision rule fixed before
  data) independently names the same gap as `hypothesis-testing` Step 4
  (canonical: the same "Pre-registration gap" bullet above), cross-confirming
  it's a real omission rather than one skill's idiosyncratic framing.
- skill-verdict: implementation-blueprint — applied: invoked; its
  `classify` tool was run against the harness's own shape and returned the
  `pipeline` archetype with a 5-unit-or-fewer solo-build threshold
  (canonical: the "implementation-blueprint classify confirms" bullet
  under `## Open findings` above), logged there as confirmation of the
  already-built layout rather than a design input, since it ran after the
  code existed.
- other mounted skills: not triggered.
