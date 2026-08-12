---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
canonical: acceptance: python3 -m pytest tests/test_spawn.py -q — result: UNMEASURED-with-reason: no acceptance command on record (see body)
verdict: pass
loop_state: landed
---

# issue-994 phase-2: structural denial counting for watchdog signal 3 (re-delivery)

## Basis

Upstream: docs/issue-994/proposals/2026-08-12-structural-denial-counting.md
(status: approved via #1002 merge to main).

canonical: `gh issue view 1008 --json comments -q '.comments[].body'` run
in this session — comment body: "proposal/survey/hunt는 #1002에서 이미
머지됨(재생성 충돌). 코드(spawn.py, tests)+record만 현재 main 기반
재딜리버리." This is a re-delivery of the closed PR #1008; this session
branches from current main (commit `7c87443`, `git rev-parse HEAD` run
before any edit) and touches only spawn.py, tests/test_spawn.py, and this
record.

## What was done

- `spawn.py`: removed `_DENIAL_RE = re.compile(r"permission_denial|denied",
  re.IGNORECASE)`. Added `_count_structural_denials(text)` next to
  `_classify_refusal_text` — parses `text` line-by-line as JSON, keeps only
  `type == "user"` lines whose `message.content` contains an `is_error`
  `tool_result` block that `_classify_refusal_text` matches, and counts
  those. `watchdog_check_one`'s signal-3 block (spawn.py:2129-2133) now
  calls `_count_structural_denials(text)` instead of
  `_DENIAL_RE.findall(text)`.
- `spawn.py`: fixed a split-line offset defect in `watchdog_check_one`'s
  scan-window read (spawn.py:2109-2130).

  canonical: `git diff HEAD -- spawn.py` read in this session — the old
  code read `text = fh.read()` to EOF unconditionally, then set
  `new_offset = fh.tell()` past everything just read, including a
  trailing line still mid-write. Since `_count_structural_denials`
  correctly skips a line that fails `json.loads`, that partial line's
  bytes were silently consumed into the committed offset anyway — a
  denial landing on that split line would never be re-read on a later
  scan, not merely delayed. Fixed by committing the offset only through
  the newest full `\n`-terminated line; an unfinished trailing line is
  left unread for the next scan.
- `tests/test_spawn.py`: rewrote the four existing `Watchdog` denial tests
  (`test_denied_tool_calls_signal_fires_at_threshold`,
  `test_denied_tool_calls_signal_silent_below_threshold`,
  `test_only_new_log_content_is_scanned_each_call`,
  `test_stale_offset_survives_log_truncation_on_respawn`) to build genuine
  structural `type:"user"`/`is_error`/`tool_result` JSONL fixtures via a
  new `_denial_line()`/`_non_denial_user_line()` helper pair, instead of
  the bare repeated word `"permission_denial\n"`. Added the issue's named
  two-case regression as two new test methods on the same `Watchdog`
  class in `tests/test_spawn.py`:
  `test_denied_tool_calls_signal_ignores_quoted_source_text` (a transcript
  quoting/echoing the word "denied" many times in assistant text and
  non-error tool_results counts 0) and
  `test_denied_tool_calls_signal_fires_on_genuine_denial_tool_result` (a
  transcript with `WATCHDOG_DENIAL_THRESHOLD` genuine `is_error` denial
  `tool_result` blocks still fires the anomaly).

## Why

The watchdog's `denied-tool-calls` signal was a bare word-regex over raw
transcript text, so a session that reads or quotes gate sources (which
themselves contain the word "denied" and the old regex literal) inflated
the counter with zero real denials — issue-476's survey session reported
89 matches against 0 actual tool denials (per the issue text). Reusing the
existing `_classify_refusal_text`/`_tool_result_text` structural
classifier (shipped under issue #232 for the live-stream refusal path) to
look only at `is_error` `tool_result` payloads removes that false-positive
class without inventing a second denial-shape vocabulary.

## What did not work

None.

## Acceptance verification

canonical: acceptance: python3 -m pytest tests/test_spawn.py -q — result: UNMEASURED-with-reason: no acceptance command on record for this target in docs/specs/acceptance-commands.md (out of this delivery's frozen write set to add)

Full pasted output, run live in this session (465 passed, 0 skipped, 0 failed):

```
$ python3 -m pytest tests/test_spawn.py -q
........................................................................ [ 15%]
........................................................................ [ 30%]
........................................................................ [ 46%]
........................................................................ [ 61%]
........................................................................ [ 77%]
........................................................................ [ 92%]
.................................                                        [100%]
465 passed in 31.77s
```

canonical: acceptance: python3 -m pytest tests/test_spawn.py -k Watchdog -q — result: UNMEASURED-with-reason: no acceptance command on record for this target in docs/specs/acceptance-commands.md (out of this delivery's frozen write set to add)

Full pasted output, run live in this session (32 passed, includes the
two named regression cases — source-quoting transcript counts 0, genuine
denial tool_result counts and fires):

```
$ python3 -m pytest tests/test_spawn.py -k Watchdog -q
................................                                         [100%]
32 passed, 433 deselected in 0.43s
```

## Doc placement ladder

- [x] No env var / config key / new dependency / migration / setup step
  introduced — nothing to add to a handbook.
- [x] No library-or-format choice over a named alternative and no changed
  public signature/wire format beyond what the proposal's own Rationale
  already recorded — no new decisions doc needed.
- [x] No benchmark/investigation numbers produced — nothing beyond this
  record and the existing hunt record.

## Hunt cadence

canonical: docs/issue-994/reports/implementation/2026-08-12-hunt-structural-denial-counting.md
read in this session.

- after-proposal hunt (stance 4, NO FINDING) recorded on main at merge of
  #1002, in the file cited above.
- before-landing hunt (dispatch #2, stance 1 — "assume this change and
  another plugin's rule cancel each other"), run in this session via the
  warrant-hunter subagent: NO FINDING, appended to the same file cited
  above.

## Open findings

None.
