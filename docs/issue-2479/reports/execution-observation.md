---
issue: 2479
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2479/reports/implementation.md
    sha: a4808703969661c5035cd91f7917c6ddf6a6582b
  - path: directive_assembly.py
    sha: a4808703969661c5035cd91f7917c6ddf6a6582b
  - path: on-the-record/hooks/record-claim-guard.sh
    sha: a4808703969661c5035cd91f7917c6ddf6a6582b
  - path: on-the-record/hooks/heredoc-command-refusal-gate.sh
    sha: a4808703969661c5035cd91f7917c6ddf6a6582b
  - path: gates/record_lint.py
    sha: a4808703969661c5035cd91f7917c6ddf6a6582b
  - path: watchdog.py
    sha: a4808703969661c5035cd91f7917c6ddf6a6582b
  - path: lifecycle.py
    sha: a4808703969661c5035cd91f7917c6ddf6a6582b
subject: PR #2491 (issue-2479/implementation, head a4808703, base main 67c3eb96)
test: issue #2479 Acceptance section — 4 check bullets
result: passed
assertedBy: execution-observation, independently re-run this turn against the real gate scripts with fresh, independently-authored fixtures
---

# issue-2479 — execution-observation record

Path convention: every file cited below lives on `issue-2479/implementation` at
sha `a4808703` (checked out into an isolated worktree, `git worktree add
/tmp/otr-2479-eo a4808703`, removed after use), not on this record's own
branch (`issue-2479/execution-observation`, based on `origin/main`). A
second worktree at unmodified base `67c3eb96` (`git worktree add
/tmp/otr-2479-eo-base 67c3eb96`, removed after use) was used for the
pre-existing-failure and gate-behavior cross-checks. Scratch fixtures under
`/tmp/otr-2479-eo-verify/` were authored fresh this turn, distinct in
wording/numbers from the implementation record's own worked examples, and
removed after use.

## What was done

Independently re-derived all four of issue #2479's Acceptance bullets
against PR #2491, rather than citing the implementation record's own
transcripts.

### Acceptance check 1 — baseline reproduction (before)

Built my own fixtures (own wording, distinct from the implementation
record's), fed them to the two **real, unmodified** gate scripts directly
(not a reimplementation) via their actual stdin-JSON-payload protocol, with
no knowledge of the new `_HOOK_CONTRACT_PROSE` shape assumed.

canonical: `on-the-record/hooks/record-claim-guard.sh` (`a4808703`, byte-
identical to base `67c3eb96` — this PR's diff does not touch it), fed a
fixture (`/tmp/otr-2479-eo-verify/fixture_before_bad.json`, own wording),
whose content was:
```
## Fixture section

Confirmed the fix is complete and the requirement met, based on reading
the diff in this session.
```
Result:
```
$ cat fixture_before_bad.json | bash /tmp/otr-2479-eo/on-the-record/hooks/record-claim-guard.sh
record-claim-guard: 레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): 'Confirmed the fix is complete and the requirement met, based on reading the diff in this session.' — ...
레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): 'Confirmed the fix is complete and the requirement met, based on reading the diff in this session.' — ...
rc=2
```

canonical: `on-the-record/hooks/heredoc-command-refusal-gate.sh`
(`a4808703`, byte-identical to base — unchanged by this PR), fed a fixture
(`/tmp/otr-2479-eo-verify/hcrg_fixture_before_bad.json`, own commit
message) whose `tool_input.command` was a heredoc-shaped `git commit -m
"$(cat <<'MSGEOF' ... MSGEOF )"`, with `CLAUDE_ROLE=execution-observation`
live in this session's own environment:
```
$ cat hcrg_fixture_before_bad.json | bash /tmp/otr-2479-eo/on-the-record/hooks/heredoc-command-refusal-gate.sh
heredoc-command-refusal-gate: heredoc-shaped commit message body detected — the host's write-capable-command classifier refuses this shape as un-analyzable. Use two -m flags instead of a heredoc: git commit -m "<title line>" -m "<body line>" (one -m per paragraph; never a heredoc/$(cat <<EOF ...) body) — issue #1976.
rc=2
```

Also tested the `gh pr create`/`--body` heredoc shape independently (own
fixture, `/tmp/otr-2479-eo-verify/hcrg_gh_fixture_before.json`, a
heredoc-shaped `--body "$(cat <<'BEOF' ... BEOF )"`):
```
$ cat hcrg_gh_fixture_before.json | bash /tmp/otr-2479-eo/on-the-record/hooks/heredoc-command-refusal-gate.sh
heredoc-command-refusal-gate: heredoc-shaped --body detected — ...
rc=2
```

All three baseline fixtures reproduce a refusal on the first attempt, with
no directive text guiding the shape — matching the issue's own baseline
claim, live, with fixtures independent of the implementation record's.

Separately and unplanned: this session's own first attempt to construct
the heredoc-shaped `gh pr create` fixture as an inline `cat > file <<EOF`
Bash command (rather than via the Write tool) was itself denied live by
this repository's installed `pretooluse-dispatcher.sh` board-gate — a
live instance of the same shape-refusal class this issue is about, on
this session's own first relevant write attempt, independent of the two
named gates. canonical: this session's own tool-call transcript this
turn (the denied `cat > /tmp/otr-2479-eo-verify/rcg_check.py << 'PYEOF'`
attempt, worked around by switching to the Write tool for every scratch
file for the rest of this turn).

### Acceptance check 2 — after adding the directive text (after)

Re-ran the same real gate scripts against fixtures built to the shape
`_HOOK_CONTRACT_PROSE` (PR #2491's diff, `directive_assembly.py`) actually
specifies — own command/number choices, not the PR's own worked examples
verbatim.

canonical: `on-the-record/hooks/record-claim-guard.sh`, fed
`/tmp/otr-2479-eo-verify/fixture_after_good.json`, whose content was:
```
## Fixture section

canonical: `gh pr view 2491` output (mergeable: MERGEABLE)
Requirement met — checked: `python3 -m pytest tests/test_directive_diet_2135.py -q` — result: 6 passed
```
Result:
```
$ cat fixture_after_good.json | bash /tmp/otr-2479-eo/on-the-record/hooks/record-claim-guard.sh
rc=0
```

canonical: `on-the-record/hooks/heredoc-command-refusal-gate.sh`, fed
`/tmp/otr-2479-eo-verify/hcrg_fixture_after_good.json`, command `git commit
-m "issue-2479: eo fixture commit" -m "second paragraph, no heredoc
anywhere"`:
```
$ cat hcrg_fixture_after_good.json | bash /tmp/otr-2479-eo/on-the-record/hooks/heredoc-command-refusal-gate.sh
rc=0
```

canonical: same gate, fed `/tmp/otr-2479-eo-verify/hcrg_gh_fixture_after.json`,
command `gh issue comment 2479 --body-file /tmp/otr-2479-eo-verify/scratch-body.txt`:
```
$ cat hcrg_gh_fixture_after.json | bash /tmp/otr-2479-eo/on-the-record/hooks/heredoc-command-refusal-gate.sh
rc=0
```

All three shapes derived from the new directive's rules clear their gate
with zero denials this turn, using fixture content and commands
constructed independently (different file paths, PR/test names, and
prose) from the PR's own worked examples — the shape generalizes, this
is not just the PR's literal example string happening to pass by
construction.

acceptance: `git diff 28c776d929b6efe5541cd1729f3b60b5c0dacea4 a4808703
-- on-the-record/hooks/record-claim-guard.sh
on-the-record/hooks/heredoc-command-refusal-gate.sh` (run in the
`a4808703` worktree) — result:
```
(empty — no output)
```
Both scripts are byte-identical to a pre-PR commit; only
`directive_assembly.py` (a new constant plus one dict entry) and docs/
tests changed — neither gate's own deny logic was touched by this PR.

### Acceptance check 3 — was the refusal-message detail sufficient to self-correct from?

Read both denial transcripts quoted under Acceptance check 1 above
directly. canonical: `gates/record_lint.py:525-537`
(`outcome_claim_citation_check`'s denial string) and
`gates/record_lint.py` (`canonical_source_claim_check`'s denial string) —
each names the exact passing shape ("통과하려면 같은 섹션 안에 ...
canonical:/derived: 태그를 두거나 ... 두면 된다"), not just the violation;
`heredoc-command-refusal-gate.sh`'s message states the sanctioned two-`-m`/
`--body-file` alternative literally, inline, in the denial text itself.

Independent assessment, reaching the same conclusion the implementation
record reaches: **in isolation, yes** — a session that reads either single
denial message carefully has what it needs to fix that one write. What
neither message covers, and what the issue's own incident (PR #2471
already open, two gates firing back-to-back on a follow-up commit, session
ending `progressed-dirty-tree`) actually turned on, is the *compounding*
case: each message is scoped to its own single refusal, names no
relationship to the other gate, and gives no signal about remaining
runway near the end of a session. That gap is what the up-front directive
text this PR adds actually closes (informing before the first attempt,
for both gates at once), not a change to either message's content
(confirmed above under Acceptance check 2 — the `git diff` on both hook
files is empty).

This session did not file a new GitHub issue for that narrower gap.
canonical: `on-the-record/hooks/gh-write-allow-gate.sh:76-77` (`"role
session — never this hook's target"`, exiting early only when
`CLAUDE_ROLE` is unset) — this session's own `CLAUDE_ROLE` is set
(`execution-observation`, `printenv` output this turn), so the same
role-session restriction the implementation record's deviation log names
applies here too. Not independently re-attempted live — a real `gh issue
create` call is a visible, side-effecting action this record has no need
to actually trigger just to re-derive a refusal the implementation record
already demonstrated and logged, canonical:
`a4808703:docs/issue-2479/reports/implementation/deviation-log/20260826T011402145329-89f7f09e0aae5ebc.md`
— noted as unverifiable-by-this-session-independently, not disputed.

### Acceptance check 4 — should `progressed-dirty-tree` be reclassified by watchdog?

Read the actual respawn code paths directly, independent of the
implementation record's own (self-disclosed-as-unverified) treatment of
this question.

canonical: `watchdog.py:290-303` (roster-scan diagnosis function,
`a4808703`):
```
    alive = _sp._alive(pid)
    if not alive:
        verdict = _sp.session_end_verdict(
            work, Path(entry["log"]) if entry.get("log") else None, now=now) \
            if work else None
        if branch is None:
            pr_number = None
        elif pr_index is not None:
            pr_number = _sp._pr_state_from_index(pr_index, branch)
        else:
            pr_number = _sp._pr_open_or_merged_for_branch(root, branch)
        if verdict == "normal" or pr_number is not None:
            return _diagnosis({"state": None, "next_action": "none",
                    "detail": "completion, not a health diagnosis"})
```
This path (used for `roster_watchdog()`'s human-facing status reporting)
does consult `pr_number` — a dead process on a branch with any open/
merged PR is treated as "completion, not a health diagnosis", not dead.

But the code path that actually triggers an automatic respawn is a
different function. canonical: `lifecycle.py:472-505`
(`_auto_respawn_check`, `a4808703`):
```
def _auto_respawn_check(key: str, entry: dict, state: dict) -> None:
    work = entry.get("work")
    issue = entry.get("issue")
    role = entry.get("role")
    if not work or issue is None or not role:
        return
    log_path = Path(entry["log"]) if entry.get("log") else None
    verdict = _sp.session_end_verdict(work, log_path)
    print(f"[watchdog] {key}: {verdict}")
    if verdict == "stalled":
        _sp._post_stall_comment(Path(work), issue, key, work, entry.get("log", ""))
        return
    if verdict != "crashed":
        return
```
This function calls `_respawn_or_cap()` whenever `session_end_verdict()`
returns `"crashed"` and never reads `pr_number`/commit state at all. A
session that hits both gate refusals back-to-back and then exits before
appending its own `session-end` event leaves no `session-end` event after
the last `session-start` in `<work>.events.jsonl`. canonical:
`board.py:1026-1069` (`session_end_verdict()`, `a4808703`) — returns
`"crashed"` for exactly that shape (pid not alive, no trailing
`session-end` event), regardless of how many commits or open PRs the
branch already carries. This is a plausible, code-grounded mechanism for
the misclassification the issue describes, independent of and more
specific than the implementation record's own "not verified" treatment
of this question — provided the actual incident session died before
finishing its own `progressed-dirty-tree` session-end write. If that
session instead managed to record the event before exiting,
`session_end_verdict()` would have returned `"normal"` instead (a
`session-end` event exists after the last `session-start`), which
`_auto_respawn_check` treats as a no-op. This record cannot determine,
from the artifacts the implementation record cites, which of the two
sub-cases actually happened for the issue-2379 incident.

canonical: `lifecycle.py:315-356` (`_classify_workspace_completion`,
added for issue #1982, `a4808703`) — inspects `git status --porcelain
-uall` in the dead workspace and, if the dirty set includes a
non-frontmatter-only `docs/issue-<n>/reports/**` or
`docs/issue-<n>/proposals/**` file, `_respawn_or_cap()`
(`lifecycle.py:359-469`) prepends a continuation preamble ("workspace
contains uncommitted work from the previous session — verify briefly,
then commit/push/PR; do not redo") to the respawned task text instead of
a from-scratch task. A respawn triggered through `_auto_respawn_check` is
therefore not always "dead session, respawn from scratch" — but this
mechanism keys on git-status dirtiness of a specific path shape at
respawn time, not on the outcome label itself, and does not cover a dirty
code file with no accompanying dirty record file, so it narrows rather
than closes the `_auto_respawn_check` PR-blindness gap identified above.

Independent conclusion, reaching the same scope answer the implementation
record reaches but with a more specific code citation: **yes, this is a
distinct, separate mechanism change** — `_auto_respawn_check`'s
`"crashed"` trigger (`lifecycle.py:472`) does not consult `pr_number`/
commit state before calling `_respawn_or_cap()`, unlike the adjacent
`roster_watchdog()` diagnosis path (`watchdog.py:301`), which already
does. Not implemented here, per the issue's own acceptance-check-4
instruction to name it as a follow-up rather than fold it into this
directive-text-only issue's scope. Not filed as a new GitHub issue by
this session either, for the same `gh-guard`/`CLAUDE_ROLE` restriction
independently confirmed above under Acceptance check 3, canonical:
`on-the-record/hooks/gh-write-allow-gate.sh:76-77`.

### Test-plan re-verification

acceptance: `python3 -m pytest tests/test_directive_diet_2135.py::SectionFileMapping -q`
(run in the `a4808703` worktree) — result:
```
......                                                                   [100%]
6 passed in 18.63s
```
Matches the PR's own claimed 6 passed.

acceptance: `python3 -m pytest tests/test_directive_diet_2135.py
tests/test_spawn_directive_assembly.py -q` (run in the `a4808703`
worktree) — result:
```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
FAILED tests/test_spawn_directive_assembly.py::SkillVerdictObligationLine::test_zero_mounted_skills_directive_unchanged
FAILED tests/test_spawn_directive_assembly.py::SkillTriggerLines::test_zero_mounted_skills_directive_unchanged
FAILED tests/test_spawn_directive_assembly.py::InvokeBeforeApplyObligation::test_zero_mounted_skills_directive_unchanged
4 failed, 47 passed, 1 skipped in 25.50s
```

canonical: same two files, re-run in the unmodified `67c3eb96` base
worktree — result:
```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
FAILED tests/test_spawn_directive_assembly.py::SkillVerdictObligationLine::test_zero_mounted_skills_directive_unchanged
FAILED tests/test_spawn_directive_assembly.py::SkillTriggerLines::test_zero_mounted_skills_directive_unchanged
FAILED tests/test_spawn_directive_assembly.py::InvokeBeforeApplyObligation::test_zero_mounted_skills_directive_unchanged
4 failed, 47 passed, 1 skipped in 26.98s
```
Identical failure set on unmodified base — these 4 failures pre-exist
this change and are not new.

acceptance: `git diff origin/main...HEAD --stat` (`a4808703` worktree,
base `67c3eb96`) — result:
```
 directive_assembly.py                              |  69 +++++-
 docs/handbooks/spawn-directive-assembly.md         |  28 +++
 docs/issue-2479/reports/implementation.md          | 241 +++++++++++++++++++++
 .../20260826T011402145329-89f7f09e0aae5ebc.md      |   1 +
 tests/test_directive_diet_2135.py                  |   3 +-
 5 files changed, 337 insertions(+), 5 deletions(-)
```
Matches the PR's own reported 337 additions / 5 deletions / 5 files
(`gh pr view 2491 --json additions,deletions,changedFiles`), no unrelated
changes.

## Why

derived: every fixture, transcript, code read, and test run quoted under
"What was done" above was constructed or executed this turn, independent
of the implementation record's own examples/wording — every claim in this
section draws only on those already-cited transcripts and file:line reads.

Built fresh fixtures (own claim text, own commit messages, own file
names/numbers) rather than reusing the PR's own worked examples verbatim,
so a pass doesn't just confirm the PR's literal example string happens to
satisfy its own gate — it confirms the shape the directive text describes
generalizes to independently-constructed input.

Ran the real, unmodified gate scripts end-to-end (piping a JSON payload
into the actual `record-claim-guard.sh`/`heredoc-command-refusal-gate.sh`
via their real stdin protocol) rather than only re-deriving `gates/
record_lint.py`'s Python functions in isolation, to close the gap between
"the underlying check function returns the right list" and "the actual
PreToolUse hook, as a shell script with its own payload-parsing and role-
scoping logic, actually denies/allows as claimed."

Went beyond the implementation record's own acceptance-check-4 treatment
(which states it did not verify whether watchdog's live dead-entry path
consults commit/PR signals) by reading `_auto_respawn_check` and
`_respawn_or_cap` directly, rather than repeating the same unverified
statement — this turned up a more specific, code-grounded answer (the
`"crashed"`-verdict trigger path is blind to `pr_number`/commit state,
while the adjacent human-facing diagnosis path is not; `_respawn_or_cap`
already has a partial, path-shape-keyed continuation-preamble mechanism
from issue #1982 that narrows but does not close the gap).

## Upstream basis

canonical: this session's own `a4808703`/`67c3eb96` worktree reads and
command runs, individually cited by file:line/command above.

- `a4808703:docs/issue-2479/reports/implementation.md` — the delivered
  work's own account; re-derived rather than cited, per this role's
  independent-execution mandate.
- `a4808703:directive_assembly.py` — the actual code change (new
  `_HOOK_CONTRACT_PROSE` constant, one new dict entry in
  `directive_section_files()`), read and diffed directly this turn.
- `a4808703:on-the-record/hooks/record-claim-guard.sh`,
  `a4808703:on-the-record/hooks/heredoc-command-refusal-gate.sh`,
  `a4808703:gates/record_lint.py` — the two gates this issue documents and
  their shared check module; run directly against fresh fixtures this
  turn, and diffed byte-for-byte against a pre-PR commit (empty diff,
  quoted above under Acceptance check 2) — neither gate's own logic
  changed.
- `a4808703:watchdog.py`, `a4808703:lifecycle.py`, `a4808703:board.py` —
  read directly this turn for Acceptance check 4, independent of the
  implementation record's own (self-disclosed) non-verification of this
  question.
- `a4808703:docs/issue-2479/reports/implementation/deviation-log/20260826T011402145329-89f7f09e0aae5ebc.md`
  — the implementation record's own disclosed deviation (role sessions
  refused from `gh issue create`); independently checked against
  `on-the-record/hooks/gh-write-allow-gate.sh:76-77`'s role-gating logic
  and this session's own live `CLAUDE_ROLE` value, rather than accepted on
  the record's word alone.
- issue #2479's live body (`gh issue view 2479`, fetched this turn) — the
  real Acceptance text (four `check` bullets) this record checks the
  delivery against.
- `67c3eb96` (this PR's base commit, unmodified) — the "before" state for
  the baseline reproduction, the pre-existing-failure cross-check, and the
  diff-scope confirmation above.

## Open findings

canonical: `lifecycle.py:472` / `watchdog.py:301` (already cited in full
above under Acceptance check 4).

1. Acceptance check 3's residual gap (both gate messages are sufficient
   for a single isolated refusal but say nothing about a second gate
   firing back-to-back, or about remaining session runway) — the same
   follow-up the implementation record already named and, per the
   `gh-guard`/`CLAUDE_ROLE` role restriction checked above, could not
   file itself. Not re-filed by this session for the same reason.
2. Acceptance check 4, refined: `_auto_respawn_check`'s `"crashed"`
   trigger (`lifecycle.py:472`) does not consult `pr_number`/commit state
   before calling `_respawn_or_cap()`, while the adjacent
   `roster_watchdog()` diagnosis path (`watchdog.py:301`) already does —
   a concrete target for the watchdog-side follow-up the issue's own
   acceptance check 4 anticipates, narrower than a blanket "reclassify
   the outcome label" framing since issue #1982's
   `_classify_workspace_completion()` already softens (but does not
   close) the gap for the specific case of a dirty non-empty record file
   at respawn time. Whether the issue-2379 incident session actually
   exited before or after recording its own `session-end` event (the
   fork identified under Acceptance check 4 above) was not determinable
   from the artifacts available this turn. Not filed as a new GitHub
   issue by this session, same role restriction as item 1.

## What did not work

None — every independently-authored fixture and code read behaved as its
own hypothesis predicted on the first run this turn; no wording or
fixture-shape correction was needed. (The one live board-gate refusal
noted under Acceptance check 1 was a genuine first-attempt refusal, not a
correction — the workaround, switching to the Write tool for scratch
files, was applied once and held for the rest of the turn.)

## Next steps

None — `loop_state: done`, all four Acceptance bullets independently
re-derived this turn (before/after fixtures for checks 1-2; explicit,
code-grounded statements for checks 3-4), both scope-boundary questions
answered with citations beyond what the implementation record itself
verified.

acceptance: summary of the four independently-executed Acceptance items
above — result:
```
check "baseline: undirected write hits a gate refusal on first attempt": three independent own-wording fixtures (record-claim-guard.sh state+outcome claim, heredoc-command-refusal-gate.sh git-commit and gh-pr-create shapes) each denied on the real, unmodified gate scripts this turn, plus one unplanned live board-gate refusal of this session's own inline-heredoc construction attempt
check "after: directive-shaped write clears both gates on first attempt": three independent own-wording fixtures built to the new _HOOK_CONTRACT_PROSE shape each passed (rc=0) against the same real, unmodified gate scripts this turn; git diff of both gate scripts between base and head is empty, confirming neither gate's deny logic changed
check "refusal-message sufficiency, stated explicitly": sufficient for a single isolated refusal (both messages name the exact fix inline); insufficient for the compounding back-to-back case the incident actually hit — same conclusion as the implementation record, independently re-derived from the quoted denial text above
check "watchdog progressed-dirty-tree reclassification, stated explicitly": yes, a separate mechanism change — refined to a specific code target (_auto_respawn_check's crashed-trigger path, lifecycle.py:472, ignores pr_number/commit state; roster_watchdog's own diagnosis path already checks it) beyond what the implementation record verified; named as a follow-up, not implemented, not filed (role-session gh-guard restriction independently confirmed)
```
