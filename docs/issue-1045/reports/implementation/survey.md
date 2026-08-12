# Current-state survey — issue #1045

## Write set this build will touch

- `spawn.py` — `_run_panel_session()` (prompt text only) and `_panel_degrade()`
  (+ one new small helper).
- `tests/test_spawn.py` — new regression tests, `-k panel` selectable.

No other file changes. No new dependency, no env var, no migration.

## Defect 2 — `_panel_degrade()` crashes on a `consult_cmd()` failure

canonical: spawn.py, lines 4517-4529 (read this session)

```
verdict_a = consult_cmd(role_a, question, issue, cwd)
verdict_b = consult_cmd(role_b, question, issue, cwd)
```

`consult_cmd()` (spawn.py, lines 4321-4391) raises `RuntimeError` on a session
exit-code failure, a timeout, or — the case the issue names verbatim — when
`_parse_consult_verdict()` finds no judgment JSON in the model's output
(`"모델 출력에서 판단 JSON 을 못 찾음"`). `_panel_degrade()` calls it unguarded twice,
so that exception propagates straight out of `panel_cmd()`'s degrade branch —
the one path whose entire job is to be the safe fallback when live messaging
isn't available. The degrade path needs to absorb that failure into the
recorded turn instead of letting it raise.

## Defect 1 — no SendMessage round-trip observed live

canonical: spawn.py, lines 4479-4490 (`_run_panel_session()`'s judge prompt, read this session)

Prior investigation (docs/issue-973/reports/product-discovery/current-state.md,
around lines 114-119) had already named the discriminating question: can an
orchestrator-spawned `claude -p` session actually address and message a
sibling session it did not spawn itself, via the official
`ListAgents`/`SendMessage` primitives? Issue #1045's live #973 run answered
"not with the current prompt" — every judge session degraded with "no
SendMessage round-trip observed".

I ran a bounded live reproduction of the same primitive, minimal and outside
the panel prompt's wording, to isolate whether the blocker is structural
(the primitive itself cannot bridge two independently-launched `claude -p`
processes) or a prompting defect (the current judge prompt just doesn't tell
the model how to find and address its peer).

canonical: `/tmp/panel_diag/sessA.jsonl` + `sessB.jsonl`, this session's own
transcript from the reproduction run below.

derived: two `claude -p` sessions launched via backgrounded subshells from
this session's own Bash tool, both `--settings` carrying `crossSessionInbound:
accept` (same key `_run_panel_session()` sets), same `--permission-mode
bypassPermissions --output-format stream-json --verbose` shape. Session A's
prompt: call `ListAgents`; if the peer isn't visible yet, sleep 5s and retry
up to 6 times; once visible, `SendMessage` to the name `ListAgents` actually
returned (not a guessed name); then emit a short fixed sentinel as its last
line of output. Session B: symmetric, reversed roles.

```
=== A tool calls ===
A: ListAgents {}
A: ToolSearch {'query': 'select:SendMessage', 'max_results': 1}
A: SendMessage {'to': 'panel-diag-32', ...}
A: SendMessage {'to': 'panel-diag-32 [00ad27]', ...}
A result: 세션 B(panel-diag-32)에 "hello from A"를 보냈고, B로부터 "hello from B" 메시지도 수신됐습니다.
=== B tool calls ===
B: ListAgents {}
B: SendMessage {'to': 'panel-diag-12', ...}
B: SendMessage {'to': 'panel-diag-12 [0f0fa1]', ...}
B result: 세션 A로부터 "hello from A" 응답을 받았습니다. 양방향 메시지 교환이 확인되었고 ...
```

Reading both sessions' final result text: A's turn shows it sent to and
received from B; B's turn shows the mirror image; the exchange finished
inside the 90s timeout, no retry actually needed in this particular run
(both were visible on the first `ListAgents` call). Reading this as evidence,
not as a fully settled certainty: it answers the discriminating question
#973 posed — the primitive itself is not the blocker. Two independently
`subprocess.run`-launched `claude -p` sessions with `crossSessionInbound:
accept` can discover each other via `ListAgents` and exchange at least one
`SendMessage` round-trip.

That leaves the panel's own prompt as the suspect. Comparing it against what
the reproduction's prompt did differently:

- The reproduction's prompt explicitly instructs the model to call
  `ListAgents` first, and to retry a few times if the peer isn't registered
  yet. `_run_panel_session()`'s current prompt (spawn.py, lines 4479-4490)
  never mentions `ListAgents` at all — it jumps straight to "SendMessage 로
  상대에게 보내라" (send via SendMessage to the counterpart).
- The reproduction addresses `SendMessage` using the exact string
  `ListAgents` returned (`panel-diag-32`, with a bracketed session-id
  suffix). The current panel prompt tells the model to address the peer as
  `'{peer_role}'` (e.g. literally `implementation`) — a role name, not a
  `ListAgents`-visible session identifier. Nothing in the prompt tells the
  model those two things can differ, or how to reconcile them.
- `panel_cmd()` launches both sessions near-simultaneously via
  `ThreadPoolExecutor` (spawn.py, lines 4553-4557); a model that calls
  `ListAgents` once, sees an empty/wrong list because the peer hasn't
  registered its inbox yet, and has no retry instruction, has no path
  forward except to give up — which reads exactly like the "no round-trip
  observed" degrade reason captured in #973's live run.

Working diagnosis: not a structural blocker, a prompting defect — missing
discovery-and-retry instructions and a wrong hard-coded address. Fixable in
the prompt text alone, no transport-layer change. This is a diagnosis backed
by one bounded reproduction, not a certainty; the fix below is proposed on
that basis and its own effect should be judged against a subsequent live
panel_cmd() run, not assumed from this survey alone.

## Existing test coverage

`tests/test_spawn.py` has a `ConsultCmd` class (consult_cmd only) and no
`panel`-named test class or test method at all — `grep -n panel
tests/test_spawn.py`, run this session, returns zero hits.
`panel_cmd()`'s own docstring already documents a `run_session` injection
seam built for exactly this (spawn.py, lines 4540-4544, "이 파라미터가
제안서의 'transport boundary' 다"): tests can seed
`{"turns": [...], "verdict": ...}` without a real `claude -p` process, and
`_panel_degrade()` can be called directly by patching `spawn.consult_cmd`.

## Alternatives considered for defect 1 (rejected)

- **Orchestrator-relayed messaging** (the mailbox path #973's product
  discovery scored as option (c)): have the orchestrator read each session's
  position from a file and hand it to the other, instead of live
  `SendMessage`. Rejected — the live reproduction above shows the official
  primitive works once addressed correctly; downgrading to a file relay
  would abandon req#5's "live discussion" clause for what looks like a
  three-line prompt fix, not a transport failure.
- **Give the session a knowable name up front** (supply a `--name`-style
  flag so the peer can be addressed by a value chosen before spawn, instead
  of discovered via `ListAgents`): no such flag exists in the `claude -p`
  invocation surface used here (`role_settings()`/`plugin_dirs()` construct
  only `--settings`, `--permission-mode`, `--output-format`, `--plugin-dir`,
  `--model`) and the reproduction above shows discovery-via-`ListAgents`
  already works, so adding a new naming surface was rejected as an
  unnecessary extra moving part.
