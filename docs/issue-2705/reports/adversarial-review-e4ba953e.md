---
issue: 2705
role: adversarial-review-e4ba953e
author: adversarial-review-e4ba953e
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: c6068dcf:on-the-record/hooks/gate-registration-guard.sh
    sha: c6068dcf496c11d1423814e22ab9975fb686aff7
  - path: c6068dcf:test/test_gate_registration_guard_bundled_add_commit.py
    sha: c6068dcf496c11d1423814e22ab9975fb686aff7
  - path: c6068dcf:docs/issue-2705/reports/secure-coding-input-validation-injection-defense+adversarial-review-cd806f25.md
    sha: c6068dcf496c11d1423814e22ab9975fb686aff7
---

# issue-2705 — adversarial-review-e4ba953e record

## What was done

Independently re-verified PR #2753 (branch tip `c6068dcf`) by live-probing
the shipped `c6068dcf:on-the-record/hooks/gate-registration-guard.sh`
directly — feeding it real PreToolUse JSON payloads against throwaway git
clones of the PR branch — rather than trusting the PR's own test suite or
its embedded first-cut adversarial review at face value.

canonical: this session's own live-probe transcript against
`c6068dcf:on-the-record/hooks/gate-registration-guard.sh`, all commands and
outputs reproduced verbatim below.

### Required check 1/4 — bundled, unregistered gate, must refuse

```
$ git clone (fresh, from c6068dcf) ; echo "def check(): pass" > gates/req1_unreg.py
$ payload='{"tool_name":"Bash","tool_input":{"command":"git add gates/req1_unreg.py && git commit -m x"},"cwd":"<repo>","session_id":"s"}'
$ echo "$payload" | bash on-the-record/hooks/gate-registration-guard.sh ; echo rc=$?
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/req1_unreg.py: no row in docs/specs/enforcement-boundary.md
rc=2
```
derived: acceptance check 1 — result: refuses (rc=2), as required.

### Required check 2/4 — bundled, gate + its spec row, must allow

```
$ echo "def check(): pass" > gates/req2_reg.py
$ printf '| mechanism | verdict |\n| --- | --- |\n| `req2_reg.py` | ok |\n' \
    | cat - docs/specs/enforcement-boundary.md > /tmp/eb && mv /tmp/eb docs/specs/enforcement-boundary.md
$ payload='{"tool_name":"Bash","tool_input":{"command":"git add gates/req2_reg.py docs/specs/enforcement-boundary.md && git commit -m x"},...}'
$ echo "$payload" | bash on-the-record/hooks/gate-registration-guard.sh ; echo rc=$?
rc=0
```
derived: acceptance check 2 — result: allows (rc=0), as required.

### Required check 3/4 — stage-then-commit (two calls), unregistered gate, must refuse

```
$ echo "def check(): pass" > gates/req3_unreg.py
$ git add gates/req3_unreg.py            # call 1
$ payload='{"tool_name":"Bash","tool_input":{"command":"git commit -m x"},...}'
$ echo "$payload" | bash on-the-record/hooks/gate-registration-guard.sh   # call 2
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/req3_unreg.py: no row in docs/specs/enforcement-boundary.md
rc=2
```
derived: acceptance check 3 (unbundled direction) — result: refuses (rc=2), matching the pre-existing behavior.

### Required check 4/4 — stage-then-commit (two calls), gate + spec row, must allow

```
$ echo "def check(): pass" > gates/req4_reg.py
$ (prepend enforcement-boundary.md row for req4_reg.py, same technique as check 2)
$ git add gates/req4_reg.py docs/specs/enforcement-boundary.md   # call 1
$ payload='{"tool_name":"Bash","tool_input":{"command":"git commit -m x"},...}'
$ echo "$payload" | bash on-the-record/hooks/gate-registration-guard.sh   # call 2
rc=0
```
derived: acceptance check 4 (unbundled direction) — result: allows (rc=0), matching the pre-existing behavior.

All four required directional results hold: the bundled shape now matches
the unbundled shape in both directions (derived: the four transcripts
immediately above, this session).

### Second adversarial round — shapes the PR's own first-cut review did not cover

canonical: `c6068dcf:docs/issue-2705/reports/secure-coding-input-validation-injection-defense+adversarial-review-cd806f25.md`,
read this session — documents one blind-evaluator round that caught 3 bugs
(`-A`/`-u`/`--all` dead code, `-c`/`-C` global-option bypass, `git add .`
scoping). This task's premise is that a parser in front of a guard is
itself new attack surface, and that one review round rarely exhausts it —
so this session ran a second, independent round against the shipped code
(not the first-cut diff), targeting shapes that round did not exercise.

**Confirmed correct** (all bundled, against an unregistered gate, all run
against the shipped `c6068dcf` hook):

```
$ git add -- gates/new.py && git commit -m x               -> rc=2 (refused)
$ git add gates/new.py; git commit -m x                     -> rc=2 (refused)
$ git add "gates/new gate space.py" && git commit -m x       -> rc=2 (refused)
$ git add gates/*.py && git commit -m x                      -> rc=2 (refused)
$ env FOO=bar git add gates/new.py && git commit -m x         -> rc=2 (refused)
$ git add && git commit -m x --allow-empty                    -> rc=0 (correct: real `git add` with no args stages nothing)
```
derived: this session's own probe-harness output, six commands above, each
run against a fresh clone of `c6068dcf` with a freshly-created untracked
`gates/new.py` (or the quoted/glob variant) present — no fix needed here.

**Four further live, reproducible silent bypasses found** — the bundled
shape still returns rc=0 (silent allow) with a genuinely new, unregistered
gate module present and about to be staged by the pending command:

```
Bypass 1 — plain directory add (no glob, no flag):
$ mkdir -p gates && echo "def check(): pass" > gates/new_dir_gate_1.py   # untracked, never committed -- probe fixture only
$ git add gates/ && git commit -m x     -> rc=0
$ git add gates && git commit -m x      -> rc=0 (no-trailing-slash form, same file)
Confirmed real git actually stages it first:
$ git add gates/ && git diff --cached --name-status
A	gates/new_dir_gate_1.py

Bypass 2 -- cd before add, same command:
$ echo "def check(): pass" > gates/new_gate_cd1.py   # untracked, never committed -- probe fixture only
$ cd gates && git add new_gate_cd1.py && git commit -m x   -> rc=0

Bypass 3 -- subshell with cd:
$ echo "def check(): pass" > gates/new_gate_sub1.py   # untracked, never committed -- probe fixture only
$ (cd gates && git add new_gate_sub1.py) && git commit -m x   -> rc=0

Bypass 4 -- cd to unrelated dir, ..-relative add:
$ echo "def check(): pass" > gates/new_gate_dotdot.py   # untracked, never committed -- probe fixture only
$ cd sub && git add ../gates/new_gate_dotdot.py && git commit -m x   -> rc=0
```
derived: all four commands above run this session against a fresh clone of
`c6068dcf:on-the-record/hooks/gate-registration-guard.sh`; rc captured via
`echo $?` immediately after each `bash on-the-record/hooks/gate-registration-guard.sh`
invocation.

Root cause, bypasses 1-4: `_pending_add_targets`
(`c6068dcf:on-the-record/hooks/gate-registration-guard.sh:229`) resolves a
positional `git add` argument only by exact-name match against the
untracked set or `fnmatch.fnmatch`; neither matches a directory argument
against the individual files inside it (bypass 1), and every relative path
is resolved against the single top-level `cwd` value taken from the JSON
payload (`e.get("cwd")`), never against an effective directory updated by
an intervening `cd` segment in the same command text or inside a `(...)`
subshell (bypasses 2-4). `git add <directory>` and `cd <dir> && git add
<file>` are not corner cases — `git add gates/` is at least as idiomatic a
way to land a new gate as the `-A`/`--all` form the PR's first round already
fixed.

**One live, reproducible false-positive (over-block) found:**

```
$ mkdir -p gates && echo "def check(): pass" > gates/should_not_flag.py   # untracked, never committed -- probe fixture only
$ echo hi > docs_note.md
Real git first, to establish ground truth:
$ git add . ':(exclude)gates/*' && git diff --cached --name-status
A	docs_note.md
(gates/should_not_flag.py correctly NOT staged by real git)
Then the shipped hook, same setup, same command text:
$ git add . ':(exclude)gates/*' && git commit -m x   -> rc=2
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/should_not_flag.py: no row in docs/specs/enforcement-boundary.md
```
derived: both commands run this session against a fresh clone of `c6068dcf`;
real git's `--cached` diff is the ground truth the hook's own verdict is
compared against in the same probe.

Root cause: `_pending_add_targets` has no concept of pathspec magic
(`:(exclude)`, `:(literal)`, `:(glob)`, the `!`-prefix short form) — the `.`
argument's cwd-relative prefix match sweeps in every untracked file under
cwd, including ones a later pathspec argument was meant to exclude. This is
not the "fail-closed on unanalyzable input" the issue's must-not list
explicitly permits: the shape parses without a parse error and produces a
concrete, wrong answer (a real path real git would not stage), rather than
abstaining.

## Why

canonical: `defect-verification-independence-from-upstream-verdicts` skill
file, loaded this session via the Skill tool (full text quoted in "Skill
verdicts" below). That skill warns against treating one clean prior
adversarial round as evidence the surface is exhausted, and against citing
a closed-check entry rather than re-deriving it under time pressure — both
apply directly to this task: the fix's own first-cut review already found
bugs once, which is reason to look harder a second time, not reason to
trust the shipped result on the strength of that first round alone.
Accordingly, the probe set here was deliberately edge/negative-path
weighted (directory arguments, an effective-directory change via
`cd`/subshell, pathspec magic) rather than re-confirming only the happy
paths the PR's own tests already cover, and the enumeration plus every
standing invariant below cites the primary command run this session
inline, rather than the PR's record at its stated sha.

None of the findings above were fixed in this review session, consistent
with this role's remit (independent verification, not remediation).

## Upstream basis

canonical: `gh pr diff 2753` and `git show pr-2753:on-the-record/hooks/gate-registration-guard.sh`,
both read directly this session against branch tip `c6068dcf`. `gh issue
view 2705` output, read directly this session, for the acceptance criteria
and the explicit "must not fail-closed on unanalyzable input" constraint.
`c6068dcf:docs/issue-2705/reports/secure-coding-input-validation-injection-defense+adversarial-review-cd806f25.md`,
read to identify what the PR's own first-cut adversarial round already
covered, so this round's probes could target what it did not — not cited
as evidence for this round's own findings, which are all re-derived live
above under "What was done".

## Open findings

canonical: this record's own "What was done" section above is the live
transcript backing every item below; no separate re-derivation is needed to
restate the verdicts here.

- **Directory-add bypass** (`git add gates/`, `git add gates`) — not fixed
  here. Resolution path: extend `_pending_add_targets` to treat a
  positional argument that resolves to an existing directory as staging
  every untracked path under it (same prefix-matching approach the `.`
  case already uses).
- **`cd`/subshell path-resolution bypass** (3 variants reproduced above) —
  not fixed here. Resolution path: track an effective cwd across `cd`
  segments (including inside a `(...)` subshell scope, restored on close)
  and thread it into `_pending_add_targets` in place of the single
  top-level `cwd` from the JSON payload.
- **Pathspec-magic false-positive** (`git add . ':(exclude)gates/*'`) — not
  fixed here. Lower severity (over-block, not a silent gap) but still a
  concrete wrong answer to a parseable shape. Resolution path: either honor
  pathspec magic in `_pending_add_targets`, or treat an argument starting
  with `:(` or `!` as unresolvable (contributing zero pending targets),
  consistent with this file's existing fail-open posture on unparseable
  shapes.
- Recommend a follow-up issue for the three items above before treating
  issue #2705's underlying "gate is unreachable in a common bundled shape"
  defect class as closed — these are the same shape of silent bypass the
  original issue targets, via un-hardened parser branches this PR's own
  first round did not reach (canonical: "What was done" above, this
  session).
- The three fail-closed sibling hooks and the two advisory-only core hooks
  the PR enumerates as "affected, not fixed here" are re-derived and
  confirmed accurate below in "Enumeration re-derivation" (derived: the
  grep/wiring commands in that section, this session) — no open finding
  beyond what the PR's own record already states about them.

## Enumeration re-derivation (issue #2705 acceptance check 3)

Re-derived independently this session, not cited from the PR's record:

```
$ grep -rln "diff --cached\|--cached" on-the-record/hooks/*.sh on-the-record/hooks/*.py
on-the-record/hooks/gate-registration-guard.sh
on-the-record/hooks/requirement-digest-preflight.sh
on-the-record/hooks/live-fire-test-guard.sh
on-the-record/hooks/acceptance-command-real-run-guard.sh
on-the-record/hooks/live-fire-claim-real-run-guard.sh
on-the-record/hooks/spec-index-preflight.sh

$ grep -rln "diff --cached\|--cached" "$CLAUDE_PLUGIN_ROOT_CORE"/hooks/*.sh "$CLAUDE_PLUGIN_ROOT_CORE"/hooks/lib/*.sh
.../core/hooks/trailer-gate.sh
.../core/hooks/handbook-trigger-gate.sh

$ grep -rln '"git", "status"\|git status' on-the-record/hooks/*.sh on-the-record/hooks/*.py
on-the-record/hooks/deviation-log-guard.sh
on-the-record/hooks/gate-registration-guard.sh
on-the-record/hooks/product-capture-stopgate.sh

$ head -3 on-the-record/hooks/deviation-log-guard.sh on-the-record/hooks/product-capture-stopgate.sh
==> deviation-log-guard.sh <==     # Stop: ...
==> product-capture-stopgate.sh <== # Stop: ...
```
derived: the grep/head commands above, executed this session against
`c6068dcf`'s working tree. The two `# Stop:`-header hooks fire after the
turn, not before a pending command, so they are correctly excluded from
this PreToolUse population.

```
$ for h in requirement-digest-preflight.sh live-fire-test-guard.sh \
    acceptance-command-real-run-guard.sh live-fire-claim-real-run-guard.sh \
    spec-index-preflight.sh; do
    grep -n "\"$h\"\|script=\"$h\"" on-the-record/hooks/hooks.json on-the-record/hooks/pretooluse_dispatcher.py
  done
requirement-digest-preflight.sh: (no match)
live-fire-test-guard.sh: (no match)
acceptance-command-real-run-guard.sh: pretooluse_dispatcher.py:286: dict(script="acceptance-command-real-run-guard.sh", ...)
live-fire-claim-real-run-guard.sh: pretooluse_dispatcher.py:289: dict(script="live-fire-claim-real-run-guard.sh", ...)
spec-index-preflight.sh: pretooluse_dispatcher.py:279: dict(script="spec-index-preflight.sh", ...)
```
derived: the loop above, run this session — confirms the PR's claim of
"three fail-closed siblings wired, two dead code unwired" exactly.

```
$ grep -n "trailer-gate.sh\|handbook-trigger-gate.sh" "$CLAUDE_PLUGIN_ROOT_CORE"/hooks/pretooluse_dispatcher.py
    ("handbook-trigger-gate.sh", _setup_handbook_trigger_gate, "demote"),
    ("trailer-gate.sh", _setup_trailer_gate, "demote"),
$ grep -n "def deny" -A5 .../trailer-gate.sh .../handbook-trigger-gate.sh
trailer-gate.sh:50:    def deny(msg):
handbook-trigger-gate.sh:54:    def deny(m):
    (both bodies end in sys.stderr.write(...) + exit 0, "issue-282 DEMOTE: advisory only")
```
derived: both commands run this session — confirms the PR's "wired,
advisory-only, never blocking" characterization for both core hooks.

Population, wiring, and verdict all match the PR's own enumeration —
derived: the commands throughout this section, this session — no
discrepancy found in the enumeration itself (the one discrepancy this
session found is in the "no new bug" invariant below, not the enumeration).

## Standing invariants

1. **Role axis retirement**: no return of the retired axis.
   ```
   $ git diff 8160def4~1 c6068dcf -- on-the-record/hooks/gate-registration-guard.sh test/test_gate_registration_guard_bundled_add_commit.py | grep -ic role
   0
   ```
   derived: command above, run this session.

2. **No new bug** (failing-test-name SET vs origin/main, not counts):
   ```
   $ (fresh clone of origin/main @ e1b35a53) python3 -m pytest test/ gates/ -q
   15 failed, 419 passed, 6 xfailed

   $ (fresh clone of c6068dcf) python3 -m pytest test/ gates/ -q
   16 failed, 429 passed, 6 xfailed
   ```
   derived: both pytest runs above, executed this session on fresh clones.
   The 16-name set on `c6068dcf` is the 15-name set on `origin/main` plus
   exactly one extra name:
   `test_auto_approval_shadow_wiring.py::SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical`
   (derived: set-diff of the two pytest runs' failing-name lists, this
   session). This is one more failed / one fewer passed than the PR's own
   record claims ("byte-identical... 419 -> 430 passed"; the two pytest
   runs immediately above this session instead show 429 passed / 16
   failed).
   ```
   $ git diff --stat main...c6068dcf -- '*approval-gate*'
   (empty)
   ```
   derived: confirms this PR does not touch `approval-gate.sh` — the extra
   failure is not this PR's own code.
   ```
   $ (fresh worktree at 8160def4~1 = 00aeaae4, the PR's own base commit, predating #2746) \
     python3 -m pytest test/test_auto_approval_shadow_wiring.py -q
   1 failed, 6 passed
   FAILED test_auto_approval_shadow_wiring.py::SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical
   ```
   derived: the same failure exists at the PR's own base commit, before any
   of this PR's own diff exists (command above, this session) — confirmed
   stale-branch symptom (branch predates PR #2746's role->skill rename),
   not a regression introduced by PR #2753. Net: this PR introduces zero
   new failing test names; the PR record's "byte-identical" phrasing
   undercounts by this one pre-existing stale-branch failure, but the
   substantive claim (no new bug) holds under this independent
   re-derivation.

3. **No overhead increase**: directive bytes unchanged.
   ```
   $ du -sb on-the-record/directive   # on c6068dcf
   53162
   $ git show c6068dcf --stat | grep directive
   (no match -- on-the-record/directive not in this PR's file set)
   ```
   derived: both commands, run this session — the directive itself is
   genuinely untouched, matching the stated baseline exactly. Separately
   measured the hook's own added parse cost (this invariant's "measure the
   added parse cost" instruction, distinct from the directive-bytes check):
   ```
   $ time (echo '<plain "git commit -m x", no add>' | bash gate-registration-guard.sh)
   real 0m0.038s
   $ time (echo '<"git add x && git commit -m x">' | bash gate-registration-guard.sh)
   real 0m0.132s
   $ time (echo '<"ls -la", no git/commit>' | bash gate-registration-guard.sh)
   real 0m0.004s
   ```
   derived: three timed runs above, this session, against `c6068dcf`. The
   new code path (a `git add` segment present alongside `git`+`commit`)
   costs roughly 90 milliseconds more over the pre-existing no-add case
   (derived: 0.132s - 0.038s from the timings above), for the added `git
   status --porcelain=v1 -z --untracked-files=all` subprocess call. This is
   a real, non-trivial added cost, though correctly scoped: paid only when
   the already-narrow trigger (text containing both `git` and `commit`)
   additionally contains a `git add` segment — a non-`git` Bash call is
   unaffected (the third timing above, this session, shows a bash-level
   short-circuit before python3 starts).

4. **Monitor/watch machinery unbroken and not quieter**: confirmed
   untouched.
   ```
   $ git show c6068dcf --stat
   on-the-record/hooks/gate-registration-guard.sh                    | ...
   test/test_gate_registration_guard_bundled_add_commit.py           | ...
   docs/issue-2705/reports/secure-coding-...-cd806f25.md              | ...
   docs/issue-2705/reports/... (skill-verdict formatting fix commit)  | ...
   ```
   derived: command above, run this session — no monitor/watch-class file
   is in the full 3-commit range's file set.

## What did not work

None — this review's probes all ran to completion; nothing was attempted
and abandoned (derived: this session's own tool-call transcript).

## Next steps

None for this record itself — `loop_state: landed`, derived: all four
required directional checks plus the second adversarial round and all
standing invariants above completed this session with commands and outputs
shown inline. Recommended next step for the subject issue: open a
follow-up issue for the three open findings above (directory add,
cd/subshell path resolution, pathspec-magic false-positive), since this
session's task premise ("assume more remain") held under test.

## Skill verdicts

canonical: this session's own tool-call transcript (three `Skill` tool
invocations earlier in this session) is the source for all three verdicts
below.

- skill-verdict: adversarial-review — applied: invoked; ran a second, independent probing round against the shipped fix (not the first-cut diff the PR's own embedded round already covered), targeting shapes that round did not exercise (directory-add, `cd`/subshell path resolution, pathspec magic, `--`, quoting, globs, semicolons, a no-op add), and found 4 further live, reproducible defects (derived: "What was done" above, this session) — 3 silent-bypass, 1 false-positive — that neither the PR's own review round nor its regression suite catches.
- skill-verdict: work-in-english — applied: invoked; this record, all probe scripts, and all intermediate commands this session were written in English.
- skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived the enumeration and all four standing invariants from primary commands run this session rather than citing the PR's record at its stated sha; deliberately probed edge/negative-path shapes the PR's own first-cut round had not covered rather than treating one clean prior round as exhausting the surface; recorded the "no new bug" invariant's one discrepancy (derived: Standing invariant 2 above, this session's own pytest runs, showing 16 failed on the PR branch vs the PR's claimed 15) with the same rigor as a reproduced defect rather than smoothing it over because the underlying claim turned out correct.

other mounted skills: not triggered
