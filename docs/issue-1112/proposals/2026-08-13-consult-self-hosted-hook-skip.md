---
status: proposed
files:
  - spawn.py
  - gates/test_consult_json_parse.py
---

## Request

#1112: `spawn.py consult requirements-engineering ...` failed twice on
2026-08-12T17:29 UTC with `모델 출력에서 판단 JSON 을 못 찾음` — the same
symptom #1097 fixed and live-smoked at 07:53 the same day. Root-cause
whether this is a regression, an environment-sensitive recurrence, or a
new failure mode sharing the symptom; fix it; add a regression guard, not
just another live smoke.

## Constraints

- The issue's own cited traces (docs/reports/consult-log.md
  2026-08-12T17:29:46 / 17:29:56) are not recoverable — survey.md's
  `git log --all -p` count came back 0 for those timestamps anywhere in
  this repo's history. The fix and its guard cannot depend on that lost
  trace; they must reproduce the *failure mode*, not replay the lost log.
- #1097's fix (the consult-prompt override sentence + one retry) must
  stay intact — it is still the correct mitigation for the core-plugin
  directives it targeted.
- `spawn_cmd()`'s (issue-scoped, branch/PR-producing spawns) use of
  `role_settings()` must keep injecting `self_hosted_hooks()` unchanged —
  those sessions genuinely write to the repo and need the repo's own
  Write/Edit/Bash-facing gates (approval-gate, record-claim-guard, etc.)
  active. Only judgment-only call sites (`consult_cmd()` and its sibling
  below) change.

After-proposal hunt (docs/issue-1112/reports/implementation/2026-08-13-hunt-consult-self-hosted-hook-skip.md,
stance 4) found `_run_panel_session()` (spawn.py:4513) is a third
`role_settings()` call site, and its own docstring (spawn.py:4497-4499)
states it is assembled "consult_cmd() 와 똑같이 role_settings()/
plugin_dirs() 로" to avoid the #695/#700 drift class where fixing one
`role_settings()` call site and not its sibling reopens the same bug —
exactly this proposal's original write set left it out. `_run_panel_session()`
is folded into this proposal's scope below.

## Rationale

survey.md traced a second, independent hook-injection path that #1097's
own root-cause note never named: `role_settings()` (spawn.py:620-626)
merges `on-the-record/hooks/hooks.json`'s own hook set
(`self_hosted_hooks()`, spawn.py:416-453) into the session whenever `cwd`
resolves to an on-the-record checkout — which, since `-C/--cwd` defaults
to `"."` (spawn.py:4714) rather than `None`, is every `spawn.py consult`
call made from inside the repo with no `-C` flag, i.e. exactly the
orchestrator's own working context. That hook set (self-update.sh,
session-role-bind.sh, directive.sh, record-claim-shape-directive.sh,
record-tiering-directive.sh, role-deviation-directive.sh, plus a long
PreToolUse block) is separate from the "core"-marketplace directive hooks
(freelunch/scout/warrant/etc.) #1097's override sentence names — it adds
its own SessionStart/UserPromptSubmit injection on top, for every
attempt including the retry, since each attempt is a fresh `claude -p`
process (spawn.py:4421-4423) that pays the full injection cost again.
Within the fixed 180s `CONSULT_TIMEOUT`, this is a second, independent
source of turn-budget pressure the #1097 fix did not touch — consistent
with the issue's own environment-sensitivity hypothesis and with the
follow-up comment that the failure is specific to the orchestrator's own
session context.

Alternative considered and rejected: strengthen the override prompt
sentence further (e.g. explicitly naming `on-the-record/hooks/hooks.json`
directive scripts too) instead of skipping the injection. Rejected
because it treats the symptom, not the cause: the hooks would still fire
and consume turn budget on every attempt regardless of what the prompt
claims about them, so a sufficiently complex question could still exhaust
budget before producing JSON — the same shape of failure #1097's own
prompt-only mitigation already left open once. Skipping the injection at
the source removes the actual budget cost, not just the model's stated
intent to ignore it; consult's own contract (`on-the-record/commands/
consult.md`) already guarantees no repo mutation, no branch, no commit,
no PR, no board write — so the repo's own Write/Edit/Bash-facing
`hooks.json` gates have nothing to guard in a consult session and are
pure overhead there.

## What will be done

1. Add a keyword parameter to `role_settings()` (e.g.
   `inject_self_hosted_hooks: bool = True`) that gates the
   `self_hosted_hooks()` merge at spawn.py:622-625; default `True` keeps
   `spawn_cmd()`'s existing call site behavior unchanged.
2. `consult_cmd()` calls `role_settings(role, cwd, inject_self_hosted_hooks=False)`.
2b. `_run_panel_session()` (spawn.py:4513) calls
   `role_settings(role, cwd, inject_self_hosted_hooks=False)` too — same
   judgment-only, no-repo-write contract as consult (panel sessions are a
   cross-role judgment round-trip, never a deliverable path), so it gets
   the same opt-out to close the drift the hunt flagged.
3. Add `gates/test_consult_json_parse.py`:
   - reproduces the reported failure mode by mocking `subprocess.run` to
     return no-JSON text on both attempts, asserts `consult_cmd()` raises
     `RuntimeError` containing `"모델 출력에서 판단 JSON 을 못 찾음"` and
     `"재시도"`, and asserts the trace file gets an `error:` line.
   - asserts `consult_cmd()`'s settings never carry the
     `on-the-record/hooks/hooks.json` hook set even when `cwd` points at
     a real on-the-record-shaped checkout (fixture: a tempdir with a
     minimal `on-the-record/hooks/hooks.json` under it) — proving the
     opt-out is actually wired, not just present as an unused parameter.
   - the same assertion against `_run_panel_session()`'s settings, same
     fixture — closing the hunt's finding with a covering test, not just
     a matching call-site edit.
4. One live smoke per the issue's acceptance: `spawn.py consult
   requirements-engineering "<tradeoff question>" -C <board repo>`
   returns an `ok:`/`no:` verdict line in the trace.

## Accumulation

Not accumulation-shaped: this is one keyword parameter added to one
existing function (`role_settings()`) and one call-site argument at one
call (`consult_cmd()`), not a per-role or per-file repeated edit — adding
a future N-th role or N-th gate does not touch this parameter again.

## Out of scope

- Recovering or backfilling the lost 17:29 trace entries.
- Changing `spawn_cmd()`'s (issue-delivery path) hook injection.
- Any change to `on-the-record/hooks/hooks.json` content itself.
- General consult observability (e.g. auto-committing
  `docs/reports/consult-log.md` after each call) — a real gap surfaced by
  survey.md, but a separate concern from this parse-failure regression.

## How you'll know it worked

`python3 gates/test_consult_json_parse.py` passes, reproducing the
both-attempts-exhausted failure mode and proving the self-hosted-hook
opt-out; `python3 gates/test_consult_verdict_parsing.py` still passes
unchanged; the live smoke returns a parsed verdict line in the trace.
