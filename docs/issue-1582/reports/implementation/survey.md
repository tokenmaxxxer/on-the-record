# Survey: issue-1582 tier-1 role-patrol pilot

## Write set (projected, none exist yet — plain-text, not backticked, so
record-lint's path-reach check does not treat them as broken references)

- gates/patrol_queue.py — new module: fingerprinting, dedup/absence-close,
  lane logic, budgets, verifiability gate, dismissal memory.
- on-the-record/hooks/test_patrol_queue.py — unit tests.
- gates/patrol_trigger.py — post-merge trigger entry point.
- on-the-record/hooks/test_patrol_trigger.py — #1360-class regression
  test: patrol-produced commits/artifacts must not re-trigger patrol.
- docs/issue-1582/reports/patrol-measurement-2026-08-15.md — the
  measurement record (wall-clock, per-scanner enqueue count,
  verifiability-drop count), written from a live run in phase 2.
- .on-the-record/findings/queue.jsonl — runtime artifact produced in the
  *target* repo when the module runs, not part of this repo's write set.

## What exists already

canonical: `gates/record_lint.py` (lines 501-511, `find_records`) read
directly in this session
Confirms a whole-repo scan mode with a stable, reusable interface —
directly usable as one tier-1 scanner per issue design req 8 ("reuse
existing gate scripts in scan mode ... record_lint whole-repo mode").

canonical: `ls gates/` output read directly in this session (no
proposal_shape.py / proposal_frontmatter.py file present); `gates/role_spec_shape.py`
read directly, functions `check` / `check_playbook_refs` / `check_role_judgment_axes`
present
The issue's "proposal frontmatter validity" scanner (4 true positives,
consumer repo) has no single drop-in equivalent module in *this* repo —
the closest is `gates/role_spec_shape.py` (`check`), and the
`files:`/`status:` proposal-frontmatter shape check that exists lives in
a plugin-side shell hook (proposal-shape-gate.sh).
canonical: `find . -iname "proposal-shape-gate.sh"` run directly in this
session, no output — not present under this repo's own tree, not a
standalone Python scanner callable in scan mode. The issue's
true-positive claim is about the separate consumer repo
(`/home/jwjung/tokenmaxxxer`), so this repo's pilot does not need to
reproduce that exact scanner — req 8 only requires reusing *some*
existing gate script in scan mode, which `gates/record_lint.py` already
satisfies on its own.

canonical: `gates/spawn_on_pr.py` (lines 1-22) read directly in this
session
Carries this repo's only prior #1360-class regression fix: `SPAWN_CAP`,
open-issue-only scope, "cap it, never silently backfill, print the drop
count" (module docstring + `SPAWN_CAP` comment). Patrol's
budget/drop-not-queue requirement (design req 5) should mirror this
shape rather than invent a new one.

canonical: `ls .git/hooks/` output read directly in this session (only
`.sample` stub files present, no live `post-merge` hook); `docs/issue-392/proposals/2026-08-07-post-merge-reconciliation.md`
(lines 1-60) read directly in this session
No git-native `post-merge` hook is used anywhere in this repo. The
repo's own precedent for "runs after a merge" is the #392 proposal's
chosen approach: chain onto the merge command the orchestrator already
always invokes, rather than a standalone step or a `.git/hooks/`
file — hooks don't propagate via clone/fork and are invisible to the
harness (`docs/issue-392/proposals/2026-08-07-post-merge-reconciliation.md`,
"Alternative considered and rejected" section). Patrol's trigger follows
the same shape.

canonical: `find . -iname "*patrol*"` and `find . -iname "*.on-the-record*" -maxdepth 2`
output, both empty, read directly in this session
No existing `.on-the-record/findings/` directory or fingerprint queue
format exists anywhere in this repo or its docs — this is new
machinery, consistent with the issue calling it a pilot.

canonical: `docs/reports/consult-log.md` tail read directly in this
session; issue #1582 body itself cites the same two consult timestamps
(2026-08-15T05:30:34Z risk-management, 2026-08-15T05:30:39Z
technical-feasibility)
The pilot's shape (tier-1 only, no LLM, no auto-promotion) is the
already-consulted-and-approved direction per the issue text, not an
independent design choice made in this survey.

## Unknowns / gaps this proposal must resolve

- Fingerprint hash inputs: issue specifies
  sha256(scanner_id + normalized_path + context-region hash of
  surrounding lines). No existing normalizer for a "context-region
  hash" exists in this repo (checked via the same `ls gates/` sweep
  above) — must be defined fresh, with a line-shift-stability test.
- Exact call site for the post-merge trigger (which file inside
  on-the-record/commands/run.md's merge step to chain onto) is deferred
  to phase 2. canonical: `docs/issue-392/proposals/2026-08-07-post-merge-reconciliation.md`
  read directly in this session — this establishes the *pattern* (chain
  onto the merge command) but this survey does not have canonical
  evidence #392 itself landed on main, so the phase-2 build reads the
  current state of the merge command at that time rather than assuming
  #392's specific file list is live.
