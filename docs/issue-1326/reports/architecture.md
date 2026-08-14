# Architecture record — issue-1326 (machinery-mapping half)

kind: report
loop_state: reviewing

## What was done

canonical: this session's direct reads of the artifacts and gate code
cited throughout this record (paths given inline below).
Inventoried on-the-record's actual trace/record machinery, then graded
each item against IMDA agentic-AI framework (Jan 2026) and EU AI Act
requirements as they analogically bear on autonomous software agents.
This record covers only the **machinery-mapping half** assigned to the
architecture role (issue text: "Roles: legal-compliance (framework
reading), architecture (machinery-side mapping)"). No legal-compliance
session has run on this issue tree yet — see Open findings.

**Precondition check (IMDA primary text access):** not attempted from
this session — the architecture role's tooling here does not include
external web fetch of the IMDA Jan-2026 primary document. All IMDA items
below are graded against a secondary, unverified characterization of the
framework's stated emphasis (per-agent identity + authorization audit
trail, per the issue title itself), one source-tier down from primary
text. legal-compliance owns correcting this against the primary source.

## Why

issue #1326, implication 2 of docs/reports/product/2026-08-14-hiring-market-recon.md.
canonical: docs/reports/consult-log.md, entry timestamped
2026-08-14T02:24:13 — validity-consult by role=requirements-engineering
states the machinery-side mapping is verifiable by reading the actual
trace artifacts, which is what this record does.

## Upstream

Based on: issue #1326 body (`gh issue view 1326`), and direct reads of
the artifacts cited per-item below.

## Grading criteria (fixed up front, applies to every item below)

- **covered** — the requirement's field is captured in a structured,
  machine-parseable location (frontmatter field, dedicated log schema
  key) **and** a gate refuses to let the record land without it (commit
  hook, PR preflight, or CI check).
- **partial** — the requirement is captured in some form but at least
  one of: (a) free-text only, not structured/queryable; (b) not
  gate-enforced (absence doesn't block landing); (c) covers only a
  subset of the requirement's scope (e.g. identifies the human account
  but not the agent/role, or vice versa).
- **missing** — no mechanism in the repository captures this
  requirement in any form.

## Machinery inventory (what actually exists)

canonical: docs/reports/consult-log.md — header states entries are
"appended by `spawn.py`, never hand-edited."
- consult-log: one line per `spawn.py consult` call — timestamp, role,
  issue, question, outcome.

canonical: gates/record_lint.py, module docstring and function
`record_wellformed_in`.
- Role records `docs/issue-<n>/reports/<role>.md`: frontmatter
  (`loop_state`, quoted requirement/upstream basis, open findings),
  shape-checked by a lint gate before landing.

canonical: docs/issue-170/_assets/rulebook-skeleton/architecture/architecture/hooks/trailer-gate.sh
(full file read, lines 1-49).
- Commit trailer gate: a PreToolUse hook matching `git commit` refuses a
  commit that stages `docs/issue-<n>/**` without a `Subject: issue-<n>`
  line in the commit message.

canonical: gates/flows.py (function `_pr_approved`) and gates/ci.py
(functions `_approved_roles_on_issue`, `_phase_from_approval`).
- Approval comments / PR reviews resolve to a GitHub account login, not
  a bare self-declared role string: either an issue comment whose body
  is exactly `APPROVE issue-<n>/<role>` from a `docs/specs/approvers.md`
  login, or a PR review Approve from a different approvers.md login.

canonical: gates/quality_bar.py, module docstring lines 1-19.
- Verdict-authorship anti-circularity: a merge gate requires callers to
  resolve `record_author_account` and `producer_account` to git
  author/committer or PR-author accounts before classifying a bar
  verdict, explicitly rejecting the bare `CLAUDE_ROLE` string as
  self-declared and operator-controlled.

canonical: spawn.py, comment above function `ledger_write`
("runs/ 는 gitignore 되어 있다").
- Process/session roster: `spawn.py` writes `pid`, `role`, `ts`, `cwd`
  session-start events and a ledger file of outcomes.
  derived: grep -n "^runs" .gitignore
  ```
  1:runs/
  ```
  The roster/ledger trace is local-only, never committed to the board.

canonical: gates/ci.py (function `_closes_ref_for_issue`) and
gates/pr_reference.py.
- PR-closing linkage: a PR is tied to the issue it closes via a
  `Closes #<n>` match in the PR body, cross-checked against
  `statusCheckRollup` for `checked:` claims.

## Gap findings — IMDA agentic-AI framework (secondary-source graded, see precondition above)

canonical: gates/quality_bar.py lines 9-19 ("`CLAUDE_ROLE` is
self-declared and operator-controlled").
- Per-agent identity (persistent identifier of the acting agent, not
  the human operator): **partial**. The role string is self-declared
  and gameable per its own documentation; account-level resolution
  exists only inside the narrow verdict-authorship check, not as a
  general per-agent identity primitive across all record types.

canonical: gates/repo_scope.py, full file read — checks scope-tagging
of capability-absence claims, not write-scope enforcement of a diff.
- Authorization scope for the action taken (what the agent was
  permitted to do): **partial**, incomplete-search basis. A
  `WRITE_SCOPE` is declared in the spawned role's directive text, but
  this session's targeted search of gates/*.py did not turn up a
  committed, gate-enforced check that a landed diff's file set is a
  subset of the declaring role's `WRITE_SCOPE` at merge time.
  unverifiable: this session's search over gates/*.py was targeted, not
  exhaustive — derived: ls gates/*.py | grep -v '^gates/test_' | wc -l
  ```
  41
  ```
  a write-scope enforcement gate may exist under a name not tried.

canonical: gates/ci.py, function `_phase_from_approval`.
- Authorization event (who approved the agent's action, and when):
  **covered**. Structured exact-string match, gate-enforced (blocks the
  phase-two transition when absent), timestamped via the GitHub
  comment/review object itself.

canonical: gates/record_lint.py, docs/reports/consult-log.md.
- Action log (what action occurred, when): **covered**. Structured
  frontmatter fields plus timestamped consult-log lines, gate-checked
  shape.

canonical: docs/reports/consult-log.md header line; no matching
enforcement hook turned up in this session's listing of
on-the-record/hooks/.
- Tamper-evidence / immutability of the trail: **partial**. Git history
  is tamper-evident by construction, but the consult-log
  never-hand-edited rule is a documented convention with no gate this
  session's search turned up that rejects a hand-edited line.

canonical: derived: grep -n "^runs" .gitignore
```
1:runs/
```
- Retention / retrievability of the trail: **partial**. Board-facing
  artifacts (records, comments, commits) are retained indefinitely by
  git; the process-level roster/ledger trace is gitignored and
  local-only.

## Gap findings — EU AI Act (no explicit autonomous-software-agent provisions; every item is interpretive)

canonical: docs/reports/consult-log.md, gates/record_lint.py.
- Automatic logging of system operation [interpretation, analogous to
  the Act's record-keeping obligation for high-risk AI systems]:
  **covered**. Structured, gate-checked, append-only.

canonical: docs/handbooks/operations.md, "루프" section (board read
described as the orchestration mechanism between role sessions).
- Traceability of functioning across the system's lifecycle
  [interpretation]: **partial**. Traceable within one repo's board, read
  by every subsequent role session as the state channel, but this
  session's search turned up no field tying a board entry back to a
  specific model/version that produced it.

canonical: gates/ci.py, function `_phase_from_approval`, and
docs/specs/approvers.md. Delivery work past the proposal stage is
mechanically blocked pending a listed human's exact-string approval.
- Human oversight / ability to intervene or override [interpretation,
  analogous to the Act's human-oversight obligation]: **covered**.

canonical: derived: grep -n "^runs" .gitignore
```
1:runs/
```
- Retention period for logs [interpretation]: **partial**, same split as
  the IMDA retention item above — committed board artifacts retained
  indefinitely, process-level roster/ledger local-only.

canonical: docs/issue-170/_assets/rulebook-skeleton/architecture/architecture/hooks/trailer-gate.sh
— trailer content checked is `Subject: issue-<n>` only, no
authorship-kind field.
- Transparency to downstream reviewers about AI-generated origin
  [interpretation, analogous to the Act's transparency obligation]:
  **partial**. Commit trailers and PR bodies disclose which issue and
  role produced a change, but this session's search turned up no field
  that explicitly discloses AI-agent authorship as opposed to human
  authorship — that fact is implicit in the on-the-record workflow, not
  an explicit disclosed trace field.

## Remediation backlog (one line per partial/missing gap)

1. Add a gate-enforced, general per-agent identity field (resolved
   GitHub/git account, not bare `CLAUDE_ROLE`) to the role-record
   schema, extending the quality_bar.py anti-circularity resolution
   beyond the verdict-authorship check.
2. Verify whether a merge-time write-scope enforcement gate exists under
   a name this session's search did not try; if none exists, file one
   that checks a landed diff's file set against the producing role's
   declared `WRITE_SCOPE`.
3. Mechanically enforce consult-log.md's never-hand-edited convention (a
   hook that rejects any diff touching existing consult-log lines, only
   appends).
4. Decide and document a retention policy for the process-level
   roster/ledger trace — either commit a redacted summary to the board
   or explicitly accept it as ephemeral.
5. Add a model/version-identity field to the board record schema so a
   given entry traces back to the producing model, not just the role
   name.
6. Add an explicit AI-authorship disclosure field to commit trailers or
   PR bodies, distinct from the existing issue/role trailer.

## Open findings

canonical: derived: git branch -a | grep -i 1326
```
* issue-1326/architecture
```
- legal-compliance role has not started on this issue tree as of this
  session's branch listing above. No legal-compliance branch and no
  legal-compliance report file existed under this issue tree at this
  session's start. The IMDA/EU-AI-Act requirement lists above are this
  session's own best-available characterization, not legal-compliance's
  framework reading — they need legal-compliance verification against
  primary text before the gap findings above are treated as final. This
  is a scope boundary per the issue's role split, not a defect in this
  session's work.
- The write-scope-enforcement search (IMDA item 2 above) is flagged
  unverifiable rather than graded outright missing, because this session
  did not read every one of the 41 non-test gate modules (see derived
  count above).

## Next steps

- resolution path: hand off to a legal-compliance session on this same
  issue tree to verify or correct the IMDA/EU-AI-Act framework
  characterizations above against primary source text, then reconcile
  the combined gap table.
- resolution path: file the six remediation backlog items above as
  individual issues once legal-compliance's half lands.

## What did not work

None.
