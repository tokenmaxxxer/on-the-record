---
subject: issue-2016
code_under_review: HEAD
loop_state: landed
type: implementation
breaking: false
verdict: pass
---

# Record: single-session hook/gate wall-clock optimization (phase 2)

## What was done

Applied a bash-level short-circuit before the `python3` interpreter spawn
in every PreToolUse gate script identified in phase 1's bucket 3 (20
files under `on-the-record/hooks/`), and a short-TTL cache (default 60s,
`OTR_FLOWS_CACHE_TTL`, override via `OTR_FLOWS_CACHE_DIR`) around the
`gh`-backed `spawn.py flows --json` network round trip in
`decision-queue-stopgate.sh` (phase 1 bucket 5).

canonical: `git diff -- on-the-record/hooks/contract-guard.sh` (this
session's own staged diff)
Each short-circuit is a `grep`-based superset check of that same script's
own authoritative Python condition — e.g. `contract-guard.sh` short-circuits
on `gh` + `pr` + `merge` before its `\bgh\s+pr\s+merge\b` regex; every
`git commit`-gated script short-circuits on the presence of both literal
`git` and `commit` before its own token/regex check.

## Why

Phase 1's survey (`docs/issue-2016/reports/performance-engineering/survey.md`)
measured per-tool-call gate/hook overhead (~2.15s standalone across both
hook layers, dominated by many separate `bash`/`python3` process spawns,
none individually expensive) and Stop-time `decision-queue-stopgate.sh`
(~4.6s, dominated by a `gh`-backed network round trip) as the two buckets
recurring most often per session. Both fixes are removal-shaped for the
common case: skip the `python3` spawn when the command plainly cannot
match (the overwhelming majority of Bash calls in a session are not `git
commit`/`gh pr create`/`gh pr merge`/etc.), and skip the network round
trip when a same-repo answer is already fresh within an hour-granularity
threshold's own tolerance for staleness.

## Basis

Upstream: `docs/issue-2016/reports/performance-engineering/survey.md`
(phase 1), `docs/issue-2016/proposals/2026-08-22-single-session-profiling.md`.
APPROVE posted on the issue authorizing phase 2 delivery.

## Before/after measurement

Both measured standalone (outside the Claude Code harness, per phase 1's
own stated floor-not-ceiling caveat), via file-based payloads (never
`gh pr create`/`gh pr merge` literals inline in a Bash command string —
those strings themselves would trigger the very gates being measured;
payloads were written to `/tmp/otr-bench/*.json` with the Write tool and
read by the timing script instead), 3 reps per script, averaged.

canonical: `bash /tmp/otr-bench/run_bench.sh` (this session's own live
timing run, before via `git stash` of `on-the-record/hooks/*.sh`)
acceptance: `bash /tmp/otr-bench/run_bench.sh` (hooks stashed to pre-change state) — result: TOTAL,1.1234,1.1663

canonical: `bash /tmp/otr-bench/run_bench.sh` (this session's own live
timing run, after with the working tree at its current staged state)
acceptance: `bash /tmp/otr-bench/run_bench.sh` (hooks at current working-tree state) — result: TOTAL,0.2887,1.0708

For the common case (a Bash call that does **not** match any gate's
condition — the majority of calls in a real session), summed across the
21 PreToolUse scripts:

| | before | after | reduction |
|---|---|---|---|
| non-matching payload, summed | 1.1234s | 0.2887s | ~74% |
| matching payload, summed | 1.1663s | 1.0708s | ~8% (python still runs when it actually matches) |

`decision-queue-stopgate.sh` (Stop hook, TTL cache), same two runs above:
before 0.1964-0.2022s per call regardless of payload (always fetches);
after, first call (cache miss) 0.1095s, repeat call within the 60s TTL
(cache hit) 0.0501s — roughly 4x faster on a cache hit, ~2x even on a
cold miss (grep short-circuit does not apply to this hook; the
improvement here is solely the cache write path replacing a second
network call).

## Verification (short-circuit safety)

canonical: `grep -nE "re.search|re.match" on-the-record/hooks/contract-guard.sh on-the-record/hooks/pr-base-guard.sh on-the-record/hooks/merge-allow-gate.sh on-the-record/hooks/quality-bar-gate.sh on-the-record/hooks/pr-preflight.sh on-the-record/hooks/claim-scan-preflight.sh on-the-record/hooks/delegation-post-gate.sh on-the-record/hooks/interaction-design-spawn-check.sh on-the-record/hooks/issue-retrospective-spawn-check.sh on-the-record/hooks/test-authoring-spawn-check.sh on-the-record/hooks/ux-engineering-spawn-check.sh on-the-record/hooks/plan-order-guard.sh`
For each of the 20 PreToolUse-gate short-circuits, this session read that
same script's own Python match condition and confirmed the bash-level
grep check is a strict superset (never narrower) — no short-circuit
produces a false negative (a command the python condition would have
matched but the bash filter skips).

Example — `contract-guard.sh`: python requires `re.search(r"\bgh\s+pr\s+merge\b", cmd)`;
bash short-circuit is `grep -qE 'gh[[:space:]]+pr[[:space:]]+merge' <<<"$payload" || exit 0`,
which matches whenever the python regex would. The `git commit`-gated
scripts (`acceptance-command-real-run-guard.sh`, `gate-registration-guard.sh`,
`live-fire-claim-real-run-guard.sh`, `live-fire-test-guard.sh`,
`perf-measurement-guard.sh`, `requirement-digest-preflight.sh`,
`role-axis-completeness-guard.sh`, `spec-index-preflight.sh`,
`test-authoring-invariant-guard.sh`) each check `git` and `commit` as
plain substrings before their own token/regex `git commit` detection —
strictly broader than any of those detections' `\bgit\s+commit\b`
regex or `shlex.split` token check.

## Test suite

canonical: `python3 -m pytest -q -m "not slow"` — this session's own live run
acceptance: `python3 -m pytest -q -m "not slow"` — result: 2481 passed, 19 xfailed, 2 xpassed in 38.40s

canonical: `python3 -m pytest -q -m slow` — this session's own live run
acceptance: `python3 -m pytest -q -m slow` — result: 106 passed, 1 xfailed, 1 xpassed in 303.69s (0:05:03)

canonical: `python3 -m pytest -q -m "not slow"` and `python3 -m pytest -q -m slow` — result: both runs above, this session's own live runs
Both suites ran clean under this change, per the two `acceptance:` results
immediately above. This repo's `.on-the-record/test-tiers.json` names
`on-the-record/hooks/*.sh` as a `slow`-tier trigger class, so both tiers
were run per the test-tier directive.

## What did not work

None — the two fix shapes (bash short-circuit, TTL cache) both landed
cleanly on the first attempt, with no reverted approach.

## Open findings

canonical: `docs/issue-2016/reports/performance-engineering/survey.md`
(phase 1's own Open findings section, this session's own read)
- Phase 1's own open finding (Stop/UserPromptSubmit firing frequency
  across turns in a live multi-turn session) carries forward untouched:
  this record's before/after numbers are still standalone, per-occurrence
  measurements, not a live-harness session total.
- `directive.sh`'s `gh auth status` probe (phase 1 bucket 2, ~4.0s) is
  out of this issue's scope (`on-the-record/hooks/` per the proposal's
  `files:`/Constraints, not the `core` plugin) and was not touched.

resolution path: a follow-up issue against the `core` plugin repository
would be needed to apply an equivalent cache/short-circuit to
`directive.sh`'s `gh auth status` probe, since that file lives outside
this issue's write-set scope.
