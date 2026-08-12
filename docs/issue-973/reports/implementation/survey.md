# Current-state survey — issue #973 implementation phase-1

Subject: issue-973. Role: implementation.
canonical: docs/issue-973/proposals/product-discovery.md (PR #975, merged), read this session.
Basis: merged design — this survey does not re-derive that design's RICE/hypothesis content, only
the code surfaces implementation will touch.

## Write surfaces named by the approved design

canonical: docs/issue-973/proposals/product-discovery.md, "Deployment-surface constraint carried
forward" section, read this session.
The design's own "Deployment-surface constraint carried forward" section assigns implementation:
`panel_cmd()` in `spawn.py`, the `docs/issue-<n>/reports/panel/` record schema, and
`harness/fixture-concurrent-judgment/test_panel.py`.

## `consult_cmd()` as the precedent to reuse

canonical: spawn.py:4095-4165, read this session.

- `consult_cmd(role, question, issue=None, cwd=None)` (spawn.py:4095) loads a role's rulebook via
  `plugin_dirs(role, spec)` (spawn.py:324) / `role_settings(role, cwd)` (spawn.py:474), writes a
  temp settings file, builds a `claude -p --output-format json` command, and appends
  `--plugin-dir` for both the role's plugins and `core_plugin_dirs()`.
- It sets `role_model = resolved_role_model()` and appends `--model` when non-empty
  (spawn.py:4133-4135) — the same model-pin path `spawn_cmd()` uses (spawn.py:4017-4019).
- The consult prompt (spawn.py:4137-4145) instructs the session to answer with no branch/commit/PR
  and to end its output with a JSON verdict object
  `{"answer":..., "confidence":..., "caveats":[...]}`. `_parse_consult_verdict()` (spawn.py:4057)
  scans the output text backward for the last parseable `{...}` containing an `"answer"` key —
  tolerant of prose wrapped around the JSON.
- `_append_consult_trace()` (spawn.py:4082) writes one line per invocation, success or failure, to
  `_consult_trace_path(issue)` (spawn.py:4073) — `docs/issue-<n>/reports/consult-log.md` when an
  issue is given, `docs/reports/consult-log.md` otherwise. Runs inside a `finally` block
  (spawn.py:4161-4165) so a raised exception still leaves a trace line.

canonical: spawn.py:4095-4165, read this session.
`consult_cmd()` is synchronous — it calls `subprocess.run(..., capture_output=True,
timeout=CONSULT_TIMEOUT)` (spawn.py:4146-4147, `CONSULT_TIMEOUT = 180`, spawn.py:65) and blocks
until that one session exits; no code path in this function launches a second concurrent session or
exchanges messages between two sessions.

## `spawn_cmd()` as the non-bare launch precedent

canonical: spawn.py:3990-4054, read this session.

- The role-spawn path already launches every session as non-bare `claude -p --settings ...
  --permission-mode bypassPermissions --output-format stream-json --verbose` (spawn.py:4003-4005)
  with `--plugin-dir` per plugin (spawn.py:4009-4012) and the model pin (spawn.py:4017-4019).
- `role_settings()` (spawn.py:474) is the shared settings-dict builder both spawn and consult call
  (spawn.py:4122) — the reuse precedent `panel_cmd()` should follow rather than inventing a third
  settings path.

canonical: `grep -n crossSessionInbound spawn.py`, run this session, zero hits.
Neither `spawn_cmd()` nor `consult_cmd()`'s settings construction sets `crossSessionInbound`
anywhere in this file.

## No existing `SendMessage`/`ListAgents` call site in this repo's own code

canonical: `grep -rn "SendMessage\|ListAgents" spawn.py roles/ *.py`, run this session, zero hits
in repository code.
Both tools appear in this session's own deferred-tool listing as harness-supplied capabilities, so
they exist as callable primitives, but no orchestration code in this repository calls them
programmatically today — `panel_cmd()` is new orchestration, not a refactor of an existing call.

## Fixture precedent

canonical: harness/fixture-multirole/test_fixture_multirole.py, read this session.
Existing harness fixtures (`harness/fixture-*/`) pair a small importable Python package
(`fixture_<name>/`) with a `test_fixture_<name>.py` that imports and asserts against it directly —
`test_fixture_multirole.py` calls `storage_a.save/load` and `storage_b.save/load` in-process, no
subprocess spawn inside the test.

canonical: docs/issue-973/proposals/product-discovery.md, "Deployment-surface constraint carried
forward" section, read this session — names only that `test_panel.py` must exist, not its internal
shape.
`test_panel.py` (named by the issue's own acceptance criterion) must decide, as an
implementation-scope choice, whether it drives a real two-`claude -p`-session exchange end-to-end
(slow, needs live messaging and network) or a seeded stand-in that exercises `panel_cmd()`'s
parsing/recording/degradation logic without a live model call.

## Approval state (contract v3 s19 gate)

canonical: gh issue view 973 --comments, run this session.
derived: gh issue view 973 --comments
```
[watch] issue-973/product-discovery: session-end: PR https://github.com/tokenmaxxxer/on-the-record/pull/975 opened

workspace: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-973-product-discovery
log: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-973-product-discovery.session.20260812T113335.223500.log
--
author:	JiwonJung94
association:	member
edited:	false
status:	none
--
APPROVE issue-973/product-discovery
```
Full comment output above, reproduced verbatim by the `derived:` command.

canonical: gh pr list --search "973" --state all, run this session.
derived: gh pr list --search "973" --state all
```
975	issue-973 product-discovery phase-1: concurrent multi-agent judgment design	issue-973/product-discovery	MERGED	2026-08-12T02:39:01Z
664	docs(issue-641): commit deferred phase-2 implementation record	issue-641/implementation	CLOSED	2026-08-10T06:15:16Z
```
Full PR list output above, reproduced verbatim by the `derived:` command — no row names branch
`issue-973/implementation`.

Per contract v3 s19, this role's own phase-2 opens only on an approval string naming this role —
`product-discovery`'s approval authorizes that role's own phase 2, not this role's. This survey and
the accompanying proposal are therefore this role's phase-1 output; phase-2 (`panel_cmd()`, the
fixture, the record) waits for `APPROVE issue-973/implementation`.
