# Issue #587 — implementation current-state survey (phase 1, remediation round 3)

Skip condition: pure bugfix. The third e2e re-verification
(`docs/issue-587/reports/execution-observation.md`, latest entry) already
names the exact defect and its exact fix shape — thread the caller's
resolved `-C`/`--cwd` root into `_remediation_merge_sweep` instead of the
hardcoded global `ROOT` — leaving no open design decision for this round.
No product-facing surface is involved, so scout's sweep is not triggered.

## The defect, confirmed by reading the code

- `_remediation_merge_sweep(root: Path, issue: int)` (spawn.py:2109-2151)
  reads `root / BOARD / f"issue-{issue}" / "decisions"` — this is the
  *target* (consumer) repo's board data, not anything belonging to
  spawn.py's own checkout.
- `roster_reconcile(issue, unreported, remediation_merged)`
  (spawn.py:2158-2189), the `remediation_merged=True` branch
  (spawn.py:2180-2183), calls `_remediation_merge_sweep(ROOT, issue)` —
  the module-level global `ROOT = Path(__file__).resolve().parent`
  (spawn.py:37), i.e. spawn.py's *own* checkout, unconditionally.
- `main()`'s `if a.role == "reconcile":` branch (spawn.py:3509-3511) calls
  `roster_reconcile(a.issue, unreported=a.unreported,
  remediation_merged=a.remediation_merged)` — `a.cwd` (the parsed `-C`
  value, spawn.py:3458, default `"."`) is never passed in at all, for any
  of the three modes.
- Net effect confirmed by trace: `spawn.py reconcile --remediation-merged
  --issue <n> -C /path/to/consumer-repo` silently ignores `-C` and sweeps
  spawn.py's own `docs/issue-<n>/decisions/` instead of the consumer
  repo's — wrong or missing directory in any real consumer repo, so
  `_remediation_merge_sweep` returns 0 with no error and no comment. This
  matches the third e2e's observed symptom (silent no-op, event 4 still
  missing) and matches PR #610's stated root cause.

## Existing test coverage's blind spot

- `RosterReconcileRemediationMergedCLI` (test_spawn.py, the class defined
  just above `RosterReconcileUnreported`, added by the prior remediation
  round) calls `spawn.roster_reconcile(issue=587, remediation_merged=True)`
  with `spawn.ROOT` monkeypatched to a tmp fixture dir in `setUp`. This
  exercises the shipped *function* entry point but not the shipped *CLI*
  entry point — the `-C` plumbing gap in `main()` has zero coverage: the
  test never goes through `argparse`/`main()`, so it cannot observe that
  `-C` is dropped. This is why the prior round shipped green while this
  round's e2e still failed on a fixture repo outside the checkout.

## Fix shape (write surfaces)

### 1. `spawn.py` — thread the resolved target root through

- `roster_reconcile`: add a `root: Path | None = None` parameter; in the
  `remediation_merged` branch, use `root if root is not None else ROOT`
  (default preserves existing non-CLI callers' behavior — see audit
  note below on why only this branch changes here).
- `main()`'s `reconcile` dispatch: pass `root=Path(a.cwd).resolve()`
  alongside the existing `a.issue`/`unreported`/`remediation_merged` args
  — the same resolution pattern already used by `drive()`
  (spawn.py:3234, `root = Path(cwd).resolve()`) and by the mainline
  spawn/watch paths (`cwd_path = Path(a.cwd)` etc., spawn.py:3672-3675).

### 2. `test_spawn.py` — CLI-level regression test, per the issue's
   explicit requirement

- New test class driving the shipped CLI via `subprocess.run([sys.executable,
  ".../spawn.py", "reconcile", "--remediation-merged", "--issue", "587",
  "-C", str(fixture_root)], ...)`, where `fixture_root` is a
  `tempfile.TemporaryDirectory()`-based fixture repo (`git init` +
  `git remote add origin ...`) that is NOT spawn.py's own checkout
  (`os.path.dirname(os.path.abspath(spawn.__file__))`) — asserting this
  inequality explicitly in the test, then asserting the `gh api
  .../comments` call (captured via a stub `gh` executable prepended to
  `PATH`) actually fires with the expected comment body. This mirrors the
  fixture shape the prior round's test already built (an open
  `remediation-*.md` record with a merged `routed_to` branch) but drives
  it through `main()`/`argparse`/`-C` instead of a monkeypatched `ROOT`
  and a direct function call.
- The existing `RosterReconcileRemediationMergedCLI` class stays — it
  still validates `roster_reconcile()`'s own dispatch logic at the
  function level and is not redundant with the new CLI-level test.

## Audit: sibling ROOT-vs-target-root sites (per the round-3 mandate — report, do not fix)

```
$ grep -n "(ROOT)\|(ROOT," spawn.py
2013:    anomaly_count = _board_wide_sweep(ROOT)
2025:        divergences = reconcile(_build_expected(e), _build_observed(ROOT, e))
2038:                _post_session_end_comment(ROOT, issue_n, key, work, e.get("log", ""))
2168:    `remediation_merged=True` 면 `_remediation_merge_sweep(ROOT, issue)` 로
2183:        return _remediation_merge_sweep(ROOT, issue)
2192:        divergences = reconcile(_build_expected(e), _build_observed(ROOT, e))
```

The hit at `_remediation_merge_sweep(ROOT, issue)` inside `roster_reconcile`
is this round's fix. The rest, examined:

- `roster_watchdog()` (the `_board_wide_sweep`/`_build_observed`/
  `_post_session_end_comment` calls above): the `watchdog` CLI verb never
  accepts `-C` — `roster_watchdog(auto_respawn=a.auto_respawn)` takes no
  cwd argument at all. This reads the *roster* (`runs/active.json`,
  spawn.py:1722), spawn.py's own orchestrator-local session-tracking
  state, regardless of which repos the tracked sessions' `work` field
  points at — so `ROOT` here plausibly is the intended scope. Flagging
  anyway because `_build_observed(root, e)` (spawn.py:1695) internally
  calls `board(root)` (spawn.py:1709) to read `root`'s own
  `docs/issue-<n>/` board for that entry's `loop_state` — if a roster
  entry's issue lives in a repo other than spawn.py's own checkout,
  `board(ROOT)` reads the wrong repo's board for that entry. Same defect
  *shape* as this round's bug; unconfirmed whether it manifests in
  practice — would need a live multi-repo roster to reproduce, out of
  this round's fixture scope.
- `roster_reconcile`'s **default mode** (neither `unreported` nor
  `remediation_merged` — the loop ending at the last
  `_build_observed(ROOT, e)` call in the grep above): same
  `ROOT`-hardcoding as the bug this round fixes, and the same `main()`
  gap (the `reconcile` dispatch never threads `a.cwd` into this call
  path either, before this round's fix). Contrast: `drive()`
  (spawn.py:3234-3266) runs materially the same `reconcile()`-over-roster
  loop but correctly resolves `root = Path(cwd).resolve()` and passes it
  into `_build_observed(root, e)` — `drive` got this right,
  `roster_reconcile`'s default mode did not.

Both are the same bug class as this round's assigned fix, on call sites
this round's write set does not cover (`--remediation-merged` only, per
the issue's explicit scope). Not fixed here per the scope-exceeded rule
— left for a follow-up issue if the operator wants them addressed.
