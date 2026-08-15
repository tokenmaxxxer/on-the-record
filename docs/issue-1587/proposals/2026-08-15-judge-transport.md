---
status: proposed
files:
  - spawn.py
  - gates/patrol_queue.py
  - docs/handbooks/spawn.md
  - test/test_spawn_judge.py
---

# `judge` transport — read-only budgeted role judgment over a merge diff

## Request

Add a `spawn.py judge <role> --merge <sha> [-C <repo>]` transport: a read-only
session (git plumbing only, no Write/no gh) that judges whether a merge's diff
violates a role's rulebook, compresses the diff PR-Agent-style under an input
token cap, runs a cheap relevance prefilter and a cheap validator pass around
the judge call, and — only for validated findings — appends to the tier-1
patrol queue (`gates/patrol_queue.py`, lane=diff). Every run leaves a trace
line, success or failure, in `docs/reports/patrol-judge-log.md`. Per-merge caps:
3 judged roles, 120s per judge call.

## Constraints

- Read-only by construction: no Write/Edit tool, Bash restricted to git
  plumbing subcommands (`git show`, `git diff`, `git log`) — no `gh ` anywhere
  in the judge code path (grep-checkable, per the issue's acceptance list).
  Session settings, not prompt text, must enforce this.
  canonical: docs/issue-1587/reports/implementation/survey.md, "Read-only session construction" section, read in full this session.
- Delivery-hook isolation happens at plugin-dir selection (which
  `--plugin-dir` args reach the argv), not via an in-prompt override string —
  the issue explicitly rejects the #1097-style prompt-suppression pattern
  `consult_cmd()`/`_verb_cmd()` currently use for this purpose.
- Diff read locally from the clone — zero GitHub API calls (R3).
- Judge input capped ~15-20k tokens with graceful degradation to name lists,
  not a hard failure, when a diff is large.
- Judge session: max-turns 4-6, agentic-with-leash (may expand via targeted
  `git show` on suspicion, bounded by the turn cap).
- Two Haiku-tier side calls: a prefilter before the judge call (skip judge
  entirely on jurisdiction miss — issue names this the largest cost saver)
  and a validator after it (refute-or-confirm + per-role exclusion list).
- Queue write goes through the existing `enqueue()` (gates/patrol_queue.py:65)
  unchanged, with `lane="diff"`.
- Trace-always: one line per judge run in docs/reports/patrol-judge-log.md
  regardless of outcome, mirroring the consult-log `finally`-block convention
  (spawn.py:5290-5296).
- Depends on tokenmaxxxer-core#216 for the read-only-session integration test
  against a repo with a malformed proposal; if #216 has not landed by the time
  this work reaches that test, it is recorded as a deferred check, not a
  blocker.

## Rationale

**Chosen: a new `judge_cmd()` reusing `_consult_cmd_and_env()` for session
assembly only, with its own 4-stage pipeline (prefilter → judge → validator →
enqueue) and its own trace trio.**

Alternative considered and rejected: extend `_verb_cmd()` (spawn.py:5340) with
a `"judge"` entry in `_VERB_INSTRUCTIONS`/`_VERB_JSON_SHAPE`, the same way
ideate/draft/review were added. Rejected because `_verb_cmd()`'s shape is
exactly one `claude -p` call in, one JSON verdict out (spawn.py:5379-5398) —
it has no place for a prefilter call before the main session, no place for a
validator call after it, and no place for a patrol-queue write as a side
effect of a successful call. Bending `_verb_cmd()` to fit judge's four stages
would either (a) special-case judge inside the shared helper, defeating the
reason `_verb_cmd()` exists (one shared loop for verbs that really do share
one shape), or (b) grow `_verb_cmd()`'s signature with judge-only parameters
that ideate/draft/review never use. A dedicated `judge_cmd()` keeps the shared
helper's contract intact for its existing three callers and gives judge's
distinct pipeline its own function, while still reusing
`_consult_cmd_and_env()` — the actual duplication risk the codebase already
guards against (spawn.py:5181-5184's stated reason for factoring that helper
out in the first place).

Second alternative considered and rejected for the isolation mechanism:
reuse consult's in-prompt override string ("이 세션에 로드된 룰북/훅이 ...")
to tell delivery hooks to stand down for judge sessions too. Rejected because
the issue is explicit that judge's isolation must be structural (plugin-dir
selection), not a request the model can be persuaded out of by hostile diff
content in a judged merge — a prompt-injection surface consult's own pattern
doesn't need to defend against (consult's input is a hand-typed question, not
attacker-controlled diff text).

## What will be done

1. Add `JUDGE_TIMEOUT = 120` alongside `CONSULT_TIMEOUT`/`PANEL_TIMEOUT`
   (spawn.py:64-65) and a `JUDGE_MAX_ROLES_PER_MERGE = 3` constant.
2. Add `_readonly_plugin_dirs(role, spec)`: like `plugin_dirs()` +
   `core_plugin_dirs()` combined, but filters `core_plugin_dirs()`'s list to
   exclude delivery-oriented core plugins (scout/proposal-shape/freelunch/
   hunt-guard and siblings) before they ever reach `--plugin-dir` — the
   isolation point the issue requires.
3. Add `_readonly_bash_allow()`: an allow-list of `git show`/`git diff`/
   `git log` prefixes only, following `_workspace_bash_allow()`'s shape
   (spawn.py:471-488), and a settings assembly path that omits Write/Edit/gh
   entirely (no deny-list needed if the allow-list never grants them).
4. Add `_compress_diff(diff_text, cap_tokens=18000)`: PR-Agent-style
   compression — additions weighted over deletions, deleted files collapsed
   to a name list, deletion-only hunks stripped, ±3-10 line context window,
   truncate to name lists when still over cap.
5. Add `_judge_prefilter(role, diff_summary) -> bool` and
   `_judge_validate(role, findings, diff) -> list[dict]`: both single
   Haiku-tier `claude -p` calls (`--model` pinned explicitly, not
   `resolved_role_model()`), JSON-parsed the same way `_parse_verb_json()`
   already does.
6. Add `judge_cmd(role, merge_sha, cwd=None) -> dict`: assembles the
   read-only session via `_consult_cmd_and_env()` (passing the filtered
   plugin-dir list and read-only settings from steps 2-3), builds the
   compressed diff via step 4, runs the prefilter (step 5) and returns early
   (traced, no judge call) on a miss, otherwise runs the judge session
   (rulebook prefix cached via `cache_control`, max-turns 4-6), runs the
   validator (step 5) on any findings, and for each validated finding calls
   `gates.patrol_queue.enqueue()` with `lane="diff"`. Wraps everything in a
   `try/finally` that always appends one line to
   `docs/reports/patrol-judge-log.md`, mirroring
   `_append_consult_trace()`/`_commit_consult_trace()`'s shape but its own
   path constant.
7. Add a `judge` CLI subcommand (`argparse` `add_parser("judge")`) taking
   `role`, `--merge <sha>`, `-C <repo>`, enforcing the 3-roles-per-merge cap
   when called with multiple roles for the same sha (state tracked via the
   trace log itself — count today's lines for this sha before dispatching a
   4th).
8. Tests in test/test_spawn_judge.py, subprocess-mocked per existing spawn
   test conventions: read-only settings assembly (no Write/Edit tools, no
   `gh` in the Bash allow-list), plugin-dir filtering excludes delivery
   plugins, diff-compression cap behavior, prefilter-skip path (no judge
   subprocess call made), validator-drop path (finding never reaches
   `enqueue()`), queue append with lane="diff", and trace-always (one line
   written on both a simulated success and a simulated subprocess failure).
9. docs/handbooks/spawn.md: document the new verb (env vars if any, the
   `--merge` flag, the budget constants) per the doc-placement ladder.
10. One real measured run against a recent merge of this repo, recorded
    under docs/issue-1587/reports/ (tokens in/out, wall-clock, findings
    before/after validator) — done as part of phase-2 build, not this
    proposal.

## Accumulation

This adds three new subprocess-spawning call sites (prefilter, judge session,
validator) alongside the four that already exist for consult/ideate/draft/
review (spawn.py:5266-5267, spawn.py:5380-5381, spawn.py:5266 reused inside
`_run_panel_session`). All three new sites go through `_consult_cmd_and_env()`
for argv/env assembly, same as the existing four — this proposal does not add
a fifth inline `subprocess.run(["claude", "-p", ...])` construction pattern,
it adds three more callers of the one shared builder. If a future sibling verb
needs the same read-only isolation judge introduces
(`_readonly_plugin_dirs`/`_readonly_bash_allow`), those two new helpers become
the second call site rather than a second copy — they are written as
standalone functions for exactly that reuse, not inlined into `judge_cmd`.
The `gh ` grep-checkable constraint does not accumulate: judge's Bash
allow-list is a fixed 3-entry tuple (show/diff/log), not a per-repo or
per-role list that grows over time.

## Out of scope

- Any change to `gates/patrol_queue.py`'s `enqueue()`/`fingerprint()`/lane
  logic — the survey found no interface gap; judge is a new caller only.
- Board writes, issue creation, or GitHub API calls of any kind — that is
  #1586/C's layer per the issue text, not judge's.
- The tokenmaxxxer-core#216 scope-gate read-only fix itself — judge's
  integration test against a malformed-proposal repo is deferred until #216
  lands, per the issue's own dependency note.
- Wiring judge into an automatic drive/patrol loop — this issue delivers the
  transport (`spawn.py judge`) callable directly; scheduling it after every
  merge is a separate concern the issue does not ask for here.

## How you'll know it worked

- `python3 -m pytest test/test_spawn_judge.py -v` passes, covering every item
  in step 8 above.
- `grep -rn "gh " spawn.py` inside the judge-specific functions (`judge_cmd`,
  `_readonly_plugin_dirs`, `_readonly_bash_allow`, `_compress_diff`,
  `_judge_prefilter`, `_judge_validate`) returns no match.
- A real `spawn.py judge <role> --merge <sha>` run against a recent merge of
  this repo completes within 120s, appends exactly one line to
  docs/reports/patrol-judge-log.md, and (if it produced a validated finding)
  one entry to `.on-the-record/findings/queue.jsonl` with `lane: "diff"`.
