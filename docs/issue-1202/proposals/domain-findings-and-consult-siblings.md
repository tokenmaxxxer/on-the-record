---
status: proposed
files:
  - docs/reports/findings/<role>/<date>-<slug>.md   # new advisory queue, per finding
  - gates/finding_shape.py                          # new: shape gate (requirement 2)
  - gates/findings_due.py                           # new: board-reading formatter (requirement 4)
  - spawn.py                                         # new CLI verbs: findings-due, consult ideate/draft/review
  - on-the-record/commands/consult.md                # doc update: sibling verbs
  - gates/test_finding_shape.py
  - gates/test_findings_due.py
  - gates/test_consult_siblings.py
---

# Role-initiated domain findings + broadened help delegation (issue #1202)

## Intent

A role session can see a domain problem in its own domain that the
orchestrator, lacking that domain's judgment, cannot see coming. Today
the only path from "role sees a problem" to "board has an issue" runs
through the orchestrator noticing first — backwards, per the operator's
stated logic. Separately, delegation to a role for help beyond a single
judgment call (consult) does not exist as a routine ask.

## Constraints (from the issue + validity-consult 2026-08-13T06:14)

- Findings never file a `gh issue` directly — advisory queue only, the
  user still confirms into an issue (scribe rule).
- Every finding carries: domain rule violated (playbook citation),
  evidence (file/line or artifact) in the target repo, impact, proposed
  direction. A shape gate rejects anything missing citation or evidence.
- Bounded per session: N=3 findings; beyond the bound, one summary line,
  not more finding files.
- New consult-sibling verbs (ideate/draft/review) carry the same
  contract consult already has: traced every call, no branch/commit/PR.
- Reuse #1160's `needs_due`/`format_report` board-reading shape where
  it fits — no duplicate machinery.

## What will be done

### 1. Finding file shape

One file per finding, frontmatter + body:

```markdown
---
role: <role>
date: 2026-08-13
domain_rule: <playbook section/rule cited, verbatim short quote>
target_repo: <path or repo identifier>
---

## Evidence
<file:line or artifact path in the target repo>

## Impact
<one paragraph>

## Proposed direction
<one paragraph — direction, not a full spec>
```

`domain_rule` and `## Evidence` are the two fields `gates/finding_shape.py`
requires non-empty; either missing is a hard reject (mirrors
`gates/record_lint.py`'s pure-validator-over-parsed-doc pattern surveyed
above).

### 2. Queue location

**Decision: `docs/reports/findings/<role>/<date>-<slug>.md`**, not the
issue text's literal `docs/findings/<role>/`. Reasoning: every existing
advisory path in this repo (consult-log, panel) lives inside the six
standing buckets; a bare top-level `docs/findings/` would be the first
bucket exception and would need its own contract-v3 carve-out with no
stated reason to diverge. `docs/reports/findings/<role>/` keeps the
literal `<role>/<date>-<slug>.md` shape the issue asks for, inside
`reports/`, matching `consult-log.md`'s no-issue fallback branch. A
role working under a specific issue may additionally write into
`docs/issue-<n>/reports/findings/<role>/` when the finding is
issue-scoped — same fallback-branch pattern `_consult_trace_path()`
already uses.

### 3. Shape gate (`gates/finding_shape.py`)

Pure function, same family as `record_lint.py`/`role_spec_shape.py`:
`check_finding(path) -> list[str]` (empty = passes). Wired as a
pre-commit-style gate (same mechanism `record-claim-guard.sh` already
uses) that runs on any staged path under
`docs/**/findings/<role>/**.md`. Rejects: missing `domain_rule`,
missing/empty `## Evidence` body, missing `## Impact`, missing
`## Proposed direction`.

### 4. Rate bound (N=3/session)

A role session counts findings it writes in `$SESSION_ID` (already
available to hook/gate scripts per this repo's existing session-scoping
convention) by counting new files under the findings glob it staged
this session. On the 4th attempt within the same session, the gate
rejects the file write and the role instead appends one line to
`docs/reports/findings/<role>/<date>-session-summary.md`:
`- <n> further findings observed, not filed (session bound N=3)`. This
mirrors the record-tiering directive's "bare marker, no padding" shape
already in force for `## What did not work`. Bound counts per-session,
not cumulative against the standing queue — a fresh session gets a
fresh N=3, since the bound exists to force depth-over-volume triage
within one look, not to cap the queue's total size.

### 5. Board-reading integration (`gates/findings_due.py`)

Mirrors `gates/need_detector.py`'s two-function shape exactly:
`findings_due(target_root) -> list[dict]` (scans
`docs/reports/findings/*/`.md` + `docs/issue-*/reports/findings/*/*.md`
for un-relayed entries — a finding is "un-relayed" until a
`relayed_to_issue: <n>` field is appended to its frontmatter by the
orchestrator after user confirmation) and `format_report(due) ->
list[str]`. New `spawn.py findings-due` subcommand, same shape as the
existing `needs-due`/`roles-due` subcommands (`spawn.py:5254-5276`):
prints lines, never spawns, never files an issue. The orchestrator's
board-reading step adds this as a third advisory source alongside
roles-due/needs-due; when the user confirms a relayed line into a real
issue, the orchestrator (not the role) appends `relayed_to_issue:` —
this is the scribe-rule boundary: role discovers and queues, user
confirms, orchestrator records the confirmation.

### 6. Consult-sibling verbs (ideate / draft / review)

Same `consult_cmd()` session-assembly (`role_settings()`/
`plugin_dirs()`) and same unconditional trace-append
(`_append_consult_trace()`-style, one line per call regardless of
outcome), reusing the split panel already demonstrates between session
assembly and verb-specific prompt/record. New CLI surface:

```
python3 spawn.py consult <role> "<question>" [--issue <n>]      # existing
python3 spawn.py ideate <role> "<prompt>" [--issue <n>]
python3 spawn.py draft <role> "<what>" [--issue <n>]
python3 spawn.py review <role> "<what to review>" [--issue <n>]
```

Chosen as three top-level subcommands (matching `consult`'s own
top-level-subcommand shape, `spawn.py`'s existing dispatch style) rather
than a `consult <verb>` nested form — no dispatch-table precedent for a
nested verb argument exists in the current `main()` structure surveyed
above, and three flat subcommands cost one `if a.role == "..."` branch
each, the same cost `roles-due`/`needs-due` already paid.

Each verb differs only in prompt template and return shape:
- `ideate`: returns `{"options": [...], "tradeoffs": [...]}` — divergent
  options, not one verdict.
- `draft`: returns `{"draft": "<text>", "open_questions": [...]}` — a
  deliverable sketch, explicitly not a landed file (no write_scope
  applies; the caller decides whether to use it).
- `review`: returns `{"findings": [...], "verdict": "..."}` — structured
  feedback on caller-supplied text/diff, no repo write.

All four verbs share one trace file family
(`docs/issue-<n>/reports/consult-log.md`, extended with a `verb:` field
per line) — no separate trace file per verb, avoiding the drift the
`consult_cmd()` docstring already warns two split code paths would
cause.

## Out of scope

- Auto-filing a `gh issue` from a confirmed finding (requirement 4 keeps
  the user as the filer; only the confirmation UX is this issue's
  scope).
- Any change to the panel machinery's own multi-turn protocol.
- Retroactively backfilling findings for issues already on the board.

## How you will know it worked (acceptance, from the issue)

- A finding file with citation + evidence passes `finding_shape.py`; one
  missing either is rejected.
- A session's 4th finding is rejected with the summary-line path taken
  instead.
- `spawn.py findings-due` lists queued, un-relayed findings in the same
  report style as `roles-due`/`needs-due`.
- `ideate`/`draft`/`review` each return a traced JSON response with no
  branch/commit/PR side effect (extends the `test_consult_json_parse`
  family).
- Live: one real role session records a genuine finding on a fixture
  repo and the orchestrator relays it to the user for confirmation.

## Ambiguities resolved here

- **Queue path**: resolved to `docs/reports/findings/<role>/` (+
  per-issue variant) over the issue text's literal `docs/findings/`, to
  stay inside the six-bucket contract — see `## 2. Queue location`
  above for the reasoning.
- **Rate-bound scope**: resolved to per-session, not cumulative — see
  `## 4. Rate bound` above.
- **Verb dispatch shape**: resolved to three flat subcommands over a
  nested `consult <verb>` form — see `## 6. Consult-sibling verbs` above.

## Accumulation

Not accumulation-cost-shaped: this is new machinery (queue schema, gate,
one CLI subcommand family) layered beside existing advisory/consult
code, not a change whose cost compounds with existing call sites. No
`## Accumulation` content beyond this note applies.
