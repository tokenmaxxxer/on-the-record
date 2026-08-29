---
issue: 2503
role: requirements-quality+silent-failure-audit-932487ab
author: requirements-quality+silent-failure-audit-932487ab
skills: requirements-quality (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: PR #2696 (branch issue-2503/requirements-quality-112361d7)
    sha: 95d3b42b62f7d16f2b9a4362435b3bc1619a2bc9
  - path: docs/issue-2503/reports/adversarial-review+requirements-quality-64e3232e.md
    sha: 4ccc4919f02c5b00b406139e46660b3a445c1ece
  - path: docs/specs/enforcement-boundary.md
    sha: same-commit
---

# issue-2503 — requirements-quality+silent-failure-audit-932487ab record

## What was done

This is the send-back fix for PR #2696, per PR #2701's independent
verification (merged, `verdict: fix-before-merge`).

1. Cherry-picked PR #2696's commit `95d3b42b` (the `on-the-record/directive/acceptance-format.md`
   ROLE-FORBIDDEN ACTION bullet and `gates/forbidden_action_rule.py`)
   onto this branch, unmodified. #2503's own two Acceptance bullets and
   both live demonstrations (positive case against #2479's original R3,
   negative cases against a compliant rewrite and a mention-only bullet)
   were already independently reproduced by PR #2701 and are not
   redone here — re-reproduced only as evidence for the disposition
   decisions below.
   canonical: `docs/issue-2503/reports/adversarial-review+requirements-quality-64e3232e.md`
   (merged at `4ccc4919`) — "Scope fit: both of #2503's Acceptance
   bullets are satisfied by the diff, and both live demonstrations ...
   reproduce independently."
2. Added the missing row for `gates/forbidden_action_rule.py` to
   `docs/specs/enforcement-boundary.md` — the blocking item from PR
   #2701's verification.
3. Investigated why `gate-registration-guard.sh` — which predates PR
   #2696 and is byte-identical between commit time and now — did not
   refuse commit `95d3b42b`'s addition of an unregistered `gates/*.py`
   module. Root cause found and reproduced live (below): a genuine gate
   hole, not an environmental gap.
4. Disclosed disposition on the two lower-severity findings from PR
   #2701's verification (`_ROLE_REASSIGNED` word-presence exemption,
   zero test coverage) rather than carrying them silently.

## Why

### The blocking item

`gates/forbidden_action_rule.py`'s two named siblings
(`acceptance_authoring_rule.py`, `artifact_smoke_rule.py`) both carry a
row in `docs/specs/enforcement-boundary.md` recording the same
not-yet-reachable verdict; the new gate had none.
canonical: `docs/specs/enforcement-boundary.md` (this commit's diff) —
new row for `forbidden_action_rule.py`, same "repo-local ... same
not-yet-reachable class as `acceptance_authoring_rule.py` and
`artifact_smoke_rule.py`" wording pattern as the two siblings' own rows.

Attempted `python3 gates/spec_index.py --update` (the standing
docs/specs/* commit obligation) after the row edit; it crashes on an
unrelated, pre-existing gap:
```
FileNotFoundError: [Errno 2] No such file or directory:
'.../roles/specs/brand-design.spec.json'
```
derived: `python3 gates/spec_index.py --update` (this session, this
branch, after the row edit) — result: traceback above. Same command
re-run via `git stash` back to this branch's clean HEAD (`4ccc4919`,
before any of this session's edits) — result: identical traceback,
identical missing path — confirms this is pre-existing repo state, not
something this change introduced. `docs/specs/reconciled-index.md` is
left unregenerated for that reason, not a silent skip.

### The guard hole — root cause found, reproduced live

`on-the-record/hooks/gate-registration-guard.sh` is the PreToolUse
Bash hook (wired into `on-the-record/hooks/pretooluse_dispatcher.py`'s
`GATES` list, confirmed present there both now and at the branch's
merge-base) that is supposed to refuse exactly this shape: a newly
staged `gates/*.py` file with no row in
`docs/specs/enforcement-boundary.md`.
derived: `diff <(git show e1f9cb5f:on-the-record/hooks/gate-registration-guard.sh) on-the-record/hooks/gate-registration-guard.sh`
and the same command for `pretooluse_dispatcher.py` (this session,
run against this repo's own git history and this branch's marketplace
plugin checkout) — both report no differences: the guard's logic at
commit `95d3b42b`'s merge-base (`e1f9cb5f`, the branch's parent) is
byte-identical to today's, ruling out "the check itself was buggy then
and got fixed since."

The original build session's own session log is a plain file on this
machine's disk (path:
/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2503-requirements-quality-112361d7.session.20260829T153621.2584880.log
— not a repo-tracked path, so not backtick-cited as one). I read it
directly this session. It records the exact Bash tool call that
produced commit `95d3b42b`:
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2503-requirements-quality-112361d7
git add on-the-record/directive/acceptance-format.md gates/forbidden_action_rule.py
git status --short
git commit -m "issue-2503: acceptance-format role-forbidden-action rule + authoring gate" -m "..."
git log -1 --format=%H
```
derived: reading that session log file directly (this session, line
188-190 of that log by its own internal line numbering) — the tool
result shows the commit succeeding with no PreToolUse denial of any
kind, while the same log shows PreToolUse:Bash hook denials firing
correctly for *other* commands later in that same session
(`heredoc-command-refusal-gate` on a `gh pr create --body <heredoc>`
call at that log's line 234, `pr-preflight` on a `gh pr create` missing
its trailer at line 241) — so the dispatcher was active and running
for Bash calls throughout that session; this one specific gate simply
did not fire for this one call.

The reason is in the guard's own check order:
```python
r = subprocess.run(
    ["git", "diff", "--cached", "--name-status"],
    capture_output=True, text=True, timeout=20, cwd=repo_root,
)
```
canonical: `on-the-record/hooks/gate-registration-guard.sh:116-120`.
This runs synchronously inside the PreToolUse hook, which fires
*before* the Bash tool's command text executes — not after. The
build session's `git add ... && git commit ...` was one multi-line
command passed to a single Bash tool call, so at the moment this check
ran, `git add` had not executed yet: nothing was staged, `git diff
--cached --name-status` returned empty, `added` was `[]`, `targets`
was `[]`, and the guard exited 0 with nothing to check — the commit
then proceeded and the addition of `gates/forbidden_action_rule.py`
never entered the guard's field of view at all.

Reproduced live, in this session, against this same branch and this
same hook, twice:
- **Bundled shape (matches the miss):** `git add
  gates/_scratch_hole_probe.py` followed by `git commit -m ...` in the
  *same* Bash tool call — committed cleanly, no denial, no output from
  `gate-registration-guard` at all. (The resulting scratch commit was
  then undone with `git reset --soft HEAD~1` before any further work —
  it carried no real change.)
- **Split shape (control):** the identical new file staged with `git
  add` in one Bash tool call, then `git commit -m ...` as a *separate*
  Bash tool call — refused:
  ```
  PreToolUse:Bash hook error: [.../on-the-record/hooks/pretooluse-dispatcher.sh]: gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
  gates/_scratch_hole_probe.py: no row in docs/specs/enforcement-boundary.md
  Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also docs/specs/generated-paths.md), then retry the commit.
  ```
  (This second attempt was refused before executing, so nothing needed
  reverting — `git status` afterward showed the file untracked with no
  new commit.)

acceptance: this session's own two commands above — result: bundled
`git add && git commit` in one Bash call passes silently; the split
form (`git add` in a prior Bash call, `git commit` in a following one)
is refused by `gate-registration-guard` with the message shown. Same
hook, same branch, same file shape, opposite outcomes — the only
variable is whether `git add` and `git commit` share a Bash
invocation.

**Verdict: a real hole in `gate-registration-guard.sh`, not an
environmental gap.** The guard's own code was present, current, and
firing correctly for other checks throughout the original build
session — it inspects the *already-staged* diff, which is a snapshot
of state a Bash call has not yet had the chance to change when the
hook runs. Bundling `git add` and `git commit` in the same call is not
a rare or careless pattern here — it is this repository's own
documented landing guidance (issue #2135: "run the landing sequence as
ONE composite Bash call"). That guidance and this guard's blind spot
point in exactly opposite directions for a newly-added gate/hook
module.

Per this task's own scope instruction, the guard itself is not touched
in this PR — landing the missing row is the fix in scope here. Naming
the follow-up per #2503's own sanctioned wording (this role cannot
file issues): **gate-registration-guard.sh's staged-diff check should
additionally parse the about-to-run command text for `git add
<path>` targets when `git add` and `git commit` are tokens in the same
invocation, not only `git diff --cached`'s pre-execution snapshot** —
the orchestrator files this if a tracked follow-up is wanted.

### `_ROLE_REASSIGNED` exemption — deferred, not fixed here

Reproduced both gaps PR #2701 found, independently, in this session:
```
>>> check_issue_body(2503, "- check: someone will file this as a follow-up issue; ask the operator about timing separately in this window.")
[]
>>> check_issue_body(2503, "- check: the user should file this as a follow-up issue once reviewed.")
["issue #2503's 'Acceptance' bullet requires an action the delivering role is forbidden from taking ..."]
```
derived: `python3 -c` importing `check_issue_body` directly (this
session) — both results as shown: the first (a bare "operator" mention
with no causal link to the filing) wrongly exempts; the second ("the
user should file", exactly the kind of non-role-account reassignment
`95d3b42b:on-the-record/directive/acceptance-format.md`'s new prose
promises an exemption for) wrongly blocks.

**Disposition: deferred, not fixed in this PR.** #2503's own Acceptance
text requires only that the orchestrator-reassignment case work, and
it does (reproduced above and by PR #2701). Both gaps here stem from
the same root design choice — word/phrase presence in a window, not
causal attribution — and fixing either half properly means either (a)
real causal-attribution logic (out of scope for a narrow authoring-time
regex gate, and this repo's own precedent for these gates is
deliberately narrow triggers over broader ones, per
`acceptance-format.md`'s NEGATIVE CRITERIA entry) or (b) tuning the
phrase list further, which — with zero test coverage on this gate (see
next section) — risks trading one untested false-negative/positive
pair for another with no harness to catch a regression. Named as a
follow-up candidate per #2503's own sanctioned wording; this role
cannot file it.

### Test coverage — no persistent test file added, evidence recorded instead

Per on-the-record #2137 ("verify-at-landing"), a durable test harness
is a deliverable only when the issue explicitly requires one; #2503
does not. `gates/forbidden_action_rule.py`'s two named siblings
(`acceptance_authoring_rule.py`, `artifact_smoke_rule.py`) also carry
no dedicated test module — same precedent.
derived: `find . -iname "*acceptance_authoring_rule*" -o -iname "*artifact_smoke_rule*" -path "*/test/*"`
(this session) — result: no matches for either sibling.

**Disposition: executed acceptance evidence recorded in this record
(below and above), not a new test file.** All four demonstrations —
positive case, compliant-rewrite negative, mention-only negative, and
the two `_ROLE_REASSIGNED` gap reproductions — were run live in this
session directly against `gates/forbidden_action_rule.py`'s
`check_issue_body`, independent of PR #2696's and PR #2701's own runs.

acceptance: `python3 gates/forbidden_action_rule.py 2479` (this
session, this branch) — result:
```
gate blocked:
  - issue #2479's 'Acceptance' bullet requires an action the delivering role is forbidden from taking ("- check: state explicitly whether the gates' own refusal-message detail was found sufficient to self-correct from without the new directive text — if insufficient, file that as a separate follow-up issue and link it here rather than expanding this issue's scope.") — gh-guard refuses issue creation for every role session (contract v3 s8/s9: issues are the user's requirement backlog, user-authored only). Rewrite with the sanctioned follow-up wording: 'name the follow-up with a drafted body in `## Open findings`; the orchestrator files it.'
```
exit code 1. Same session, `check_issue_body` against a compliant
rewrite body ("name the follow-up with a drafted body in `## Open
findings`; the orchestrator files it.") — result: `[]`. Against a
mention-only body ("see issue #2501 and #2502 for the filed items.") —
result: `[]`.

## What did not work

`python3 gates/spec_index.py --update` (the docs/specs/* regeneration
obligation) crashes on an unrelated, pre-existing missing-file gap.
derived: `python3 gates/spec_index.py --update` on this branch after
the enforcement-boundary.md edit, and again on this branch's clean
HEAD (`4ccc4919`) via `git stash` — both raise the identical
`FileNotFoundError: ... roles/specs/brand-design.spec.json` traceback
— confirmed pre-existing, not caused by this change and not fixable
within #2503's scope. `docs/specs/reconciled-index.md` is therefore
left unregenerated.

## Upstream basis

- PR #2696 (branch `issue-2503/requirements-quality-112361d7`), commit
  `95d3b42b` — the gate + directive change, cherry-picked unmodified.
- PR #2701 — independent verification that found the missing-row gap
  and the two lower-severity gaps; its own Acceptance-bullet
  reproductions are relied on, not redone, per the send-back's own "not
  in dispute" scope note.
  canonical: `gh pr view 2701 --json state,mergedAt,mergeCommit` (this
  session) — result: `{"state":"MERGED","mergedAt":"2026-08-29T07:21:05Z","mergeCommit":{"oid":"4ccc4919f02c5b00b406139e46660b3a445c1ece"}}`.
- `on-the-record/hooks/gate-registration-guard.sh` and
  `on-the-record/hooks/pretooluse_dispatcher.py` at commit `e1f9cb5f`
  (the branch's merge-base) and at current HEAD — read and diffed to
  confirm the guard's logic was unchanged, then live-fired twice in
  this session to isolate the root cause.

## Open findings

1. `gate-registration-guard.sh` is blind to a `git add <new-gate-file>`
   that happens inside the same Bash invocation as the `git commit`
   that lands it, because it evaluates `git diff --cached` before that
   invocation's own body executes — reproduced live above. Resolution
   path: the guard's check needs to also parse the about-to-run command
   text for `git add` targets, not only the pre-execution staged-diff
   snapshot. Not fixed here per this task's own scope instruction
   (land the row, name the hole). Named here per #2503's sanctioned
   wording; this role cannot file it — the orchestrator names a
   tracked follow-up if wanted.
2. `_ROLE_REASSIGNED`'s word-presence exemption both over- and
   under-exempts (bare "operator" mention vs. unrecognized "the user
   should/will file" phrasing) — deferred, not fixed here; reasoning
   above. Named as a follow-up candidate, not filed.
3. `gates/forbidden_action_rule.py` has no persistent test module —
   accepted per #2137 and sibling-gate precedent, evidence recorded in
   this record instead. Not treated as an open gap requiring a
   follow-up.

## Next steps

None pending.
acceptance: `python3 gates/forbidden_action_rule.py 2479` (this
session, this branch, after cherry-picking PR #2696's commit and
landing the enforcement-boundary.md row) — result:
```
gate blocked:
  - issue #2479's 'Acceptance' bullet requires an action the delivering role is forbidden from taking (...) — gh-guard refuses issue creation for every role session (contract v3 s8/s9: issues are the user's requirement backlog, user-authored only). Rewrite with the sanctioned follow-up wording: 'name the follow-up with a drafted body in `## Open findings`; the orchestrator files it.'
```
exit code 1 — confirms the delivered diff on this branch is
functionally identical to PR #2696's own diff. The blocking item
(`docs/specs/enforcement-boundary.md` row) is landed in this same
commit set, and the guard-hole investigation above is backed by two
live, opposite-outcome reproductions in this same session, not by
inference.

skill-verdict: requirements-quality — not-applicable: #2503's own
Acceptance bullets are this repo's `check:`/`must not:` format, not
EARS system requirements or Connextra/QUS user stories — no
trigger/response clause and no role/goal/benefit clause in either
bullet (same verdict PR #2696's and PR #2701's records independently
reached; checked directly against both templates' required clauses
again here rather than inherited).
skill-verdict: silent-failure-audit — applied: invoked; used to frame
the guard-hole investigation itself — `gate-registration-guard.sh`
exiting 0 with no denial and no stderr output on the bundled-commit
shape is exactly a silently-absorbed failure path (a check that runs,
finds nothing because it looked at the wrong moment, and reports
success indistinguishably from "nothing to check"), which is why the
live bundled-vs-split comparison above was run rather than accepting
"the guard exists, so it must have caught this" at face value.
