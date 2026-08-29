<!-- on-the-record orchestrate directive, on-demand section file (issue #2102). Loaded via the always-on index injected by hooks/directive.sh. ${CHECKOUT} below means the on-the-record checkout path printed in that index. -->

- DELEGATION IS THE DEFAULT (issue #699 R2). This applies whether or not
  you are mid-issue-flow above: whenever you hit a judgment point —
  design choice, feasibility, risk, spec ambiguity — recognize it as one
  and delegate it to the matching role instead of deciding it inline
  yourself. A judgment you can answer without touching the repo or the
  ecosystem is still a judgment point; "I could just decide this" is not
  an exemption. Two delegation shapes, and the difference is whether the
  outcome changes the repo:
  - A judgment whose answer does NOT need to change the repo (design/
    feasibility/risk/ambiguity questions) is a CONSULT:
    `python3 ${CHECKOUT}/spawn.py consult <role> "<question>" [--issue
    <n>]` — role skills loaded, judgment rendered, answer returned as
    `{answer, confidence, caveats}`, no branch/commit/PR, but always one
    line appended to this session's own consult-trace shard
    (`docs/issue-<n>/reports/consult-log/<session-ts-pid>.md`, or
    `docs/reports/consult-log/<session-ts-pid>.md` with no issue — issue
    #2333: sharded per session so concurrent consults never fight over one
    path; `spawn.py consult-log --issue <n>` reconstructs the single
    chronological view) whether it succeeds or fails — read `/consult` for
    the full contract. Consults
    are fast enough to wait on inline; they do not need
    run_in_background. When two roles should judge concurrently and
    argue it out instead of one role judging alone, the same no-branch/
    no-PR contract has a concurrent-judgment variant: `python3
    ${CHECKOUT}/spawn.py panel <role_a> <role_b> "<question>" [--issue
    <n>]`.
  - Work whose outcome changes the repo (code, docs, specs) stays a
    DELIVERABLE and goes through the existing issue → spawn → PR path
    above — a consult never substitutes for it.
- YOUR GOAL LOOP (issue #699 R3) — this is what delegation is FOR, not an
  end in itself, and it nests inside everything above rather than
  replacing it: given the user's request, decompose it into the
  judgments and the work needed to reach it; delegate each judgment to a
  consult and each artifact to a spawned role (issue → branch → PR, per
  the flow above); integrate what comes back; continue — re-decomposing
  as new judgments surface — until the goal is reached or you are
  genuinely blocked on the user (never resolve a real ambiguity by
  guessing when a consult or the user could settle it); then report,
  tracing which judgments went to which role and what each one
  returned, alongside the deliverable/PR reporting the flow above already
  asks for. A single exchange of this loop can stay entirely inside a
  consult or two with no deliverable at all — the issue → spawn → PR
  machinery only engages once the loop actually needs the repo changed.

  - YOUR DEVIATION LOOP (issue #803) — nests inside this goal loop, not a
    fifth separate loop: a deviation surfaces mid-loop the same way any
    other new judgment/artifact does. RECOGNIZE: a deviation is anything
    mid-task that is NOT normal task friction — it counts only if
    resolving it needs something the current task's own scope did not
    already call for (an edit outside the task's frozen write set, a
    judgment a role would normally render, a risk that would recur beyond
    this one task). A test failure the task exists to fix, a routine
    lint/type error in the file already being edited, or an expected
    retry is NOT a deviation. Most turns recognize zero — that is the
    empty-state guard, by design. CLASSIFY, only once RECOGNIZE fires:
    INLINE-FIX iff ALL hold — (a) stays inside the frozen write set, (b)
    mechanical (no design/architecture/security/product judgment a
    reviewer would need to weigh alternatives on), (c) does not change
    what the deliverable claims to do, (d) a one-off, not a recognizable
    systemic pattern; otherwise FILE-AS-ISSUE. When the classification
    itself is not obvious from (a)-(d), render it via one `spawn.py
    consult <role> "<question>"` call before acting — the classification
    is itself a judgment point per #699 R2. RESOLVE-AND-CONTINUE: run
    `spawn.py deviation-log-path --issue <n>` (issue #2348: sharded per
    session, role-scoped under `$CLAUDE_SKILL` when set, mirroring
    `consult-log.md`'s own sharding) and append your entry to the path it
    prints. Inline case — apply the fix, append one line — timestamp,
    `inline`, one-line description, the diff's location; resume the
    original task same turn.
    File case — draft the issue, `spawn.py spawn <role> "<task>" --issue
    <n> --background`, append a `filed` line to the same log (timestamp,
    issue number, role, one-line description); wait on it via the
    existing `spawn.py watch --issue <n>` pattern if it blocks the
    original task, otherwise continue other work in parallel; when the PR
    merges, append a `resolved` line (issue number, PR, one line on what
    changed) and resume referencing the resolution. Every deviation,
    inline or filed, leaves exactly one traceable log entry — no entry
    for non-deviations. Full format and rationale: read
    docs/handbooks/deviation-loop.md.

- DELEGATION-CITING APPROVE (issue #707, demoted from
  delegation-post-gate.sh): only an orchestrator session (no CLAUDE_SKILL
  binding) may post an APPROVE comment citing a delegation record as
  provenance — a role-bound session never posts one, for any role; that
  would be self-approval through the delegation path.
- DELEGATED AUTO-JUDGMENT (issue #573, demoted from
  delegated-judgment-gate.sh): auto-approve/auto-reject a candidate
  decision only when a recorded operator judgment under
  docs/issue-<n>/product/*.md covers it (depth axis), the impact is
  mechanically reversible (impact axis), AND a multi-role panel of every
  role with standing reaches unanimous `approve`/`reject`
  (panel-unanimous-support-v1) — any missing precondition escalates to
  the user; never a solo role's verdict, never an inline orchestrator
  call.
- AUTONOMOUS ASYNC COMPLETION (issue #878) — the completion half of the
  #699 R3 goal loop above, not a new loop: when a `watch --follow`
  notification (or a resumed-turn nudge, for a headless install) reports
  that a delegated PR you yourself spawned is **opened / mergeable /
  checks-passed**, your very next action — same turn the notification
  lands in, never deferred — is: verify it (read the diff and checks,
  the same acceptance judgment `/orchestrate:run` step 6 already
  defines — do not invent new verify criteria; also cite which
  requirement — the issue number, or its requirement-digest entry — the
  merged PR answers, issue #1006 req#1) -> `gh pr merge` it ->
  rebuild/re-check against the now-updated default branch -> emit the
  4-part `final_report` (`what_broke`/`what_changed`/
  `what_became_possible`/`what_limits_remain`), naming that
  requirement in `what_changed`, as your reply text.
  This is the LIVE, same-session continuation for an interactive
  installed session — #829/#835/#782's poll/watch machinery is unchanged,
  this only says what you do once it notifies you. A headless (`claude
  -p`) invocation cannot be revived in-process once its turn has ended
  (`code.claude.com/docs/en/headless.md` "Background tasks at exit") —
  for that shape, continuation is an external `claude -p "<nudge>"
  --resume "<session_id>"` re-invocation (spawn.py's roster-entry
  `session_id` field + `--resume`-invoke), never an in-process trick;
  if you are resumed this way, the same verify->merge->rebuild->report
  sequence is what this nudge is asking you to run now.
