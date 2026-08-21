---
status: proposed
files:
  - core/hooks/board-gate.sh
  - core/hooks/citation-gate.sh
---

## Request

Issue #1827 (phase 5 FINAL of the skill-axis removal cycle, dependency
recorded on #1814, verified against core commit `38052e5`): core is the
last consumer that still makes the role-name-in-branch convention
LOAD-BEARING. Two mechanisms in `tokenmaxxxer-core` do this: (1)
`core/hooks/board-gate.sh` rule R4 requires the current branch to be
exactly `issue-N/<CLAUDE_ROLE>` for any `docs/issue-N/` write — an
enforcement READ of the branch-name convention; (2)
`core/hooks/citation-gate.sh` exports `CIT_BRANCH` from
`git rev-parse --abbrev-ref HEAD` and consumes it in its embedded
python. This issue asks that both gates go carrier-aware with the SAME
dual-read + fallback pattern already landed for #1818/#1821/#1824: R4
should prefer the workspace role sidecar `.on-the-record/role.json`
(#1814) when present — checking branch issue-number match plus
sidecar role == `CLAUDE_ROLE`, no longer requiring the role string
inside the branch name itself — and fall back to today's exact
branch-string check only when the sidecar is absent. citation-gate's
`CIT_BRANCH` consumption must be surveyed first: if it only extracts
the issue number it is already role-free and the finding is recorded
with no code change; if it reads a role segment, the same dual-read
applies. After this lands, no core enforcement anywhere REQUIRES the
role string in a branch name — branch names may still carry it
cosmetically, but nothing in core parses that segment as authority.

## Constraints

- **bash 3.2 safety**: both files already carry the house guard
  ("no heredoc-in-command-substitution", core#245) — board-gate.sh via
  `IFS='' read -r -d '' CORE_BOARD_GATE <<'PY'` fed to `python3`
  afterward, citation-gate.sh via a top-level `python3 <<'PYEOF'`. Any
  new sidecar-read code is added INSIDE these existing heredoc bodies,
  never in a new `$(...)`-wrapped heredoc, and introduces no
  associative arrays, `mapfile`, or `${var^^}`-style bashisms.
- **Live-fire must keep working**: R4's existing live-fire behavior for
  a no-sidecar workspace must be byte-identical to today — same denies,
  same allows, same message text — verified by a dedicated live-fire
  case, not just unit assertions.
- **Fail-closed on mismatch**: a sidecar present with a role/issue that
  disagrees with an independently-parseable branch is a hard refuse
  (exit 2, naming both values), not a warning and not a silent
  sidecar-wins.
- **Byte-identical legacy fallback**: when the sidecar is absent,
  unreadable, malformed, or missing the required `role`/`issue` keys,
  R4 falls through to exactly the check that exists today
  (`core/hooks/board-gate.sh:719-784`) — same comparison, same deny
  message, same maintenance-targets exception path
  (`:734-768`, untouched).
- **Must not break other rules**: R1-R3, R5 (`core/hooks/board-gate.sh`,
  documented at `:6-33`) and the maintenance-targets exception
  (`:734-768`) are unrelated code paths and must not be touched or
  have their behavior altered. citation-gate.sh's other 10 config rows
  and other check functions (`core/hooks/citation-gate.sh`, the
  `check_*` function table around `:637`) must not be touched.

## Rationale

**Chosen**: reuse the exact `.on-the-record/role.json`-preferred,
independent-branch-cross-check, fail-closed-on-disagreement shape
already landed in `on-the-record/hooks/approval-gate.sh:109-169`
(#1821), adapted to R4's specific comparison (issue number + role
match, not approval-record lookup).

**Rejected alternative 1 — sidecar-only, drop the branch check
entirely.** Rejected because branches created before the sidecar
convention existed (or workspaces where `_write_role_sidecar` failed —
it is fail-open by design, `spawn.py:7625-7639`) would have no sidecar
and no fallback path, silently losing R4 enforcement rather than
degrading safely. The issue's own requirement 1 explicitly asks for
"with no sidecar, behavior byte-identical to today" — a sidecar-only
design cannot satisfy that.

**Rejected alternative 2 — warn-and-continue on sidecar/branch
mismatch.** Rejected because #1818/#1821/#1824 already established
fail-closed-on-mismatch as the invariant for this exact carrier chain
(see `on-the-record/hooks/approval-gate.sh:144-152`, which denies
rather than warns on a sidecar/branch disagreement). A warning-only
mode here would make R4 the one inconsistent link in an otherwise
uniform fail-closed chain, and — being an enforcement gate rather than
a report — a warning that doesn't block is functionally identical to
no check at all for anyone not reading stderr.

**Rejected alternative 3 — change citation-gate.sh's `CIT_BRANCH`
derivation or its `branch_regex` shape while we're in the file
anyway.** Rejected: the survey found `citation-gate.sh`'s only
`branch_regex` (`core/hooks/citation-config.json:185`,
`"^issue-(\\d+)/"`) already captures issue-number-only and never reads
a role segment — it is already role-free per the issue's own
requirement 2 ("if issue-number-only, the finding is recorded ... and
no change is made"). Touching it anyway would be scope creep against
an explicit non-goal and would risk the config-row-parameterized fold
(11 rulebooks' worth, `core/hooks/citation-gate.sh:1-14`) for zero
carrier-awareness benefit.

## What will be done

Phase 2 (gated on approval of this proposal) will edit only
`core/hooks/board-gate.sh`, R4 section (`:719-784`):

1. After the existing `symbolic-ref --short HEAD` resolution
   (`:723-731`, kept verbatim as the fallback branch string), add a
   sidecar read: `open(os.path.join(root, ".on-the-record",
   "role.json"))`, parsed the same way as
   `on-the-record/hooks/approval-gate.sh:118-126`  —
   `{"role": str, "issue": int}` shape required, any
   OSError/ValueError/shape mismatch falls through with sidecar values
   left `None`.
2. When the sidecar resolves (`issue`/`sidecar_role` both set): the R4
   per-hit loop (`:770-784`) is changed from
   `expected = "%s/%s" % (issue_dir, role); if branch == expected:
   continue` to a two-part check — (a) the branch's OWN issue number
   (parsed from `branch` via the existing `_bm` regex at `:741`, or a
   fresh `re.match(r"^issue-([0-9]+)", branch)` if branch carries no
   role segment at all) equals `issue_dir`'s number, AND (b)
   `sidecar_role == role` (`role` being the existing `CLAUDE_ROLE`
   value already in scope). Either failing falls through to the
   existing maintenance-targets exception (`:734-768`, unchanged) and
   then the existing deny (`:779-784`, message text extended to name
   the sidecar-vs-legacy source it used, mirroring
   `on-the-record/hooks/approval-gate.sh:145-148`'s two-value deny
   text).
3. When the sidecar is present but disagrees with an independently
   parseable full `issue-N/<role>` branch (both a role segment AND a
   sidecar resolve, and they name different issue/role pairs): fail
   closed immediately, before the per-hit loop, mirroring
   `on-the-record/hooks/approval-gate.sh:128-152`'s cross-check block
   verbatim in shape (adapted variable names).
4. When the sidecar is absent/unreadable/malformed: skip 1-3 entirely;
   the per-hit loop runs exactly the `:770-784` comparison that exists
   today, unmodified — byte-identical fallback.

No change to `core/hooks/citation-gate.sh` in phase 2: the survey
finding (already role-free) is the deliverable for requirement 2, and
per the issue text itself no code change is made in that case.

## Out of scope

- Actually implementing the dual-read (this document is phase 1;
  implementation is phase 2, gated on this proposal's approval).
- Any change to `core/hooks/citation-gate.sh` (surveyed as
  already-role-free; no dual-read needed per issue requirement 2).
- Touching any other core gate (R1-R3, R5, or any hook outside
  board-gate.sh/citation-gate.sh).
- Changing the `.on-the-record/role.json` sidecar schema, its writer
  (`spawn.py:_write_role_sidecar`), or `spawn.py`'s branch-naming
  behavior (explicit non-goal 4 in the issue body).
- Removing the legacy branch-regex fallback itself — per the issue's
  non-goal list, "removing the fallbacks (legacy entries age out)" is
  explicitly out of scope; this phase only makes the convention
  non-load-bearing, not absent.

## How you'll know it worked

Per issue #1827's Acceptance section, quoted verbatim from
`gh issue view 1827` this session:

> 1. Core's live-fire matrix (5 cases above) green, executed live from
>    the core checkout, with the no-sidecar case byte-identical to
>    today.
>    - check: the live-fire run outputs pasted in the record, executed
>      live
>    - empty state: no-sidecar legacy workspace → both gates behave
>      byte-identically to today, asserted by dedicated cases
>    - provenance: executed-live
> 2. After the core PR merges, a role-free-branch spawn dry-run plus a
>    docs write through board-gate with sidecar present succeeds
>    end-to-end, and the on-the-record equivalence harness remains
>    green on unmodified main.
>    - check: the E2E run and
>      `python3 -m pytest test/test_convention_equivalence.py -q`
>      outputs pasted in the record, executed live
>    - empty state: n/a
>    - provenance: executed-live

The "5 cases" referenced are requirement 3's live-fire matrix: real
PreToolUse JSON via stdin to the real `.sh`, covering sidecar +
role-free branch, sidecar + legacy branch, no-sidecar legacy
(byte-identical), mismatch refusal, and corrupt-sidecar fallback — plus
the bash-3.2 guard test staying green. Phase 2's implementation report
must paste the live-fire run output, the E2E run output, and the
`python3 -m pytest test/test_convention_equivalence.py -q` output, all
executed live, not narrated.
