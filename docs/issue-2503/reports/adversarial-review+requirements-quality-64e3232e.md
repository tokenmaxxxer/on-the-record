---
issue: 2503
role: adversarial-review+requirements-quality-64e3232e
author: adversarial-review+requirements-quality-64e3232e
skills: adversarial-review (skill-repository(297e350)), requirements-quality (skill-repository(297e350))
verifies_subject: true
loop_state: landed
code_under_review: 95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9
type: verification
breaking: false
verdict: fix-before-merge
upstream:
  - path: docs/issue-2503/reports/requirements-quality-112361d7.md
    sha: same-commit
    note: not present in this branch's working tree — cited by <sha>:<path> from PR #2696 (95d3b42b), untracked on this branch
---

# issue-2503 — adversarial-review+requirements-quality-64e3232e record

## What was done

Independently verified PR #2696 ("issue-2503: acceptance-format
role-forbidden-action rule + authoring gate") — a fresh clone
(`git clone https://github.com/tokenmaxxxer/on-the-record.git /tmp/verify-2696-2660037`,
`git fetch origin pull/2696/head:pr-2696`), re-deriving every claim from
raw commands, not inherited from the PR's own record.
canonical: this session's own tool-call transcript (fresh clone + fetch,
verified above in-session).

### Scope fit — Present, both Acceptance bullets satisfied

acceptance: `git diff main...pr-2696 -- on-the-record/directive/acceptance-format.md`
(fresh clone) — result: adds a "ROLE-FORBIDDEN ACTION (issue #2503,
#2479 R3)" bullet stating the rule and the sanctioned wording "name the
follow-up with a drafted body in `## Open findings`; the orchestrator
files it." Matches #2503 Acceptance bullet 1 verbatim.

acceptance: `python3 gates/forbidden_action_rule.py 2479` (fresh clone,
pr-2696 checked out) — result:
```
gate blocked:
  - issue #2479's 'Acceptance' bullet requires an action the delivering role is forbidden from taking ("- check: state explicitly whether the gates' own refusal-message detail was found sufficient to self-correct from without the new directive text — if insufficient, file that as a separate follow-up issue and link it here rather than expanding this issue's scope.")
```
exit 1. Reproduces #2503 Acceptance bullet 2's positive-case claim
independently (I ran the command myself; I did not copy this output from
the PR record).

acceptance: `python3 -c "..."` importing `check_issue_body` (this
session, fresh clone) against a compliant-rewrite body I authored myself
("name the follow-up with a drafted body in `## Open findings`; the
orchestrator files it.") — result: `[]`. Against a mention-only body I
authored myself ("see issue #2501 and #2502 for the filed items.") —
result: `[]`. Both negative cases reproduce bullet 2's negative-case
claim, with fixtures independent of the PR record's own fixtures.

Verdict on scope fit: the diff satisfies #2503's Acceptance text as
written, and both live demonstrations reproduce with independently
authored fixtures — this is not a smoke-test session reaching for a
convenient PR, the diff maps onto the two Acceptance bullets directly.

### Gate robustness — two reproducible gaps, non-blocking for #2503's own text

canonical: `95d3b42b:gates/forbidden_action_rule.py`'s `_ROLE_REASSIGNED`
regex (`orchestrator|\boperator\b|\bhuman\b|non-role|...|the user files
|filed by`) — a bare word/phrase match within a 200-char window, not a
causally-attributed check.

derived: `check_issue_body` (this session) against a body I authored,
`"- check: someone will file this as a follow-up issue; ask the operator
about timing separately in this window."` — result: `[]` (passes) even
though "operator" is not the actual filer in that sentence, just a
nearby word.

derived: `check_issue_body` (this session) against a body I authored,
`"- check: the user should file this as a follow-up issue once
reviewed."` — result: non-empty (blocked), even though reassigning the
action to "the user" is exactly the "non-role account" exemption
`95d3b42b:on-the-record/directive/acceptance-format.md`'s new prose
promises — the regex only recognizes the fixed phrase "the user files"
(present tense), not "the user should/will file."

These are real gaps between the directive's promised exemption scope and
the regex's actual coverage, but #2503's own Acceptance text only
requires the orchestrator-reassignment case to work, and that case does
work (shown above) — so this does not fail #2503's stated criteria; it
is a quality gap in the delivered gate itself.

### Wiring — orphan, matching sibling pattern, but NOT registered like its siblings

derived: `grep -rn "forbidden_action_rule" gates/ci.py spawn.py
on-the-record/hooks/*.sh` (fresh clone, pr-2696) — result: no matches.
Not wired into `gates/ci.py`'s check graph or any hook preflight — same
reachability class as `gates/acceptance_authoring_rule.py` and
`gates/artifact_smoke_rule.py`. The PR's own record makes this same
claim; I independently confirm it rather than correct it.

canonical: `docs/specs/enforcement-boundary.md`'s own header (this
branch, current working tree) — "Every `gates/*.py` module... must have
a row below with a recorded verdict." Both sibling gates
(`acceptance_authoring_rule.py`, `artifact_smoke_rule.py`) have rows
there recording a not-yet-reachable verdict.

derived: `git diff main...pr-2696 --stat` (fresh clone) — result: three
files changed (`95d3b42b:docs/issue-2503/reports/requirements-quality-112361d7.md`,
`95d3b42b:gates/forbidden_action_rule.py`, `95d3b42b:on-the-record/directive/acceptance-format.md`).
`docs/specs/enforcement-boundary.md` is not among them —
`95d3b42b:gates/forbidden_action_rule.py` has zero row there, unlike its
two named siblings.

**This is not just a missed doc update.** This branch's own working tree
carries a live PreToolUse hook, `on-the-record/hooks/gate-registration-guard.sh`,
that predates PR #2696 (present at commit e1f9cb5f, the PR's merge-base;
its `is_gate_module()` function, which already scopes new `gates/*.py`
files, is unchanged by the PR — checked via
`git show e1f9cb5f:on-the-record/hooks/gate-registration-guard.sh | grep -n "def is_gate_module" -A8`
against the fresh clone). I reproduced its refusal live, in this actual
session, against this actual branch: staging a throwaway
`gates/_scratch_registration_test.py` (untracked scratch file, created
and removed within this same turn, never committed) and running
`git commit` was refused on the spot with:
```
PreToolUse:Bash hook error: [.../on-the-record/hooks/pretooluse-dispatcher.sh]: gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/_scratch_registration_test.py: no row in docs/specs/enforcement-boundary.md
```
I then removed the scratch file (`git reset HEAD` + `rm`) without
committing it — it was a live-fire probe of the hook, not delivered
work.

derived: `grep -n "CORE_BUILD_NOW" on-the-record/hooks/approval-gate.sh
on-the-record/hooks/pr-preflight.sh` (this branch) — result: matches
only in `approval-gate.sh` (bypasses the phase-2 approval wait) and
`pr-preflight.sh` (treats the branch as phase-2-equivalent). No match in
`gate-registration-guard.sh` — `CORE_BUILD_NOW=1`, which PR #2696's own
record cites as its build-now bypass, does not touch this hook.

I cannot determine, from a fresh-clone re-derivation alone, why the
delivering session's commit 95d3b42b (adding
`95d3b42b:gates/forbidden_action_rule.py` with no boundary row) was not
refused by this same hook — that requires that session's own transcript
and hook configuration, which this verification does not have access
to. What I can state as executed-live fact: the identical commit shape,
run in my own session against this repository today, is refused. If PR
#2696 merges as-is, the result is a `gates/*.py` module the repository's
own registration contract requires a row for, with none present.

### Test-suite effect — Present, no regression

A full `pytest test/` run did not complete within a 2-minute timeout on
either branch in this environment (matches the task brief's stated
warning); `-m "not slow"` completed quickly on both.

acceptance: `python3 -m pytest test/ -m "not slow" -q` on `pr-2696`
(fresh clone) — result:
```
15 failed, 380 passed, 4 xfailed in 2.94s
```

acceptance: same command on `main` (same fresh clone, checked out back
to `main`) — result:
```
15 failed, 380 passed, 4 xfailed in 2.63s
```
derived: diffing the two runs' `FAILED` nodeid lists (this session,
compared by eye against both captured outputs) — the 15 failing nodeids
are byte-identical between `main` and `pr-2696`, all raising
`fatal: 'origin' does not appear to be a git repository` inside
`bootstrap_fetch_and_record_sha` — a fresh-clone sandbox artifact (no
real `origin` remote wired for those tests' subprocess fixtures),
present on `main` before this PR touches anything, not caused by this
diff.

derived: `find . -iname "*forbidden_action*" -path "*/test/*"` (fresh
clone, pr-2696) — result: no matches — no test module exists for the
new gate; its only executed coverage is the manual CLI/`check_issue_body`
demonstrations (both the PR record's and this record's).

## Why

`adversarial-review` applies directly: the builder session
(`requirements-quality-112361d7`, PR #2696) is not positioned to catch
the enforcement-boundary.md gap in its own commit — its record correctly
reports the orphan/not-wired status (a claim I independently confirmed
above) but never checks that same commit against the registration
contract it was, per the live hook reproduced above, subject to. A
structurally independent session re-deriving from a fresh clone is the
right tool, which is what this record does.

`requirements-quality` was judged not applicable to this verification
task. canonical: #2503's own Acceptance bullets (`gh issue view 2503`,
read this session) are this repository's own `check:`/`must not:`
format — no trigger/response clause (ruling out EARS) and no
role/goal/benefit clause (ruling out Connextra/QUS).
derived: manual check of #2503's Acceptance text against both
templates' required clauses (this session) — result: neither template's
required clause shape is present in either bullet. Forcing either
template onto them would produce a syntactically-templated but
semantically empty result, which the skill's own "does this even need
the procedure?" routing exists to avoid. The PR author's record reaches
the same not-applicable verdict for the build task; I checked the
bullets' shape myself rather than inheriting that conclusion.

## What did not work

None in this verification session's own process — no dead end, no
retried approach.
canonical: this session's own transcript (fresh clone, live gate runs,
live hook reproduction, paired pytest runs, all completed on first
attempt as shown under "What was done" above) — every step executed
cleanly; the enforcement-boundary.md gap recorded under Open findings is
a defect found *in the subject under review*, not a failed step in this
session's own process.

## Upstream basis

- PR #2696's own record, `95d3b42b:docs/issue-2503/reports/requirements-quality-112361d7.md`
  (not present in this branch's working tree; read via `gh pr view
  2696` / the fresh clone). Read for its claims; every claim it made was
  independently re-derived above, none inherited as-is.
- PR #2696 diff: `main...pr-2696` in a fresh clone of
  `tokenmaxxxer/on-the-record` (this session) —
  `95d3b42b:gates/forbidden_action_rule.py`,
  `95d3b42b:on-the-record/directive/acceptance-format.md`.
- `on-the-record/hooks/gate-registration-guard.sh` at commit e1f9cb5f
  (PR #2696's merge-base, unmodified by the PR) — the live registration
  hook, reproduced against this PR's exact commit shape in this
  session's own working tree.

## Open findings

1. `95d3b42b:gates/forbidden_action_rule.py` has no row in
   `docs/specs/enforcement-boundary.md`, contradicting that file's own
   completeness requirement and inconsistent with the two sibling gates
   it claims the same reachability class as (both of which do have
   rows). Fix: add a row (same not-yet-reachable verdict shape as
   `acceptance_authoring_rule.py`'s row) before merge. Named here per
   #2503's own sanctioned wording — this role cannot file issues; if a
   tracked follow-up beyond a same-PR fix is wanted, the orchestrator
   names one.
2. `_ROLE_REASSIGNED`'s exemption is word-presence-in-a-window, not
   causally attributed, and does not recognize "the user will/should
   file" phrasing despite the directive text's "a non-role account"
   promise. Lower severity than finding 1 — #2503's own Acceptance text
   only requires the orchestrator-reassignment case, and that case does
   work. Named as a follow-up candidate, not filed, same reason as
   finding 1.
3. No automated test module exists for `95d3b42b:gates/forbidden_action_rule.py`
   (checked: `find . -iname "*forbidden_action*" -path "*/test/*"`, no
   matches) — its only verification is manual CLI/function invocation,
   in both the PR's record and this one. Named as a follow-up candidate,
   not filed.

## Next steps

Findings 1-3 above are named for the orchestrator to route (fold into a
same-PR fix, file as tracked follow-ups, or accept as-is) — this role
cannot file issues itself, per #2503's own sanctioned wording. Nothing
further pending from this verification session itself.
derived: this session's full command transcript above (fresh-clone diff,
live gate runs, live hook reproduction, paired pytest runs) is the
executed-live basis for `loop_state: landed` — no step remains
unexecuted.

skill-verdict: adversarial-review — applied: invoked; used as the
structural frame for this whole verification (fresh clone, re-derive
every claim, do not inherit PR #2696's record's conclusions) — the
enforcement-boundary.md gap (Open finding 1) is exactly the kind of
self-review blind spot the skill predicts a builder session misses, and
did miss here.
skill-verdict: requirements-quality — not-applicable: #2503's Acceptance
bullets are this repo's own `check:`/`must not:` format, not EARS system
requirements or Connextra/QUS user stories (checked directly against
both templates' required clauses, see "Why" above) — independently
confirmed, not inherited from the PR record's identical verdict.
