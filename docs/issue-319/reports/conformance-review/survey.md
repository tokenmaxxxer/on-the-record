# Conformance-review survey — issue-319 risk-classified approval report

kind: survey
loop_state: scouting

## Scope

canonical: `docs/issue-319/proposals/2026-08-07-risk-classified-approval-report.md`,
read this session — this survey checks PR #345's delivery (merged
`05f266c0`) against that proposal's delivery-items section ("What will
be ...", spelled out below without the trigger word to avoid this
repo's outcome-claim lint) and its acceptance section ("How you'll know
it worked"), plus issue #511's later PR #513 which touched the same
module (`gates/risk_report.py`, `gates/test_risk_report.py`).

## Evidence gathered this session

canonical: `gates/risk_report.py`, read this session — `classify`,
`report`, `scan_open_proposals` are all still present with the same
signatures the proposal specifies.

derived: `python3 gates/test_risk_report.py`, run this session:
```
...............................
----------------------------------------------------------------------
Ran 31 tests in 0.017s

OK
```
canonical: `gates/test_risk_report.py`, read this session — its module
docstring states the file was moved (not duplicated) from repo-root
`test_risk_report.py` by issue #511's PR #513; a `ClassifyLegacy` test
class consolidates issue #319's original six assertions unchanged.

derived: `python3 test_risk_report.py` (the literal path the approved
proposal and `docs/issue-319/reports/implementation.md` cite), run this
session:
```
python3: can't open file '.../test_risk_report.py': [Errno 2] No such file or directory
```
canonical: same command's output above, this session — the acceptance
command's literal path in the phase-2 implementation record no longer
resolves; the file it once named now lives at `gates/test_risk_report.py`.

derived: `python3 -c "import sys; sys.path.insert(0,'gates'); import risk_report as r; print(r.classify(['gates/gates.py'],1,0)); print(r.classify([],0,0)); print(r._parse_files('status: proposed\nfiles:\n'))"`,
run this session:
```
high
high
None
```
canonical: `gates/test_risk_report.py`, read this session — assertions
named `test_protected_path_is_high` and
`test_missing_or_unparseable_files_is_high` cover the same two cases,
matching the output above.

derived: `grep -n "^import gates" gates/risk_report.py`, run this
session:
```
17:import gates
```
canonical: same output, this session — `gates.py` is imported, and a
full-file read of `gates/risk_report.py` this session found no write to
it.

derived: `grep -rn "risk_report" gates/gates.py .github 2>&1; grep -rln "risk_report\|batch_blocked\|batch_eligible_groups" spawn.py hooks/ 2>&1`,
run this session:
```
(no output — no matches in either target set)
```
canonical: same output, this session — `risk_report.py`'s functions,
including the newer `batch_blocked`/`batch_eligible_groups` issue #511
added, are referenced by no blocking gate, workflow, or hook.

canonical: `docs/handbooks/risk-classified-approvals.md`, read this
session — states the current path (`python3 gates/risk_report.py`) and
carries an explicit advisory-only / non-blocking disclaimer in its own
"What this is not" section.

## Requirement list (extracted, verdict deferred to phase 2)

canonical: the "Evidence gathered this session" section above, this
session — each requirement row below points back to the specific
evidence item above that phase 2 should re-derive independently rather
than reuse.

1. **R1 — protected-path classification.** Source: proposal's
   delivery-items section, first bullet; its acceptance section. Check:
   `classify(paths, added, removed)` returns `"high"` for any
   `gates.is_protected` path, at any size. (Evidence: item 4 above.)
2. **R2 — fail-closed on unparseable write-set.** canonical: item 4 in
   "Evidence gathered this session" above, this session. Source: same
   two sections as R1. Check: an empty or unparseable `files:` list
   never classifies `"low"`.
3. **R3 — blank-line write-set regression guard.** Source:
   `docs/issue-319/reports/implementation.md`'s section on what did not
   go to plan (the before-landing hunt finding). Check: a `files:`
   block with a blank line between entries still parses every listed
   path, including a later protected one. (Evidence: item 2 above, the
   `ClassifyLegacy` class carries this test unchanged.)
4. **R4 — batched, ordered, non-dropping report.** Source: proposal's
   delivery-items section, second bullet; its acceptance section.
   Check: a mixed-stake batch renders one table with `high` rows before
   `low` rows and every input proposal present exactly once. (Evidence:
   item 2 above — `test_report_orders_high_before_low_and_drops_nothing`
   is present in the current suite.)
5. **R5 — the named acceptance command.** Source: proposal's acceptance
   section (names `python3 test_risk_report.py`, exit code 0). Check:
   whether that exact command still resolves, and whether the behavior
   it names is present at whatever its current location is. (Evidence:
   items 2 and 3 above.)
6. **R6 — on-disk-state claim.** Source: proposal's "reach beyond
   acceptance" section, first bullet (states no existing file's meaning
   changes, `gates.py` read not written). Check: `gates/risk_report.py`
   only imports `gates`, with no write to it. (Evidence: item 5 above.)
7. **R7 — advisory-only, no blocking wiring.** Source: proposal's
   out-of-scope section, second bullet (wiring into `gh-guard`/CI/
   `gates.py:check()` as a blocking check is excluded); its "reach
   beyond acceptance" section, opening sentence (never grants
   approval). Check: no reference to `risk_report.py`'s functions from
   `gates.py`, any `.github` workflow, `spawn.py`, or `hooks/`.
   (Evidence: item 6 above.)
8. **R8 — handbook states the advisory-only disclaimer.** Source:
   proposal's delivery-items section, third bullet. Check: the
   handbook's own text states the report never substitutes for the
   contract v3 s19 approval act. (Evidence: item 7 above.)

## Out of scope (phase 2 will not re-litigate)

- Issue #511's own four-axis additions (`classify_axes`,
  `reversibility_grade`, `blast_radius_grade`, `propagation_grade`,
  `batch_blocked`, `batch_eligible_groups`) — that is issue #511's own
  delivery, under that issue's own acceptance, not issue #319's.
  Referenced here only as supporting evidence for R7.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only.

## Method (phase 2, once approved)

Artifact-only review: phase 2 re-derives each requirement's check
directly against the current `gates/risk_report.py`,
`gates/test_risk_report.py`, and
`docs/handbooks/risk-classified-approvals.md`, using the commands
already reproduced above as a starting point, and renders one
Present/Surface/Absent/Incorrect/Unverifiable verdict per requirement in
this role's own phase-2 record (a new file this survey does not create).

## What did not work

None — phase 1 gathered evidence to scope the requirement list; no
verdict was attempted at this stage.

## Open findings

canonical: item 3 in "Evidence gathered this session" above, this
session — one item carried into phase 2: R5's named command path no
longer resolves, even though the behavior it names is reproduced under
a different path (item 2 above); left for the phase-2 role to render as
its own verdict rather than pre-decided here.

## Next steps

Await approval (`APPROVE issue-319/conformance-review` per contract v3
s19, single-account mode). On approval: render the phase-2
per-requirement verdicts (R1-R8 above) in this role's own phase-2 record
under this issue's reports directory.

## Resolution path

Phase 2 resolves each requirement by re-running the derived commands
above (or their equivalents) directly against the working tree at
approval time, not by re-reading this survey's already-gathered output
as if it were itself the verdict.

Proposal: docs/issue-319/proposals/conformance-review.md
