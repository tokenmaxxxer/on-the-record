---
issue: 2139
role: overengineering-audit-ecf2ec0d
author: overengineering-audit-ecf2ec0d
skills: overengineering-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gates/forbidden_action_rule.py
    sha: same-commit
  - path: gates/record_lint.py
    sha: same-commit
---

# issue-2139 — overengineering-audit-ecf2ec0d record

## What was done

Continued issue #2139's relic sweep (retired "role"-axis vocabulary →
current "skill"-axis vocabulary; a #2600 follow-up applying its own
lesson that a word-grep alone under-covers). Two parts: a kind-lens
evidence pass (already executed and posted by a prior worker session in
this same delivery chain, re-verified here), and this session's own
batch-cleanup + verification + record + PR.

**Kind-lens sweep** — 8 occurrence kinds a plain word-grep misses, each
file in the population checked against all 8: (1) CLI help/usage text,
(2) user-facing error/exit messages, (3) log/status print format
strings, (4) messages posted live to GitHub (PR bodies, issue comments,
CI check output), (5) docstring/comment references to a renamed
function or constant, (6) on-disk config/generated file paths, (7)
on-disk schema field names (trace logs, YAML frontmatter, roster/dict
keys), (8) directive/commands prose invocation examples.

**Population searched** (matching the evidence comment's own stated
scope): `spawn.py` + the 10 extracted modules (`pipeline.py`,
`consult.py`, `lifecycle.py`, `directive_assembly.py`, `board.py`,
`roster.py`, `watchdog.py`, `relay.py`, `events.py`, `skills.py`,
`checkpoint.py`, `deviation_log.py`, `hook_fires.py`, `plumbing.py`,
`priorities.py`, `trajectory_analyzer.py`), `gates/*.py`,
`on-the-record/directive/*.md` + `on-the-record/commands/*.md`, full-text
read. `docs/` was read only as corroborating evidence, never edited
(out of scope by this issue's own `must not` — this record is the one
stated exception). `hooks/*.sh` was explicitly excluded (issue #2138's
territory).

**Batch cleanup applied this session** — mechanical, behavior-preserving
wording/dead-name-reference fixes only (comments, docstrings, error
strings, log-format strings, trace-field names, directive prose — no
logic changes), across:

- `skills.py` — module docstring, `resolve_role_family_source()` →
  `resolve_skill_family_source()` docstring references (2 sites) and its
  own error-string prefix, `{role}-`→`{skill}-` example text.
- `roster.py` — `_watcher_looks_real()` docstring's stale `role` kwarg
  reference → `skill` (the real parameter).
- `relay.py` — `_open_role_prs`→`_open_skill_prs` docstring reference,
  two public PR-body/issue-comment strings that said `"{skill} role
  session"` / `"the role's own work"` while a `skill: {skill}` line sat
  two lines below (self-contradicting).
- `pipeline.py` — `skill_settings()`'s own docstring (still said
  "역할" throughout despite the function's real `skill` parameter),
  two stale `role_settings()`→`skill_settings()` comment references, one
  `sys.exit` message ("역할 세션은 core 없이" → "스킬 세션은 core
  없이").
- `consult.py` — three trace-log format strings that wrote a literal
  `role=` field label into `docs/issue-<n>/reports/consult-log/*.md`,
  `runs/patrol-judge-log.md`, and `docs/issue-<n>/reports/panel/*.md`
  (now `skill=`); `_commit_consult_trace()`'s unused-name parameter
  renamed `role`→`skill` (all 3 call sites already positional, so only
  the signature moved); `_JUDGE_ROLE_EXCLUSIONS`→`_JUDGE_SKILL_EXCLUSIONS`,
  `_judge_roles_run_today()`→`_judge_skills_run_today()`,
  `JUDGE_MAX_ROLES_PER_MERGE`→`JUDGE_MAX_SKILLS_PER_MERGE` docstring/
  module-docstring references to names that no longer exist under the
  old spelling; `judge_cmd()`'s own invocation-example docstring;
  `_run_panel_session` signature-description docstring.
- `board.py` — two `roster_ps` status prints ("돌고 있는 역할 세션...")
  and one no-board fallback message's `<역할>.md` example.
- `watchdog.py` — the board-sweep denial message (issue's own
  already-flagged A5-adjacent finding) and two docstring/comment sites
  that still described the branch shape as `issue-<n>/<role>` instead of
  the current `issue-<n>/<skill>[+<skill>]-<lease>`; one `roster_ps`-style
  status print.
- `events.py` — a watch-stall exit message, a same-issue-multi-skill
  `sys.exit` disambiguation message, and a ROSTER-key-shape comment.
- `gates/ci.py` — the CI-posted branch-shape denial message (`gh`-visible
  check output), the module docstring's `--autodetect` example, the
  comment block above `_ISSUE_SKILL_BRANCH`, and
  `_autodetect_issue_phase()`'s own docstring — all still said
  `issue-<n>/<role>`/"role 세그먼트" even though `_ISSUE_SKILL_BRANCH`
  itself already accepts any skill/lease token.
- `spawn.py` — five `role=` log-label prefixes in
  `_reconcile_pr_expected_missing()`/`reconcile()` (the value was
  already the skill variable — only the label was wrong), two
  `drive`-path status prints, the `--checkpoint` error's `APPROVE
  issue-<n>/<role>` example, a stale `resolved_role_model()` comment
  reference, and one rebase-conflict error message.
- `on-the-record/directive/delegation-loops.md` — issue #2139's own
  already-known finding A5 ("rulebook loaded"→"skill loaded"), and a
  fictional `spawn.py spawn <skill> "<task>" --issue <n> --background`
  invocation example rewritten to the real dispatch shape (verified via
  `python3 spawn.py --help` — the dispatch table has no `spawn`
  subcommand, the sole spawn form is `--skills`, and `--no-wait` is the
  real flag for "fork and return immediately, print the resume command"
  — `--background` does not exist as a flag).
- `test/test_consult_trace_commit.py`, `test/test_ps_live_reliability.py`
  — corollary fixes, not in the original site list: the `consult.py`
  parameter rename broke 5 keyword-argument call sites
  (`role="tester"`→`skill="tester"`), and the `board.py` print-string
  rewrite broke 5 literal-string assertions
  (`"역할 세션 없음"`→`"스킬 세션 없음"`) — both surfaced only by
  running the test suite after the Part A edits (see Invariant 2 below);
  fixed to keep the same behavioral assertions passing under the new
  wording, not a scope change.

**Invariant verification** (all 4 required checks; before = pre-edit
tree, after = post-edit tree including the two test-file corollary
fixes above):

1. Role-axis count must go down.
acceptance: `grep -rln '역할\|\brole\b' --include=*.py --include=*.md . | grep -vE '/(test|docs)/' | xargs -I{} grep -c '역할\|\brole\b' {} | awk -F: '{sum+=$1} END {print sum}'` — result:
```
before: 18994
after:  18938
```
Decreased by 56, as required (nonzero remainder is expected — e.g.
`role-or-skill` help text, the `APPROVE issue-<n>/<role>` token
vocabulary kept deliberately in sync with `gates/ci.py`'s still-"role"
regexes per the evidence comment's own "Kept, not relics" section).

2. No new bug — full test suite, failing-test-name sets compared.
acceptance: `python3 -m pytest test/ -q` (run before any Part A edit, then again after all edits including the two test-file corollary fixes) — result:
```
before: 15 failed, 441 passed, 3 xfailed
after:  15 failed, 441 passed, 3 xfailed
before-failure-set == after-failure-set (`diff` exit 0, all 15 are the
same pre-existing network-environment failures: "fatal: 'origin' does
not appear to be a git repository" inside bootstrap_fetch_and_record_sha,
unrelated to this delivery's write set)
```
AFTER-set minus BEFORE-set is empty — no newly-failing test survives in
the final tree (two transient regressions this session's own edits
caused along the way — 5 `test_consult_trace_commit.py` failures from
the `_commit_consult_trace` keyword-arg rename, 1
`test_ps_live_reliability.py` failure from the `board.py` string rewrite
— were caught by this same acceptance run and fixed before the final
comparison above).

3. No overhead increase — `delegation-loops.md` byte size.
acceptance: `wc -c on-the-record/directive/delegation-loops.md` — result:
```
before: 7986
after:  7983
```
Shrank by 3 bytes (word-level swaps of comparable or shorter length);
did not grow.

4. Monitor/watch machinery unbroken and not quieter.
acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py -q` — result:
```
before: 10 passed, 0 failed
after:  10 passed, 0 failed
```
derived: `git diff watchdog.py` shows only string-literal changes inside
existing `print(...)` calls at the same call sites (lines 1053, 1072-1078,
579, 1617) — no `print`/`sys.exit` call site was added, removed, or
made conditional; the board-sweep message and the `roster_ps`-style
"no live sessions" print still fire on the same conditions as before.

**GitHub comment posted**: the kind-lens evidence sweep, its full
per-row evidence table, and the disposition of the four prior issue
comments (dated 2026-08-24, 2026-08-27 x2, and 2026-08-29), is posted at
https://github.com/tokenmaxxxer/on-the-record/issues/2139#issuecomment-5467431758 .

**Filing new fix-issues was BLOCKED, not skipped.** This session attempted
no `gh issue create` call because the repo's own contract already settles
the question:
canonical: `gates/forbidden_action_rule.py:6-19,87-95` read this turn — the module docstring and its `check_issue_body()` refusal text both state that `gh-guard` refuses issue creation for every skill/role session ("issues are the user's requirement backlog, user-authored only", contract v3 s8/s9) — a two-account-model guard this delivery should not try to route around.
The three higher-stakes findings the prior evidence sweep surfaced (Actions
2-4 of that sweep) are therefore reported here in full instead of filed,
so nothing is lost to this session's own transcript:

**(1) `lifecycle.py` roster_kill/branch lease-suffix mismatch — a
potential blocking defect, unestablished.** `roster_kill()` and a
stale-branch flag (`lifecycle.py:436,566-581`) build the roster identity
key as `f"issue-{issue}/{skill}"` — no lease suffix — while the live
roster is lease-keyed via `roster.lease_key()`, used everywhere else a
roster entry is looked up (e.g. `spawn.py:4272`). If this mismatch is
real, a `roster_kill()` lookup can never hit a live lease-keyed roster
entry — it would silently no-op with "로스터에 없다" (not in roster)
instead of actually killing the session it was asked to kill. Not fixed
here: this is a functional-defect claim, not a wording fix, and needs
someone to trace `a.task`'s actual value at `spawn.py:2534` (the call
site that constructs the kill target) before it can be dispositioned as
a real defect versus an intentional lease-agnostic kill-by-bare-key
design. Filing this under the user's account, with that trace done
first, is the recommended next step.

**(2) directive/commands markdown pointing at deleted `roles/` paths.**
Three sites in `on-the-record/directive/` and `on-the-record/commands/`
still name a `roles/` directory that does not exist anywhere in the
current tree:
- `on-the-record/commands/report-upstream.md:17-18` — cites
  `roles/upstream-defect-report.json`.
- `on-the-record/commands/run.md:490-491` — cites a per-role catalog at
  `roles/<역할>.json`; `on-the-record/commands/consult.md` already
  documents the current skill-repository-directory-listing method
  correctly, so the fix is a rewrite pointing at that already-correct
  method, not new research.
- `on-the-record/directive/merge-gates.md:49-53` — cites
  `roles/specs/<role>.spec.json`; per `gates/quality_bar.py`'s own
  docstring, that file was deleted and replaced by the fixed 7-domain
  set inlined directly in `quality-bar-gate.sh` (#2539/#2610).
Not fixed here: each needs its correct current source-of-truth path
established before rewriting (the evidence sweep flagged these as
"reported only" for exactly that reason), not folded into this
delivery's mechanical word-swap scope.

**(3) Dead-code/rename-coordination bundle** — four independent items,
each needing a design judgment call this delivery deliberately stayed
out of:
- `directive_assembly.py:206-235` defines module-level
  `_HOOK_CONTRACT_PROSE` a second time at lines 288-348; the later
  definition always wins (both consumers — `spawn.py:607`,
  `directive_assembly.py:457,463` — read the module attribute only after
  both assignments have already executed). Open question: whether the
  content unique to the first (#2409) block was intentionally folded
  into the surviving (#2479) block, or silently dropped — needs a
  content diff before disposing either way.
- `pipeline.py:1172-1195` `checkout_issue_branch()` has zero production
  callers (`spawn.py:3799-3803` inlines the equivalent logic directly
  instead); its only caller anywhere is
  `test/test_branch_naming_dual_scheme.py:66`. Removing it would need to
  also touch that test file, widening this delivery's write set beyond
  its mechanical-wording scope.
- `spawn.py:4006` — the `_dp("role-skill-triggers", ...)` directive-diet
  component label is externally observed by literal string in at least
  one prior conformance-review report. Renaming it is itself a mechanical
  wording fix in spirit, but risks breaking whatever external process
  reads that literal string — needs that consumer identified first.
- `spawn.py:1984` — the `role_model.txt` filename (env override file for
  `--model` resolution) carries the same stale vocabulary; deferred
  rename, same externally-observed-name risk as the item above.

## Why

**Kind-lens rationale.** A word-grep for `역할`/`role` alone systematically
misses several classes of relic reference: a function/constant that was
already renamed leaves its OLD name alive only in comments/docstrings
that reference it by name (kind 5) — a plain grep for the retired Korean
word never sees an English identifier like `resolve_role_family_source`
unless it happens to also contain "role" as a substring match, which it
does, but the SHAPE of the defect (docstring pointing at a dead name) is
different from a wording relic and needs its own check to establish the
named thing no longer exists. Similarly, a trace-log field name
(`role=`, kind 7) is a live, machine-read format string, not decorative
prose — get it wrong and every downstream reader of that log
(`_judge_roles_run_today()`'s own grep-anchor, for one) is reading a
field whose name lies about what it holds. Kind 4 (live GitHub-posted
text) and kind 8 (directive prose an agent literally executes) both
carry a materially higher cost than a stray code comment: a
self-contradicting PR body misleads a human reviewer, and a fictional
CLI invocation in a directive an agent follows literally causes a
runtime error, not just a mis-read.

canonical: `gates/forbidden_action_rule.py:6-19` read this turn — same source cited above, re-read here to ground the two-account-model reasoning behind the batch-now-vs-report-later split below.

**Batch-now vs. report-for-later.** Everything landed in this delivery
satisfies the same three-part test: (a) touches only a comment/
docstring/error-string/log-format-string/trace-field-name/directive-prose
— never a conditional, a data shape a test pins byte-for-byte, or a
function's actual behavior; (b) the replacement is a same-length-class
word swap with an unambiguous correct target already visible in the
adjacent real code (the function's actual parameter name, the constant's
actual current spelling); (c) reversion cost of getting it wrong is a
second one-line fix, not a data-loss or availability incident. The three
findings held back — the `lifecycle.py` lease-key mismatch (a
behavior-change candidate, needs its reachability established before
anyone touches the kill path), the `roles/` directive rewrites (each
needs a source-of-truth established, not just a s/role/skill/), and the
dead-code/rename-coordination bundle (each item's correct disposition is
itself the judgment call, not something inferable from the surrounding
code alone) — all fail (b) or (c): each needs either new investigation
to get right, or carries a real behavior-change/breakage risk if
guessed wrong.

## Upstream basis

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5467431758 -q .body` read this turn — the comment's own "Status of the 2026-08-24/27/29 findings" section, re-verified against the current tree by this session's own edits and greps above.

This session re-verified the four prior issue comments on #2139, dated
2026-08-24, 2026-08-27 (two comments that day), and 2026-08-29:

- ALREADY FIXED (still fixed in the current tree, no regression): A1
  (hook deleted), A2 (row struck through, #2141), A3 (deadman wired,
  #2145), A4 (test-tier scoped to plugin, #2141), B1 (`consult.py`
  wording, #2722), B2 (`merge-gates.md` wording), B3 (supersession
  banner added), B4 (all 4 tracker files removed, #2141), B5 (LEGACY map
  flattened, #2654), B6 (documented in `docs/specs/env-knobs.md`),
  run.md rows 1 and 2 (both removed, #2697). `recut-corrupted --role`
  now hard-errors (`--role 는 은퇴했다`, #2595) rather than reaching
  git — no longer merely stale.
- STILL LIVE (still live before this session's edits, fixed by this
  delivery): A5
  (`on-the-record/directive/delegation-loops.md:14`, "rulebook loaded")
  and the watchdog board-sweep message (`watchdog.py:1072-1078`, still
  named `issue-<n>/<role>` format even though the command it suggests
  had already migrated to `--session`).

## Open findings

canonical: `gates/forbidden_action_rule.py:6-19,87-95` read this turn — same gh-guard source cited in "What was done" above, re-cited here to ground why these three items are open findings rather than fixes.

The three unfiled items from "What was done" above, cross-referenced
here per this delivery's own record convention:

1. `lifecycle.py:436,566-581` roster_kill/branch lease-suffix mismatch —
   see full write-up above. Resolution path: trace `a.task`'s actual
   value at `spawn.py:2534`, establish whether the mismatch is
   reachable, then file (or rule out) under the user's own account.
2. Three directive/commands rows pointing at a deleted `roles/`
   directory (`report-upstream.md:17-18`, `run.md:490-491`,
   `merge-gates.md:49-53`) — see full write-up above. Resolution path:
   establish each correct current source-of-truth path, then file a
   single follow-up covering all three (they share one relic shape).
3. Dead-code/rename-coordination bundle — `directive_assembly.py:206-235`
   duplicate `_HOOK_CONTRACT_PROSE` (needs a content diff before
   disposing), `pipeline.py:1172-1195` dead `checkout_issue_branch()`
   (needs its one test caller migrated first), `spawn.py:4006`
   `role-skill-triggers` label (needs its external string-matching
   consumer identified first), `spawn.py:1984` `role_model.txt` filename
   (same external-consumer risk). See full write-up above. Resolution
   path: each item needs its own small investigation before a rename/
   removal is safe; file as one tracking issue or four small ones, per
   the user's preference.
4. `directive_assembly.py`'s own `_RECORD_SKELETON` (around line 512)
   stamps every spawned session's own record frontmatter with a literal
   `role:` key — ironic, since this very record's own frontmatter
   (above) carries that same `role:` key, generated by that same
   skeleton. Not renamed in this record: doing so would be a repo-wide
   generator change affecting every future record's frontmatter shape,
   well outside this delivery's mechanical-wording-fix scope, and
   deserves its own scoped issue rather than a silent one-off deviation
   here.

## Next steps

Whoever picks up the 3 unfiled items (open findings 1-3 above) should
file them under the user's own account — `gh-guard` refuses issue
creation from any skill/role session, so this step cannot be done by a
spawned session no matter which one picks it up next. The bodies are
usable close to as-is: reconstruct each issue's exact text from the
full write-ups quoted in "What was done" / "Open findings" above (the
prior worker's own drafts existed only as files under `/tmp` in that
session's sandbox, which does not persist across sessions — this
record is now the durable copy of that content). Finding 4 (the
`role:` frontmatter key in `_RECORD_SKELETON`) should get its own
separate issue too, scoped explicitly to the generator change and its
blast radius across every future record, not bundled with the other
three.

skill-verdict: overengineering-audit — applied: invoked; used to check for unnecessary abstraction/scope growth framing before scoping this delivery to mechanical wording fixes only, deferring anything requiring a design judgment call
