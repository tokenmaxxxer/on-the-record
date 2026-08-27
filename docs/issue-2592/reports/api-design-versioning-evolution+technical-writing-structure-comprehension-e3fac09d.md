---
issue: 2592
role: api-design-versioning-evolution+technical-writing-structure-comprehension-e3fac09d
author: api-design-versioning-evolution+technical-writing-structure-comprehension-e3fac09d
loop_state: landed
upstream:
  - path: gh issue view 2592
    sha: same-commit
code_under_review:
  - spawn.py
  - events.py
  - directive_assembly.py
  - pipeline.py
  - watchdog.py
  - on-the-record/directive/merge-gates.md
  - on-the-record/directive/spawn-and-board.md
type: fix
breaking: true
verdict: pass
---

# issue-2592 — api-design-versioning-evolution+technical-writing-structure-comprehension-e3fac09d record

## What was done

canonical: `gh issue view 2592` output (Ask/Acceptance/Non-goals)

Renamed spawn.py's `--role` CLI flag to `--session` everywhere it
appears — argparse definition, three usage/help strings, and the
`spawn.py:3630` self-invocation — landed in one commit as the issue
required. Acceptance requirement met — checked: `python3 spawn.py watch`
(no `--issue`) — result: `사용법: spawn.py watch --issue <n> [--session
<slug>] [--stall-timeout <분>], 또는 spawn.py watch --all` (no `역할`).

The old flag is removed outright, not aliased. Acceptance requirement
met — checked: `python3 spawn.py watch --issue 1 --role foo` — result:
rejected before argparse even runs, `spawn.py: --role 는 은퇴했다(이슈
#2592) — 세션을 고르는 건 역할이 아니라 슬러그다. 대신 --session <slug>
를 써라`, exit 1. A pre-parse guard (spawn.py, right before `a =
ap.parse_args()`) checks `sys.argv` for `--role`/`--role=...` and exits
with this message — naming the replacement, unlike argparse's generic
"unrecognized arguments" — matching the #2572 precedent the issue cites.

Acceptance requirement met — checked: seeded an isolated
`MUSTER_STATE_ROOT` workspace index entry, then ran `python3 spawn.py
watch --issue 999999 --session verify-session-e3fac09d --rearm
--stall-timeout 0.02 -C <scratch dir>` — result: `[watch]
issue-999999/verify-session-e3fac09d: 워처 재무장 pid 3018023 (로그
...)`; `ps -p 3018023 -o pid,args=` showed the live process command line
`... watch --issue 999999 --session verify-session-e3fac09d --follow
--self-heal --stall-timeout 0.02` — the armed watcher carries the new
flag. Re-verified identically after the pre-parse-guard edit (pid
3026641, same command shape). Both scratch processes/dirs were killed
and removed after inspection.

Both changes (flag removal + self-invocation fix) land in this same
commit — checked: `git diff --stat` at commit time shows `spawn.py`
(argparse def + `_spawn_one`'s Popen call) in one uncommitted diff prior
to the single commit this record accompanies.

Beyond the issue's named site list, a grep sweep (derived:
`grep -rn -- "--role" on-the-record/` plus a repo-wide
`grep -rn -- "--role"` filtered to code/docstrings referencing
spawn.py's watch/await-approval/recut-corrupted) turned up two more live
self-invocation sites carrying the same broken flag, which had to move
in the same commit for the removal to be safe:

- `events.py:903` (`_rearm_watcher_detached`, backing `spawn.py watch
  --rearm`) re-invokes spawn.py with `--role` the same way
  `spawn.py:3630` does.
- `directive_assembly.py:55` and `:97` (`_CHECKPOINT_CONTRACT_BLOCK` /
  `_checkpoint_index_block`) generate the literal `await-approval
  --issue <n> --role <role>` Bash command that checkpoint-mode role
  sessions are instructed to run verbatim.

Also updated (pure text, no executable consumers): two printed
suggested-command strings in `spawn.py`'s `watchdog_check_one` anomaly
messages, the equivalent ones in `events.py`'s `_ambiguous_watch_exit`/
`_lookup_roster_entry` docstring, one in `watchdog.py:_board_wide_sweep`,
one docstring in `pipeline.py:recut_corrupted_cli`, and the two
on-the-record/ directive prose references (`merge-gates.md`,
`spawn-and-board.md`).

## Why

The flag selects which session under an issue to act on, not a role —
the role axis is already gone. `--session` names what it actually
selects.

Hard removal (no alias) follows the api-design-versioning-evolution
consult the issue cites. derived: `git show
6efe62ff:docs/issue-2139/reports/consult-log/20260827T034114401854-2957145.md`
— consult-log entry confirms a `skill_judge` verb ran against this exact
question (verbatim: "spawn.py has a flag --role (dest watch_role) used
by three subcommands... purely to select WHICH session/branch") on
2026-08-27T03:41 UTC under `role=api-design-versioning-evolution`,
`issue=2139`; the two commits carrying this consult-log
(`6efe62ff`, `b60843fa`) exist on `main` per `git branch --all --contains
6efe62ff` but are untracked on this branch (this branch was cut before
they merged) — `docs/issue-2139/` does not exist in this worktree.

Independently of that consult, this session also loaded the
api-design-versioning-evolution skill directly this turn (per the
skill-obligations directive) and applied its rule 4 (Google AIP-180:
removal of any existing component is backward-incompatible) to classify
this change as breaking — see `breaking: true` in frontmatter — and its
rules 9-10 (external sunset/Deprecation-header machinery) as
inapplicable here: an internal dev-tool CLI has a closed, in-repo
consumer set (this commit updates every call site directly), not an
unknown external consumer base a header could notify.

The pre-parse guard (rather than relying on argparse's default
"unrecognized arguments" rejection) exists specifically to satisfy the
"naming the replacement" half of the #2572 precedent — argparse's own
message doesn't mention what to use instead.

skill-verdict: api-design-versioning-evolution — applied: invoked; loaded
via Skill tool this session, rule 4 used to classify the flag removal as
breaking (frontmatter `breaking: true`), rules 9-10 judged inapplicable
to an internal CLI with a closed consumer set (see rationale above)
skill-verdict: technical-writing-structure-comprehension — applied: invoked;
loaded via Skill tool this session, applied when rewriting the
`--session` help text and the new pre-parse-guard error message (short,
~15-20-word sentences split on em dash/period rather than one long run-on)

## What did not work

None.

## Upstream basis

derived: `git show 6efe62ff:docs/issue-2139/reports/consult-log/20260827T034114401854-2957145.md`
(reproduced above, under Why); `git branch --all --contains 6efe62ff`
returns `main`, confirming the commit is real and reachable from main,
not a dangling/unreachable object

- `gh issue view 2592` (same-commit): the Ask, Acceptance, and Non-goals
  read at the start of this session — canonical source for the flag
  rename requirement, the hard-removal-not-alias constraint, and the
  same-commit-as-3630 constraint.
- `docs/issue-2139/reports/consult-log/20260827T034114401854-2957145.md`
  (untracked on this branch, sha 6efe62ff15aded005cd5ea34c7e4daab2bf2e7b7):
  the api-design-versioning-evolution consult the issue cites —
  committed on `main` per the `derived:` check above, not yet merged
  into `issue-2592/...e3fac09d`. Read via `git show 6efe62ff:...`, not
  from this branch's working tree.

## Open findings

canonical: warrant-hunter agent `aec6c4fe94319c475` task-notification
result (before-landing dispatch, stance "assume this guard goes silent
when its own input is malformed — make it go silent", tier
size:21-200-lines/120s cap)

- Hunter tried `--role` after a `--` separator, `--role=value`,
  argparse-prefix abbreviation (`--rol`), case variants (`--ROLE`), and a
  repo-wide grep for any remaining spawn.py caller still passing literal
  `--role`. Verbatim verdict: "Every gap I found (--rol, --ROLE) does
  slip past the custom guard, but argparse's own 'unrecognized
  arguments' handling still rejects the invocation loudly (exit code 2),
  just with a generic message instead of the friendly #2592 redirect. I
  could not produce a case where the guard's absence makes a malformed
  --role invocation look like success (silent acceptance)... No leftover
  repo caller still invokes spawn.py with literal --role either." NO
  FINDING. Resolution: none needed — the two edge cases that bypass the
  custom pre-parse guard still hit argparse's own hard rejection, so
  "old flag is rejected" holds for those inputs too, just with a less
  specific message. Full hunt record (written this session, lands in
  this same commit as this record — not yet committed at hook-check
  time): docs/issue-2592/reports/api-design-versioning-evolution+technical-writing-structure-comprehension-e3fac09d/2026-08-27-hunt-spawn-role-to-session-flag-retirement.md
- derived: `grep -rn -- "--role" on-the-record/` (3 hits, all fixed) and
  a repo-wide `--role` grep filtered to spawn.py-referencing
  code/docstrings — files outside this diff that reference a
  *different*, unrelated `--role` flag were checked and left alone:
  `gates/landing_obligation.py`, `gates/reexecution_gate.py`,
  `gates/spawn_on_pr.py` (each owns its own separate `--role` argparse
  definition, unrelated to spawn.py's), `bench/run.py` (its own `--role`
  for benchmark target selection), and `README.md`/`README.ko.md`'s
  mermaid diagram (`spawn.py --issue N --role R` describes the retired
  role-positional *spawn* form from #2572, a different flag/meaning than
  the session-selector `--role` this issue renames — already stale
  independent of this change). Resolution: no action needed, out of
  scope.

## Next steps

None — landed in this commit; PR carries the same-commit constraint and
this record.
