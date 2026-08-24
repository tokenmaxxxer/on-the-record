"""issue #2210 — shared heredoc-body-blanking helper.

Four PreToolUse gates (gate-registration-guard.sh,
acceptance-command-real-run-guard.sh, live-fire-claim-real-run-guard.sh,
spec-index-preflight.sh) all answer the same question before doing any
real work: does this Bash command's shell SYNTAX actually invoke `git
commit`? Each answers it by shlex-tokenizing the WHOLE raw command text
and checking for standalone "git"/"commit" tokens (issue #866/#882) --
and until this module, "the whole raw command text" included any
heredoc BODY text (`cat >> file << 'EOF' ... EOF`), which is DATA the
shell never parses as syntax, not command tokens. A record/report body
appended via heredoc that happens to mention the words "git" and
"commit" in prose -- an unremarkable thing for an engineering record
about this very repository to do -- tokenized as if those words were
real command tokens, so all four gates ran their full body (subprocess
`git`/`gh` calls) on an ordinary heredoc append that was never a git
commit at all. shlex's own per-character work over a body that can be
many KB was also redone four times over, once per gate, since
core#282/#283 put all four in one dispatcher process (issue #2210
profile).

strip_heredoc_bodies() blanks out heredoc body spans -- keeping the
open marker and the closing delimiter line, so the surrounding
command's own real shell tokens (including anything chained after the
heredoc) are untouched -- so callers can shlex-tokenize a command
SKELETON whose size no longer scales with an appended body's size at
all.
"""
import re

_HEREDOC_RE = re.compile(
    r"(?P<open><<(?!<)-?[ \t]*(?P<q>['\"]?)(?P<delim>[A-Za-z_][A-Za-z0-9_]*)(?P=q)[ \t]*\r?\n)"
    r"(?P<body>.*?\r?\n)"
    r"(?P<close>[ \t]*(?P=delim)[ \t]*)(?:\r?\n|\Z)",
    re.DOTALL,
)


def strip_heredoc_bodies(cmd):
    """Return `cmd` with every heredoc body span replaced by nothing,
    keeping the `<<[-]DELIM` open marker and the closing DELIM line so
    the command's real shell structure (including a `&&`/`;` chained
    after the heredoc) survives intact. `cmd` unchanged when it has no
    `<<` at all (the common case) -- no regex work done."""
    if "<<" not in cmd:
        return cmd
    return _HEREDOC_RE.sub(
        lambda m: m.group("open") + m.group("close") + "\n", cmd)
