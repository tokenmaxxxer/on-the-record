---
status: proposed
files:
  - spawn.py
  - gates/roles_due.py
  - gates/role_spec_shape.py
  - roles/specs/*.spec.json
  - docs/specs/role-activation.md
  - harness/scenarios/*
  - harness/signals.py
  - gates/test_roles_due.py
---

# Proposal — issue-896: board_condition evaluator + enforcement policy

## Intent
Turn each role's `use_when.board_condition` from documentation into an actual activation signal: compute, from a branch's landed records and diff, which roles' conditions currently fire and have no record yet ("due"), surface that to the orchestrator/board, and hard-gate a named subset of load-bearing roles so a firing condition cannot be silently skipped — without forced CI and without over-blocking. This is step 1 (design) only, per the issue's own execution plan; step 2 (implementation) and step 3 (harness verification) are separate, later issues/branches.

## Constraints stated so far
- Plugin-only, no forced CI (req#7, restated in the issue) — enforcement runs inside `spawn.py`'s own gate family, never via a GitHub required status check.
- Must be grounded in the actual `roles/*.json`/`roles/specs/*.spec.json` triggers, not invented categories (survey: `docs/issue-896/reports/product-discovery/survey.md` confirms all 43 specs carry a machine-readable `use_when.board_condition`).
- Must not multiply the existing unconditional "missing role record" noise (survey: `status()`'s missing-role list is already unconditional across all 43 roles per subject) — the evaluator's whole value is conditioning that list on whether the trigger fired.
- Generalizes #894 (security-threat-model enforcement is this design's one instance, not a separate mechanism) and must specify how the #776 harness proves a scenario needing a specialist role actually activates it.
- No code in this deliverable — design only.

## Design

### 1. The evaluator: `spawn.py roles-due`

**Inputs**: the subject's landed board records (`docs/issue-<n>/reports/*.md` frontmatter, via the existing `board()`/`status()` reader) and the branch's diff against base (`spawn.py`'s existing `_base()`/diff-reading path).

**Per role**, `board_condition` is not free text to an LLM at evaluation time — it is decomposed once, by hand, into a small structured predicate stored alongside the human-readable string in each `roles/specs/*.spec.json`, e.g.:

```json
"use_when": {
  "board_condition": "a spec or design doc landed that introduces a new trust boundary, authentication surface, or sensitive-data flow AND no security-threat-model record exists yet for it",
  "trigger": {
    "diff_path_patterns": ["**/auth/**", "**/*permission*", "**/*credential*"],
    "diff_content_patterns": ["bypassPermissions", "sudo", "trust boundary"],
    "record_absent_for": "security-threat-model"
  }
}
```

`trigger` is additive metadata, not a replacement for `board_condition` (which stays the human-readable source of truth reviewed at spec-authoring time) — `roles-due` evaluates `trigger`, a person or a role-authoring session evaluates whether `trigger` still matches what `board_condition` says. This mirrors the scouted CODEOWNERS/OPA pattern (docs/issue-896/reports/product-discovery/scout-brief.md): a required check computed from the diff's paths/content, not from remembered prose.

`roles-due` then reports: for each of the 43 roles, does `trigger` match the current diff, AND is `record_absent_for`'s named role's record missing from the board for this subject? If both hold, the role is **due**. Output is a short list — role name, one-line reason (which pattern matched), nothing else — appended to `spawn.py status`'s existing output, not a new noisy surface.

**Why decomposed patterns, not an LLM re-reading `board_condition` as prose at evaluation time**: determinism and auditability. A pattern match is reproducible and testable (`gates/test_roles_due.py`); an LLM judgment call re-run on the same diff could answer differently session to session, which would make the hard-gate below unenforceable (a role could be gated out one run and not the next on identical input). The prose stays as the spec's contract for what the pattern is *supposed* to approximate — the gap between prose and pattern is exactly what a stale-trigger review (below) catches.

**Empty state**: no pattern matches for any role → `roles-due` prints nothing extra, consistent with the issue's stated acceptance ("a branch firing no role condition is unaffected").

### 2. Enforcement policy: hard-gated vs surfaced-as-due

Not all 43 roles get the same enforcement weight — over-blocking (explicitly warned against in the issue) comes from treating "due" and "must-block" as the same thing. Two tiers, decided per role at spec-authoring time and recorded as a field on the role's spec (`enforcement: hard | surfaced`), not computed dynamically:

- **Hard-gated** (small, deliberately short list — the roles whose absence is a landed, uncaught defect, not a missed nicety): `security-threat-model`, `secure-coding`, `test-authoring`. These three are the ones the issue itself names as observed-missing with concrete consequence (#894's unreviewed permission-broadening changes; untested new code shipping). A hard-gated role that is due and unrun blocks the same way `require_acceptance_gate`/`require_board` already block in `spawn.py` — the gate call sits in the same family, so "plugin-only, no forced CI" is inherited for free (these are pre-existing local gates, not GitHub checks).
- **Surfaced-as-due** (the remaining ~40, including `performance-engineering`, `accessibility`, `risk-management`): reported by `roles-due` and included in `status()`'s board output, never blocking. This is the majority tier by design — the issue's own framing ("~6 of 43" activated) says the problem is *visibility*, not that all 43 need to be load-bearing simultaneously; escalating a role from surfaced to hard-gated is a follow-up decision made with evidence from real misses, not a day-one default.

**Escape hatch (false-fire / N/A handling)**: a hard-gated role that is due can be dismissed by writing an N/A record — `docs/issue-<n>/reports/<role>.md` with `loop_state: not-applicable` and a required `reason:` field — instead of the full role record. `require_board`'s existing frontmatter reader already treats any record with valid frontmatter as satisfying "role has run" for board purposes, so this needs no new record type, only a new accepted `loop_state` value per role's spec (mirrors the terminal-state override mechanism already in the interaction protocol: `docs/specs/record-fields-terminal-states.json`). The reason is not optional prose either — `record-claim-guard.sh`'s existing pattern (refusing bare claims without justification, already enforced on every record write in this repo) is the model: an N/A with no reason is refused the same way an unverifiable claim with no reason is refused today.

**Waiver durability** (scouted must-be: exceptions are controlled and expiring, not permanent — vulnerability risk-acceptance practice, scout-brief.md): an N/A record is scoped to the commit sha it was written against (mirrors `secure-coding`'s own `board_condition`, which already scopes "record exists" per commit sha, not per branch) — a later commit on the same branch that also matches the trigger fires `roles-due` again, fresh. N/A is never a standing blanket exemption for the branch.

### 3. False-fire management
Two failure directions, both bounded by the pattern being conservative and auditable rather than clever:
- **False positive** (pattern matches, role genuinely not needed): the N/A escape above, at the cost of one recorded line — cheap enough not to be a real burden, expensive enough (a written, attributable reason) not to be a rubber stamp.
- **False negative** (pattern misses a case `board_condition`'s prose would have caught): this is a spec-quality defect, not an enforcement defect — it belongs to #807 (role methodology quality) as a periodic audit: does each role's `trigger` still approximate its `board_condition` prose, checked by re-reading the prose against recent misses. This proposal does not attempt to make the pattern perfect on day one; it makes the miss auditable (the mismatch is a `trigger` vs `board_condition` review question, always inspectable, never a silent black box).

### 4. #776 harness verification
The harness (`harness/driver.py`, `harness/signals.py`) already captures a transcript and instantiates a fixture target per scenario. To verify activation:
- Add a scenario whose `REPRESENTATIVE_REQUIREMENT`-equivalent fixture deliberately matches a hard-gated role's `trigger` (e.g. a requirement that touches `auth/` and introduces a new permission check — fires `security-threat-model`'s pattern).
- After the session, `harness/signals.py` gains one new signal: read the resulting board (`spawn.py status` or `board()` directly) for the fixture's issue subject, and check that the hard-gated role that should have fired has either a real record or a valid N/A record with a reason — not silently absent.
- A second scenario, deliberately matching no role's `trigger`, checks the negative: the board carries no N/A/due noise for roles that were never due, keeping the "branch firing no role condition is unaffected" acceptance criterion testable, not just asserted.
- This is genuinely new harness surface (a new scenario + a new signal), not a repurposing of an existing one — `signals.py` currently has no role-activation-aware check to extend (survey confirms this).

## Out of scope
- Implementation of `roles-due`, the `trigger` schema on all 43 specs, and the harness scenarios (issue #896 step 2 and step 3 — separate branches/roles).
- Deciding the final hard-gated list beyond the three named above; that list is itself a candidate for revision once `roles-due` has run for a while and produced real due/N-A data (an ITWWS follow-up, below).
- Any change to CI or branch-protection configuration — explicitly excluded by req#7.

## How we'll know it worked
This design succeeds if, once implemented (step 2) and exercised by the harness (step 3): a scenario firing a hard-gated role's trigger cannot reach a terminal board state without either that role's record or a reasoned N/A; a scenario firing a surfaced-only role's trigger shows up in `roles-due`/`status()` output but does not block; and a scenario firing nothing produces no additional output versus today's baseline.

## Accumulation
This is a phase-1 design deliverable (no code, no schema migration performed here) — no accumulation cost is incurred by this PR itself. The accumulation cost belongs to step 2: adding a `trigger` block to 43 spec files is a one-time, mechanical, per-file edit (not a growing-without-bound cost), and the N/A escape adds one record per false-fire, bounded by how often the trigger patterns are imprecise — which is exactly the signal #807's periodic trigger-quality audit (above) is meant to drive down over time, not a cost this design lets grow unchecked.

## ITWWS (if this works we should ...)
... revisit the hard-gated list (`security-threat-model`, `secure-coding`, `test-authoring`) using real `roles-due`/N-A data collected over several subjects, and consider promoting `accessibility` or `performance-engineering` to hard-gated if their surfaced-as-due signal shows a similar pattern of being ignored, the way security was before #894.
