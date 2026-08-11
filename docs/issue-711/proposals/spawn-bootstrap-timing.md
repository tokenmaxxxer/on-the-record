---
status: proposed
files:
  - spawn.py
  - test/test_bootstrap_timing.py
  - docs/issue-711/reports/implementation/survey.md
  - docs/issue-711/proposals/spawn-bootstrap-timing.md
---

## Request

Instrument `spawn.py`'s per-spawn bootstrap path (workspace fetch, branch
checkout, rulebook fetch, core plugin fetch, plugin-dir assembly) so its
wall-clock cost is visible per phase and per spawn, both in the human-readable
spawn log and as a machine-readable line. From real measurements, propose
(not yet implement — that is step 2) the highest-yield remaining reduction of
the repeated fixed cost, without letting a role session run on a stale
rulebook/core clone silently.

## Constraints

- Never weaken the freshness guarantee: the existing TTL mechanism
  (`_pull_is_fresh`/`_ttl_marker`, spawn.py:59-88, landed under issue #285)
  already bounds rulebook/core staleness to a configurable window
  (`MUSTER_RULEBOOK_TTL`, default 15 min). Any further change must keep an
  explicit, bounded answer to "how stale can this get," never an implicit one.
- No new dependency, no new env var beyond what's already `MUSTER_*`-namespaced.
- Instrumentation must not change `_spawn_one`'s control flow or exit codes —
  step 1 is measurement only.
- Timing output must survive being read by both a human (the existing stderr
  status line) and a script (ledger/board tooling), per the issue's acceptance
  check ("machine-readable line").

## Rationale

**Chosen approach: wrap each existing bootstrap call with a lightweight timer
context and emit a summary line, no protocol change to the calls themselves.**

Alternative considered and rejected: **give `gh_token` its own phase timer
around `spawn_cmd`'s `_resolve_gh_token()` call**, matching the issue's naming
of bootstrap phases one-to-one with call sites. Rejected because the survey
found `_resolve_gh_token()` is already cached process-wide
(`_GH_TOKEN_CACHE`, spawn.py:3885) specifically because `issue_workspace`/
`checkout_issue_branch` already resolve it earlier (via `_git_env()` →
`_fetch_or_halt`) in the same spawn. Timing `spawn_cmd`'s call in isolation
would read ~0 on every `--issue`-scoped spawn (the normal case) while the real
`gh auth token` shell-out cost — which did happen — sits silently inside
whichever of `workspace`/`branch` triggered the cache fill first. Instead,
the timer wraps `_resolve_gh_token()` itself (memoizing its own first-call
duration) and the summary line attributes that one shared cost explicitly as
`gh_token=`, decoupled from which phase happened to trigger it — this is
more accurate than either merging it into `workspace` (loses visibility) or
pretending `spawn_cmd`'s call has its own cost (double-counts nothing, but
reports a number that is always misleadingly ~0).

Alternative considered and rejected: **wire the timing into a general
profiling/tracing library** (e.g. `cProfile`, an OpenTelemetry span exporter).
Rejected because the ask is five specific phases, not general profiling —
pulling in a tracing dependency for a handful of `time.monotonic()` deltas
is exactly the kind of new dependency the write-set/no-footgun discipline
warns against, and it would need its own sink that doesn't exist yet in this
single-host CLI tool.

Alternative considered and rejected: **propose extending the existing TTL
skip (issue #285) to the workspace/branch `git fetch` calls now, in this
step**. Rejected for ordering, not merit: the issue's acceptance section
requires step 2's reduction to cite before/after numbers from step 1's
instrumentation on this host — proposing the technique before any number
exists would repeat the failure the survey-order discipline names explicitly
(a rationale wrapped around a decision already made). The survey's "What
issue #285 already delivered" section records this as the standing candidate
for step 2 to evaluate once real numbers land, not something step 1 decides.

## What will be done

1. Add a small `_Timing` helper (dict of phase name → seconds, built with
   `time.monotonic()` deltas) local to `spawn.py`; no new module.
2. Wrap these phases in `_spawn_one` (spawn.py:4308) with the timer:
   `workspace` (`issue_workspace`, spawn.py:3975), `branch`
   (`checkout_issue_branch`, spawn.py:4088), `rulebook` (`plugin_dirs` →
   `rulebook_checkout`, spawn.py:185, including its TTL-skip branch — a fast
   TTL hit should show up as a near-zero `rulebook=` reading, which is itself
   evidence the skip is working), `core` (`core_plugin_dirs` → `core_root`,
   spawn.py:3181, same TTL-aware wrap), `gh_token` (`_resolve_gh_token`,
   spawn.py:3888 — timed at its own memoization point per the Rationale
   above, not at `spawn_cmd`'s call site), `settings` (`role_settings` +
   tempfile write, spawn.py:4375-4378).
3. Emit the summary as **one additional stderr line** immediately after the
   existing `print(f"[{role}] 플러그인 {len(plugins)}개, ...")` status line
   (spawn.py:4380), in a `key=value` machine-parseable shape, e.g.:
   `[role] bootstrap_timing workspace=0.42 branch=0.03 rulebook=0.01 core=0.01 gh_token=0.09 settings=0.01 total=0.57`
   — parseable via simple `key=value` split; a near-zero `rulebook=`/`core=`
   reading on a TTL-hit spawn and a larger one on a TTL-miss spawn is exactly
   the evidence step 2 needs to size the remaining gap.
4. `--dry-run` runs the bootstrap phases through settings assembly before
   exiting (already true today — dry-run stops before `spawn_cmd`'s actual
   `claude` invocation, not before bootstrap), so the timing line is
   observable from a dry-run without spending on a real session — this is
   what the acceptance check's "spawn dry-run (or fixture)" targets.
5. Add `test/test_bootstrap_timing.py`: a unit test that calls the timing
   wrapper directly (or drives a `--dry-run` spawn against a fixture role/repo)
   and asserts the emitted line contains all six named phases with numeric
   durations. Matches the issue's acceptance check verbatim.
6. Once real numbers exist, propose (in a follow-up decision record, not this
   document) the specific remaining reduction — per the survey, the only
   named candidate not already covered by issue #285's TTL mechanism is
   **warm pool**, plus possibly extending the existing TTL skip to the
   workspace/branch `git fetch` calls, which currently only dedupe
   within-process and have no cross-spawn TTL. That technique choice is step
   2's implementation, gated on this step 1's real timing data landing first.

## Accumulation

The instrumentation adds one more inline `time.monotonic()` wrap per bootstrap
phase inside `_spawn_one`/`_resolve_gh_token` — the same shape as the existing
uninstrumented calls it wraps, not a new abstraction layer. If this pattern
repeats N more times (e.g. a future issue wants to time individual gate hooks,
or per-tool-call latency inside the child session), inline
`time.monotonic()` deltas scattered across `spawn.py` stop being readable and
should be consolidated into a small shared `_Timing` context manager (a single
`with timed(name): ...` helper) rather than each call site hand-rolling
start/stop pairs — this proposal introduces exactly one such helper now
(step 1 above) specifically so the six phases share it instead of six
independent hand-rolled timers; a second unrelated timing need should reuse
this same helper, not add a seventh pattern. No `roles/*.json`-style
repeated-file edit is involved — the change is confined to `spawn.py` and one
new test file, both singular.

## Out of scope

- Implementing any reduction beyond what issue #285 already landed
  (cache-and-verify/skip-unchanged for rulebook/core pulls) — evaluating and
  implementing warm-pool or TTL-extension-to-fetch is step 2, gated on this
  step's before/after numbers per the issue's acceptance section.
- Changing `gates/` or `hooks/` (issue-659 phase 2's declared write set) —
  confirmed clear of this proposal's write set per the survey's concurrency
  check.
- Any change to `role_settings`'s merge semantics, sandbox policy, the TTL
  window's default value, or the freshness-check *logic* itself (only phase
  durations are measured here — `MUSTER_RULEBOOK_TTL` stays untouched).
- A machine-readable sink beyond the stderr `key=value` line (no ledger
  schema change, no new JSON file) — the issue's acceptance check only
  requires the line to exist and be parseable, not a persisted store.

## How you'll know it worked

- `python3 spawn.py <role> <task> --issue <n> --dry-run` (or the new unit
  test's fixture path) emits a stderr line starting `bootstrap_timing` with
  all of `workspace=`, `branch=`, `rulebook=`, `core=`, `gh_token=`,
  `settings=`, `total=` present and numeric.
- `test/test_bootstrap_timing.py` passes and fails when the timing line is
  absent (the issue's stated "empty state" check).
- No existing test in the repo's suite regresses (control flow and exit codes
  of `_spawn_one` are unchanged — timing is additive).
- A TTL-hit spawn (`rulebook=`/`core=` near zero) and a TTL-miss/first spawn
  (`rulebook=`/`core=` in the hundreds-of-ms-to-seconds range) are visibly
  distinguishable in the emitted line — confirming the instrumentation
  actually reflects the skip-unchanged mechanism already in place, not just a
  constant.
