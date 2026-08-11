---
kind: implementation-record
code_under_review:
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
type: fix
breaking: false
verdict: n/a
loop_state: landed
---

# Implementation record: gh-write-allow-gate.sh heredoc-body backtick fix (#873)

## What was done

canonical: `on-the-record/hooks/gh-write-allow-gate.sh` diff, this session
— changed the heredoc-collapse gate condition in the `$(cat <<'EOF' ...
EOF)` benign-substitution check from testing backticks/`$(` against the
WHOLE raw command to testing them against the command with the matched
heredoc substitution span already removed
(`cmd[:_sub.start()] + cmd[_sub.end():]`). Backticks or `$(` inside the
heredoc's own quoted body (inert by construction — a quoted heredoc
delimiter disables all expansion of its body) no longer defeat the
collapse; backticks/`$(` anywhere else in the command still block the
allow exactly as before.

canonical: `on-the-record/hooks/test_gh_write_allow_gate.py` diff, this
session, and `docs/issue-776/reports/execution-observation/steady-state-
2026-08-11-rerun4-transcript.jsonl` (read this session via the Read tool)
— added new tests: two ALLOW cases reproducing PR #871's exact
`gh issue create -R <repo> --title ... --body-file <path>` and
`-R <repo> --title ... --body "$(cat <<'EOF' ...)"` (with a real markdown
body carrying its own backtick code-spans) invocations verbatim from that
transcript; and two DENY cases — the body-file shape chained with
`; rm -rf x`, and `--body "$(curl evil)"`.

canonical: this session's own
`python3 on-the-record/hooks/test_gh_write_allow_gate.py` run
```
28 passed
```
No failures; all pre-existing tests plus the new ones pass with no
regressions.

## Why

canonical: `docs/issue-873/reports/implementation/survey.md`, this
session — the survey found the gate's verb-matching was already
shlex-tokenized and flag-order-independent (direct invocation of the
pre-fix script against `-R <repo> --title ... --body-file <path>`
returned `allow`); the actual reproduced defect was narrower: the
heredoc-collapse backtick check ran against the whole raw command before
collapsing the substitution, so a real markdown body's own backtick
code-spans defeated the collapse for the `--body "$(cat <<'EOF' ...)"`
shape, which is why PR #871's real invocation was denied.

## Upstream basis

Based on: docs/issue-873/proposals/2026-08-11-gh-write-allow-gate-heredoc-backtick-fix.md

## What did not work

None.

## Doc placement

- No new dependency, env var, migration, or setup step — no handbook entry.
- No new public signature/wire format and no library-or-format choice over
  a named alternative — no docs/issue-873/decisions/ entry (the survey's
  "Alternatives considered" section already carries the one rejected
  alternative, per the proposal's own Rationale).
- No benchmark/investigation numbers beyond what the survey already
  records.

## Open findings

None.
