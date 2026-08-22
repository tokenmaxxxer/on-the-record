---
code_under_review: 948d2fd4
loop_state: landed
type: implementation
breaking: false
verdict: partial
---

# issue-2028: fire-counter instrumentation; gh-auth-probe cache found out of scope

## What was done

Added an append-only fire counter to two on-the-record hooks in this
repo's write set (commit 948d2fd4):

- `on-the-record/hooks/directive.sh` (UserPromptSubmit) — appends one
  `<UTC timestamp> UserPromptSubmit directive.sh` line to
  `<session workspace>/.orchestrate-hook-fires.log` on every firing,
  written before the `ORCHESTRATE_OFF`/`CLAUDE_ROLE` short-circuits so the
  count reflects every real trip of the hook, not only the ones that go
  on to do further work.
- `on-the-record/hooks/stop-gate.sh` (Stop) — same convention, same file,
  `Stop stop-gate.sh` line.

Both hooks share one counter file per session workspace
(`$(pwd -P)/.orchestrate-hook-fires.log`), following the same
per-workspace-marker convention `directive.sh`'s existing
`GREETED_MARKER` already uses (workspace-scoped, not the shared
on-the-record checkout).

canonical: `on-the-record/hooks/directive.sh` and
`on-the-record/hooks/stop-gate.sh` at commit 948d2fd4.

Test coverage added at `on-the-record/hooks/test_hook_fire_counter.py`
(commit 948d2fd4) — each test function there runs a hook twice against
a fresh temp workspace and asserts the counter file gains exactly one
line per run.
canonical: `on-the-record/hooks/test_hook_fire_counter.py` at commit
948d2fd4, read this session.

canonical: `python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py on-the-record/hooks/test_stop_gate.py on-the-record/hooks/test_directive_content.py -q` — this session's own live run
acceptance: `python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py on-the-record/hooks/test_stop_gate.py on-the-record/hooks/test_directive_content.py -q` — result: 19 passed in 0.94s

Before/after timing of `directive.sh` (3 standalone runs each,
`ORCHESTRATE_OFF=1`, warm shell, `/usr/bin/time -f "real %e s"`, cwd a
scratch workspace, before = pre-commit working tree, after = commit
948d2fd4): both measured `0.00s` — the counter write is a single
`printf >>` append, not a network call, so it adds no measurable
wall-clock cost.
derived:
```
$ /usr/bin/time -f "real %e s" bash on-the-record/hooks/directive.sh < payload.json >/dev/null
real 0.00 s
real 0.00 s
real 0.00 s
```

## Why

The #2016 survey (`docs/issue-2016/reports/performance-engineering/survey.md`)
left "how often does Stop/UserPromptSubmit actually fire per session"
as an open finding — no real numbers existed. This gives the next
dogfood run a cheap, always-on counter to read those numbers off of.

## Open findings — gh-auth-probe TTL cache is out of this repo's scope

Issue #2028's other half of the ask — "cache the auth-probe outcome...
following PR #2027's pattern" — names a specific line, cited by the
#2016 survey.

canonical: `docs/issue-2016/reports/performance-engineering/survey.md`
lines 70-79, read this session — cites `directive.sh:41`'s `gh auth
status` probe via `grep -n "gh auth status"
/home/jwjung/tokenmaxxxer-core/core/hooks/directive.sh`.

That path resolves inside a separate git repository (`tokenmaxxxer-core`),
not this one (`on-the-record`, this branch's repo).
canonical: `cd /home/jwjung/tokenmaxxxer-core && git remote -v`, run this
session — origin is `git@github.com:tokenmaxxxer/tokenmaxxxer-core.git`,
a different repo/remote than this session's `on-the-record` checkout.

This repo's own `on-the-record/hooks/directive.sh` (the file issue-2028's
frozen write set actually covers, at commit 948d2fd4) contains no `gh`
invocation at all.
canonical: `grep -n 'gh auth' on-the-record/hooks/directive.sh` at
commit 948d2fd4, run this session.
derived:
```
$ grep -n 'gh auth' on-the-record/hooks/directive.sh; echo "rc=$?"
rc=1
```
Zero matches — no `gh` subprocess call present in this repo's file.

Editing `tokenmaxxxer-core/core/hooks/directive.sh` would mean writing
outside issue-2028's frozen write set (`on-the-record/hooks/`, `spawn.py`,
`tests/`, `test/`, `docs/`) and outside this branch's own git repository
— there is no commit this session can make there that lands through
`issue-2028/performance-engineering`. Per the role-deviation SCOPE-EXCEEDED
rule, the frozen write set stays as delivered above (the fire-counter
half) and this gh-auth-probe half is reported, not built. A `gh`-invocation-
counting test proving "second run makes zero gh calls" (the acceptance's
literal check) cannot be written against this repo's `directive.sh`,
since there is no `gh` call in it to cache.

filed to `docs/reports/deviation-log.md`, this session.

## What did not work

Writing a gh-invocation-counting test against `on-the-record/hooks/directive.sh`
per the acceptance's literal wording — there is no `gh auth status` call
in this file to cache or count (see Open findings above).

## Next steps

Re-file the gh-auth-probe TTL-cache half of #2028 (or open a new issue)
scoped to the `tokenmaxxxer-core` repository's `core/hooks/directive.sh`,
where the `gh auth status` probe this issue describes actually lives.

## Resolution path

A performance-engineering session opened against `tokenmaxxxer-core`
(not `on-the-record`), with a write set covering `core/hooks/directive.sh`,
applying the same TTL-cache pattern PR #2027 used for
`decision-queue-stopgate.sh`'s `spawn.py flows --json` call.
