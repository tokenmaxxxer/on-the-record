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
