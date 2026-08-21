---
subject: issue-1937
role: implementation
kind: record
code_under_review:
  - skill-repository/skills/performance-engineering-operational-playbook/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: commit-unreachable
type: guidance-only
breaking: false
verdict: pass
---

# Phase-2 record: procedural body for performance-engineering-operational-playbook

## What was done

Authored `## Trigger` / `## Procedure` / `## Output shape` for the single
skill `performance-engineering-operational-playbook` in
`tokenmaxxxer/skill-repository`, per the approved proposal
(docs/issue-1937/proposals/procedural-body-performance-engineering-operational-playbook.md):

1. Inserted the three sections between the framing paragraph and
   `## Layer A`, one Procedure step per research layer/axis (practitioner
   rules 1–7, named methodologies 8–9, academic grounding 10), each
   citing its rule numbers, mirroring `content-design-operational-playbook`'s
   shape.
2. Rewrote `description:` to a single sentence derived from the
   authored Trigger's opening clause, keeping "use when" ("Use when
   diagnosing an unexplained slowdown ...").
3. Appended `performance-engineering-operational-playbook` to
   `scripts/procedure_authored_skills.txt`.
4. Ran the four checks live from `/tmp/skill-repository` (branch
   `issue-1937-perf-eng-procedural-body`, base commit `615d169`, new
   commit `04239b7`) — outputs below.
5. Committed locally (`04239b7`); `git push` failed with a network error
   in this sandboxed session — see Open findings.

## Why

why: the frozen wave recipe from #1790 (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) applies verbatim to this family, and the survey
canonical: docs/issue-1937/reports/implementation/survey.md (Body shape,
Skip-condition check sections) confirmed this skill is a live-edit case
(no existing Trigger/Procedure/Output-shape headings, not yet in the
manifest, 10 pre-existing rule lines).

## Upstream

upstream: docs/issue-1937/proposals/procedural-body-performance-engineering-operational-playbook.md
(approved via `APPROVE issue-1937/implementation` on the issue), itself
based on docs/issue-1790/reports/implementation.md (WAVE RECIPE) and
docs/issue-1937/reports/implementation/survey.md.

## The four live checks (executed live from `/tmp/skill-repository`, commit `04239b7`)

canonical: executed live in /tmp/skill-repository at commit 04239b7 (branch issue-1937-perf-eng-procedural-body, base 615d169)

### Check 1 — manifest checker

canonical: acceptance: `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt` — result: pass

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
exit: 0
```

### Check 2 — rule-retention sweep

canonical: acceptance: `grep -nE "^[0-9]+\." skills/performance-engineering-operational-playbook/SKILL.md` reproduces every pre-change `**Condition:**` line from the survey baseline (docs/issue-1937/reports/implementation/survey.md, Rule-retention baseline section) — result: pass

```
$ grep -nE "^[0-9]+\." skills/performance-engineering-operational-playbook/SKILL.md
29:1. Practitioner decision rules (rules 1–7): check Utilization,
37:2. Named methodologies verified at source (rules 8–9): apply the USE
41:3. Academic/theoretical grounding (rule 10): ground any wait-time or
54:1. **Condition:** a service is "slow" with no prior hypothesis.
61:2. **Condition:** reporting or alerting on request latency.
68:3. **Condition:** deciding how strict an SLO/error budget should be.
76:4. **Condition:** a queue/pool/worker pool is running "hot" (util near
84:5. **[REMOVAL] Condition:** an ORM-driven code path issues one query per
95:6. **[REMOVAL] Condition:** a connection pool is periodically exhausted
104:7. **Condition:** choosing a fix among several that close the same
117:8. **Condition:** starting any performance investigation with no
125:9. **Condition:** defining what "reliable enough" means for a service
135:10. **Condition:** justifying why a wait-time or capacity claim is valid
```

derived: the fence above's `**Condition:**` lines match the survey's
pre-change baseline fence 1-for-1; the other lines in the fence are this
change's new `## Procedure` step numbers, not pre-existing rules. The
`git diff` fence in Check 3 below shows the only line removed from this
file is the old `description:` line, so every rule line's text is
unchanged.

### Check 3 — `git diff --stat`

canonical: acceptance: `git diff --stat` scoped to only the skill's `SKILL.md` and the manifest file — result: pass

```
$ git diff --stat
 scripts/procedure_authored_skills.txt                              |  1 +
 skills/performance-engineering-operational-playbook/SKILL.md        | 39 +++++++++++++++++++++-
 2 files changed, 39 insertions(+), 1 deletion(-)
```

### Check 4 — full-tree checker

canonical: acceptance: `python3 scripts/check_skill_conformance.py` (no `--manifest` flag) — result: pass

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
exit: 0
```

## What did not work

None.

## Open findings

canonical: acceptance: `git push -u origin issue-1937-perf-eng-procedural-body` executed live in /tmp/skill-repository, this turn — result: fail (network)

The skill-repository commit `04239b7` (branch
`issue-1937-perf-eng-procedural-body`, based on local `main` at
`615d169`) could not be pushed and no skill-repository PR could be
opened in this session. `git push` exited non-zero with an SSH/network
error, not a content or conformance issue.

canonical: acceptance: the four checks above all executed live with a pasted `exit: 0` / passing fence in this same record — result: pass

canonical: acceptance: `git fetch origin main` executed live in /tmp/skill-repository, this turn — result: fail (network)

unverifiable: whether local `main` (`615d169`) is still
skill-repository's current `main` at push time — reason: the fetch
above also exited non-zero with the same network error.

next steps: push branch `issue-1937-perf-eng-procedural-body` (commit
`04239b7`) to `tokenmaxxxer/skill-repository` once network access is
available, rebase onto current main if it has moved, open the PR
referencing `tokenmaxxxer/on-the-record#1937` with `Closes #1937`, and
link the PR URL back into this record.

resolution path: retry the push/PR from a session with working network
access to github.com over SSH; if `main` has moved, `git fetch && git
rebase origin/main` on this branch before pushing (the change is
file-scoped and low-collision-risk per the family-bounded write set).
</content>
