---
status: proposed
files:
  - docs/issue-476/reports/implementation/survey-round2.md
  - docs/issue-476/proposals/implementation-round2.md
---

# Proposal — issue #476 round 2 implementation: build the claim-scan preflight hook

Phase 1 only, per role-handoff contract v3 s19. Builds on
`docs/issue-476/proposals/architecture-round2.md` (approved,
`APPROVE issue-476/architecture`, PR #572 merged) and this round's own
survey (`docs/issue-476/reports/implementation/survey-round2.md`, linked
above by path). Scope: build the hook exactly as architecture-round2's
Decision section specifies — no new design decision (phase 2, on
approval).

## Request

Build `on-the-record/hooks/claim-scan-preflight.sh` per
`docs/issue-476/proposals/architecture-round2.md`: a `PreToolUse` `Bash`
hook joining the existing matcher array after the pr-body preflight
check, inheriting that check's `gh pr create`/`gh pr edit` matcher regex
and `--body`/`--body-file` extraction verbatim; a character-for-character
port of the claim-vocabulary regex, the evidence-marker regex, and the
fence-adjacency check from the repo's existing claim-scan module (not an
import — this hook must run in a consumer repo with no dev-tooling
checkout); three distinct fail branches (ambiguous input passes silently,
a positive hit warns without blocking, and a future deny branch that only
this hook's own header names as not-yet-active); the same kill-switch
convention every hook in this plugin already carries; and the wiring
entry in the plugin's hook manifest.

## Constraints

- No `gates/` import from the new hook — the survey confirmed the one
  existing hook that does resolve `gates/` via a relative path only works
  in this repo's own dev checkout, not a marketplace-installed consumer
  repo (architecture-round2 Decision point 3, Alternatives #1).
- Matcher regex and `--body`/`--body-file` extraction copied verbatim
  from the existing pr-body preflight hook — no widening, no narrowing
  (architecture-round2 Decision point 2; matcher-widening is a pivot
  action gated on a coverage metric this round does not measure).
- Positive-hit branch never blocks (`exit 0` with guidance), and is a
  structurally separate code branch from the ambiguity branch, so the
  future flip to deny only touches one branch (architecture-round2
  Decision points 5-6).
- The two-week/60%-threshold flip-to-deny rule is quoted verbatim into
  the new hook's own header comment, not paraphrased and not left to a
  separate doc (architecture-round2 Decision point 6).
- Kill switch (`ORCHESTRATE_OFF`) checked first, before any parsing
  (architecture-round2 Decision point 7).
- New hook joins the manifest immediately after the pr-body preflight
  entry and before the next existing entry in that same matcher array —
  no new matcher group (architecture-round2 Decision point 1,
  Alternatives #4).

## Rationale

**Chosen approach**: build now, phase 2, with no further design work —
architecture-round2 already fixed every open variable (file path, regex
text, branch structure, header citation, manifest position). The only
implementation-level choice this round makes for itself is the shape of
the new test file, since no existing hook script in this repo has a
committed test to pattern-match.

**Alternative considered and rejected — import `gates/claim_scan.py`'s
`scan_text()` directly instead of porting the regex constants.** This
would be less code and would guarantee the two sites can never drift.
Rejected because it was already rejected one layer up, in
architecture-round2 (Decision point 3, Alternatives #1), for a concrete
reason the survey re-confirmed by direct read: the only existing hook
that imports `gates/` (`record-claim-guard.sh`) does so via a
relative-path `sys.path` insert that only resolves because `gates/` sits
beside `on-the-record/` in this repo's own dev checkout — a
marketplace-installed consumer repo has no `gates/` directory at all, so
that import would raise at hook-invocation time in exactly the
deployment surface this mechanism exists to reach. Re-litigating this
choice at the implementation layer would contradict the phase it was
already decided at; the implementation's job is to execute the decision,
not re-open it.

## What will be done

1. Read `gates/claim_scan.py` at build time and copy `CLAIM_RE`,
   `EVIDENCE_MARKER_RE`, `FENCE_RE`, and the fence-adjacency helper logic
   (`_fence_spans`/`_in_fence`/`_nearby_evidence`, `ADJACENCY_LINES = 5`)
   character-for-character into the new hook's embedded Python, adapted
   only for standalone execution (no imports from `gates/`, no
   `repo_targets`/traceability — out of scope per the survey's reading of
   architecture-round2 point 3).
2. Read `on-the-record/hooks/pr-preflight.sh` at build time and copy its
   kill-switch line, its `gh\s+pr\s+(create|edit)` matcher regex, its
   stdin-payload handling, and its `--body`/`--body-file` extraction
   regex pair character-for-character.
3. Write the new hook script with three branches on the ported
   `scan_text`-equivalent result: (a) any parse ambiguity (non-matching
   command, missing `python3`, absent `--body`/`--body-file`, unreadable
   body-file) → `exit 0`, no output; (b) a positive claim-with-no-evidence
   finding → `exit 0`, emitting `additionalContext` in the hook's JSON
   stdout plus a mirrored stderr message, both naming the specific claim
   line, the missing evidence-marker requirement, and the flip-to-deny
   condition; (c) a header-comment-only future branch, not live code yet,
   documenting what changes when the flip fires (per architecture-round2
   point 6) so the future edit touches only branch (b)'s exit code.
4. Quote the H1b flip rule (two-week window from first shipped commit
   date, `>= 60%` correction rate to flip, `< 60%` pivots to a
   documentation fix instead) verbatim into the new hook's header
   comment, dated from this proposal's approval commit.
5. Insert one new object into the plugin's hook manifest's `PreToolUse`
   `"Bash"` matcher array, positioned immediately after the pr-body
   preflight entry and before the next existing entry.
6. Write a new root-level test script under `test/` that invokes the new
   hook as a subprocess with constructed JSON payloads and asserts: a
   claim-with-adjacent-evidence input exits 0 with no
   `additionalContext`; a claim-with-no-evidence input exits 0 with
   `additionalContext` and a mirrored stderr message naming the claim
   line; a non-`gh pr create`/`edit` command exits 0 silently; an
   `ORCHESTRATE_OFF`-set environment exits 0 before any parsing, verified
   by a payload that would otherwise trigger the positive-hit branch.
7. Update the plugin's gates-enforcement-boundary table (the
   consumer-facing gates listing) to record the claim-scan check's
   enforcement class as zero-install-hooked, per architecture-round2's
   own Files section — matching the row-update pattern the existing
   record for round 1 of this issue already used when a `gates/*.py`
   module gained a new enforcement site outside its own frozen write set.
8. Write the phase-2 implementation record at
   `docs/issue-476/reports/implementation.md`, citing this proposal, the
   architecture-round2 decision, and the test run.

## Out of scope

- Widening the matcher beyond `gh pr create`/`gh pr edit` (`gh api`
  PR-body writes, wrapper-script indirection) — explicitly deferred by
  architecture-round2 pending a measured `wiring_coverage_rate`.
- Repo-target traceability (`TARGET_RE`/`_cite_matches`) — not named in
  architecture-round2's ported-logic list; this hook judges claim +
  evidence-marker presence only, the same text-only mode
  `gates/claim_scan.py`'s `scan_text()` runs in when called with no
  `repo_targets`.
- Actually flipping the positive-hit branch to `exit 2` — that edit is
  gated on the two-week/60% measurement window and is a future change to
  this same file, not part of this build.
- `reexecution_gate.run_reexecution()` — explicitly not ported per
  architecture-round2 point 3 (candidate B territory, deferred).
- Step 4 of the issue's execution plan (execution-observation /
  conformance-review) — measuring `wiring_coverage_rate` and
  `warn_period_correction_rate` against threshold is the next step in the
  issue's own plan, not this build.

## How you'll know it worked

On `APPROVE issue-476/implementation`, phase 2 ships a hook file that:
fires on a constructed `gh pr create --body "..."` command carrying claim
vocabulary with no evidence marker, producing `additionalContext` and a
mirrored stderr message rather than a silent pass or a block; does not
import anything from `gates/`; carries the `ORCHESTRATE_OFF` kill switch
as its first executable check, verified by a test case that sets it and
confirms no output; and states the H1b flip-to-deny date and threshold
verbatim in its own header comment. The new test script passes,
alongside the existing hook and gate test suites showing no regression.
