# Current-state survey — issue #834, implementation phase 1

## Write set this proposal will freeze

- `on-the-record/hooks/spawn-allow-gate.sh`
- `on-the-record/hooks/test_spawn_allow_gate.py`
- docs/issue-834/reports/implementation.md (phase-2 output, listed here per
  issue-824's own proposal precedent — not written until the Approve, so
  the path does not exist in the tree yet)

`docs/specs/generated-paths.md` already carries a row for
`spawn-allow-gate.sh` (`n/a | reads/validates only, no write call`) and
this fix adds no new write call, so that file is not part of the write set.

## The defect, read at its cited lines

canonical: `on-the-record/hooks/spawn-allow-gate.sh` lines 104-125, current
branch HEAD (`origin/main` `cfe429f`, working tree clean before this
session's edits)

```
104	# --- command-shape resolution: strip an optional `cd DIR &&` prefix --------
105	rest = cmd.strip()
106	cd_m = re.match(r"^cd\s+\S+\s*&&\s*(.*)$", rest, re.DOTALL)
107	if cd_m:
108	    rest = cd_m.group(1).strip()
109	
110	# --- reject if any shell-chaining/substitution operator is reachable -------
...
118	stripped = re.sub(r"'[^']*'", "", rest)
119	if re.search(r"&&|;|\||\$\(|`|<\(|>\(", stripped):
120	    sys.exit(0)
121	
122	# --- must be exactly a `python3 <...spawn.py> ...` invocation --------------
123	m = re.match(r"^python3?\s+(\S*spawn\.py)(?:\s|$)", rest)
```

canonical: same file, lines 104-108 read above — the prefix-strip runs
before the operator search, and its captured directory slot (`\S+`) is
unbounded: any run of non-whitespace characters satisfies it, including a
command-substitution payload with no internal whitespace
(`$(id>/tmp/x)`, `` `id>/tmp/x` ``). When that happens, the text the
operator search at line 119 actually inspects no longer contains the
substitution — it was consumed by the prefix strip one step earlier.

Reproduced live, this session, with the file's own regex logic run
standalone in `python3 -c`: the command
`cd $(id>/tmp/PWNED_MARKER) && python3 spawn.py review "task"` strips to
`rest == 'python3 spawn.py review "task"'` at line 108 — the
`$(id>/tmp/PWNED_MARKER)` substitution is absent from the string the hook
ever checks for operators, while bash itself evaluates that substitution
(running `id`, redirecting its output to `/tmp/PWNED_MARKER`) before
`spawn.py` starts. The hook's remaining checks then pass normally and it
grants `permissionDecision: allow` for the whole line — this is the
bypass issue #834 reports.

canonical: `docs/issue-824/proposals/strict-merge-allow-validation.md`
lines 62-96 — this is the same bug *class* `merge-allow-gate.sh` shipped
and fixed in issue #824 (a regex reasoning about a substring/remainder of
the command instead of the whole command's token shape), but a different
concrete mechanism: issue-824's bypass was a quote-pairing regex desyncing
from bash's real quote state; this one is an order-of-operations bug where
the prefix-strip removes the very material the next check was meant to
see. Both collapse to the same fix direction: stop reasoning about
substrings/remainders and tokenize the whole command once, with an engine
that tracks bash's real quote/escape/operator state.

## What issue-824 already landed and validated

canonical: `on-the-record/hooks/merge-allow-gate.sh` lines 91-129, current
branch HEAD — the corrected design in production:

- Reject the whole command outright, before any stripping, if a backtick,
  `$(`, or a literal newline appears anywhere in it.
- Tokenize the full, unstripped command with
  `shlex.shlex(cmd, posix=True, punctuation_chars=True)`
  (`whitespace_split = True`).
- Recognize exactly two token shapes (`["gh","pr","merge",...]` or
  `["cd",DIR,"&&","gh","pr","merge",...]`) and reject if any token outside
  the one tolerated `&&` position is composed entirely of operator
  characters (`shlex`'s `punctuation_chars`, plus `;` added explicitly
  since `punctuation_chars` itself omits it).

canonical: `on-the-record/hooks/test_merge_allow_gate.py`, this session's
read — regression coverage for that design:

```
$ grep -c "^def t_" on-the-record/hooks/test_merge_allow_gate.py
14
```

8 of those pre-date issue #824 (bare, flagged, `-R`, `cd`-prefixed forms);
the rest were added by issue #824 for both chain directions, `;`, `|`,
and a backslash-escaped-quote payload that desyncs a naive quote-pairing
regex (file section starting at the `# --- issue #824:` comment,
`on-the-record/hooks/test_merge_allow_gate.py` line 148 onward).

Verified live, this session (`python3 -c`, `shlex.shlex(cmd, posix=True,
punctuation_chars=True)` with `whitespace_split = True`), that this exact
tokenizer handles `spawn-allow-gate.sh`'s payload shapes correctly:

```
'python3 spawn.py review "PR 12 review"'
  -> ['python3', 'spawn.py', 'review', 'PR 12 review']
'cd $(id>/tmp/PWNED_MARKER) && python3 spawn.py review "task"'
  -> ['cd', '$', '(', 'id', '>', '/tmp/PWNED_MARKER', ')', '&&', 'python3', 'spawn.py', 'review', 'task']
"python3 spawn.py review 'build A && B; also C | D'"
  -> ['python3', 'spawn.py', 'review', 'build A && B; also C | D']
'python3 spawn.py review "$(touch /tmp/PWNED_MARKER)"'
  -> ['python3', 'spawn.py', 'review', '$(touch /tmp/PWNED_MARKER)']
python3 spawn.py review 42 \';evil;'X'   (backslash-escaped quote)
  -> ['python3', 'spawn.py', 'review', '42', "'", ';', 'evil', ';', 'X']
'cd `id>/tmp/PWNED_MARKER` && python3 spawn.py review "task"'
  -> ['cd', '`id', '>', '/tmp/PWNED_MARKER`', '&&', 'python3', 'spawn.py', 'review', 'task']
```

The single-quoted task-text case (`'build A && B; also C | D'`) stays one
token — `shlex(posix=True)` groups quoted spans regardless of
`punctuation_chars`, so legitimate literal `&&`/`;`/`|` characters inside
quoted task text are never misread as live operators. Both
command-substitution-hiding-in-the-cd-slot traces above ($( and backtick)
produce a token stream where `tokens[2]` is `'('`/`'>' ` instead of the
literal `"&&"` the recognized `cd`-prefixed shape requires — so even
without the upfront backtick/`$(`/newline reject, the shape match alone
already refuses both, matching the tolerant-cd-prefix shape's own design
intent (only a single, literal `&&` token in that exact position is ever
accepted).

## Existing test coverage that must not regress

canonical: `on-the-record/hooks/test_spawn_allow_gate.py`, this session's
read, current branch HEAD

```
$ grep -c "^def t_" on-the-record/hooks/test_spawn_allow_gate.py
12
```

Those 12 cover: bare invocation allow, sensitive-literal-in-task-text
allow (the original SCOPE-EXTENSION-2 live-observed failure this hook
exists to fix), `cd`-prefixed allow, `consult` subcommand allow,
role-session never-allow, unquoted-`&&`-after-spawn unreached,
single-quoted-operator-in-task-text still-allow, double-quoted `$(...)`
unreached, backtick unreached, spawn.py-outside-checkout unreached,
non-spawn-command untouched, kill-switch suppression. All must keep
passing unmodified in behavior under the new tokenizer — the traces above
show none of the existing payloads land in a different
shape/operator-token classification under `shlex` than they do today.

## Scout skip record (scout-directive mandatory skip line)

Skip condition: **the spec leaves no design decision open.** Issue #834's
body names the corrected design to reuse — `shlex.shlex(..., posix=True,
punctuation_chars=True)`, citing
`docs/issue-824/proposals/strict-merge-allow-validation.md` and
`on-the-record/hooks/test_merge_allow_gate.py` by path — and explicitly
forbids the alternative a category sweep would otherwise surface first
("정규식으로 되돌아가지 마라" — do not return to regex). The remaining
decisions — where inside the existing file structure the tokenizer
replaces the regex block, and which regression payloads to port — are
mechanical porting choices, not open design questions a sweep could
inform. No web/product scouting was run: this is a same-repo, same-pattern
bugfix, not a product-shaped surface.

## Baseline: main HEAD test state

canonical: this session's run of
`python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`, branch
`issue-834/implementation` at `origin/main` `cfe429f`, no local changes

```
$ python3 -m pytest gates/ tests/ on-the-record/hooks/ -q
...
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
1 failed, 1209 passed, 2 skipped, 1 xfailed in 191.91s (0:03:11)
```

canonical: same pytest run's failure output, `gates/test_generated_paths.py`
`t_all_generators_recorded_and_disjoint` assertion message — this one
failure is pre-existing and unrelated to `spawn-allow-gate.sh`:
`stop-poll-rearm.sh 는 write 호출이 없는데 docs/specs/generated-paths.md 는
n/a 가 아닌 'out-of-tree' 로 기록했다` — a `docs/specs/generated-paths.md`
row/generator mismatch for a different hook (`stop-poll-rearm.sh`, landed
by the `d4a8228` commit already on this branch's history per
`git log --oneline -1 -- on-the-record/hooks/stop-poll-rearm.sh`). Out of
scope for #834's frozen write set — flagged here, not fixed here, and this
proposal's "How you'll know it worked" section states the exact delta this
issue's own change must produce against this same baseline.
