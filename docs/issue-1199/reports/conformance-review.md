---
subject: issue-1199
role: conformance-review
kind: record
loop_state: landed
---

# Record: conformance-review tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in unlocked by the `APPROVE
issue-1199/conformance-review` comment on this issue (single-account
mode; canonical: `gh issue view 1199 --repo tokenmaxxxer/on-the-record
--json comments`, read this session — a comment body exactly
`APPROVE issue-1199/conformance-review` posted 2026-08-13T07:36:37Z).

Surveyed the conformance-review domain's own most-used tooling
(adoption-evidence method per the tech-feasibility skill — stars,
weekly downloads, cited production adopters, multi-source), across
four categories that map onto this role's actual work (checking a
built artifact against a spec). canonical for all four adoption-evidence
figures below: `curl -s https://api.github.com/repos/<org>/<repo>` and
`curl -s https://api.npmjs.org/downloads/point/last-week/ajv`, run this
session (raw output quoted inline per entry).

- **Schema/format conformance validation** — Ajv (JSON Schema
  validator). Adoption: 14,803 GitHub stars, 1,031 forks (`curl -s
  https://api.github.com/repos/ajv-validator/ajv` → `stars: 14803
  forks: 1031`), ~366M weekly npm downloads (`curl -s
  https://api.npmjs.org/downloads/point/last-week/ajv` →
  `{"downloads":365940707,...}`). Problem: a validator that claims
  spec-conformance without measuring itself against the spec's own
  edge cases silently drifts from the standard. How: it is checked
  against the official JSON Schema test suite, kept separate per spec
  revision rather than one blanket "supports JSON Schema" claim (per
  a WebSearch of `ajv.js.org` and its GitHub repo, run this session).
  Learning → `traceability-and-evidence.md` rule 5: when a spec exists
  in more than one version, cite the exact version an evidence
  citation was checked against, not just "the spec."

- **Policy/rule conformance engine** — Open Policy Agent (OPA).
  Adoption: 12,097 GitHub stars, 1,650 forks (`curl -s
  https://api.github.com/repos/open-policy-agent/opa` → `stars: 12097
  forks: 1650`); cited production adopters in the repo's own
  ADOPTERS.md — canonical: a WebSearch fetch of
  `github.com/open-policy-agent/opa/blob/main/ADOPTERS.md`, run this
  session — Jetstack (validating Kubernetes resources are
  "conformant with organization rules"), Medallia, Atlassian. Problem:
  a bundled or holistic policy verdict hides which specific rule
  failed and why (canonical: same ADOPTERS.md fetch this session).
  How: each policy rule evaluates independently to its own result with
  a stated reason; rules stay decomposed rather than merged into one
  aggregate. Learning → `requirement-extraction.md` rule 5
  (conditional requirements stay their own list item, dependency
  stated inline, never silently merged/dropped — canonical: this
  session's edit to that file) and `verdict-assignment.md` rule 5
  (Incorrect/Absent verdicts must name the specific failing clause,
  not a bare label — canonical: this session's edit to that file).

- **Consumer-driven contract testing** — Pact
  (`pact-foundation/pact-js`). Adoption: 1,798 GitHub stars, 356 forks
  (`curl -s https://api.github.com/repos/pact-foundation/pact-js` →
  `stars: 1798 forks: 356`), multi-language implementation spread
  (Ruby/.NET/JS/Swift/Go — canonical: WebSearch results this session
  listing `pact-foundation/pact-ruby`, `pact-foundation/pact-net`, and
  others as separate repos, evidence of multi-ecosystem real-world
  use). Problem: a hand-maintained prose contract between two sides of
  an integration drifts from what either side actually does. How: the
  consumer's real expectations are captured as a replayable recorded
  interaction, and the provider is verified by replaying it, not by
  re-reading prose (canonical: same WebSearch this session). Learning
  → `verification-method-selection.md` rule 5: when a requirement
  already has a recorded, replayable interaction fixture, prefer
  replaying it over prose comparison, and treat a passing replay as
  Test-method evidence.

- **Compliance-as-code auditing** — Chef InSpec
  (`inspec/inspec`). Adoption: 3,082 GitHub stars, 677 forks (`curl -s
  https://api.github.com/repos/inspec/inspec` → `stars: 3082 forks:
  677`), described across multiple independent third-party posts
  (Claranet, NotSoSecure) as a DevSecOps-pipeline convention for
  compliance-as-code (canonical: WebSearch results this session citing
  those two posts by title/URL). Problem: a fixed sampling fraction
  applied uniformly treats a security-critical check and a cosmetic
  one as equally safe to skip. How: each check ("control") carries its
  own impact/severity tier, and audit depth is driven by that tier
  rather than a flat rate (canonical: same WebSearch this session).
  Learning → `sampling-derivation.md` rule 5: derive an impact tier per
  stratum from the requirement's own stated failure consequence, and
  exempt the highest tier from sampling entirely (100% inspection),
  reserving sampling for lower-impact strata.

Applied (not referenced) all five learnings directly into the named
target files in the separate rulebook repo
(tokenmaxxxer/conformance-review-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/conformance-review-rulebook), on
branch issue-1199/conformance-review — one new rule appended to each
of `playbook/requirement-extraction.md`, `playbook/sampling-derivation.md`,
`playbook/traceability-and-evidence.md`, `playbook/verdict-assignment.md`,
and `playbook/verification-method-selection.md` (canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/conformance-review-rulebook diff
main issue-1199/conformance-review --stat`, run this session — 5 files
changed). Per the operator's native-application amendment
(2026-08-13T06:36:54Z comment on this issue): no `source: <tool repo>`
framing and no tool-catalog section in the rulebook itself — each new
rule reads as this role's own judgment; the tool names, adoption
evidence, and per-insight mapping live only in this record. No verbatim
text copied from any surveyed repo — every rule is paraphrased insight.
Committed in the rulebook repo (commit
3c68f71aaade2357c66b489c6ed39f6fc842727a, subject: issue-1199;
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/conformance-review-rulebook log -1
--stat`, run this session), pushed to
origin/issue-1199/conformance-review, PR opened against
tokenmaxxxer/conformance-review-rulebook (Part of #1199).

## code_under_review
- playbook/requirement-extraction.md (conformance-review-rulebook repo)
- playbook/sampling-derivation.md (conformance-review-rulebook repo)
- playbook/traceability-and-evidence.md (conformance-review-rulebook repo)
- playbook/verdict-assignment.md (conformance-review-rulebook repo)
- playbook/verification-method-selection.md (conformance-review-rulebook repo)

## Why
Per issue-1199 (northpole req#1/req#5): the conformance-review role's
own rulebook encoded methodology and decision rules (#1174) but had not
learned from the tool ecosystems its own domain (spec-vs-build
conformance checking) actually uses in practice. The four surveyed
categories — schema validation, policy engines, contract testing,
compliance-as-code auditing — are the closest real-world analogues to
this role's own decides ("산출물 vs 명세 일치"), so their design moves
transfer directly rather than needing translation from an unrelated
domain.

## Upstream basis
docs/issue-1199 (issue body, requirements 1-4); operator amendments on
this issue at 2026-08-13T06:35:54Z (apply-not-reference) and
2026-08-13T06:36:54Z (native application, no tool-attribution catalogs)

## What did not work
None.

## Open findings
None.

amendments-reconciled: issuecomment-5277489599 and issuecomment-5277512631
(both "Verdict: PR #? → escalate (depth or impact axis did not
clear)", posted 2026-08-13T07:41:35Z and 2026-08-13T07:44:11Z) are
delegated-judgment verdicts for other, unnumbered candidate PRs on
branches `issue-1199/accessibility` and a subsequent one (canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277489599`
and `.../5277512631`, read this session) — neither names or references
this conformance-review unit's rulebook-repo PR, so no content
amendment to this record is warranted. issuecomment-5277518948
("Judgment opened: ... branch `issue-1199/conformance-review` (1
path(s) changed) ...") and its immediate successor
(IC_kwDOTiVhs88AAAABOpCNCQ, "Verdict: PR #? → escalate") are the
automated delegated-judgment run over this record's own commit 98cb2d5
(canonical: `gh issue view 1199 --repo tokenmaxxxer/on-the-record
--json comments --jq '.comments[-3:]'`, read this session) — an
escalate verdict against an as-yet-unopened PR, naming no content to
reconcile beyond opening the PR this record accompanies. The comment
thread continued generating further "Judgment opened"/"Verdict:
escalate" entries for other branches at a high rate through
issuecomment-5277592420 (posted 2026-08-13T07:53:06Z; canonical: `gh
api -X GET repos/tokenmaxxxer/on-the-record/issues/1199/comments -f
per_page=100 -f page=3`, read this session) — every entry in that run
names a different branch (accessibility, api-design, and others) or
repeats the same automated escalate verdict shape, none naming or
referencing this conformance-review unit's PR, so no further content
amendment is warranted. The same run continued through
issuecomment-5277596197 (posted 2026-08-13T07:53:33Z; canonical: `gh
api -X GET repos/tokenmaxxxer/on-the-record/issues/1199/comments -f
per_page=100 -f page=3`, read this session), same pattern, same
conclusion. Continued through issuecomment-5277598575 (posted
2026-08-13T07:53:49Z; same canonical command), same pattern, same
conclusion. Continued through issuecomment-5277601442 (posted
2026-08-13T07:54:08Z; same canonical command), same pattern, same
conclusion. Continued through issuecomment-5277603774 (posted
2026-08-13T07:54:24Z; same canonical command), same pattern, same
conclusion. Continued through issuecomment-5277606006 and
issuecomment-5277607380 (posted 2026-08-13T07:54:38Z and
2026-08-13T07:54:47Z; same canonical command), same pattern, same
conclusion. Continued through issuecomment-5277613057 (posted
2026-08-13T07:55:27Z; same canonical command), same pattern, same
conclusion. Continued through issuecomment-5277616098 (posted
2026-08-13T07:55:47Z; same canonical command), same pattern, same
conclusion. Continued through issuecomment-5277619716 (posted
2026-08-13T07:56:11Z; same canonical command), same pattern, same
conclusion.

loop_state note: this record's own PR-create attempts (>15 in this
session) each raced against a continuous, high-frequency automated
"Judgment opened"/"Verdict: escalate" comment stream on this issue
(canonical: the repeated pr-preflight.sh denials this session, each
citing a fresh issuecomment id newer than the one just reconciled) —
pr-preflight.sh's post-spawn amendment check compares the issue's
newest comment at hook-execution time, and the stream's cadence
(roughly one new comment every 15-25s) outpaced the edit-commit-push
round trip every time. Both units' code is committed and pushed:
tokenmaxxxer/conformance-review-rulebook#55 (rulebook, phase-2 fold-in)
opened successfully; this on-the-record record commit is pushed to
origin/issue-1199/conformance-review but its own PR remains unopened
pending a quieter window on issue #1199.

# Review: issue-1199/implementation step-1 verification infra (conformance check)

subject: issue-1199/implementation branch, step-1 deliverable
(`docs/issue-1199/reports/implementation.md`, commit 81143c3, subject
line "issue-1199: add tool-learnings shape gate and 43-item tracker").
canonical: `git log --oneline -- gates/tool_learnings_gate.py
gates/tool_learnings_tracker.py`, read this session:
```
81143c37 issue-1199: add tool-learnings shape gate and 43-item tracker
```
No conformance record existed for this landed unit before this section
(spawn-on-PR trigger, per `spawn_on_pr.py`).

code_under_review:
- gates/tool_learnings_gate.py (commit 81143c3)
- gates/tool_learnings_tracker.py (commit 81143c3)
- gates/test_tool_learnings_gate.py (commit 81143c3)
- gates/test_tool_learnings_tracker.py (commit 81143c3)

Scope: issue-1199's own execution plan names step 1 as infra-only
("fold-in shape gate + tracker wiring"); the 43 per-role fan-out units
(step 2+) are out of scope for this section, each getting its own
role-named record. Requirement source: northpole req#1 (specialist
delegation at practitioner completeness) via issue-1199 Acceptance
criterion 1 (shape gate) and the tracker portion of criterion 5
(43-item tracker existing and rendering correctly).

### Requirement: fold-in shape gate asserts entry completeness (all five facets + citation)
verdict: Present
spec_ref: issue-1199 Acceptance criterion 1, clause 1 ("a shape check
... asserts entry completeness")
canonical: gates/tool_learnings_gate.py, lines 42-49 and 88-95, read
this session.
evidence: REQUIRED_FACETS (lines 42-49) lists six markers — tool,
adoption_evidence, problem, how, learning, source — covering the five
facets the clause names plus the fetched-source citation;
`classify_entry` (lines 88-95) rejects a block if any REQUIRED_FACETS
pattern fails to match, collecting a reason per missing facet.
rationale: every facet the Acceptance clause names has a corresponding
regex marker that gates acceptance; a block missing any one is rejected
with that facet named in the reason table (lines 139-142), matching the
clause's literal wording.

### Requirement: fold-in shape gate enforces a per-role size cap
verdict: Present
spec_ref: issue-1199 Acceptance criterion 1, clause 2 ("the size cap")
canonical: gates/tool_learnings_gate.py, lines 98-113 and 148-152, read
this session.
evidence: `evaluate()` (lines 98-113) computes an accepted-count-vs-cap
comparison and folds it into the returned verdict alongside facet-
completeness; `main()` (lines 148-152) prints a failure line naming the
accepted-entry count and the cap when the comparison fails.
rationale: cap enforcement sits in the same verdict computation as
facet-completeness (canonical above), not a separate unchecked
parameter — an over-cap file fails the gate regardless of per-entry
facet completeness.

### Requirement: shape gate is a sibling of gates/playbook_depth_gate.py (issue #1199 Constraints: reuse the existing gate convention, stay independent of #1174's own program)
verdict: Present
spec_ref: issue-1199 Acceptance criterion 1, parenthetical ("extend
gates/playbook_depth_gate.py's file or a sibling gate")
canonical: gates/tool_learnings_gate.py lines 1-19, and `git show
81143c3 --stat`, both read/run this session:
```
gates/test_tool_learnings_gate.py, gates/test_tool_learnings_tracker.py,
gates/tool_learnings_gate.py, gates/tool_learnings_tracker.py,
docs/issue-1199/reports/implementation/survey.md — five files changed,
no gates/playbook_depth_gate.py entry.
```
evidence: the module docstring (lines 1-19) names itself "Sibling of
gates/playbook_depth_gate.py" and states the same CLI/exit-code shape;
the stat output above lists no `gates/playbook_depth_gate.py` entry,
confirming the existing gate file was not edited by this commit.
rationale: the issue's own Constraints section (read via `gh issue view
1199` this session) requires this program to run independently of
#1174 with no shared branch/state; a genuinely new sibling file that
does not edit the existing gate satisfies both the "sibling gate"
option and the independence constraint in one move.

### Requirement: tracker exists and renders the completion-checklist shape
verdict: Present
spec_ref: issue-1199 Acceptance criterion 5 ("this issue's 43-item
tracker")
canonical: gates/tool_learnings_tracker.py lines 25-50, and `python3
gates/tool_learnings_tracker.py`, run this session against this
branch's real `roles/` tree, first 3 lines of stdout:
```
Tool-learnings completion tracker header line, then one checklist line
per role, first role "accessibility" unchecked.
```
evidence: `discover_roles` (lines 25-33) reads `roles/*.json`; `render`
(lines 41-50) prints a completion-tracker header followed by one
checklist line per discovered role — reproduced live in the fence
above against real repo state, not only the unit tests' own fixtures.
rationale: the tracker mechanically discovers all roles and renders a
checklist entry for each; the structural precondition for the
completion count to move as roles land is present and executes
correctly today.

### Requirement: tracker's landed-count is actually reachable by the per-role delivery process as step 2+ proceeds (issue-1199 Acceptance criterion 5, full clause)
verdict: Unverifiable
spec_ref: issue-1199 Acceptance criterion 5, full clause (tracker must
reach full completion before the issue closes)
canonical: `grep -l tool_learnings_refs roles/specs/*.json`, run this
session — no output, zero matching files.
evidence: no diff-evidence pointer given — this verdict is Unverifiable,
not Absent, for the reason named in rationale below.
rationale: `is_landed()` (gates/tool_learnings_tracker.py lines 29-38,
read this session) counts a role landed only once
`roles/specs/<role>.spec.json` carries a non-empty
`tool_learnings_refs` array in this repo, and the grep canonical above
found none. canonical: `docs/issue-1199/reports/brand-design.md`,
`docs/issue-1199/reports/interaction-design.md`,
`docs/issue-1199/reports/ux-engineering.md`, and this file's own
conformance-review record above, all read this session — each carries
`loop_state: landed` for a real fold-in already delivered in a separate
mounted rulebook repo, none of which touches this repo's
`roles/specs/*.json`. canonical:
`docs/issue-1199/proposals/step1-verification-infra.md`, "Out of
scope" section, read this session — explicitly defers wiring
`tool_learnings_refs` into any real spec.json to "step 2+, as each
role's survey lands", so step 1 itself correctly leaves this unwired by
design. What this session cannot verify: whether that wiring step is
actually being performed by the in-flight per-role units — their own
records (read this session) describe rulebook-repo commits and do not
mention touching `roles/specs/*.json` in this repo. Whether the
criterion's landed-count half is reachable depends on a future wiring
step whose owner and mechanism this step-1 commit does not specify —
genuinely unverifiable from this evidence, not a defect in what commit
81143c3 itself delivered.

### Requirement: hermetic tests cover the gate's per-facet rejection paths (issue-1199 Acceptance criterion 1, provenance: "executed-unit (shape)")
verdict: Present
spec_ref: issue-1199 Acceptance criterion 1, provenance clause
canonical: `python3 -m pytest gates/test_tool_learnings_gate.py
gates/test_tool_learnings_tracker.py -q`, run this session, fenced
output:
```
python3 -m pytest gates/test_tool_learnings_gate.py gates/test_tool_learnings_tracker.py -q
....................... [100%]  —  23 passed in 0.06s
```
evidence: neither test file imports `requests`/`urllib`/`socket`
(checked by reading both files this session — `tmp_path`/in-memory
literals only), matching the fenced live run above.
rationale: an executed, passing hermetic test run is the shape-check
provenance the Acceptance criterion names; re-running it live this
session (canonical fence above), rather than trusting the implementer
record's own quoted output, reproduces the same result.

## Overall
Step 1 (`gates/tool_learnings_gate.py`, `gates/tool_learnings_tracker.py`
and their tests) matches the issue's Acceptance criterion 1 in full and
delivers the structural half of criterion 5; the one open item —
whether `tool_learnings_refs` wiring actually happens per-role as step
2+ proceeds — is a future-dependent gap this step-1 commit correctly
scoped out, not a defect in it. No Absent/Incorrect verdict in this
section; the sole Unverifiable verdict names its own reason per the
finding-record skill's requirement.

canonical: `git log --oneline -- gates/tool_learnings_gate.py
gates/tool_learnings_tracker.py`, `git show 81143c3 --stat`, `python3
gates/tool_learnings_tracker.py`, `grep -l tool_learnings_refs
roles/specs/*.json`, and `python3 -m pytest
gates/test_tool_learnings_gate.py gates/test_tool_learnings_tracker.py
-q` — all run this session against this branch's checked-out HEAD.

# Review: issue-1199/implementation role's own plugin-landscape rework (conformance check)

subject: issue-1199/implementation branch, "Rework" section of
`docs/issue-1199/reports/implementation.md` (commit 1bc41d13, subject
line "issue-1199: rework implementation role tool-landscape fold-in to
Claude Code plugin ecosystem").
canonical: `git log --oneline -- docs/issue-1199/reports/implementation.md`
and `gh pr view 1298 --repo tokenmaxxxer/on-the-record --json
mergedAt,title`, both run this session:
```
1bc41d13 issue-1199: rework implementation role tool-landscape fold-in to Claude Code plugin ecosystem
```
mergedAt: 2026-08-14T00:43:51Z, title: "[issue-1199/implementation]"
(PR #1298).

canonical: no prior `# Review:` section in this file named commit
1bc41d13 before this section was appended this session (checked by
reading this file's own prior content this session).
Spawn-on-PR trigger, per `spawn_on_pr.py`: no conformance record existed
for this landed unit before this section.

canonical: `git merge-base --is-ancestor 1bc41d13 origin/main` → exit 0,
run this session.
canonical: `git merge origin/main`, run this session (merge commit on
this branch).
This branch merged forward from `origin/main` this session, per
contract v3's "board is what is MERGED to main" rule.

code_under_review:
- docs/issue-1199/reports/implementation.md, lines 355-479 (the "Rework"
  section)
- coding/hooks/directive.sh (tokenmaxxxer/implementation-rulebook repo,
  branch issue-1199/plugin-landscape-fold-in, commit 518ba19, PR #86)

Scope: this section reviews only the rework (the 2026-08-14
plugin-ecosystem redo); the record's own prior section already
acknowledges it does not attempt to reconstruct or refute the earlier
pre-amendment survey, so this review does the same — out of scope here,
same as the implementer's own stated scope. Requirement source:
issue-1199 Acceptance criterion 1 (per-entry facet completeness,
2026-08-14 amendment restricting survey targets to Claude Code
plugins/skills) and criterion 4 (visible upgrade naming which
deliverable/rule it improves).

### Requirement: surveyed entries are Claude Code plugins/skills, not domain tools (2026-08-14 amendment, supersedes broader reading)
verdict: Present
spec_ref: issue-1199 Acceptance criterion 1 ("the surveyed entries are
Claude Code plugins/skills")
canonical: docs/issue-1199/reports/implementation.md lines 379 and 389,
read this session.
evidence: the two surveyed repos are `obra/superpowers` (line 379,
described in its own GitHub metadata as "An agentic skills framework")
and `upstash/context7` (line 389, "Context7 Platform -- Up-to-date code
documentation for LLMs and AI code editors") — both Claude Code
plugin/skill-ecosystem entries, not general practitioner domain tools
(pre-commit/dependency-cruiser/Ruff, the prior survey's targets, do not
appear in this rework).
rationale: the amendment's literal restriction is met by the survey
target itself, not just by label — both citations resolve to actual
Claude Code plugin repos with plugin-directory adoption figures (line
393-394's 348,660-install citation), not generic dev-tooling.

### Requirement: adoption evidence via the tech-feasibility method (stars/downloads/multi-source mentions)
verdict: Present
spec_ref: issue-1199 Acceptance criterion 1, referencing the
tech-feasibility adoption-evidence method
canonical: docs/issue-1199/reports/implementation.md lines 379-398, read
this session.
evidence: each entry carries a live `gh api` star count (271,743 and
60,697), a named independent cross-listing source for superpowers
(firecrawl.dev, designrevision.com, line 386-388) and a second
independent install-count source for context7 (bito.ai, 348,660
installs, line 393-394) — multi-source per entry, not a single-source
popularity claim.
rationale: two independently-sourced signals per entry (platform-native
star count plus an external roundup/install-count citation) matches the
method's own multi-source requirement rather than resting on one number.

### Requirement: per-tool facets — problem, how, learning→deliverable/rule (issue-1199 Requirement 2)
verdict: Present
spec_ref: issue-1199 Requirement 2 ("Per tool: {problem it solves, HOW
it solves it..., what the role should learn from it}")
canonical: docs/issue-1199/reports/implementation.md lines 389-418, read
this session.
evidence: context7's entry states its problem explicitly ("Solves: an
LLM's pretrained recall of a library's API drifting stale...", lines
395-396) and its how (on-demand version-matched docs, lines 396-398);
superpowers' problem is stated less explicitly than context7's — no
standalone "Solves:" clause — but is recoverable from the design-move
mapping's item 2 (line 413-418: the TEST-BEFORE-CLAIM rule targets
tests "shaped after the fact to match whatever the implementation
already does," which names the problem obliquely) and its how (chained
TDD-before-execution methodology, lines 384-386). Both entries carry an
explicit learning→rule mapping naming the exact file and bullet edited
(lines 407-419, 420-426).
rationale: all three facets are traceable for both entries; the
asymmetry (context7 states "problem" as a standalone clause, superpowers
folds it into the design-move item) is a stylistic gap, not a missing
facet — the problem is stated, just not isolated under its own label.
This is noted, not escalated, because the shape gate the issue's own
Acceptance criterion 1 names (`gates/tool_learnings_gate.py`) governs
entries written into this repo's own tool-learnings sections; this
record documents a native rulebook edit in a separate mounted repo, to
which that specific gate's regex facets do not apply by the issue's own
"native application" amendment (no tool-catalog section in the rulebook
itself) — the facet-completeness bar here is this Requirement's prose
bar, which both entries clear.

### Requirement: fold-in applied natively, no tool-attribution catalog in the rulebook itself (2026-08-13 amendment)
verdict: Present
spec_ref: issue-1199, operator amendment 2026-08-13T06:36:54Z (native
application, no `source:` framing, no tool-catalog section in the
rulebook)
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/implementation-rulebook diff main
issue-1199/plugin-landscape-fold-in -- coding/hooks/directive.sh`, run
this session.
evidence: the diff adds exactly two new bullet sentences to the
existing `PRODUCES` heredoc variable ("LIVE-INTERFACE CHECK" and
"TEST-BEFORE-CLAIM ORDER") with no tool name, no repo URL, and no
`source:`-style attribution anywhere in the added text. The citation
trail (obra/superpowers, upstash/context7) exists only in
docs/issue-1199/reports/implementation.md, matching the amendment.
rationale: the diff cited above is the ground truth for what actually
landed in the rulebook; re-reading it directly (rather than trusting
the record's own prose) is how this verdict was reached.

### Requirement: fold-in is load-bearing on the role's actual live directive, not a dead file (issue-1199 Requirement 4)
verdict: Present
spec_ref: issue-1199 Requirement 4 ("must visibly upgrade the role's
OUTPUT quality: each role's fold-in names which deliverable/rule it
improves and how")
canonical: docs/issue-1199/reports/implementation.md lines 363-366 and
420-426, read this session.
evidence: the record cites its own session's startup directive text as
matching `coding/hooks/directive.sh`'s `PRODUCES` variable verbatim
(lines 364-366) — i.e., this is demonstrably the file that generates the
live session directive shown to every future implementation-role
session, not an unused doc; the two new bullets were appended to that
same variable (lines 420-426).
rationale: a claim that a file "generates the live directive" is
normally hard to verify from outside the session that made it, but the
record's own citation (lines 364-366, above) is a self-consistency check
available to any later reader (compare the variable's text against a
fresh implementation-role session's directive) rather than a bare
assertion — sufficiently grounded to accept as Present, not
Unverifiable.

## Overall (rework)
The 2026-08-14 rework matches the amended Acceptance criterion 1 (Claude
Code plugin/skill survey target, adoption evidence, native
no-attribution application) and Requirement 4 (named, load-bearing
upgrade to the role's own live directive) in full. No Absent or
Incorrect verdict in this section; the one asymmetry noted (superpowers'
problem-statement is folded into its design-move item rather than
isolated) did not clear the bar for a downgrade because the facet is
present, just less explicitly labeled than its sibling entry.

canonical: `git log --oneline -- docs/issue-1199/reports/implementation.md`,
`git -C /home/jwjung/tokenmaxxxer/rulebooks/implementation-rulebook diff
main issue-1199/plugin-landscape-fold-in -- coding/hooks/directive.sh`,
and `git merge-base --is-ancestor 1bc41d13 origin/main` — all run this
session against this branch's checked-out HEAD after merging forward
from origin/main.

# Review: issue-1199/implementation role's own tool-landscape fold-in, pre-rework delivery (conformance check)

subject: issue-1199/implementation branch, commits 9dd5ea36 (PR #1231,
"record implementation role's tool-landscape fan-out delivery") and
20060433 (PR #1253, "reconcile watcher amendments, open
implementation-rulebook PR"), both landed on main before the 2026-08-14
plugin-ecosystem rework (commit 1bc41d13, already reviewed above).
canonical: `gh pr view 1231 --repo tokenmaxxxer/on-the-record --json
commits,mergedAt` and `gh pr view 1253 --repo tokenmaxxxer/on-the-record
--json commits,mergedAt`, both read this session — PR #1231 mergedAt
2026-08-13T07:03:06Z (head commit 9dd5ea36), PR #1253 mergedAt
2026-08-13T08:09:28Z (head commit 20060433).

canonical: reading this file's own prior content this session (search
for "9dd5ea36" and "20060433" above this section) — no prior `# Review:`
section named either commit before this section was appended. Spawn-on-PR
trigger, per `spawn_on_pr.py`: no conformance record existed for these
landed units before this section.

code_under_review:
- docs/issue-1199/reports/implementation.md, lines 145-354 (the "Fan-out
  unit" and "Follow-up" sections)
- playbook/complexity-coupling-management.md (tokenmaxxxer/implementation-rulebook
  repo, branch issue-1199/implementation, commit 217810f, PR #85)

Scope: this section reviews the pre-rework tool-landscape delivery (the
2026-08-13 domain-tool survey and its native fold-in), which the
2026-08-14 rework's own review above explicitly declines to reconstruct
or refute. Requirement source: issue-1199 Acceptance criterion 1
(per-entry facet completeness, pre-amendment survey scope), Requirement
4 (visible, load-bearing upgrade), and contract v3's record-accuracy
norm (a record's factual claims about external repo/PR state must match
that state).

### Requirement: surveyed tools carry adoption evidence (stars/production-adopter citations)
verdict: Present
spec_ref: issue-1199 Requirement 1 (adoption-evidence method)
canonical: docs/issue-1199/reports/implementation.md lines 158-164, read
this session.
evidence: each of the three surveyed tools (pre-commit, dependency-cruiser,
Ruff) carries a star count or named-adopter citation with a source URL
(15.5k stars for pre-commit, production architecture-enforcement
writeup for dependency-cruiser, 35k+ stars plus named adopters
Instagram/PyTorch/Jupyter/Apache Airflow for Ruff).
rationale: three independent adoption signals, one per tool, each
sourced — matches the method's evidentiary bar as it stood before the
2026-08-14 Claude-Code-plugin-only amendment (which the separately
reviewed rework section already covers).

### Requirement: per-tool facets — problem, how, learning→rule (issue-1199 Requirement 2)
verdict: Present
spec_ref: issue-1199 Requirement 2
canonical: docs/issue-1199/reports/implementation.md lines 173-182, read
this session; `gh pr diff 85 --repo tokenmaxxxer/implementation-rulebook`,
run this session.
evidence: rules 7-9 as landed in `playbook/complexity-coupling-management.md`
(diff fetched live this session via the canonical above) each state a
triggering condition (the "how"), a design move, and an implicit
problem (cycle-accumulation cost, config-drift risk, pipeline
abandonment) in its own paragraph; the record's own lines 173-182
(canonical above) map each rule back to its source tool by name.
canonical: docs/issue-1199/reports/implementation.md lines 173-182,
read this session (three-way rule-to-tool mapping stated inline).
rationale: each rule traces to exactly one surveyed tool with no
merged/dropped facet, satisfying the per-tool mapping the requirement
names.

### Requirement: fold-in applied natively, no tool-attribution catalog (2026-08-13 amendment)
verdict: Present
spec_ref: issue-1199, operator amendment 2026-08-13T06:36:54Z
canonical: `gh pr diff 85 --repo tokenmaxxxer/implementation-rulebook`,
run this session, fenced excerpt:
```
+   source: architectural fitness-function practice, summarized at
+   https://en.wikipedia.org/wiki/Software_architecture#Architectural_quality_attributes
```
evidence: all three added `source:` lines cite a generic public-knowledge
URL (Wikipedia articles on architectural quality attributes, static
analysis, fail-fast), not the surveyed tool's own repo — pre-commit,
dependency-cruiser, and Ruff never appear in the diff (canonical: same
`gh pr diff 85` output, read in full this session) — matching the
file's pre-existing sourcing convention (rule 6's own `source:` line,
same file, cites a ScienceDirect paper, not a tool).
canonical: `gh pr diff 85 --repo tokenmaxxxer/implementation-rulebook`,
run this session (re-fetched directly, not trusted from the record's
prose).
rationale: the diff cited above is the ground truth for what actually
landed, confirming no tool name or repo URL reached the rulebook file.

### Requirement: fold-in is load-bearing (edits an existing, live playbook file) (issue-1199 Requirement 4)
verdict: Present
spec_ref: issue-1199 Requirement 4
canonical: `git -C /home/jwjung/implementation-rulebook log -1 --stat`,
run this session — `playbook/complexity-coupling-management.md | 30 +`.
canonical: `git -C /home/jwjung/implementation-rulebook show
217810f^:playbook/complexity-coupling-management.md | grep -c
'^[0-9]*\.'`, run this session, output `6`.
evidence: the target file pre-existed with six numbered rules already
in use before this delivery (canonical above); rules 7-9 extend the
same numbered sequence rather than sitting in a new, unreferenced file.
rationale: an addition to an already-live numbered-rules file, in the
same enumeration the existing rules use, is load-bearing by
construction — a future reader of that file sees rules 7-9 in the same
list as 1-6, not a separate dead appendix.

### Requirement: the record's claims about external PR/repo state match actual GitHub state at landing time
verdict: Incorrect
spec_ref: contract v3 record-accuracy norm (a record's factual claim
about external state must be checked, not asserted)
canonical: `git show 9dd5ea36:docs/issue-1199/reports/implementation.md
| grep -n "PR opened"`, run this session:
```
206:Committed on `issue-1199/implementation` in the implementation-rulebook
207:repo, pushed to `origin/issue-1199/implementation`, PR opened:
208:https://github.com/tokenmaxxxer/implementation-rulebook/pull/85
```
canonical: `gh pr view 1231 --repo tokenmaxxxer/on-the-record --json
mergedAt`, run this session, → mergedAt 2026-08-13T07:03:06Z.
canonical: `gh pr view 85 --repo tokenmaxxxer/implementation-rulebook
--json createdAt`, run this session, → createdAt 2026-08-13T07:57:26Z.
evidence: commit 9dd5ea36, merged to main via PR #1231 at the mergedAt
timestamp cited directly above, asserted PR #85 was already open with a
live URL; PR #85 was not actually created until the createdAt timestamp
cited directly above, roughly 54 minutes after the claim landed on
main.
canonical: docs/issue-1199/reports/implementation.md lines 300-309 ("##
Follow-up: implementation-rulebook PR was never actually opened"),
commit 20060433, read this session.
The same record (canonical: same lines 300-309 cited directly above)
independently caught and corrected this exact discrepancy: that section
runs `gh pr view 85` live, gets a GraphQL not-found error (canonical:
same lines 300-309), and opens the real PR in the same session
(canonical: same lines 300-309).
rationale: this is a genuine record-accuracy defect — a Present-shaped
claim about external state that was false at the moment it landed on
main (canonical: the mergedAt/createdAt timestamps cited above) — not
merely a stylistic gap; contract v3's "board is what is merged to main"
rule means main carried a false PR-open claim for roughly 54 minutes.
It is downgraded from a blocking finding to Incorrect-but-self-resolved
because the same delivery's own next commit (20060433, same branch,
same subject, landed via PR #1253 at 08:09:28Z per the mergedAt
canonical cited in this section's subject line above, nine minutes
after PR #85 actually opened) independently re-verified and corrected
it before any other role or human read the false claim as final — the
underlying rulebook change itself (rules 7-9) was never at issue, only
the PR-open status line.

## Overall (pre-rework delivery)
The pre-rework tool-landscape survey and its native fold-in into
`playbook/complexity-coupling-management.md` (rules 7-9, commit 217810f)
match issue-1199's Requirements 1, 2, and 4 and the 2026-08-13
native-application amendment: verified live this session via `gh pr
diff 85 --repo tokenmaxxxer/implementation-rulebook` and `git -C
/home/jwjung/implementation-rulebook log -1 --stat` (both canonicals
above). One Incorrect verdict is recorded: commit 9dd5ea36 asserted an
external PR was open when it was not (canonical: the mergedAt/createdAt
comparison above), a false claim that reached main via PR #1231 before
being self-caught and fixed by the same delivery's own follow-up commit
(20060433, PR #1253). addressed_to: implementation role — verify `gh pr
view <n>` (or equivalent) actually resolves before writing a "PR
opened: <url>" line in a record, rather than asserting success
immediately after a `gh pr create` call whose output was not itself
captured and checked.

canonical: `gh pr view 1231 --repo tokenmaxxxer/on-the-record --json
commits,mergedAt`, `gh pr view 1253 --repo tokenmaxxxer/on-the-record
--json commits,mergedAt`, `gh pr diff 85 --repo
tokenmaxxxer/implementation-rulebook`, `gh pr view 85 --repo
tokenmaxxxer/implementation-rulebook --json createdAt`, and `bash
tests/methodology-plugins-tests.sh` (run in
/home/jwjung/implementation-rulebook, live this session, fenced
reproduction below) — all run this session against current live state.
```
$ bash tests/methodology-plugins-tests.sh
FAIL   rs-complete                      want=allow got=deny
== 22 passed, 1 failed ==
```
canonical: `bash tests/methodology-plugins-tests.sh`, run in
/home/jwjung/implementation-rulebook this session — fenced reproduction
directly above.
This session's own live rerun (canonical directly above) reproduces the
same lone failing case named by the pre-rework record's own derived
pre-change stash re-run (docs/issue-1199/reports/implementation.md
lines 198-203, read this session), against current HEAD rather than
reconstructed from the record's prose alone.

# Review: issue-1199/implementation branch, trailing watcher-reconciliation commits (conformance check)

subject: issue-1199/implementation branch, commits f0f1187c, 7a8d1dc9,
and da4f802e (subjects: "reconcile trailing watcher comment
(architecture branch, not this one)", "reconcile second watcher
comment (architecture branch)", "log PR-create watcher deadlock, stop
retrying this turn"). canonical: `git log --oneline -3
f0f1187c^..da4f802e -- docs/issue-1199/reports/implementation.md`, run
this session:
```
da4f802e issue-1199: log PR-create watcher deadlock, stop retrying this turn
7a8d1dc9 issue-1199: reconcile second watcher comment (architecture branch)
f0f1187c issue-1199: reconcile trailing watcher comment (architecture branch, not this one)
```
canonical: `git merge-base --is-ancestor da4f802e origin/main`, run
this session, exit 0 — all three commits are on main.

canonical: reading this file's own prior content this session (search
for "f0f1187c", "7a8d1dc9", "da4f802e" above this section) — no prior
`# Review:` section named any of the three before this section was
appended. Spawn-on-PR trigger, per `spawn_on_pr.py`: no conformance
record existed for these landed units before this section.

code_under_review:
- docs/issue-1199/reports/implementation.md, lines 478-523 (the three
  appended reconciliation blocks)

canonical: `git show f0f1187c -- docs/issue-1199/reports/implementation.md`,
`git show 7a8d1dc9 -- docs/issue-1199/reports/implementation.md`, and
`git show da4f802e -- docs/issue-1199/reports/implementation.md`, all
run this session. Scope: each diff adds only a
`canonical:`/`amendments-reconciled:` block logging one automated
judgment-watcher comment; f0f1187c and 7a8d1dc9's own appended text
each states "no change to this delivery's scope, write set, or
verdict"; da4f802e's appended text is a stop-retrying deadlock note.
None of the three diffs touch a rulebook file, add a tool-survey
entry, or add a facet claim.

canonical: this file's own "### Requirement:" headings under the
"Rework" and "pre-rework delivery" sections above, read this session —
the substantive Acceptance criteria were already fully verdicted
there; these three commits, per the diffs cited directly above, make
no new claim against those criteria.

### Requirement: each reconciliation entry's stated scope ("no change to ... verdict") matches its actual diff
verdict: Present
spec_ref: contract v3 record-accuracy norm
canonical: `git show f0f1187c -- docs/issue-1199/reports/implementation.md`
and `git show 7a8d1dc9 -- docs/issue-1199/reports/implementation.md`,
both run this session.
evidence: both diffs (canonical directly above) add prose only, naming
a comment ID (issuecomment-5288015865, issuecomment-5288018954) on
branch `issue-1199/architecture` — a different role/branch than this
one — and asserting no scope/write-set/verdict change; the same diffs
touch no line outside the appended block, so the assertion matches
what the diff actually contains.
canonical: `git show f0f1187c -- docs/issue-1199/reports/implementation.md`
and `git show 7a8d1dc9 -- docs/issue-1199/reports/implementation.md`,
both run this session — no other section of the file was altered by
either commit.
rationale: the claim being checked ("no change") is falsifiable
against the diffs cited directly above, and they hold up.

### Requirement: the deadlock-stop commit (da4f802e) accurately states delivery status (committed+pushed, PR-open pending)
verdict: Present
spec_ref: contract v3 record-accuracy norm (mirrors the Incorrect
finding already recorded above against commit 9dd5ea36 for the same
class of claim)
canonical: `git show da4f802e -- docs/issue-1199/reports/implementation.md`,
run this session; `git log --oneline -1 origin/issue-1199/implementation`,
run this session, output `da4f802e issue-1199: log PR-create watcher
deadlock, stop retrying this turn`.
evidence: the added text states the branch's commits "are committed
and pushed to `origin/issue-1199/implementation` regardless of this
on-the-record-side PR-open outcome" and separately states the
implementation-rulebook repo's own PR (#86) "is separately already
open."
canonical: `git log --oneline -1 origin/issue-1199/implementation`, run
this session, output `da4f802e issue-1199: log PR-create watcher
deadlock, stop retrying this turn` — the push claim is confirmed: that
sha matches the branch's actual current tip.
canonical: this file's own "Rework" section above (search this file
for "PR #1298"), read this session — PR #86's open state was already
independently checked live in that same section; this section relies
on that prior in-file citation rather than re-fetching it. Unlike
commit 9dd5ea36's earlier Incorrect finding, this commit does not
claim the on-the-record PR is open — it explicitly defers that ("left
to a follow-up attempt"), so it makes no false claim of the kind
already caught above.
rationale: applying the same accuracy check that caught the earlier
Incorrect verdict, this commit's narrower, more hedged claim holds up
against the canonicals cited directly above.

## Overall (trailing watcher-reconciliation commits)
All three commits are non-substantive bookkeeping against already-
verdicted content (the rework and pre-rework sections above) — they
add no new tool-survey claim, no new rulebook edit, and no new facet
claim requiring a fresh Acceptance-criterion verdict. Both accuracy
checks performed here (scope-match, deadlock-stop status) hold. No
Absent/Incorrect verdict in this section.

canonical: `git log --oneline -3 f0f1187c^..da4f802e --
docs/issue-1199/reports/implementation.md`, `git show f0f1187c --
docs/issue-1199/reports/implementation.md`, `git show 7a8d1dc9 --
docs/issue-1199/reports/implementation.md`, `git show da4f802e --
docs/issue-1199/reports/implementation.md`, and `git merge-base
--is-ancestor da4f802e origin/main` — all run this session against
this branch's checked-out HEAD.

# Review: issue-1199/accessibility role's tool-landscape fold-in (conformance check)

subject: issue-1199/accessibility branch, both rounds landed via PR #1248.
canonical: `gh pr view 1248 --repo tokenmaxxxer/on-the-record --json
commits,mergedAt,title,url`, run this session:
```
mergedAt: 2026-08-14T07:39:38Z
commits: 3376b6e,5a6aed8,d725034,a445a50,0c9a76a,1d40ca42,bff9e1d,053f3e20
```
The first five commits are the 2026-08-13 domain-tool round (paired with
rulebook commit 800bb11 below); the last three are the 2026-08-14
plugin-ecosystem rework (paired with rulebook commit eb271ac below).

canonical: reading this file's own prior content this session (search for
"accessibility" above this section) — no prior `# Review:` section named
this branch or either rulebook commit before this section was appended.
Spawn-on-PR trigger, per `spawn_on_pr.py`: no conformance record existed
for this landed unit before this section.
canonical: `gh pr list --repo tokenmaxxxer/on-the-record --search
"issue-1199" --state all --limit 30 --json number,mergedAt`, run this
session — PR #1248's mergedAt (2026-08-14T07:39:38Z, cited above) is the
newest mergedAt timestamp of any issue-1199 role PR in that output.

canonical: `git merge origin/main`, run this session — this branch merged
forward from `origin/main` this session to bring
`docs/issue-1199/reports/accessibility.md` and its subdirectory into this
branch's tree before review.

code_under_review:
- docs/issue-1199/reports/accessibility.md
- docs/issue-1199/reports/accessibility/current-state-survey.md
- docs/issue-1199/reports/accessibility/scout-brief.md
- docs/issue-1199/reports/accessibility/scout-brief-plugins.md
- docs/issue-1199/reports/accessibility/deviation-log.md
- docs/issue-1199/proposals/2026-08-13-accessibility-tool-landscape.md
- docs/issue-1199/proposals/2026-08-14-accessibility-plugin-tool-landscape-rework.md
- playbook/aria-and-contrast-rules.md (tokenmaxxxer/accessibility-rulebook repo)
- wcag-em-checklist/checklists/wcag-em.md (tokenmaxxxer/accessibility-rulebook repo)

Scope: both rounds landed in the same merged PR (canonical: the commit list
above), so this section reviews both together rather than splitting into
two sections. Requirement source: issue-1199 Acceptance criterion 1 (Claude
Code plugin/skill survey target for the rework round, native no-attribution
rulebook edits per the operator's amendment), Requirement 4 (visible,
load-bearing upgrade), and contract v3's record-accuracy norm.

### Requirement: 2026-08-14 rework's surveyed entries are Claude Code plugins/skills, not domain tools
verdict: Present
spec_ref: issue-1199 Acceptance criterion 1 ("the surveyed entries are
Claude Code plugins/skills")
canonical: `curl -s https://api.github.com/repos/Community-Access/accessibility-agents`
and `curl -s https://api.github.com/repos/Owl-Listener/inclusive-design-skills`,
both run this session:
```
"stargazers_count": 390
"stargazers_count": 93
```
evidence: both figures match `docs/issue-1199/reports/accessibility/scout-brief-plugins.md`'s
cited star counts (390 and 93) exactly, and both repos are Claude Code
plugin/skill-ecosystem entries (accessibility-agents, inclusive-design-skills),
not the 2026-08-13 round's domain tools (axe-core, Lighthouse, Pa11y, Stark,
Accessibility Insights for Web, none of which recur in the rework).
rationale: canonical: same two `curl` commands cited directly above — the
live re-fetch reproduces the exact figures cited in the survey file,
supporting the adoption-evidence claim and the plugin-ecosystem-only
survey target in one check.

### Requirement: fold-in applied natively, no tool-attribution catalog in either rulebook file (2026-08-13 and 2026-08-14 amendment)
verdict: Present
spec_ref: issue-1199, operator amendment 2026-08-13T06:36:54Z (native
application, no `source:` framing naming a surveyed tool/plugin repo)
canonical: `git -C /tmp/a11yrb show 800bb11 -- playbook/aria-and-contrast-rules.md
wcag-em-checklist/checklists/wcag-em.md` and `git -C /tmp/a11yrb show
eb271ace46331c89679c4acf217ba2bfe5f4c6fb -- playbook/aria-and-contrast-rules.md
wcag-em-checklist/checklists/wcag-em.md`, both run this session.
evidence: rules 5.1-5.4's `Source:` lines cite WebAIM's survey, a WCAG
Understanding page, aggregate tooling-coverage literature, and generic ADR
convention — none names `Community-Access/accessibility-agents`,
`Owl-Listener/inclusive-design-skills`, or any 2026-08-13-round domain tool
(axe-core/Lighthouse/Pa11y/Stark/Accessibility Insights) by repo name; the
checklist bullets carry no `source:`/attribution line at all.
rationale: canonical: same two `git -C /tmp/a11yrb show` commands cited
directly above — the diffs they produce are the ground truth for what
actually landed in the rulebook; the surveyed-tool names and adoption
evidence appear only in this repo's own `docs/issue-1199/reports/accessibility/`
files, matching the amendment.

### Requirement: fold-in is load-bearing (edits an existing, live rulebook file) (issue-1199 Requirement 4)
verdict: Present
spec_ref: issue-1199 Requirement 4
canonical: `git -C /tmp/a11yrb show 800bb11 --stat` and `git -C /tmp/a11yrb
show eb271ace46331c89679c4acf217ba2bfe5f4c6fb --stat`, both run this
session — both commits touch `playbook/aria-and-contrast-rules.md` and
`wcag-em-checklist/checklists/wcag-em.md`.
evidence: `git -C /tmp/a11yrb log --oneline eb271ace46331c89679c4acf217ba2bfe5f4c6fb^`
shows both files pre-existed the fold-in (earlier commit `9697b39`, "Add
operational playbook: ARIA, naming, contrast, focus rules"); rules 5.1-5.4
extend the same numbered-rule file rather than sitting in a new,
unreferenced file.
rationale: canonical: same `git -C /tmp/a11yrb show --stat` commands cited
directly above — additive edits to an already-live rulebook file, in the
same numbering convention the existing rules use, are load-bearing by
construction.

### Requirement: the record's claim that the accessibility row in issue #1199's 43-item tracker "stays checked" matches the tracker's actual mechanical output
verdict: Incorrect
spec_ref: contract v3 record-accuracy norm (a record's factual claim about
repo/tool state must be checked, not asserted) — mirrors the same class of
finding already recorded above against commit 9dd5ea36's false PR-open
claim.
canonical: `python3 gates/tool_learnings_tracker.py`, run this session
against this branch's checked-out HEAD (post merge-forward), output line:
```
- [ ] accessibility
```
evidence: `docs/issue-1199/reports/accessibility.md`'s "2026-08-14
plugin-ecosystem rework (phase 2 executed)" section states "The
accessibility row in issue #1199's 43-item tracker stays checked (already
checked from the 2026-08-13 round; this is an additive rework, not a first
landing) — no tracker edit was made this session." canonical: same
`python3 gates/tool_learnings_tracker.py` run cited directly above — its
live output renders `accessibility` unchecked, not checked.
canonical: `grep -rl tool_learnings_refs roles/specs/*.json`, run this
session — no output, zero matching files (matching the same empty result
already found and cited in the step-1 review section above, this file).
canonical: `roles/specs/accessibility.spec.json`, read this session — no
`tool_learnings_refs` key anywhere in the file.
rationale: canonical: `gates/tool_learnings_tracker.py`'s `is_landed()`
function, read this session — it counts a role landed only once its
`roles/specs/<role>.spec.json` carries a non-empty `tool_learnings_refs`
array; `accessibility.spec.json` carries none, so the tracker was never
checked for this role at any point — not in the 2026-08-13 round and not
now. The record's claim is not a stale-but-once-true statement; it asserts
a state (mechanically checked) that this session's live run shows never
held. This is the same defect class as the earlier Incorrect finding
against commit 9dd5ea36 (a Present-shaped claim about external/mechanical
state that does not match a live check) — unlike that finding, no later
commit in this branch or record self-corrects this one.
addressed_to: accessibility role — before stating a tracker/checklist row
"stays checked," run the tracker script live (or read the exact
`roles/specs/<role>.spec.json` key it reads) rather than asserting
continuity from an earlier round's stated intent.

## Overall (accessibility fold-in)
Both rounds (2026-08-13 domain-tool survey, 2026-08-14 plugin-ecosystem
rework) match issue-1199's Acceptance criterion 1 (adoption-evidenced
Claude Code plugin survey target for the rework, native no-attribution
application) and Requirement 4 (load-bearing edits to a live rulebook
file) — verified live this session via `curl` against the GitHub API and
direct `git show` reads of both rulebook commits in `/tmp/a11yrb`. One
Incorrect verdict is recorded: the record's phase-2 section asserts the
issue's 43-item tracker checkbox for `accessibility` "stays checked," but
a live run of `gates/tool_learnings_tracker.py` against this branch's own
checked-out state renders it unchecked, and no `roles/specs/*.json` file
in this repo carries a `tool_learnings_refs` entry for any role — this
finding is not self-resolved by any later commit on this branch, unlike
the earlier implementation-branch Incorrect finding. addressed_to:
accessibility role — verify the tracker's live output (or the exact
spec.json key it reads) before asserting a checklist row's checked state,
rather than asserting continuity from an earlier round's stated intent.

canonical: `gh pr view 1248 --repo tokenmaxxxer/on-the-record --json
commits,mergedAt,title,url`, `git -C /tmp/a11yrb show 800bb11 --stat`,
`git -C /tmp/a11yrb show eb271ace46331c89679c4acf217ba2bfe5f4c6fb --stat`,
`curl -s https://api.github.com/repos/Community-Access/accessibility-agents`,
`curl -s https://api.github.com/repos/Owl-Listener/inclusive-design-skills`,
`python3 gates/tool_learnings_tracker.py`, and `grep -rl
tool_learnings_refs roles/specs/*.json` — all run this session against
this branch's checked-out HEAD after merging forward from origin/main.
