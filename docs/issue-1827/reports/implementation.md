---
code_under_review:
  - core/hooks/board-gate.sh
  - core/hooks/tests/run-board-gate-tests.sh
loop_state: committing
type: feature
breaking: false
verdict: pass
---

# issue-1827 implementation record

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-1827/proposals/board-gate-citation-gate-carrier-aware.md`)
as a PR against the target repo `tokenmaxxxer/tokenmaxxxer-core`.

canonical: git -C /home/jwjung/tokenmaxxxer-core log -1 --format=%H (branch issue-1827/board-gate-carrier-aware, this session)
PR: https://github.com/tokenmaxxxer/tokenmaxxxer-core/pull/268, commit `9cc638d93aa7b0b4cea03778b27734706f33d996`.

1. `core/hooks/board-gate.sh` R4 (`:719-784` before edit) now reads
   `.on-the-record/role.json` right after the existing
   `symbolic-ref --short HEAD` branch resolution, adapting the
   sidecar-preferred / independent-branch-cross-check /
   fail-closed-on-mismatch shape already landed for
   `on-the-record/hooks/approval-gate.sh:109-169` (#1821):
   - Sidecar parsed the same way (`{"role": str, "issue": int}` shape
     required; `OSError`/`ValueError`/shape mismatch leaves it `None`
     and falls through to legacy).
   - canonical: git -C /home/jwjung/tokenmaxxxer-core diff main issue-1827/board-gate-carrier-aware -- core/hooks/board-gate.sh (this session)
     When the sidecar resolves AND the branch independently parses as a
     full `issue-N/role` shape, a disagreeing pair (issue or role)
     fails closed immediately with a deny naming both the sidecar and
     branch-parsed values — before the per-hit loop runs.
   - The per-hit loop's comparison changed from a single
     `branch == "issue-<n>/<role>"` string check to: if the sidecar
     resolved, allow iff the hit's own issue number equals the sidecar
     issue AND `sidecar.role == CLAUDE_ROLE`; if the sidecar did not
     resolve, run exactly the pre-existing string comparison,
     unmodified.
   - canonical: git -C /home/jwjung/tokenmaxxxer-core diff main issue-1827/board-gate-carrier-aware -- core/hooks/board-gate.sh (this session)
     The maintenance-targets exception block (`:734-768`) and R1-R3/R5
     are the only other code in the file's R4 area and are not part of
     the diff above — no lines outside the two edited hunks changed.
2. `core/hooks/citation-gate.sh`: no code change, per the survey's
   finding (issue requirement 2) that `CIT_BRANCH` is consumed only
   through `citation-config.json:185`'s `branch_regex`
   (`^issue-(\d+)/`), which captures the issue number only and never a
   role segment — already role-free.
3. `core/hooks/tests/run-board-gate-tests.sh`: added a `runs()` helper
   (sidecar variant of the existing `runb()`) and a 5-case sidecar
   live-fire matrix — sidecar + role-free branch, sidecar + legacy
   branch (values agree), no-sidecar legacy (byte-identical), sidecar
   vs. legacy-branch mismatch (fail-closed), and corrupt-sidecar
   fallback to legacy.

### Live-fire matrix (executed live, from the core checkout)

canonical: bash /home/jwjung/tokenmaxxxer-core/core/hooks/tests/run-board-gate-tests.sh (this session)
acceptance: bash core/hooks/tests/run-board-gate-tests.sh — result: pass

```
ok     sidecar-role-free-branch           allow
ok     sidecar-legacy-branch-agree        allow
ok     no-sidecar-legacy                  allow
ok     sidecar-branch-mismatch            deny
ok     corrupt-sidecar-falls-back         deny

== 135 passed, 0 failed ==
```

derived: bash /home/jwjung/tokenmaxxxer-core/core/hooks/tests/run-board-gate-tests.sh 2>&1 | grep -c '^ok' (this session) — 135 `ok` lines, 0 `FAIL` lines, matching the printed summary exactly; this is the full suite (130 pre-existing cases plus the 5 new sidecar cases), no subset run. `bash -n core/hooks/board-gate.sh` also ran clean (syntax OK) before the suite.

### E2E: role-free-branch write through board-gate with sidecar present

canonical: bash /tmp/e2e-1827/run.sh (this session; scratch git repo checked out on branch `issue-3`, no role segment, `.on-the-record/role.json` containing `{"role":"qa","issue":3}`)
acceptance: role-free branch `issue-3` + sidecar naming issue 3 / role qa, real `board-gate.sh` subprocess invoked against a Write of a docs report file under that scratch tree's issue-3 board — result: pass

```
exit=0
```

The same live-fire run above includes the pre-existing `board-right-branch`
legacy case (no sidecar) still passing, confirming the no-sidecar path
stays byte-identical alongside this new sidecar-driven allow.

### spawn dry-run (unaffected-path confirmation)

canonical: python3 spawn.py implementation "dry-run smoke for issue-1827 E2E" --dry-run (this session, on-the-record checkout)
acceptance: spawn.py --dry-run for role implementation — result: pass (exit 0, merged config JSON printed to stdout, no session launched, no workspace/network side effect)

Confirms `spawn.py`'s branch-naming/session-launch path is unmodified by
this change (explicit non-goal 4 of the issue and proposal).

### Equivalence harness (on unmodified on-the-record main)

canonical: python3 -m pytest test/test_convention_equivalence.py -q (this session, on-the-record checkout, branch issue-1827/implementation, no code changes in this repo)
acceptance: python3 -m pytest test/test_convention_equivalence.py -q — result: pass

```
.................................                                        [100%]
33 passed in 0.81s
```

No SKIPPED lines appear in the output; 33 is the collected-and-passed
count shown in the pasted summary line itself.

## Why

Issue #1827 is phase 5 FINAL of the skill-axis removal cycle
(`gh issue view 1827`, this session): core's `board-gate.sh` R4 and
`citation-gate.sh` were the last two mechanisms that made the
role-name-in-branch convention load-bearing. This applies the same
sidecar-preferred / legacy-fallback / fail-closed-on-mismatch shape
used for the prior dual-read phases, so that after tokenmaxxxer-core#268
merges, no core enforcement requires the role string inside a branch
name; branch names may still carry it cosmetically but nothing parses
that segment as authority.

## Upstream basis

Based on: `docs/issue-1827/proposals/board-gate-citation-gate-carrier-aware.md`
(this repo, approved via `APPROVE issue-1827/implementation` on issue
#1827) and `docs/issue-1827/reports/implementation/survey.md`. Pattern
reused verbatim in shape from `on-the-record/hooks/approval-gate.sh:109-169`
(#1821).

## What did not work

None — the proposal's chosen shape (reuse of the approval-gate.sh
dual-read pattern) implemented cleanly against R4's existing structure
with no rework needed; no alternative approach was attempted and
discarded during phase 2.

## Open findings

None. The one open question the survey flagged — citation-gate.sh's
`CIT_BRANCH` derivation using `rev-parse --abbrev-ref` while
board-gate.sh uses `symbolic-ref --short` — was already recorded in the
survey as a pre-existing inconsistency out of scope for this issue, and
remains out of scope here; no new finding surfaced during phase 2.

## loop_state

`committing`: tokenmaxxxer-core#268 is pushed and open against `main`
on the target repo, carrying the live-fire-verified change.

canonical: gh pr view 268 --repo tokenmaxxxer/tokenmaxxxer-core --json state,mergedAt (this session)

```
{"mergedAt":null,"state":"OPEN"}
```

This on-the-record PR carries the phase-2 record itself.

## Next steps

Await review and merge of tokenmaxxxer-core#268. No further action is
expected in this repo for issue #1827 once that merges — the issue's
Acceptance criteria are both satisfied by the runs pasted above,
executed live this session.

## Resolution path

If tokenmaxxxer-core#268 requires changes during review, push follow-up
commits to the same `issue-1827/board-gate-carrier-aware` branch there;
no new proposal round is needed unless the requested change alters the
approved design (sidecar-preferred + fail-closed-mismatch +
byte-identical fallback) rather than refining its implementation.
