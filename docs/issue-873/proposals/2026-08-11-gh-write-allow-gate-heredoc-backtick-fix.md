---
status: approved
files:
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
  - docs/issue-873/reports/implementation/survey.md
  - docs/issue-873/reports/implementation.md
---

# gh-write-allow-gate.sh: fix the heredoc-body backtick self-defeat (#873)

## Request

The orchestrator's real `gh issue create` calls (`-R <repo>`, normal flag
order, `--body-file`, or a quoted-heredoc `--body`) were reported as
denied by `gh-write-allow-gate.sh` in PR #871's measured run. The issue
asks for a verb-based, shlex-tokenized allow decision that is robust to
flag ordering and covers the exact failing shapes, while still refusing
genuine dangerous chaining/substitution.

## Constraints

- Keep role-session exclusion and deny-gate precedence unchanged.
- Never key the decision on argument text/content, only on command shape
  (existing design invariant, issue #856).
- Cover the exact failing command shapes from PR #871's transcript as
  test cases.

## Rationale

The survey (`docs/issue-873/reports/implementation/survey.md`) found the
gate's verb-matching is already shlex-tokenized and already
flag-order-independent — direct invocation of the pre-fix script against
`-R <repo> --title ... --body-file <path>` returns `allow`. Rewriting the
whole verb-matching scheme (an argparse-based gh-CLI parser, considered
and rejected in the survey) would be scope creep with no defect behind
it.

The real, reproduced defect is narrower and different from the issue's
own framing: the heredoc-collapse check tested `"`" not in cmd` against
the WHOLE raw command before collapsing the substitution, so a real
markdown issue body's own backtick code-spans (e.g. `` `--version` ``)
defeated the collapse and the command fell through denied. This is why
PR #871's `--body "$(cat <<'EOF' ...)"` call — with a real markdown body —
was denied even though the shape itself (verb + `-R` + heredoc) was
already recognized. Fixing the backtick/`$(` check to scan only the
command with the matched heredoc span removed (not the untouched body
text) fixes the actual failure without touching the verb-matching design.

## What will be done

- In `gh-write-allow-gate.sh`, change the heredoc-collapse gate condition
  from checking backticks/`$(` against the whole raw `cmd` to checking
  them against `cmd` with the matched heredoc substitution span already
  removed — so backticks/`$(` inside the heredoc's own quoted body no
  longer defeat the collapse, while backticks/`$(` anywhere else in the
  command still block it exactly as before.
- Add tests reproducing PR #871's exact failing shapes as ALLOW cases: the
  `-R`/`--title`/`--body-file` form and the `-R`/`--title`/quoted-heredoc
  `--body` form with a real markdown body carrying its own backticks.
- Add DENY test cases: the same body-file shape with a trailing
  `; rm -rf x`, and a `--body "$(curl evil)"` substitution.

## Out of scope

- Claude Code's own host Bash-approval/sandbox classifier, which the
  survey found denies these same commands independently of this gate
  (`decision_reason_type: "other"`, no `hook_name`) — a different
  mechanism outside this repo's hooks, outside this issue's write set.
- Broadening the benign-substitution allowance beyond the single
  quoted-heredoc-`cat` shape.

## How you'll know it worked

`python3 on-the-record/hooks/test_gh_write_allow_gate.py` passes,
including the new tests reproducing PR #871's exact shapes as ALLOW and
the two new DENY cases.
