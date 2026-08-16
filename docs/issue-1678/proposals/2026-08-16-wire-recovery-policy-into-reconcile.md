---
status: approved
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

Issue #1678 (northpole req#6): `reconcile()`'s `pr-expected-missing`
branch in spawn.py always names `next_action: "respawn"` when a session
died without opening its expected PR — no cap, no distinction between "no
work lost, retry the same brief" and "work exists but wasn't pushed", no
escalation when the same failure keeps recurring. Wire the existing
`gates/recovery_policy.classify_from_state()` (issue #1670) into that
branch so the recommendation is bounded and failure-classified instead of
unconditional.

## Constraints

- Reuse `recovery_policy.classify_from_state()` as-is — do not re-derive
  its cap/signature-repeat logic inside spawn.py.
- `reconcile()`'s `next_action` output stays inside its existing closed
  set (`respawn`, `resume-watch`, `manual-review`, `none` — ADR Decision
  3 from issue-492); ESCALATE must map onto an existing member, not add
  a new one.
- Existing `reconcile()` callers (`roster_watchdog`, `roster_reconcile`,
  `drive`) only ever print `next_action` as a recommendation — none
  auto-executes a respawn — so this change alters what gets recommended
  and persists counter state, not an auto-exec path.
- Existing `Reconcile` test-class fixtures that call `reconcile()`
  without an `issue` key must keep passing unchanged (issue-492
  regression floor).
- Concurrent issue #1677 owns `directive.sh` — do not touch it.

## Rationale

Considered wiring the policy call inside `roster_watchdog()` /
`_auto_respawn_check()` instead of inside `reconcile()` itself — that
site already has a separate `respawn_state`/`_respawn_or_cap()` counter
for the `session-crashed` path, so a first instinct was to reuse that
existing counter mechanism. Rejected: that counter answers a different
question (total-attempts / no-progress cap across *any* death cause) and
lives in a different file (`runs/respawn_state.json`, keyed just by
roster key), while issue #1678 explicitly asks to persist "the
per-(issue,role) counter via recovery_policy's state file" — a second,
purpose-built state file that already exists (issue #1670) and already
has the exact classify-then-persist shape the issue wants. Wiring inside
`reconcile()` also keeps the change scoped to the one branch the issue
names (`pr-expected-missing`), rather than touching the broader
crashed-session respawn path that issue #1678 does not ask to change.

## What will be done

- `reconcile()`'s `pr-expected-missing` branch delegates to a new
  `_reconcile_pr_expected_missing()` helper that calls
  `recovery_policy.classify_from_state(issue, role, has_commit, has_pr=False,
  failure_signature)` when `expected["issue"]` is present, and maps the
  verdict: `RESPAWN_IDENTICAL`/`RESPAWN_WITH_HANDOFF` → `next_action:
  "respawn"` (with a `handoff` flag on the divergence dict), `ESCALATE` →
  `next_action: "manual-review"`.
- `_build_expected()` adds an `"issue"` key (from the roster entry) so
  the (issue, role) state key is available at the call site; the three
  existing callers pass a `recovery_state_dir` derived from their own
  `root`, so the counter lives under `<root>/.on-the-record/recovery-state/`
  rather than the process cwd.
- When `expected["issue"]` is absent (older/ad-hoc callers), the branch
  falls back to a stateless has-commit check with no policy-module call
  and no state I/O — preserving byte-identical behavior for existing
  callers that never populate `issue`.
- New `tests/test_spawn.py` test class exercising: pre-first-commit
  under cap → respawn identically; has-commit-no-PR → respawn with
  handoff; at-cap/same-signature-repeat → ESCALATE, no respawn;
  healthy-with-PR → no action, policy never called; a live-style
  reconstruction of issue #1660 through the real `classify_from_state`
  with an isolated tmp state directory.

## Out of scope

- `directive.sh` (issue #1677's concurrent write set).
- The `session-crashed` and `session-stalled` reconcile branches, and
  the separate `roster_watchdog`/`_respawn_or_cap()` crash-counter path
  — issue #1678 only names `pr-expected-missing`.
- Deriving a real `failure_signature` from session logs/events — this
  proposal threads an optional `failure_signature` field through
  `observed` for callers to supply, but does not build a signature
  extractor; today's live callers pass `None`, which is safe (no
  same-signature-repeat escalation fires without one) but does not yet
  give the cap-independent repeat-escalation acceptance case a live
  signal source.

## Accumulation

This adds exactly one new lazy `gates/*` import call site
(`_recovery_policy_module()`), mirroring a pattern spawn.py already has
~10 instances of (`sys.path.insert(0, str(ROOT / "gates")); import
<module>`) — this proposal does not add an eleventh ad-hoc inline
variant, it factors the recovery_policy one behind a single named
helper so a future caller reuses the helper instead of repeating the
`sys.path.insert` boilerplate again. The three `reconcile()` call sites
that gain a `recovery_state_dir=...` keyword argument are the fixed set
of existing callers (`roster_watchdog`, `roster_reconcile`, `drive`) —
this is not a growing list; a future new caller would pass the same
keyword the same way, not accumulate a new inline variant.

## How you'll know it worked

- `python3 -m pytest tests/test_spawn.py -k Reconcile -q` — new and
  pre-existing `Reconcile`/`reconcile`-adjacent tests pass.
- `python3 -m pytest -q -m "not slow"` and `python3 -m pytest -q -m slow`
  (this repo's `.on-the-record/test-tiers.json` tiers, both triggered by
  touching `spawn.py`/`tests/test_spawn.py`) both pass clean.
- A synthetic reconstruction of issue #1660 (commit exists, no PR,
  session ended) through `reconcile()` respawns with `handoff=True` on
  the first death, then ESCALATEs (`next_action: "manual-review"`) on
  the second death carrying the same `failure_signature` — no third
  blind respawn.
