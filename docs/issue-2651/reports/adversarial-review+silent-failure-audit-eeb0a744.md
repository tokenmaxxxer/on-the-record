---
issue: 2651
role: adversarial-review+silent-failure-audit-eeb0a744
author: adversarial-review+silent-failure-audit-eeb0a744
skills: adversarial-review (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: true  # independent verification of PR #2654's deliverable, different author
loop_state: landed
code_under_review:
  - path: spawn.py
    sha: 6ba163672f4b0218dfdb8f73ebdb041fb3cb82d2
  - path: board.py
    sha: 6ba163672f4b0218dfdb8f73ebdb041fb3cb82d2
type: verification
breaking: none
verdict: pass-with-open-finding
---

# issue-2651 — adversarial-review+silent-failure-audit-eeb0a744 record

## What was done

Independent verification of PR #2654 (issue #2651, "spawn.py `LEGACY`: a
live 4-entry dict keyed by retired identity names, printed to the
consumer by `board.py`") against the issue's Acceptance section.

canonical: `gh issue view 2651` (this turn) — Ask/Acceptance/Non-goals
text. canonical: `gh pr diff 2654` (this turn) — full diff. canonical:
`gh pr view 2654 --json headRefOid,headRefName` (this turn) — result:
`6ba163672f4b0218dfdb8f73ebdb041fb3cb82d2`,
`issue-2651/architecture-interface-contract-shape+silent-failure-audit-fb35aea0`.

derived: `git fetch origin pull/2654/head:pr-2654-verify && git worktree
add /tmp/verify-2651 pr-2654-verify` (this turn) — post-change checkout.
derived: `git worktree add /tmp/verify-2651-pre pr-2654-verify~1` (this
turn) — result: HEAD `a93cbf95af82d194fddff5a980284dc3a0349f37`, the
PR's parent commit, used as the pre-change baseline. Did not read PR
#2654's own record before forming each verdict below; consulted it only
afterward to check whether it had already surfaced the open finding
below (it had not).

The diff itself, canonical (`gh pr diff 2654`, this turn):
```diff
-LEGACY = {"conformance-review": "review-record.md",
-          "technical-feasibility": "feasibility-record.md",
-          "release-engineering": "state.md",
-          "product-discovery": "product-record.md"}
+LEGACY_FILES = ("review-record.md", "feasibility-record.md", "state.md",
+                "product-record.md")
```
```diff
-    stale = sorted(r for r, name in _sp.LEGACY.items()
+    stale = sorted(name for name in _sp.LEGACY_FILES
                    if (root / name).exists() or (root / "docs" / name).exists())
```
plus two new files under `docs/issue-2651/reports/` (the PR's own record
and hunt log), which this record does not modify.

### Acceptance bullet 1 — "Nothing in `spawn.py` or `board.py` is keyed
by, or prints, a retired identity name"

acceptance: `grep -n 'LEGACY' spawn.py board.py` (this turn, in
`/tmp/verify-2651`) — result:
```
board.py:826:    stale = sorted(name for name in _sp.LEGACY_FILES
spawn.py:274:_LEGACY_WORKSPACE_KEY_RE = events._LEGACY_WORKSPACE_KEY_RE
spawn.py:425:LEGACY_MONITOR_ALIVE_DIRNAME = lifecycle.LEGACY_MONITOR_ALIVE_DIRNAME
spawn.py:750:LEGACY_FILES = ("review-record.md", "feasibility-record.md", "state.md",
```
derived: `git show a93cbf95:spawn.py | grep -n LEGACY` (this turn) —
same `_LEGACY_WORKSPACE_KEY_RE`/`LEGACY_MONITOR_ALIVE_DIRNAME` lines
present pre-change too, at the same names — unrelated pre-existing
symbols sharing only the `LEGACY` substring. derived: `python3 -c
"import spawn; print(hasattr(spawn,'LEGACY'), hasattr(spawn,
'LEGACY_FILES'))"` (this turn, `/tmp/verify-2651`) — result: `False
True`. The old dict attribute is fully deleted, not aliased. Verdict for
the `LEGACY`/`LEGACY_FILES` structure and its one reader: **Present**.

The acceptance's own "read what remains" instruction does not stop at
grepping `LEGACY` — the issue's prose calls the four strings "retired
identity names" independent of the dict. derived: `grep -n
'conformance-review\|technical-feasibility\|release-engineering\|
product-discovery' spawn.py board.py` (this turn) — result:
```
board.py:587:    for r in ("product-discovery", "technical-feasibility"):
board.py:897:        if role == "technical-feasibility" and rest.startswith("spikes/"):
board.py:899:        if role == "release-engineering" and rest.startswith("postmortems/"):
spawn.py:9:  python3 spawn.py --skills conformance-review-verdict-assignment "PR 12 를 리뷰해라" --issue 12
```
derived: `grep -n '| .* conformance-review\|| .* technical-feasibility\|
| .* release-engineering\|| .* product-discovery'
docs/specs/role-invariant-coverage.md` (this turn) — result: all four
strings appear as items #6, #31, #33, #39 of a 43-role live domain
matrix (`docs/specs/role-invariant-coverage.md`), i.e. `spawn.py:9`'s
`conformance-review-verdict-assignment` names a currently-tracked skill,
not a retired identity — correctly out of this issue's scope.
`board.py:587,897,899` are the two functions the task asked me to check
by name — see "Non-goal 2" below; one of the two is **not** fully
"unrelated" and is recorded as an open finding rather than fixed here,
per the task's explicit instruction.

### Acceptance bullet 2 — the board still distinguishes "pre-v3 layout"
from "nothing written yet"

Built a fixture harness (`/tmp/fixture_demo.py`, outside the repo write
set) that imports `spawn` then `board`, builds a fresh
`tempfile.mkdtemp()` fixture per state, and calls
`board.status(fixture_dir)`. derived: first attempt (`import board`
alone, no `import spawn`) failed with `AttributeError: 'NoneType' object
has no attribute 'slug'` at `board.py:786` — `board.py`'s module-level
`_sp = None` is only wired by `spawn.py`'s own `board._sp =
sys.modules[__name__]` (`spawn.py:476`), confirmed by reading that line
directly; fixed by importing `spawn` first.

acceptance: fixture run (this turn) against `/tmp/verify-2651`
(post-change, PR #2654 head `6ba16367`) — result:
```
=== STATE 1: nothing written yet ===
보드 없음 (docs/issue-<n>/). 아직 아무 역할도 기록을 쓰지 않았다.

=== STATE 2: 2 of 4 legacy files at root ===
보드 없음. 계약 v1 자리에 기록이 있다: product-record.md, review-record.md
  이 레포는 v3 이전 판이다. v3 는 docs/issue-<n>/reports/<역할>.md 다.

=== STATE 2b: ONE legacy file located under docs/, not root ===
보드 없음. 계약 v1 자리에 기록이 있다: state.md

=== STATE 2c: legacy file present but EMPTY ===
보드 없음. 계약 v1 자리에 기록이 있다: review-record.md
```
acceptance: identical fixture run (this turn) against
`/tmp/verify-2651-pre` (pre-change, `a93cbf95`) — result:
```
=== STATE 1 === 보드 없음 (docs/issue-<n>/). 아직 아무 역할도 기록을 쓰지 않았다.
=== STATE 2 === 보드 없음. 계약 v1 자리에 기록이 있다: conformance-review, product-discovery
=== STATE 2b === 보드 없음. 계약 v1 자리에 기록이 있다: release-engineering
=== STATE 2c === 보드 없음. 계약 v1 자리에 기록이 있다: conformance-review
```
The two-state distinction survives identically pre- and post-change in
all four sub-cases, including the three narrowing candidates probed
specifically (partial file set, `docs/`-located file, empty-but-present
file) — none narrow the distinction. The only behavior change is *what
`stale` names*: retired role identities pre-change, plain filenames
post-change. Verdict: **Present**.

### Acceptance bullet 3 — the two output lines no longer teach retired
vocabulary

canonical: `sed -n '824,833p' board.py` (this turn, post-change) —
result:
```python
    stale = sorted(name for name in _sp.LEGACY_FILES
                   if (root / name).exists() or (root / "docs" / name).exists())
    if stale:
        out.append(f"보드 없음. 계약 v1 자리에 기록이 있다: {', '.join(stale)}")
        out.append("  이 레포는 v3 이전 판이다. v3 는 docs/issue-<n>/reports/<역할>.md 다.")
```
derived (Acceptance-bullet-2 fixture output above): the first line
interpolates filenames (`product-record.md, review-record.md`), never
role identities, in every state tried. The second line's `<역할>` is the
generic Korean word "role" used as a path-template placeholder, not one
of the four retired identity strings — the issue's own Non-goals assigns
retirement-narrating prose to #2139, and `<역할>` is exactly that kind of
prose, not a printed identity. Verdict: **Present**.

### `must not` clause

derived: `diff <(git show a93cbf95:board.py) board.py` (this turn,
`/tmp/verify-2651`) — result: single hunk, line 826 only (quoted in
"What was done" above). derived: `diff <(git show a93cbf95:spawn.py)
spawn.py` (this turn) — result: single hunk, the `LEGACY` block only
(quoted above). No other line in either file changed — the board-exists
path (`board.py`'s `if b:` branch) is untouched, and `LEGACY_FILES` was
not moved to another module/file/JSON/per-entry files (it stays at the
same location in `spawn.py`, confirmed by the same diff). The
capability-drop escape hatch does not apply since Acceptance bullet 2
above demonstrates the capability survived. Verdict: **Present**.

### Is `LEGACY_FILES` a genuine de-identification, or a rename with extra
steps?

derived: `grep -rn '\.LEGACY\b\|\.LEGACY_FILES\b' --include='*.py' .`
(this turn, repo root, excluding `__pycache__`) — result:
```
board.py:826:    stale = sorted(name for name in _sp.LEGACY_FILES
```
Only one attribute access exists anywhere in the repo, and it iterates
values only — no `.items()`/`.keys()` call on `LEGACY_FILES` exists
anywhere (same grep, zero such matches). derived: `python3 -c "import
spawn; print(hasattr(spawn, 'LEGACY'))"` (repeated from above) — `False`:
the old shape is deleted, not aliased, so nothing can read it back under
the old name.

Judged: **genuine de-identification for the one consumer that exists**,
not a rename-with-extra-steps. The runtime type changed from `dict`
(key→value, indexable/iterable by identity) to `tuple` (flat values,
no identity axis); the printed message now shows filenames a caller
cannot query as a closed set of valid identities the way the old dict's
`.keys()` could be. `product-record.md`/`review-record.md` carry
semantic hints of their domain by English-word choice, but that is a
file-naming-convention property, not a data structure — no code
anywhere reconstructs an identity→filename mapping from `LEGACY_FILES`
(confirmed by the grep above and by the cross-module sweep below). This
matches the operator ruling quoted in the issue's `must not` clause: the
capability was "does this legacy filename exist," never "which role
owned it," so dropping the key axis while keeping the value axis removes
exactly the part of the structure the issue's Ask targets.

### Cross-module reader sweep (the miss PR #2640's verifications made)

The issue states prior verifications greped `spawn.py` alone and missed
`board.py`'s cross-module read. Repeated that mistake's opposite: swept
every module that imports `spawn` as `_sp`, not just `board.py`.

derived: `grep -rln 'as _sp\|_sp = ' --include='*.py' .` (this turn) —
result: 29 files, including `events.py, directive_assembly.py,
lifecycle.py, plumbing.py, relay.py, board.py, gates/merge_gate.py,
skills.py, roster.py, gates/patrol_promote.py, gates/patrol_wiring.py,
pipeline.py, gates/patrol_board.py, gates/spawn_on_approve.py,
gates/spawn_on_pr.py, gates/check_runner.py, watchdog.py,
gates/spawn_coverage.py, consult.py, gates/test_spawn_on_pr.py,
harness/fixture-requirement-digest/scenario.py,
harness/fixture-concurrent-judgment/test_panel.py, spawn.py,
tests/test_tmp_resource_gc.py, gates/closure_sweep.py, gates/ci.py,
gates/flows.py, tests/test_cross_checkout_prune_liveness.py, bench/run.py,
on-the-record/monitors/test_poll_heartbeat.py`.

derived: `grep -rn '\.LEGACY\b' --include='*.py' .` (this turn, excludes
`__pycache__`) — result: `board.py:826` only (already shown above,
post-change reading `LEGACY_FILES`). **0 matches** in any of the other
28 files. `board.py` was the only reader before this PR and remains the
only reader after. `ledger/collect.py` does not import `spawn` at all
(confirmed absent from the 29-file list above) and defines its own
unrelated `LEGACY` — see Non-goal 1.

### Non-goal 1 — `ledger/collect.py`'s `LEGACY`

canonical: `sed -n '20,31p;70,76p;99p;124,127p' ledger/collect.py` (this
turn) — result:
```python
LEGACY = "review-record.md"
...
    return [LEGACY] if (repo / LEGACY).exists() else []
...
    legacy = rels == [LEGACY]
...
        out.append(f"  ⚠ v1 자리({LEGACY})를 읽었다 — v3 는 "
```
`LEGACY = "review-record.md"` is a bare string constant, not a dict, not
keyed by anything — it detects one specific pre-v3 file to avoid the
review-effectiveness ledger reporting "never reviewed" for a repo that
has an un-migrated v1 record. It shares a name and a purpose family
(detect pre-v3 layout) with `spawn.py`'s old `LEGACY`, but carries no
identity axis and no role name. derived: `gh pr diff 2654 --name-only`
(this turn) — result: `board.py`, two new `docs/issue-2651/` files, and
`spawn.py` only — `ledger/collect.py` absent, confirmed untouched by
this PR. Non-goal claim: **holds**.

### Non-goal 2 — `board.py`'s `_front_role` / `ownership_report`

canonical: `sed -n '577,590p' board.py` (this turn) — result:
```python
def _front_role(root: Path, subject: str, roles: dict) -> str | None:
    rootless = [r for r in roles
                if not _sp._record_upstream(root / _sp.BOARD / subject / "reports" / f"{r}.md")]
    if len(rootless) == 1:
        return rootless[0]
    for r in ("product-discovery", "technical-feasibility"):
        if r in roles:
            return r
    return None
```
canonical: `sed -n '893,900p' board.py` (this turn) — result:
```python
        if rest == f"{role}.md" or rest.startswith(f"{role}/"):
            continue
        if role == "technical-feasibility" and rest.startswith("spikes/"):
            continue
        if role == "release-engineering" and rest.startswith("postmortems/"):
            continue
```

**`ownership_report`** — `role` is the *calling session's own declared
role* (passed in by the caller, already known to whoever invokes this),
compared against two literals only to grant a subdirectory exception
(`spikes/`, `postmortems/`). It never prints the two comparison literals
themselves — the header line (read in the same `sed` output's caller
context) prints `role` (already caller-supplied) and a generic "다른
역할의 기록" phrase; no retired vocabulary is taught to a reader who
didn't already supply it. "Unrelated reasons": **holds**.

**`_front_role`** does not hold up the same way. derived: wrote
`/tmp/front_role_demo.py` (fixture: a subject with two rootless records
named exactly `product-discovery.md` and `technical-feasibility.md`,
no `upstream:`), ran it against `/tmp/verify-2651` this turn — result:
```
roles seen: ['product-discovery', 'technical-feasibility']
front_role() returned literal identity string: product-discovery
```
This is a live closed-set comparison against two of the four names the
issue calls retired (`for r in ("product-discovery",
"technical-feasibility"): if r in roles: return r`, quoted above) —
existence/ambiguity-gated reveal of an identity string, the same shape
as the bug this issue corrects, just keyed on `roles` (a dict of
role→record for one subject) instead of the filesystem.

canonical: `sed -n '611,621p;636,648p' board.py` (this turn) — result:
```python
    front = _sp._front_role(root, subject, roles)
    if not front:
        sys.exit(f"{subject} 의 front record 를 판별할 수 없다.")

    record_path = root / _sp.BOARD / subject / "reports" / f"{front}.md"
    fm = _sp.frontmatter(record_path)
    state = fm.get("loop_state")
    if state == "scope-approved":
        print(f"이미 scope-approved 다: {record_path}")
        return 0
    if state != "scope-proposed":
        sys.exit(f"{record_path} 의 loop_state 가 scope-proposed 가 아니다 "
                 f"(지금: {state or '(없음)'}) — 승인 대상이 아니다.")
```
`_front_role`'s return (`front`) is interpolated into `record_path` and
printed verbatim in multiple `print()`/`sys.exit()` calls inside
`approve_scope` (quoted above). derived: `grep -n 'approve_scope ='
spawn.py; grep -n 'approve-scope' spawn.py` (this turn) — result:
```
spawn.py:491:approve_scope = _board_mod.approve_scope
spawn.py:2436:    if a.role == "approve-scope":
```
`approve_scope` is live, CLI-wired code (`spawn.py approve-scope --issue
<n>`), not dead code. So a retired identity name (`product-discovery`)
can still reach an operator's terminal from `board.py`, through a
different trigger (ambiguous rootless roles for a subject, on the
board-exists path) than the one issue #2651's Ask targeted
(`LEGACY`/no-board path) — a path this issue's `must not` clause
explicitly puts out of scope ("do not change the board's behavior on the
path where a board exists").

Calling both functions "unrelated" (the framing offered to this
verification) is only half right: `ownership_report` genuinely is;
`_front_role` is a second, narrower, still-live identity-keyed
comparison whose result can print a retired name. Recorded as an open
finding below rather than fixed here, per the task's explicit
instruction and per this issue's own scope boundary.

## Why

Adversarial-review + silent-failure-audit skills applied: treated PR
#2654's own record and PR body as untrusted until independently
re-derived every acceptance check from a fresh worktree, and specifically
hunted for the kind of cross-module or same-shape-different-name miss
that let the original bug survive one prior review round (PR #2640)
uncaught — the same failure mode this issue itself was opened to correct.

## What did not work

None — every acceptance check was independently reproducible from a
fresh worktree. The one substantive disagreement with the PR's own
framing is the `_front_role` finding above, which the PR's record reads
`board.py:587,897,899` together and calls all three "unrelated" without
separately testing `_front_role`'s reachability to a printed message.

## Upstream basis

- `gh issue view 2651` (canonical, read this turn) — Ask/Acceptance/
  Non-goals text quoted above.
- PR #2654, branch
  `issue-2651/architecture-interface-contract-shape+silent-failure-audit-fb35aea0`,
  head `6ba163672f4b0218dfdb8f73ebdb041fb3cb82d2` — the code under review
  (`code_under_review:` above); fetched via `git fetch origin
  pull/2654/head:pr-2654-verify` and checked out at `/tmp/verify-2651`
  (post-change) and `/tmp/verify-2651-pre` (parent commit `a93cbf95`,
  pre-change), both independent of this branch's own checkout.
- `docs/handbooks/observer-verification.md` (canonical, read this turn)
  — basis for setting `verifies_subject: true` (this record's author
  differs from PR #2654's deliverable author,
  `architecture-interface-contract-shape+silent-failure-audit-fb35aea0`).

## Open findings

1. `board.py:577-588`'s `_front_role()` performs a live closed-set
   comparison against two of the four identity strings issue #2651 calls
   "retired" (`"product-discovery"`, `"technical-feasibility"`) as a
   tie-break fallback when a subject's rootless-record set is ambiguous,
   and its return value reaches an operator's terminal (via
   `approve_scope`'s `record_path` interpolation, `board.py:611-648`)
   when that fallback fires — demonstrated live this turn (see Non-goal
   2 above), not just read. Same shape of defect as the one #2651
   corrects, on a different trigger (ambiguous rootless roles, not
   no-board) and a different code path (`approve_scope`, board-exists —
   explicitly out of #2651's scope per its `must not` clause). Not fixed
   here, per the task's explicit instruction and this issue's own scope
   boundary. Resolution path: a follow-up issue scoped to
   `approve_scope`'s ambiguous-root fallback, parallel to how #2651
   itself scoped to the no-board path only — does not require reopening
   #2651 or blocking PR #2654.
2. `board.py:897,899`'s `ownership_report` comparisons and
   `ledger/collect.py`'s `LEGACY` were both checked and found genuinely
   unrelated. canonical: see the "Non-goal 1" and "Non-goal 2" sections
   above (`sed -n` code fences of `ledger/collect.py:20-31,70-76,99,
   124-127` and `board.py:893-900`) — no action needed.

## Next steps

None for this record — `loop_state: landed`. Open finding 1 above is a
candidate for a follow-up issue, not a blocker for PR #2654: PR #2654
satisfies issue #2651's Acceptance section as written (all three
Acceptance bullets and the `must not` clause verified Present against
independently re-run checks above).

skill-verdict: adversarial-review — applied: invoked; used to treat PR
#2654's own record and PR body as untrusted, re-derive every acceptance
check from a fresh worktree, and specifically look for what a
structurally-motivated defender of the PR would not go looking for (the
`_front_role` finding).
skill-verdict: silent-failure-audit — not-applicable: the diff under
review (a dict→tuple literal change and a comprehension-header rewrite)
introduces no new try/except, error callback, or fallible I/O path; the
`Path.exists()` calls are the same pre-existing calls with the same
arguments as pre-change. `approve_scope`'s `sys.exit()`/`print()` calls
examined for the `_front_role` finding are pre-existing error-reporting
paths, not introduced or altered by this PR — noted only because they
are the mechanism by which the open finding's identity string reaches a
consumer, not because this PR's diff added fallible error handling.
