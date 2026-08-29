---
issue: 2503
role: adversarial-review+silent-failure-audit-a99512e0
author: adversarial-review+silent-failure-audit-a99512e0
skills: adversarial-review (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: true
loop_state: landed
code_under_review: 18dde3c98a644a83133c2fbf9d860788ea035cf2
type: verification
breaking: false
verdict: pass-with-open-finding
upstream:
  - path: docs/issue-2503/reports/requirements-quality+silent-failure-audit-932487ab.md
    sha: 18dde3c98a644a83133c2fbf9d860788ea035cf2
    note: PR #2702's own record; untracked on this branch (PR #2702 not yet merged), cited by <sha>:<path>
  - path: on-the-record/hooks/gate-registration-guard.sh
    sha: 18dde3c98a644a83133c2fbf9d860788ea035cf2
    note: pre-existing, unmodified file — present on this branch too; content read at PR #2702's tip in a scratch clone
  - path: docs/specs/enforcement-boundary.md
    sha: 18dde3c98a644a83133c2fbf9d860788ea035cf2
    note: row cited is untracked on this branch (PR #2702 not yet merged); the file itself pre-exists here, read in a scratch clone
  - path: gates/forbidden_action_rule.py
    sha: 95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9
    note: untracked on this branch (neither PR #2696 nor PR #2702 merged yet), read in a scratch clone
---

# issue-2503 — adversarial-review+silent-failure-audit-a99512e0 record

## What was done

Independently verified PR #2702 ("issue-2503: register forbidden_action_rule.py
+ disclose registration-guard hole") in a fresh clone, re-deriving all three
assigned claims from raw commands rather than trusting the PR's own record.
#2503's own two Acceptance bullets and both live demonstrations were already
independently verified by PR #2701 (merged) and are not redisputed here, per
the task's own scope instruction.
canonical: fresh clone (`git clone https://github.com/tokenmaxxxer/on-the-record.git /tmp/verify-2702`,
`git fetch origin pull/2702/head:pr2702`) — this session's own transcript.

### Cherry-pick fidelity — confirmed unmodified

`gates/forbidden_action_rule.py` (untracked on this branch) and
`on-the-record/directive/acceptance-format.md` (present, unmodified on
this branch) were diffed against PR #2696's commit in the scratch clone.
derived: `git diff 95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9 pr2702 -- gates/forbidden_action_rule.py`
(untracked on this branch) and
`git diff 95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9 pr2702 -- on-the-record/directive/acceptance-format.md`
(this session, scratch clone) — result: both empty (no output). Confirms
PR #2696's commit `95d3b42b` was cherry-picked byte-identical; PR #2701's
already-merged verification of these two files' content is not
redisputed.

### Claim 1 (root-cause) — Present, reproduced both directions live

The PR claims `gate-registration-guard.sh` reads `git diff --cached
--name-status` from a PreToolUse hook, so a bundled `git add X && git
commit` has nothing staged when the hook fires and passes silently, while
the same file staged in a prior call then committed separately is
correctly refused.

Read the hook end to end (present, unmodified, on this branch too) and
confirmed the mechanism:
canonical: `on-the-record/hooks/gate-registration-guard.sh:116-124` —
```
try:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        capture_output=True, text=True, timeout=20, cwd=repo_root,
    )
```
and `:174` (`if not targets: sys.exit(0)`) — the fail-open branch that
fires when nothing is staged yet.

Reproduced live with a throwaway, untracked gate module
(`gates/repro_2705_check.py` — created only in the scratch clone, never
staged for real registration, deleted after the test, never committed to
any branch), simulating PreToolUse's actual firing point — before the
Bash call's own command text executes.

Bundled shape — hook fired with nothing staged yet:
```
$ git diff --cached --name-status
(empty)
$ echo "$PAYLOAD" | ./on-the-record/hooks/gate-registration-guard.sh
EXIT CODE (bundled, hook fired BEFORE staging): 0
```
derived: this session's own command — payload
`{"tool_name":"Bash","tool_input":{"command":"git add gates/repro_2705_check.py && git commit -m \"repro bundled\""}}`
piped into the hook — exit 0, no stderr. Passes silently, exactly as
claimed.

Unbundled shape — file staged in a prior call, hook fired for the
following commit-only call:
```
$ git add gates/repro_2705_check.py
$ git diff --cached --name-status
A	gates/repro_2705_check.py
$ echo "$PAYLOAD" | ./on-the-record/hooks/gate-registration-guard.sh
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/repro_2705_check.py: no row in docs/specs/enforcement-boundary.md
Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also docs/specs/generated-paths.md), then retry the commit.
EXIT CODE: 2
```
derived: same method — payload
`{"tool_input":{"command":"git commit -m \"repro unbundled\""}}` — exit 2,
correctly refused.

**Verdict on claim 1: Present.** The mechanism is exactly as the PR
describes; issue #2705 (filed on this basis) is correctly scoped to it —
this is not a broader bug in the guard's logic, only in the shape that
reaches it.

### Claim 2 (enforcement-boundary.md row) — Present

canonical: `docs/specs/enforcement-boundary.md:100` (this row is
untracked on this branch — PR #2702 not yet merged — read in the scratch
clone) — the added row carries the same shape as the immediately
preceding sibling row (`acceptance_authoring_rule.py`, line 99, present
on this branch): `repo-local` classification, standalone-CLI note, and
the literal phrase "same not-yet-reachable class as
`acceptance_authoring_rule.py` and `artifact_smoke_rule.py` above" — not
a new format.

Ran the guard the *unbundled* way against `gates/forbidden_action_rule.py`
itself (untracked on this branch, read in the scratch clone — the
sibling gate this row registers, not the claim-1 throwaway) to confirm
the row satisfies the guard's own parser, not merely that a row was
added. `git reset --soft HEAD~1` on `pr2702` in the scratch clone, then
re-staged only `gates/forbidden_action_rule.py` (untracked on this
branch) alone (simulating the "add" half of the unbundled shape) while
`docs/specs/enforcement-boundary.md`'s row existed only on disk —
unstaged — exercising `read_spec`'s disk-fallback path:
```
$ git diff --cached --name-status
A	gates/forbidden_action_rule.py
$ echo "$PAYLOAD" | ./on-the-record/hooks/gate-registration-guard.sh
EXIT CODE (unbundled second call, row present on disk): 0
```
derived: this session's own commands (`git reset --soft HEAD~1`,
`git reset HEAD -- .`, `git add gates/forbidden_action_rule.py` —
untracked on this branch — then hook fired with a commit-only payload)
— exit 0, no denial. Confirms the
row's text actually satisfies `recorded_names()`'s `_ROW_RE` parser
against `docs/specs/enforcement-boundary.md`'s table, not only that text
exists in the file.

**Verdict on claim 2: Present.**

### Claim 3 (disclosed dispositions) — Present, with one citation defect

Both dispositions appear in PR #2702's own record (untracked on this
branch, cited by `<sha>:<path>` from `18dde3c9`) with stated reasoning,
not silently carried.

**`_ROLE_REASSIGNED` word-presence exemption — deferred, not fixed.**
Reproduced all five cases myself, independent of the PR's own run
(network-free, `check_issue_body` — a function `gates/forbidden_action_rule.py`
(untracked on this branch) defines — called directly against
`## Acceptance`-headed bodies):
```
positive (2479 R3): ["issue #2479's 'Acceptance' bullet requires an action the delivering role is forbidden from taking (...)"]
negative (compliant rewrite): []
negative (mention-only): []
gap1 (bare operator mention): []          # wrongly exempts
gap2 (user should file): ["issue #2503's 'Acceptance' bullet requires an action..."]   # wrongly blocks
```
derived: `python3 -c "from gates.forbidden_action_rule import check_issue_body; ..."`
(this session, scratch clone, `pr2702` checkout) — all five outputs match
the PR's own claimed reproductions.

Whether the deferral reason holds: #2503's own Acceptance bullet 2
(verbatim, from this task's spawning prompt) requires demonstration
"against #2479's original R3 text as the positive case and against a
compliant rewrite as the negative case," with a `must not:` restricted to
"block an issue whose bullet merely mentions an issue number or links
one." Neither clause requires the gate to correctly classify arbitrary
non-orchestrator reassignment phrasing ("the user should file") or
reject a bare "operator" mention with no causal link — those are
robustness gaps beyond #2503's own literal Acceptance text, not a
narrowing of what the issue asked for. The deferral's framing holds.
canonical: #2503's Acceptance bullet 2, as quoted verbatim in this task's
spawning prompt — `gh issue view 2503` (this session) reproduces the
identical text.

**Test coverage — declined per #2137 + sibling precedent.** No dedicated
test module exists for `gates/forbidden_action_rule.py` (a module that
is itself untracked on this branch):
```
$ find . -iname "*forbidden_action_rule*"
./gates/forbidden_action_rule.py
./gates/__pycache__/forbidden_action_rule.cpython-310.pyc
```
derived: this session, scratch clone, `pr2702` checkout — no test
module with a name resembling `forbidden_action_rule` exists anywhere in
that tree.

Nodeid-level diff confirms zero test-suite change: `origin/main` and
PR #2702's branch collect the identical node set under `-m "not slow"`.
```
$ diff main_nodeids.txt pr2702_nodeids.txt
(empty)
$ wc -l main_nodeids.txt pr2702_nodeids.txt
399 main_nodeids.txt
399 pr2702_nodeids.txt
```
derived: `python3 -m pytest --collect-only -q -m "not slow" test/` run
separately against a `git worktree add` of `origin/main` and against the
`pr2702` checkout, both piped through `grep -E "^test/" | sort`, then
diffed — this session, both collections executed live and produced an
identical count on each side. (A full `pytest test/` run was not
attempted, per this machine's known >2min timeout today; collection-only
needs no test execution and is sufficient for a nodeid-level diff.)

**Citation defect found.** PR #2702's record cites
`find . -iname "*acceptance_authoring_rule*" -o -iname "*artifact_smoke_rule*" -path "*/test/*"`
with "result: no matches for either sibling." Run verbatim against
`gates/acceptance_authoring_rule.py` (present on this branch), this
command does not return empty:
```
$ find . -iname "*acceptance_authoring_rule*" -o -iname "*artifact_smoke_rule*" -path "*/test/*"
./gates/acceptance_authoring_rule.py
```
derived: this session, scratch clone, `pr2702` checkout, exact command
copied from the PR's record — one match, not zero. Cause: `find`'s `-o`
binds `-path "*/test/*"` only to the second alternative
(`artifact_smoke_rule`), not the first (`acceptance_authoring_rule`), so
the first branch is unrestricted and matches the gate's own source file.
A precedence-corrected form
(`find . -path "*/test/*" \( -iname "*acceptance_authoring_rule*" -o -iname "*artifact_smoke_rule*" \)`)
does return empty, so the *substantive* claim (neither sibling gate has
a dedicated test file) still holds independently — but the record's own
literal `derived:` command does not reproduce the result it cites.

**Verdict on claim 3: Present** for the substance of both dispositions
and their reasoning; **one open citation defect** in the test-coverage
disposition's `derived:` line (does not undercut the underlying finding,
but the command-and-result pair as written does not reproduce).

## Why

Methodology: fresh clone, re-derive every command from scratch rather
than re-running the PR's own transcript verbatim, per this task's
instruction to distinguish "I executed this" from "I read this." All
assigned claims reproduce as stated except one citation-level defect
inside claim 3's test-coverage disposition (the `find` command's stated
result does not match its actual output). That defect is a
documentation-accuracy gap, not a correctness gap in the deliverable
itself — the row lands, the guard's mechanism is as described, and the
underlying "no sibling test file" claim is independently true when
checked with a precedence-corrected command. `pass-with-open-finding`
reflects that split: approve the deliverable, flag the one citation to
fix.

adversarial-review skill applied: this entire session is structured as a
blind-to-intent, structurally independent evaluation of PR #2702's
claims — re-deriving from raw commands rather than accepting the PR's or
its own record's stated results, exactly the protocol's core mechanism.

silent-failure-audit skill applied: claim 1's mechanism is itself a
silent-failure shape — `gate-registration-guard.sh`'s `targets = []` /
`sys.exit(0)` branch (line 174, cited above) is indistinguishable, from
any downstream artifact, from "checked and found nothing wrong." The
audit's classification vocabulary (Silently Absorbed: continues as if
the operation succeeded, with no indication that it didn't) applies
directly to this hook's fail-open branch in the bundled-command shape,
and is the same framing issue #2705 uses to scope its own acceptance
criteria.
canonical: `on-the-record/hooks/gate-registration-guard.sh:174` (cited
above, same section as its reproduction).

skill-verdict: adversarial-review — applied: invoked; framed the whole
session as a blind-to-intent, structurally independent re-derivation of
PR #2702's claims from raw commands rather than trusting its own record
skill-verdict: silent-failure-audit — applied: invoked; classified
`gate-registration-guard.sh`'s nothing-staged fail-open branch
(line 174) as a Silently-Absorbed-shaped gap in claim 1's analysis above
skill-verdict: work-in-english — applied: invoked; this record, its
commit message, and its PR body are written in English per policy
skill-verdict: implementation-audit — applied: invoked; treated this
session as the two-session protocol's evaluator half, classifying
PR #2702's three pre-extracted claims (Present/Present/Present-with-defect)
against raw reproduction, independent of the builder's stated intent

## What did not work

`git reset --soft HEAD~1` in the scratch clone, used to isolate claim 2's
unbundled test, incidentally moved that clone's local `pr2702` branch ref
back to `origin/main`'s tip (branch pointers move with whichever commit
HEAD is reset to while checked out on that branch). Harmless — the clone
is a `/tmp` scratch copy never pushed anywhere — but required
re-fetching and re-checking-out PR #2702's tip before continuing.
derived: `git fetch origin pull/2702/head -q && git checkout --detach FETCH_HEAD -q && git log --oneline -1`
(this session, scratch clone) — result: `18dde3c9 issue-2503: register forbidden_action_rule.py, disclose guard-registration hole and lower-severity dispositions`,
confirming the scratch clone was restored to PR #2702's actual tip
before the claim 3 reproductions. No effect on the actual PR, its
branch, or this repository — the scratch clone was never pushed.

## Upstream basis

- PR #2702 (branch `issue-2503/requirements-quality+silent-failure-audit-932487ab`),
  commit `18dde3c98a644a83133c2fbf9d860788ea035cf2` — this record's
  subject.
- PR #2701 (merged), commit `4ccc4919f02c5b00b406139e46660b3a445c1ece` —
  independent verification of PR #2696; its Acceptance-bullet and
  live-demonstration findings are relied on, not redone, per this task's
  own scope note.
  canonical: `gh pr view 2701 --json state,mergedAt` (this session) —
  `{"state":"MERGED", ...}`.
- PR #2696, commit `95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9` —
  cherry-pick source, diffed empty against `pr2702`'s copy of the same
  two files (above).
- Issue #2705 — filed on claim 1's root-cause finding; this record's
  independent reproduction supports its scoping as written.
  canonical: `gh issue view 2705` (this session).

## Open findings

1. PR #2702's record contains a `derived:` citation
   (test-coverage disposition, the `find ... -path "*/test/*"` command)
   whose literal output does not match the "no matches for either
   sibling" result stated for it — see Claim 3 above for the full
   reproduction and cause (an `-o`/`-path` precedence gap in the find
   invocation). The underlying substantive claim (neither sibling gate
   has a dedicated test file) is independently true; only the cited
   command-and-result pair needs correcting. Resolution path: fix the
   `find` grouping (`-path "*/test/*" \( -iname ... -o -iname ... \)`)
   or reword the stated result to describe the actual match. Named here
   per #2503's own sanctioned wording — this role cannot file a tracked
   follow-up; the orchestrator names one if wanted.

## Next steps

None pending.
