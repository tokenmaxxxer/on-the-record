# Survey — issue #882

## Write set

- `on-the-record/hooks/spec-index-preflight.sh`
- `on-the-record/hooks/gate-registration-guard.sh`
- `on-the-record/hooks/role-axis-completeness-guard.sh`
- `on-the-record/hooks/test_spec_index_preflight.py`
- `on-the-record/hooks/test_gate_registration_guard.py`
- `on-the-record/hooks/test_role_axis_completeness_guard.py`
- `docs/issue-882/**` (this survey, the proposal, the resolution write-up,
  the hunt record)

Unlike issue #876, `spec-index-preflight.sh` is now IN scope — it is the
file that carries the design flaw this issue closes, not a frozen
reference.

## Scout-directive skip condition

Pure bugfix: the issue names the exact bypass (`(git commit -m x)`
tokenizing to `["(git", "commit", "-m", "x)"]`, so `"git" in tokens` is
`False`) and directs evaluating a specific already-landed alternative
design (`punctuation_chars=True`, issue #824/#834) against the same five
inputs, rather than open-ended design search. No product-shaped surface,
no exemplar field to scout. Scouting is skipped per the scout-directive's
first skip condition.

## Reproducing the issue's own table

canonical: this session's own run, this branch (== `origin/main` at
survey time, `fc018b5`), against the byte-identical `shlex.split`-based
check established in "## Current state of all three hooks" below:

```
$ python3 - <<'DONE'
import shlex
inputs = [
    'git commit -m x',
    'git -c user.name=B -c user.email=b@e commit -m x',
    '(git commit -m x)',
    'cd /tmp && git commit -m x',
    'git commit-tree abc',
]
for cmd in inputs:
    try:
        tokens = shlex.split(cmd)
        ok = True
    except ValueError:
        tokens, ok = None, False
    matched = ok and ("git" in tokens and "commit" in tokens)
    print(f"{cmd!r:55} tokens={tokens} matched={matched}")
DONE
'git commit -m x'                                      tokens=['git', 'commit', '-m', 'x'] matched=True
'git -c user.name=B -c user.email=b@e commit -m x'     tokens=['git', '-c', 'user.name=B', '-c', 'user.email=b@e', 'commit', '-m', 'x'] matched=True
'(git commit -m x)'                                    tokens=['(git', 'commit', '-m', 'x)'] matched=False
'cd /tmp && git commit -m x'                            tokens=['cd', '/tmp', '&&', 'git', 'commit', '-m', 'x'] matched=True
'git commit-tree abc'                                  tokens=['git', 'commit-tree', 'abc'] matched=False
```

canonical: this session's own fenced repro immediately above — matches
the issue body's own table (the issue's `old`/`new` columns are the
pre-#866 regex / current `shlex.split` columns; this survey's `matched`
column reproduces the issue's `new` column).

canonical: same fenced repro — reproduced before any code was touched
this session.

## Current state of all three hooks

canonical: `grep -n -B2 -A6 'tokens = shlex.split' on-the-record/hooks/spec-index-preflight.sh on-the-record/hooks/gate-registration-guard.sh on-the-record/hooks/role-axis-completeness-guard.sh`,
run this session against this branch's working tree:

```
on-the-record/hooks/spec-index-preflight.sh-55-try:
on-the-record/hooks/spec-index-preflight.sh:56:    tokens = shlex.split(cmd)
on-the-record/hooks/spec-index-preflight.sh-57-except ValueError:
on-the-record/hooks/spec-index-preflight.sh-58-    sys.exit(0)
on-the-record/hooks/spec-index-preflight.sh:59:if "git" not in tokens or "commit" not in tokens:
on-the-record/hooks/spec-index-preflight.sh-60-    sys.exit(0)
--
on-the-record/hooks/gate-registration-guard.sh-68-try:
on-the-record/hooks/gate-registration-guard.sh:69:    tokens = shlex.split(cmd)
on-the-record/hooks/gate-registration-guard.sh-70-except ValueError:
on-the-record/hooks/gate-registration-guard.sh-71-    sys.exit(0)
on-the-record/hooks/gate-registration-guard.sh:72:if "git" not in tokens or "commit" not in tokens:
on-the-record/hooks/gate-registration-guard.sh-73-    sys.exit(0)
--
on-the-record/hooks/role-axis-completeness-guard.sh-74-try:
on-the-record/hooks/role-axis-completeness-guard.sh:75:    tokens = shlex.split(cmd)
on-the-record/hooks/role-axis-completeness-guard.sh-76-except ValueError:
on-the-record/hooks/role-axis-completeness-guard.sh-77-    sys.exit(0)
on-the-record/hooks/role-axis-completeness-guard.sh:78:if "git" not in tokens or "commit" not in tokens:
on-the-record/hooks/role-axis-completeness-guard.sh-79-    sys.exit(0)
```

canonical: the fenced grep output immediately above — byte-identical
six-line block across all three files. `shlex` is already imported at
each file's GUARD top import line (`spec-index-preflight.sh:31`,
`gate-registration-guard.sh:44`, `role-axis-completeness-guard.sh:48`,
per `grep -n '^import ' on-the-record/hooks/*.sh` run this session) — no
import-line change needed for a fix that stays within the `shlex`
module.

## Origin of this issue, and the repeat-hole pattern

canonical: `docs/issue-876/reports/implementation/resolution.md`, "##
Open findings" section, read this session:

```
$ python3 - <<'DONE'
import shlex
print(shlex.split('(git commit -m "test")'))
DONE
['(git', 'commit', '-m', 'test)']
```

canonical: same resolution.md "## Open findings" section — its
end-to-end harness ran the wrapped form against a disposable repo
(`direct-exec rc= 0`, commit landed in `git log`), and it named this
issue's shape as the needed follow-up: "design a shell-aware (not purely
whitespace-tokenizing) `git commit` trigger check ... and apply it
uniformly to all three hooks (`spec-index-preflight.sh` included)".

canonical: `docs/issue-876/reports/implementation/resolution.md` ("##
Open findings", pre-#876 regex comparison) plus this issue's own body,
both read this session.

canonical: same two sources — this is the second round in a row where a
trigger-check fix traded one gap for another; table below:

| round | closed | opened |
|---|---|---|
| #866/#875 | `\bgit\s+commit\b` regex missed `git -c k=v commit` (global-option bypass) | switching to `shlex.split` lost the `\b` word-boundary behavior that caught `(git commit ...)` (paren-fused bypass) |
| #876 | ported the #866 fix to the two sibling hooks, closing the `git -c k=v commit` bypass on those two as well | reproduced the identical paren-fused bypass on those same two hooks (already present, unfixed, on `spec-index-preflight.sh` since #866) |
| #882 (this issue) | closes the paren-fused bypass, on all three hooks at once | see "## Candidate fix" below — evaluated against all five inputs first, specifically to check for a third round |

## Candidate fix: `punctuation_chars=True` (issue #824/#834's landed design)

canonical: `on-the-record/hooks/merge-allow-gate.sh` lines 29-39, 91-116
and `on-the-record/hooks/spawn-allow-gate.sh` lines 20-21, 105-127, read
this session, this branch. Both hooks tokenize `tool_input.command` via:

```python
_lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
_lexer.whitespace_split = True
tokens = list(_lexer)
```

then build `OPERATOR_CHARS = set(_lexer.punctuation_chars) | {";"}` for
their own strict-shape allowlist logic (`gh pr merge` / `spawn.py`
argv-position matching).

canonical: same two files, same line ranges — that allowlist-shape logic
is specific to those two hooks' narrower job (granting a permission, not
just detecting a trigger) and is not needed here; only the tokenizer
construction itself is the reusable, already-landed shape this issue's
own body directs reading.

canonical: this session's own run, this branch, applying only the
tokenizer swap (`shlex.split(cmd)` -> the `shlex.shlex(...)` construction
above) to the trigger condition, against the same five inputs:

```
$ python3 - <<'DONE'
import shlex
inputs = [
    'git commit -m x',
    'git -c user.name=B -c user.email=b@e commit -m x',
    '(git commit -m x)',
    'cd /tmp && git commit -m x',
    'git commit-tree abc',
]
for cmd in inputs:
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
        ok = True
    except ValueError:
        tokens, ok = None, False
    matched = ok and ("git" in tokens and "commit" in tokens)
    print(f"{cmd!r:55} tokens={tokens} matched={matched}")
DONE
'git commit -m x'                                      tokens=['git', 'commit', '-m', 'x'] matched=True
'git -c user.name=B -c user.email=b@e commit -m x'     tokens=['git', '-c', 'user.name=B', '-c', 'user.email=b@e', 'commit', '-m', 'x'] matched=True
'(git commit -m x)'                                    tokens=['(', 'git', 'commit', '-m', 'x', ')'] matched=True
'cd /tmp && git commit -m x'                            tokens=['cd', '/tmp', '&&', 'git', 'commit', '-m', 'x'] matched=True
'git commit-tree abc'                                  tokens=['git', 'commit-tree', 'abc'] matched=False
```

canonical: the fenced repro immediately above — all five inputs now show
the correct judgment (`True, True, True, True, False`) — the paren case
flips from `False` to `True` without disturbing the other four,
including the two shapes #866/#876 already fixed (`git -c ...`, and
`commit-tree` as a bycatch true-negative).

canonical: this session's own run immediately below, re-checking the two
prior true-negative/fail-open regression shapes each hook's test suite
already pins (`test_spec_index_preflight.py` lines 194-211, per `grep -n`
cited in "## Test-file conventions" below), against the candidate
tokenizer:

```
$ python3 - <<'DONE'
import shlex
def tok(cmd):
    lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)
try:
    tok('git commit -m "unterminated')
except ValueError as exc:
    print("ValueError:", exc)
print(tok('echo "please run git commit before pushing"'))
DONE
ValueError: No closing quotation
['echo', 'please run git commit before pushing']
```

canonical: the fenced repro immediately above — unterminated quote still
raises `ValueError` (fail-open `exit(0)` unchanged, same wrapper as
today); `'commit'` inside a quoted string stays fused into one token,
not a standalone `"commit"` token.

canonical: this session's own run immediately below — `whitespace_split
= True` is required for the `git -c ...` case specifically:

```
$ python3 - <<'DONE'
import shlex
lexer = shlex.shlex('git -c user.name=B -c user.email=b@e commit -m x', posix=True, punctuation_chars=True)
print(list(lexer))  # whitespace_split left at its default (False)
DONE
['git', '-c', 'user.name=B', '-c', 'user.email=b', '@', 'e', 'commit', '-m', 'x']
```

canonical: the fenced repro immediately above — without
`whitespace_split = True`, `shlex.shlex(..., punctuation_chars=True)`'s
default `wordchars` also splits on `@` inside an unquoted token,
fragmenting `user.email=b@e` into three pieces, a correctness bug in the
token list even though this particular case still happens to keep `git`
and `commit` standalone. `merge-allow-gate.sh` and `spawn-allow-gate.sh`
(cited above) both set `whitespace_split = True` for this reason.

### Alternative considered: strip a leading `(` before tokenizing

Regex-strip a leading `(` (and trailing `)`) from `cmd` before calling
`shlex.split`, instead of switching tokenizers. Rejected in the
proposal's `## Rationale` — narrower fix, handles only the one reported
shape and not other punctuation-fused prefixes (e.g. `{git commit -m
x;}`, a brace-grouped subshell), and does not reuse an already-landed,
already-tested design the issue explicitly directs reading first.

## The shared-helper question (issue's decision point 3)

canonical: `docs/issue-876/reports/implementation/survey.md`, "The
shared-helper question" section, and
`docs/issue-876/proposals/2026-08-11-port-shlex-trigger-fix-to-sibling-guards.md`,
`## Rationale`, both read this session.

canonical: same two sources — issue #876 investigated and rejected a
shared Python helper module for this exact now-triplicated check, on
four grounds: (1) `hooks.json` invokes every hook by absolute path under
`${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh` with no guaranteed
consumer-repo checkout for a shared module to live in; (2) the one hook
in this family that does import a shared module
(`role-axis-completeness-guard.sh` -> `gates/role_spec_shape.py`) needs a
two-candidate fallback because the packaged copy verifiably lags the
top-level one; (3) every other hook needing Python logic in this
directory inline-ports rather than imports; (4) this hook family's own
fail-open policy means a missing/stale shared dependency degrades to
silently skipping the check, reproducing the exact bypass-by-omission
class this whole issue chain exists to close.

canonical: `on-the-record/hooks/hooks.json`, `grep -n
'spec-index-preflight\|role-axis-completeness-guard\|gate-registration-guard'`,
run this session:

```
{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/spec-index-preflight.sh" },
{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/gate-registration-guard.sh" },
{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/role-axis-completeness-guard.sh" },
```

canonical: the fenced grep output immediately above — still all three,
still invoked by absolute plugin-root path, so ground (1) is unchanged.
This issue's own fix does not touch `hooks.json`, `gates/`, or
`role_spec_shape.py`, so grounds (2)-(4) are unchanged in kind — this
issue only changes the shape of the inline check itself (which tokenizer
call), not whether it is inline. The #876 rejection is re-affirmed, not
re-derived from scratch, in the proposal's own `## Rationale`.

This issue does not grow the duplication count (still three hook files,
same as after #876) — it changes what is duplicated (a multi-line
tokenizer construction instead of a one-line `shlex.split` call), so the
`## Accumulation` question is narrower here than in #876: whether a
sixth future change to this same snippet is still an accepted, by-hand,
three-file edit. Addressed in the proposal's own `## Accumulation`
section.

## Test-file conventions

canonical: `on-the-record/hooks/test_spec_index_preflight.py` lines
15-32, `grep -n -A12 'def is_git_commit_invocation'`, read this session
— this file (only) carries a pure-Python mirror of the GUARD body's
trigger check (`is_git_commit_invocation`), used by its own in-process
test cases rather than shelling out to the real hook. This mirror must
be edited in the same tokenizer-swap shape as the hook itself, or the
mirror and the hook silently diverge.

canonical: `on-the-record/hooks/test_spec_index_preflight.py` lines
177-211, `grep -n -A2 '@test'`, read this session — six existing
regression cases pin the plain-`git commit`, `git -c ...`,
`--grep=commit`, `commit-tree`, quoted-string, and unterminated-quote
shapes; none currently cover the paren-fused shape this issue adds.

canonical: `on-the-record/hooks/test_gate_registration_guard.py` and
`on-the-record/hooks/test_role_axis_completeness_guard.py`, `grep -n
'subprocess.run(\[.bash.'`, read this session.

canonical: same two files, same grep — both drive the real hook script
end-to-end via `subprocess.run(["bash", str(GUARD)], ...)` against a
real `git init` fixture repo, the existing convention in each file's own
`t_git_dash_c_commit_is_still_detected` /
`t_commit_tree_is_not_a_commit_trigger` cases. No pure-Python mirror to
keep in sync in either of these two files; a new regression case is a
real staged violation committed via `(git commit -m msg)` (or
equivalent), asserting `returncode == 2`.
