---
issue: 3134
role: implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310
author: implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310
skills: implementation-blueprint (skill-repository(c05de12)), knowledge-management-supersession-lifecycle (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # this is a repair round on PR #3143's own deliverable, not an independent verification of it
loop_state: landed
upstream:
  - path: docs/issue-3134/reports/implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2.md
    sha: 52c981f5dd0fd06ab4d73447c8d90a3e50d77595
  - path: docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md
    sha: 4671de88e50c26cc66e119a11d48736c1c743703
---

# issue-3134 — implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310 record

## What was done

canonical: `docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md` (PR #3146, sha `4671de88`), read in full — the verdict section states check 2 Absent and must-not 1 Surface, quoted verbatim in "Why" below.
canonical: `gh pr view 3143` output (state: OPEN, headRefName: `issue-3134/implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2`)

A repair round on PR #3143, addressing the two findings PR #3146's
independent verification raised: check 2 Absent (discoverability) and
must-not 1 Surface (wiring). Resolution and fails-closed behavior were
already Present and are untouched.

Delivered, pushed to PR #3143's own branch (commit `1eb52701`, then
merged forward onto this session's own branch — see "Upstream basis"):

1. **`amends_backlink.py`** (new, domain layer, root-level, mirrors
   `amends.py`'s no-filesystem contract): `render_backlink_marker`,
   `has_backlink`, `insert_backlink`, `apply_backlinks`,
   `missing_backlinks`. Computes the backlink text a LANDING step
   inserts directly into an amended target's own content, right under
   the heading it corrects.
2. **`gates/amends_index.py`** extended: `check()` now fails closed on
   two independent axes — index staleness (unchanged from PR #3143) AND
   any unambiguous `amended` edge whose target lacks the backlink
   (`amends_backlink.missing_backlinks`). New `write_backlinks()` /
   `--apply-backlinks` CLI mode performs the landing-step write.
   `amends.py` gained a shared `extract_reason()` (moved out of this
   module's former private `_reason()`), reused by both the index-row
   renderer and the backlink marker.
3. **`on-the-record/hooks/amends-index-preflight.sh`** (new): wires
   `amends_index.check()` into commit-time enforcement, joining
   `spec-index-preflight.sh`'s `git commit` matcher group, narrowed to a
   staged `docs/issue-*/reports/**/*.md` or `docs/specs/amends-index.md`
   change. Registered in `on-the-record/hooks/pretooluse_dispatcher.py`'s
   `GATES` list — the actual live-wiring point in this repo (issue #2146
   migrated every individual `PreToolUse` gate behind one dispatcher; no
   gate here carries its own direct `hooks.json` command entry, only
   `pretooluse-dispatcher.sh` does).
4. **`gates/probe_amends_is_discoverable.py`** rewritten: instead of
   asserting the amendment is reachable by "consulting the generated
   index" (what PR #3143 shipped, graded Absent), it now asserts three
   reader routes against a LANDED fixture tree (post `apply_backlinks()`)
   — open the amended record directly, grep the wrong claim's own text
   and find the correction within 4 lines, follow an inbound link from
   an unrelated third record into the amended section — plus `check()`
   failing closed on the index axis and the backlink axis
   independently, and passing only once both are landed.
5. `docs/specs/enforcement-boundary.md` / `docs/specs/generated-paths.md`
   rows for the three previously-unregistered `gates/*.py` probes/module
   and the new hook; `docs/handbooks/record-authoring.md` /
   `record-contract.md` updated to describe the backlink+landing-step
   shape instead of the index-only shape.
6. Tests: `tests/test_amends_backlink.py` — derived: `python3 -m pytest tests/test_amends_backlink.py -q` → 14 passed (marker rendering, idempotent insertion, missing-anchor `ValueError`, two-sections-one-target, `apply_backlinks`/`missing_backlinks` over the base/broken/conflict/cycle partitions `tests/test_amends_resolution.py` already established) and `tests/test_amends_index_wiring.py` — derived: `python3 -m pytest tests/test_amends_index_wiring.py -q` → 3 passed (`check()` against `ROOT` itself, and against a real on-disk copy with an injected unlinked amendment, before and after landing).

Acceptance checks, re-run on this session's own merged branch (this
session's branch now contains PR #3143's original two commits plus this
round's fix commit, merged forward onto latest `main` — see "Upstream
basis"):

acceptance: python3 -m pytest tests/test_amends_resolution.py -q — result: PASS
```
19 passed in 0.83s
```
acceptance: python3 gates/probe_amends_is_discoverable.py — result: PASS
```
-- confirmed Route 1: opening A directly surfaces the amendment ...
-- confirmed Route 2: grepping the wrong claim's own text ... lands within 2 line(s) of the amendment marker ...
-- confirmed Route 3: following a link into A's `limitation` anchor ... still surfaces the marker immediately --
ok
```
acceptance: python3 gates/probe_amends_fails_closed.py — result: PASS
```
ok
```
acceptance: python3 -m pytest tests/ -q — result: PASS
```
323 passed, 2 warnings in 10.60s
```
acceptance: python3 -m pytest test/ -q — result: PASS
```
563 passed, 3 xfailed in 32.34s
```

derived: `python3 -m pytest tests/ -q` on PR #3146's checked-out branch (PR #3143's branch alone) returned 273 (cited in the upstream verification record); the same command on THIS session's branch (that branch's tip merged forward onto current `main`) returns 323 — the +33 delta over 290 (273 + this round's own 17 new tests) is main commits that landed after PR #3143 branched (`4671de88`/`c76d0662`/`ac157167`/`82156c31`/`796684d9`, none touching `amends*.py`/`gates/amends_index.py`), not a regression.

derived: `python3 -m pytest test/ -q` on this session's branch returns 0 failed (563 passed, 3 xfailed) because this branch is merged forward onto current `main`, which already carries whatever landed to fix the 15 pre-existing failures the task described (owned by #3091) since PR #3143 branched; re-running the identical command directly on PR #3143's own branch before the merge still reproduces exactly 15 failures (`test_convention_equivalence.py` x2, `test_local_dependency_env.py` x1, `test_spawn_cross_family_skill_selection.py` x5, `test_spawn_skill_judge_haiku_timeout_overlap.py` x4, `test_spawn_artifact_skill_pairing.py` x2, `test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest` x1), confirming they are pre-existing and unrelated to this round.

## Why

canonical: `docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md` — verdict quote: "Check 2 (`gates/probe_amends_is_discoverable.py`) — **Absent**. The probe exits 0 but only because it redefines 'reaching A' as 'consulting the generated index,' not 'opening A.'" and "Must-not 1 ... — **Surface**. ... nothing forces it to be invoked: no `PreToolUse` hook wires it in ..., the three new `gates/*.py` files were never registered in `docs/specs/enforcement-boundary.md`, and `tests/` never exercises `check()` against the real tree."

**Discoverability (check 2).** The independent verification found
`probe_amends_is_discoverable.py` defined "reaching A" as "consulting
the generated index" rather than "opening A" — a reader who does not
already know the index convention exists has no path to the correction,
and A's own raw content carried zero signal. The issue's own text names
the fix: a required backlink in the target, with discoverability
meaning a reader who opens the amended record directly cannot miss the
amendment.

That collides with write-set isolation: the correcting session's own
`Edit`/`Write`/`Bash` calls against a foreign issue's `docs/issue-<n>/`
tree are refused live by board-gate — reproduced directly in this
session (see "What did not work" below), not merely asserted from the
original module's docstring. So the backlink cannot be written by the
correcting session, ever, regardless of sequencing.

Three shapes were on the table (recorded in full in
`amends_backlink.py`'s module docstring and `amends.py`'s revised
"Discoverability decision" section):

1. Backlink in the SAME commit as the correcting session's own record.
   Rejected — not a design trade-off, a hard impossibility under
   write-set isolation (reproduced live, not merely asserted — see
   "What did not work").
2. The generated index alone. This is what PR #3143 shipped and what
   the verification found Absent (canonical quote above). Kept, but
   demoted to a supplementary cross-cutting view ("what in this tree has
   an open correction"), not the primary mechanism.
3. A backlink applied by the LANDING step — the orchestrator/operator
   identity `merge-allow-gate.sh` already distinguishes via
   `TOKENMAXXXER_SPAWNED` resolving empty, not bound to any single
   issue's branch — after the correcting PR lands, gated so an `amends:`
   edge cannot be called linked until it happens. Adopted:
   `gates/amends_index.py --apply-backlinks` / `write_backlinks()`
   performs it; `check()`'s `missing_backlinks` reasons refuse to let it
   go missing.

**Wiring (must-not 1).** `amends_index.py::check()` was correct but
unreachable per the canonical quote above. Followed the stated
precedent for the TRIGGER (join `spec-index-preflight.sh`'s `git commit`
matcher group), but not for the IMPLEMENTATION shape: `check()` composes
three modules (`amends.py`, `amends_backlink.py`, `amends_index.py`
itself) over an unbounded glob, a much larger surface to hand-port
inline (spec-index-preflight.sh's own approach) and keep byte-for-byte
in sync than that hook's single self-contained hash comparison.
Followed `quality-bar-gate.sh`/`merge-allow-gate.sh`'s alternate,
equally-established precedent instead: resolve a checkout carrying
`gates/`, import the real modules, run the real function — fails open
(no consumer-reach claim; `amends:` is repo-local, same class as
`spec_index.py`) when this checkout carries no `gates/amends_index.py`.

**Test derivation (test-derivation skill, applied).** The
discoverability requirement's shape is "every reader route must surface
the amendment" — not a single input/output pair, so it routed to
Given-When-Then scenarios per named route rather than EP/BVA (no ordered
input domain to partition): Given a landed fixture tree, When a reader
opens the amended record directly / greps the wrong claim's own text /
follows an inbound link into the amended section, Then each surfaces the
amendment (`gates/probe_amends_is_discoverable.py`'s three routes). The
backlink's own lifecycle (a data-shape/structural concern, same shape as
`resolve_amendments()`'s own derivation in `tests/test_amends_
resolution.py`) routed to equivalence partitioning over the marker's
presence/absence and the edge's amended/broken/missing_section/conflict/
cycle partitions (`tests/test_amends_backlink.py`, mirroring the eight
partitions `test_amends_resolution.py` already established one layer
up). High risk classification (Step 3a): a bug here reproduces the exact
defect class the repair round exists to close.

derived: `python3 /home/jwjung/skill-registry/skills/implementation-blueprint/scripts/prep.py classify --surface backend --external no --logic rich --asynchronous no` → `ARCHETYPE: domain-rich`; `python3 /home/jwjung/skill-registry/skills/implementation-blueprint/scripts/prep.py recommend domain-rich --team 1` → confirmed the domain-layer/infra-layer split (`amends_backlink.py` pure functions vs `gates/amends_index.py` filesystem I/O) already established by `amends.py`/`supersession.py`, and that the four work units (backlink domain module, index/gate wiring, probe rewrite, tests) stayed under the 5-unit solo-build threshold — no fan-out.

**Silent-failure audit (silent-failure-audit skill, applied).** Four
`except` blocks were added, all in
`on-the-record/hooks/amends-index-preflight.sh`: `except ValueError`
(shlex tokenization), `except (OSError, subprocess.SubprocessError)`
(`git diff --cached`), `except ImportError` (`import amends_index`).
Each is followed by `sys.exit(0)` — classified Handled (H), not Silently
Absorbed: this is a documented, deliberate fail-OPEN contract identical
to every sibling hook's own stated policy. canonical:
`on-the-record/hooks/spec-index-preflight.sh` lines 16-22 (read in
full): "Fail-open by design: any environment gap ... exits 0 rather than
blocking an unrelated or best-effort commit. What must never happen is
silently allowing a commit this script positively determined has
drifted a tracked spec file without a matching index update in the same
staged set; that path is the only one that exits 2." The bar this audit
applies is whether an error the code POSITIVELY determined should block
gets swallowed — none of the four new sites make that determination;
each represents "this hook cannot form an opinion here" (missing
git/python, unparseable command, no `gates/` checkout), the same
degrade path every sibling gate in this family uses, not a stubbed-out
failure path. `amends_backlink.insert_backlink`'s `ValueError` on a
missing anchor is the one new fail-CLOSED path (a caller-contract
violation, not a data condition) — propagates, uncaught, by design (see
its own docstring, `amends_backlink.py` lines 90-99).

## What did not work

canonical: this session's own Bash tool transcript (Write and Bash tool
calls against `docs/issue-99999/reports/scratch-test.md` and
`docs/issue-3134/reports/scratch/scratch-test.md`, both untracked and
never committed — neither path exists in the tree or in git history;
referenced here only as the literal targets of the refused write
attempts).

A live-fire reproduction of the write-set-isolation deadlock this round
had to design around: attempted a `Write` tool call, then a `Bash: cat >
... <<EOF` call, against `docs/issue-99999/reports/scratch-test.md`
(untracked, never landed) and then against
`docs/issue-3134/reports/scratch/scratch-test.md` (untracked, never
landed) while checked out on PR #3143's own branch
(`...-ba3ca3d2`) — both refused live by board-gate:

```
board-gate: writing docs/issue-3134/ requires branch issue-3134/implementation-blueprint+knowledge-management-supersession-lifecycle+silent-failure-audit+test-derivation-95735310 (current: issue-3134/implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2), and issue #?'s body declares no matching `maintenance-targets:` entry for issue-3134. Every skill output reaches main only through a PR the human merges — never a direct write from another branch. (contract v3 s10)
```

This confirms directly (not merely citing PR #3050's prior docstring
claim) that this session's own tool calls cannot reach a foreign
`docs/issue-<n>/` tree — including this record's own path while checked
out on the wrong branch. Resolved by merging PR #3143's branch forward
onto this session's own identity-matched branch (`git merge --no-edit`,
one file auto-merged cleanly: `docs/specs/enforcement-boundary.md`)
before writing this record, then pushing the merged branch back onto PR
#3143's remote ref (`git push origin <local>:<remote ba3ca3d2 ref>`, a
fast-forward since the local branch contains the remote's prior tip as
an ancestor). Both scratch paths above were removed (`git reset` + `rm
-rf`) before any commit; neither ever landed, and neither exists in the
tree today.

## Upstream basis

- `docs/issue-3134/reports/implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2.md`
  (sha `52c981f5dd0fd06ab4d73447c8d90a3e50d77595`) — PR #3143's own
  delivery record.
- `docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md`
  (sha `4671de88e50c26cc66e119a11d48736c1c743703`) — PR #3146's
  independent verification, the source of both findings this round
  addresses.

canonical: `git log --oneline -1 -- docs/issue-3134/reports/implementation-blueprint+knowledge-management-supersession-lifecycle+test-derivation+silent-failure-audit-ba3ca3d2.md` → `52c981f5`
canonical: `git log --oneline -1 -- docs/issue-3134/reports/adversarial-review+knowledge-management-supersession-lifecycle+defect-verification-independence-from-upstream-verdicts-29406a3a.md` → `4671de88`

## Open findings

None new. The verification's fourth finding ("the PR #11 disposition
case — Surface: delivers no reader-facing correction yet for someone who
opens PR #11's record directly" — canonical quote, upstream verification
record) is resolved by this round's mechanism (a landed backlink makes
exactly that reader-facing correction real), but applying it to the
actual study-companion PR #11/#15 pair is explicitly out of scope here —
the issue's own must-not 3 forbids retrofitting those two existing
records as part of this issue ("do not retrofit the two existing
study-companion verification records into `amends:` edges as part of
this issue... it needs its own decision").

## Next steps

None from this session — PR #3143 is pushed and awaiting the next
verification round. If a future round finds the checkout-resolve-and-
import shape (rather than a full inline port) insufficient for
`amends-index-preflight.sh`'s zero-install claim, that would be the next
open question; not raised as a finding here since `amends:` is
repo-local by the same reasoning `spec_index.py` already carries in
`docs/specs/enforcement-boundary.md`.

derived: skill-verdict provenance — `python3 /home/jwjung/skill-registry/skills/implementation-blueprint/scripts/prep.py classify --surface backend --external no --logic rich --asynchronous no` → `ARCHETYPE: domain-rich` (implementation-blueprint); the silent-failure-audit and test-derivation applications are the reasoning in "Why" above, run inline in this session, not a separate re-runnable command.

skill-verdict: implementation-blueprint — applied: invoked; derived tag immediately above — confirmed domain/infra layer split and solo-build threshold
skill-verdict: silent-failure-audit — applied: invoked; audited all four new `except` sites (see "Why" above), classified Handled, none Silently Absorbed
skill-verdict: test-derivation — applied: invoked; routed the three-reader-route requirement to Given-When-Then scenarios and the backlink lifecycle to equivalence partitioning (see "Why" above)
skill-verdict: knowledge-management-supersession-lifecycle — not-applicable: this task builds the `amends:`/backlink mechanism itself, not a decision to mark an existing knowledge-library entry superseded or deprecated
other mounted skills: not triggered (work-in-english, implementation-audit, test-depth-audit, technical-feasibility-reversibility-tag, prose-modes, premortem)
