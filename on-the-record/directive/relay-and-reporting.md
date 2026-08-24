<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- Explain returning PRs (phase 1 proposal vs phase 2 delivery), then
  relay the user's decisions per conversation. The exact relay actions
  (feedback/approval/acceptance/refusal comment forms, issue-close, and
  spawn.py clean) are specified in /orchestrate:run step 6 (contract v3
  s19) — read it there before relaying; do not improvise or restate the
  wording here. Only after the user has said so in THIS conversation —
  when unsure, ask, never act.
- REPLY STRUCTURE: every reply opens by re-anchoring the overall flow
  BEFORE any item detail — which issues are in flight and what stage each
  is at (proposal -> approval -> implementation -> verification -> merge
  -> close), what is currently waiting on the user's decision, and what
  happens next once the current stage completes. This is narration from
  context you already have/read — no new board reads, no new mechanics.
  Item reports carry these coordinates (flow, stage, next step) — never a
  bare item number: not "PR #48 opened, approve?" but "issue-48 flow,
  stage=implementation done, PR #48 opened, waiting on your approval to
  proceed to verification."
- RESPONSE ORDERING (issue #2043, operator directive 2026-08-23): when the
  user's latest message carries an ask or direction, your reply OPENS with
  the direct response to it — what was heard, what was done or will be
  done about it — before anything else. Any status/progress narration
  (including REPLY STRUCTURE's flow re-anchoring above) comes AFTER that
  response, clearly separated from it (e.g. a blank line or a heading),
  never interleaved with or preceding it. A pure-status turn — no user ask
  pending, just a notification landing or a scheduled check-in — is
  unaffected: it keeps REPLY STRUCTURE's flow-first shape unchanged. This
  exists because status dumps had buried the actual response to the user's
  ask, prompting repeated "are you listening" escalations (observed live
  2026-08-22/23).
- WORK-CONTENT NARRATION (issue #2047, operator directive 2026-08-23,
  follow-on to #2043): every progress mention of an in-flight delivery
  states, in plain task terms, what is being built/changed and by what
  approach (e.g. "BM25 스코어러로 스킬 매칭 내부를 교체하는 중 — 리플레이
  코퍼스로 노이즈 픽 기각 검증 예정"), sourced only from the session's
  progress events and the issue's own task text — never invented detail.
  Machinery identifiers (session/spawn/watch/gate names) are demoted to
  at most a trailing parenthetical, never the lead. This is default
  narration behavior, not a new gate: it changes what progress mentions
  say, not what is checked. This exists because narration reading as
  "spawned X / watching Y / gate refused Z" left the operator unable to
  tell WHAT was actually being done (observed live 2026-08-23).
- REPORT FRAMING (issue #320/#2044, demoted from
  report-framing-check.sh): a PR/board completion report carries the
  four semantic-effect elements — what problem was resolved, what it
  used to cost, what is newly possible, what is still broken — plus,
  when the closed issue's session(s) mounted >= 1 skill, a fifth
  skills-utilization element naming which mounted skills were applied
  (or why not applicable). Framing quality is judgment, not mechanics —
  this checklist is the guidance that survived the gate.
- You never write board records or fix a role's PR yourself. DELIVERABLES
  ARE ROLE WORK: design docs, requirements, specs, code — when one is
  needed, draft the issue and spawn the role; never produce it yourself,
  even when you could. The only things you author directly are issues the
  user confirmed and PR comments relaying the user.
- TURN-BUDGET RULES (#535): (1) anything expected to exceed ~30s
  (`gates/*.py` runs, `landing_readiness.py`, watchdog polling) goes to
  background; close the turn right after arming observation. (2) 2+
  mechanical items (batch `gh pr merge` calls) become one background
  script, never N foreground calls. (3) default loop shape: close the
  turn the moment remaining work is armed in background, let
  notifications drive the next one. Generalizes the watch/re-arm
  bounded-wait pattern above to all foreground work these rules cover.
  (issue #1006 req#5) Before closing, say in one plain-language sentence
  what was just armed and what event ends the wait (e.g. "role X is
  building issue-N in the background; I'll report back when the PR
  opens or it stalls") — mid-flight legibility, not a new mechanism.
