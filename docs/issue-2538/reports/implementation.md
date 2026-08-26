---
issue: 2538
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: on-the-record/hooks/session-role-bind.sh
    sha: same-commit
code_under_review:
  - on-the-record/hooks/session-role-bind.sh
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/heredoc-command-refusal-gate.sh
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/retry-loop-bound.sh
  - on-the-record/hooks/spawn-allow-gate.sh
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/delegation-post-gate.sh
  - on-the-record/hooks/approach-cap-warning.sh
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/report-framing-check.sh
  - on-the-record/hooks/role-deviation-directive.sh
  - on-the-record/hooks/stop-gate.sh
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/record-claim-shape-directive.sh
  - on-the-record/hooks/stop-poll-rearm.sh
  - on-the-record/hooks/pretooluse_dispatcher.py
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/post-landing-obligation-gate.sh
type: refactor
breaking: "no — every migrated identity check preserves the identical allow/deny decision for identical input; verified live below (acceptance check 3), not just asserted"
verdict: pass
---

# issue-2538 — implementation record

## What was done

Stage 6B, part B of three (issue #2538, `Advances #2538`). Retired the role
*name* as a session-identity signal from `on-the-record/hooks/` and
dispositioned the `ROLES` tuple and the listed `roles/`-shaped path
strings. `roles/` itself is untouched — derived: `ls roles/ | wc -l` —
result: 45, same count `git show HEAD:roles` origin-tree listing has
(unchanged from HEAD).

**1. The `ROLES` tuple — kept, callers named, not renamed.**
derived: `grep -n '^ROLES *=' spawn.py` — result:
`694:ROLES = ("product-discovery", "interaction-design", ...)`. Two real
callers, both about enumerating the *set of legacy role names* for board
rendering, not session identity, so out of this issue's scope:
- `board.py` — canonical: board.py:717,744,770,782,788 (`_skill_axis_report_names`,
  `board()`, `status()`), read this session — issue #2432 stage-4
  dual-scheme coexistence: `_sp.ROLES` is the closed set of old-axis file
  stems `board()` walks alongside the open set of skill-axis record names.
- `on-the-record/monitors/poll-heartbeat.sh` — canonical: line 181
  (`print(' '.join(spawn.ROLES))`), read this session — enumerates the
  same set to build `POLL_HEARTBEAT_PATROL_ROLES`, the per-role
  patrol-promotion tick list.
No equivalent hardcoded list was reintroduced under another name — both
callers still call `spawn.ROLES` itself.

**2. 25 hooks — 17 migrated to `TOKENMAXXXER_SPAWNED`, 8 remain, each
decided per-hook per the issue's "not by sweep" instruction.**
derived: `grep -rl CLAUDE_ROLE on-the-record/hooks/ | grep -v test_ | wc -l`
on HEAD — result: 25 (matches the issue body's own count).

*Migrated (presence-only — the hook only ever tested truthiness of the
CLAUDE_ROLE-sourced value, never compared the role name itself; verified
by reading every downstream use of the variable in each file before
editing):*
- `deliverable-guard.sh`, `gh-write-allow-gate.sh`,
  `heredoc-command-refusal-gate.sh`, `decision-queue-stopgate.sh`,
  `retry-loop-bound.sh`, `spawn-allow-gate.sh`, `merge-allow-gate.sh`,
  `delegation-post-gate.sh`, `approach-cap-warning.sh` — all nine shared
  the identical "SessionStart snapshot first (session-role-bind.sh),
  live-env fallback" primitive, resolving to a bare `if role:` /
  `if not role:` test — canonical: each file's own identity block, read
  in full this session (e.g. gh-write-allow-gate.sh:58-77,
  deliverable-guard.sh:63-84, merge-allow-gate.sh:143-163). Now reads
  `TOKENMAXXXER_SPAWNED` instead of `CLAUDE_ROLE`, and the snapshot field
  is `spawned: true/false` instead of `role: "<name>"`.
  `TOKENMAXXXER_SPAWNED` is the correct replacement because it needs no
  identity at all, not because it's a stand-in role name: derived:
  `grep -n 'CLAUDE_ROLE\|TOKENMAXXXER_SPAWNED' pipeline.py consult.py` —
  result: both keys are written together on every spawn path
  (`pipeline.py:672`, `consult.py:748`, `consult.py:1069`,
  `consult.py:1436`), and derived: `grep -rn 'CLAUDE_ROLE' --include='*.py' . | grep -v test_ | grep -v 'on-the-record/hooks/'`
  — result: no other site in the repo sets `CLAUDE_ROLE` (only
  `spawn.py`'s own CLI-flag reader and `pipeline.py`/`consult.py`'s
  writers) — so the two are always co-present or co-absent today, and the
  substitution is behavior-identical by construction.
- `session-role-bind.sh` (the producer of the snapshot all nine above
  read): rewritten to gate on `TOKENMAXXXER_SPAWNED` and write
  `{"spawned": true}` instead of `{"role": "<value>"}`.
- `directive.sh`, `report-framing-check.sh`, `role-deviation-directive.sh`,
  `stop-gate.sh`, `product-capture-stopgate.sh`,
  `record-claim-shape-directive.sh`, `stop-poll-rearm.sh` — pure
  single-line bash presence gates (`[ -z/-n "${CLAUDE_ROLE:-}" ]`), no
  other role usage anywhere else in the file — derived:
  `grep -n '\brole\b\|CLAUDE_ROLE' on-the-record/hooks/<file>.sh` run
  individually against each of the seven before editing, each returning
  only the one gate line (plus unrelated prose mentions of "role" as an
  English word). Same substitution applied.
- `pretooluse_dispatcher.py` (`_pre_approval`) and
  `delegated-judgment-gate.sh` (line 314) — bare
  `bool(os.environ.get("CLAUDE_ROLE"))` / `if not os.environ.get("CLAUDE_ROLE")`
  presence checks with no snapshot fallback — canonical:
  pretooluse_dispatcher.py:234-237, delegated-judgment-gate.sh:308-314,
  read this session. Same substitution.
- `post-landing-obligation-gate.sh` — had no code dependency at all, only
  a comment describing merge-allow-gate.sh's own invariant — canonical:
  post-landing-obligation-gate.sh:150, read this session, was the only
  `CLAUDE_ROLE` hit in the file. Reworded the comment to say
  `TOKENMAXXXER_SPAWNED` so it stays accurate after merge-allow-gate.sh's
  migration. This dropped it off the grep list entirely.

*Intentional survivors (8 files still match the grep; each is either a
genuine per-hook decision to keep the value, or a documentation/advisory
string describing a still-surviving hook, not an independent code
dependency).* derived:
`grep -rl CLAUDE_ROLE on-the-record/hooks/ | grep -v test_` after all
edits — result:
```
on-the-record/hooks/approval-gate.sh
on-the-record/hooks/deviation-log-guard.sh
on-the-record/hooks/pretooluse_dispatcher.py
on-the-record/hooks/quality-bar-gate.sh
on-the-record/hooks/role-deviation-directive.sh
on-the-record/hooks/session-role-bind.sh
on-the-record/hooks/skill-verdict-guard.sh
on-the-record/hooks/upstream-defect-scope-guard.sh
```
- `approval-gate.sh` — code dependency, kept. Read past the snapshot block
  (canonical: approval-gate.sh:92-168, read this session): `role` is not
  merely tested for truthiness — it is cross-checked against
  `branch_role` (independently resolved from `.on-the-record/role.json`
  sidecar / branch-name regex, approval-gate.sh:111-152) at
  `if role != branch_role: sys.exit(0)`, and reused by *value* afterward
  to build `record_path`, the approval needle text — derived:
  `grep -n 'APPROVE issue-%d/%s' on-the-record/hooks/approval-gate.sh` —
  result: two sites build that needle from `(issue, role)` — and a past
  passing-record needle scan. This is issue #1821's "dual carrier"
  design: the session's *self-declared* identity (CLAUDE_ROLE, the only
  thing session-role-bind.sh's snapshot carries) is required to
  independently agree with the *workspace-derived* identity (sidecar/
  branch) before this write-time approval gate applies at all; on
  disagreement the gate backs off (`exit(0)`, i.e. allow) rather than
  narrowing what it enforces. Collapsing to `branch_role` alone would
  remove that independent corroboration — an orchestrator working inside
  a role's checkout would newly become subject to a gate meant only to
  police the role's own session. No lease/author-identity/record-kind
  signal is exposed into the session environment yet — derived:
  `grep -n 'CLAUDE_ROLE\|TOKENMAXXXER_SPAWNED' pipeline.py consult.py` —
  those are the only two identity-shaped keys either spawner writes — to
  serve as that second, independent, self-declared carrier, so weakening
  this specific check was the one edit in this issue most likely to
  violate "must not weaken any gate" — left alone.
- `upstream-defect-scope-guard.sh` — code dependency, kept — canonical:
  lines 59 and 97, read this session
  (`CHANNEL_ROLE = "upstream-defect-report"`;
  `channel_role_active = role == CHANNEL_ROLE`) — compares the live role
  to one specific literal name, at Bash-tool-call time, before any record
  exists — a genuine "which one role" question (issue #1171's own
  scoping fix, distinguishing the upstream-defect-report channel's own
  PR-creation attempts from an unrelated role's normal delivery-PR
  creation against the same origin repo). No record-kind or
  author-identity signal is resolvable this early (pre-record, live
  Bash-tool gate), so there is no non-role-name replacement available yet.
- `deviation-log-guard.sh` — code dependency, kept — canonical: line 149,
  read this session
  (`rel = os.path.join(base, role, "deviation-log") if role else ...`) —
  uses the role name as a literal path segment
  (`reports/<role>/deviation-log`), matching the write-scope directory
  convention — needed pre-record (the deviation log is appended to before
  any record file necessarily exists) so there is no author-identity/
  record-kind source to read instead. Path-string usage, not directory
  enumeration (`roles/` itself is never opened here), but genuinely
  value-dependent, not presence-only, so it does not fit the
  `TOKENMAXXXER_SPAWNED` substitution the other 17 hooks used.
- `quality-bar-gate.sh` — no code dependency — canonical: lines 29-35,
  read this session. `CLAUDE_ROLE` appears only in a comment explicitly
  documenting the anti-pattern this hook already avoids: "identity is
  account-resolved, never a bare CLAUDE_ROLE compare... both are real
  accounts, never a CLAUDE_ROLE string" (issue #1156's own
  anti-circularity design) — derived: `grep -n '\brole\b' on-the-record/hooks/quality-bar-gate.sh`
  — result: no code usage, comment-only. Left as accurate documentation
  of a deliberately-avoided pattern.
- `pretooluse_dispatcher.py` — no residual code dependency after the edit
  above; the two remaining lines are a comment describing
  approval-gate.sh's own surviving CLAUDE_ROLE dependency (see above), not
  an independent read.
- `session-role-bind.sh` — no residual code dependency; the remaining
  lines are the migration-rationale comment (explaining why the snapshot
  changed from `role` to `spawned`, and naming
  approval-gate.sh/upstream-defect-scope-guard.sh/deviation-log-guard.sh
  as the three hooks that still read CLAUDE_ROLE directly rather than this
  snapshot).
- `role-deviation-directive.sh` — the hook's own gate was migrated (see
  above); one advisory string shown to the model still names the env var
  because it is accurately describing deviation-log-guard.sh's real,
  surviving sharding convention — not a gating dependency of this file —
  derived: `grep -n 'CLAUDE_ROLE' on-the-record/hooks/role-deviation-directive.sh`
  — result: one hit, inside the heredoc text block, not the gate line.
- `skill-verdict-guard.sh` — no code dependency; `role` here comes from
  `branch_m.group(2)` (branch-name regex) — canonical: line 325, read
  this session — never from `os.environ`. The one `CLAUDE_ROLE`
  occurrence is inside a string literal (line 261) — an advisory message
  shown to the model, again accurately describing deviation-log-guard.sh's
  convention.

**3. At least three migrated hooks demonstrated live, same payload
before/after, both outcomes quoted** — see "Upstream basis" section below
for the exact commands and quoted output (`gh-write-allow-gate.sh`:
allow; `deliverable-guard.sh`: deny; `heredoc-command-refusal-gate.sh`:
deny — the third demo also exercises the opposite gate polarity, since it
fires ON spawned=true rather than off it).

**4. Path-string-only sites — each of the 12 listed modules plus 3 hooks
dispositioned.** derived: reading `roles/` in each of the 12 modules plus
3 hooks named in the issue body, one at a time, this session. 5 of them
turned out to be misclassified in the issue's own premise — derived:
`grep -n 'read_text\|\.glob(' gates/gates.py gates/roles_due.py directive_assembly.py on-the-record/hooks/record-scaffold.sh`
— result: each of those four files (`gates/gates.py` counted once,
`on-the-record/gates/gates.py` is its byte-identical duplicate — derived:
`diff gates/gates.py on-the-record/gates/gates.py` — result: no output,
i.e. identical) has a real `roles/`-content read — corrected below rather
than silently left as "path-string-only".

Genuinely path-string-only (glob/regex classification of already-known
file paths, or docstring examples — no `roles/` directory open/glob/stat
anywhere in the file); left as-is, no dangling-reference risk once part C
deletes `roles/` (a classifier that never matches again is harmless, not
broken):
- `gates/accumulation.py` — canonical: line 98, read this session
  (`re.match(r"^roles/[^/]+\.json$", rel)`) against already-enumerated
  changed-file paths.
- `gates/ci.py` — canonical: line 414, read this session — comment only
  (`roles/implementation.json` named in prose, no code reference).
- `gates/constitution_check.py` — canonical: `_glob_hit`, lines 39-47,
  read this session — the `roles/**` special-case matches an
  already-loaded frozen-decision glob pattern against an already-known
  touched-path string.
- `gates/frozen_decisions.py` — canonical: line 16, read this session —
  `"roles/**"` is a docstring *example* of the front-matter contract
  shape; the module parses `docs/decisions/*.md`, never `roles/` itself.
- `gates/patrol_board.py` — canonical: line 60, read this session
  (`entry["path"].startswith(f"roles/{role}/")`) classifies an
  already-loaded queue entry's own `path` field.
- `gates/quality_bar.py` — canonical: lines 1-30, read this session —
  docstring only; `bar_scoped_roles`/`classify` take `role_path_patterns`
  as a parameter, never read `roles/` themselves.
- `gates/skip_eligibility.py` — canonical: lines 11 and 50, read this
  session — `HARD_TO_REVERT_RE` classifies already-diffed changed-file
  paths.
- `on-the-record/hooks/accumulation-claim-guard.sh` — canonical: line
  114, read this session — `_touches_shape_5`, the session-side mirror of
  `accumulation.py`'s same regex, same non-reading classification.
- `on-the-record/hooks/quality-bar-gate.sh` — canonical: line 17, read
  this session — docstring only, mirrors `gates/quality_bar.py`.

Misclassified in the issue text — these actually call
`open()`/`.read_text()`/`.glob()` against `roles/`, just not on the same
line as the `"roles"` string literal (path built on one line, read on a
later line). #2537's own measured grep methodology is explicitly
same-line (canonical: `gh issue view 2537` — its own quoted command is
`grep -nE '(open|glob|iterdir|exists|read_text|is_dir|is_file|listdir)' <file> | grep roles`),
so it would have missed this two-line shape too. Left untouched — these
are real readers, #2537's/part-C's territory, not mine to fix under a "do
NOT touch the real readers" instruction, but flagging the discrepancy so
#2537 or a follow-up corrects its count:
- `gates/gates.py` — canonical: `record_enums` lines 326-329
  (`role_file = ON_THE_RECORD_ROOT / "roles" / f"{role}.json"` then
  `role_file.read_text(...)`) and `role_scope` lines 879-880, both read
  this session.
- `on-the-record/gates/gates.py` — byte-identical duplicate (see the
  `diff` result above), same finding applies.
- `gates/roles_due.py` — canonical: `_specs_dir` (line 45:
  `root / "roles" / "specs"`) and `load_triggered_specs` (line 58:
  `d.glob("*.spec.json")`), both read this session — an actual directory
  enumeration.
- `directive_assembly.py` — canonical: lines 590 and 622, read this
  session — derived: `grep -n 'read_text' directive_assembly.py` —
  result: two sites, `(_sp.ROOT / "roles" / f"{role}.json").read_text(...)`
  and `(_sp.ROOT / "roles" / "specs" / f"{role}.spec.json").read_text(...)`.
- `on-the-record/hooks/record-scaffold.sh` — canonical: lines 32-33, read
  this session (`role_file = plugin_root / "roles" / f"{role}.json"` then
  `json.loads(role_file.read_text(...))`).

`gates/closure_sweep.py` — canonical: line 459, read this session
(`git ls-files roles/*.json`) — a count-only enumeration via git
subprocess (not `open`/`glob`/`stat`, so it wasn't caught by #2537's grep
either, and it doesn't crash on a missing directory — after part C it
degrades to an empty list, not an error). Neither a clean "never reads"
case nor a fragile "real reader" — left as-is with this note rather than
silently bucketed either way.

`gates/gates.py`'s `PROTECTED_ROOT_DIRS = {"roles", "gates", ...}` —
canonical: line 36, read this session — is a third category: a literal
directory-name membership check that correctly still names the live
directory today — not identity logic at all, and not something to change
ahead of part C's actual deletion.

## Why

The issue's own instruction — "decide per hook, not by sweep" — is the
central design constraint here. A single global sed-replace of
`CLAUDE_ROLE` to some other name would have satisfied the grep-count
acceptance check without actually addressing the risk the issue calls out
("a hook that stops refusing is worse than one that refuses wrongly"):
three of the 25 hooks (`approval-gate.sh`, `upstream-defect-scope-guard.sh`,
`deviation-log-guard.sh`) genuinely consume the role *value*, not just its
presence, for reasons specific to each hook's own design history (dual
carrier corroboration, one-specific-role scoping, pre-record path
construction) — blindly swapping those would have either broken the
check (a `TOKENMAXXXER_SPAWNED` boolean can't reproduce a role-name
comparison or a path segment) or silently narrowed/widened what the gate
enforces, which the acceptance criteria explicitly forbid. So each of the
25 was read in full — not just the grep-matched line, but every
downstream use of the resulting variable — before deciding whether it was
presence-only (migrate) or value-dependent (survivor, and say why).

`TOKENMAXXXER_SPAWNED` was chosen as the presence-only replacement (over
inventing a new flag, or exposing a new lease/author-identity primitive)
because it is not a new signal — it already exists, is already written on
every session-spawn path pipeline.py/consult.py control, and is already
semantically a provenance flag ("this session's prompt was written by the
orchestrator, not a human turn" — canonical: pipeline.py:576-579, read
this session), not a role-name carrier. Reusing it is the "genuinely
needs no identity at all" branch the issue explicitly sanctions, and it
is strictly narrower in scope than minting new plumbing (author-identity/
lease into the session env) that stage 3 has proposed but not landed —
building that now would have been scope creep into #2537/a future stage,
not this issue's ask.

The path-string-site investigation surfaced a premise error in the
issue's own text (some of the 12 listed "never reads" modules do read,
just split across two lines — see the "misclassified" list above) rather
than something I could silently work around: correcting it in the record,
with citations, was the only honest option — asserting "left as-is,
doesn't read" for a function that literally calls `.read_text()` a few
lines below the `"roles"` string would have been a false claim under this
repo's own citation discipline.

## What did not work

No edit was made and reverted, and the two-phase default was correctly
bypassed under `CORE_BUILD_NOW=1` (spawner-set, verified: canonical: this
session's own environment, `CORE_BUILD_NOW=1` was present at session
start) with no deviation from that path.

One pre-existing, unrelated environment quirk was found and is worth
recording so it isn't mistaken for a regression: `decision-queue-stopgate.sh`
raises `E2BIG` ("인수 명단이 너무 김") in this sandbox on an empty-stdin
smoke test, both before and after this change. derived:
`git stash push -- on-the-record/hooks/decision-queue-stopgate.sh && echo '{}' | bash on-the-record/hooks/decision-queue-stopgate.sh; git stash pop`
— result: the unmodified HEAD version, run at its real path, fails with
the identical `E2BIG` message and exit code 126 as the edited version.
Root cause: the script resolves and executes `spawn.py flows --json` for
real (unlike a `/tmp`-copied comparator, whose self-location logic can't
find spawn.py outside the real checkout tree and silently no-ops
instead), and whatever `spawn.py flows --json` returns in this sandbox is
apparently large enough to hit this environment's `E2BIG` — unrelated to
the CLAUDE_ROLE-to-TOKENMAXXXER_SPAWNED migration, since HEAD reproduces
it identically. Not investigated further — out of this issue's scope.

## Upstream basis

- `gh issue view 2538` (canonical, read at session start) — the Ask,
  Non-goals, and Acceptance sections quoted/paraphrased above.
- `gh issue view 2537` (canonical, read this session) — confirms the
  "five real readers" (`consult.py`, `gates/risk_report.py`,
  `pipeline.py`, `gates/flows.py`, `gates/patrol_wiring.py`) are a
  different set than the 12 files this issue lists as path-string-only,
  and confirms #2537's own measured grep methodology (same-line `roles`
  plus read-verb co-occurrence), which is the basis for the
  "misclassified" finding above.
- Acceptance check 1 — derived: `grep -rl CLAUDE_ROLE on-the-record/hooks/ | grep -v test_`
  — result (executed after all edits):
  ```
  on-the-record/hooks/approval-gate.sh
  on-the-record/hooks/deviation-log-guard.sh
  on-the-record/hooks/pretooluse_dispatcher.py
  on-the-record/hooks/quality-bar-gate.sh
  on-the-record/hooks/role-deviation-directive.sh
  on-the-record/hooks/session-role-bind.sh
  on-the-record/hooks/skill-verdict-guard.sh
  on-the-record/hooks/upstream-defect-scope-guard.sh
  ```
  8 files, down from the 25 named in the issue; each named above with
  reason and replacement identity (or "no identity, comment/advisory-text
  only").
- Acceptance check 2 — derived: `grep -n '^ROLES *=' spawn.py` — result:
  `694:ROLES = ("product-discovery", "interaction-design", ...)`. Kept,
  callers named above (`board.py`, `on-the-record/monitors/poll-heartbeat.sh`),
  not renamed or duplicated.
- Acceptance check 3 — three migrated hooks demonstrated live, same
  payload before/after, both outcomes quoted. derived: commands run from
  the repo root; "before" ran the unmodified HEAD content
  (`git show HEAD:<path>`) at a scratch path, "after" ran the current
  working tree at its real path (payloads built to avoid the harness's
  own heredoc-refusal gate firing on the demo command itself):

  **gh-write-allow-gate.sh** (orchestrator-only allow gate), payload
  `{"session_id":"demo1","tool_name":"Bash","tool_input":{"command":"gh issue comment 5 --body \"hi\""}}`:
  ```
  BEFORE, orchestrator (CLAUDE_ROLE unset):
  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": "gh-write-allow-gate: orchestration session (CLAUDE_ROLE unset) invoking a recognized gh issue/pr write verb with no unquoted shell chaining — issue #856."}}
  exit=0
  BEFORE, role session (CLAUDE_ROLE=implementation):
  (no output) exit=0
  AFTER, orchestrator (TOKENMAXXXER_SPAWNED unset):
  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": "gh-write-allow-gate: orchestration session (not spawned) invoking a recognized gh issue/pr write verb with no unquoted shell chaining — issue #856."}}
  exit=0
  AFTER, role session (TOKENMAXXXER_SPAWNED=1):
  (no output) exit=0
  ```
  Identical allow/no-op decisions before and after; only the human-readable
  reason string's parenthetical changed.

  **deliverable-guard.sh** (orchestrator-only deny gate), payload
  `{"session_id":"demo2","tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"x=1"}}`:
  ```
  BEFORE, orchestrator (CLAUDE_ROLE unset):
  orchestrate: PreToolUse payload is missing an absolute cwd — cannot verify this write's target relative to the session's actual working directory, denying rather than silently resolving a relative cwd against the hook process's own unrelated cwd.
  exit=2
  BEFORE, role session (CLAUDE_ROLE=implementation):
  (no output) exit=0
  AFTER, orchestrator (TOKENMAXXXER_SPAWNED unset):
  orchestrate: PreToolUse payload is missing an absolute cwd — cannot verify this write's target relative to the session's actual working directory, denying rather than silently resolving a relative cwd against the hook process's own unrelated cwd.
  exit=2
  AFTER, role session (TOKENMAXXXER_SPAWNED=1):
  (no output) exit=0
  ```
  Byte-identical deny message and exit code for the orchestrator case;
  identical silent-allow (exit 0) for the role-session case.

  **heredoc-command-refusal-gate.sh** (role-only deny gate — opposite
  polarity, fires ON spawned rather than off it), payload
  `{"session_id":"demo3","tool_name":"Bash","tool_input":{"command":"git commit -m \"$(cat <<EOF\ntitle\nEOF\n)\""}}`:
  ```
  BEFORE, role session (CLAUDE_ROLE=implementation):
  heredoc-command-refusal-gate: heredoc-shaped commit message body detected — the host's write-capable-command classifier refuses this shape as un-analyzable. Use two -m flags instead of a heredoc: git commit -m "<title line>" -m "<body line>" (one -m per paragraph; never a heredoc/$(cat <<EOF ...) body) — issue #1976.
  exit=2
  BEFORE, orchestrator (CLAUDE_ROLE unset):
  (no output) exit=0
  AFTER, role session (TOKENMAXXXER_SPAWNED=1):
  heredoc-command-refusal-gate: heredoc-shaped commit message body detected — the host's write-capable-command classifier refuses this shape as un-analyzable. Use two -m flags instead of a heredoc: git commit -m "<title line>" -m "<body line>" (one -m per paragraph; never a heredoc/$(cat <<EOF ...) body) — issue #1976.
  exit=2
  AFTER, orchestrator (TOKENMAXXXER_SPAWNED unset):
  (no output) exit=0
  ```
  Byte-identical deny message and exit code for the role-session case;
  identical silent-allow for the orchestrator case.

- Acceptance check 4 — path-string sites — see "What was done" section 4
  above; each of the 12 listed modules plus 3 hooks dispositioned by
  citation, with the premise correction called out explicitly.
- derived: `bash -n` run individually on all 19 edited `.sh` files, and
  `python3 -m py_compile on-the-record/hooks/pretooluse_dispatcher.py` —
  result: no syntax errors on any file.
- derived: `git diff --stat` — result: 20 files changed, 192
  insertions(+), 144 deletions(-); derived: `ls roles/ | wc -l` — result:
  45 (unchanged from HEAD, part C's deletion has not run).

skill-verdict: work-in-english — applied: invoked; used throughout this
session for code comments, commit message, and this record — final
user-facing summary written in Korean per the skill.
skill-verdict: merge-gates — not-applicable: this issue edits identity
sources inside already-existing gates, it does not design a new merge
gate or decide how to cut work into parallel pieces before spawning;
avoided collision with the concurrent #2537 session by reading its issue
text and its file list directly, not by the skill's merge-gate procedure.

## Open findings

- The "misclassified real reader" discrepancy in #2537's own same-line
  grep count (gates/gates.py, on-the-record/gates/gates.py,
  gates/roles_due.py, directive_assembly.py, record-scaffold.sh — derived:
  `grep -n 'read_text\|\.glob(' gates/gates.py gates/roles_due.py directive_assembly.py on-the-record/hooks/record-scaffold.sh`,
  see "What was done" section 4) is flagged in this record but not filed
  as a separate issue — resolution path: whoever picks up #2537 or part C
  (roles/ deletion) should re-run a cross-line-aware read-site count
  before relying on "five modules" being exhaustive.
- `gates/closure_sweep.py`'s `git ls-files roles/*.json` count-only
  enumeration is neither cleanly "never reads" nor a fragile "real
  reader" — resolution path: no action needed before part C (it degrades
  to zero, not an error), but part C's own session should still notice it
  when grepping for `roles/` references.
- The `decision-queue-stopgate.sh` E2BIG environment quirk (see "What did
  not work" — derived:
  `git stash push -- on-the-record/hooks/decision-queue-stopgate.sh && echo '{}' | bash on-the-record/hooks/decision-queue-stopgate.sh; git stash pop`,
  confirmed identical on HEAD) — resolution path: none needed for this
  issue; would need separate investigation into what
  `spawn.py flows --json` returns in this sandbox if anyone wants to
  chase it.

## Next steps

None — loop_state is terminal (`landed`). derived:
`grep -rl CLAUDE_ROLE on-the-record/hooks/ | grep -v test_ | wc -l` —
result: 8 (down from 25), and `grep -n '^ROLES *=' spawn.py` — result:
line 694 still present with callers named — both acceptance checks 1-2
pass by this session's own executed commands, and checks 3-4 are quoted
live in "Upstream basis" above. Part C (delete `roles/`) is a separate
issue (#2539) and depends on #2537 (the five real readers) landing first,
not on this issue beyond what is already done here.
