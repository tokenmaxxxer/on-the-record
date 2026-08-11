# Phase-1 survey: gate-required shapes vs authoring-time sources (issue-726)

kind: survey
loop_state: survey-drafted
upstream: docs/issue-726/proposals/gate-shape-vs-authoring-source-audit.md

## Scope of this pass

This checkout (`on-the-record`) contains all gate hooks and their gate
logic. It does NOT contain `tokenmaxxxer-core` or any `*-rulebook` repo —
those are cloned per-session at spawn time into role sandboxes, not
present here. Per the issue, the authoring-time sources for role-session
directives live largely in those repos (confirmed directly: this very
session's SessionStart hooks injected "[conformance-review] Role
directive" and "[core] Interaction protocol ... contract v3" text that
has no file in this checkout — it is generated/fetched from
`tokenmaxxxer-core` + the role's rulebook at spawn time). So this pass
completes side A (gate shapes, full) and the LOCAL half of side B
(on-the-record's own templates/guidance); it flags, rather than
resolves, the cross-repo half of side B. Full MATCH/MISMATCH/GAP
resolution against `tokenmaxxxer-core`/`*-rulebook` needs those repos
checked out — that is phase-2 scope, proposed below.

## Side A — gate-enforced shapes (all hooks under on-the-record/hooks/*.sh, file:line, exhaustive)

Enumerated via `derived: find on-the-record/hooks -maxdepth 1 -name
'*.sh' | wc -l` (25 non-test hook files). Most have no hard
shape-mismatch deny/exit-2 path (advisory/state-only, listed at the
bottom); the rest enforce at least one required shape, listed below.

### accumulation-claim-guard.sh
- **:184-186** — a proposal touching an accumulation-cost shape (an
  inline-subprocess/gh-call pattern without a shared helper, repeated
  enough to matter, or a `roles/*.json` repeat-file edit) must carry a
  filled `## Accumulation` heading (issue #424/#512).
- **:252-253** — same check, re-applied against the committed proposal
  file when a `.py` write touches one of those same accumulation-cost
  shapes.

### approval-gate.sh
- **:126-134** — `docs/specs/approvers.md` must exist before any
  phase-2-shaped write (record file or src/test path) is allowed.
- **:220-231** — phase-2 gate requires an issue comment whose entire body
  is exactly `APPROVE issue-<n>/<role>`, or a delegation citation matching
  `^APPROVE issue-(\d+)/([\w-]+) VIA DELEGATION (\S+)$` backed by a live
  `DELEGATE <scope> UNTIL <date>` grant, from a `docs/specs/approvers.md`
  login.

### call-shape-guard.sh
- **:153-165** — all call sites of the same `(argv[0], argv[1])` command
  tuple must use the same semantic flag set (issue #419, recurrence of
  #388).
- **:204-209** — a `# sibling:` marked function/class must be named in the
  branch record's `## Siblings` section.

### contract-guard.sh — self-heals a missing `Closes #<issue>` trailer via
`gh pr edit`; only denies if that edit call itself fails (infra failure,
not a shape mismatch).

### decision-queue-stopgate.sh — blocks on staleness/turn-occupancy, not
content shape (no shape-mismatch deny path).

### delegated-judgment-gate.sh — escalates/comments only, unconditional
`exit 0` (no deny path).

### delegation-post-gate.sh
- **:100-108** — a delegation-citing `APPROVE ... VIA DELEGATION ...`
  comment may only be posted by a session with no `CLAUDE_ROLE` bound.

### deliverable-guard.sh
- **:88-112** — an orchestrator session may not write under
  `(^|/)(src|tests?|docs)/` in a board repo, except
  `docs/specs/approvers.md`.

### directive.sh — orchestrator-side injected text only; no deny path.
Notably: contains none of the shape vocabulary (`Accumulation`,
`Siblings`, `derived:`, `spec_index`) that other gates enforce — see Side
B.

### impact-guard.sh
- **:100-104** — a batch of multiple `gh pr merge` calls in one turn is
  denied if any open `status: proposed` proposal is high-reversibility per
  `docs/specs/impact-classification.md`'s dominant-axis rule.

### plan-order-guard.sh
- **:141-144** — a `spawn.py <role> --issue <n>` call must follow the
  issue's `## 실행 계획` declared step order (parser:
  `^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$`, roles split on `‖`).

### pr-preflight.sh
- **:820-821** (phase-1) — PR body must contain a bare `#<issue>`
  reference and must NOT use Closes/Fixes/Resolves.
- **:815-816** (phase-2, incomplete plan) — must NOT use
  Closes/Fixes/Resolves unless this is the last plan step.
- **:820-821** (phase-2, final step) — PR body MUST contain
  `Closes/Fixes/Resolves #<issue>`.
- **:691, 706-708** — phase-2 approval-citation shape, same as
  approval-gate.sh's `APPROVE issue-<n>/<role>` / `VIA DELEGATION` shape.

### product-capture-stopgate.sh — advisory-only (`additionalContext`),
never blocks on shape.

### record-claim-guard.sh
- **:68-69** — scoped to `(^|/)docs/issue-[^/]+/reports/`; delegates to
  `gates/record_lint.py`: a bare ratio/count claim (`N of M`, `N/M`, or
  `N items/works/checks/cases/tests`) needs a code fence or a
  `` `derived: <command-or-path>` `` tag on the same line;
  `unverifiable:` lines need a reason; `checked: X — result: unverifiable`
  lines need a reason; backtick-quoted relative paths must resolve in the
  working tree. (This very file was refused once while drafting this
  survey, for exactly this reason — direct confirmation of the gate's
  shape and of the issue's "first write attempt is then refused"
  pattern.)

### record-scaffold.sh (authoring-time TEMPLATE SOURCE, not a pure gate)
- **:39-87** — generates `docs/issue-<n>/reports/<role>.md` with YAML
  frontmatter (`code_under_review:` list + one
  `<field>: PLACEHOLDER: <field>` line per `roles/<role>.json`'s
  `record_fields`) and body sections `## Summary of work`, `## Why`,
  `## What did not work`, `## Open findings`, `## Next steps`,
  `## Resolution path`, `upstream: PLACEHOLDER: proposal path`. Any
  surviving `PLACEHOLDER` token is later flagged invalid by
  `record_lint` — this is by design (forces replacement), confirmed
  MATCH, not a mismatch candidate.
- **:46-48** — refuses to overwrite an existing record file.

### report-framing-check.sh
- **:66-69** — a PR/board report message must hit all four framing
  elements (resolved problem / prior cost / newly possible / still
  broken, issue #320). Delivered as `decision:"block"`, not a hard exit.

### retry-loop-bound.sh
- **:274-280** — an identical (tool, target) signature denied repeatedly
  past a fixed session-wide cap aborts the action class for the rest of
  the session.

### role-axis-completeness-guard.sh
- **:461** — staged `roles/*.json` must be valid JSON.
- **:471** — every `judgment_axes` entry must be owned by exactly one
  role.

### role-spec-reference-guard.sh
- **:595-596** — for the verification-family roles' record files, every
  `ref`/`ref[]`-typed field must resolve to an existing repo path, commit
  sha, or line-anchored citation.

### role-test-claim-guard.sh
- **:697-701** — pasted pytest output with `SKIPPED` lines forbids a
  clean-pass claim that omits mentioning the skip (issue #334).
- **:711-715** — a hand-typed pass-count claim must equal the pasted
  pytest summary's passed-count (issue #435).

### self-update.sh — no shape-based refusals (offline/env fail-open only).

### session-role-bind.sh — pure state snapshot, always exits 0.

### spec-index-preflight.sh
- **:981-984** — `docs/specs/reconciled-index.md` rows are
  `` | `<path>` | `<64-hex-sha256>` | ``; any staged tracked spec file's
  new sha256 must match its row in the same staged commit, else:
  "Regenerate with `python3 gates/spec_index.py --update`".

### stop-gate.sh
- **:1062-1071** — an approval-shaped reply (trigger phrases like
  "승인 요청"/"APPROVE issue-") must state an issue reference, a change
  statement, and a risk/tradeoff statement. `additionalContext`, not a
  hard block.

## Side B — authoring-time sources located in THIS checkout

| Gate shape | Local source | file:line | Verdict |
|---|---|---|---|
| `## Accumulation` field (accumulation-claim-guard.sh:184) | `/run` orchestrator doc explains the rule in prose | on-the-record/commands/run.md:551-561 | MATCH (orchestrator-facing only — no role-session directive text in this checkout carries it forward; see cross-repo gap below) |
| `## Siblings` / `# sibling:` marker (call-shape-guard.sh:204) | `/run` orchestrator doc | on-the-record/commands/run.md:541-550 | MATCH (same caveat) |
| Record file field scaffold (record-scaffold.sh generated PLACEHOLDER shape) | record-scaffold.sh itself | on-the-record/hooks/record-scaffold.sh:39-87 | MATCH (generator and its own consumer, record_lint, agree — single-repo, self-consistent) |
| `APPROVE issue-<n>/<role>` exact-string comment (approval-gate.sh:220, pr-preflight.sh:691) | `/run` orchestrator doc | on-the-record/commands/run.md:275 | MATCH for the orchestrator path; role-session-side directive text (this session's own `[core] Interaction protocol` SessionStart block) independently states the identical string — also MATCH, but that text is generated by tokenmaxxxer-core at spawn time, not present as a file here, so its file:line cannot be cited from this checkout (see below) |
| `docs/specs/reconciled-index.md` sha256 rows + `spec_index.py --update` regeneration instruction (spec-index-preflight.sh:981) | error text itself names the fix command; no separate authoring-time directive found in this checkout that pre-warns a session to regenerate the index before editing a tracked spec file | — | **GAP (local)**: nothing found in on-the-record/commands/*.md or hooks/directive.sh that states this proactively; the session only learns the required shape from the refusal itself, matching the issue's "first write attempt is then refused" pattern |
| PR trailer Closes/Fixes shape split by phase (pr-preflight.sh:815-821) | none found in on-the-record/commands/*.md phrased as a pre-write rule (run.md discusses `## 실행 계획` step order, not the Closes/Fixes phase split) | — | **GAP (local)**: same "learn from refusal" pattern |
| Call-shape flag consistency (call-shape-guard.sh:153) | none found as a proactive style-guide statement in this checkout | — | **GAP (local)** |

## Side B — sources this checkout cannot see (flagged, not resolved)

The role-session directive text this very session received at
`SessionStart` (`[conformance-review] Role directive`,
`[core] Interaction protocol ... contract v3`) is the single largest
authoring-time source for role sessions, and it is generated/fetched
from `tokenmaxxxer-core` and the `conformance-review` rulebook — repos
absent from this checkout. It already visibly states the
`APPROVE issue-<n>/<role>` shape and record-field requirements
consistent with the local gates (a partial MATCH, observed empirically
from this session's own hook output, not from a citable file here). It
does **not** mention, in the text this session received: the
`## Accumulation` field, the `# sibling:`/`## Siblings` convention, the
`docs/specs/reconciled-index.md` regeneration step, or the pr-preflight
Closes/Fixes phase split — all four are candidates for cross-repo GAP or
MISMATCH once `tokenmaxxxer-core` and the relevant `*-rulebook` are
checked out and diffed against these exact hook lines. This matches the
issue's already-confirmed instances (tokenmaxxxer-core#202,
implementation-rulebook#82, #705), which is why the issue expects more
matches of the same shape once the cross-repo sources are pulled in.

## What this pass could not do

- Could not check out `tokenmaxxxer-core` or any `*-rulebook` repo (no
  such checkouts exist under this session's working tree; cloning a
  second repo mid-audit is new environment setup, not review — flagged
  as phase-2 scope, not done here per this role's read-only provenance).
- Could not run the session-watcher gate-refusal cross-reference:
  `derived: grep -n "2026-08-11" ~/.tokenmaxxxer/work/*.watcher.log |
  grep -iE "refus|gate|block|denied|blocked"` returned no matches. The
  watcher logs present locally do not carry a matching line in this
  environment, so strand-frequency ranking cannot be filled from this
  checkout; recorded as unverifiable rather than omitted.

## Scout

Skipped. Reason: the issue's `## Method` section fully prescribes the
audit's steps (enumerate hooks, extract shape, find authoring source,
classify, rank) — there is no open design decision this deliverable's
shape depends on; it is a read-only research/audit task, not a
build-shaped one.
