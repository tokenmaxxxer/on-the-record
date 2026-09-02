---
issue: 3061
role: adversarial-review+test-depth-audit+silent-failure-audit-db36701b
author: adversarial-review+test-depth-audit+silent-failure-audit-db36701b
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # seventh independent verification of PR #3087's deliverable, this time of round 5's repair (PR #3204's record) closing PR #3201's three holes
code_under_review: 6f600355b5778817bda5a714c0b42c1673cb5c57
type: defect-verification-record
breaking: false
verdict: Round 5 closes none of its three holes cleanly (full reproductions
  and grades are in the body, each with its own derived: citation). Hole 1
  (compound command via wildcard) grades Surface. Hole 2 (malformed
  manifest UTF-8) grades Incorrect. Hole 3 (audit() truncated episodes)
  grades Incorrect. Regression attribution grades Present, re-derived at
  round 5's own tip. The three previously-Present properties (no lexical
  classifier, the four historical cases, action identity from tool_use
  arguments) are re-confirmed Present. See "What was done" below for the
  full per-hole evidence.
loop_state: verified
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3087 (code
      on its own branch through commit 6f600355, round 5's repair)
    sha: 6f600355b5778817bda5a714c0b42c1673cb5c57
  - path: docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-317d79e9.md (PR #3201, sixth independent verification — the round this repair responds to)
    sha: same-commit
  - path: docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-17eeb4c9.md (PR #3204, round 5's own repair record)
    sha: same-commit
---

# issue-3061 — adversarial-review+test-depth-audit+silent-failure-audit-db36701b record

## What was done

canonical: `6f600355:delegation_state.py` (round 5's tip, commits
`5a7e790c` fix + `6f600355` tests, on top of `1e27c69b`) and
`docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-317d79e9.md`
(PR #3201's sixth verification, read in full before this session's own
reproductions).

Seventh independent, builder-blind verification against issue #3061 — of
round 5's repair (PR #3204's record; two commits pushed directly onto PR
#3087's own branch: `5a7e790c` the fix, `6f600355` the regression tests,
on top of `1e27c69b`), which claims to close three holes PR #3201's
sixth independent verification found in round 4's scope-manifest lookup:
a wildcard manifest entry silently authorizing a newline/CR-separated
second command; a lone Unicode surrogate in a manifest field crashing
`grant()` uncaught at the disk-write step; and `audit()` flagging a
truncated/still-running session log's last episode as a clean avoidable
stop instead of reporting it indeterminate.

Every finding below was reproduced independently in an isolated `git
worktree` checkout of PR #3087's branch at `6f600355` (never edited,
never merged, removed at session end) via small, self-contained
reproduction scripts run directly against
`6f600355:delegation_state.py`'s public functions (`is_covered()`,
`grant()`, `audit()`, `format_audit()`) — not by reading the round-5 diff
and trusting its own test suite.

### Hole 1 (compound command via wildcard) — grade: Surface

canonical: `6f600355:delegation_state.py:493-511` (`_is_provably_single_command()`)

**Control-character shapes named in this round's task.**

derived: python3 reproduction against `is_covered()` with
`manifest=[{"tool":"Bash","resource":"git *","repo":"*"}]`, isolated
worktree at `6f600355` (this session, this turn) — result:
```
'git status\x00rm -rf /var/lib/postgres'                          -> covered=False (NUL)
'git status\rrm -rf /var/lib/postgres'                             -> covered=False (CR)
'git status\r\nrm -rf /var/lib/postgres'                           -> covered=False (CRLF)
'git status\x0crm -rf /var/lib/postgres'                           -> covered=False (form feed)
'git status\x0brm -rf /var/lib/postgres'                           -> covered=False (vertical tab)
'git status' + chr(0x2028) + 'rm -rf /var/lib/postgres'            -> covered=False (U+2028 line sep)
'git log' + chr(0x2029) + '--all'                                  -> covered=False (U+2029 para sep)
'git commit -m "line1\nline2"'                                     -> covered=False (newline inside a quoted arg)
```
No case slipped a compound-looking string past a wildcard entry.

derived: `python3 -m pytest test/test_delegation_state.py -q` inside the
isolated worktree at `6f600355` (this session, this turn) — result: full
suite passes, including round 4's already-covered compound shapes
(`&&`, `;`, pipe, subshell, heredoc, backgrounded) and the harmless
literal cases — none regressed.

**The over-refusal boundary (what the task asked to find).** The fix's
own docstring (`6f600355:delegation_state.py:505-511`) calls the false-
positive direction "rare." `_is_provably_single_command()` is a
presence-only check — `str.isprintable()` plus a small substring
blacklist — over the WHOLE resource string, with no awareness of
quoting: a legitimate single command whose own quoted argument contains
one of those characters is refused identically to a real chain.

derived: python3 reproduction, 20-command corpus of ordinary, non-
chained developer commands (git, ls, grep, find, python3, curl, npm,
sed, docker, rsync, gh, tar, ssh, awk, printf), each checked via
`is_covered()` against a wildcard entry matching its own tool prefix,
isolated worktree at `6f600355` (this session, this turn) — result:
```
matched: 16/20 (80%)
refused (over-refusal), 4/20 (20%):
  'git commit -m "fix: handle empty input\nfixes #123"'   (multi-line commit message)
  'git log --grep="foo|bar" --oneline'                     (regex alternation in a quoted arg)
  'curl -sS "https://example.com/api?x=1&y=2"'             (& in a quoted URL query string)
  'gh pr create --title "fix bug" --body "line1\nline2"'   (multi-line PR body)
```
20% over-refusal on an ordinary-usage sample is not the "rare" cost the
fix's own comment claims, and two of the four hits (multi-line commit/PR
messages) are common enough that this repo's own `hook-contract.md`
directive tells sessions to split a commit message across two `-m` flags
specifically because a single `-m` with an embedded `\n` is standard
practice elsewhere.

canonical: `6f600355:test/test_delegation_state.py` `ControlCharacterCompoundCoverageTest`
class — its only must-not-over-refuse cases are
`test_plain_git_command_still_covered` and
`test_exact_literal_compound_entry_still_matches_on_purpose`; neither
constructs a quoted operator character or an embedded newline inside
quoted data, so the round-5 suite does not exercise the failure mode
reproduced above.

**Grade rationale.** Surface, not Present: the specific defect PR #3201
named (control-character omission from the operator-token blacklist) is
genuinely fixed and the safety direction never fails open in this
session's testing. Not Incorrect: no compound command was found to
bypass the check. The gap is the undisclosed, untested regression cost —
round 5 fixed the omission PR #3201 found without addressing the over-
refusal direction that same report already flagged in the same finding.

### Hole 2 (malformed manifest, UTF-8) — grade: Incorrect

canonical: `6f600355:delegation_state.py:256-272` (`_validate_manifest_entry()`)
iterates exactly `("tool", "resource", "repo")` and returns `entry`
unchanged at line 272 — any other key in the dict, and its value, is
never checked and is written to disk as-is.

derived: python3 reproduction calling `grant()` in an isolated tmp dir,
isolated worktree at `6f600355` (this session, this turn) — result:
```
extra_field_value:  manifest=[{"tool":"Bash","resource":"git *","repo":"*","note":"context\ud800here"}]
  -> grant() raised UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' in position 307: surrogates not allowed
dict_key:           manifest=[{"tool":"Bash","resource":"git *","repo":"*","weird\ud800key":"value"}]
  -> grant() raised UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' in position 297: surrogates not allowed
nested_structure:   manifest=[{"tool":"Bash","resource":"git *","repo":"*","meta":{"inner":["deep\ud800value"]}}]
  -> grant() raised UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' in position 335: surrogates not allowed
```
All three are the identical uncaught `UnicodeEncodeError` at
`6f600355:delegation_state.py:221` (`path.write_text(...,
encoding="utf-8")`) that PR #3201 originally found for the three named
fields — round 5 closed that door for `tool`/`resource`/`repo` only.
This is realistic, not contrived: `6f600355:delegation_state.py:186-189`
and `6f600355:delegation_state.py:409-420` direct authors to hand-write
JSON manifests via `grant(..., manifest=[...])` directly for any
resource a `--allow` spec's colon grammar cannot express, inviting
exactly the kind of hand-authored dict where an extra note/typo'd key is
plausible.

**More severe than the original defect: this destroys prior good
state.** `Path.write_text()` opens the file in truncating write mode
before the encode error fires.

derived: python3 reproduction — (1) `grant()` a genuinely valid, in-
force delegation; (2) `grant()` again with a surrogate in an unnamed
field; (3) inspect the state file after the crash, isolated worktree at
`6f600355` (this session, this turn) — result:
```
1. state file before: 316 bytes, describe() reports "IN FORCE"
2. second grant() call -> raised UnicodeEncodeError (uncaught)
3. state file after the crash: EXISTS, 0 bytes
4. describe(): "delegation state file exists but is unreadable/corrupt
   ... treating as no standing delegation (fail-closed, not silently
   equated)"
```
`describe()`'s corruption detection correctly distinguishes "corrupt"
from "never granted" — that fail-closed direction holds — but the
operator's actual standing delegation is gone: an unrecoverable data
loss triggered by a field the fix's own commit message claims is
covered.

**Control confirming the named-field path genuinely works.**

derived: python3 reproduction — same two-step setup, but the surrogate
placed inside the named `resource` field instead, isolated worktree at
`6f600355` (this session, this turn) — result:
```
before bytes: 299
grant() raised MalformedManifestError (expected): manifest entry 0
  field 'resource' contains a character that cannot round-trip through
  UTF-8 encoding
after bytes (named-field surrogate case): 299
file unchanged: True
```
Zero disk mutation on rejection for a named field — the write-ordering
logic is correct where the field-name allowlist actually covers it.

**Grade rationale.** Incorrect: the round-5 commit message's claim
("UTF-8 round-trip validation to every string field a manifest entry can
hold") is falsified by the three reproductions above, the crash is the
identical uncaught exception class the round was supposed to close, and
the consequence is now worse than the original bug — data loss on top of
the crash, not merely an unresolved crash.

### Hole 3 (audit() truncated episodes) — grade: Incorrect

canonical: `6f600355:delegation_state.py:746-751` — `log_reached_completion
= trajectory_analyzer.final_result_event(events) is not None` is
computed once per log file, before the per-episode loop, and reused for
every boundary-at-EOF episode in that log.

derived: python3 reproduction building synthetic stream-json session
logs by hand and calling `audit()` against a repo with one in-force
delegation covering `Bash:"git *"`, isolated worktree at `6f600355`
(this session, this turn) — result:
```
no final-result event at all                        -> flagged=0, indeterminate=1
truncated final line (partial JSON, mid-write)       -> flagged=0, indeterminate=1
clean EOF at event boundary, no result event         -> flagged=0, indeterminate=1
genuinely complete single episode (control)          -> flagged=1, indeterminate=0
```
All three broken single-episode-per-log shapes are correctly reported
indeterminate, never flagged, never silently folded into "not flagged" —
`format_audit()` names them explicitly. The control confirms the fix has
not made `audit()` useless: a genuinely complete episode is still
flagged cleanly.

**Where it breaks: completion evidence is not scoped to the boundary
episode.** `final_result_event()` returns the LAST `result`-typed event
anywhere in the events list — if an EARLIER episode in the same log
genuinely completed and a LATER episode is the one actually truncated,
the earlier episode's own result event satisfies the whole-log check and
incorrectly vouches for the later, cut-off episode too.

derived: python3 reproduction, log = `[ask1, tool_use1(covered), result1
(episode 1 genuinely completes), ask2, tool_use2(covered)]` — truncated
here, no result2 — calling `audit()`, isolated worktree at `6f600355`
(this session, this turn) — result:
```
scanned_logs=1, flagged=2, indeterminate=0
```
Episode 2 — the actually-truncated one — was FLAGGED, not indeterminate.

derived: python3 reproduction, extended to three episodes: ep1 completes
(result1), ep2 completes (result2), ep3 truncated with no result3,
calling `audit()`, isolated worktree at `6f600355` (this session, this
turn) — result:
```
scanned_logs=1, flagged=3, indeterminate=0
```
Episode 3, truncated, still FLAGGED — two prior genuine completions in
the same log make the misclassification worse, not better.

derived: python3 reproduction, control — two full episodes, BOTH with
their own genuine result event, no truncation, calling `audit()`,
isolated worktree at `6f600355` (this session, this turn) — result:
```
scanned_logs=1, flagged=2, indeterminate=0
```
This control shows the mechanism is not broken in general — when every
episode genuinely gets its own result event, both are correctly flagged.
The defect is specifically that "did the file reach a result event
anywhere" cannot distinguish that from "did THIS episode's own tail
reach one," and a multi-episode log — several ask/act cycles before the
log gets cut — is the ordinary shape a real session log takes over time,
not a contrived construction.

**Grade rationale.** Incorrect: `6f600355:delegation_state.py:717-739`'s
own docstring claims a truncated episode "is reported INDETERMINATE,
never flagged, regardless of whether the visible portion happens to look
fully covered" — that does not hold once a log contains more than one
episode boundary. This reproduces the identical silent-failure shape (a
truncated stop reported as a clean, avoidable escalation) that hole 3
was scoped to close, one level up from where PR #3201 found it.

### Regression attribution — grade: Present

derived: `python3 -m pytest -q -m "not slow"` inside an isolated
worktree at `1e27c69b` (round 4's tip), this session, this turn —
result: `22 failed, 1032 passed, 3 xfailed, 2 warnings`

derived: `python3 -m pytest -q -m "not slow"` inside an isolated
worktree at `6f600355` (round 5's tip), this session, this turn —
result: `22 failed, 1032 passed, 3 xfailed, 2 warnings`

derived: `diff` of the two independently captured, sorted `FAILED` line
sets, this session, this turn — result: no output (identical), 22 lines
in each file

Round 5's two commits (`5a7e790c`, `6f600355`) introduce zero new
failures and fix none of the pre-existing ones, matching PR #3201's own
independently-derived count and the same diff-of-sorted-name-sets
methodology.

### Three previously-Present properties — re-confirmed independently, grade: Present

derived: `grep -n "_is_redundant_ask\|_REDUNDANT_ASK"
delegation_state.py` inside the isolated worktree at `6f600355`, this
session, this turn — result: matches only historical-context prose
inside comments/docstrings; no function by that name or shape exists.
`is_covered()` (`6f600355:delegation_state.py:518`) is the sole
classifier — set-membership over `{tool, resource}`, not text inference.

canonical: `6f600355:test/test_delegation_state.py:339` still carries
"The four real historical misclassifications, one per independent
[verification]" with PR #3107/#3122 citations.

derived: `python3 -m pytest test/test_delegation_state.py -q` inside the
isolated worktree at `6f600355`, this session, this turn — result: full
suite passes, including the four-historical-case class above.

canonical: `6f600355:delegation_state.py:581-602` (`_extract_action()`)
reads `tool_use.get("input")`'s own fields (`command`/`file_path`/
`path`/`url`/`description`) — never the ask's own text — unchanged from
round 4 and exercised by the passing suite above.

## Why

canonical: PR #3201's record
(`docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-317d79e9.md`)
and PR #3204's round 5 record
(`docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-17eeb4c9.md`),
both read in full before this session's own reproductions.

Builder-blind, structurally independent verification (adversarial-review
skill): read only round 5's diff and its own claims, then constructed
inputs round 5's test suite does not contain, run directly against the
delivered code in an isolated checkout, rather than trusting the passing
suite as proof of the claimed properties. Each of the three holes was
graded from an actual reproduction against
`6f600355:delegation_state.py`'s public functions, not from re-reading
the commit message's own account of what it fixed — the same standard
the prior six verification rounds in this issue's history have applied,
since a builder session grading its own diff has repeatedly (rounds 1-5)
missed exactly this class of gap.

## Upstream basis

- PR #3087 (`https://github.com/tokenmaxxxer/on-the-record/pull/3087`),
  code at `6f600355b5778817bda5a714c0b42c1673cb5c57` (round 5's tip:
  `5a7e790c` the fix, `6f600355` the regression tests, on top of
  `1e27c69b`).
- `docs/issue-3061/reports/adversarial-review+test-depth-audit+silent-failure-audit-317d79e9.md`
  (PR #3201, sixth independent verification, the round this repair
  responds to) — `same-commit`.
- `docs/issue-3061/reports/implementation-blueprint+silent-failure-audit+test-derivation-17eeb4c9.md`
  (PR #3204, round 5's own repair record) — `same-commit`.

## Open findings

canonical: reproductions above, this session, this turn —
`6f600355:delegation_state.py:256-272` (hole 2 field allowlist) and
`6f600355:delegation_state.py:746-751` (hole 3 whole-log completion
check) are the two code locations these resolution paths change.

- Hole 1 over-refusal cost (Surface). resolution path: either build a
  real shell tokenizer that understands quoting (the module's own
  docstring already rejected this path for the compound-detection
  problem, for good reason, so the same argument likely applies here) or
  explicitly, honestly quantify and test the cost instead of the current
  "rare" claim. Not fixed by this session — verification-only scope, no
  edits to PR #3087.
- Hole 2 (Incorrect). resolution path: either UTF-8-validate every
  string value recursively across the whole manifest entry dict
  regardless of key name, or reject any manifest entry key outside the
  three named fields at validation time (closed schema); and separately,
  `grant()` should validate before ever opening the destination file for
  writing (e.g. write to a temp file and rename), so a crash on the
  write path cannot destroy prior good state even for a defect this
  validation function does not yet catch. Not fixed by this session.
- Hole 3 (Incorrect). resolution path: scope `log_reached_completion`
  per-episode, not per-log — an episode should only be treated as having
  reached its own end if a `result` event exists after that specific
  episode's own last tool_use event, not merely anywhere in the file.
  Not fixed by this session.
- None of the above were edited in PR #3087; this record is
  verification-only, per the task's explicit instruction not to edit the
  subject PR. resolution path for all three: a subsequent repair round
  on PR #3087, re-checked by an eighth independent verification against
  fresh, independently-constructed inputs rather than this round's own
  citations.

## Next steps

None from this session — verification-only, loop_state set to `verified`
as the terminal state for this record kind.

canonical: this session's own Skill tool invocations (transcript, this
turn) for `adversarial-review`, `silent-failure-audit`, and
`test-depth-audit` — the three skill-verdict lines below report where
each was applied, per each skill's own body above.

skill-verdict: adversarial-review — applied: invoked; used to structure this whole session as a builder-blind, no-shared-context evaluation of PR #3087's round-5 diff, incentivized to find everything wrong with it rather than confirm its own claims
skill-verdict: silent-failure-audit — applied: invoked; used to drive the hole-2 (grant() crash path, error handling around disk writes) and hole-3 (audit()'s truncated-log handling) investigations specifically as error/failure-path audits, not just functional tests
skill-verdict: test-depth-audit — applied: invoked; used to assess round 5's own added tests (`ControlCharacterCompoundCoverageTest`, `MalformedManifestTest`'s surrogate cases, `TruncatedLogIndeterminateTest`) and find they are Happy-Path-Only relative to the must-not-over-refuse and multi-episode-log directions — real assertions, but missing exactly the adversarial cases this session constructed
