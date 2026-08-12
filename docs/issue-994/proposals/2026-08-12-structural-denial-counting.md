---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

The watchdog's "denied-tool-calls" anomaly signal (`spawn.py:2012`'s
`_DENIAL_RE`) is a bare word-regex (`permission_denial|denied`) run over
the raw transcript scan window. A session that reads or quotes gate
sources — which themselves contain the word "denied" and this very
regex — inflates the counter even with zero real denials (issue-476's
survey session: 89 reported vs 0 actual, 100% quoted-source matches).
Fix it to count only structural denial events — a `tool_result` block
with `is_error: true` whose text matches the known denial shapes — never
a word occurring anywhere in assistant or file text.

## Constraints

- Reuse the existing tool-result-refusal classifier (`_classify_refusal_
  text`, `_tool_result_text`, `_HARNESS_REFUSAL_PATTERNS`/`_SANDBOX_
  REFUSAL_PATTERNS`/gate-hook regexes at `spawn.py:2690-2772`, shipped
  under issue #232) rather than inventing a second denial-shape
  vocabulary.
- `watchdog_check_one` only sees a raw text slice of the log (byte-offset
  windowed), not the live `proc.stdout` line iterator — the fix parses
  that slice as JSONL itself; it cannot call into the live-stream loop.
- Preserve observe-only tolerance: a malformed/partial JSON line in the
  scan window (mid-write truncation, same as the live stream already
  tolerates at `spawn.py:5573-5575`) is skipped, not fatal.
- Two-case regression required by the issue: a transcript quoting gate
  sources containing "denied" N times counts 0; a genuine denial
  tool_result counts >=1.

## Rationale

Chosen approach: parse the scan-window text line-by-line as JSONL inside
`watchdog_check_one`, and for each `type: "user"` line's `tool_result`
blocks with `is_error: true`, run `_classify_refusal_text` on the
extracted text; count only lines that classify as an actual denial shape.

Alternative considered and rejected: extend `_DENIAL_RE` with negative
lookaround to exclude quoted/code-block contexts (e.g. skip matches
inside triple-backtick fences or lines starting with a quote marker).
Rejected because it is a heuristic patch on top of a fundamentally wrong
signal — the transcript log is JSONL, not free prose, and any text-only
heuristic can be defeated by a session quoting a real (non-fenced) tool
result verbatim, or by a fenced denial that legitimately did happen. The
structural parse is not more complex than a correct negative-lookaround
regex would be, and it's the shape issue #232's classifier was already
built and tested for.

## What will be done

- `spawn.py`: remove `_DENIAL_RE`; add `_count_structural_denials(text)`
  next to `_classify_refusal_text`, parsing `text` line-by-line as JSON,
  filtering to `type == "user"` lines whose `message.content` contains an
  `is_error` `tool_result` block that `_classify_refusal_text` matches;
  `watchdog_check_one`'s signal-3 block calls this instead of
  `_DENIAL_RE.findall`.
- `tests/test_spawn.py`: rewrite the four existing `Watchdog` denial
  tests (`test_denied_tool_calls_signal_fires_at_threshold`,
  `test_denied_tool_calls_signal_silent_below_threshold`,
  `test_only_new_log_content_is_scanned_each_call`,
  `test_stale_offset_survives_log_truncation_on_respawn`) to build
  genuine structural `tool_result`/`is_error` JSONL fixtures instead of
  the bare repeated word; add the issue's two named regression cases
  (source-quoting transcript -> 0; genuine denial tool_result -> counted).
- `docs/issue-994/reports/implementation.md`: phase-2 delivery record.

## Out of scope

- Changing the other three watchdog signals (silence, delegation-phrasing,
  no-commits-late) or signal 5 (dead watcher) — untouched by this issue.
- Changing `_classify_refusal_text`'s own matching rules or adding new
  denial-shape patterns — this issue is about where counting looks, not
  what counts as a denial shape.
- Any change to the live-stream refusal correlation path
  (`spawn.py:5502-5619`, issue #232/#246/#558) — that path is already
  structural and out of scope.

## How you'll know it worked

- `tests/test_spawn.py::Watchdog`'s rewritten and new tests pass,
  including the two-case regression: a transcript quoting gate sources
  containing "denied" N times (N >= `WATCHDOG_DENIAL_THRESHOLD`) reports
  no `denied-tool-calls` anomaly; a transcript with a genuine `is_error`
  denial `tool_result` reports the anomaly once threshold is met.
- Reading `spawn.py` itself (which contains the word "denied" many times
  in comments/regex literals) as a session's own transcript no longer
  raises a false `denied-tool-calls` anomaly.

## Accumulation

Not accumulation-shaped: this is a single named-function fix
(`_count_structural_denials` in `watchdog_check_one`'s signal-3 block)
plus its own dedicated test rewrite, not an inline subprocess/gh call
being added alongside N existing look-alikes, and not a per-file repeated
one-line edit across a `roles/*.json`-style fan-out. There is exactly one
call site (`watchdog_check_one`, `spawn.py`) and one test class
(`Watchdog`, `tests/test_spawn.py`) touched; N more watchdog-signal fixes
arriving later would each add their own named helper and test class in
the same two files, not grow this one.
