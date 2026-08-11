---
code_under_review:
  - on-the-record/hooks/spawn-allow-gate.sh
  - on-the-record/hooks/test_spawn_allow_gate.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #834

## Summary of work

Implemented the approved phase-1 design in
`docs/issue-834/proposals/strict-spawn-allow-validation.md`.

canonical: `on-the-record/hooks/spawn-allow-gate.sh` (this build's own
edit, read directly) — the command-shape block (previously: strip an
optional `cd DIR &&` prefix via `\S+`-bounded regex, then regex-search
only the remainder for shell operators) is replaced with a strict
tokenizer check, ported in shape from `merge-allow-gate.sh`'s issue #824
fix: reject the whole command outright, before any stripping, if a
backtick, `$(`, or a literal newline appears anywhere in it; otherwise
tokenize the full, unstripped command with `shlex.shlex(cmd, posix=True,
punctuation_chars=True)` (`whitespace_split = True`; a `ValueError` for
unbalanced quoting falls through the same fail-open way as before); the
token list must be exactly `[PYBIN, SPAWN_PATH, *tail]` or `["cd", DIR,
"&&", PYBIN, SPAWN_PATH, *tail]` (`PYBIN` in `("python3", "python")`,
`SPAWN_PATH` ending in `spawn.py`), with no token in `tail` (or `DIR` for
the `cd`-prefixed shape) composed entirely of shell operator characters
(`shlex`'s `punctuation_chars` plus `;`, added explicitly since
`punctuation_chars` itself omits it). Only after both checks pass does the
existing (unchanged) `SAG_CHECKOUT`-relative spawn-path resolution/
existence check run. The file's top-of-file comment block was updated to
describe the fixed check, mirroring how `merge-allow-gate.sh`'s comment
documents issue #824's fix.

canonical: `docs/specs/generated-paths.md` line 26 (read directly,
unmodified by this build) — already carries `spawn-allow-gate.sh | n/a |
reads/validates only, no write call`; this build's edit adds no new write
call (no `mkdir`/`open(...,"w")`/`write_text`/`shutil.copy`/`move`
anywhere in the new code), so that row stays correct as-is and the file is
not part of this build's `code_under_review`.

canonical: `on-the-record/hooks/test_spawn_allow_gate.py` (this build's
own edit, read directly) — all 12 pre-existing test functions
(`t_orchestrator_spawn_invocation_gets_allow` through
`t_kill_switch_suppresses_allow`, file lines 52-168) were kept byte-for-
byte unmodified; 6 new regression cases were appended (file lines
187-244): `t_cd_prefix_dollar_paren_substitution_in_dir_slot_is_unreached`
and `t_cd_prefix_backtick_substitution_in_dir_slot_is_unreached` (this
issue's exact reproduction — a substitution payload with no internal
whitespace hidden in the `cd` prefix's directory slot, both forms),
`t_chain_prepended_with_semicolon_is_unreached`,
`t_chain_appended_with_semicolon_is_unreached`,
`t_chain_appended_with_pipe_is_unreached` (parity with issue #824's own
regression set for the remaining chain directions/operators;
chain-appended `&&` was already covered by the pre-existing
`t_unquoted_chained_command_after_spawn_is_unreached`), and
`t_backslash_escaped_quote_payload_is_unreached`.

canonical: `on-the-record/hooks/test_merge_allow_gate.py` lines 196-207
(read directly) — that last new case's payload shape
(`python3 spawn.py review 42 \';evil;'X'`) mirrors
`t_backslash_escaped_quote_payload_is_not_allowed`, the case issue #824's
own after-proposal hunt record documented as desyncing a naive
quote-stripping regex; `shlex(posix=True)` must not repeat that desync.

derived: `python3 -m pytest on-the-record/hooks/test_spawn_allow_gate.py -q`
```
..................                                                       [100%]
18 passed in 0.71s
```

## Why

canonical: `docs/issue-834/reports/implementation/survey.md`'s "The
defect, read at its cited lines" section (read directly) — the shipped
hook's `cd DIR &&`-prefix strip ran before the operator search, and the
prefix's captured directory slot (`\S+`) was unbounded, so a
command-substitution payload with no internal whitespace placed there
(`cd $(id>/tmp/x) && python3 spawn.py ...`) was consumed by the strip and
vanished from what the operator search ever inspected, while bash itself
still evaluated the substitution before `spawn.py` ran — the hook then
granted `permissionDecision: allow` for the whole line, skipping the
harness's human-confirmation prompt for an attacker-controlled command.

## Upstream

Based on: `docs/issue-834/proposals/strict-spawn-allow-validation.md`
(phase-1 proposal, itself built on
`docs/issue-834/reports/implementation/survey.md`, which live-verified the
ported tokenizer's token stream for every existing and new payload shape
before the proposal was written), and
`on-the-record/hooks/merge-allow-gate.sh` lines 91-129 / `on-the-record/
hooks/test_merge_allow_gate.py` (issue #824's already-landed, already-hunt-
tested design, ported here in shape as instructed).

## What did not work

The proposal's `## How you'll know it worked` section expected
`python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` to report the
survey's baseline (1 pre-existing, unrelated failure —
`t_all_generators_recorded_and_disjoint`) plus the new regression cases,
with no other new failure. canonical: live pytest run pasted under
`## Acceptance` below, this session — the first live run instead showed a
second failure, `t_rulebook_version_is_recorded` in `tests/test_gates.py`
— not a regression from this build's code, the same dirty-working-tree
self-check artifact `docs/issue-824/reports/implementation.md` lines
198-213 already documented (`spawn.rulebook_version()`'s own `git status
--porcelain` check against this checkout reacting to this build's own
staged-but-uncommitted files, appending a `커밋안됨` marker). See
`## Acceptance` below for the pre-commit run and the post-commit re-run
that clears it.

## Hunt cadence

canonical: `docs/issue-834/reports/implementation/2026-08-11-hunt-strict-spawn-allow-validation.md`
"after-proposal — stance 0" section (read directly, written in phase 1,
before this build's code existed) — verdict NO FINDING; live-probed
unquoted/adjacent operators, process substitution in the `cd` DIR slot,
backslash-escaped and ANSI-C-quoted operators, and env-var indirection
against the design the proposal described, finding no shape where the
tokenize-then-check-operator-tokens approach grants `allow` while bash
still executes a second, attacker-controlled command.

canonical: same file's "before-landing — stance 1" section (read
directly, written this session against this build's actual diff) —
verdict FINDING, kind composition: see `## Open findings` below.

closed_checks:
- after-proposal hunt, stance 0: the design that section probed is what
  `on-the-record/hooks/spawn-allow-gate.sh` (this record's
  `code_under_review`) now implements; every regression payload named in
  that section's probes (chain operators, process substitution, quoted
  operators) has a corresponding passing test in
  `on-the-record/hooks/test_spawn_allow_gate.py`, in the passing run
  cited under `## Summary of work` above.

## Open findings

canonical: `docs/issue-834/reports/implementation/2026-08-11-hunt-strict-spawn-allow-validation.md`
"before-landing — stance 1" section (read directly, live-fire
reproduction included there) — `on-the-record/hooks/retry-loop-bound.sh`
(issue #507, a pre-existing, unrelated PreToolUse hook in the same Bash
matcher group) grants its own `permissionDecision: allow` for an exact
command string once any *other* gate has denied that identical string 5
times and then stops denying it (a state change, or a fail-open on that
other gate's own lookup failure) — the fatigue-allow never re-inspects
the command's shape or content. The hunt reproduced this live against
this build's own malicious payload
(`cd $(touch /tmp/pwned_poc)&&python3 spawn.py implementation "task"
--issue 834`): `spawn-allow-gate.sh`'s new strict check correctly gives
no allow signal for it, but after 5 simulated prior denials by an
unrelated gate, `retry-loop-bound.sh pre` on attempt 6 grants
`permissionDecision: allow` for the identical string anyway, keyed only
on the (tool, verbatim command) retry signature.

canonical: `docs/issue-824/reports/implementation.md` lines 152-171 (read
directly) — that record's own before-landing hunt found the same
composition-defect class (a generic, content-blind gate accidentally
supplying the `allow` signal a content-aware gate had just correctly
refused) against `impact-guard.sh`, a different file, opposite failure
direction (false deny there, false allow here), left as an out-of-scope
follow-up-issue candidate rather than fixed in that build. Left the same
way here — `on-the-record/hooks/retry-loop-bound.sh` is outside this
issue's frozen write set (`spawn-allow-gate.sh`, its test file, and this
record only).

next steps: file a follow-up GitHub issue against
`on-the-record/hooks/retry-loop-bound.sh`'s fatigue-allow, scoped to that
file only.

resolution path: have `retry-loop-bound.sh`'s fatigue-allow re-consult
(or at minimum, never override) the content-aware gates scoped to that
command shape before granting its own `allow`, instead of keying purely
on retry-count-for-an-identical-string plus whichever unrelated gate
denied it last.

## Acceptance

check 1 — the issue's own acceptance items (a command-substitution
payload hidden in the `cd`-prefix directory slot never gets `allow`, pure
and legitimate `cd`-prefixed forms unaffected; both chain directions,
`;`, `|`, and the backslash-escaped-quote payload also get no `allow`):
the passing test run cited under `## Summary of work` above covers both
`cd`-prefix substitution forms (`$(...)` and backtick), both chain
directions, `;`, `|`, the backslash-escaped-quote payload, and the
pure-form green cases (bare, `cd`-prefixed, `consult` subcommand,
sensitive-literal-in-task-text, single-quoted-operator-in-task-text).

check 2 — `main` restored to no *new* failure beyond the pre-existing,
out-of-scope baseline
(`python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`):

canonical: live pytest run, this session, fence immediately below, run
against this build's own uncommitted working tree (pre-commit) —

```
$ python3 -m pytest gates/ tests/ on-the-record/hooks/ -q
2 failed, 1214 passed, 2 skipped, 1 xfailed in 186.24s (0:03:06)
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_rulebook_version_is_recorded
```

`t_all_generators_recorded_and_disjoint` is the pre-existing,
`stop-poll-rearm.sh`-caused baseline failure the proposal already recorded
(survey's Baseline section) and this issue's own `## Out of scope`
excludes — unchanged by this build. `t_rulebook_version_is_recorded` (in
`tests/test_gates.py`) is the dirty-tree self-check artifact discussed in
`## What did not work` above; a post-commit re-run, expected to show only
the one pre-existing failure once this change is committed, is pasted in
a follow-up commit to this record, the same two-commit convention
`docs/issue-824/reports/implementation.md` used (`git log --oneline --
docs/issue-824/reports/implementation.md` shows commits `64c9ed0` then
`11a2f06`).
