<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- Roles are spawned with
  `python3 ${CHECKOUT}/spawn.py <role> "<task>" --issue <n> -C <repo>`;
  read the board first with `python3 ${CHECKOUT}/spawn.py -C <repo>`.
  There is no auto-routing table — who runs next is your judgment call
  from reading the board (records under docs/issue-<n>/, each one's
  loop_state). The board reflects MERGED main only — an open PR changes
  nothing there, so after EVERY merge (and every new issue) re-read the
  board unprompted and propose the next role in the same reply, with
  your reasoning. If nothing looks ready, say that and why.
  ALWAYS spawn IN THE BACKGROUND (run_in_background: true) — a role
  session runs for minutes and the conversation must not block on it.
  Keep talking with the user; when the completion notification arrives,
  read the spawn output and report the outcome (the PR, or the refusal)
  in your next reply. Multiple roles may run concurrently — each gets its
  own isolated workspace. PROGRESS CHECKS: `spawn.py <role> "<task>"
  --issue <n>` and `spawn.py watch --issue <n>` both return early, at
  the first material event (PR opened, gate refusal, session end) or
  after `--stall-timeout` minutes (default 5) with no session activity
  — never wait longer than that for either call. After EVERY spawn, and
  after every `watch` call returns an event that is not session-end
  (including `stall`), re-arm by calling `spawn.py watch --issue <n>`
  again before doing anything else — this block-then-report cycle IS the
  progress-check mechanism; there is no separate "check logs when idle"
  judgment call, and a `stall` report is just another reason to re-arm,
  not a different code path. This is unrelated to reading the board for
  who's next (merged main only still governs when COMPLETED work
  reopens the board); watch only reports on a session that is still
  running. `spawn.py watch --issue <n> --follow` streams the same
  `_await_bounded` results in one call until session-end, so the
  manual re-arm loop above is not required with it — the loop remains a
  valid alternative when you want to see each event land one at a time.
- EXECUTION-PLAN ORDER (issue #659, demoted from plan-order-guard.sh):
  when the issue body declares an `## 실행 계획` block, spawn/merge in
  its declared step order (`‖` marks parallel-safe steps;
  gates/flows.py:plan_order_blocked is the reference computation) — do
  not run a later step's role while an earlier sequential step is
  unfinished.
- DECISION-QUEUE VISIBILITY (issue #466/#374, demoted from
  decision-queue-stopgate.sh): when reading the board, also read
  `spawn.py flows --json`'s decision_queue; an item aged >= 1 hour is
  surfaced to the user in your next reply, and one aged >= 4 hours is
  treated as the turn's first priority — an operator decision must not
  sit unread across turns.
