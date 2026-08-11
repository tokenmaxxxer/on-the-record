---
status: proposed
files:
  - on-the-record/hooks/test-authoring-invariant-guard.sh
  - on-the-record/hooks/test_test_authoring_invariant_guard.py
  - on-the-record/hooks/hooks.json
  - gates/roles_due.py
  - gates/test_roles_due.py
  - roles/specs/security-threat-model.spec.json
  - roles/specs/accessibility.spec.json
  - roles/specs/product-discovery.spec.json
  - roles/specs/interaction-design.spec.json
  - roles/specs/defect-verification.spec.json
  - roles/specs/execution-observation.spec.json
  - roles/specs/conformance-review.spec.json
  - spawn.py
  - docs/issue-896/reports/implementation.md
---

# Proposal — issue-896 step 2: standing test-authoring invariant + roles-due evaluator (judgment residue)

## Request
Per the operator's REFRAME comment on #896 (invariant-first, supersedes
the issue body's spawn-when framing): split test-authoring's expertise
into (1) a standing invariant — "a new or changed code path that ships
without a covering test cannot land" — enforced as an always-on gate with
no spawn and no cost decision, and (2) the board_condition evaluator
(`spawn.py roles-due`) for the judgment residue that cannot be reduced to
an always-on check. Plugin-only, no forced CI, explicit N/A escape for
code paths with no testable behavior.

## Constraints
- Plugin-only / no forced CI (req#7) — enforcement is a PreToolUse Bash
  hook in this plugin, not a GitHub required check.
- No command allow/deny lists (explicit instruction) — classification is
  by staged file path/extension, not by inspecting or blocking specific
  shell commands.
- Must not multiply the existing unconditional missing-role-record noise —
  `roles-due` only reports a role when its trigger pattern matches the
  diff AND its record is absent; no match, no output (empty state).
- test-authoring's existing spec (`roles/specs/test-authoring.spec.json`)
  already states the bar in prose (`use_when.board_condition`); this
  proposal encodes that same bar as a mechanical check, it does not
  redefine the bar.

## Rationale
Considered making the invariant a PreToolUse `Write|Edit` gate (same
matcher as `deliverable-guard.sh`/`credential-record-guard.sh`) that
blocks writing a code file unless a test file was already written this
session. Rejected: code and its test routinely land in separate,
independently-ordered tool calls within the same commit (write the
implementation file, then the test file, or vice versa) — a per-edit gate
would false-positive on the very common case of writing the source file
first, with no way to know a test is coming later in the same commit. The
commit boundary is the point where "this change, as a whole, has no test"
is actually decidable, and it is already an established interception
point in this repo (`pr-preflight.sh`, `contract-guard.sh` both hook
`git commit`/`gh pr` Bash calls the same way) — reusing that boundary
avoids inventing a new hook shape.

Considered making `roles-due` re-decompose all 43 `use_when.board_condition`
strings into structured triggers in this pass. Rejected as out of scope by
the merged phase-1 proposal itself and by the operator's own scoping
instruction ("if the full per-role derivation is too large, implement the
invariant + evaluator now and record the rest as staged next steps") — the
seven roles whose Korean `use_when` already embeds a parenthetical English
`board_condition` are the ones precise enough to decompose without
inventing new categories; the remaining ~35 are staged as next steps
below rather than guessed at here.

## What will be done
1. `on-the-record/hooks/test-authoring-invariant-guard.sh` — PreToolUse
   Bash hook, deny-only, mirrors `pr-preflight.sh`'s inline-Python-in-
   heredoc shape. Fires only on a matched `git commit` invocation. Reads
   `git diff --cached --name-only --diff-filter=ACM` (falls back to
   `git diff --name-only --diff-filter=ACM HEAD` if nothing is staged,
   covering `git commit -a`). Classifies each path: test (path contains a
   `test`/`tests`/`spec` segment, or a `test_*`/`*_test.*`/`*.spec.*`
   basename), doc (`docs/` or `.md`), config/non-code (no recognized code
   extension), code (recognized source extension: `.py .js .ts .tsx .jsx
   .sh .go .rb .java .rs .c .cpp .kt`). Denies (exit 2) when at least one
   code path changed and zero test paths changed in the same set, unless
   the commit message (extracted the same way `pr-preflight.sh` extracts
   `--body`, plus a plain `-m "..."` case) contains a line matching
   `^Test-N/A: .+` (a non-empty reason). Fail-open: no `python3`, no `git`
   repo, not a `git commit` command, empty diff, or unparseable message ->
   allow.
2. `on-the-record/hooks/test_test_authoring_invariant_guard.py` — unit
   tests for the classification + decision function, run as pure Python
   (no subprocess), covering: code-with-test allow, code-without-test
   deny, N/A-with-reason allow, N/A-with-empty-reason deny, docs-only
   change allow, non-commit command allow, malformed payload allow.
3. Register the hook in `on-the-record/hooks/hooks.json` under
   `PreToolUse`, matcher `Bash`, alongside the existing `contract-guard.sh`
   / `pr-preflight.sh` entries.
4. `gates/roles_due.py` — `roles_due(root: Path, base: str) -> list[dict]`.
   For each of the seven named role specs, reads its `use_when.trigger`
   block (path-glob + optional content-regex list), matches against
   `changed_files(root)` (reused from `gates/gates.py`) content via
   `git show`/working-tree read, and checks the current subject's board
   record (via a local, dependency-free frontmatter reader mirroring
   `gates.record_frontmatter`) for the named role. Returns due entries:
   `{role, reason, subject}`. Subject is derived from the branch name
   (`issue-<n>/...`) the same way `pr-preflight.sh` does.
5. `gates/test_roles_due.py` — unit tests for match/no-match, record-
   present suppresses due, empty state (no trigger fires -> `[]`).
6. Add a `use_when.trigger` block to the seven named specs (path/content
   patterns approximating each existing parenthetical `board_condition`).
   `test-authoring.spec.json` is deliberately left without a `trigger` key
   — it is not part of this evaluator's roster (see Rationale).
7. `spawn.py`: add `a.role == "roles-due"` in `main()`, importing
   `gates/roles_due.py` the same way the existing `flows` subcommand
   imports `gates/flows.py`; prints one line per due role, nothing when
   the list is empty.
8. `docs/issue-896/reports/implementation.md` — this phase's record.

## Out of scope
- Decomposing the remaining ~35 roles' `use_when.board_condition` into
  structured triggers — staged as an explicit next step below, not
  attempted here.
- Hard-gating any of the seven `roles-due` roles the way test-authoring is
  now hard-gated — they stay surfaced-only, per the merged phase-1
  proposal's enforcement-tier design.
- Command allow/deny lists of any kind.
- Wiring `roles-due` into `spawn.py status`'s automatic output or into a
  blocking gate — this pass ships the evaluator as an explicit,
  opt-in subcommand only (`spawn.py roles-due`), matching the issue's own
  wording ("surface ... for the orchestrator").
- The #776 harness scenario from the phase-1 proposal's section 4 — a
  separate, later step per the issue's own execution plan.

## Accumulation
Adding a `use_when.trigger` block is a one-time, per-file mechanical edit
on seven role specs now; extending to the remaining ~35 (staged next
step) grows the same way — bounded by 43 total roles, never open-ended,
and each addition is independently reviewable (a static JSON literal, not
generated code, so no shared helper is needed to keep it from drifting).
`roles_due` itself carries no accumulating state across runs — it
recomputes from the current diff + board every call, so repeated calls
never grow a file or list.

## How you'll know it worked
`gates/test_roles_due.py` and
`on-the-record/hooks/test_test_authoring_invariant_guard.py` pass;
a manual `git commit` of a code-only change (no test) is denied by the new
hook and allowed once a `Test-N/A: <reason>` trailer is added or a test
file is included in the staged set; `spawn.py roles-due` prints nothing on
a branch matching none of the seven triggers and prints the matching
role(s) on one that does.
