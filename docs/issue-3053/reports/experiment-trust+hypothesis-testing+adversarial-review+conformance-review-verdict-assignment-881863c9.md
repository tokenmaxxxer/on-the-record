---
issue: 3053
role: experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-881863c9
author: experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-881863c9
skills: experiment-trust (skill-repository(c05de12)), hypothesis-testing (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), conformance-review-verdict-assignment (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3074's own deliverable against issue #3053
code_under_review: 2272ffa44dd1ef66add01ebf7f56585ad68973cc
type: defect-verification-record
breaking: false
verdict: All 4 written acceptance criteria Present, must-not clause held.
  Every reported figure re-derived independently from PR #3074's own
  retained assets and matches exactly (see Results in "What was done"
  below). The +/-3 threshold was pre-registered by commit order before the
  run. One unreported defect found independently, not in PR #3074's own
  record -- see "Open findings".
loop_state: landed
upstream:
  - path: PR #3074 (github.com/tokenmaxxxxer/on-the-record/pull/3074),
      fetched as local ref pr-3074-review, head commit 2272ffa4 -- not
      merged to main, untracked in this repo's own tree
    sha: 2272ffa44dd1ef66add01ebf7f56585ad68973cc
  - path: docs/issue-3053/decisions/pre-registration.md -- untracked here,
      exists only on PR #3074's branch (commit 4c064708)
    sha: 4c0647085c5013663b82dc65bac1cca74fb2031d
  - path: docs/issue-3053/_assets/*/ -- untracked here, exists only on PR
      #3074's branch (commit 3ecf7c80)
    sha: 3ecf7c80776408d9aa33eefad9ad6a47ee3ed4ae
---

# issue-3053 — experiment-trust+hypothesis-testing+adversarial-review+conformance-review-verdict-assignment-881863c9 record

## What was done

Independent, builder-blind verification of PR #3074 against issue #3053's
Acceptance section. PR #3074 is not yet merged: `docs/issue-3053/_assets/`
and `docs/issue-3053/decisions/` are untracked in this repository's own
tree and exist only on PR #3074's branch. Worked only from the retained
assets and harness code on that branch, re-deriving every reported figure
rather than trusting the PR body or the PR's own record.

canonical: `gh pr view 3074` (state OPEN, 8 commits), `gh issue view 3053
--comments` (4 comments: retraction, re-anchor, consumer-path amendment,
session-end watch), both read this session.

**Setup.** `git fetch origin pull/3074/head:pr-3074-review` (resolves to
`2272ffa4`), then `git archive pr-3074-review docs/issue-3053/_assets |
tar -x` into `/tmp/pr3074check` for read-only inspection -- no merge, no
edit to the PR branch, no push.

**Re-derivation of all 4 acceptance criteria**, independent of the PR's own
record, run against the extracted (untracked-here) `_assets` tree:

```
$ python3 -c "
import json,glob,sys
n=0
for f in glob.glob('docs/issue-3053/_assets/*/skills-on.session.jsonl'):
    for line in open(f):
        d=json.loads(line)
        if d.get('type')=='system' and d.get('subtype')=='init':
            n += 1 if len(d.get('skills') or []) > 20 else 0
            break
print(n)"
4
$ grep -L '"Skill"' docs/issue-3053/_assets/*/skills-off.session.jsonl | wc -l
4
$ ls -d docs/issue-3053/_assets/*/ | wc -l
4
$ grep -l document_1_score docs/issue-3053/_assets/*/verdict.json | wc -l
4
```
derived: the 4 commands above, run this session against
`/tmp/pr3074check/docs/issue-3053/_assets/` (extracted from PR #3074
commit `3ecf7c80`, untracked on `main`) -- these are the issue's own
literal acceptance checks, all 4 pass, matching PR #3074's own reported
test-plan results.

**Criterion 1 (H1 mount, from the raw init event, not config).** A second,
independent pass printing the raw per-file counts:
```
$ python3 check.py   # written this session
=== H1: skills-on init event skill counts ===
docs/issue-3053/_assets/01-study-groups/skills-on.session.jsonl skills_count= 290
docs/issue-3053/_assets/02-onboarding-experiment/skills-on.session.jsonl skills_count= 290
docs/issue-3053/_assets/03-review-scheduler/skills-on.session.jsonl skills_count= 290
docs/issue-3053/_assets/04-pilot-trust/skills-on.session.jsonl skills_count= 290
```
derived: `python3 check.py`, run this session -- 290 skills in all 4, each
>20, matching PR #3074's own claim of "290 skills, not 17" against the
retracted baseline's 17-built-ins-only mount. **Verdict: Present.**

**Criterion 2 (skills-off arm still lacks Skill, arms differ only in the
intended way).** `grep -L` above shows all 4 skills-off logs lack the
`"Skill"` substring entirely. Cross-checked against the harness script
itself:
```
$ git show pr-3074-review:scripts/issue-3041/run_pair.sh | grep -n "TOOLS_ON=\|TOOLS_OFF=\|plugin-dir\|disable-slash"
27:TOOLS_ON="Read,Glob,Grep,Write,Edit,TodoWrite,Skill"
28:TOOLS_OFF="Read,Glob,Grep,Write,Edit,TodoWrite"
91:        --plugin-dir "$PLUGIN_DIR" \
105:        --disable-slash-commands \
```
derived: `git show pr-3074-review:scripts/issue-3041/run_pair.sh | grep -n
...`, run this session against PR #3074's branch -- the tool-use surface
differs only by `Skill`; `--plugin-dir` is present on the skills-on
invocation only (line 91, mounts the corpus). One additional, pre-existing
asymmetry found: `--disable-slash-commands` on the skills-off invocation
only (line 105) -- filed under "Open findings" below with a re-check
before judging it non-blocking. **Verdict: Present** (caveat filed, not a
criterion failure).

**Criterion 3 (>=3 pairs against real target-repo content, not
scaffolding).** `ls -d` above shows 4 pair directories. Independently
cloned `JiwonJung94/study-companion` at the pinned commit myself (not from
PR #3074's citation of it):
```
$ git clone --quiet https://github.com/JiwonJung94/study-companion.git sc-check
$ cd sc-check && git checkout --quiet d6f14aebd1a79002fda3a7f22320ee63c6e7a736
$ git ls-tree -r --name-only HEAD | grep -E "^docs/" | sort
docs/issue-1/reports/conformance-review-verdict-assignment+adversarial-review+research-evidence-discipline+conformance-review-traceability-and-evidence-1ec6a09c.md
docs/issue-1/reports/research-evidence-discipline+user-discovery-evidence-strength-tagging-1ae594fd.md
docs/issue-1/reports/user-discovery+research-evidence-discipline+user-discovery-evidence-strength-tagging+user-discovery-switch-timeline-causal-forces-2d8db0b0.md
docs/issue-5/reports/product-discovery-one-pager+product-discovery-jtbd-problem-framing+market-analysis-jtbd-fit+decision-brief-4cd9b7bb.md
docs/issue-5/specs/one-pager.md
docs/specs/approvers.md
docs/specs/requirement-digest.md
```
derived: `git clone`/`git checkout`/`git ls-tree`, all run this session
directly against the external `study-companion` repository (a separate
GitHub repo, not a path inside this repository), pinned at
`d6f14aebd1a79002fda3a7f22320ee63c6e7a736` -- a discovery report plus 2
verification records, and a product one-pager plus its own report, all
real content, not the 3-scaffolding-file state the retracted baseline
(issue #3053's first comment) ran against. **Verdict: Present.**

**Criterion 4 (verdict states better/worse/indistinguishable, per-pair
scores, reversal condition, skill-open count alongside).** `grep -l
document_1_score` above shows 4 verdict.json files. Re-derived every score
from each file's own `document_N_actual_arm` + `evaluator_verdict.
document_N_score` fields (not from PR #3074's table):
```
$ python3 scores.py   # written this session
docs/issue-3053/_assets/01-study-groups/verdict.json skills-on= 8 skills-off= 9
docs/issue-3053/_assets/02-onboarding-experiment/verdict.json skills-on= 9 skills-off= 9
docs/issue-3053/_assets/03-review-scheduler/verdict.json skills-on= 9 skills-off= 8
docs/issue-3053/_assets/04-pilot-trust/verdict.json skills-on= 9 skills-off= 8

sum skills-on= 35 sum skills-off= 34 margin= 1
wins_on= 2 ties= 1 wins_off= 1
```
derived: `python3 scores.py` (reads `document_1_actual_arm`/
`document_2_actual_arm` and maps each to `evaluator_verdict.
document_N_score`), run this session -- matches PR #3074's reported
"35 to 34 ... 2 wins to 1 with a tie" exactly. Skill-open count
independently re-derived by walking `tool_use` blocks
(`block.get('name')=='Skill'`) over each skills-on session log:
```
$ python3 check.py   # same script as criterion 1, second section
docs/issue-3053/_assets/01-study-groups/skills-on.session.jsonl skill_opens= 1 total_tool_calls= 7
docs/issue-3053/_assets/02-onboarding-experiment/skills-on.session.jsonl skill_opens= 3 total_tool_calls= 12
docs/issue-3053/_assets/03-review-scheduler/skills-on.session.jsonl skill_opens= 1 total_tool_calls= 9
docs/issue-3053/_assets/04-pilot-trust/skills-on.session.jsonl skill_opens= 3 total_tool_calls= 6
TOTAL skill opens across skills-on: 8
TOTAL skill opens across skills-off: 0
```
derived: same `check.py`, run this session -- matches PR #3074's reported
"8 total ... vs 0 off" exactly. The pre-registered H2 decision rule
(untracked here, exists only on PR #3074's branch at
`docs/issue-3053/decisions/pre-registration.md`, commit `4c064708`, field
(d): wins>=3 of 4 AND margin>=3 -> better; symmetric -> worse; else
indistinguishable) applied to the re-derived 2 wins / 1 tie / 1 loss and
+1 margin yields **indistinguishable**, matching PR #3074's stated
verdict. **Verdict: Present.**

**Must-not clause -- held.** (a) H1 (mount) is verified and reported before
H2's null is interpreted, in both the pre-registration document's own gate
language and this record's ordering above -- the mount-not-shown-to-succeed
failure mode the issue names is not repeated. (b) The pre-registered
decision rule's field (d) states skill-open count is "diagnostic only ...
never itself the pass condition for H2" -- H2's indistinguishable call
above rests on the re-derived score margin (+1, below the +/-3 bar), not
on the open count (8 vs 0). (c) Task-text grounding, checked by diffing PR
#3074's final tasks against the original pre-retraction baseline commit
(`4822045d`, on `main`):
```
$ git diff 4822045d pr-3074-review -- scripts/issue-3041/tasks/ | grep "^diff --git\|^+We\|^+Read\|^+Check the repo"
diff --git a/scripts/issue-3041/tasks/01-study-groups.txt b/scripts/issue-3041/tasks/01-study-groups.txt
+We're thinking about adding a feature where students can be matched into small study groups by course and exam date. Before the team invests further: read what's already in docs/issue-1 ...
diff --git a/scripts/issue-3041/tasks/02-onboarding-experiment.txt b/scripts/issue-3041/tasks/02-onboarding-experiment.txt
+We're about to test a redesigned first-run onboarding flow that introduces new users to the comprehension-gap feature described in docs/issue-5's one-pager ...
diff --git a/scripts/issue-3041/tasks/03-review-scheduler.txt b/scripts/issue-3041/tasks/03-review-scheduler.txt
+We need a new spaced-repetition review scheduler ... Check the repo first: as of now it holds no application code, only the product-discovery documents under docs/issue-1 and docs/issue-5 ... treat it as a green-field design ...
diff --git a/scripts/issue-3041/tasks/04-paywall-ab-trust.txt b/scripts/issue-3041/tasks/04-paywall-ab-trust.txt
diff --git a/scripts/issue-3041/tasks/04-pilot-trust.txt b/scripts/issue-3041/tasks/04-pilot-trust.txt
```
derived: `git diff 4822045d pr-3074-review -- scripts/issue-3041/tasks/`,
run this session -- 3 of the 4 task files (`01-study-groups.txt`,
`02-onboarding-experiment.txt`, `04-paywall-ab-trust.txt` renamed to
`04-pilot-trust.txt`) were rewritten to require reading the now-real
`study-companion` content; the 4th (`03-review-scheduler.txt`) states
explicitly the repo holds no application code and instructs the model to
treat the task as green-field, the must-not clause's own named second
option. **Must-not clause: held.**

## Why

Applied `adversarial-review`'s blind-evaluator protocol to this
verification itself: every number above is re-derived this session
(`derived:` tags throughout "What was done") from PR #3074's own retained
assets, not quoted from the PR body or the PR's own record's tables.
Applied `experiment-trust`'s Step-1 scope gate against the pre-registration
document's own "Scope note" section (cited under "Open findings" below,
`canonical:` tag) to confirm this pre-assigned-condition, n=4 comparison
correctly routes away from SRM/A-A machinery rather than fabricating a
chi-square check that does not apply. Applied `hypothesis-testing`'s Step
4/6 gates against the `git log --oneline --reverse pr-3074-review
^4822045d` output (cited under "Open findings" below, `derived:` tag) to
confirm the registration commit precedes the run commit, and against the
re-derived scores under "What was done" above to confirm the
"indistinguishable" verdict follows the registered rule mechanically, not
a fresh post-hoc call. Applied `conformance-review-verdict-assignment` to
assign Present/Surface/Absent/Incorrect/Unverifiable per criterion from
the re-derived evidence above, re-checking the one candidate near-miss
(`--disable-slash-commands`, cited under "Open findings" below with its
own `derived:` re-check) before finalizing it as non-blocking rather than
asserting a verdict on a single pass (rule 6).

## Upstream basis

- PR #3074, all 8 commits, head `2272ffa4` -- the subject of this
  verification; not merged to `main`; fetched via `git fetch origin
  pull/3074/head:pr-3074-review`, read-only, no edits. derived: `git
  rev-parse pr-3074-review` -> `2272ffa44dd1ef66add01ebf7f56585ad68973cc`,
  run this session.
- `docs/issue-3053/decisions/pre-registration.md` -- untracked here,
  exists only on PR #3074's branch, commit `4c064708` -- the registration
  this record checked for pre-run timing and applied the H2 decision rule
  from.
- `docs/issue-3053/_assets/{01-study-groups,02-onboarding-experiment,
  03-review-scheduler,04-pilot-trust}/` -- untracked here, exists only on
  PR #3074's branch, commit `3ecf7c80` -- the session logs, deliverables,
  and verdict.json files every figure in this record was re-derived from.
- `scripts/issue-3041/run_pair.sh`, `evaluate_pair.py` -- on PR #3074's
  branch, commit `3ecf7c80` -- the harness code checked for the
  skills-on/off invocation asymmetry and the blind-evaluator's actual
  input surface.
- The external `study-companion` repository (not a path inside this
  repository) at commit `d6f14aebd1a79002fda3a7f22320ee63c6e7a736` --
  cloned independently this session to confirm target-repo content, not
  taken from PR #3074's own citation of it. derived: `git ls-tree -r
  --name-only HEAD` output cited under "What was done" (criterion 3)
  above, run this session against that clone.
- issue #3053 and its 4 comments (retraction, re-anchor, consumer-path
  amendment, session-end watch) -- read via `gh issue view 3053
  --comments` this session.

## What did not work

None -- every figure PR #3074 reported re-derived to the same value from
its own retained assets (see the `derived:` citations under "What was
done" above); no acceptance criterion failed. The blind-scoring content
leak and the `--disable-slash-commands` asymmetry named under "Open
findings" were found during this verification, not something this session
attempted and failed at.

## Open findings

- **Blind-scoring content leak, not in PR #3074's own record.**
  `scripts/issue-3041/evaluate_pair.py` (on PR #3074's branch, commit
  `3ecf7c80`) gives the evaluator only pasted document text:
  ```
  $ git show pr-3074-review:scripts/issue-3041/evaluate_pair.py | sed -n '46,54p'
  docs = [("skills-on", text_on), ("skills-off", text_off)]
  random.shuffle(docs)
  (label_1, doc1_text), (label_2, doc2_text) = docs
  ```
  (`--tools ""`, no filesystem access, elsewhere in the same file) --
  confirmed by reading the script this session, so arm-named directory
  paths never reach the evaluator and the storage layout itself does not
  break blinding. But grepping every skills-on deliverable (extracted from
  PR #3074's branch, untracked here) for skill-slug citations:
  ```
  $ grep -in -E "hypothesis-testing|experiment-trust|product-discovery-" docs/issue-3053/_assets/*/skills-on/DELIVERABLE.md
  01-study-groups/skills-on/DELIVERABLE.md:3:...(per `hypothesis-testing`)
  02-onboarding-experiment/skills-on/DELIVERABLE.md:3:Pre-registered per `product-discovery-hypothesis-preregistration`: ...
  04-pilot-trust/skills-on/DELIVERABLE.md:32:...pre-registration territory (hypothesis-testing, product-discovery-hypothesis-preregistration
  04-pilot-trust/skills-on/DELIVERABLE.md:35:...(experiment-trust) don't apply; ...
  $ grep -in -E "hypothesis-testing|experiment-trust|product-discovery-" docs/issue-3053/_assets/*/skills-off/DELIVERABLE.md
  (no matches)
  ```
  derived: the two `grep` commands above, run this session -- 3 of 4
  skills-on deliverables (`01-study-groups`, `02-onboarding-experiment`,
  `04-pilot-trust`) cite skill slugs by name; 0 of 4 skills-off
  deliverables do. This is content the nominally-blind evaluator does see
  and could use to infer arm identity, independent of actual quality.
  Checked whether it explains the outcome against the per-pair scores
  re-derived under "What was done" (criterion 4) above: it does not
  correlate with winning -- pair 01 has the citation and lost (8 vs 9),
  pair 03 has no citation and won (9 vs 8) -- so it does not appear to have
  driven the +1 margin, but it is a genuine, unreported gap in the "blind
  scoring" claim. Resolution path: a future run should instruct the
  skills-on arm not to name the methodology it drew on inside the
  deliverable text itself, or the evaluator prompt should explicitly
  discount methodology name-dropping as a scoring signal.
- **`--disable-slash-commands` asymmetry, inherited unchanged from the
  original PR #3052 harness, not introduced by PR #3074.** Cited under
  "What was done" (criterion 2) above (`run_pair.sh` line 105, skills-off
  invocation only). Re-checked before finalizing as non-blocking
  (conformance-review-verdict-assignment rule 6): no `/`-prefixed
  slash-command invocation appears in any of the 8 retained transcripts --
  ```
  $ grep -c '"/' docs/issue-3053/_assets/*/skills-*.session.jsonl | grep -v ':0$'
  (no output -- 0 in every file)
  ```
  derived: the `grep -c` command above, run this session against all 8
  session logs -- 0 matches in every file, so the flag has no observed
  behavioral surface in this run's own transcripts. Judged non-substantive
  for this run, but criterion 2's "differ ... only in that way" is not
  literally true of the full CLI invocation (only of the tool-use surface
  the model actually exercised). Resolution path: a future harness
  revision should add `--disable-slash-commands` to both arms or drop it
  from both.
- **Pre-registration threshold provenance.**
  ```
  $ git log --oneline --reverse pr-3074-review ^4822045d | head -6
  4c064708 issue-3053: fix harness mount + re-pin + ground task texts, pre-register decision rule
  275c08a0 issue-3053: document the --setting-sources/--plugin-dir trap in operations.md
  9ca012cc issue-3053: fix relative-output-root path bug in run_pair.sh
  7667f279 issue-3053: strip CLAUDE_*/MUSTER_* env vars from the child claude -p process
  0e2141b5 issue-3053: document the child-session env-var-leak trap in operations.md
  3ecf7c80 issue-3053: run the corrected paired skills-on/skills-off comparison for real
  ```
  derived: `git log --oneline --reverse pr-3074-review ^4822045d`, run
  this session -- the registration commit (`4c064708`) precedes the run
  commit (`3ecf7c80`) in the same branch's history, and the
  pre-registration document's own text states "No pair has been run under
  this registration at the time this file is written." This holds
  strictly for this run's own data. But canonical: `gh issue view 3053`
  (read this session, see "What was done" above) already quotes the
  retracted baseline's margin ("34 to 33") in its body, visible to the
  same author before this registration was written -- so the +/-3 bar was
  not chosen in genuine ignorance of what small-n margins on this
  rubric/evaluator tend to look like, even though it was written down
  before this run's own data per `hypothesis-testing` Step 4's literal
  gate. Not a rule violation; named so a future reader does not read
  "+/-3" as chosen from a vacuum.
- **n=4 statistical power.** canonical:
  `docs/issue-3053/decisions/pre-registration.md` field (d) (untracked
  here, exists only on PR #3074's branch, commit `4c064708`, read this
  session) itself states the design is "too small for a significance test
  -- this is a directional read, not a statistical one." This is
  accurate: a 4-pair, 1-10-integer-score design cannot resolve a real
  effect much smaller than the registered +/-3 bar from noise. What the
  re-derived +1 margin (cited under "What was done", criterion 4, above)
  establishes is that this run cannot resolve an effect of that size, not
  that no effect exists. No action needed -- already disclosed accurately
  in the pre-registration document.
- none other beyond the four items above.

## Next steps

loop_state is terminal (`landed`): all 4 acceptance criteria independently
re-derived Present (each with its own `derived:` citation under "What was
done" above), must-not clause held, and the open findings above are named
with resolution paths rather than started here -- per this task's scope
(verify, do not edit the PR, do not merge). No further action from this
session.

skill-verdict: experiment-trust — applied: invoked; used Step 1's scope
gate against the pre-registration document's own "Scope note" section
(canonical: `docs/issue-3053/decisions/pre-registration.md`, untracked
here, PR #3074 branch commit `4c064708`, read this session) to confirm
this pre-assigned-condition, n=4 comparison correctly routes away from
SRM/A-A machinery rather than fabricating a chi-square check that does not
apply.
skill-verdict: hypothesis-testing — applied: invoked; used Step 4/6 gates
against the `git log --oneline --reverse pr-3074-review ^4822045d` output
(derived: cited under "Open findings" above) to verify the pre-registration
commit precedes the run commit, and against the re-derived scores under
"What was done" (criterion 4) above to confirm the "indistinguishable"
verdict follows the registered rule mechanically.
skill-verdict: adversarial-review — applied: invoked; worked only from PR
#3074's own retained assets and harness code (every figure under "What was
done" carries its own `derived:` re-run this session, not a quote of the
PR's tables), and found one unreported defect (the blind-evaluator content
leak, derived: the two `grep` commands cited under "Open findings" above)
that PR #3074's own record did not surface.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
assigned Present to all 4 written acceptance criteria from the re-derived
evidence under "What was done" above, re-checked the
`--disable-slash-commands` near-miss against the actual transcripts
(derived: the `grep -c '"/'` re-run cited under "Open findings" above)
before finalizing it as non-blocking rather than asserting a verdict on a
single pass (rule 6), and named the specific clause each open finding
bears on rather than a bare label (rule 5).
