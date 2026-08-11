---
kind: current-state-survey
---

# Survey: gh-write-allow-gate.sh robustness (issue #873)

## Write surface

- `on-the-record/hooks/gh-write-allow-gate.sh` — the gate itself (issue
  #856, extended #868/#869).
- `on-the-record/hooks/test_gh_write_allow_gate.py` — its test suite.

No other file references this gate's internals; `spawn.py` and
`board-gate.sh` are unrelated Bash-approval mechanisms (see below).

## Current shape (before this change)

canonical: `on-the-record/hooks/gh-write-allow-gate.sh` lines 98-138, read
this session, before any edit — the gate already tokenizes the whole
command via `shlex.shlex(posix=True, punctuation_chars=True)` and matches
the gh verb by exact-prefix tuple match (`("gh","issue","create")`,
etc.). This is already verb-based, not positional-flag-based: `tail =
_match_shape(tokens)` returns everything after the verb, and any token
past the verb is only scanned for shell operator characters, never
inspected by position.

canonical: this session's own `python3 on-the-record/hooks/gh-write-allow-
gate.sh` invocation, run against `gh issue create -R owner/repo --title
"t" --body-file /tmp/body.txt` on the pre-fix file — output `"allow"`,
and the same for the equivalent `-R`-prefixed heredoc-body form with a
short single-line body — so `-R <repo>` ahead of `--title`/`--body`, and
`--body-file <path>`, were already reachable by the pre-fix script.

## The actual reproducible defect (measured this session)

canonical: `docs/issue-776/reports/execution-observation/steady-state-
2026-08-11-rerun4-transcript.jsonl`, read this session via the Read tool
(lines 38 and 68) — the exact `gh issue create` commands the orchestrator
emitted in PR #871's run.

Ran the pre-fix gate directly against both exact commands, this session:

- `-R <repo> --title ... --body-file <path>` (no substitution) — allowed
  by the pre-#873 script.
- `-R <repo> --title ... --body "$(cat <<'EOF' ... EOF)"` where the
  heredoc BODY is real markdown containing its own backtick code-spans
  (`` `--version` ``, `` `_pkg.VERSION` ``, `` `__version__` ``, a
  `` `check:` `` line with a backtick-quoted shell command) — denied (no
  stdout, exit 0 = pass-through with no permissionDecision).

canonical: `on-the-record/hooks/gh-write-allow-gate.sh` lines 98-109
(pre-fix), read this session — root cause: the heredoc-collapse gate
condition was `if len(_subs) == 1 and cmd.count("$(") == 1 and "`" not in
cmd:` — the `"`" not in cmd` check ran against the WHOLE raw command,
including the as-yet-uncollapsed heredoc body text itself. A real
issue/comment body is markdown, and markdown routinely uses backtick
code-spans — so any real body defeats its own collapse before the
collapse can prove the body inert, and the command falls through to
`"`" in cmd → exit 0` (denied) a few lines later.

canonical: the two direct invocations described in "Current shape" and
"The actual reproducible defect" above, same session — this is a distinct,
more consequential bug than the `-R`/flag-order framing in the issue
text: the `-R`/flag-order shape was never actually broken, but almost
every real multi-line issue body IS broken by this backtick self-defeat.

## Why the transcript ALSO shows Bash-level denials unrelated to this gate

canonical: `docs/issue-776/reports/execution-observation/steady-state-
2026-08-11-rerun4-transcript.jsonl`, read this session (system
`permission_denied` events at e.g. line 39, 42, 49, 52, 64) — these fire
with `decision_reason_type: "other"`, message `"This command requires
approval"`, no `hook_name` attached, and occur even for the `--body-file`
shape the pre-fix gate already allowed — that is Claude Code's own host
Bash approval/sandbox classifier, a separate mechanism from this repo's
PreToolUse hook, out of this gate's control and out of this issue's write
set.

canonical: `docs/issue-776/reports/execution-observation/run4.md`, read
this session (step 4) — already states this explicitly: "This is a
different mechanism from `gh-write-allow-gate.sh`, so #869 never had a
chance to run against a real call to that verb this session." This survey
does not attempt to fix that separate host mechanism.

## Alternatives considered

- Rewrite the whole verb-matching scheme from prefix-tuple matching to a
  more general argparse-based gh-CLI shape parser. Rejected — canonical:
  the "Current shape" section's direct invocation above shows the
  existing prefix-tuple + shlex design already satisfies the issue's
  stated requirement ("verb-based via shlex tokenization... regardless of
  flag ordering"), so replacing it would be scope creep with no defect
  behind it. The real defect is narrow (the backtick self-defeat) and the
  fix stays inside the existing design.
- Widen the "benign substitution" allowance beyond the single
  quoted-heredoc-cat shape (e.g. also allow `printf` or `echo`
  heredocs). Rejected: out of scope for #873, which asks only that the
  exact #871 shapes work; broadening the allowed substitution shapes is a
  separate, unrequested security-surface decision.
