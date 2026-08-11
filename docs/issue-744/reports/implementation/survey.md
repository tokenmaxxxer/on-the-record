# Survey: gate-noise triage across the four #744 candidates

## Repo-boundary finding (governs every item below)

Before triaging the four items individually, the single most consequential
fact this survey turned up: the four gates #744 names do not all live in
this repo.

- `on-the-record/hooks/spec-index-preflight.sh` and
  `on-the-record/hooks/record-claim-guard.sh` (backed by
  `gates/record_lint.py`) are on-the-record's own files — in this repo's
  write set, git-tracked, testable here.
- board-gate and trailer-gate are not present anywhere in this repo's
  source tree (confirmed: a repo-wide search for their filenames turns up
  only unrelated skeleton-generator examples under the issue-167/issue-170
  asset trees, plus references that treat them as an external dependency —
  e.g. gates/test_hooks_parity.py's self-hosted pattern, which exists
  specifically because spec-index-preflight.sh is self-hosted here while
  board-gate/trailer-gate are not). They ship from a separate GitHub repo,
  tokenmaxxxer-core, installed as the "tokenmaxxxer-core plugins" the
  on-the-record handbook's orchestration-model section names as a
  dependency alongside each role's own rulebook. A locally cached checkout
  of that repo (clean, tracking its own origin/main, distinct git history)
  confirms board-gate.sh and trailer-gate.sh live under its core/hooks/
  directory, not under this repo's on-the-record/hooks/.

Practical consequence: this session's write set can carry code fixes for
item 1 and item 2's guidance layer, but not for item 3 or item 4's gate
logic — those changes, if still needed after this survey, belong to a
tokenmaxxxer-core issue, filed and built there, the same way #705's own
proposal already scoped itself (its "What will be done" section states
outright that the warrant/coding/record-shape plugin edits it recommends
"live in different repos... than this one (on-the-record)... become the
phase-2 (or a separate cross-repo) unit once this proposal is approved and
the plugin repos' own role sessions pick it up").

## Provenance: #744 sits downstream of #726's systematic audit

on-the-record issue #726 ("systematic audit: gate-required shape vs
authoring-time directive/template mismatches strand or slow role sessions
repo-wide", closed) is the 2026-08-11 성능 분석 #744's body refers to. Its
own body names the exact fixes already spun out: "warrant hunt-record path
(tokenmaxxxer-core#202)... and the on-the-record-side guidance (#705)".
Reading tokenmaxxxer-core's own history (local checkout, `git log
--oneline -25`) confirms three of those spun-out issues already merged
today, hours before this session started:

```
8178711 Merge pull request #210 from tokenmaxxxer/issue-204/implementation
78f660d feat(directive): promote spec-index, PR-trailer phase-split, test-claim shapes into shared heredoc
...
66c96c2 fix(warrant): derive hunt-record path from role scope, not proposal path
...
ea939ca fix(directive): instruct staging of new/untracked files before commit
```

`gh issue list --repo tokenmaxxxer/tokenmaxxxer-core` confirms the three
issue numbers and their closed state:

```
204  CLOSED  shared role directive omits several gate-enforced shapes — role sessions learn them only from refusal (audit on-the-record#726: rows 2,3,4/14,19,20,25)
203  CLOSED  commit directive omits staging of NEW files — untracked new files never land, PR-create fails 'No commits between main and branch'
202  CLOSED  warrant hunt-record path directive collides with on-the-record's board-gate role-scope — hunt writes strand every post-PR session
151  CLOSED  trailer-gate cannot read heredoc-supplied commit messages, so the standard multi-line commit idiom is unusable
```

This reframes the investigation: for three of the four candidates, the
question is no longer "what prescription fixes this" but "is the fix that
already landed upstream actually sufficient, verified from this session's
own vantage point."

## Item 1 — docs/specs/reconciled-index.md companion-update requirement

Mechanism (on-the-record's own, read from source):
`on-the-record/hooks/spec-index-preflight.sh` denies a `git commit` that
stages a tracked spec file (row in `docs/specs/reconciled-index.md`) whose
staged content hash no longer matches the index's recorded hash, unless
the index itself is staged with a matching update in the same commit. The
deny message already carries the fix command: "Regenerate with `python3
gates/spec_index.py --update`, stage the updated index, and retry the
commit." `gates/spec_index.py`'s own `check()` function requires the same
under CI, plus an explicit prompt to review the "Resolved ambiguities"
section for a real semantic conflict — this is deliberate friction, not
an oversight: the module's own docstring states the check is deterministic
drift detection, not semantic-conflict detection, and hands that judgment
to a human/session on purpose. That argues against silently
auto-regenerating the index inside the hook (candidate "automation"):
doing so would remove the one moment a session is forced to notice the
index exists and open it.

What #744 diagnosed as missing: this requirement stated nowhere at
authoring time, only at refusal time.

Current state, verified live in this very session: the "[core] Interaction
protocol for role 'implementation'" text injected at this session's own
SessionStart already states — verbatim — "A session that stages a change
to any docs/specs/* file must also regenerate and stage
docs/specs/reconciled-index.md (python3 gates/spec_index.py --update) in
the same commit — spec-index-preflight.sh refuses a docs/specs/* commit
that leaves the index stale." That text is generated by
tokenmaxxxer-core's `core/hooks/directive.sh`, and git history on the
local tokenmaxxxer-core checkout shows it landed today via issue-204 (see
Provenance above), commit `78f660d`, timestamped 2026-08-11 13:48 KST —
before this session started.

Regression coverage already exists in this repo, in the function
`t_live_fire_deny_before_commit_lands` inside `gates/test_hooks_parity.py`:
it builds a real temp git repo, stages a spec-file drift with a stale
index (RED: asserts exit code 2, commit does not land), then regenerates
the index and re-stages (GREEN: asserts exit code 0, commit lands). Ran
directly this session:

```
$ python3 gates/test_hooks_parity.py
  ok  t_live_fire_deny_before_commit_lands
  ok  t_non_self_hosted_target_gets_no_injection
  ok  t_registered_hooks_match_hooksjson_entries
  ok  t_role_settings_merges_hooks_only_for_self_hosted_target

4 passed
```

Also verified directly: `docs/specs/reconciled-index.md` is 2480 bytes
(matches #744's own citation) and currently in sync —

```
$ python3 gates/spec_index.py
통과: 모든 spec 문서가 기록된 해시와 일치한다
```

Verdict: item 1 was genuine noise (a real gap, not a legitimate refusal in
disguise), and it is already resolved upstream as of today. The mechanical
refusal itself is a legitimate, deliberately-designed check and stays as
is. Nothing in this repo needs to change for item 1; the existing
live-fire regression test already covers the mechanism, and the
authoring-time guidance now exists and is confirmed present in this
session's own context.

## Item 2 — backtick-quoted paths to not-yet-created files / path:function notation

Mechanism (on-the-record's own): `gates/record_lint.py`'s
`orphaned_path_reference_check` matches any backtick-quoted string
beginning with one of six path prefixes (src, test, tests, docs, gates,
on-the-record) and denies if `(root / ref).exists()` is false at the
moment of the write.

#744's own scope note says changing this check's logic is explicitly out
of scope right now, because #730 just landed the write-time guidance
countermeasure and the issue asks to observe that guidance's effect before
touching the logic. This survey honors that boundary and does not propose
a logic change.

Current state of the guidance layer: `on-the-record/hooks/record-claim-shape-directive.sh`
(issue #730) is a UserPromptSubmit hook, present in this repo, that
generates its output text directly from `record_lint.py`'s check-function
docstrings at hook-run time — the same functions the PreToolUse gate
calls — so the two cannot drift apart the way a hand-copied second text
would. It fires whenever CLAUDE_ROLE is set and prints the citation shape
before the gate is ever hit. This exact text appears live in this
session's own context as the "record-claim-citation-directive" block,
confirming the countermeasure is deployed and active.

What the guidance layer does not (and structurally cannot) do: name every
individual false-positive shape the underlying regex produces. Reading the
check's own pattern confirms two of #744's cited shapes are genuine
false positives, not hypothetical — a path:function locator suffix (a
colon plus a function name appended after a real, existing file path) and
a reference to a path this session's own proposed work will create later
in the same PR (not yet present in the working tree at write time) both
match the six-prefix regex and both fail the existence check, exactly like
a truly broken reference would. The check cannot distinguish "this path
will exist once this PR's own writes land" or "this is file:function
shorthand" from "this reference is hallucinated" — all three currently
deny identically.

Existing regression coverage: the function
`t_one_invocation_reports_all_distinct_violations` inside
`gates/test_record_lint.py` already pins the legitimate case (a reference
to a path that plainly does not and will never exist) as a red case that
must keep failing. No existing test documents the two false-positive
shapes.

Verdict: guidance-only fix (write-time directive) already landed and
verified live; the underlying check retains a real, reproducible
false-positive gap for two specific shapes, but fixing that gap is
explicitly out of #744's own current scope. This is a third category
distinct from "noise, now fixed" and "legitimate, stays as is": a real
flaw, deliberately deferred by the issue's own text, mitigated for now by
guidance rather than a logic change.

## Item 3 — reports/hunt-*.md ownership vs board-gate role-scope

Mechanism: board-gate (tokenmaxxxer-core) allows a role to write only
inside its own docs/issue-<n>/reports/<role>/** subtree (its R5 rule); a
bare docs/issue-<n>/reports/hunt-*.md path is a foreign-role path from
board-gate's point of view because it carries no role segment.

#744 itself flags this item as adjacent to #705 and asks for a duplication
call. on-the-record issue #705 ("role sessions repeatedly strand post-PR:
hunt/record writes hit ownership and claim gates after the PR is already
open") is open, already carries a phase-1 proposal
(`docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md`,
status: proposed) whose "What will be done" targets precisely this
mechanism — correcting warrant/hooks/directive.sh's hunt-record path text
so it derives from role scope instead of the proposal path. That is the
identical fix tokenmaxxxer-core issue-202 already delivered (commit
`66c96c2`, "fix(warrant): derive hunt-record path from role scope, not
proposal path", landed 2026-08-11 13:35 KST — 13 minutes before item 1's
fix, same session of upstream work). The warrant/hooks/directive.sh text
now present in this session's own "warrant-directive" context block
reflects that corrected, role-derived routing (it explicitly branches on
whether CLAUDE_ROLE and the branch name resolve to an issue-scoped, role-
scoped session before choosing the path shape).

#705's own scope is broader than item 3 alone — it also covers
record-claim-guard and record-fields-gate template alignment for the
post-PR record write, which core#202 does not touch. That broader part of
#705 remains open and unduplicated by anything in #744.

Verdict: item 3 is a duplicate of work #705 already owns and has already
proposed; the hunt-record-path portion specifically is already resolved
upstream (verified via this session's own live warrant-directive context,
which already names the role-derived path this repo's convention section
also states: hunt records for this issue go to the path with segment
reports/implementation/hunt-, not a bare reports/hunt- path). Building a
second, parallel fix inside #744 for the same mechanism #705 already
targeted would recreate exactly the drift #705's own Rationale explicitly
rejected ("recreates exactly the failure mode... a corrected string that
will drift again"). Item 3 should close by reference to #705, not by a
duplicate prescription here.

## Item 4 — trailer-gate and heredoc commit messages

The comment that added this item to #744 states a specific, falsifiable
claim: trailer-gate cannot parse a git commit -m $(cat <<EOF ... EOF)
message, and this killed an issue-759 phase-2 session outright (zero
commits, PR-create failed with "No commits between main and
issue-759/implementation").

Reading trailer-gate.sh's own source (tokenmaxxxer-core, local checkout)
shows this capability already exists: its `_check_allowlist` /
`_evaluate_allowlisted` path specifically resolves a `-m` value shaped as
a double-quoted, single $(...)/backtick expression wrapping a bare `cat`
call with a heredoc body — nothing else, no file operand — by actually
running that narrow, PATH-cleared allowlisted snippet and reading its
resolved output, then checking the resolved text for the Subject:
issue-<n> trailer. The code comments cite this as tokenmaxxxer-core
issue-141 machinery ("D1: resolve $(...)/backtick/heredoc -m message
constructs by effect, not by shlex-tokenizing the raw source text"), and
`gh issue list --repo tokenmaxxxer/tokenmaxxxer-core --search trailer`
confirms a closed issue #151 titled exactly "trailer-gate cannot read
heredoc-supplied commit messages, so the standard multi-line commit idiom
is unusable" — closed 2026-08-07, four days before #744 was filed.

This session verified the capability empirically rather than trusting the
code read alone, by inspecting the actual issue-759 session logs on disk
(three files across the phase-1 session and two phase-2 attempts, under
/Users/jk/.tokenmaxxxer/work/, named
on-the-record-issue-759-implementation.session.*.log). Every real
deliverable commit issue-759 made — one in the phase-1 session, two in
the final phase-2 session — used exactly the pattern git commit -m
"$(cat <<'EOF' ... EOF)" (double-quoted, single-quoted heredoc delimiter)
and every one of those three commits succeeded on the first try; the
phase-2 session's gh pr create (also heredoc-bodied) succeeded as well and
produced the PR the #744 comment itself links to.

The four consecutive trailer-gate refusals the #744 comment describes do
appear in the middle log file, but every one of them traces back to a
single subagent_type: warrant:warrant-hunter dispatch running
"Before-landing hunt, stance 0" (per the warrant plugin's own stance
rotation: "assume the gate just touched is bypassable — find the
bypass"), adversarially probing the session's own newly-built
gate-registration-guard.sh for a rename-based bypass. Those four commands
were sandbox/bypass experiments (an unquoted $(cat <<EOF...) construct, a
message-less commit, a git -c core.hooksPath=/dev/null commit bypass
attempt, and a python-heredoc write), not attempts to land the
deliverable — and one of the four denials is itself informative: it fired
because trailer-gate's root-resolution prefers CLAUDE_PROJECT_DIR over the
Bash command's own cd-ed working directory, so a hunter experiment that
cd's into a scratch mktemp -d repo still gets judged against the real
workspace's staged issue-744 tree. That is a real, separate, narrower gap
(sandboxed experiments can inherit an unrelated repo's staged state) than
"heredoc is unparseable" — and it lives in trailer-gate's own
root-detection logic, not its message-parsing logic.

The session that actually died with zero commits is the middle one: its
entire visible activity is hunt investigation and sandboxed reproduction
of the gate-registration-guard.sh rename-bypass finding (matches the hunt
record this session wrote, stance 0, "before-landing" transition, filed
under docs/issue-759/reports/implementation/) — it never reaches a real,
non-sandboxed git commit for its own deliverable anywhere in its log.
Separately, tokenmaxxxer-core issue-203 (closed today, commit `ea939ca`)
diagnoses and fixes exactly the symptom string the #744 comment quotes —
"PR-create fails 'No commits between main and branch'" — as caused by the
commit directive never instructing a session to stage newly-created,
untracked files before committing (git commit -a/-am only restages
already-tracked paths). That fix's text is present live in this session's
own "core" interaction-protocol block today. Between the hunter's
incidental, expected-to-refuse experiments and the untracked-staging gap
(now fixed), there is no remaining evidence that trailer-gate's heredoc
handling itself caused the stranding.

One narrower, real gap does remain even after issue-151: an unquoted -m
$(cat <<EOF ... EOF) (no surrounding double quotes) is refused with
"contains a $(...)/backtick/heredoc construct that could not be parsed
into a single resolvable expression" rather than being resolved. That
refusal is arguably correct on its own terms, independent of the gate:
unquoted command substitution undergoes normal shell word-splitting on the
heredoc body before git ever sees it, which silently turns a multi-line
commit message into multiple mangled -m arguments — a real shell hazard
the gate's refusal happens to catch as a side effect, not an artificial
restriction.

Verdict: the premise "trailer-gate cannot parse heredoc commit messages"
is false as stated and was already false before #744 was filed (fixed
2026-08-07, tokenmaxxxer-core#151); the specific stranding episode cited
as evidence is better explained by (a) a warrant-hunter's adversarial
probing of an unrelated gate, which is supposed to hit denials, plus (b)
the untracked-file-staging gap, independently already fixed today
(tokenmaxxxer-core#203). No trailer-gate code or message change is
warranted by the evidence gathered here. The one real residual gap (the
CLAUDE_PROJECT_DIR-vs-cwd root resolution during sandboxed experiments)
and the one real shell hazard (unquoted heredoc substitution) both live in
tokenmaxxxer-core, outside this repo's write set.

## Direction-conflict check: gate-registration-guard.sh (issue-759) vs #744

The user's turn instructions ask this session to judge whether keeping
issue-759's new `on-the-record/hooks/gate-registration-guard.sh` (a
landing-time gate requiring a spec row for any newly-staged
gates/*.py/on-the-record/hooks/*.sh/.github/workflows/*.yml file) is
correct despite #744 pulling toward less friction. Reading that hook's own
header comment (already merged, commit `dd651ed`) shows it was written
with explicit awareness of #744: "editing an already-registered module's
internals (plain \"M\"), or any unrelated commit, is untouched (the
ambient-noise failure mode #744 investigates)." Its trigger condition is
narrow by construction — only a newly-staged mechanism file with no
existing spec row fires it; every other commit, including this session's
own docs-only commits, passes through untouched.

Verdict: not noise, and not a conflict to resolve by weakening either
side. #744 exists to remove friction from gates whose requirement was
never stated at authoring time; gate-registration-guard.sh is a new gate
whose own authoring-time requirement (the spec-row precondition) is
explicit in every role session's own directive context and narrowly
scoped to the one file-class that caused two same-day recurrences
(issue-759's body cites #689 fixing the identical gap once, then it
reappearing before a day passed). The two issues check each other by
design and should stay separate: #744 does not need to (and should not)
loosen or remove gate-registration-guard.sh.

## Baseline: main is green

```
$ python3 -m pytest gates/ tests/ on-the-record/hooks/ -q
1127 passed, 2 skipped in 153.90s (0:02:33)
```
derived: python3 -m pytest gates/ tests/ on-the-record/hooks/ -q

No proposed change in the accompanying proposal touches gate logic, so
this baseline is the number any phase-2 regression-test additions are
expected to grow from, not replace.

## Evidentiary note: which local copy of tokenmaxxxer-core actually governs this session

The after-proposal warrant hunt (stance 0, hunt record at
docs/issue-744/reports/implementation/hunt-2026-08-11-gate-noise-item-dispositions.md)
found a second, stale local copy of tokenmaxxxer-core at Claude Code's
generic plugin-cache path (~/.claude/plugins/cache/tokenmaxxxer-core),
mtime before today's fixes and missing the reconciled-index and
untracked-staging guidance text entirely, and flagged that this survey's
item 1 and item 4 claims never checked that path against the one actually
used for verification
(~/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core).

Verified and closed, not disputed: this session's own environment carries
CLAUDE_PLUGIN_ROOT_CORE pointing at the runs/rulebooks copy, and
trailer-gate.sh's own source line honors that variable ahead of any
fallback. Independently of that configuration read, real historical
denial messages from actual past role sessions (issue-759's own session
logs, cited under Item 4 above) self-report their firing gate's path as
the runs/rulebooks copy, not the plugins/cache one — direct evidence of
which copy a live session executes, from before this survey was even
written. The plugins/cache copy carries its own .orphaned_at marker,
consistent with being a superseded artifact bypassed by the
CLAUDE_PLUGIN_ROOT_CORE override rather than a competing live source.
Full reproduction is in the hunt record.
