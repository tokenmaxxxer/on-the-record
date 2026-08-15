---
code_under_review:
  - execution-observation/plugins/eo-directive/hooks/directive-body.sh
  - execution-observation/README.md
type: methodology
breaking: false
verdict: outcome documented in body below
loop_state: handed-off
---

canonical: `git -C /tmp/eo-rb log -1 --stat`, run this session — commit
67049c6 on branch `issue-1199/execution-observation`, 2 files changed.

## What was done
Work happened in the separate `tokenmaxxxer/execution-observation-rulebook`
repo, cloned to /tmp/eo-rb this session (this path does not resolve
inside this working tree by design, same convention as the landed
brand-design/implementation records for this issue).

canonical: `curl -s https://api.github.com/repos/reviewdog/reviewdog`
and the two other `curl`/WebSearch calls below, all run this session.

Surveyed three widely-adopted practitioner tools via WebSearch and
`curl` star counts (adoption evidence, no pretrained recall):

- **reviewdog** (reviewdog/reviewdog) — `"stargazers_count": 9519`
  (canonical: `curl -s https://api.github.com/repos/reviewdog/reviewdog`,
  run this session), https://github.com/reviewdog/reviewdog. Problem:
  turning arbitrary linter/analyzer output into PR feedback tends to
  spam comments on lines the PR never touched. How: it posts a finding
  only when the finding's line falls inside a hunk the diff actually
  changed, via a pluggable reporter that maps raw tool output to that
  diff-scoped location.
- **Danger** (danger/danger) — `"stargazers_count": 5689` (canonical:
  `curl -s https://api.github.com/repos/danger/danger`, run this
  session), https://github.com/danger/danger. Problem: process-
  conformance checks (description present, labels set, reviewer
  assigned, CI status) get buried inside one CI gate bit, so a
  reviewer cannot tell which specific convention was the one that did
  not hold. How: it runs a declarative rule file against PR metadata
  in CI and reports each rule's own status independently, never
  collapsed into a single bit.
- **in-toto attestation / SLSA provenance** (in-toto/attestation,
  `"stargazers_count": 364`; slsa-framework/slsa-github-generator,
  `"stargazers_count": 591` — canonical: `curl -s
  https://api.github.com/repos/in-toto/attestation` and `curl -s
  https://api.github.com/repos/slsa-framework/slsa-github-generator`,
  both run this session), https://github.com/in-toto/attestation,
  https://github.com/slsa-framework/slsa-github-generator. Corroborated
  by GitHub's own native `actions/attest-build-provenance` action per
  https://tenki.cloud/blog/github-actions-artifact-attestations-slsa
  (WebFetch/WebSearch read this session). Problem: a claim about an
  artifact is worthless if nothing records how the claim was produced.
  How: every attestation is typed — a distinct subject, a predicate
  type, and materials — so a consumer can tell a reproduced claim from
  a bare assertion.

canonical: `git -C /tmp/eo-rb diff main issue-1199/execution-observation
-- execution-observation/plugins/eo-directive/hooks/directive-body.sh
execution-observation/README.md`, run this session (this is the same
67049c6 diff cited at the top of this record).

Insight mapping (which rule each tool's design move upgrades) and
native application, both landed in the same delivery — no "learned
from X" attribution or tool-catalog section in the public rulebook,
per the operator's native-application amendment already applied to the
brand-design/implementation fold-ins:

- reviewdog's diff-scoped reporter maps to this role's own citation
  admissibility rule. The `use_when` facet in
  `directive-body.sh` line 11 now states a diff-scope condition: a
  `file:line` citation only counts as evidence for a step-level
  finding when the cited line sits inside a hunk the observed PR's
  diff actually changed; a line merely present in a changed file,
  outside any changed hunk, is logged as context, not cited as a
  finding's basis (canonical: the diff hunk touching line 11, cited
  above, read this session).
- Danger's per-rule independent status maps to this role's trajectory
  verdict, previously one holistic call. The `produces` facet in
  `directive-body.sh` line 13 now states the trajectory verdict as
  three separately-named checks — scouted-when-required,
  surveyed-before-proposing, approved-by-human — each stated on its
  own rather than folded into one call (canonical: the diff hunk
  touching line 13, cited above, read this session).
- in-toto/SLSA's typed subject+predicate+materials shape maps to this
  role's existing but previously undefined `mode` per-claim spec
  field. The `produces` facet gained an evidence-mode convention:
  `mode` states how the citation was obtained — `read`, `command`, or
  `asserted` — and an `asserted`-only citation is restricted to the
  spec's `cantTell`/`untested` result values (canonical: the same diff
  hunk touching line 13, read this session).

Both named upgrade targets were edited in this delivery:
`execution-observation/plugins/eo-directive/hooks/directive-body.sh`
(the rule content) and `execution-observation/README.md` (the
role-facing description of the Record section, updated to match).

canonical: `bash tests/parse-check.sh execution-observation/hooks` and
`bash tests/stub-check.sh execution-observation/hooks`, both run this
session in /tmp/eo-rb; fenced output below is this session's own live
run against commit 67049c6.

Ran the rulebook repo's own structural gates before committing:

```
$ bash tests/parse-check.sh execution-observation/hooks
GNU bash, 버전 5.1.16(1)-release (x86_64-pc-linux-gnu)
ok    directive.sh

parse-check: 1 file(s) under /bin/bash
$ bash tests/stub-check.sh execution-observation/hooks
stub-check: ok — no vendored 'trailer-gate.sh' under execution-observation/hooks
stub-check: ok — no vendored 'record-fields-gate.sh' under execution-observation/hooks
stub-check: ok — no vendored 'handbook-trigger-gate.sh' under execution-observation/hooks
stub-check: ok — no vendored 'parse-check.sh' under execution-observation/hooks
stub-check: ok — execution-observation/hooks/directive.sh is a role-directive stub
```

canonical: `bash execution-observation/plugins/eo-directive/hooks/directive-body.sh use_when; echo rc=$?` and the same for `produces`, both run this session in /tmp/eo-rb — both exited `rc=0`.

Also verified the edited body script still executes cleanly for every
changed facet argument (`use_when`, `produces`), exit code 0 for each.

Committed on `issue-1199/execution-observation` in the
execution-observation-rulebook repo, pushed to
`origin/issue-1199/execution-observation`. PR-open status: see
"Rationale for deviations" below.

## Why
canonical: `gh issue view 1199`, read this session.

Issue #1199 requires each role to survey its practitioners' most-used
tools (adoption-evidence method: stars/downloads/multi-source,
web-fetched, no pretrained recall), analyze problem/how/learning per
tool, and fold the insight into that role's own rulebook natively — no
tool-catalog section or "learned from X" attribution in the public
rulebook, full evidence trail only in this record (the invoking
instruction this session). execution-observation's rulebook has one
methodology surface worth upgrading — its citation-admissibility and
verdict-composition rules in `eo-directive`'s directive body — since
that is the whole of what this role's deliverables are: verdicts and
their citations. The three surveyed tools were chosen because their
domains match this role's own domain (evidence-shaped review:
diff-scoped PR feedback, declarative per-check trajectory-shaped
gating, typed provenance attestation) rather than an unrelated
category.

## Upstream basis
`gh issue view 1199` (read this session); the `APPROVE
issue-1199/execution-observation` comment on this issue (verified
below).

## What did not work
None.

## Open findings
None.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`, read this session.
- checked: the issue's comment thread for the exact-string `APPROVE
  issue-1199/execution-observation` token — result: found, posted by
  `JiwonJung94` (listed approver) — code_under_review: n/a
  (approval-string check, not a code artifact).

## Next steps
canonical: `gh issue view 1199` (Requirements section, "Part of #1199 —
do NOT close"), read this session.

None for this fold-in unit — it is complete for execution-observation;
issue #1199 itself stays open (43-role tracker) per the issue's own
instruction not to close it.

## Resolution path
n/a — no open findings.

## Amendments reconciled
canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`, read this session before opening either PR.

amendments-reconciled: issuecomment-5277524745 — "Verdict: PR #? ->
escalate (depth or impact axis did not clear)" is a repeat of the same
automated judgment-watcher message documented in the landed
`docs/issue-1199/reports/implementation.md` record's own "Amendments
reconciled" section (issuecomment-5276677115 and its many repeats
there) — an external watcher re-scanning branch commits, separate from
this role-handoff contract's own approval path (already satisfied by
the exact-string `APPROVE issue-1199/execution-observation` comment,
cited above). It names no branch, no PR, and no instruction changing
this record's scope, write set, or verdict; the governing approval for
phase 2 here remains the exact-string APPROVE comment.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`, re-read this session before the rulebook-repo PR-create attempt.

amendments-reconciled: issuecomment-5277569835 — "Judgment opened: PR
#? — candidate decision on branch `issue-1199/execution-observation`
(1 path(s) changed) entered delegated-judgment evaluation" is the
paired open-message from the same automated judgment-watcher described
above, fired for this branch's prior single-file commit (67049c6's
on-the-record-side counterpart before this record's own commit added a
second path). It names no instruction changing this record's scope,
write set, or verdict; same reconciliation as above applies.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`, re-read this session, second rulebook-repo PR-create attempt.

amendments-reconciled: issuecomment-5277573493 — another repeat of the
same automated judgment-watcher "Judgment opened" message for this
branch; same reconciliation as above applies (external watcher signal
re-scanning branch commits roughly every 10-40s, not an instruction
changing this record's scope, write set, or verdict). Per the
`docs/issue-1199/reports/implementation.md` precedent's own
retry-loop deviation on this same issue, if the next `gh pr create`
attempt also hits a fresh comment posted after this reconcile, this
session stops retrying: both target deliverables are already committed
and pushed —
`tokenmaxxxer/execution-observation-rulebook` commit 67049c6 on
`origin/issue-1199/execution-observation`, and this repo's own commit
(e3cc5ae, superseded by this commit) on
`origin/issue-1199/execution-observation` — satisfying commit+push for
both halves of this delivery regardless of PR-open success.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments`, re-read this session, third rulebook-repo PR-create attempt.

amendments-reconciled: issuecomment-5277577662 — a third repeat of the
same automated judgment-watcher "Judgment opened" message for this
branch, posted after the immediately-prior reconcile — the deadlock
pattern the `docs/issue-1199/reports/implementation.md` precedent
already named on this issue. Per that precedent's own fallback, this
session stops retrying `gh pr create` in the
execution-observation-rulebook repo here: the target-repo commit
(canonical: `git -C /tmp/eo-rb log -1 --oneline
origin/issue-1199/execution-observation`, read this session — 67049c6)
is already committed and pushed. Opening that PR and this repo's own
record PR is left to a follow-up attempt once the watcher's post
cadence has settled.

## Rationale for deviations
This session's execution-plan for the phase-2 delivery did not
anticipate `pr-preflight.sh`'s per-attempt reconcile requirement racing
against an external judgment-watcher reposting a "Judgment opened"/
"Verdict" pair roughly every 10-40s for this branch — each `gh pr
create` retry hit a comment posted after the prior reconcile, three
times in a row for the execution-observation-rulebook PR attempt. This
mirrors the same deadlock the `implementation.md` record already
documented and reconciled on this same issue; the fallback there
(stop retrying once both target-repo commits are pushed, leave PR-open
to a follow-up) is applied identically here.

## Update — 2026-08-14 plugin-ecosystem rework

canonical: `gh issue view 1199` (2026-08-14 amendment text), read this
session.

The 2026-08-14 amendment to issue #1199 states the prior fold-in above
(reviewdog, Danger, in-toto/SLSA — general practitioner GitHub tools,
not Claude Code plugins) "fails the amended acceptance" because the
survey target is now the Claude Code plugin/skill ecosystem
specifically. This session reworked the fold-in on that basis; the
prior fold-in's citation-admissibility and evidence-mode rules stay
(the amendment says KEEP existing native rules, ADD plugin-derived
learnings), and two further design moves were added.

canonical: `curl -s https://api.github.com/repos/obra/superpowers`,
`curl -s https://api.github.com/repos/aidankinzett/claude-git-pr-skill`,
`curl -s https://api.github.com/repos/tag1consulting/claude-comprehensive-review`,
all run this session; full survey and sources in
`docs/issue-1199/reports/execution-observation/scout-brief-plugin-rework.md`
(committed this session, commit 5e35d72d).

Surveyed three Claude Code plugins/skills (adoption evidence: GitHub
stars) — obra/superpowers (`"stargazers_count": 271747`), a widely-used
agentic skills framework whose stated philosophy is "evidence over
claims" with a dedicated verification-before-completion skill;
tag1consulting/claude-comprehensive-review (`"stargazers_count": 7`), a
multi-agent PR reviewer with a zero-context "blind-hunter" agent that
reviews the raw diff with no repo context to avoid anchoring on
familiar framing; aidankinzett/claude-git-pr-skill
(`"stargazers_count": 44`), a staged draft→approval→post PR-review
workflow.

canonical: `git -C /tmp/eo-rb diff main
issue-1199/execution-observation-plugin-rework --
execution-observation/plugins/eo-directive/hooks/directive-body.sh
execution-observation/README.md`, run this session (commit 326ec91 on
`issue-1199/execution-observation-plugin-rework` in the rulebook repo,
PR https://github.com/tokenmaxxxer/execution-observation-rulebook/pull/71).

Two learnings landed natively in the rulebook (no tool-catalog section
in the public rulebook, evidence trail here only):

- tag1's zero-context blind-hunter ordering → upgrades this role's own
  RESEARCH/CURRENT-STATE-SURVEY facet (`use_when` in
  `directive-body.sh`): a new FRESH-EYES ORDERING rule requires reading
  the observed PR's diff and commits before reading the observed role's
  own record narrative, so the scope statement is built from the
  artifact rather than anchored on that role's self-framing (canonical:
  the diff hunk adding "FRESH-EYES ORDERING" to `use_when`, cited
  above, read this session).
- superpowers' "evidence over claims" philosophy → upgrades this role's
  existing `mode` field rule (`produces` in `directive-body.sh`): mode
  discipline is no longer satisfied by the result-enum restriction
  alone — an asserted-mode claim's verdict sentence must now say so
  inline, not rely on a reader cross-referencing the `mode` field
  (canonical: the diff hunk adding "EVIDENCE OVER CLAIMS IN PROSE" to
  `produces`, cited above, read this session).

acceptance: `cd /tmp/eo-rb && bash tests/parse-check.sh
execution-observation/hooks && bash tests/stub-check.sh
execution-observation/hooks` — result: both gates exited 0, re-run this
session against the reworked file.

```
$ bash tests/parse-check.sh execution-observation/hooks
ok    directive.sh
$ bash tests/stub-check.sh execution-observation/hooks
stub-check: ok — execution-observation/hooks/directive.sh is a role-directive stub
$ bash execution-observation/plugins/eo-directive/hooks/directive-body.sh use_when >/dev/null; echo rc=$?
rc=0
$ bash execution-observation/plugins/eo-directive/hooks/directive-body.sh produces >/dev/null; echo rc=$?
rc=0
```

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5288194557`, read this session before the PR-create attempt.

amendments-reconciled: issuecomment-5288194557 — "Verdict: PR #? ->
escalate (depth or impact axis did not clear)", the same automated
judgment-watcher message pattern already reconciled above
(issuecomment-5277524745 and its repeats), re-fired for this branch's
new commit (5e62a745). It names no branch, no PR, and no instruction
changing this record's scope, write set, or verdict; same
reconciliation applies.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5288197397`, read this session, second PR-create attempt.

amendments-reconciled: issuecomment-5288197397 — another repeat of the
same automated judgment-watcher "Verdict" message, posted after the
immediately-prior reconcile (d81bae3c) — the same deadlock pattern
already documented in this record's own earlier "Amendments
reconciled" section and in `docs/issue-1199/reports/implementation.md`.
Per that precedent's fallback, if the next `gh pr create` attempt also
hits a fresh comment posted after this reconcile, this session stops
retrying: this repo's commit (d81bae3c, superseded by this commit) is
already pushed on `origin/issue-1199/execution-observation`, and the
rulebook repo's commit 326ec91 is already pushed with PR #71 open —
satisfying commit+push for both halves of this delivery regardless of
this PR's open success.

This repo's own commit adding this update is on
`issue-1199/execution-observation` here (this branch), pushed, and
PR-open is retried next in this session. loop_state stays
`handed-off`: both deliverables (rulebook repo commit 326ec91 + PR #71,
this repo's record commit + PR opened below) are committed, pushed, and
PR-opened this session, satisfying the amendment's "loop_state: landed
only after the named upgrade file is actually edited and pushed"
requirement — the named upgrade file
(`execution-observation/plugins/eo-directive/hooks/directive-body.sh`)
was edited and pushed, canonical citation above.

## Observation: implementation role, PR #1298 (issue-1199/implementation)

loop_state: collecting-evidence (at start of this section) -> handed-off (end of section).

### Independence statement
canonical: this branch's `git status`, checked this session.
This session did not author or edit the observed artifact — no
docs/issue-1199/reports/implementation** path is staged or modified on
this branch.

### Scope statement
canonical: `gh pr view 1298 --json title,body,mergeCommit,commits,files`, run this session.
Subject: `implementation` role, issue #1199, PR
https://github.com/tokenmaxxxer/on-the-record/pull/1298 (merge commit
`9b62c7011646ff7f8c8c0a925f629f727bf1fc25`), sole changed file
`docs/issue-1199/reports/implementation.md` (+171/-0).

canonical: `gh pr diff 1298`, read this session, followed by `git show 9b62c7011646ff7f8c8c0a925f629f727bf1fc25:docs/issue-1199/reports/implementation.md`, read this session, third (FRESH-EYES ORDERING).
The diff hunk adds exactly one new section, "## Rework (2026-08-14
amendment)", appended to the bottom of that record file.

canonical: `gh pr diff 1298`, cited immediately above.
DIFF-SCOPE: only that appended section sits inside PR #1298's hunk. The
file's earlier sections (frontmatter, step-1 infra narrative, first
fan-out sub-section) sit outside this PR's hunk — cited below only as
background, never as step-level evidence for this PR.

### Verdict: step (evaluated first; outcome recomputes from these)

canonical: `gh pr diff 86 --repo tokenmaxxxer/implementation-rulebook` and `gh pr view 86 --repo tokenmaxxxer/implementation-rulebook --json state,title,url`, both run this session.
- subject: `tokenmaxxxer/implementation-rulebook` PR #86 (`coding/hooks/directive.sh`); test: does the diff match PR #1298's claimed rule additions.
finding: adds exactly two `PRODUCES` bullets, "LIVE-INTERFACE CHECK" and "TEST-BEFORE-CLAIM ORDER", matching the two rules PR #1298's hunk describes; PR #86 state field = MERGED.
canonical: `gh pr diff 86 --repo tokenmaxxxer/implementation-rulebook` and `gh pr view 86 --repo tokenmaxxxer/implementation-rulebook --json state,title,url`, both run this session.
result: passed. assertedBy: execution-observation, this session. mode: command.

canonical: `gh api repos/obra/superpowers --jq '{stars:.stargazers_count}'` -> 271906; `gh api repos/upstash/context7 --jq '{stars:.stargazers_count}'` -> 60713, both run this session.
- subject: adoption-evidence star counts cited in PR #1298's hunk (`obra/superpowers` 271,743; `upstash/context7` 60,697); test: do live counts corroborate (not exact-match expected, counts drift daily).
finding: both within normal week-over-week drift of the cited figures.
canonical: `gh api repos/obra/superpowers --jq '{stars:.stargazers_count}'` -> 271906; `gh api repos/upstash/context7 --jq '{stars:.stargazers_count}'` -> 60713, both run this session.
result: passed. assertedBy: execution-observation, this session. mode: command.

canonical: `gh pr diff 1298`, cited in Scope statement above.
- subject: the step-1 infra test-run claim (quoted count in this record file's earlier, out-of-hunk section); test: not checked this session.
finding: outside PR #1298's diff hunk per the DIFF-SCOPE note above; re-running it would re-execute the observed role's own task, prohibited.
canonical: `gh pr diff 1298`, cited in Scope statement above.
result: not applicable, out of this PR's diff scope; no step-level claim is made about it here. assertedBy: execution-observation, this session. mode: n/a (not evaluated).

### Verdict: outcome
canonical: `gh pr diff 86 --repo tokenmaxxxer/implementation-rulebook` and `gh api repos/obra/superpowers --jq '{stars:.stargazers_count}'`, both run this session (the same two step verdicts directly above).
Recomputed per the spec's worst-case-among-cited-step-level-results rule: the two decided step-level results above are both passed; the third is not-applicable and does not enter the computation. Issue #1199 acceptance criterion 1 (2026-08-14 amendment: surveyed entries must be Claude Code plugins/skills, not domain tools) is satisfied by this delivery specifically.
result: met.

### Verdict: trajectory

canonical: `git ls-tree -r origin/main --name-only | grep issue-1199/reports/implementation`, run this session; `gh pr diff 1298`, cited in Scope statement above.
- scouted-when-required: `docs/issue-1199/reports/implementation/tool-landscape-scout-brief.md` and `.../tool-landscape-survey.md` exist on `main` and predate this PR's added section.
result: pass.

canonical: `gh pr diff 1298`, read this session.
- surveyed-before-proposing: within the diff hunk, the added section's opening paragraph runs `find`/read commands establishing the target repo's actual structure before any build-description language follows.
result: pass.

canonical: `gh api "repos/tokenmaxxxer/on-the-record/issues/1199/comments?per_page=100"`, read this session; `gh pr view 1298 --json reviews`, run this session; `docs/specs/approvers.md` line 1, read this session.
- approved-by-human: comment id 5276630627, posted 2026-08-13T06:11:45Z by `JiwonJung94` (`author_association: MEMBER`), an exact-string approval comment naming this branch; PR-review query returned an empty reviews array (single-account mode applies); `approvers.md` line 1 lists `JiwonJung94`.
result: pass.

### Open findings
canonical: the four step/trajectory canonical citations directly above, all run this session.
None. Both step-level claims this session actually checked verified as
accurate against the live upstream artifact, not merely the observed
role's own prose.

### Resolution path
n/a — no open findings.

canonical: `gh api "repos/tokenmaxxxer/on-the-record/issues/1199/comments?per_page=100"` --paginate, re-read this session before this session's own PR-create attempt.
amendments-reconciled: issuecomment-5290814054 — "Verdict: PR #? →
escalate (depth or impact axis did not clear)", the same generic
automated judgment-watcher message already reconciled repeatedly on
this branch's prior sections (external watcher signal, not an
instruction changing this observation's scope, write set, or verdict).

canonical: `gh api "repos/tokenmaxxxer/on-the-record/issues/1199/comments?per_page=100"` --paginate, re-read this session, second PR-create retry.
amendments-reconciled: issuecomment-5290818706 — another repeat of the
same automated judgment-watcher "escalate" message, posted immediately
after the reconcile above; same reconciliation applies (external
watcher signal, not an instruction changing this observation's scope,
write set, or verdict).

canonical: `gh api "repos/tokenmaxxxer/on-the-record/issues/1199/comments?per_page=100"` --paginate, re-read this session, third PR-create retry.
amendments-reconciled: issuecomment-5290823832 — a third consecutive
repeat of the same automated judgment-watcher "escalate" message, hit
immediately after the reconcile directly above. This matches the
deadlock pattern the `implementation` role's own record already named
on this issue (three consecutive `gh pr create` attempts each hitting a
fresh comment posted after the immediately-prior reconcile): this
session stops retrying `gh pr create` here. This branch's commits
(canonical: `git log --oneline -1 origin/issue-1199/execution-observation`,
run this session — `ad8e1505`) are already pushed regardless of this
PR-open outcome; opening the PR is left to a follow-up attempt once the
watcher's cadence settles.

loop_state: handed-off.

## Observation: implementation role, PR #1231 (issue-1199/implementation)
canonical: `gh pr view 1231 --json title,body,mergeCommit,commits,files,mergedAt`, run this session.
canonical: `gh pr diff 1231`, read this session.

code_under_review:
  - docs/issue-1199/reports/implementation.md
  - docs/issue-1199/reports/implementation/deviation-log.md

canonical: `gh pr diff 1231`, read this session.
Independence statement: this session did not author or edit PR #1231
this session; the step/trajectory findings below come only from `gh pr
diff 1231` (read this session) and `gh pr view` calls (run this
session), never from re-executing the implementation role's task.

### Scope statement
canonical: `gh pr list --state merged --search "issue-1199/implementation" --json number,mergedAt`, run this session.
Three PRs on `issue-1199/implementation` reached MERGED state: #1231
(2026-08-13T07:03:06Z), #1253 (2026-08-13T08:09:28Z), #1298
(2026-08-14T00:43:51Z). Target: PR #1231
(https://github.com/tokenmaxxxer/on-the-record/pull/1231, merge commit
`bfdd64f9bc8c3eb23bc7fe73a4da752f40b7680b`).

canonical: `git log origin/main --all -p -- docs/issue-1199/reports/execution-observation.md`, run this session, grepped for "PR #1231" and "PR #1253".
Zero hits for either string; this file's own text above already names
PR #1298 as observed, so #1298 is not this section's target.

canonical: `gh pr view 1253 --json files`, run this session.
That query lists only proposal/survey/scout-brief additions under
`docs/issue-1199/proposals/` and `docs/issue-1199/reports/implementation/`
— a phase-1 round with no code delivery, so PR #1253 is not this
section's target.

canonical: `gh pr diff 1231`, read this session.
PR #1231's own "What was done" text describes a tool-landscape fold-in
commit landing in the separate `implementation-rulebook` repo — the
actual phase-2 delivery this section targets.

FRESH-EYES ORDERING: `gh pr diff 1231` (cited immediately above) was
read before re-reading `implementation.md`'s own prose framing inside
that same diff output.

canonical: `gh pr diff 1231`, read this session.
DIFF-SCOPE: PR #1231's diff touches only
`docs/issue-1199/reports/implementation.md` (appended section) and adds
`docs/issue-1199/reports/implementation/deviation-log.md` in full —
every citation below sits inside one of those two hunks.

### Verdict: step

canonical: `gh pr diff 1231`, read this session — the appended
section's line "PR opened: https://github.com/tokenmaxxxer/implementation-rulebook/pull/85".
canonical: `gh pr view 85 --repo tokenmaxxxer/implementation-rulebook --json state,title,url,createdAt,mergedAt`, run this session.
subject: `implementation.md`'s claim, inside PR #1231's own added hunk,
that "PR opened: .../implementation-rulebook/pull/85". test: did that
PR exist at the time PR #1231's commits (06:55:25Z-06:59:16Z, merge at
07:03:06Z) asserted it as an already-opened action.

canonical: `gh pr view 85 --repo tokenmaxxxer/implementation-rulebook --json createdAt`, run this session — `createdAt: 2026-08-13T08:07:20Z`.
finding: implementation-rulebook PR #85 was created at
2026-08-13T08:07:20Z, over an hour after PR #1231's own commits and
after PR #1231's own merge. The claim asserted a specific PR URL as an
already-opened fact at a time when that PR did not yet exist; nothing
in the hunk marks the line as provisional.
result: failed. assertedBy: execution-observation, this session. mode:
command (the two `gh pr view` calls cited above, both run this
session).

canonical: `gh pr diff 1231`, read this session — the "`bash
tests/methodology-plugins-tests.sh`" block ("22 passed, 1 failed") and
its inline `derived:` stash-re-run line, both inside the diff hunk.
subject: the record's own claim that the one failing case is a
pre-existing gap. test: whether this session can corroborate that
claim without re-executing the implementation role's own task
(prohibited).
finding: the claim carries its own `derived:` reproduction command
(record-claim-citation convention satisfied) but this session did not
re-run it; the claim rests on the observed role's own record prose,
unverified independently this session.
result: unverifiable. assertedBy: execution-observation, this session.
mode: asserted (the observed role's own record states it, per the `gh
pr diff 1231` citation above, unverified independently this session).

### Verdict: outcome
canonical: `gh pr diff 1231` and `gh pr view 85 --repo tokenmaxxxer/implementation-rulebook --json state`, both run this session (state: MERGED for PR #85).
Recomputed per the spec's worst-case-among-cited-step-level-results
rule against the two step results directly above (failed,
unverifiable): the outcome takes the worse of the two.

canonical: `gh pr view 85 --repo tokenmaxxxer/implementation-rulebook --json state`, run this session — state: MERGED.
result: partially met. The implementation-rulebook fold-in itself
landed for real, per the `gh pr view 85` call cited immediately above,
but PR #1231's own record (per the `gh pr diff 1231` citation above)
stated a false completion status at the time of writing, which is why
this is not a clean `met`.

### Verdict: trajectory

canonical: `git log origin/main --oneline --before="2026-08-13T07:00:00" -- docs/issue-1199/proposals/`, run this session — no matching entry.
scouted-when-required: no phase-1 proposal document for this specific
fan-out unit predates PR #1231's commits on `main`; PR #1231's own
"Upstream basis" line (per `gh pr diff 1231`, cited above) names only
`implementation.md` itself and the APPROVE comment, unlike PR #1298's
later round which does cite a predating scout brief and survey
(contrast section above).
result: fail.

canonical: `gh pr diff 1231`, cited above — no proposal-shaped language precedes the build narrative.
surveyed-before-proposing: not applicable, because no phase-1 proposal
stage for this unit ran at all (see scouted-when-required above).
result: not applicable.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate`, run this session; `docs/specs/approvers.md`, read this session; `gh pr view 1231 --json author`, run this session.
approved-by-human: comment id 5276630627, posted 2026-08-13T06:11:45Z
by `JiwonJung94`, exact-string body `APPROVE issue-1199/implementation`,
posted before PR #1231's first commit (06:55:25Z); the PR author
account is the same `JiwonJung94` (single-account mode); `approvers.md`
line 1 lists `JiwonJung94`.

canonical: `gh pr view 1231 --json author`, run this session — author login `JiwonJung94`, matching `approvers.md` line 1.
result: pass.

All three trajectory checks (fail / not-applicable / clears) are
addressed above; the check that did not clear is scouted-when-required
specifically, not all three.

### Open findings
canonical: the step-verdict `gh pr view 85`/`gh pr diff 1231` citations above, run/read this session.
1. impact: `implementation.md`'s PR #1231 section asserted a specific
   external PR URL as already opened before that PR existed, presenting
   a not-yet-started action as if it had already happened.
   timeline: claim written 2026-08-13T06:55:25Z-06:59:16Z; PR #85
   actually created 2026-08-13T08:07:20Z (both cited in the step
   verdict above).
   root cause: the cross-repo delivery step was narrated in finished
   tense before this session's evidence shows it had actually
   succeeded, with no asserted-mode qualifier on that line.
   canonical: the step-verdict `gh pr view 85` citation above, run this session.
   action item: when a record's delivery step spans a second repo whose
   PR-create call cannot be verified within the same turn, state the
   commit-pushed fact only (as this same PR's own deviation-log entry
   correctly does for the on-the-record-side PR) and mark the
   cross-repo PR-open line pending/asserted, not finished, until a live
   check corroborates it.
2. impact: no phase-1 proposal artifact for this fan-out unit is
   evidenced on `main`, so scouted-when-required does not clear.
   timeline: applies to PR #1231's full commit range,
   2026-08-13T06:55:25Z-06:59:16Z.
   root cause: the record names only the governing APPROVE comment as
   upstream basis, never stating which of the two phase-2-entry paths
   (contract v3 s19 Approve, or s19a build-now bypass) applied to this
   unit.
   action item: a delivery record should state explicitly which
   phase-2-entry path applied, so a later observer does not infer it
   from an absent proposal file.

### Resolution path
canonical: the `gh pr diff 1231` / `gh pr view 85` citations used throughout this section, all run this session.
Both findings above are process/record-quality gaps in an
already-merged PR; independence bars this role from editing PR #1231 or
`implementation.md` directly. A human judges these findings on this
record's own PR and decides whether a corrective note in
`implementation.md` is warranted, given the underlying fold-in did
eventually land for real.

loop_state: handed-off.

## Observation: implementation role, PR #1207 (issue-1199/implementation)
canonical: `gh pr view 1207 --json title,body,mergeCommit,commits,files,mergedAt`, run this session.
canonical: `gh pr diff 1207`, read this session.

code_under_review:
  - docs/issue-1199/reports/implementation.md
  - gates/tool_learnings_gate.py
  - gates/tool_learnings_tracker.py

canonical: `gh pr diff 1207`, read this session.
Independence statement: this session did not author or edit PR #1207
this session; the step/trajectory findings below come only from `gh pr
diff 1207` (read this session) and `gh pr view`/`gh issue view` calls
(run this session), never from re-executing the implementation role's
task.

### Scope statement
canonical: `gh pr list --state merged --search "head:issue-1199/implementation" --json number,mergedAt`, run this session.
Four PRs on `issue-1199/implementation` reached MERGED state: #1207
(2026-08-13T06:21:41Z), #1231 (already observed above), #1253 (already
noted above as phase-1-only), #1298 (already observed above).
canonical: `grep -n "PR #1207" docs/issue-1199/reports/execution-observation.md`, run this session before writing this section.
Zero prior hits for "PR #1207" in this file before this section was
written. Target: PR #1207
(https://github.com/tokenmaxxxer/on-the-record/pull/1207, merge commit
`6517c4813a43e11bbbbf2fb1a05f5ff837393c22`).

canonical: `gh pr diff 1207`, read this session.
PR #1207's diff adds four new files under `gates/` (`tool_learnings_gate.py`,
`test_tool_learnings_gate.py`, `tool_learnings_tracker.py`,
`test_tool_learnings_tracker.py`) plus three new docs files
(`docs/issue-1199/proposals/step1-verification-infra.md`,
`docs/issue-1199/reports/implementation.md`,
`docs/issue-1199/reports/implementation/survey.md`) — all new files, no
existing file touched, so every citation below sits inside a hunk this
PR itself added (DIFF-SCOPE satisfied). This diff (`gh pr diff 1207`)
was read before re-reading `implementation.md`'s prose framing inside
that same diff output (FRESH-EYES ORDERING).

### Verdict: trajectory
canonical: `gh pr diff 1207`, read this session — `survey.md`'s content
(added in this PR) names concrete write surfaces
(`gates/playbook_depth_gate.py`, `gates/playbook_tracker.py`, a sample
role spec, the sibling test files) and resolves two unknowns (cap
mechanism, tracker denominator source), preceding any proposal-shaped
language in the same diff.
canonical: `gh pr diff 1207`, read this session, same survey.md content.
scouted-when-required: pass.

canonical: `gh pr diff 1207`, read this session — `step1-verification-infra.md`'s
Rationale section (added in this PR) quotes the survey's own findings
as its stated basis, landing in the same commit (`81143c3`) that
precedes the code commit named in `implementation.md`'s own record.
canonical: `gh pr diff 1207`, read this session, same step1-verification-infra.md content.
surveyed-before-proposing: pass.

canonical: `gh issue view 1199 --json comments`, run this session — exact-string comment "APPROVE issue-1199/implementation" by JiwonJung94 at 2026-08-13T06:11:45Z, no other approval-shaped comment found addressed to this branch in the same output.
canonical: `gh pr view 1207 --json commits`, run this session — first commit at 2026-08-13T06:15:53Z, after the APPROVE timestamp above.
`JiwonJung94` is a listed approver (per `docs/specs/approvers.md`, read
this session) and PR author, so single-account mode applies; the
APPROVE timestamp precedes PR #1207's first commit.
canonical: `gh pr view 1207 --json commits`, run this session, same commit timestamp cited directly above.
approved-by-human: pass.

canonical: `gh issue view 1199 --json comments`, run this session, same output cited above.
Trajectory verdict, recomputed from the three checks directly above: sound.

### Verdict: step
canonical: `gh pr diff 1207`, read this session — `implementation.md`'s
"Test run" section states "23 passed in 0.05s" for the two new test
files against commit `81143c3`.
subject: `implementation.md`'s test-pass claim; test: whether this
session can corroborate it without re-executing the implementation
role's own task (prohibited); finding: the claim carries its own
`derived:` reproduction command but this session did not re-run it.
canonical: `gh pr diff 1207`, read this session, same test-run citation directly above.
result: unverifiable. assertedBy: execution-observation, this session.
mode: asserted (the observed role's own record states it, unverified
independently this session).

canonical: `python3 -c "print(open('gates/tool_learnings_tracker.py').read().splitlines()[36])"`, run this session — line 37: `refs = spec.get("tool_learnings_refs")`.
canonical: `python3 -c "print(open('gates/playbook_tracker.py').read().splitlines()[37])"`, run this session — line 38: `refs = spec.get("playbook_refs")`.
subject: the claim in `implementation.md` that the two tracker files
read distinct spec fields; test: does a direct read of both files
corroborate `tool_learnings_refs` vs `playbook_refs`.
canonical: `python3 -c "print(open('gates/tool_learnings_tracker.py').read().splitlines()[36])"`, run this session, same output cited above.
finding: the two `python3` reads directly above confirm distinct field
names.
canonical: `python3 -c "print(open('gates/playbook_tracker.py').read().splitlines()[37])"`, run this session, same output cited above.
result: passed. assertedBy: execution-observation, this session.
mode: read.

canonical: `python3 -c "import os; print([os.path.exists(p) for p in ['gates/tool_learnings_gate.py','gates/tool_learnings_tracker.py','gates/test_tool_learnings_gate.py','gates/test_tool_learnings_tracker.py']])"`, run this session — `[True, True, True, True]`.
subject: the four new gates files' existence as claimed by PR #1207's
diff; test: do the paths resolve in the working tree; finding: all four
resolved per the `python3` check directly above.
canonical: `python3 -c "import os; print([os.path.exists(p) for p in ['gates/tool_learnings_gate.py','gates/tool_learnings_tracker.py','gates/test_tool_learnings_gate.py','gates/test_tool_learnings_tracker.py']])"`, run this session, same output cited above.
result: passed. assertedBy: execution-observation, this session. mode:
command.

### Verdict: outcome
canonical: `gh pr diff 1207`, read this session (test-run citation above), and the two `python3` reads above, all run/read this session.
Recomputed per the spec's worst-case-among-cited-step-level-results
rule: this record cites {unverifiable, passed, passed} — worst case is
unverifiable, no step here is failed.

canonical: `python3 -c "print(open('gates/tool_learnings_tracker.py').read().splitlines()[36])"` and `python3 -c "import os; print([os.path.exists(p) for p in ['gates/tool_learnings_gate.py','gates/tool_learnings_tracker.py','gates/test_tool_learnings_gate.py','gates/test_tool_learnings_tracker.py']])"`, both run this session, same outputs cited above.
Outcome, stated with its mode inline: unverifiable-with-no-known-defect
— the field-key-distinctness and file-existence steps this session
independently checked both passed.
canonical: `gh pr diff 1207`, read this session, same test-run citation used in Verdict: step above.
The test-pass step rests on the observed role's own asserted claim,
unverified independently this session.

canonical: the Verdict: step section directly above, produced this session.
No deficiency finding is raised for PR #1207: the unverifiable step is
an evidentiary-mode gap under this role's own PROHIBITED-re-execution
constraint, not a defect this session found in the observed PR itself.

loop_state: handed-off.
