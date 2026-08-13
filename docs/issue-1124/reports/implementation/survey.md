# Current-state survey — issue #1124

Scope: `spawn.py clean` deletes ledger-referenced logs for non-landed
sessions; `spawn.py reconcile --unreported` crashes on a workspace
`clean` already removed.

Scout skip: this is a pure bugfix against two reproduced crashes/data-loss
paths named in the issue, with no open design decision (no new dependency,
no new UX surface, no alternative architecture to weigh) — scouting the
field is skipped per scout-directive's pure-bugfix condition.

## Write surfaces

- `spawn.py:4871-4942` (main(), `a.role == "clean"` branch): globs
  `<workspace-base>/*`, for each workspace with no live PID and a clean/
  pushed git tree, `shutil.rmtree()`s the workspace directory, then
  unconditionally `unlink()`s every sibling file matching
  `<workspace-name>.*` — this includes the generation session log
  (`.session.<ts>.<pid>.log`, issue #192) regardless of what that
  session's outcome was. No read of `runs/ledger.jsonl` happens anywhere
  in this branch today.

- `spawn.py:2734-2781` (`_roster_reconcile_unreported`, issue #534): for
  each workspace-index entry it calls `session_end_verdict(work, ...)`
  (spawn.py:1678, safe — only checks `Path.exists()`) and then
  `_issue_comments(Path(work), issue_n)` (spawn.py:1239), which runs
  `subprocess.run([...], cwd=root, ...)`. `subprocess.run` raises
  `FileNotFoundError` when `cwd` does not exist on disk — this is the
  crash the issue reproduced (traceback path
  `.../on-the-record-issue-1110-implementation`, a workspace `clean` had
  already `rmtree`'d while the workspace-index entry survived, since
  `clean` never touches `WORKSPACE_INDEX`). No existence check on `work`
  precedes this call today.

- `spawn.py:1640-1676` (`classify()`): the outcome vocabulary a session
  can land in — `progressed`, `waiting-on-human`, `refused`,
  `refused-null-result`, `silent-failure`, `errored` — plus
  `fail_closed_downgrade()` (spawn.py:1726) can further produce
  `progressed-dirty-tree` or `failed-no-commit`. There is no literal
  `"landed"` value; "landed" (per the issue's language) is read here as
  the two outcomes where a new commit reached origin: `progressed` and
  `progressed-dirty-tree` (`fail_closed_downgrade`, spawn.py:1726, gates
  on `new_commit and push_succeeded`). Every other outcome is treated as
  non-landed — its log is the only durable evidence of what happened
  (the issue's own example: a `refused` session, 581a8f7e).

- `spawn.py:3970-3978` (`ledger_write`): appends one JSON line per
  session to `ROOT / "runs" / "ledger.jsonl"` with `"log": str(log_path)`
  (the exact sibling path `clean` would later delete) and `"outcome"`.
  This is the only existing source of "which outcome produced this log
  file" — `clean` has to consult it to know which logs are safe to
  delete.

- No existing helper reads `ledger.jsonl` back for lookup by log path;
  `ledger_write`/`ledger_stamp`/`_reconcile_ledger_*` (a *different*,
  unrelated JSON ledger at `runs/reconcile_ledger.json` used for
  dedup-key TTLs, spawn.py:2047) are the only readers/writers near this
  area — none of them serve this task.

## Test surface

- `gates/test_*.py` convention (e.g. `gates/test_closure_sweep.py`):
  `sys.path.insert(0, .../gates)` then `.../..` , `import spawn`,
  `unittest.TestCase`, mocking via `unittest.mock.patch.object` on
  module-level names (`spawn.subprocess`, `spawn._alive`, etc.) rather
  than real network/process calls. No existing test file exercises
  `clean` or `_roster_reconcile_unreported`.
- `clean`'s logic today lives inline inside `main()`'s `if a.role ==
  "clean":` branch — not a standalone function — so it is not currently
  unit-testable without invoking the full CLI (argv, real
  `Path.home()`-based work dir, live `gh`/git). Testing it per the
  issue's acceptance requires extracting it into a callable the test can
  invoke directly with an injected work-base dir and mocked roster/ledger
  state, mirroring the existing extraction pattern used elsewhere in this
  file (e.g. `_roster_reconcile_unreported`, `_remediation_merge_sweep`
  are already free functions, not inlined in `main()`).

## Empty-state check

- `ROSTER` / `WORKSPACE_INDEX` loaders (`_roster_load`,
  `_workspace_index_load`) both catch `(OSError, ValueError)` and return
  `{}` when the backing JSON file is absent — a fresh install already
  degrades safely there. `ledger_write` creates `runs/` on first write
  (`d.mkdir(exist_ok=True)`), so a fresh install has no
  `runs/ledger.jsonl` at all; any new ledger-reading helper this fix adds
  must treat a missing ledger file as "no outcome known for any log" (empty
  map), not an error.
