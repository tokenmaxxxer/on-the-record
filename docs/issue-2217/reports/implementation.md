---
issue: 2217
role: implementation
loop_state: landed
upstream:
  - path: f8c02940016844e868e626b9c4acaad3baae5e23
    sha: f8c02940016844e868e626b9c4acaad3baae5e23
code_under_review:
  - events.py
  - spawn.py
  - watchdog.py
  - tests/test_watchdog_local_signals.py
type: fix
breaking: false
verdict: pass
---

# issue-2217 — implementation record

## What was done

CORE_BUILD_NOW=1 build-now bypass — delivered directly on this branch, no
phase-1 proposal round (no open design decision: the issue names the exact
precedent transition to replicate).

watchdog signal 2 ("background-delegation-phrasing") word-matched
`run_in_background|백그라운드|delegate|background worker` against the
entire scanned log slice (`_DELEGATION_RE`, was `watchdog.py:98-99`,
applied at `spawn.py:935`). Every spawned session gets an injected
directive warning it *against* background delegation using exactly those
words (`spawn._COMPLETION_PROSE`), so the regex matched its own warning
and fired unconditionally — measured at 100% of recent sessions (#2204
both observer roles, #2208, #2210, #2214, #2215; see Acceptance evidence
below for a live re-run against those exact logs).

Applied the same structural-parsing transition issue #994 already made
for signal 3 (`_count_structural_denials`, replacing "denied" word-count
with structural `tool_result`/`is_error` parsing):

- Added `_count_structural_delegations(text)` to `events.py`, next to
  `_count_structural_denials`. Parses the log slice as line-delimited
  JSON, and counts only `type: "assistant"` lines whose `message.content`
  holds a `tool_use` block with a truthy `input.run_in_background` — the
  same act #994 already made countable for denials, not a vocabulary
  match. Malformed/truncated lines are skipped silently (same tolerance
  as `_count_structural_denials`, since the scanned slice can end
  mid-line while the live session is still writing it).
- `spawn.py:935` now checks `_count_structural_delegations(text) > 0`
  instead of `_DELEGATION_RE.search(text)`; re-exported the new function
  next to `_count_structural_denials` in spawn's events re-export block.
- Removed the now-dead `_DELEGATION_RE` regex and its re-export
  (`watchdog.py`, `spawn.py:153`) — nothing else referenced it.
- Updated `tests/test_watchdog_local_signals.py`:
  `test_every_inventoried_signal_type_still_derivable` fed a plain-text
  line containing the word `run_in_background` to trip the old regex;
  replaced with a structural `tool_use`/`run_in_background` fixture line
  so the test still exercises signal 2 under the new detector. Added a
  new `TestBackgroundDelegationStructural` class covering: the injected
  directive alone (empty-state acceptance criterion), the directive's
  vocabulary inside an assistant *text* block (must not fire), a genuine
  `Bash` tool_use with `run_in_background: true` (must fire), a genuine
  `Agent` tool_use with `run_in_background: true` (must fire — the
  detector is tool-name-agnostic per the issue's "Bash ... or an
  Agent/Task call" wording), and two direct unit tests on
  `_count_structural_delegations` itself.

## Why

The issue traces the bug to its root: the detector inspects a substring
of the whole log rather than the structured act it claims to detect, and
the substring it looks for is guaranteed present because we ourselves
inject it as a warning. Tuning the regex (narrower wording, negative
lookahead around the warning's phrasing) would still be a word match
racing against whatever wording future warnings/discussions happen to
use — the same class of fragility the user named as a standing priority
("false positives must be fixed structurally, not tuned"). Issue #994
already established the fix pattern for the sibling signal (3) in this
exact function: parse the log as structured JSONL and count the real
event (`tool_result`/`is_error` there, `tool_use`/`run_in_background`
here) instead of matching words that can appear anywhere, including in
our own injected prose. Reusing that pattern keeps the two signals
consistent and auditable the same way.

## What did not work

None.

## Upstream basis

- `f8c0294` (issue #994 phase-2, PR #1014): `_count_structural_denials` —
  the structural-parsing pattern this change replicates for signal 2
  (same JSONL line-by-line parse, same silent-skip-on-malformed-line
  tolerance, same "count the tool event, not the word" transition).
- Issue #2217 itself: names the precedent, the acceptance gate, and the
  five live sessions to re-run the detector against.

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).

## Acceptance evidence

Gate: `tests/test_watchdog_local_signals.py`.

```
$ python3 -m pytest tests/test_watchdog_local_signals.py -v
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_genuine_agent_run_in_background_tool_use_still_trips_signal PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_empty_workspace_set_yields_empty_verdicts_not_error PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_zero_commit_aged_session_signals_no_gh PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_fresh_log_no_anomalies_no_gh PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_dead_watcher_pid_signals_no_gh PASSED
tests/test_watchdog_local_signals.py::TestSignalCoverageNoRegression::test_watcher_missing_signal_derivable PASSED
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_stale_log_signals_silence_no_gh PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_count_structural_delegations_ignores_non_assistant_types PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_count_structural_delegations_counts_tool_use_run_in_background PASSED
tests/test_watchdog_local_signals.py::TestSignalCoverageNoRegression::test_every_inventoried_signal_type_still_derivable PASSED
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_dead_entry_with_pr_index_makes_zero_gh_calls PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_own_injected_warning_in_assistant_text_does_not_trigger PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_injected_directive_text_alone_yields_zero_anomalies PASSED
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_dead_entry_without_pr_index_makes_one_gh_call PASSED
tests/test_watchdog_local_signals.py::TestBackgroundDelegationStructural::test_genuine_bash_run_in_background_tool_use_still_trips_signal PASSED
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_pr_state_from_index_matches_open_or_merged_semantics PASSED
============================== 16 passed in 0.85s ==============================
```

SKIPPED: none.

Adjacent watchdog test files re-run for regressions (not part of the
gate, run as a sanity check since this touches `watchdog.py`):

```
$ python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py \
    tests/test_watchdog_heartbeat_noise.py tests/test_poll_watchdog_log.py -q
....................................
34 passed in 1.13s
```

SKIPPED: none.

Empty-state acceptance criterion ("a session log containing the injected
directive and nothing else ... must produce zero anomalies"): covered
live by
`TestBackgroundDelegationStructural.test_injected_directive_text_alone_yields_zero_anomalies`
(tests/test_watchdog_local_signals.py), which feeds `spawn._COMPLETION_PROSE`
(the actual injected warning text, verbatim) as the only log content and
asserts `watchdog_check_one` returns `[]`.

Provenance: executed-live — ran the fixed detector directly against the
real logs of the sessions the issue named, under
`/home/jwjung/.tokenmaxxxer/work/`, comparing the old regex
(reconstructed inline, since it's now deleted from the source) against
the new `spawn._count_structural_delegations`:

```
$ python3 - <<'EOF'
import re, sys
sys.path.insert(0, ".")
import spawn
OLD_RE = re.compile(r"run_in_background|백그라운드|delegate|background worker", re.IGNORECASE)
logs = [
    "on-the-record-issue-2204-implementation.session.20260824T222535.4130680.log",
    "on-the-record-issue-2204-execution-observation.session.20260824T232057.1632735.log",
    "on-the-record-issue-2204-conformance-review.session.20260824T232215.1632735.log",
    "on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log",
    "on-the-record-issue-2210-implementation.session.20260824T232302.1650855.log",
    "on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log",
    "on-the-record-issue-2215-implementation.session.20260824T233302.2032422.log",
]
for name in logs:
    text = open("/home/jwjung/.tokenmaxxxer/work/" + name, encoding="utf-8", errors="replace").read()
    before = bool(OLD_RE.search(text))
    after = spawn._count_structural_delegations(text) > 0
    print(f"{name:70s} BEFORE={before!s:5s} AFTER={after!s:5s}")
EOF

on-the-record-issue-2204-implementation.session.20260824T222535.4130680.log         BEFORE=True  AFTER=True
on-the-record-issue-2204-execution-observation.session.20260824T232057.1632735.log  BEFORE=True  AFTER=False
on-the-record-issue-2204-conformance-review.session.20260824T232215.1632735.log     BEFORE=True  AFTER=True
on-the-record-issue-2208-implementation.session.20260824T231045.1590418.log         BEFORE=True  AFTER=False
on-the-record-issue-2210-implementation.session.20260824T232302.1650855.log         BEFORE=True  AFTER=False
on-the-record-issue-2214-implementation.session.20260824T233348.2080038.log         BEFORE=True  AFTER=False
on-the-record-issue-2215-implementation.session.20260824T233302.2032422.log         BEFORE=True  AFTER=False
```

canonical: ran this script live against the logs listed
(/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-{2204,2208,2210,2214,2215}-*.session.*.log)
in this session; output pasted verbatim above, not summarized.

Before: all 7 logs false-positive, matching the issue's report. After: 5
of 7 flip to no-anomaly — those 5 sessions never issued a real
`run_in_background` tool call, only received the injected warning. The 2
that stay `True` are genuine: their `tool_use` blocks were inspected
directly (same script, filtering for `input.run_in_background is True`)
and each shows one real background delegation —
`on-the-record-issue-2204-implementation` ran a `Bash` call
(`{"command": "timeout 590 python3 -m pytest ...", "run_in_background":
true}`), and `on-the-record-issue-2204-conformance-review` ran an
`Agent` call (`{"description": "Warrant hunt after-proposal, stance 0",
"run_in_background": true}`). This satisfies the acceptance criterion's
second half on real data: the fix removes the false positives without
blinding the detector to the actual act.

## Skill verdicts

skill-verdict: implementation-blueprint — not-applicable: fix follows one existing, already-established structural-parsing pattern (issue #994's `_count_structural_denials`, events.py) with no open architecture decision to make.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion metric, accessor chain, or check-pipeline-ordering question in scope.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern-vs-direct-form decision; this is a regex-search-to-JSONL-parse substitution, not an abstraction choice.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data-structure/algorithm/perf-cliff decision in scope for this fix.
other mounted skills: not triggered
