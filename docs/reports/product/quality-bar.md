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

- 2026-08-27: design principle for any disambiguation/naming syntax added
  to fix an ambiguity bug (surfaced on issue #2579, `--skills` source
  resolution): the syntax that resolves an ambiguity must be legal
  unconditionally, not only once the ambiguity actually fires. Stated
  directly in the issue body: "Naming the source must be possible always,
  not only when forced... any disambiguation syntax added *only* for the
  collision case is a syntax nobody uses until something breaks — the
  ambiguity exists first and the means to resolve it appears afterward."
  The corollary: a record that only ever names a resolved *result* (e.g.
  a mounted skill's bare name) without a way to also name which *source*
  produced it cannot be re-judged later — "a record saying `--skills
  secure-coding` cannot be re-judged later: which `secure-coding` ran is
  unrecoverable." This generalizes past `--skills`: anywhere a name is
  resolved across more than one candidate source, the resolver should
  accept an explicit source qualifier as a first-class, always-available
  option, not a special form that only exists in the CHANGES/error path.
  Paired constraint from the same issue, so the fix doesn't overcorrect:
  an unqualified name must still resolve on its own when unambiguous —
  "requiring qualification everywhere would be noise." Source: issue body,
  tokenmaxxxer/on-the-record#2579, opened before 2026-08-27
  (https://github.com/tokenmaxxxer/on-the-record/issues/2579).

- 2026-08-27: standing design principle for any liveness/status-reporting
  surface in this codebase (`spawn.py ps`, and generalizable to future
  status commands): an empty/negative result must never conflate "verified
  absent" with "enumeration failed" — a genuinely empty state is legitimate
  and must stay distinguishable from a state the code simply couldn't
  determine. Motivated by two recorded incidents where `ps`'s ambiguous
  empty listing was read as "confirmed dead" and triggered destructive
  action (force-push+merge of a running branch; `git stash` of a running
  session's edits) on sessions that were actually alive. Source: issue
  body, tokenmaxxxer/on-the-record#2203 ("empty state: no sessions running
  is a legitimate empty listing and must stay distinguishable from an
  enumeration failure"; "If enumeration cannot be made reliable, it must
  distinguish 'no session' from 'cannot determine' and say so, rather than
  printing an empty list that reads as authoritative.").

- 2026-08-27: two standing principles for any "was this earlier failure
  superseded/resolved" check added to a retention-pruned ledger in this
  codebase (surfaced on issue #2511, watchdog spawn-attempt staleness):
  (1) evidence-retention symmetry — the proof that an earlier record was
  superseded must survive at least as long as that record does; if the
  positive-outcome evidence is pruned faster than the negative-outcome
  record it would resolve, the check is unsatisfiable in production no
  matter how correct its logic is, and this can hide behind a demo built
  from an isolated/hand-built copy of the ledger that never ran the real
  prune cadence against it — verification for this class of check must run
  against the real, live ledger, not a constructed one. (2) "same work"
  identity across a retry must not require an exact match on the part of
  an identifier that is *designed* to differ every attempt (a lease
  disambiguator, a per-attempt nonce); a differing disambiguator is the
  normal shape of a retry, not an edge case, so an exact-match rule
  silently never fires for real retries while looking correct in a
  hand-built demo. Both principles were the two ways a prior attempt at
  this same fix (PR #2608) failed review. Source: operator's reopen
  comment and correction comment on issue #2511, and operator's review
  comment on the closed PR #2608, relayed via this session's task
  instructions, 2026-08-27.

- 2026-08-27: standing operator requirement for any claimed removal in this
  codebase: "there must be no case where something was declared removed and
  was in fact only reshaped." A grep for the old name is not sufficient
  evidence of removal — it is only the weakest of three checks (name gone /
  reconstructed under another name-shape-file-layout / still branches on
  closed-set membership), and a rename or file-split passes a bare grep
  trivially. This system's own role-axis program declared removal four
  times and reshaped it three of those times (a wrapper function, a rename,
  a 44-file split reassembled by `glob`), each passing its own review at
  the time — so the failure is systematic, not incidental, and a one-time
  sweep is not a sufficient response; a repeatable, rerunnable check is
  required going forward. Source: issue body, tokenmaxxxer/on-the-record#2626.
