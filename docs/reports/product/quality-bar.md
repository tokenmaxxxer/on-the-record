# Quality bar

Append-only, newest entry last.

- 2026-08-25: operator-frozen constraint on infrastructure/tooling fixes to
  on-the-record itself (issues touching spawn.py/pipeline.py/skills.py/
  gates/hooks, not target-repo deliverables): a fix must hold systemically
  for every session that installs on-the-record and works against any
  target repo, not just the self-hosted checkout, and must land without
  side effects — no added per-spawn overhead or steady-state load, no new
  conflict surfaces (append-log or otherwise), no stall/deadlock modes, no
  consumer-tree pollution. Reviewers grade against this bar directly: a
  delivery that works on the self-hosted checkout but adds overhead, a new
  contention point, or consumer-visible residue elsewhere does not meet it.
  Where a trade-off is unavoidable, it must be measured and stated in the
  record at delivery time, not discovered later. Source: operator comment
  on issue #2250, 2026-08-25T01:28:11Z
  (https://github.com/tokenmaxxxer/on-the-record/issues/2250#issuecomment-5403812705).

- 2026-08-25: design principle for any retention/grace-period bound in this
  codebase (surfaced on issue #2431, spawn-attempt prune bound): a calendar
  bound is only justified while the outcome it's protecting against is
  still genuinely uncertain. Once a check has already produced a
  confirmed, final answer (e.g. `_pid_is_alive()` returning `False` —
  the process is gone, nothing further can change that), no additional
  waiting learns anything new, so no calendar delay should be applied to
  that case at all; time-bounding belongs only to the case where the
  check itself is ambiguous (e.g. an inconclusive `OSError` from a
  liveness probe). A short bound "just to be safe" on an already-certain
  outcome is not a safety margin, it's unjustified latency — reviewers
  should push back on it the same way they'd push back on an
  under-justified long one. Source: operator comment on issue #2431,
  2026-08-25T13:24:28Z
  (https://github.com/tokenmaxxxer/on-the-record/issues/2431#issuecomment-5411038089).

- 2026-08-25: refinement to the entry above, surfaced by a CHANGES round
  on the same issue (#2431, PR #2434/#2438): "no calendar delay once an
  outcome is confirmed-final" governs only bounds whose purpose is
  re-checking that same outcome — it does not license removing a bound
  that exists for a *different* invariant. The PR #2434 fix that dropped
  the age check entirely for confirmed-dead-pid spawn-attempt records
  (correctly, per the entry above, as far as liveness re-checking goes)
  had a side effect the entry didn't anticipate: it could delete a record
  before the watchdog's own report loop — gated on a separate threshold,
  `SPAWN_ATTEMPT_GRACE_SEC` — ever got a chance to report it, so a
  fast-dying genuine halt could vanish with zero reports ever fired.
  PR #2438's execution-observation caught this before merge. The fix
  reintroduced a bound for the dead-pid case, but tied to the report
  loop's own existing threshold rather than a new or reused-elsewhere
  constant — the bound's job is "guarantee this record was reviewable at
  least once before deletion," not "wait in case the death determination
  might not be final." Generalizable lesson for future retention/prune
  work: before removing a bound because the underlying check is already
  certain, check whether anything *downstream* (a report loop, an
  audit trail, a consumer) also depends on that bound's timing to get its
  own turn first — certainty about one thing doesn't imply nothing else
  needs the delay. Source: this session's task instructions relaying
  PR #2438's execution-observation finding on issue #2431, 2026-08-25.

- 2026-08-26: before implementing a fix for a resource-leak/crash-recovery
  mechanism, the record must state explicitly whether the leak's observed
  *scale* was driven by abnormal load/unusual conditions (so the mechanism
  is a rare-case backstop) or by a chronic path that fires under normal
  usage too (so the mechanism is the primary fix) — and must read the
  actual call sites for non-crash early-exit gaps (a caught exception, an
  early return) rather than assuming the crash-only case is the only
  contributor. An honest "primarily X, could not fully attribute Y" is an
  acceptable answer; an unstated assumption about which case applies is
  not. Source: operator comment on issue #2468, 2026-08-26T00:26:12Z
  (https://github.com/tokenmaxxxer/on-the-record/issues/2468#issuecomment-5418860838).
- 2026-08-26: when a fix gitignores/untracks a repository path that was
  previously (even if accidentally) tracked, the rollout must be checked
  for whether it turns an existing write path into a silent no-op —
  "silent loss is the exact failure class this program is fixing," so a
  CHANGES round dispatch treats that check as mandatory, not optional
  polish. Concretely: verify what happens when something still tries to
  `git add` the now-ignored path — an explicit, named add should fail
  loudly (git's own default behavior), and a broad add's silent skip is
  only acceptable if nothing anywhere actually reads a committed copy of
  that path (checked against the reader code, not just a design doc's
  classification of the path). State the verified behavior in the
  record; don't assume it. Source: this session's task instructions,
  CHANGES round 2 on PR #2445 (issue #2381), 2026-08-26, re: untracking
  `.orchestrate-hook-fires.log`/`.orchestrate-hook-fires/`.
- 2026-08-27: no per-category carve-outs for the spawn single-phase
  default. When a session faced the choice of treating observer spawns
  (verification-record-only, no code_under_review) as their own
  exception to the build-now default versus just ordinary single-phase
  work like everything else, the operator ruled for the latter: "Do not
  deliberate it further and do not build a separate category for
  observers... observers get no special case; they are simply not an
  exception to the default." The corollary that generalizes: a shared
  default (single-phase/build-now) should stay one mechanism every spawn
  path inherits, not a base case plus role-specific exceptions layered
  on top — a role-shaped carve-out is exactly the kind of divergence
  that goes silent the next time someone adds a caller. `--two-phase`/
  `--checkpoint` remain the only sanctioned opt-outs, and they stay
  explicit, human-invoked flags, not inferred from role identity. Source:
  operator comment on issue #2574, 2026-08-27T01:21:04Z
  (https://github.com/tokenmaxxxer/on-the-record/issues/2574#issuecomment-5433139986).
