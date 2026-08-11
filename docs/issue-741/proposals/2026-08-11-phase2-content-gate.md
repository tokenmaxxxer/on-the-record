files:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py
  - docs/issue-741/decisions/phase2-signal-choice.md
  - docs/issue-741/reports/implementation.md

## Request

`contract-guard.sh` (issue #653's merge-time broker) currently attaches
`Closes #<issue>` whenever an `APPROVE issue-<n>/` comment postdates the
merging PR's own first commit (issue #577's round-scoping). Because
phase-1 and phase-2 PRs share one branch, and approval by definition
postdates phase-1's first commit, this condition is trivially true the
moment a phase-1 (docs-only) PR gets approved — so a phase-1 PR merged
right after approval gets `Closes` attached and prematurely closes the
issue with zero delivery work done (reproduced 2026-08-11 on issue-729,
PR #739). Add a second, content-based condition so the broker only
attaches/requires `Closes` on a PR whose own diff is actually
phase-2-shaped, and record which candidate signal was chosen and why,
including a forgeability judgment against the #476 precedent.

## Constraints

- Zero-install: only `gh` + `python3`, no new dependency, no local
  checkout requirement beyond what `contract-guard.sh` already assumes
  (it must keep working for the cross-repo `-R`/URL/`cd` cases issue #443
  added).
- No new `gh` round trip: the added signal must be obtainable by widening
  a `--json` field list on a call the script already makes, matching the
  precedent issue #577's own proposal set (`docs/issue-577/proposals/
  2026-08-10-round-role-scoped-phase2.md` Constraints).
- Existing 12 tests in `on-the-record/hooks/test_contract_guard.py`
  (derived: `grep -n "^def test_" on-the-record/hooks/test_contract_guard.py`
  — 8 target-repo-resolution tests + 4 round-scoping tests) must keep
  passing unchanged.
- Must not touch `pr-preflight.sh`'s own phase-2 signal or unify it with
  `contract-guard.sh`'s — issue #653's ADR already made and justified
  that split (see Rationale); re-opening it needs its own issue, not a
  side effect of this one.
- Must not touch any root-level test file, `test/`, `tests/`,
  `pytest.ini`, `conftest.py`, or `spawn.py` — a concurrent session
  (issue-729) is mid-move on those paths.

## Rationale

**Chosen signal**: a PR only counts as phase-2-shaped for the
Closes-attach decision when its own diff touches at least one path
matching the same pattern `approval-gate.sh` already uses to decide a
*write* is phase-2-shaped (`on-the-record/hooks/approval-gate.sh:116-119`):
a `src/` or `tests?/` path, or the issue's own role record file directly
under its `reports/` directory (not a subdirectory of it). The path list
comes from widening the existing `gh pr view ... --json body,number,commits`
call (`contract-guard.sh:125`) to also request `files` — one more field
on a call already made, zero extra round trips.

**Considered and rejected — PR body phase declaration** (a `phase: 2` or
similar self-declared field in the PR body). This is the plain
self-report shape issue #476 already ruled untrustworthy for exactly this
class of decision: #476's H1 argument (`docs/issue-476/proposals/
discovery.md:94-100`) is that ground truth must come from a source that
"share[s] no state and no authorship" with the thing being judged, not
from "a self-report" the same actor controls. A PR body is authored by
the same session whose own compliance is in question — trivially
forgeable (accidentally or not) with no independent check, the same
failure class #476 named. `pr-preflight.sh` and `contract-guard.sh`
already agree on this in practice: neither derives `phase` from PR body
content today; both derive it from an independent `gh issue view`
comments lookup. Adding a body-text signal here would be a step backward
from that existing posture.

**Considered and rejected — proposal frontmatter write-set realization**
(compare the approved proposal's `files:` list against the PR's actual
diff). Rejected on two grounds: (1) no existing code in this repo parses
a proposal's YAML `files:` list at all — `gates/gates.py`'s two
existing declared-vs-diff comparators (`writeset()` at `:177-201` against
`spec.md`'s `- write: <glob>` lines, and `role_scope()` at `:846-878`
against `roles/<role>.json`'s `write_scope` globs) both compare against a
*different*, already-machine-readable declaration, never a proposal's
frontmatter; building a new parser is a materially bigger, more fragile
surface for the same yes/no answer the simpler content check already
gives. (2) it is ambiguous which proposal file is authoritative once an
issue accumulates more than one round's proposals, and it would force
`contract-guard.sh` to locate and read a specific markdown file's
frontmatter across repos it may have no local checkout of (issue #443's
`-R`/URL case) — the simpler path-pattern check needs no such lookup,
since `gh pr view --json files` already returns paths directly.

**Forgeability of the chosen signal (the #476 line)**: could a session
force a docs-only PR to look phase-2-shaped by adding a throwaway file
under `src/`/`tests?/`, or force a real code PR to look phase-1-shaped by
omitting them? The `src/`/`tests?/` direction is already blocked by a
deployed, independent gate: `approval-gate.sh` denies any
`Write/Edit/MultiEdit` to a `src/`/`tests?/` path from an un-approved
session (`approval-gate.sh:115-134`) — a phase-1 session cannot legally
create such a path before approval in the first place, so gaming this
signal upward requires first defeating a *different*, already-hardened
gate.

The record-file direction needed a second pass: the after-proposal
warrant hunt (`docs/issue-741/reports/implementation/
2026-08-11-hunt-phase2-content-gate.md`) found that this proposal's
first draft ported `approval-gate.sh`'s record-file check
*role-agnostically* — matching any direct-child filename under
`docs/issue-<n>/reports/`, not just the one exact filename
`approval-gate.sh` itself actually restricts
(`docs/issue-<n>/reports/<role>.md`, `approval-gate.sh:116-117`). That
broadened match reopens exactly the hole the earlier paragraph claimed
was closed: a phase-1 session can legally create an unrelated file in
that same directory today (a stray note, another role's record filename)
— `approval-gate.sh`'s `is_record` check is false for it, so it is not
denied — and if that file ships in a docs-only PR's diff, the
role-agnostic pattern would misread it as phase-2-shaped. The design
below (see "What will be done") closes this by deriving the acting
role from the branch name — the same `git rev-parse --abbrev-ref HEAD`
lookup `pr-preflight.sh`/`approval-gate.sh` already do — and matching
only that role's exact filename, the same restriction `approval-gate.sh`
itself enforces; when the role can't be determined (an unparseable
branch), the record-file half of the check is skipped rather than
widened, so the failure direction stays narrower-match, never a false
positive.

The remaining question — a genuine phase-2 delivery that touches none of
`src/`, `tests?/`, or its own record file — is not gaming so much as
non-delivery: the RECORD REQUIREMENT already mandates every phase-2
session commit its own exact record file before ending, so a real
delivery always trips the (now role-matched) record-path check even in
the degenerate docs-only-deliverable case. This mirrors the external
precedent found in scouting
(`docs/issue-741/reports/implementation/scout-brief.md`): path-glob-
against-diff is the standard external pattern for this exact doc-vs-code
distinction (e.g. `dorny/paths-filter`-style GitHub Actions), and it
lines up with this repo's own only existing precedent for the same
question.

**Scope boundary — `pr-preflight.sh` unification, explicitly out**: issue
#653's ADR (`docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`
lines 60-70, 88-91) already decided `pr-preflight.sh`'s own phase-2 signal
(unscoped by time, unlike `contract-guard.sh`) is "nice to have, out of
scope for this pass," because `pr-preflight.sh` only `deny()`s at
create/edit time — it never executes a merge and never writes `Closes`
itself, so a wrong verdict there cannot reproduce #741's actual failure
(an issue closing with no delivery). That reasoning still holds today
(confirmed by direct reading of both scripts this round) and is not
reopened by this proposal: `contract-guard.sh` remains the sole
authoritative enforcement point, exactly as #653 argued. Unifying the two
scripts' comment-matching logic remains a distinct, already-identified
gap (`docs/issue-653/reports/architecture/survey.md` gap #1) that stays
its own issue if picked up.

## What will be done

In `contract-guard.sh`:
- Widen the existing `gh_json("pr", "view", pr, "--json",
  "body,number,commits")` call to also request `files`.
- After computing today's `phase2` boolean unchanged, add a second
  boolean: does any path in `pr_data.get("files")` match
  `(^|/)(src|tests?)/`, OR match the acting role's own exact record file
  `docs/issue-<n>/reports/<role>.md` — the same two conditions
  `approval-gate.sh:116-119` already checks, at the same precision (an
  exact filename, not a directory-wide match).
- Derive `role` via `git rev-parse --abbrev-ref HEAD` run with
  `cwd=target_cwd or os.getcwd()`, parsed against `^issue-(\d+)/([\w-]+)$`
  — the same lookup `pr-preflight.sh`/`approval-gate.sh` already do. This
  is always a real local checkout by the time this code runs: the one
  case with no local checkout at all (`target_repo_flag` set,
  `target_cwd` is `None`) already exits at `contract-guard.sh:149-155`
  before reaching here (issue #443), so a role lookup never needs to
  reach across a repo boundary it doesn't have.
- If the branch doesn't parse (detached HEAD, non-issue branch) or its
  issue number doesn't match the PR's own `issue`, skip the record-file
  half of the check (treat it as not matched) rather than falling back to
  a broader pattern — the `(^|/)(src|tests?)/` half still applies
  unconditionally. This is the direct fix for the after-proposal hunt
  finding (`docs/issue-741/reports/implementation/
  2026-08-11-hunt-phase2-content-gate.md`): failure narrows the match,
  it never widens it.
- Gate the existing attach-or-deny block (`:177-201`) on `phase2 AND`
  that new boolean — when `phase2` is true but the PR carries no
  phase-2-shaped path, `exit 0` without touching the body (same as the
  existing "no phase2" early exit), leaving the merge to proceed exactly
  as an ordinary phase-1 merge would.

In `test_contract_guard.py`:
- Extend `FAKE_GH`'s `pr view` branch to also emit `files` (a list of
  `{"path": ...}`) from the fixture.
- Add the two Acceptance-criteria cases plus their empty-state pairing:
  - same-round approval + PR fixture with only `docs/`-prefixed file
    paths -> `returncode == 0`, no `gh pr edit` call recorded (the #741
    regression case, PR-#739-shaped).
  - no approval comment at all + docs-only file paths -> `returncode ==
    0`, no edit call (existing empty-state behavior, included as a green
    case in the same matrix per the Acceptance text).
  - same-round approval + PR fixture whose files include a `src/...`
    path -> `Closes` attached as today (regression guard on the existing
    12 tests' behavior, generalized to the new code path).
  - same-round approval + PR fixture whose only file is a *different*
    filename directly under `docs/issue-<n>/reports/` (e.g. another
    role's record file, or an unrelated note) -> `returncode == 0`, no
    `Closes` attached — the after-proposal hunt's exact scenario, pinned
    as a permanent regression so the role-agnostic version of this bug
    cannot silently return.
  - same-round approval + PR fixture whose only file is the acting
    role's own exact record file (`docs/issue-<n>/reports/<role>.md`) ->
    `Closes` attached — confirms a genuine docs-only phase-2 delivery
    (no `src/`/`tests/` touched) still gets recognized.

New: `docs/issue-741/decisions/phase2-signal-choice.md` records the
chosen signal, the two rejected alternatives, and the forgeability
judgment above in permanent form (doctrine ladder: an algorithm/format
choice over named alternatives belongs in `docs/issue-<n>/decisions/`).

`docs/issue-741/reports/implementation.md` is the phase-2 record
mandated by contract v3 s19 — written during phase-2, not before.

## Out of scope

- Unifying `pr-preflight.sh`'s phase-2 signal with `contract-guard.sh`'s
  (round-scoping port, exact-vs-prefix comment match, delegation-citation
  parity) — issue #653 already deferred this deliberately and the
  reasoning for that deferral still holds (see Rationale); a future
  session may reopen it as its own issue if `pr-preflight.sh`'s
  unscoped signal starts causing its own (different-shaped) problem.
- Reconstructing a first-class round counter — issue #577 already ruled
  this out of the data model; this proposal reuses that same time-based
  round signal unchanged, only adding a second, independent content
  condition alongside it.
- Any change to `approval-gate.sh` itself — it is only read here as
  existing precedent for the path pattern, not modified.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_contract_guard.py -v` passes:
the 12 existing tests unchanged, plus the new regression/empty-state/
content-positive matrix described above, directly exercising both
Acceptance rows from the issue (docs-only PR + same-round approval ->
no `Closes` attach, issue stays open; code-bearing PR + approval ->
`Closes` attach and merge-pass preserved).

## Accumulation

`contract-guard.sh`'s `gh_json()` remains the single choke point for all
`gh` calls; this change widens one existing call's `--json` field list
and adds one pure-Python predicate, no new call site. `test_contract_guard.py`'s
`FAKE_GH` fixture shim is extended the same way issue #577's round-scoping
matrix already extended it (new fixture fields, no new shim branches) —
not an accumulating inline-call-site pattern (accumulation.py shape 1).
