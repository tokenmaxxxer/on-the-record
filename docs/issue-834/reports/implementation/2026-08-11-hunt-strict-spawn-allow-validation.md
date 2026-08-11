---
proposal: docs/issue-834/proposals/strict-spawn-allow-validation.md
---

# Hunt record — strict-spawn-allow-validation

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-834/proposals/strict-spawn-allow-validation.md (design not yet ported to
  on-the-record/hooks/spawn-allow-gate.sh); reference implementation read from
  on-the-record/hooks/merge-allow-gate.sh lines 91-129 (issue #824's shlex-based check, which
  the proposal says it will port verbatim in shape).
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only phase-1, no code touched yet — proposal doc only)
started_at: 2026-08-11T10:56:00Z
ended_at: 2026-08-11T11:02:30Z

Tried, live, against a throwaway Python script reproducing the exact
`shlex.shlex(cmd, posix=True, punctuation_chars=True)` +
`_is_operator_token` design from merge-allow-gate.sh (ported in shape to the
`[PYBIN, SPAWN_PATH, *tail]` / `["cd", DIR, "&&", PYBIN, SPAWN_PATH, *tail]`
shapes the proposal describes):

- Unquoted/adjacent operators with no whitespace (`foo;evil`, `foo&&evil`,
  `foo|evil`, `1>/tmp/pwned;touch`, `2>&1;touch /tmp/PWNED`): shlex reliably
  splits every occurrence of `;`, `&&`, `|`, `>`, `&`, `<` into its own
  token regardless of adjacency to non-punctuation text (confirmed via
  direct tokenization dump) — each such token is composed entirely of
  operator characters and gets caught by `_is_operator_token`, matching
  bash's real (whitespace-independent) operator recognition. No gap here.
- Process substitution in the `cd` DIR slot or task-text tail
  (`cd <(touch /tmp/PWNED) && python3 spawn.py ...`,
  `python3 spawn.py review <(id>/tmp/PWNED)`): not `$(`/backtick, so the
  upfront reject doesn't catch it directly — but shlex tokenizes `<(` as
  its own token composed entirely of operator chars (`<`, `(` are both in
  `punctuation_chars`), so it's either flagged by `_is_operator_token`
  directly, or (in the `cd` case) breaks the required `tokens[2] == "&&"`
  shape match entirely, falling through unreached. No allow either way.
- Backslash-escaped operators (`foo\;evil`) and bash ANSI-C-quoted
  operators (`foo$'\073'touch /tmp/PWNED`): shlex's parse of these differs
  textually from bash's real interpretation (shlex doesn't understand
  `$'...'` and produces a different literal token than bash's actual
  single argv element `foo;touch`), but in both bash's real behavior and
  shlex's approximation, the semicolon-shaped byte stays *inside one
  argument* — it never becomes a second command. Confirmed with
  `bash -c 'set -x; echo python3 spawn.py review foo$'"'"'\073'"'"'touch
  /tmp/PWNED'`: the trace shows `'foo;touch'` as a single quoted argv
  element, not two commands. This is tokenizer-output drift, not a
  privilege/execution bypass (no reproduction of a wrong `allow` +
  attacker-controlled side effect).
- Env-var indirection in place of `$(...)`: an unquoted `$VAR` token is
  never expanded by shlex (matches bash's real parse-time operator
  recognition, which happens before expansion) and either fails the
  SPAWN_PATH-ends-with-`spawn.py` shape match (falls through unreached) or,
  if it's in `tail`, is inert plain text — bash does not re-interpret
  metacharacters that appear *inside* an expanded variable's value as
  operators, so no injection path here either.

No shape was found where this design's shlex tokenize-then-check-operator-
tokens approach classifies a command as one of the two allowed shapes with
no operator-only token in `tail`/`DIR`, while bash itself still executes a
second, attacker-controlled command. Everything tried either (a) gets
correctly flagged as an operator token by `_is_operator_token`, (b) fails
the strict shape match and falls through unreached (fail-open-to-no-allow,
same as today), or (c) changes only the literal text of a single argument
passed to `spawn.py`, never causing a second command to run. Time budget
spent on live probing rather than static reasoning; stopping here with no
reproduction to report.
