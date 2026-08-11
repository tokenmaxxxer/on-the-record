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
