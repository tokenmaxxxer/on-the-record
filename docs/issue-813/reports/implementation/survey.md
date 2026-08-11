# Current-state survey — issue #813

## Skip condition

Pure bugfix; the requirement is fully specified in the issue text
(classify by invoked verb, not by merge-verb substrings inside a quoted
argument body). No design decision is open. Scouting skipped per the
scout-directive's first skip condition — recorded here per its mandatory
skip-record rule.

## Write set surveyed

- `on-the-record/hooks/impact-guard.sh` — the PreToolUse Bash hook that
  denies a batch of `gh pr merge` invocations. Its batch counter (line
  ~79, before this fix) was:
  ```python
  merge_count = len(re.findall(r"\bgh\s+pr\s+merge\b", cmd))
  ```
  `cmd` is the *entire* raw Bash command string from `tool_input.command`
  — including the contents of any `--body`/`--body-file` string or
  here-string argument, since those bytes are part of the same shell
  command line the hook receives. The regex has no notion of "this is an
  invoked verb" vs. "this is quoted text" — it just counts substring
  matches across the whole string.
  canonical: on-the-record/hooks/impact-guard.sh:79 (pre-fix, read this session)
- `on-the-record/hooks/test_impact_guard.py` — the only test file
  covering this hook; already exercises the batch-deny/single-pass/
  kill-switch/low-impact paths (four tests, live-fired against the real
  script).

No other file references this counting logic — `merge-allow-gate.sh` (a
different hook, the allow-side counterpart) has its own separate
`re.search(r"\bgh\s+pr\s+merge\b", cmd)` check, out of scope for this
issue (see the proposal's Out of scope).

## Prior art in this repo

canonical: `git log --oneline -1 -- docs/issue-824/proposals/strict-merge-allow-validation.md` output this session — `1928e32 docs(issue-824): after-proposal hunt found a bypass, revise design to punctuation-aware shlex`

`docs/issue-824/proposals/strict-merge-allow-validation.md` independently
designed a fix for the sibling `merge-allow-gate.sh` hook's own
injection-through-a-quoted-argument class of bug, landing on
`shlex.shlex(cmd, posix=True, punctuation_chars=True)` — Python's POSIX
tokenizer, quote/escape-aware — instead of a hand-rolled quote-stripping
regex. That proposal's "Rejected" section documents that a
quote-stripping regex is "equally fooled by the same payload shape" as
the naive approach; the same argument applies here.

## Reproduction

canonical: this session's own PreToolUse:Bash hook stderr, verbatim in
this session's transcript — running a `python3 -c "..."` command whose
*string literal argument* mentioned `gh pr merge` twice was refused by
the live `impact-guard.sh` hook with "impact-guard: batch of 2 `gh pr
merge` calls denied before executing: 89 open proposal(s) require
individual approval ..." (exit code 2), even though no `gh pr merge` was
invoked — the text was inside a quoted Python string literal passed as a
`-c` argument. Reproduced twice in this session, independently, before
any fix was applied.

## Fix direction

Reuse the same tokenizer approach issue #824 already validated for the
sibling hook: `shlex.shlex(cmd, posix=True, punctuation_chars=True)`
merges a quoted argument into a single token, so merge-verb text inside
`--body`/`--body-file`/a here-string can never reassemble into three
adjacent bare tokens `gh`, `pr`, `merge`. Count adjacent
`("gh", "pr", "merge")` token triplets instead of regex substring
matches; a genuine `gh pr merge 1 && gh pr merge 2` still produces two
such triplets since the verb tokens are bare, unquoted words there.
