---
issue: 2651
role: architecture-interface-contract-shape+silent-failure-audit-fb35aea0
author: architecture-interface-contract-shape+silent-failure-audit-fb35aea0
skills: architecture-interface-contract-shape (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
code_under_review:
  - spawn.py
  - board.py
type: fix
breaking: true
verdict: pass
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2628/reports/adversarial-review+silent-failure-audit-f8365dc9.md (the "dead, unrelated ... LEGACY dict" classification issue #2651 corrects)
    sha: same-commit
  - path: docs/issue-2628/reports/conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-2d6823f8.md (the second "pre-existing, out-of-scope LEGACY dict" classification issue #2651 corrects)
    sha: same-commit
---

# issue-2651 — architecture-interface-contract-shape+silent-failure-audit-fb35aea0 record

## What was done

canonical: `gh issue view 2651` — the issue states PR #2640's independent
verifications called `LEGACY` dead/unrelated, and that this is wrong
because `board.py:826` reads it. Checked both prior classifications
directly:

```
docs/issue-2628/reports/adversarial-review+silent-failure-audit-f8365dc9.md:73-75:
spawn.py:9,740,1548,3673 — CLI help text + LEGACY dict (0 usages anywhere
  else in spawn.py, per `grep -n '\bLEGACY\b' spawn.py` — dead, unrelated
  to spawn_on_pr's auto-spawn decision, out of this issue's Non-goals scope)
```
```
docs/issue-2628/reports/conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-2d6823f8.md:144-146:
text + 2 unrelated comments + a pre-existing, out-of-scope `LEGACY` dict
(`spawn.py:740`) containing only 1 of the 2 member samples;
```
Both checked `LEGACY` usage only *within spawn.py itself* (`grep -n
'\bLEGACY\b' spawn.py`) and missed the cross-module reader. Confirmed the
issue's correction independently, pre-change:

```
board.py:826:    stale = sorted(r for r, name in _sp.LEGACY.items()
board.py:827:                   if (root / name).exists() or (root / "docs" / name).exists())
board.py:828:    if stale:
```
`board.py:826` does read `_sp.LEGACY` (`_sp` is the `spawn` module object,
per board.py's own module docstring, `board.py:8-13`). The earlier
"dead"/"out of scope" classification was wrong on that point; the issue's
correction is confirmed, not assumed.

Removed the identity-keying rather than moving/hiding it. `LEGACY` (a dict
keyed by four retired role-identity strings — `conformance-review`,
`technical-feasibility`, `release-engineering`, `product-discovery` —
mapped to legacy filenames) became `LEGACY_FILES`, a plain tuple of the
same four filenames with no identity dimension:

```
spawn.py:750-751 (post-change):
LEGACY_FILES = ("review-record.md", "feasibility-record.md", "state.md",
                "product-record.md")
```
`board.py:826-827` (post-change) iterates the tuple directly instead of
`.items()`, and `stale` now holds matched **filenames**:

```
board.py:826-827 (post-change):
    stale = sorted(name for name in _sp.LEGACY_FILES
                   if (root / name).exists() or (root / "docs" / name).exists())
```

acceptance: `grep -n 'LEGACY' spawn.py board.py` — result:
```
board.py:826:    stale = sorted(name for name in _sp.LEGACY_FILES
spawn.py:274:_LEGACY_WORKSPACE_KEY_RE = events._LEGACY_WORKSPACE_KEY_RE
spawn.py:425:LEGACY_MONITOR_ALIVE_DIRNAME = lifecycle.LEGACY_MONITOR_ALIVE_DIRNAME
spawn.py:750:LEGACY_FILES = ("review-record.md", "feasibility-record.md", "state.md",
```
derived: `grep -nE 'conformance-review|technical-feasibility|release-engineering|product-discovery' spawn.py board.py` (full-file, not restricted to the LEGACY lines above) — result:
```
board.py:587:    for r in ("product-discovery", "technical-feasibility"):
board.py:897:        if role == "technical-feasibility" and rest.startswith("spikes/"):
board.py:899:        if role == "release-engineering" and rest.startswith("postmortems/"):
spawn.py:9:  python3 spawn.py --skills conformance-review-verdict-assignment "PR 12 를 리뷰해라" --issue 12
```
None of these four hits are on a `LEGACY`/`LEGACY_FILES` line — none are
keyed by, or print, a retired identity name as part of *this* issue's
target (the `LEGACY` dict and its consumer). Hand-classified below.

Ran the mechanical removal-claim tool the issue-2628 architecture record
(this role's own prior delivery) used for the same kind of claim.
acceptance: `python3 scripts/audit_removal_claim.py /tmp/audit_claim_2651_repro.json --root .` where the claim file was `{"name": "LEGACY dict identity-keying removed", "removed_names": ["LEGACY"], "member_samples": ["conformance-review", "technical-feasibility", "release-engineering", "product-discovery"], "min_coloc": 2}` — result:
```
verdict: RESHAPE_DETECTED
q1 live_hits (LEGACY substring): lifecycle.py, board.py, events.py,
  spawn.py, ledger/collect.py, __pycache__/*.pyc,
  runs/rulebooks/tokenmaxxxer-core/core/hooks/record-fields-gate.sh
q2 colocated_files (>=2 of the 4 name strings, non-doc/non-test): board.py
  (3), gates/gates.py (3), on-the-record/gates/gates.py (3),
  .claude-plugin/marketplace.json (4), on-the-record/commands/run.md (2),
  on-the-record/hooks/merge-allow-gate.sh (2),
  on-the-record/monitors/test_poll_heartbeat.py (2),
  runs/rulebooks/tokenmaxxxer-core/core/hooks/{board-gate.sh,
  citation-gate.sh, test_board_gate.py} (2 each), plus .git internals
q3 branch_hits: [("technical-feasibility", "./board.py"),
  ("release-engineering", "./board.py")]
```
Hand classification, per the tool's own documented caveat that Q1/Q2/Q3
are blunt greps requiring manual review (the same caveat the issue-2628
architecture record applied to its own `AUTO_SPAWN_ROLES` claim):
- Q1 `LEGACY` hits: substring false positives —
  `_LEGACY_WORKSPACE_KEY_RE` (events.py/spawn.py/lifecycle.py, an
  unrelated workspace-key regex) and `LEGACY_MONITOR_ALIVE_DIRNAME`
  (lifecycle.py/spawn.py, an unrelated monitor dirname) predate this
  issue and are untouched; `spawn.py`'s own hit is `LEGACY_FILES`, this
  change's own replacement, which carries no identity keys; `board.py`'s
  hit is the tuple-iterating line quoted above; `ledger/collect.py`'s
  `LEGACY = "review-record.md"` is the issue's own Non-goal (checked,
  single filename constant, not an identity set, left untouched); the
  `record-fields-gate.sh`/`__pycache__/*.pyc` hits are an unrelated
  rulebook hook and stale compiled bytecode, neither of which is source
  this issue's Ask covers (spawn.py/board.py only).
- Q2/Q3 hits outside `board.py`: none of these files read
  `_sp.LEGACY`/`_sp.LEGACY_FILES` — confirmed above (`grep -rn
  "_sp\.LEGACY\b" .` found only `board.py`, now updated to
  `LEGACY_FILES`) — so none reconstruct *this issue's* removed dict under
  another name; they are separate, pre-existing uses of the same literal
  strings for unrelated purposes (e.g. CLI examples, marketplace/hook
  config), out of this issue's Ask (spawn.py/board.py's `LEGACY` and its
  one reader) and out of its Non-goals note ("prose ... elsewhere ...
  #2139 owns those").
- Q2/Q3 hits inside `board.py` (`board.py:587,897,899`): pre-existing,
  unrelated heuristics — `_front_role` (board.py:584-588) uses
  `("product-discovery", "technical-feasibility")` only as a tie-break
  order among roles that already have records for a subject (not a
  membership test against a closed set of *valid* identities — any role
  slug can appear in `roles`); `ownership_report` (board.py:895-900)
  special-cases two report subdirectories (`spikes/`, `postmortems/`) by
  comparing the *caller's own declared role* string, not validating it
  against an enumerated set. Neither reads `LEGACY`/`LEGACY_FILES`,
  neither is "printed to the consumer" the way the issue's Ask describes.
  Left untouched — out of scope for this issue's Ask.

Demonstrated both no-board states against a fixture repo
(`docs/specs/approvers.md` present, no `docs/issue-*` tree). canonical:
this turn's own live run of `board.status()` against a fresh
`tempfile.mkdtemp()` fixture (script written to `/tmp/fixture_demo_2651.py`
outside the repo write set, run, then deleted) — result:
```
=== STATE 1: nothing written yet (no legacy files, no board) ===
프로젝트: tmpmqj95r30   경로: /tmp/tmpmqj95r30
보드 없음 (docs/issue-<n>/). 아직 아무 역할도 기록을 쓰지 않았다.

=== STATE 2: pre-v3 layout (legacy files present: review-record.md, product-record.md) ===
프로젝트: tmpmqj95r30   경로: /tmp/tmpmqj95r30
보드 없음. 계약 v1 자리에 기록이 있다: product-record.md, review-record.md
  이 레포는 v3 이전 판이다. v3 는 docs/issue-<n>/reports/<역할>.md 다.
```
The two states remain distinguishable — the distinction survives on the
dict's values (legacy filenames) alone; the keys (identities) were not
needed for it, so no capability was dropped. The board's behavior on the
path where a board exists (`board.status()`'s `if b:` branch, board.py:792
onward) was not touched — only the no-board path (`board.py:825-833`) was
in scope, per the issue's `must not`.

acceptance: `python3 -m pytest test/ -k "board or legacy or status" -q` —
result:
```
20 passed in 1.01s
```
acceptance: `python3 -m pytest test/ -q` — result:
```
15 failed, 342 passed in 2.75s
```
derived: `git stash && python3 -m pytest test/ -q; git stash pop` (this
turn, against the pre-change tree) — result:
```
15 failed, 342 passed in 2.31s
```
The same 15 test IDs (by name, compared in this turn's own tool output)
fail on both the pre-change and post-change tree — pre-existing failures
in unrelated subsystems (`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_convention_equivalence.py`), not caused by this change.

skill-verdict: silent-failure-audit — not-applicable: the diff (a tuple
literal in spawn.py, and a comprehension-header change in board.py) adds
no try/except, no error-first callback, and no new fallible operation; the
`Path.exists()` calls are the same calls with the same arguments as the
pre-change code and are not part of this diff's error-handling surface.
skill-verdict: architecture-interface-contract-shape — not-applicable:
this issue is not a service/module boundary-contract shape decision (sync
vs. async, orchestration vs. choreography, ACL vs. Conformist); it is
removing an identity-keyed closed set per operator ruling, with no
sync/async or orchestration-style boundary choice in question.

## Why

canonical: `gh issue view 2651` — supplies the correction and the design
question together, and the operator ruling (2026-08-27, in the Acceptance
`must not` line): if the "pre-v3 vs. nothing-written" distinction needs
identity enumeration, drop the capability and say so; if it survives on
filenames alone, keep the capability but drop the identities.

Reading the one consumer, `board.py:826-830` pre-change:
```
    stale = sorted(r for r, name in _sp.LEGACY.items()
                   if (root / name).exists() or (root / "docs" / name).exists())
    if stale:
        out.append(f"보드 없음. 계약 v1 자리에 기록이 있다: {', '.join(stale)}")
        out.append("  이 레포는 v3 이전 판이다. v3 는 docs/issue-<n>/reports/<역할>.md 다.")
```
(derived: `git show HEAD:board.py | sed -n '826,830p'`, run this turn),
showed the capability only ever needed "does this legacy filename exist on
disk" — the role name was never load-bearing for the existence check
itself, only for the printed message, which is exactly the surface the
issue is about. The minimal-loss path is therefore a plain tuple of
filenames: the pre-v3/nothing-written distinction is fully preserved
(demonstrated above under "What was done", both fixture states), and the
retired vocabulary is gone from both the data structure and the printed
message. No capability was dropped, so there is nothing to state as lost.

Why a tuple and not, say, a `set` or a second dict keyed by filename: the
consumer (`board.py:826-827`) only ever needs "iterate, check existence,
collect matches" — the original code already used `sorted(...)` to
normalize order, so an unordered container loses nothing and a dict adds
a key axis (filename -> filename) with no behavior it would enable. A
tuple is the flattest container that satisfies the one consumer.

The spawning prompt named this check by issue number, #2651's own text
referring back to #2548 — applying it to this result: nothing in the new
code validates an incoming value against the four retired names as a
closed set, and nothing reconstructs that closed set under another name —
`LEGACY_FILES` is a flat existence-check tuple with no identity axis, not
a renamed version of the same lookup. The removal-claim tool run above
(`scripts/audit_removal_claim.py`, derived: run this turn, full output
quoted under "What was done") reached `RESHAPE_DETECTED`, a false positive
from blunt substring/co-location matching against pre-existing, unrelated
code (hand-classified above), the same kind of false positive the
issue-2628 architecture record already documented for this same tool on a
different claim.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 2651` — cites PR #2640's independent
verifications as having wrongly classified `LEGACY` as dead/unrelated;
both are cited in frontmatter `upstream:` by path (sha: same-commit,
since neither path is edited by this session — they are read-only prior
context).

- `docs/issue-2628/reports/adversarial-review+silent-failure-audit-f8365dc9.md:73-75`
  — the first "dead, unrelated ... LEGACY dict" classification this issue
  corrects.
- `docs/issue-2628/reports/conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-2d6823f8.md:144-146`
  — the second "pre-existing, out-of-scope LEGACY dict" classification
  this issue corrects.
- `spawn.py:747` / `board.py:826` (pre-change) — the dict and its sole
  reader, both edited in this session's own commit (sha: same-commit).

## Open findings

None.

## Next steps

None — `loop_state: landed`.
