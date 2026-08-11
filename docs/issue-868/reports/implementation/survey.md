# issue-868 current-state survey

Skip condition: N/A — scouting for this change is skipped under the scout
directive's second condition ("the spec leaves no design decision open"):
issue #868 already names and grounds the two candidate approaches (a)/(b)
in the security reasoning required to choose between them (quoted-heredoc
non-expansion is a shell primitive, not a product-taste decision), and
requires referencing official `gh`/Claude Code hooks docs rather than
scouting comparable products. The open work is a security-shape
implementation, not a design/product choice.

canonical: on-the-record/hooks/gh-write-allow-gate.sh (pre-change, full file read)
## Write set found

- `on-the-record/hooks/gh-write-allow-gate.sh` — the gate itself
  (issue #856/#859). canonical: on-the-record/hooks/gh-write-allow-gate.sh:85-86
  (pre-change) reads:
  ```
  if "`" in cmd or "$(" in cmd or "\n" in cmd:
      sys.exit(0)  # no legitimate invocation needs substitution or a newline
  ```
  This is the file that must learn the one benign exception.
- `on-the-record/hooks/test_gh_write_allow_gate.py` — the existing test
  suite. canonical: on-the-record/hooks/test_gh_write_allow_gate.py:1-213
  (pre-change) already covers: five verb shapes, `cd &&` prefix,
  role-session non-allow, sensitive literal in `--body` not flipping the
  decision, chained/piped commands unreached, backtick/`$(` substitution
  unreached, single-quoted operators in body not tripping the chain
  check, non-gh commands untouched, `gh pr merge` not matched, kill
  switch, and deny-gate-still-wins composition.
  derived: `git stash && python3 on-the-record/hooks/test_gh_write_allow_gate.py; git stash pop` (pre-change run)
  ```
  18 passed
  ```
  New tests for #868 belong in this same file (mirrors its own stated
  convention).
- No other file references `gh-write-allow-gate.sh`'s substitution
  exclusion. derived: `grep -rln "gh-write-allow-gate" --include=*.md --include=*.sh .`
  ```
  ./on-the-record/hooks/gh-write-allow-gate.sh
  ./docs/issue-856/proposals/gh-write-allow-gate.md
  ```
  The doc hit is a landed phase-1 proposal, not live behavior — out of
  scope for this write set.

canonical: on-the-record/hooks/gh-write-allow-gate.sh:85-86 (pre-change) + PR #867 record, finding 4
## Root cause confirmed

That line (quoted above) is a blanket exclusion — any `$(` anywhere,
including inside a provably-inert quoted heredoc, exits with no allow
signal. PR #867's record (finding 4) traces the failure this produces: a
fresh orchestrator session composes
`gh issue create --title "..." --body "$(cat <<'EOF' ... EOF)"` for a
multi-line body, and this line denies it, so `gh issue create` never
returns an allow, issue creation stays denied by the host classifier
default, and delegation is never attempted.

## Security grounding for approach (a)

A heredoc's delimiter can be quoted (`<<'EOF'`, `<<"EOF"`) or unquoted
(`<<EOF`). POSIX shell semantics (documented behavior, not a claim
requiring live scouting): quoting *any part* of the delimiter suppresses
parameter/command substitution and quote removal on the heredoc body —
the body is passed to the command's stdin completely literally, no
matter what characters it contains. This is exactly why
`--body "$(cat <<'EOF' ... EOF)"` is the idiomatic multi-line-body shape:
the heredoc's job is to get literal text (which may itself contain `$(`,
backticks, or anything else as inert text) into the body argument
without executing any of it. An UNQUOTED delimiter (`<<EOF`) does NOT
have this property — its body undergoes normal expansion — so it stays
outside the allowed shape.

Reference: `gh issue create --help` documents `--body-file <file>` (read
body from a file or stdin via `-`) as the alternative that needs no
substitution at all — the existing gate already allows that shape
untouched, since it carries no `$(`/backtick/newline. Approach (b) (steer
sessions to `--body-file`) is available but does not, by itself, fix a
session that has already composed the heredoc shape; approach (a) fixes
the gate to recognize the shape actually observed in the field (PR #867).

Claude Code hooks reference (PreToolUse `hookSpecificOutput.
permissionDecision`): unchanged by this issue — the exception adds no
new hook event or output field, only a pre-check inside the existing
Python guard before the current substitution-exclusion line runs.

## Decision

Implement (a): recognize the single benign shape
`$(cat <<'DELIM' ... DELIM<newline>)` (delimiter quoted with either `'`
or `"`) as a structural exception, collapse it to an inert placeholder
token before the rest of the shape/tokenization checks run, and keep
every other `` ` ``/`$(`/newline shape denied exactly as before —
including a second, unrelated `$(` anywhere else in the same command,
and an unquoted-delimiter heredoc.
