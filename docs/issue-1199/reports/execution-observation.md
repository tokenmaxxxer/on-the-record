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
