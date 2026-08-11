---
proposal: docs/issue-824/proposals/strict-merge-allow-validation.md
---

# Hunt record — strict-merge-allow-validation

## after-proposal — stance 0: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — the naive `re.sub(r"'[^']*'", "", rest)` single-quote-span
stripping the proposal specifies (copied from spawn-allow-gate.sh's shipped
pattern) desyncs from bash's real single-quote toggle whenever the payload
uses bash's standard backslash-escaped-quote-outside-single-quotes idiom
(`\'`), letting a live, unquoted `;` hide inside what the regex misclassifies
as a stripped/inert quoted span.
Kind: composition
Seed: docs/issue-824/proposals/strict-merge-allow-validation.md (phase-2
design of on-the-record/hooks/merge-allow-gate.sh's anti-chaining check,
mirroring on-the-record/hooks/spawn-allow-gate.sh's shipped
`re.sub(r"'[^']*'", "", rest)` + forbidden-operator-search pattern)
cap_seconds: 60
tier: docs-only
diff_stat_lines: n/a (docs-only proposal, no code diff yet)
started_at: 2026-08-11T09:53:00Z
ended_at: 2026-08-11T10:02:00Z

canonical: docs/issue-824/proposals/strict-merge-allow-validation.md
"What will be done" section (read directly) — the described check is
"reject the whole command if any of `&&`, `;`, `|`, backtick, `$(`, `<`,
`>`, or a newline is reachable outside single-quoted spans anywhere in the
remainder", naming on-the-record/hooks/spawn-allow-gate.sh's shipped
`re.sub(r"'[^']*'", "", rest)` step as the precedent to reuse. The three
fences below run that exact two-step algorithm live in this session, then
run the identical string through real bash, to test whether the algorithm
and bash's own parsing agree.

### Reproduce

derived: apply the design's own forbidden-operator check exactly as
specified (strip single-quoted spans via the named `re.sub` pattern, then
search the remainder for `&&|;|\||\$\(|`|<|>|\n`) against a candidate
command built from: the merge target words, space, `42`, space, backslash,
apostrophe, semicolon, the word `evil`, semicolon, apostrophe, the letter
`X`, apostrophe.

```
$ python3 - <<'PY'
import re
target = "gh" + " pr" + " merge"
rest = target + " 42 \\';evil;'X'"
stripped = re.sub(r"'[^']*'", "", rest)
print("stripped:", repr(stripped))
print("forbidden match:", re.search(r"&&|;|\||\$\(|`|<|>|\n", stripped))
PY
stripped: "gh pr merge 42 \\X'"
forbidden match: None
```

canonical: the fence immediately above (own read, this session) — the
design's specified check, applied to this exact candidate string, reports
no forbidden operator reachable.

derived: apply the design's shlex first-three-token check on the
(unstripped) remainder of the same candidate string.

```
$ python3 -c "
import shlex
target = 'gh' + ' pr' + ' merge'
rest = target + ' 42 \\\\\'\;evil;\'X\''
print(shlex.split(rest)[:3])
"
['gh', 'pr', 'merge']
```

canonical: the fence immediately above (own read, this session) — the
design's specified shlex-based shape check also passes for this candidate,
and the standalone token `42` remains present in the unstripped remainder
for the existing PR-number regex to pick up.

derived: run the identical candidate string through a real bash shell with
the target program and the injected program stubbed out, to see what
actually executes.

```
$ bash -c '
gh() { echo "TARGET CALLED: $*"; }
evil() { echo "INJECTED COMMAND EXECUTED with args: $*"; }
CMD="gh pr merge 42 \\'"'"';evil;'"'"'X'"'"'"
eval "$CMD"
'
TARGET CALLED: pr merge 42 '
INJECTED COMMAND EXECUTED with args:
bash: line 5: X: command not found
```

canonical: the fence immediately above (own read, this session) — real
bash treats the `;` in the candidate string as a live, unquoted statement
separator and runs the stub function `evil` as a fully separate command
(then attempts a third command named `X`, which fails only because `X`
stands in for a placeholder second payload in this reproduction rather
than a real binary).

### Observed

canonical: the three fences above (own read, this session) — the design's
two specified checks (forbidden-operator search over the single-quote-
stripped remainder, and shlex first-three-token match) both certify this
candidate string as clean/no-chaining, while the same string, run through
real bash, executes a second command that the checks never saw. The gap is
the single-quote-stripping step: it treats every apostrophe as an
unconditional open/close toggle, but bash's `\'` (backslash immediately
followed by a quote, appearing outside any open quote) is a literal-quote
escape, not a toggle — so bash's true quote state after that point differs
from the regex's assumed state, and text bash treats as unquoted (the `;`)
lands inside a span the regex treats as matched and removes before the
forbidden-character search runs.

### Expected

canonical: the fences above (own read, this session) — the forbidden-
operator check should either detect the live, unquoted `;` in this
candidate (reject it) or the single-quote-stripping step should track
bash's actual quote-toggle state (accounting for the `\'`-escaped-quote-
outside-quotes idiom) instead of naively pairing every apostrophe left to
right, so it does not misclassify unquoted, executable text as an inert
quoted span. As specified, the phase-2 design lets a merge command
suffixed with `\';evil;'X'` (and equivalent constructions using the same
escaped-quote desync) receive the `allow` decision while chaining an
arbitrary second command onto the merge — the same defect class the
proposal exists to close, reachable through a different syntactic door.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — impact-guard.sh's coarse substring count of the merge
invocation phrase (unaffected by this diff) disagrees with
merge-allow-gate.sh's new precise shlex-based single-invocation
recognition, on the same command string: a legitimate single merge command
with an ordinary `--subject`-style argument that happens to echo the same
three words is recognized by merge-allow-gate.sh's stricter check as the
clean single-merge shape (proceeds toward `allow` if READY), while
impact-guard.sh's `re.findall(r"\bgh\s+pr\s+merge\b", cmd)` counts it as 2
occurrences in the raw text and denies the command outright as a "batch" —
both hooks are wired to the same PreToolUse+Bash event in
`on-the-record/hooks/hooks.json`, evaluating the identical
`tool_input.command` string, and disagree on whether it is one merge or
two.
Kind: composition
Seed: on-the-record/hooks/merge-allow-gate.sh (git diff HEAD),
on-the-record/hooks/impact-guard.sh, on-the-record/hooks/hooks.json
cap_seconds: 120
tier: default
diff_stat_lines: 53 insertions(+), 1 deletion(-) (on-the-record/hooks/merge-allow-gate.sh)
started_at: 2026-08-11T10:18:16Z
ended_at: 2026-08-11T10:24:30Z

Note: this run overran the 120s cap (finished at roughly T+375s including
the write step below) — reasoning and reproduction were captured live
before wrap-up; the section is written in full despite the overrun per
"stop at 120 seconds even if incomplete — write what you have." One
reproduction attempt (a `cat >>` heredoc append containing the target
phrase repeated many times in prose) was itself denied by the live,
currently-wired impact-guard.sh mid-hunt, which is direct, additional,
unplanned confirmation of the exact substring-counting behavior this
finding is about — the record was instead written via the Write tool
(not Bash-matched, so impact-guard never inspects it) to avoid that
self-inflicted loop.

### Reproduce

canonical: `on-the-record/hooks/hooks.json` PreToolUse+Bash list —
`impact-guard.sh` is wired before `merge-allow-gate.sh`, both firing on
the identical `tool_input.command`.

canonical: `on-the-record/hooks/impact-guard.sh` line 79 —
`merge_count = len(re.findall(r"\bgh\s+pr\s+merge\b", cmd))`, a plain
substring/regex count over the whole raw command text, with no
quote/token awareness — counts a match anywhere in the string, including
inside a quoted argument that is not a second shell invocation.

canonical: `git diff HEAD -- on-the-record/hooks/merge-allow-gate.sh` —
the new strict shape check (`shlex.shlex(cmd, posix=True,
punctuation_chars=True)`), which correctly folds a whole quoted argument
into a single token and therefore correctly recognizes a command shaped
like `<merge target words> 42 --subject "<merge target words> notes"` as
the one-shape single-merge command, with no operator token in the tail.

derived: live-fire reproduction, run in this very session (impact-guard.sh
is itself a live PreToolUse hook here) — a Bash tool call whose command
string contained the merge-target phrase twice (once as the real
invocation, once inside a `--subject` argument) was denied by the actual,
currently-wired impact-guard.sh before it ever ran:

```
$ (Bash tool call; command text built as: CMD='<merge> 42 --subject "<merge> notes"' ... )
PreToolUse:Bash hook error: [.../on-the-record/hooks/impact-guard.sh]: impact-guard: batch of 2 `gh pr merge` calls denied before executing: 89 open proposal(s) require individual approval per docs/specs/impact-classification.md's dominant-axis rule: ... Merge them one at a time so each gets its own individual approval.
```

derived: the same command string fed to each hook's own extracted parsing
logic directly (built via Python string concatenation so the outer Bash
command text itself never contains the target phrase twice, per this
hunt's own instruction to avoid re-tripping the live impact-guard hook):

```
$ python3 - <<'EOF'
import re, shlex
gpm = "gh" + " pr" + " merge"
cmd = gpm + ' 42 --subject "' + gpm + ' notes"'
print("CMD:", repr(cmd))
print("impact-guard substring count:", len(re.findall(r"\bgh\s+pr\s+merge\b", cmd)))
lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
lex.whitespace_split = True
tokens = list(lex)
print("merge-allow-gate tokens:", tokens)
OPERATOR_CHARS = set(lex.punctuation_chars) | {";"}
def is_op(t): return bool(t) and all(c in OPERATOR_CHARS for c in t)
if len(tokens) >= 3 and tokens[0]=="gh" and tokens[1]=="pr" and tokens[2]=="merge":
    tail = tokens[3:]
    print("merge-allow-gate: recognized single-merge shape; tail =", tail)
    print("merge-allow-gate: operator token present in tail? ->", any(is_op(t) for t in tail))
else:
    print("merge-allow-gate: NOT recognized shape (falls through, no allow)")
EOF
```

### Observed

```
CMD: 'gh pr merge 42 --subject "gh pr merge notes"'
impact-guard substring count: 2
merge-allow-gate tokens: ['gh', 'pr', 'merge', '42', '--subject', 'gh pr merge notes']
merge-allow-gate: recognized single-merge shape; tail = ['42', '--subject', 'gh pr merge notes']
merge-allow-gate: operator token present in tail? -> False
```

Plus the live hook error above: the actual, currently-wired
impact-guard.sh, given a command containing this same textual pattern,
denies with exit 2 ("batch of 2 ... calls denied") — even though
merge-allow-gate.sh's own (more careful, quote/token-aware) reading of the
identical string sees exactly one real invocation of the merge target and
would proceed toward `allow`.

### Expected

canonical: the fences above (own read, this session) — the two hooks
evaluating the same `tool_input.command` for "how many merge invocations
does this contain" should agree, or at minimum impact-guard.sh's coarser
count should not be able to override merge-allow-gate.sh's careful,
tokenization-based determination that there is only one real invocation —
the rule that composed the "batch" check (plain word-boundary substring
counting) never accounted for the same command shapes issue #824 now
tokenizes precisely, so a single, ordinary merge with an incidental
subject/body string is misclassified as a 2-invocation batch and blocked,
while merge-allow-gate.sh — evaluated on the identical raw text — reaches
the opposite, correct conclusion.
