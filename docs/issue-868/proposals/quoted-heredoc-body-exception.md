---
status: approved
files:
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
  - docs/issue-868/reports/implementation/survey.md
  - docs/issue-868/proposals/quoted-heredoc-body-exception.md
  - docs/issue-868/reports/implementation.md
---

## Request

`gh-write-allow-gate.sh` (#859) correctly refuses any command containing
`` ` ``/`$(`/newline, but that blanket refusal also denies the real shape
a session emits for a multi-line issue body:
`gh issue create --body "$(cat <<'EOF' ... EOF)"`. #859 is not a bug
(safely strict) — it is incomplete: it never learned the one benign
shape a real session needs. #868 asks for the gate to recognize that
specific shape without weakening the refusal of any other substitution.

## Constraints

- Never loosen the refusal of any `$(`/backtick shape other than exactly
  `$(cat <<'DELIM' ... DELIM)` / `$(cat <<"DELIM" ... DELIM)` (quoted
  delimiter only — unquoted `<<EOF` still expands its body and stays
  denied).
- The decision must still be keyed on command SHAPE, never argument
  text — the exception is a structural match, not a body-content scan.
- Role sessions must never get an auto-allow through this shape either
  (existing role-exclusion in the gate must still apply).
- Existing 24 tests in `test_gh_write_allow_gate.py` must keep passing
  unmodified.

## Rationale

Considered (b) alone — steer sessions via docs to `gh issue create
--body-file <path>` instead, which the gate already allows untouched
(no substitution). Rejected as the sole fix: it depends on the session
choosing that shape; #867's measured failure is a session that already
composed the heredoc shape, and (b) does nothing to unblock that
specific, already-observed command. #868 also requires the fix to work
"by default" for a fresh session, and a docs-only steer is not
mechanically enforced the way a gate change is.

Chose (a): teach the gate to recognize
`$(cat <<'DELIM' ... DELIM)` structurally. A QUOTED heredoc delimiter is
a POSIX shell primitive that disables all expansion of its body — the
substitution can only ever yield `cat`'s literal stdin, never execute
anything hidden, regardless of what the body contains. This is provably
safe by shell semantics, not by inspecting the body's content, so it
does not compromise the shape-only-never-content design #856 states
requirement (c) for. (b) stays available as a secondary path (the gate
already allows `--body-file` today, unaffected by this change) but is
not the mechanism relied upon here.

## What will be done

- In `gh-write-allow-gate.sh`'s embedded Python guard, before the
  existing `` "`" in cmd or "$(" in cmd or "\n" in cmd `` exclusion:
  detect exactly one regex match of the shape
  `$(cat <<'DELIM'\n...\nDELIM\n)` (delimiter quoted with `'` or `"`,
  `DELIM` a bare identifier) AND confirm `cmd.count("$(") == 1` and no
  backtick anywhere in `cmd` — i.e. this is the *only* substitution in
  the command. If matched, replace that span with a single inert
  placeholder token, then run the existing exclusion/tokenization/verb-
  shape checks unchanged on the rewritten command.
- Add tests to `test_gh_write_allow_gate.py`: the benign quoted-heredoc
  shape gets `allow`; the same shape under a role session still gets no
  signal; a double-quoted delimiter variant also gets `allow`; an
  UNQUOTED delimiter (`<<EOF`) does NOT get the exception and stays
  unreached; a second unrelated `$(rm -rf x)` alongside the heredoc
  shape stays denied; a plain `$(rm -rf x)` substitution (no heredoc)
  stays denied.
- Write the phase-2 record with a short safety rationale citing the
  quoted-heredoc non-expansion property and referencing `gh issue create
  --help`'s `--body-file` and the Claude Code PreToolUse hook contract.

## Out of scope

- Does not touch `merge-allow-gate.sh` or `spawn-allow-gate.sh` (#816,
  #823) — same three-part design, but not this issue's write set.
- Does not add a `--body-file` steering directive to any docs/handbook —
  approach (b) is not the chosen primary mechanism; no doc changes are
  needed for approach (a) alone.
- Does not re-run the on-the-record harness end-to-end (#868's step 2,
  execution-observation) — that is explicitly a separate acceptance
  step, not part of this gate-code change.

## How you'll know it worked

`python3 on-the-record/hooks/test_gh_write_allow_gate.py` passes with
the existing 24 tests plus the new ones (benign heredoc allowed, role
session still not allowed, dangerous substitution still denied) — 0
regressions, new tests green.
