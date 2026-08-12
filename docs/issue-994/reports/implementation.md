---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
canonical: python3 -m pytest tests/test_spawn.py -q run this session, 462 passed
verdict: pass
loop_state: landed
---

# issue-994 phase-2: structural denial counting

## What was done

Replaced the watchdog's bare word-regex denial signal with a structural
JSONL parse, per the approved proposal
(docs/issue-994/proposals/2026-08-12-structural-denial-counting.md,
approved via `APPROVE issue-994/implementation` on issue #994).

- `spawn.py`: removed `_DENIAL_RE = re.compile(r"permission_denial|denied", re.IGNORECASE)`.
  Added `_count_structural_denials(text)` next to `_classify_refusal_text`
  (spawn.py:2027-2056): parses the watchdog's scanned log-text slice
  line-by-line as JSON, skips malformed/partial lines, filters to
  `type == "user"` messages whose `message.content` contains a
  `tool_result` block with `is_error: true`, extracts the block text via
  the existing `_tool_result_text`, and counts it only when
  `_classify_refusal_text` (issue #232's classifier) matches a known
  denial shape (gate/harness/sandbox). `watchdog_check_one`'s signal-3
  block now calls `_count_structural_denials(text)` instead of
  `_DENIAL_RE.findall(text)`.
- `spawn.py`: also touched the `watchdog_check_one` offset block, per
  `## Resolved findings` below.
- `tests/test_spawn.py`: rewrote the four existing `Watchdog` denial
  tests to build genuine structural `tool_result`/`is_error` JSONL
  fixtures via a new `_denial_line()` helper, instead of the bare
  repeated word. Added the issue's two-case regression:
  `test_denied_tool_calls_signal_ignores_quoted_gate_source_text` and
  `test_denied_tool_calls_signal_fires_on_genuine_tool_result_denial`.

canonical: this session's own run, `python3 -m pytest tests/test_spawn.py -q`:
```
462 passed in 33.40s
```

## Why

spawn.py:2012's `_DENIAL_RE` matched the word "denied" anywhere in the
raw transcript scan window, including a session's own assistant text
when it reads or quotes gate sources (which contain the word "denied"
and the regex literal itself). issue-476's survey session measured 89
reported denials vs 0 actual, 100% quoted-source matches. Since the
sandbox is abolished (full-open policy), real permission denials are
now rare, so word-occurrence counting produces almost pure noise
exactly when a session does the desired read-the-source discipline.
Parsing the transcript as JSONL and counting only `tool_result` blocks
that are both `is_error: true` and classify as a real denial shape
(reusing issue #232's `_classify_refusal_text`) ties the signal to an
actual structural event instead of incidental word occurrence.

## Upstream

Basis: docs/issue-994/proposals/2026-08-12-structural-denial-counting.md
(approved), issue #994.

Proposal: docs/issue-994/proposals/2026-08-12-structural-denial-counting.md

## Doc-placement ladder

- [x] No new env var / config key / dependency / migration / setup step
      introduced.
- [x] No new library-or-format choice beyond what the proposal's own
      Rationale already recorded — no decision record warranted.
- [x] No public signature/wire format changed (internal watchdog helper
      only).
- [x] No benchmark/investigation numbers beyond the pytest run cited
      above.

## What did not work

None.

## Resolved findings

canonical: docs/issue-994/reports/implementation/2026-08-12-hunt-structural-denial-counting.md,
lines 47-97 (before-landing warrant hunt, stance 0, read this turn).
The hunter reproduced a defect: a denial JSONL line split across two log
flushes, with a watchdog scan landing between them, was silently
dropped forever because `watchdog_check_one` advanced `offset` to
`fh.tell()` past a truncated trailing line, and
`_count_structural_denials` silently skips a `json.loads` failure.

resolved_findings: fixed in this same commit — `watchdog_check_one`'s
offset block (spawn.py, the block reading `log_path`) now rewinds
`new_offset` to the start of any trailing line not yet terminated by a
newline.

canonical: this session's own re-run of the hunt record's repro script
against the fixed code, executed live this turn:
```
[]
offset1 0
[]
offset2 177
>>> spawn._count_structural_denials(line)
1
```
Denial count: 0 on the partial-write scan, 1 on the follow-up scan —
previously it was 0 on both.

## Open findings

None.

canonical: this session's own run, `python3 -m pytest tests/test_spawn.py -q`
(see fenced output in `## Closed checks` below)

## Closed checks

canonical: this session's own run, `python3 -m pytest tests/test_spawn.py -q`,
re-run after the split-line fix above:
```
462 passed in 33.40s
```
closed_checks: full `tests/test_spawn.py` suite re-run against
`code_under_review:` above.
