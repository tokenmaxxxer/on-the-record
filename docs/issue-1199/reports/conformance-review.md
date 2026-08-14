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
