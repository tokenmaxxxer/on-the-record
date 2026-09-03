---
issue: 3245
type: drafted-followup
status: not-filed
---

# issue-3245 — drafted follow-up issues (pairs 3-5), not filed by this session

`gh-guard` (`runs/rulebooks/tokenmaxxxer-core/core/hooks/gh-guard.sh`)
refuses `gh issue create` for every role session (`CLAUDE_SKILL` set).
This session cannot file these on `JiwonJung94/study-companion` itself —
the sanctioned shape (`gates/forbidden_action_rule.py`) is to draft the
body here and name the orchestrator/human as the filer. Six issues (two
per pair, identical body except the arm label, same shape as issues
19-22) are needed to reach the registered n>=5 floor (pairs 1-2 already
provisioned as issues 19-22).

Task/rubric source files: `scripts/issue-3041/tasks/04-pilot-trust.txt`
(pair 3, already existed before this issue), `05-notification-cadence.txt`
and `06-peer-review-swap.txt` (pairs 4-5, drafted this session, same
shape as `01-study-groups.txt`/`02-onboarding-experiment.txt`: a
feature idea, a pointer to docs/issue-1 + docs/issue-5, a request for a
worth-building-next brief with a stop/pivot condition).

Each issue's body should end with the same measurement footer and
Acceptance block as issues 19-22 (`gh issue view 19/20`), with the arm
label and pair id substituted:

```
measurement: issue #3245 consumer-path pair `<pair-id>`, arm `<skills-on|skills-off>`. Body text is identical across the two arms of this pair except this label.

## Acceptance

- check: `bash -c "test -n \"$(ls docs/issue-*/specs/*.md docs/issue-*/reports/*.md 2>/dev/null | head -1)\""`
- must-not: do not read or reference the other arm of this pair.
```

## Pair 3 — `04-pilot-trust` (task file already existed; issues not yet filed)

Title (skills-on): `measurement 04-pilot-trust [skills-on]: Read the one-pager under docs/issue-5, in particular the section near the ...`
Title (skills-off): same with `[skills-off]`.

Body (shared, both arms):
> Read the one-pager under docs/issue-5, in particular the section near the end that proposes a small pilot to check whether the comprehension-gap feature actually works before we build more on top of it: roughly 15-20 students, comparing what they predict they'll score against what they actually score, over a fixed number of weeks, with a stated rule for when we'd stop. The team wants to run this pilot as written and treat its outcome as the answer. Before that happens: would this pilot's design actually let a bad result stop us, or is it built in a way that leans toward "proceed" regardless of what happens? Write up what you'd check and what you'd tell the team.

## Pair 4 — `05-notification-cadence` (task drafted this session)

Title (skills-on): `measurement 05-notification-cadence [skills-on]: We're thinking about adding a feature where the app sends students a daily ...`
Title (skills-off): same with `[skills-off]`.

Body (shared, both arms): contents of `scripts/issue-3041/tasks/05-notification-cadence.txt` verbatim.

## Pair 5 — `06-peer-review-swap` (task drafted this session)

Title (skills-on): `measurement 06-peer-review-swap [skills-on]: We're thinking about adding a feature where two students working on the ...`
Title (skills-off): same with `[skills-off]`.

Body (shared, both arms): contents of `scripts/issue-3041/tasks/06-peer-review-swap.txt` verbatim.

## Comparability note

Pairs 4-5 mirror issues 19/21's exact shape (feature idea -> read
docs/issue-1 + docs/issue-5 -> worth-building-next brief with a named
stop/pivot condition) and reuse issues 19/21's own rubric structure
verbatim (`scripts/issue-3041/rubrics/01-study-groups.md`'s five bullets),
so difficulty and scoring criteria are held constant, only the feature
premise changes. Pair 3 (`04-pilot-trust`) is shaped differently (a
pre-registration-adequacy critique of an already-written pilot design,
not a fresh worth-building-next brief) because it is the fourth task this
issue's own prior batch (`scripts/issue-3041`) already scaffolded with a
task file and rubric before this issue existed — reusing it costs no new
drafting and keeps the skill fit tight (`product-discovery-hypothesis-
preregistration` is a closer match to "audit whether this pilot's
stopping rule is falsifiable" than to a fresh green-field brief), at the
cost of pair 3 being one notch less shape-identical to 19-22 than pairs
4-5 are.

## Once filed

Whoever files these six issues should hand the resulting `(pair_id,
on_issue, off_issue)` triples to a future session running
`scripts/consumer-path/run_pair.py --pair-id <id> --repo <clone> --skill
product-discovery-hypothesis-preregistration --on-issue <n> --off-issue
<n> --out-dir docs/issue-3245/_assets/<id> --execute
--i-understand-this-spawns-real-sessions`, one pair at a time, committing
`docs/issue-3245/_assets/<id>/{manifest,transport,result}.json` after
each pair completes so a later `verify_manipulation.py --report` run
sees it.
