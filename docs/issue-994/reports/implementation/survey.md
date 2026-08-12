kind: survey
subject: issue-994
code_under_review:
  - spawn.py

## Current state (read evidence)

`spawn.py:2012` (pre-change):
```
_DENIAL_RE = re.compile(r"permission_denial|denied", re.IGNORECASE)
```
Used at `spawn.py:2077` (pre-change line numbers) inside `watchdog_check_one` (spawn.py:2027) as signal 3:
```
new_denials = len(_DENIAL_RE.findall(text))
```
`text` is the raw scan-window slice of the session's stream-json transcript
log (`entry["log"]`), read verbatim between `start_offset` and EOF —
`_DENIAL_RE` runs over the whole raw text, including assistant prose and
any quoted file/tool content, not just structural events.

Issue #994's cited fact: issue-476's survey session showed
`denied-tool-calls: 89건` with 0 real denials — the session was reading/
quoting gate sources (which contain the literal word "denied" and this
very regex), and 100% of matches were quoted source/test strings, not
structural denial events.

## What already exists to build on

`spawn.py:2690-2772` (issue #232's tool-result-refusal classifier,
already shipped and tested) is the structural shape this issue asks to
reuse:
- `_tool_result_text(content)` (spawn.py:2716) — extracts text from a
  `tool_result` block's `content` (str or list-of-text-blocks).
- `_classify_refusal_text(text, command=None)` (spawn.py:2731) — matches
  `text` against `_GATE_HOOK_RE`/`_GATE_DENY_RE` (gate layer),
  `_HARNESS_REFUSAL_PATTERNS` (spawn.py:2698, harness layer), and
  `_SANDBOX_REFUSAL_PATTERNS` (spawn.py:2704, sandbox layer); returns
  `None` on no match, else `(event_type, dedup_key, detail)`.
- The live-stream consumer at `spawn.py:5603-5619` shows the shape a
  structural denial event actually has on the wire: a `type: "user"` line
  whose `message.content` contains a `tool_result` block with
  `is_error: true`, whose text (via `_tool_result_text`) is fed to
  `_classify_refusal_text`.

`watchdog_check_one` only has access to raw log text (a byte-offset
window), not the live `proc.stdout` iterator `spawn.py:5550` consumes —
so the fix must re-parse the scan-window text as JSONL (one `json.loads`
per line, skip malformed lines — same tolerance `spawn.py:5573-5575`
already uses for the live stream) rather than reuse the live-stream loop
directly.

## Tests already covering this signal

`tests/test_spawn.py`'s `Watchdog` class (`test_spawn.py:3503`) has four
tests keyed to the current `_DENIAL_RE` word-match behavior, all built on
`log.write_text("permission_denial\n" * N)` — a bare word repeated, not a
structural tool_result:
- `test_denied_tool_calls_signal_fires_at_threshold` (3540)
- `test_denied_tool_calls_signal_silent_below_threshold` (3547)
- `test_only_new_log_content_is_scanned_each_call` (3554)
- `test_stale_offset_survives_log_truncation_on_respawn` (3565)

These four must be rewritten to build genuine structural
`tool_result`/`is_error` JSONL lines (matching `_HARNESS_REFUSAL_PATTERNS`)
instead of the bare word, or they will fail against the fixed counter —
this is inherent to changing what counts as a denial, not scope creep.

## Write set implied

- `spawn.py` — replace `_DENIAL_RE` word-scan with a structural JSONL
  parse + `_classify_refusal_text` reuse.
- `tests/test_spawn.py` — rewrite the four existing denial tests to use
  structural fixtures, add the issue's two-case regression (quoted-source
  transcript counts 0; genuine denial tool_result counts >=1).

## Skip conditions checked

Scout (product-discovery sweep) skipped: this is a pure bugfix to an
existing internal counting bug, not a product-shaped surface with no field
to scout — the fix target, the shape to reuse, and the acceptance test
are all fully specified by the issue text and the existing `_classify_
refusal_text` implementation already in this codebase.
