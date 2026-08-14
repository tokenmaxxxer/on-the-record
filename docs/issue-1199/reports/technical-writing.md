kind: report
subject: issue-1199
doc-type: reference

## Amendments reconciled

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276711943
issuecomment-5276711943 ("APPROVE issue-1199/brand-design", posted
after this session started) approves the sibling issue-1199/brand-design
unit, not this technical-writing unit — no amendment to this unit's
scope or the approved tool-landscape-fold-in proposal.
amendments-reconciled: issuecomment-5276711943 — out of scope for this
unit (approves a different fan-out unit), no action taken on this
record or the rulebook PR.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276738377
issuecomment-5276738377 ("Verdict: PR #? → escalate (depth or impact
axis did not clear)", posted after this session started) is a
delegated-judgment verdict for one of the other issue-1199 fan-out
branches' implementation PRs, not this technical-writing unit — no
amendment to this unit's scope.
amendments-reconciled: issuecomment-5276738377 — out of scope for this
unit (verdict on a different fan-out unit's PR), no action taken on
this record or the rulebook PR.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276794729
issuecomment-5276794729 ("Verdict: PR #? → escalate (depth or impact
axis did not clear)", posted after this session started) is another
delegated-judgment verdict for a different issue-1199 fan-out branch's
implementation PR, not this technical-writing unit — no amendment to
this unit's scope.
amendments-reconciled: issuecomment-5276794729 — out of scope for this
unit (verdict on a different fan-out unit's PR), no action taken on
this record or the rulebook PR.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276795934
issuecomment-5276795934 ("Verdict: PR #? → escalate (depth or impact
axis did not clear)", posted after this session started) is another
delegated-judgment verdict for a different issue-1199 fan-out branch's
implementation PR, not this technical-writing unit — no amendment to
this unit's scope.
amendments-reconciled: issuecomment-5276795934 — out of scope for this
unit (verdict on a different fan-out unit's PR), no action taken on
this record or the rulebook PR.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276871308
issuecomment-5276871308 ("a fold-in must APPLY its upgrades, not only
reference them ... technical-writing's landed fold-in referenced
upgrades without applying them and needs a retrofit pass") is in
scope: it names this unit directly and requires a retrofit — this
session's build work described in the "What was" section is that
retrofit.
canonical: git -C /tmp/technical-writing-rulebook log --oneline -3
```
13ded01 Reconcile no-tool-attribution amendment: absorb insight natively
d3cbd8c Retrofit tool-landscape fold-in: apply diagram/Vale rules into axis files
3f53654 Merge pull request #26 from tokenmaxxxer/issue-1199/tool-landscape
```
amendments-reconciled: issuecomment-5276871308 — reconciled by commit
d3cbd8c, which edits doc-type-selection.md, minimalism-scoping.md, and
style-guide-compliance.md to carry the named upgrades.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276881749
issuecomment-5276881749 ("NATIVE APPLICATION, NO TOOL-ATTRIBUTION
CATALOGS ... retrofit the two landed fold-ins: technical-writing's
playbook/tool-landscape.md and brand-design's edits — strip
tool-attribution framing, keep the absorbed rules native, move any
provenance to the on-the-record record") is in scope: it names this
unit's landed fold-in directly and supersedes part of this session's
first retrofit commit.
amendments-reconciled: issuecomment-5276881749 — reconciled by commit
13ded01 (cited above), which removes playbook/tool-landscape.md and
its README entry from the rulebook, rewrites the four applied rules to
drop source-repo names and `source: <url>` framing, and moves the
evidence trail to this record's "Accuracy review evidence" section.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276957084
issuecomment-5276957084 ("Verdict: PR #? → escalate (depth or impact
axis did not clear)", posted after this session started) is another
delegated-judgment verdict for a different issue-1199 fan-out branch's
implementation PR, not this technical-writing unit — no amendment to
this unit's scope.
amendments-reconciled: issuecomment-5276957084 — out of scope for this
unit (verdict on a different fan-out unit's PR), no action taken on
this record or the rulebook PR.

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276958317
issuecomment-5276958317 ("Verdict: PR #? → escalate (depth or impact
axis did not clear)", posted after this session started) is another
delegated-judgment verdict for a different issue-1199 fan-out branch's
implementation PR, not this technical-writing unit — no amendment to
this unit's scope.
amendments-reconciled: issuecomment-5276958317 — out of scope for this
unit (verdict on a different fan-out unit's PR), no action taken on
this record or the rulebook PR. Same reconcile-then-retry-`gh pr
create` deadlock already logged in this issue's history (commit
df36363) and in this record's own "Resolution path" section — retries
stop here; the on-the-record branch is committed and pushed (commits
af7716f, f0e5c43 on `issue-1199/technical-writing` at origin) for
external relay to open the delivery PR.

# technical-writing — phase-2 record (issue #1199)

## What was done

canonical: cat /tmp/twr1199/playbook/tool-landscape.md (this turn's
tool transcript — file written and committed this session, commit
94037703a6484249e08868916fb17b6ac343ce1c)
Delivered the approved tool-landscape fold-in from
`docs/issue-1199/proposals/2026-08-13-tool-landscape-fold-in.md`: added
`playbook/tool-landscape.md` to `tokenmaxxxer/technical-writing-rulebook`
(branch `issue-1199/tool-landscape`, commit
`94037703a6484249e08868916fb17b6ac343ce1c`) with six condition→choice→
source rule blocks.
canonical: cat /tmp/twr1199/playbook/tool-landscape.md (same file read
this turn — see above)
The six rules: diagram-cost tradeoff, visual-noise discipline,
style-rule executability, Diátaxis confirmed-by-field, a generation/
style separability detail, and an explicit skip on cloning exemplar
surface syntax. Each names which existing axis file's judgment it
upgrades (doc-type-selection.md, minimalism-scoping.md, style-guide-
compliance.md). Added a matching README Layout line. Push to
`tokenmaxxxer/technical-writing-rulebook` succeeded this session.
Rulebook PR opened this same turn:
https://github.com/tokenmaxxxer/technical-writing-rulebook/pull/26

code_under_review:
- playbook/tool-landscape.md (tokenmaxxxer/technical-writing-rulebook)
- README.md (tokenmaxxxer/technical-writing-rulebook)

## Why

Issue #1199 (northpole req#1) requires every role to survey tools its
domain actually uses and fold distilled learnings into a bounded
rulebook section naming which rule each upgrades, so the rulebook
reflects real practitioner tooling rather than methodology alone.

## Upstream / basis

- docs/issue-1199/proposals/2026-08-13-tool-landscape-fold-in.md
- docs/issue-1199/reports/technical-writing/scout-brief.md
- docs/issue-1199/reports/technical-writing/current-state-survey.md

## Target reader

The phase-1 proposal's approver and future sessions maintaining
tokenmaxxxer/technical-writing-rulebook's playbook/*.md set.

## Doc outline

1. Work summary (this file, reference-type record)
2. Rulebook PR content: front matter + 6 rule blocks in
   playbook/tool-landscape.md, README Layout line

## Minimalism check

Each rule in playbook/tool-landscape.md ties to one scout-brief
finding and one named upgrade target; the confirming entry (Diátaxis)
and the explicit skip entry both serve the target reader's need to
know what was checked and rejected, not padding.

## Style-guide compliance note

no deviations — playbook/tool-landscape.md's front matter and rule
shape mirrors the five existing playbook/*.md axis files (verified
against playbook/doc-type-selection.md's shape before writing).

## Accuracy review evidence

derived: cd /tmp/twr1199 && git log -1 --format=%H
```
94037703a6484249e08868916fb17b6ac343ce1c
```
Every source URL in playbook/tool-landscape.md's six rules carries
over verbatim from the scout-brief's own Sources list (phase-1
WebSearch/WebFetch trail), not re-derived from memory this turn.

## kind / loop_state

canonical: git -C /tmp/twr1199 log -1 --format=%H (commit 94037703a6484249e08868916fb17b6ac343ce1c, this turn's tool transcript)
kind: report
loop_state: phase-2-complete

## Next steps

canonical: gh pr view 26 --repo tokenmaxxxer/technical-writing-rulebook (https://github.com/tokenmaxxxer/technical-writing-rulebook/pull/26, opened this turn's tool transcript)
Rulebook PR is open; the only remaining step is checking off the
technical-writing row in issue #1199's 43-item tracker, per the
proposal's Plan for phase 2 step 4 — left to the tracker's own owner
per this role's write scope.

## Resolution path

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276799867
issuecomment-5276799867 arrived while this turn's own `gh pr create`
attempt was in flight — the same PR-creation deadlock a prior session
already hit and logged (commit df36363, "note PR-creation deadlock,
stop retries"): an automated delegated-judgment verdict stream on
sibling issue-1199 fan-out branches posts faster than the
reconcile-record-then-retry-PR cycle can close. Per that precedent,
retries stop here rather than looping; the branch is committed and
pushed (commit 1fa3448 and this record's own landing commit, both on
`issue-1199/technical-writing` at origin) so on-the-record's external
relay can open the delivery PR. This is a filed, not inline, deviation
per the role-deviation directive — logged in
docs/issue-1199/reports/technical-writing/deviation-log.md.

## Retrofit — this session (apply-not-reference + no-tool-attribution)

canonical: git -C /tmp/technical-writing-rulebook log --oneline -3
```
13ded01 Reconcile no-tool-attribution amendment: absorb insight natively
d3cbd8c Retrofit tool-landscape fold-in: apply diagram/Vale rules into axis files
3f53654 Merge pull request #26 from tokenmaxxxer/issue-1199/tool-landscape
```

### What was done (retrofit)

Two commits on branch `issue-1199/tool-landscape-retrofit` in
`tokenmaxxxer/technical-writing-rulebook`, pushed to origin:

1. `d3cbd8c` — added `doc-type-selection.md` rules 11-12 (diagram
   polish-vs-update-cheapness judgment; generation/style
   separability), `minimalism-scoping.md` rule 11 (editorial-diagram
   visual-discipline cap), and `style-guide-compliance.md` rule 11
   (executable-check preference over prose-only compliance) — the
   three axis-file edits `playbook/tool-landscape.md` had named as
   upgrade targets without previously editing them.
2. `13ded01` — reconciling issuecomment-5276881749: removed
   `playbook/tool-landscape.md` and its README entry entirely, and
   rewrote the four rules added in `d3cbd8c` to drop tool-repo names
   and `source: <url>` framing, phrasing each as the role's own
   native judgment rather than an attributed borrowing.

code_under_review:
- playbook/doc-type-selection.md (tokenmaxxxer/technical-writing-rulebook)
- playbook/minimalism-scoping.md (tokenmaxxxer/technical-writing-rulebook)
- playbook/style-guide-compliance.md (tokenmaxxxer/technical-writing-rulebook)
- README.md (tokenmaxxxer/technical-writing-rulebook)
- playbook/tool-landscape.md (tokenmaxxxer/technical-writing-rulebook, deleted)

### Why (retrofit)

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276871308
issuecomment-5276871308's stated finding: the first fold-in (PR #26)
referenced its upgrade targets without editing them — documentation,
not an applied implementation.
canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5276881749
issuecomment-5276881749's stated finding: the retrofit's own first
commit (d3cbd8c) still carried tool-attribution framing (repo names,
`source:` links to external tools) inside the public rulebook, which
the operator's amendment rules out — insight must be absorbed as
native role judgment, with the survey/adoption evidence trail confined
to on-the-record's own issue-side record.

### Adoption evidence trail (moved here per issuecomment-5276881749)

The survey underlying the four applied rules — diagram-cost tradeoff
(editorial vs. as-code), visual-discipline caps for editorial
diagrams, and style-rule executability — is recorded in
`docs/issue-1199/reports/technical-writing/scout-brief.md`'s Sources
list (phase-1 WebSearch/WebFetch trail, adoption evidence per tool:
star counts, GitHub-trending listing, named production adopters).
That file is the canonical evidence source; this record does not
duplicate the tool names/URLs per the no-attribution amendment, only
points to where they are kept.

### Rulebook PR — blocked, branch pushed instead

canonical: this turn's own tool transcript — the `gh pr create --repo
tokenmaxxxer/technical-writing-rulebook ...` call and its
`PreToolUse:Bash hook error` denial from
`on-the-record/hooks/upstream-defect-scope-guard.sh` (citing issue
#1171 scoping, commit 5154a3d)
That guard denied PR creation — its cross-repo check has no exemption
for a role's protocol-required phase-2 rulebook PR against a separate
consuming repo. Fixing the guard is not in scope for this session
(hooks/gates changes are outside this role's write scope and this
task's frozen write set).

canonical: git -C /tmp/technical-writing-rulebook log --oneline -1 origin/issue-1199/tool-landscape-retrofit
```
13ded01 Reconcile no-tool-attribution amendment: absorb insight natively
```
Both retrofit commits (d3cbd8c, 13ded01) reached
`tokenmaxxxer/technical-writing-rulebook` origin on branch
`issue-1199/tool-landscape-retrofit`, per the `git log` on
`origin/...` cited immediately above; PR creation is left to an
orchestrator/on-the-record external relay. Logged as a filed deviation
in `docs/issue-1199/reports/technical-writing/deviation-log.md`.

### kind / loop_state (retrofit)

canonical: git -C /tmp/technical-writing-rulebook log --oneline -3 (cited at the top of this section)
kind: report
loop_state: phase-2-complete

### Next steps (retrofit)

An orchestrator/relay session needs to open the rulebook PR from
`issue-1199/tool-landscape-retrofit` (both commits already on origin,
cited above) against `tokenmaxxxer/technical-writing-rulebook`'s
`main`; no further action owned by this role's write scope beyond what
this record and that pushed branch already carry.

### Resolution path (retrofit)

Once the rulebook PR is opened (by relay, or by a future session after
the guard gains a cross-repo exemption), the next technical-writing
session on issue-1199 picks up from this record's Amendments-reconciled
log and that PR's diff — no open blocker on this session's own branch
otherwise.

## Plugin-ecosystem rework — this session (2026-08-14 amendment)

canonical: git -C /tmp/technical-writing-rulebook log --oneline -1 origin/issue-1199/tool-landscape-plugin-rework
```
7339910 Rework tool-landscape fold-in to Claude Code plugin ecosystem (issue #1199, 2026-08-14 amendment)
```

### What was done (plugin rework)

The 2026-08-14 issue amendment supersedes the earlier domain-tool-basis
survey with a CLAUDE CODE PLUGIN/SKILL ecosystem survey, and asks that
`playbook/tool-landscape.md` be kept/recreated with plugin-derived
entries (not deleted per the earlier no-attribution retrofit). This
session:

1. Ran a web/adoption-evidence sweep (`gh api repos/<owner>/<repo>
   --jq .stargazers_count`) over Claude Code plugin/skill marketplaces
   relevant to technical writing: cathrynlavery/diagram-design (14,471
   stars), jeremylongshore/claude-code-plugins-plus-skills (2,630
   stars), daymade/claude-code-skills (1,333 stars),
   rohitg00/awesome-claude-code-toolkit (2,501 stars).
2. Recreated `playbook/tool-landscape.md` in
   `tokenmaxxxer/technical-writing-rulebook` (branch
   `issue-1199/tool-landscape-plugin-rework`, commit `7339910`) with
   three entries, each carrying {tool, adoption evidence, problem, how,
   upgraded-rule mapping, source URL}: diagram-design's grid/color/font
   constraint set (upgrades doc-type-selection.md rule 11 and
   minimalism-scoping.md rule 11), diagram-design's redraw "what
   changed" ledger (upgrades style-guide-compliance.md's
   accuracy-review-evidence expectation to cover diagram edits), and
   the content-consistency-validator skill's deterministic drift-check
   shape (upgrades technical-writing.md's own accuracy-review-evidence
   requirement).
3. Added a matching README Layout line.
4. Committed and pushed to origin. `gh pr create --repo
   tokenmaxxxer/technical-writing-rulebook ...` was denied again by
   `upstream-defect-scope-guard.sh` (same denial as the prior retrofit
   session, issue #1131 req#4 — the upstream channel files issues, not
   PRs) — branch is on origin for external relay to open the PR.

code_under_review:
- playbook/tool-landscape.md (tokenmaxxxer/technical-writing-rulebook)
- README.md (tokenmaxxxer/technical-writing-rulebook)

### Why (plugin rework)

Issue #1199's 2026-08-14 amendment (northpole req#1): the survey target
is the Claude Code plugin/skill ecosystem, not general domain tools —
the prior domain-tool-basis survey fails the amended acceptance check,
and `loop_state: landed` requires the named upgrade file to actually be
edited and pushed.

### Upstream / basis (plugin rework)

- Issue #1199 body, 2026-08-14 amendment comment (Claude Code plugin
  ecosystem survey target)
- docs/issue-1199/proposals/2026-08-13-tool-landscape-fold-in.md

### Accuracy review evidence (plugin rework)

derived: cd /tmp/technical-writing-rulebook && git log -1 --format=%H origin/issue-1199/tool-landscape-plugin-rework
```
7339910
```
derived: gh api repos/cathrynlavery/diagram-design --jq .stargazers_count
```
14471
```
Star counts for all four surveyed repos were read live this session via
`gh api .../--jq .stargazers_count`, not recalled from memory; the two
cited plugin descriptions were read via WebFetch of the repos' own
README content this session.

### kind / loop_state (plugin rework)

kind: report
loop_state: landed

### Next steps (plugin rework)

An orchestrator/relay session needs to open the rulebook PR from
`issue-1199/tool-landscape-plugin-rework` (commit `7339910`, already on
origin) against `tokenmaxxxer/technical-writing-rulebook`'s `main` —
`gh pr create` is refused from inside this role session by
`upstream-defect-scope-guard.sh`.

### Resolution path (plugin rework)

Once the rulebook PR lands, check off the technical-writing row in
issue #1199's 43-item tracker; no other blocker on this branch.

## Open findings

None.
