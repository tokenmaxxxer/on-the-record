---
issue: 3053
role: experiment-trust+adversarial-review+hypothesis-testing+conformance-review-verdict-assignment-27c56ae7
author: experiment-trust+adversarial-review+hypothesis-testing+conformance-review-verdict-assignment-27c56ae7
skills: experiment-trust (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), hypothesis-testing (skill-repository(c05de12)), conformance-review-verdict-assignment (skill-repository(c05de12))
verifies_subject: true  # second independent, builder-blind verification of PR #3074's own deliverable against issue #3053
code_under_review: 2272ffa44dd1ef66add01ebf7f56585ad68973cc
type: defect-verification-record
breaking: false
verdict: All 4 written acceptance criteria re-derived Present a third time
  (see "What was done" for the re-run commands, matching PR #3074's own
  report and the first verification exactly). This record's own angle,
  worked out below with quoted evaluator reasoning and a per-pair
  arithmetic table: the blind-scoring leak the first verification found
  nets to zero effect on the reported margin, and neither the cited
  skills nor any mounted directive instructs the self-citation that caused
  it -- see "Distinct angle 2" for why it recurs anyway. Honest framing:
  the aggregate margin cannot be reported as a blind-scored result without
  caveat, but the "indistinguishable" call itself is not overturned.
loop_state: landed
upstream:
  - path: PR #3074 (github.com/tokenmaxxxer/on-the-record/pull/3074), head
      commit 2272ffa4 -- not merged to main, untracked in this repo's own
      tree; fetched read-only this session as local ref pr-3074-verify2
    sha: 2272ffa44dd1ef66add01ebf7f56585ad68973cc
  - path: docs/issue-3053/reports/experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-881863c9.md
      (the first independent verification, landed on main)
    sha: same-commit
  - path: docs/issue-3053/_assets/*/ -- untracked here, exists only on PR
      #3074's branch
    sha: 3ecf7c80776408d9aa33eefad9ad6a47ee3ed4ae
---

# issue-3053 — experiment-trust+adversarial-review+hypothesis-testing+conformance-review-verdict-assignment-27c56ae7 record

## What was done

Second independent, builder-blind verification of PR #3074 against issue
#3053. Read the first verification's landed record first, then worked out
this task's own distinct angle: the blind-scoring leak's actual effect on
the reported result, and whether that leak is a one-off artifact of this
run or a structural property of skills-on arms.

canonical: `git rev-parse pr-3074-verify2` -> `2272ffa44dd1ef66add01ebf7f56585ad68973cc`,
run this session -- matches `code_under_review:` above, and matches the
commit the first verification cited (`2272ffa4`), confirming PR #3074 has
not been rebased between the two verification passes.

canonical: `docs/issue-3053/reports/experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-881863c9.md`
(read this session, on `main`) -- established: all 4 written acceptance
criteria Present, every PR #3074 figure re-derived exactly, the +/-3
threshold pre-registered by commit order, and one unreported defect: 3 of
4 (grep count reproduced below) skills-on `DELIVERABLE.md` files cite
their own skill slugs by name, while 0 of 4 skills-off deliverables do.

**Setup.** `git fetch origin pull/3074/head:pr-3074-verify2` (resolves to
`2272ffa4`), then `git archive pr-3074-verify2 docs/issue-3053/_assets
docs/issue-3053/decisions scripts/issue-3041 | tar -x` into
`/tmp/pr3074check2` for read-only inspection -- no merge, no edit to the PR
branch, no push. Every `docs/issue-3053/_assets/...` and
`scripts/issue-3041/...` path cited below is untracked on `main` and
exists only on PR #3074's branch, commit `3ecf7c80` -- not re-stated at
every citation.

### Re-confirmation of the 4 literal acceptance criteria (third derivation)

```
$ python3 h1_check.py    # same H1 mount test as the issue's own check
4
$ grep -L '"Skill"' docs/issue-3053/_assets/*/skills-off.session.jsonl | wc -l
4
$ ls -d docs/issue-3053/_assets/*/ | wc -l
4
$ grep -l document_1_score docs/issue-3053/_assets/*/verdict.json | wc -l
4
```
derived: the 4 commands above, run this session against
`/tmp/pr3074check2/docs/issue-3053/_assets/` extracted from PR #3074 commit
`3ecf7c80` -- 4/4 on every check, identical to PR #3074's own reported
test-plan results and to the first verification's independent
re-derivation. **All 4 criteria: Present**, carried forward per
conformance-review-verdict-assignment rule 4 (same evidence, same commit,
third independent confirmation) -- not re-litigated further below; this
record's distinct contribution is the leak-effect analysis that follows.

### Distinct angle 1 — does the leak explain the outcome?

```
$ python3 skill_opens.py   # walks tool_use blocks, name=='Skill', over each skills-on.session.jsonl
01-study-groups.session.jsonl:          hypothesis-testing
02-onboarding-experiment.session.jsonl: product-discovery-hypothesis-preregistration, experiment-trust, product-discovery-guardrail-metrics
03-review-scheduler.session.jsonl:      skill-registry:code-architecture
04-pilot-trust.session.jsonl:           skill-registry:product-discovery-hypothesis-preregistration, skill-registry:hypothesis-testing, skill-registry:experiment-trust
$ grep -in -E "hypothesis-testing|experiment-trust|product-discovery-" docs/issue-3053/_assets/*/skills-on/DELIVERABLE.md
01-study-groups/skills-on/DELIVERABLE.md:3:...(per `hypothesis-testing`)
02-onboarding-experiment/skills-on/DELIVERABLE.md:3:Pre-registered per `product-discovery-hypothesis-preregistration`
04-pilot-trust/skills-on/DELIVERABLE.md:32,35:...(hypothesis-testing, product-discovery-hypothesis-preregistration...) / ...(experiment-trust)...
$ grep -in "code-architecture" docs/issue-3053/_assets/03-review-scheduler/skills-on/DELIVERABLE.md
(no output)
```
derived: the 4 commands above, written and run this session -- 3 of 4
(3/4=75%) of the skills-on sessions (01, 02, 04) both invoked a skill AND
named that exact skill inside their own `DELIVERABLE.md`; the 4th (03)
invoked a skill (`code-architecture`) but never names it in its
deliverable (0 matches, shown in the code fence directly above).

Mapped each pair's `verdict.json` `document_N_actual_arm` field to its
`document_N_score`:
```
$ python3 margin.py   # reads document_1_actual_arm/document_2_actual_arm + document_N_score per verdict.json
01-study-groups:            skills-on=8  skills-off=9  on-margin=-1  (skills-on DELIVERABLE cites hypothesis-testing)
02-onboarding-experiment:   skills-on=9  skills-off=9  on-margin=0   (skills-on DELIVERABLE cites product-discovery-hypothesis-preregistration)
03-review-scheduler:        skills-on=9  skills-off=8  on-margin=+1  (skills-on DELIVERABLE cites nothing)
04-pilot-trust:             skills-on=9  skills-off=8  on-margin=+1  (skills-on DELIVERABLE cites hypothesis-testing, experiment-trust, product-discovery-hypothesis-preregistration)
sum skills-on=8+9+9+9=35  sum skills-off=9+9+8+8=34  total margin=35-34=+1
leaked-pairs net = -1+0+1 = 0
```
derived: `python3 margin.py`, written and run this session directly against
each pair's own `verdict.json` fields (not against PR #3074's or the first
verification's prose) -- matches "35 to 34" exactly, and decomposes it:
the three cited (leaked) pairs' own on-margins sum to 0 (-1+0+1=0, shown
in the code fence above). **The entire +1 aggregate margin is produced by
pair 03 alone -- the one pair with no citation in either deliverable.**

**Quoted evaluator reasoning, checked for any sign of citation-driven
scoring** (canonical: each pair's own `evaluator_verdict.reasoning` field
in its `verdict.json`, read this session, untracked here, exists only on
PR #3074's branch commit `3ecf7c80`):

- Pair 01 (skills-on cites `hypothesis-testing`, loses 8 to 9): "Document 2
  edges ahead by grounding its claims more tightly in cited evidence
  (specific rows, quotes, a comparative table) and by more precisely
  distinguishing discovery/logistics failure from fit/quality failure as
  the key open condition, making its 'what would need to be true' section
  sharper and less generic than Document 1's." No skill name appears; the
  citing document lost anyway.
- Pair 02 (skills-on cites `product-discovery-hypothesis-preregistration`,
  ties 9 to 9): "Both name a single primary metric with a
  pre-registration-committed numeric threshold (D1: +8pp/2x relative; D2:
  +10pp with a durability sub-condition) ... neither has a meaningful edge
  against the rubric's specific criteria." "Pre-registration" is applied to
  **both** documents equally, including the uncited skills-off one -- read
  as a rubric concept found in both texts' content, not the leaked slug
  string, which never appears.
- Pair 04 (skills-on cites all three of `hypothesis-testing`,
  `experiment-trust`, `product-discovery-hypothesis-preregistration`, wins
  9 to 8): "Document 2 goes further by adding a three-bin
  (stop/proceed/inconclusive-retest) framework, explicitly distinguishes
  the predicted-vs-actual gap metric as unregistered and ripe for post-hoc
  rationalization ... more sharply, and adds an interim-peeking/early-stop
  policy gap that Document 1 omits." No literal skill-slug string appears;
  the credited content is the kind of output the cited skills' procedures
  produce, but the evaluator is scoring that substance, not the citation.

```
$ grep -iE "hypothesis-testing|experiment-trust|product-discovery-" docs/issue-3053/_assets/*/verdict.json
(no output)
```
derived: the `grep` command above, run this session against all 4
`verdict.json` files (which embed the full `evaluator_verdict.reasoning`
text) -- zero matches across all 4 files. The evaluator's stated reasoning
never quotes the leaked skill-slug strings, either to reward them as
rigour or penalise them as jargon; on the retained record it appears to
have ignored them and scored on content. A stated rationale cannot fully
rule out latent influence on the numeric score itself, but this is the
strongest evidence the retained artifacts provide, and it is consistent
with the arithmetic above: the leaked pairs cancel to exactly 0 (-1+0+1=0,
shown in the `margin.py` code fence above), which is what "no net effect"
would mechanically look like if the leak is inert.

**Judgment on whether the 35-34 margin survives as meaningful.** derived:
the citation grep above (0 matches for the skills-off side, 3 matches for
the skills-on side) -- the honest statement is that the comparison was not
blind for 3 of 4 pairs (3/4=75%), so the aggregate "35 to 34" cannot be
reported as a blind-scored result without that caveat -- the harness's
blinding design (no filesystem access in `evaluate_pair.py`) did not
anticipate a citation inside the document text itself. That said, this
defect does not overturn PR #3074's actual verdict: since the 3 leaked
pairs cancel to a net contribution of 0 (-1+0+1=0, shown in the `margin.py`
code fence above), the reported margin is arithmetically identical to a
maximally conservative "discard every leaked pair" analysis, which leaves
only the single unleaked pair's own +1 -- still far short of the
pre-registered +/-3 bar either way. The correct framing for a future
reader: "indistinguishable" still holds, but not because a 4-pair blind
comparison found no difference -- because a compromised comparison
happened to net to zero on its leaked pairs, leaving one genuinely blind
pair whose own margin was already too small to cross the registered bar.
PR #3074's own record does not draw this distinction.

### Distinct angle 2 — is the leak a run artifact or a structural property?

```
$ grep -inE "cite|citation|name the skill|mention the skill|\(per \`|skill name|skill slug" \
    /home/jwjung/skill-registry/skills/hypothesis-testing/SKILL.md \
    /home/jwjung/skill-registry/skills/experiment-trust/SKILL.md \
    /home/jwjung/skill-registry/skills/product-discovery-hypothesis-preregistration/SKILL.md
hypothesis-testing/SKILL.md:84: ... cites the registered threshold and the measured number ...
hypothesis-testing/SKILL.md:98: ... cite the metric and the measured vs. registered threshold ...
experiment-trust/SKILL.md:37:  ... the verdict already cites registered thresholds vs. measured numbers ...
```
derived: the `grep` command above, run this session against the three
cited skills' own `SKILL.md` files (each also read in full this session)
-- every "cite" instruction found is about citing thresholds/measured
numbers, never about citing the skill's own name. No skill file instructs
self-attribution in the deliverable it produces.

```
$ git show pr-3074-verify2:scripts/issue-3041/run_pair.sh | sed -n '85,95p'
        --setting-sources project,local \
        --plugin-dir "$PLUGIN_DIR" \
        --tools "$TOOLS_ON" \
$ find /home/jwjung/skill-registry -iname "hooks*" -o -iname "*.json" | grep -v "/\.git/"
(no output)
```
derived: the two commands above -- `--setting-sources project,local`
excludes the `user` scope where the on-the-record marketplace plugin (and
its own skill-verdict-obligation hook) is registered on this machine, and
`--plugin-dir` points at a bare `skill-registry/` tree containing only
`SKILL.md` + `references/` per skill, no `hooks.json`, no plugin manifest.
The skills-on session that produced these deliverables never received the
on-the-record skill-verdict directive or any other hook that could
instruct self-citation -- derived: the citation grep in "Distinct angle 1"
above -- the citation behavior found in 3 of 4 deliverables (3/4=75%) is
not injected by any harness component or by the skill files themselves.

```
$ grep -in "code-architecture" docs/issue-3053/_assets/03-review-scheduler/skills-on/DELIVERABLE.md
(no output)
$ grep -inE "cite|auditable|written down|disclos" /home/jwjung/skill-registry/skills/code-architecture/SKILL.md
(no output)
```
derived: the two commands above -- pair 03's skills-on session invoked
`skill-registry:code-architecture` (see the skill-opens listing in
"Distinct angle 1" above) but its `DELIVERABLE.md` never names that skill,
and `code-architecture/SKILL.md` itself carries none of the
"cite/auditable/written down/disclose" language the other three skills
repeat (`hypothesis-testing/SKILL.md` Step 6: "auditable, not silent";
`experiment-trust/SKILL.md` Step 6: "every deviation individually named").
derived: the skill-opens listing and citation grep, both shown in
"Distinct angle 1" above -- every one of the 3 skills-on sessions that
invoked a skill from that audit-oriented family (01, 02, 04; 3/3=100%)
named it in its own deliverable; the other skills-on session, the 1 that
invoked a differently-styled skill (03; 1/1=100% of that group), did not.
This is a small sample (4 skills-on runs total, 1 outside the family), so
it is not proof of a universal rule, but the pattern tracks skill genre
across three unrelated task texts (a discovery brief, an A/B
pre-registration, a trust-pilot review), not shared task content --
consistent with a structural tendency of this skill family's own
disclosure ethos, not a one-off fluke of this run. A future skills-on arm
drawing on this same family should be expected to leak the same way;
blinding by document text alone would need an explicit scrub step or an
evaluator prompt that discounts methodology name-dropping, not just
`evaluate_pair.py`'s existing no-filesystem-access design.

## Why

Applied `adversarial-review`'s blind-evaluator discipline to this
verification's own method: every reasoning quote above is read directly
from PR #3074's retained `verdict.json` files (canonical, quoted verbatim
above), and every count is recomputed this session (derived, commands
shown above), not taken from PR #3074's or the first verification's own
prose.

Applied `experiment-trust`'s Twyman's-law posture to the reported margin:
treated "the leak doesn't correlate with winning" (the first
verification's finding) as a claim needing its own numeric check, and the
per-pair decomposition above (derived: `margin.py` output, "Distinct angle
1", "-1+0+1=0") is this record's own independent confirmation of that
claim, not a restatement of it.

Applied `hypothesis-testing`'s Step 6 framing (the registered rule, not
post-hoc judgment, makes the call): the "Judgment" paragraph in "Distinct
angle 1" above (derived: `margin.py` output cited there) shows a "discard
all 3 leaked pairs" worst-case re-analysis still does not cross the
registered +/-3 bar (derived: `margin.py` output, "Distinct angle 1"
above), so this defect does not change which decision the pre-registered
rule reaches.

Applied `conformance-review-verdict-assignment` rule 1 (Surface vs.
Present) to distinguish the 4 literal, mechanical acceptance criteria (all
Present, carried forward per rule 4 from two prior independent
confirmations, re-run again in "Re-confirmation" above) from the
qualitative "blind scoring" premise underlying criterion 4's reported
margin: derived, the citation grep in "Distinct angle 1" above -- that
premise is Surface, not Present, for 3 of 4 pairs (3/4=75%) -- the
blinding mechanism (`evaluate_pair.py`'s no-filesystem-access design)
exists and is real, but does not fire on the actual condition "the
evaluator cannot infer arm identity" for those pairs.

## Upstream basis

canonical: `git rev-parse pr-3074-verify2` -> `2272ffa44dd1ef66add01ebf7f56585ad68973cc`
(run this session, see "What was done" above) -- matches the first
verification's cited head commit, confirming no rebase between passes.

- PR #3074, head `2272ffa4` -- the subject of this verification, not
  merged to `main`; fetched read-only this session (`git fetch origin
  pull/3074/head:pr-3074-verify2`, see "What was done" above).
- `docs/issue-3053/reports/experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-881863c9.md`
  (first verification, on `main`) -- read this session for its established
  facts before deriving this record's own distinct angle; canonical tag
  and summary of its findings given in "What was done" above.
- `docs/issue-3053/_assets/{01-study-groups,02-onboarding-experiment,
  03-review-scheduler,04-pilot-trust}/` -- untracked on `main`, exists only
  on PR #3074's branch, commit `3ecf7c80` -- all 8 `DELIVERABLE.md` files
  and all 4 `verdict.json` files read and quoted from directly this
  session (see "Distinct angle 1" above for the derived commands).
- `scripts/issue-3041/run_pair.sh` -- on PR #3074's branch, commit
  `3ecf7c80` -- read this session (command and output shown in "Distinct
  angle 2" above) to confirm the skills-on invocation's
  `--setting-sources`/`--plugin-dir` scope and rule out on-the-record hook
  injection.
- `/home/jwjung/skill-registry/skills/{hypothesis-testing,experiment-trust,
  product-discovery-hypothesis-preregistration,code-architecture}/SKILL.md`
  -- read in full this session (grep commands and output shown in
  "Distinct angle 2" above) to check for any self-citation instruction and
  compare the audit-oriented family's language against
  `code-architecture`'s.

## What did not work

None -- this record's distinct-angle findings (the leaked pairs' exact
cancellation, the absence of citation-string matches in the evaluator
reasoning, and the family-specific structural pattern) were all derived
successfully from the retained assets on the first attempt (see the
`derived:`/`canonical:` commands throughout "What was done" above); nothing
attempted here failed or was reverted.

## Open findings

- **The "35 to 34" margin should not be cited as a blind-scored result
  without caveat.** derived: the citation grep in "Distinct angle 1"
  above -- 3 of 4 pairs (3/4=75%) carried a textual tell in the skills-on
  deliverable. Resolution path (sharpening the first verification's own
  item): a future run should either instruct the skills-on arm not to
  name the methodology it drew on inside the deliverable text, have the
  evaluator prompt explicitly discount methodology name-dropping, or have
  the harness strip skill-slug mentions from `DELIVERABLE.md` before
  `evaluate_pair.py` ever sees it. This record's addition: the leak's
  real-world impact on *this* run's reported figure was zero net effect
  via cancellation (-1+0+1=0, shown in the `margin.py` code fence in
  "Distinct angle 1" above), not because the leak never mattered -- a
  property of this run's particular scores, not a guarantee for a future
  run with a different score distribution.
- **The skill-family-specific citation pattern is a standing risk for
  future paired runs, not just this one.** derived: the skill-opens vs.
  citation cross-reference in "Distinct angle 2" above -- every one of the
  3 within-family invocations was cited (3/3=100%); the 1 non-family
  invocation was not (1/1=100% of that single-item group). Any future
  skills-on arm drawing on `hypothesis-testing`, `experiment-trust`, or a
  `product-discovery-hypothesis-*` skill should be expected to name that
  skill in its own deliverable text unprompted. No action taken beyond
  naming it here, per this task's scope (verify, do not edit the PR, do
  not merge).
- none other beyond the two items above -- the items the first
  verification opened (the `--disable-slash-commands` asymmetry, the
  pre-registration threshold provenance, n=4 statistical power, and the
  citation leak itself) are not re-opened here; the two items above
  sharpen the first verification's own citation-leak finding rather than
  duplicate it.

## Next steps

loop_state is terminal (`landed`): the 4 literal acceptance criteria are
Present for the third independent time (re-run in "Re-confirmation"
above), the leak's numeric effect on the reported margin is fully
decomposed and quoted (derived: `margin.py` output, "Distinct angle 1"
above), and the structural question (run artifact vs. skill-family
property) is answered with its own evidence in "Distinct angle 2" above.
Per this task's scope (verify, do not edit the PR, do not merge), no
further action from this session.

skill-verdict: adversarial-review — applied: invoked; this record's core
method is reading PR #3074's own retained `verdict.json` reasoning fields
directly and quoting them verbatim rather than trusting either PR #3074's
or the first verification's characterization of "no correlation with
winning" -- the per-pair arithmetic decomposition (derived: `margin.py`
output, "Distinct angle 1" above, "-1+0+1=0") is this session's own
independent finding, sharper than what either prior document stated.
skill-verdict: experiment-trust — applied: invoked; applied Twyman's-law
skepticism to the claim "the leak doesn't explain the outcome" by
recomputing the leaked pairs' own net contribution (derived: `margin.py`
output, "Distinct angle 1" above) rather than accepting the correlation
check at face value, and confirmed a "discard all leaked pairs" worst case
still falls short of the registered +/-3 bar (derived: `margin.py` output,
"Distinct angle 1" above).
skill-verdict: hypothesis-testing — applied: invoked; confirmed the
pre-registered decision rule's mechanical bar (wins>=3 of 4 and margin>=3,
per the first verification's citation of `pre-registration.md` field (d))
is not crossed under any re-analysis of the leak (derived: `margin.py`
output, "Distinct angle 1" above), full data or leaked-pairs-discarded
alike, so the registered rule's own call is not what this defect puts at
risk.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
carried the 4 literal acceptance criteria forward as Present per rule 4
(same evidence, third independent confirmation, re-derived rather than
blindly trusted, see "Re-confirmation" above) and applied rule 1 (Surface
vs. Present) to the qualitative "blind scoring" premise underlying
criterion 4's margin: derived, the citation grep in "Distinct angle 1"
above -- Surface, not Present, for 3 of 4 pairs (3/4=75%) -- the blinding
mechanism exists in the harness but does not fire on the actual condition
of arm-identity concealment for those pairs.
