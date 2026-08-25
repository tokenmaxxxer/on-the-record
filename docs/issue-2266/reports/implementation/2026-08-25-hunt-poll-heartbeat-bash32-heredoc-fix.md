---
proposal: none (build-now bypass) — issue #2266
---

# Hunt record — poll-heartbeat-bash32-heredoc-fix

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the new regression test `t_no_command_substitution_wrapped_heredoc_in_script` (and its sibling `t_poll_heartbeat_bash_syntax_is_clean`) only catch the landmine shape when `$(` and `<<DELIM` sit on the *same physical line*; a heredoc opened on a line following the `$(` (e.g. via a trailing `\` continuation) reproduces the identical bash-3.2 parse failure #1719/#2181 hit, and neither new test detects it.
Kind: silent-failure
Seed: issue #2266 — on-the-record/monitors/poll-heartbeat.sh, on-the-record/monitors/poll_heartbeat_delta.py (new), on-the-record/monitors/test_poll_heartbeat.py; full diff read from /tmp/issue-2266-diff.txt
cap_seconds: 180
tier: size:200+ lines changed
diff_stat_lines: 250+ lines across 2 modified files + 1 new ~220-line file
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:07:00Z

### Reproduce
```
mkdir -p /tmp/repro2266
cat > /tmp/repro2266/case_multiline.sh << 'OUTER'
#!/bin/bash
CHECKOUT=/tmp
printed_text="hi"
diff_output="$(POLL_HEARTBEAT_TEXT="${printed_text}" python3 - "${CHECKOUT}/x" "$(date +%s)" \
<<'PY'
import hashlib, json, os, re, sys
state_path, now_s = sys.argv[1], sys.argv[2]
now = int(now_s)
text = os.environ.get("POLL_HEARTBEAT_TEXT", "")
lines = text.split("\n") if text else []
# issue #1719: [returned-pr] no longer joins the always-emit set —
# it is compared below with its age= token stripped instead, so an
# unchanged set doesn't re-announce every tick (supersedes #1239 req 2).
ALWAYS_RE = re.compile(
    r"^\[(resume|orphaned|watchdog-crash|awaiting-approval)\]|STALLED|CRASHED|COMPLETED|watcher-dead",
    re.IGNORECASE,
)
print("done")
PY
)"
if [ -n "${diff_output}" ]; then printf '%s\n' "${diff_output}"; fi
OUTER

# 1. Real bash 3.2 (the exact class of consumer that reported #1719/#2181) rejects it:
docker run --rm -v /tmp/repro2266:/w bash:3.2 bash -n /w/case_multiline.sh

# 2. The sandbox's own bash (what `t_poll_heartbeat_bash_syntax_is_clean` would run under
#    in CI) parses it fine — that test's own docstring admits it is only "the minimal
#    proxy ... when [bash 3.2] isn't reachable in CI":
bash -n /tmp/repro2266/case_multiline.sh; echo "exit=$?"

# 3. The repo's new structural regex guard (t_no_command_substitution_wrapped_heredoc_in_script)
#    applied to the same file:
python3 - << 'EOF'
import re
_LANDMINE_RE = re.compile(r"\$\(.*<<-?\s*['\"]?[A-Za-z_][A-Za-z0-9_]*['\"]?\s*$")
text = open("/tmp/repro2266/case_multiline.sh").read()
hits = [(i, line) for i, line in enumerate(text.splitlines(), 1) if _LANDMINE_RE.search(line)]
print("hits:", hits)
EOF
```

### Observed
- Real bash 3.2 (`docker run --rm -v /tmp/repro2266:/w bash:3.2 bash -n /w/case_multiline.sh`):
  `/w/case_multiline.sh: line 32: unexpected EOF while looking for matching \`''` /
  `line 34: syntax error: unexpected end of file`, exit=2 — the exact #1719/#2181 failure mode,
  reproduced on a file whose heredoc is nested in a `$( )` split across two physical lines.
- The sandbox's bash 5.1.16 (`bash -n`) on the identical file: exit=0, clean — so
  `t_poll_heartbeat_bash_syntax_is_clean` (which runs under whatever bash the test host ships,
  per its own docstring) would not fail in this repo's CI.
- `_LANDMINE_RE` (copied verbatim from `test_poll_heartbeat.py`) applied to the identical file:
  `hits: []` — the structural guard added by this fix does not flag the file either, because it
  requires `$(` and `<<DELIM` on the same source line.

### Expected
A regression guard whose stated purpose is "poll-heartbeat.sh contains no line that opens a
`$( ... )` command substitution and a `<<DELIM` heredoc redirect" should catch any heredoc that
is lexically nested inside an unclosed `$( )`, not only the case where both tokens happen to sit
on one line. As written, a future edit that reintroduces the delta script (or any other heredoc)
inside `diff_output="$( ... )"` and merely wraps the invocation across two lines — a natural
thing to do to shorten an overlong line — reproduces #1719/#2181's exact bash-3.2 parse failure
while passing both new regression tests and this repo's CI (which runs under a modern bash, not
3.2), i.e. the guard added specifically to prevent recurrence of this landmine is silently
bypassable by the same class of edit it was written to catch.

### Resolution

Fixed in the same commit: `_LANDMINE_RE` (same-line-only regex) replaced with
`_find_command_substitution_wrapped_heredocs` in
on-the-record/monitors/test_poll_heartbeat.py — a depth-tracking scan that counts unmatched `$(`
opens across the whole file (heredoc bodies excluded from counting) and flags any heredoc opener
seen while that count is still positive, regardless of line span. Verified against this hunt's
own repro (`case_multiline.sh` above): the new detector returns a non-empty hit list where the old
regex returned `[]`. A synthetic-sample self-check,
`t_command_substitution_wrapped_heredoc_detector_catches_multiline_shape`, pins the detector's
multi-line coverage going forward without depending on poll-heartbeat.sh happening to stay clean.
The repo-wide structural audit (188 .sh files) was re-run with the same depth-tracking scanner:
0 hits.
