# Paired skills-on/skills-off harness (issue #3041)

Builds and scores one paired run: the same task text executed twice against
the same pinned commit of the target repo, once with the full skill corpus
available and once with `--disable-slash-commands` (skill layer suppressed),
in separate clones so neither arm can see the other's work.

## Invocation

```bash
bash scripts/issue-3041/run_pair.sh \
  scripts/issue-3041/tasks/01-study-groups.txt \
  01-study-groups \
  <output-root>
```

Run as written, this produces two workspaces and two deliverables for one
task:

```
<output-root>/01-study-groups/skills-on/DELIVERABLE.md
<output-root>/01-study-groups/skills-off/DELIVERABLE.md
<output-root>/01-study-groups/skills-on.session.jsonl
<output-root>/01-study-groups/skills-off.session.jsonl
```

Then score the pair blind:

```bash
python3 scripts/issue-3041/evaluate_pair.py \
  scripts/issue-3041/tasks/01-study-groups.txt \
  scripts/issue-3041/rubrics/01-study-groups.md \
  <output-root>/01-study-groups/skills-on/DELIVERABLE.md \
  <output-root>/01-study-groups/skills-off/DELIVERABLE.md \
  <output-root>/01-study-groups/verdict.json
```

And pull secondary instrumentation for the skills-on arm:

```bash
python3 scripts/issue-3041/instrument.py <output-root>/01-study-groups/skills-on.session.jsonl
```

## What is held constant vs. what varies

Held constant across the two arms of a pair: model (`sonnet`), target-repo
commit (pinned SHA, cloned once into a seed then copied so both arms start
from byte-identical state), task text, permission mode, and allowed
non-Skill tools. The only thing that differs is whether the skill layer is
present (`Skill` in `--tools` plus the default full corpus) or suppressed
(`--disable-slash-commands`, `Skill` excluded from `--tools`).

`--setting-sources project,local` is passed to both arms and to the
evaluator to keep this repo's own operator hooks (proposal/warrant/freelunch
directives etc., which are registered at the user settings level and would
otherwise fire inside the target-repo clone too) from leaking into the
subject sessions. It affects both arms identically, so it does not
differentially confound the comparison.

The skills-on arm also passes `--plugin-dir "$PLUGIN_DIR"` (resolved from
`$MUSTER_SKILL_REGISTRY_ROOT`'s parent, falling back to `$HOME/skill-registry`).
This is not redundant with `--setting-sources`: marketplace plugins register
at `user` scope on this machine, the same scope that carries this repo's
operator-hook plugin, so `--setting-sources project,local` alone (issue
#3041's original invocation) mounted zero marketplace skills in the
skills-on arm -- the `Skill` tool was present but nothing was behind it
(issue #3053). `--plugin-dir` is session-scoped and orthogonal to
`--setting-sources`: it loads the target skill corpus without the
operator-hook plugin coming along. Verified live in issue #3053 (init event
carries the full corpus, transcript has no hook-leak signal). The
skills-off arm needs no equivalent change: `--disable-slash-commands`
suppresses the skill layer regardless of what `--plugin-dir` would load.

## Blinding

`evaluate_pair.py` calls a fresh `claude -p` process with `--tools ""` (no
tool access at all -- it cannot inspect either workspace, git history, or
any path that would disclose the arm). It never generated either
deliverable. Which deliverable is labeled "Document 1" vs "Document 2" is
randomized per call and recorded only in the script's own JSON output, never
shown to the evaluator.

## Scoring inputs

The evaluator sees only: the task text, a rubric derived from what the
target methodology skill for that task claims a good answer contains
(`rubrics/*.md`), and the two blinded deliverables. It never sees
call-success, mount-count, or open-timing -- those are recorded separately
by `instrument.py` from the skills-on arm's own transcript, purely as
diagnostic instrumentation.

## Task-text register (uncontrolled-variable handling)

Issue #3041's second comment reports that skill selection is sensitive to
the vocabulary register of the task text -- the same idea phrased in the
skill's own vocabulary (research register) retrieves it; phrased in plain
or engineering register, it may not. Task texts in `tasks/` are deliberately
written in a single, plain "stakeholder request" register across all
pairs -- avoiding both the target skill's own jargon (e.g. no
"falsifiable", "pre-register", "decision rule", "guardrail metric" in
`02-onboarding-experiment.txt`, no "archetype" in `03-review-scheduler.txt`)
and raw engineering register. This register is held fixed across the two
arms *within* a pair (both arms receive byte-identical task text), so
phrasing cannot differentially advantage one arm over the other in the same
pair -- it can only affect whether the skills-on arm's selector finds a
fitting skill at all, which is itself part of what this harness measures.
`instrument.py`'s `distinct_skills` field reports whichever skill(s)
actually opened per run, so a selection miss is visible in the record
rather than silently absorbed into the rubric.

## Target-repo grounding (issue #3053)

The original 4 task texts (issue #3041) were self-contained synthetic
scenarios, written when the pinned `study-companion` commit held only 3
scaffolding files. `PIN_SHA` now points past that -- past a landed,
independently-verified discovery report on a comprehension-gap job
(`docs/issue-1`) and a one-pager for it (`docs/issue-5`, live on the
`issue-5/product-discovery-one-pager+...` branch as of this pin; not yet
merged to `study-companion`'s `main`, but real, reviewed content at this
commit). Task texts 01, 02, and 04 were rewritten to require reading those
documents and reason about their actual content (e.g. task 04 asks whether
the one-pager's own proposed pilot design can produce a "stop," the same
question that document's own independent verification raised). Task 03 (the
review scheduler) has no application code to ground against even at this
pin -- its text now says so explicitly and asks the model to treat it as
green-field, rather than silently reusing a task written for a repo that no
longer matches what it claims.
