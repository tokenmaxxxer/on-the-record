# Survey — issue #534

Scout skip: pure infra/observability fix inside an existing internal tool
(spawn.py); no product-shaped design decision or external category to
benchmark against. The design space is bounded by spawn.py's own existing
patterns (marker-based idempotent comments, roster/events files, CLI
verbs), which the current-state survey below covers directly — this is the
"scout the best of their own deliverable's kind" carve-out for non-product
roles, satisfied by reading spawn.py's own prior features (#488, #484,
#325) rather than external sources.

## Write set (expected)

- `spawn.py` — new comment marker + poster for session-end (normal
  completion / no-PR outcome and PR-opened outcome), wired into
  `_auto_respawn_check()` (or a new call site if that function's contract
  is kept respawn-only); new `--unreported` sweep mode for
  `roster_reconcile()` / `spawn.py reconcile`.
- `test_spawn.py` — unit tests for the new comment poster (idempotent,
  event-path driven, no live `gh` calls, following the existing
  `_post_stall_comment`/`_post_crash_comment` test pattern) and for the
  `--unreported` sweep (synthetic ended-session-with-open-PR fixture).
- `on-the-record/commands/run.md` — add a session-start/compaction-recovery
  step: first act is the reconcile sweep, not memory.
- Design-decision note for the chosen PR-open signal and its failure mode
  (per the issue's "empty state" acceptance line), placed per the doctrine
  ladder during phase-2 build.

## Current architecture (from Explore agent findings, file:line cited)

- `session_end_verdict()` (spawn.py:1456) classifies a dead roster entry as
  `normal` / `crashed` / `stalled` / `in-progress` from roster + log mtime +
  events — already persistent-state-derived, not LLM memory.
- `reconcile(expected, observed)` (spawn.py:1557) is a pure diff function;
  today it only recognizes two divergence kinds (`crashed`->respawn,
  `stalled`->resume-watch). `normal` completion and PR-opened are not
  divergence kinds at all — reconcile() has nothing to say about them.
- `roster_watchdog()` (spawn.py:1905) ticks over the roster, calling
  `reconcile()` (1940) and `_auto_respawn_check()` (1948) when
  `auto_respawn` is set.
- `_auto_respawn_check()` (spawn.py:2313-2348): for `verdict == "stalled"`
  it posts a comment via `_post_stall_comment()` (2201) and returns; for
  `"crashed"` it proceeds to `_respawn_or_cap()` (2289, which itself calls
  `_post_crash_comment()` at 2173 when respawn attempts are exhausted); for
  `"normal"` or `"in-progress"` it returns silently at line 2330-2331. **No
  comment is ever posted for a normal session-end or a PR-opened
  outcome.** This is the exact gap #534 targets.
- Comment posting is idempotent via `_issue_comments()` (spawn.py:1070) —
  read existing issue comments, check for a marker string
  (`_CRASH_COMMENT_MARKER` / `_STALL_COMMENT_MARKER`, 2157-2158), skip if
  already posted. `_post_stranded_push_comment()` (2227) follows the same
  pattern for push/PR-create failures (#326).
- `roster_reconcile()` (spawn.py:1964, CLI verb `spawn.py reconcile
  [--issue N]`, dispatched 3043-3044) already exists as a sweep, but only
  re-runs `reconcile()`'s two divergence kinds. No `--unreported` flag
  exists anywhere (grep confirmed empty).
- `_pr_open_or_merged_for_branch()` (spawn.py:1049) is the existing
  PR-state helper, fixed by #484 to use PR open-or-merged (not `--state
  all`) as the delivery signal — this is the signal to reuse for PR-open
  detection rather than inventing a new one.
- `docs/issue-488/proposals/2026-08-08-global-watch-all.md`: added `spawn.py
  watch --all`, explicitly out-of-scope'd "a durable notification stream
  beyond stdout printing" — direct ancestor gap.
- #484's proposal doc fixed the watch registration race and outcome
  mislabeling (PR open-or-merged as delivery signal, per above); it did not
  add durable posting for normal/PR-opened outcomes.
- `on-the-record/commands/run.md` (526 lines): "하지 않는 것" section
  (502-527) has the orchestrator self-drive `spawn.py watchdog` from LLM
  turn-by-turn attention — no session-start/compaction-recovery step exists
  today calling `reconcile`/`watchdog`/`watch --all` on resume.
- Tests: `test_spawn.py` (6334 lines), idempotent-comment test pattern
  around 4317-4584 — monkeypatch `spawn._issue_comments` to a lambda
  returning `(comments, ok)`, assert on marker presence / call count, no
  real `gh` calls. This convention is what the new tests will follow.
- Issue #533 (roster key collision) has no trace in this checkout
  (`grep 533 spawn.py` empty) — not yet landed, no dependency here.

## Design decision surfaced (drives proposal Rationale)

Where to post the session-end comment from:
1. **Extend `_auto_respawn_check()`** to also handle `normal`/`in-progress`
   by posting a comment (with PR-open lookup) — reuses the existing
   watchdog tick and idempotent-comment machinery directly, minimal new
   surface.
2. **New standalone function** called from `roster_watchdog()` alongside
   `_auto_respawn_check()`, keeping `_auto_respawn_check()`'s docstring
   contract ("respawn-only decision") intact.

Both are plausible; the current docstring at spawn.py:2313-2318 explicitly
states `_auto_respawn_check()`'s contract is respawn-decision, and folding
an unrelated reporting concern into it would violate that stated contract
and make the function's own docstring wrong the moment it's edited.
