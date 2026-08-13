# issue-1112 survey — consult 'ok판단 JSON 을 못 찾음' recurrence

Scout skip: pure bugfix (regression root-cause + fix + regression guard on
an existing code path) — no product/design decision open, so the scout
sweep is skipped per scout-directive's mandatory skip condition.

## What the issue's own trace citation resolves to

canonical: `git log --all -p -- docs/reports/consult-log.md` (full
history of the file, this working tree)

derived: `git log --all -p -- docs/reports/consult-log.md | grep -c "17:29:4\|17:29:5"`

```
0
```

The two entries the issue cites (docs/reports/consult-log.md at
2026-08-12T17:29:46 and 17:29:56) do not appear anywhere in this repo's
git history per the count above.

canonical: `docs/reports/consult-log.md` (working-tree read, this repo)

derived: `wc -l docs/reports/consult-log.md`

```
9 docs/reports/consult-log.md
```

derived: `grep -oE '^- 2026-08-12T[0-9:]+' docs/reports/consult-log.md`

```
- 2026-08-12T07:42:13
- 2026-08-12T07:47:22
- 2026-08-12T07:53:18
```

The file on `main` carries 3 log lines total, all from the #1097 phase-2
smoke earlier the same day. Whatever local trace the orchestrator session
wrote at 17:29 was never committed. This is a real observability gap (a
consult failure trace can be lost if the calling session never commits
`docs/reports/`), but it is separate from the parse-failure root cause
below — the failure *mode* (`모델 출력에서 판단 JSON 을 못 찾음`, retry
included, both attempts fail) is independently reproducible from the code
without needing the lost trace.

## Current code path

canonical: `spawn.py:4350-4443` (consult_cmd, this working tree)

`consult_cmd()` builds its session with:
- `plugins = plugin_dirs(role, spec)` (spawn.py:4376) — the role's own
  rulebook.
- `s = role_settings(role, cwd)` (spawn.py:4377) — sandbox + hook merge.
- `--plugin-dir` for every `plugins` entry AND every `core_plugin_dirs()`
  entry (spawn.py:4384-4387) — this is where the "core" marketplace's
  freelunch/scout/warrant/no-mock/no-footgun/proposal-shape/record-shape/
  survey-order/terse directive hooks come from (visible verbatim as this
  very session's own `<*-directive>` system-reminders).

canonical: `spawn.py:620-626` (role_settings, this working tree)

`role_settings()` does a SECOND, independent hook injection that #1097's
own root-cause note does not mention:

```
620   # on-the-record 가 자기 자신을 대상으로 스폰할 때만, 자기 hooks.json 을
621   # 병합해 넣는다 — 컨슈머 설치 경로 밖에서는 늘 inert 였다(이슈 #508).
622   if cwd is not None:
623       injected = self_hosted_hooks(cwd)
624       if injected:
625           s["hooks"] = injected
626   return s
```

canonical: `spawn.py:416-453` (self_hosted_hooks, this working tree)

`self_hosted_hooks(cwd)` returns the parsed `"hooks"` value of
`<resolve(cwd)>/on-the-record/hooks/hooks.json` whenever that file exists
under `cwd` — i.e. whenever `cwd` resolves to an on-the-record checkout
(self-hosted target). `role_settings()`'s own `cwd is not None` guard is
not a real filter for CLI callers:

canonical: `spawn.py:4714` (argparse `-C/--cwd` definition, this working
tree)

`spawn.py`'s `-C/--cwd` argparse flag defaults to `"."`, never `None`, so
every `spawn.py consult ...` invocation from inside an on-the-record
checkout with no `-C` flag at all resolves `cwd="."` to that checkout and
triggers the injection.

canonical: `on-the-record/hooks/hooks.json` (working-tree read, this
repo)

`on-the-record/hooks/hooks.json` itself declares its own
`SessionStart`/`UserPromptSubmit` hooks (self-update.sh,
session-role-bind.sh, directive.sh, record-claim-shape-directive.sh,
record-tiering-directive.sh, role-deviation-directive.sh) plus a long
`PreToolUse` set aimed at Write/Edit/Bash. These are a **separate hook
set** from the "core" marketplace hooks already loaded via
`--plugin-dir` — not a duplicate of them. #1097's fix added one override
sentence to the consult prompt naming "스카우트, 제안서(proposal) 작성,
위임, 승인 게이트, 기록 작성" — that sentence addresses the core-plugin
directives (matching #1097's own root-cause note, which cites only
"freelunch/scout/warrant" as the culprit) but never names or accounts
for the second, on-the-record-owned hook set that `role_settings()`
layers on top whenever `cwd` is self-hosted.

## Why this reproduces the reported symptom and its env-sensitivity

A consult session whose `cwd` resolves to the on-the-record repo itself
(the orchestrator's own working directory — matches the issue's own
follow-up comment: "Failure appears specific to consult invoked from the
orchestrator session context (possibly the -C target...)") receives BOTH
hook sets on every turn, including the retry turn: each attempt is a
fresh `claude -p` process (canonical: `spawn.py:4421-4423`, this working
tree) so the retry re-pays the full injection cost — it does not resume
a session that already spent its budget once. A consult session whose
`cwd` does not resolve to an on-the-record checkout root in that exact
relative shape (e.g. a role-session's own workspace, matching the
issue-1111 role session's successful consult the same day) never
triggers `self_hosted_hooks()` and only pays the core-plugin injection
cost #1097 already covers. Within a fixed 180s budget (canonical:
`spawn.py:66`, `CONSULT_TIMEOUT = 180`), whether the extra injected block
pushes a given run over budget is exactly the kind of environment-
sensitive, close-to-the-edge failure the issue names as possibility #2 —
consistent with the same question class passing at 07:53 and failing
twice at 17:29 the same day with no code change in between.

## Existing regression coverage and the actual gap

canonical: `gates/test_consult_verdict_parsing.py` (this working tree)

That file (issue #1097) covers: parsing a captured real transcript,
`None` on no-JSON text, recovery when the *retry* attempt succeeds, and
that the prompt carries the override sentence.

canonical: `tests/test_spawn.py` (this working tree)

derived: `grep -rn "attempts_exhausted\|재시도 1회 포함\|모두 실패" tests/test_spawn.py gates/`

```
(no output)
```

Neither `tests/test_spawn.py` nor any `gates/` file exercises
`consult_cmd()`'s own both-attempts-exhausted branch (spawn.py:4429-4435)
— `tests/test_spawn.py`'s consult-adjacent tests mock `consult_cmd()`
itself to test `_panel_degrade()`'s error handling; they never call the
real `consult_cmd()` with a fake `subprocess.run` that fails on *both*
attempts. That branch has no covering test today per the grep above.
This is the concrete regression-guard gap the issue's acceptance
criterion (a new gates/test_consult_json_parse.py file — path does not
exist yet in this working tree, to be created by the fix) names.

## Write set the fix will touch

- `spawn.py` — give `consult_cmd()` a way to opt out of the self-hosted
  hook merge that #1097 never accounted for: a `role_settings()`
  parameter, off by default so `spawn_cmd()`'s call site keeps its
  current argument list, that `consult_cmd()` sets explicitly to skip
  the merge.
- a new regression test file under `gates/` (planned name:
  test_consult_json_parse.py, matching the issue's acceptance text) —
  covers the both-attempts-exhausted path (raise + `error:` trace line)
  and the self-hosted-hook-merge-is-skipped behavior for consult.
