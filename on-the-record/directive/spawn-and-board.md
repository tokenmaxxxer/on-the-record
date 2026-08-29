<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- Sessions are spawned with
  `python3 ${CHECKOUT}/spawn.py --skills <skill>[,<skill>...] "<task>" --issue <n> -C <path>`
  (`-C`/`--cwd` is a filesystem path, not a repo slug. It defaults to `.`,
  so omit it when the target repo is already the current directory. Issue
  #2572: `--skills` is the sole spawn form — the retired
  role-positional (`spawn.py <role> "<task>"`) and bare-task
  (`spawn.py "<task>"`) forms are both refused, naming `--skills`, if
  typed); read the board first with `python3 ${CHECKOUT}/spawn.py -C <path>`.
  There is no auto-routing table — who runs next is your judgment call
  from reading the board (records under docs/issue-<n>/, each one's
  loop_state).
  Issue #2678: before picking `--skills`, run
  `python3 ${CHECKOUT}/spawn.py --skill-candidates "<task>" --issue <n>` to
  see ranked candidates for that exact task text — same BM25 scoring
  spawn's own internal add-only cross-family mount already uses, so the
  ranking you see here cannot disagree with what spawn would add on top of
  whatever you name. It never spawns a session and never picks for you —
  it prints `{"ranked": [...], "outcome", "picked"}` and you still decide
  `--skills`. Run it whenever the task doesn't obviously match one of the
  skills you already know by name, or whenever a `--skills` guess got
  rejected and you would otherwise just retype the last name that worked
  (that reuse pattern is exactly how one name comes to cover every spawn
  in a day — see the sibling issue on the dead-end resolver error). An
  empty `"ranked": []` with `"outcome": "no-candidates"` means nothing
  matched — proceed with your own judgment, same as today. `outcome` is one
  of `no-candidates`, `bm25-only`, `completed`, `fail-open`, or
  `fast-path:<names>[+completed|+fail-open]` — `fail-open` means the judge
  errored or timed out but `ranked` (BM25) is still fully populated, never
  collapsed into `no-candidates`. Add `--with-judge` for the same haiku
  judge refinement spawn's own internal mount uses (an extra LLM call +
  consult-trace commit) instead of the free BM25-only ranking — note this
  preview asks for `k=2` candidates by default while spawn's own internal
  mount asks for `k=5` (`_COMPOSED_SKILLS_TOPK`), so a `--with-judge`
  preview is the same scoring and judge call, not a byte-identical result
  to what spawn would actually mount. The board reflects MERGED main only — an open PR changes
  nothing there, so after EVERY merge (and every new issue) re-read the
  board unprompted and propose what runs next in the same reply, with
  your reasoning. If nothing looks ready, say that and why.
  ALWAYS spawn IN THE BACKGROUND (run_in_background: true) — a spawned
  session runs for minutes and the conversation must not block on it.
  Keep talking with the user; when the completion notification arrives,
  read the spawn output and report the outcome (the PR, or the refusal)
  in your next reply. Multiple spawned sessions may run concurrently — each gets its
  own isolated workspace. PROGRESS CHECKS: `spawn.py --skills <skill>
  "<task>" --issue <n>` and `spawn.py watch --issue <n>` both return early, at
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
  NO REDUNDANT WATCHER, BY ANY MECHANISM (issue #2156): after `spawn.py`
  returns, do not build a separate standing watch loop for that spawn by
  ANY means — not a separate Agent (general-purpose or otherwise) whose
  sole job is to poll it to completion, and not a substitute with the same
  shape, such as a backgrounded `Bash(run_in_background: true)` sleep-and-
  poll loop, a cron/schedule entry, or any other mechanism that re-checks
  spawn/session status on a timer outside the sanctioned calls below. The
  prohibition is on the PATTERN (a standing loop re-deriving status the
  platform already pushes), not on the specific tool used to build it —
  swapping the tool while keeping the loop is still the forbidden pattern.
  Such a loop cannot actually block-wait for the spawn's terminal state,
  so it self-polls, producing content-free "still waiting" notifications
  every couple of minutes — pure duplicate overhead of what the
  mechanisms above already provide for free: the spawn's own watcher
  process plus the `spawn.py watch`/`--follow` poll cycle already surface
  HEALTHY/RUNNING/anomaly/returned-PR events as notifications to this
  session automatically. Trust those and act on them when they arrive; the
  only sanctioned direct status checks are a one-shot `spawn.py ps` or
  `spawn.py watch --issue <n> --session <s>` call — never a standing loop of
  any kind.
- SPAWN INDEPENDENT WORK TOGETHER, NOT ONE-THEN-WAIT (issue #2382): before
  spawning, check whether more than one pending spawn has no data dependency
  on another pending spawn's output. If so, dispatch ALL of them as
  background spawns in the SAME reply/turn — never spawn one, wait for its
  completion notification, and only then spawn the next, when nothing about
  running either session actually requires the other's result first.
  Concrete example (the observer-pair case, issue #2380): a same-issue
  conformance-review and execution-observation are independent siblings —
  both read the same merged commit, produce independent records, and
  neither's session needs the other's output to run (the only real
  dependency between them is at MERGE time, via `merge_gate`'s cross-check,
  which #2380 handles separately). Launch both together, naming each by its
  skills (issue #2572): `spawn.py --skills conformance-review-verdict-assignment
  "<task>" --issue <n> -C <path>` covers conformance-review — the seven
  `conformance-review-*` skills in skill-repository. `execution-observation`
  has no corresponding skill yet (checked: nothing under skill-repository's
  `observ*`/`verif*`/`defect*` names matches; this is a skill-repository gap,
  out of on-the-record's own reach) — until one exists, rely on
  `spawn_on_pr.py`'s skip-eligibility classification (issue #745) to tell
  whether a given subject even requires an execution-observation record, and
  otherwise flag the gap to the human rather than guessing a substitute
  skill name. Whichever pair is actually spawnable, dispatch back-to-back in
  the same turn, both backgrounded, before returning to the user — not one
  spawned and awaited before the other is even issued.
  Measured (issue #2382, docs/issue-2382/reports/implementation.md): a
  same-issue conformance-review + execution-observation pair run
  concurrently finished faster than the same pair run sequentially — see
  that record for the wall-clock numbers. Reserve one-then-wait for spawns
  that genuinely consume a prior spawn's output (e.g. a session reviewing
  another session's just-opened PR, or a later `## 실행 계획` step per the
  EXECUTION-PLAN ORDER rule below) — the default for anything else is
  together, not serial.
- EXECUTION-PLAN ORDER (issue #659, demoted from plan-order-guard.sh):
  when the issue body declares an `## 실행 계획` block, spawn/merge in
  its declared step order (`‖` marks parallel-safe steps;
  gates/flows.py:plan_order_blocked is the reference computation) — do
  not run a later step while an earlier sequential step is
  unfinished.
- DECISION-QUEUE VISIBILITY (issue #466/#374, demoted from
  decision-queue-stopgate.sh): when reading the board, also read
  `spawn.py flows --json`'s decision_queue; an item aged >= 1 hour is
  surfaced to the user in your next reply, and one aged >= 4 hours is
  treated as the turn's first priority — an operator decision must not
  sit unread across turns.
