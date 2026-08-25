---
status: proposed
subject: issue-2241
stage: 6
files:
  - spawn.py
  - roles/
  - roles/specs/
  - gates/quality_bar.py
  - gates/need_detector.py
  - gates/roles_due.py
  - gates/role_spec_shape.py
  - skills.py
  - consult.py
  - pipeline.py
  - board.py
  - tokenmaxxxer-core:core/hooks/board-gate.sh
  - docs/handbooks/architecture-methodology.md
---

# Stage 6 (last) — delete roles/*.json, roles/specs/, ROLES, per-role quality_bar

## Request

Delete the 43-name `ROLES` tuple (`spawn.py:557-569`), every
`roles/*.json` and `roles/specs/*.spec.json` file, and every consumer
branch that reads them, once stages 0-5 confirm nothing depends on role
identity anymore. State what a fresh install (never used roles) looks
like afterward, per this issue's acceptance criterion.

## Constraints

- Requires stages 0-5 all landed and stable — this is the terminal
  stage; nothing else in the program depends on it.
- Every consumer of `roles/specs/*.spec.json` beyond `quality_bar` that
  this survey found (`gates/need_detector.py`, `gates/roles_due.py`,
  `gates/role_spec_shape.py`) must be migrated or deleted in the same
  stage — deleting the directory out from under a live consumer is a
  correctness bug, not an acceptable partial landing.
- Frozen decision `single-skill-axis`: this stage is the one that makes
  that decision fully true in code, not merely in spec text.
- The dual-scheme branch/record reader stage 4 introduced may be
  retired in this same stage only once no old-scheme branch remains
  open (a live `gh pr list` / board check at build time, not assumed).

## Rationale

Chosen: one final deletion stage, executed only after every consumer
identified in the survey is confirmed migrated. Rejected alternative:
delete incrementally, one file per consumer, spread across the earlier
stages as each consumer stops needing it. Rejected because
`roles/specs/*.spec.json` has (per this survey) at least four distinct
consumers with different migration timelines in this plan
(`need_detector`/`roles_due`/`role_spec_shape` don't have a natural
per-earlier-stage migration point the way `quality_bar` does) — a
piecemeal deletion risks leaving one consumer reading a
half-deleted directory mid-program, which is a worse failure mode than
one clearly-scoped final stage. This also matches the issue's own
"each independently landable" framing better than interleaved partial
deletes would.

## What will be done

- `spawn.py`: delete the `ROLES` tuple; `board.py`'s discovery walk
  (already skill/lease-keyed since stage 4) needs no `ROLES` iteration
  to find records — confirm this via the test below rather than assume
  it.
- Delete `roles/*.json` and `roles/specs/*.spec.json` (44 + 43 files).
- `gates/quality_bar.py`, `gates/need_detector.py`, `gates/roles_due.py`,
  `gates/role_spec_shape.py`: each migrated to read whatever
  replacement source now carries their needed data (e.g. skill
  metadata already resolvable via `skills.py`) or deleted outright if
  the survey confirms (at this stage's build time) nothing still calls
  them.
- `skills.py`: delete `_ROLE_SKILLS`; `consult.py`'s
  `roles/<role>.json` existence-check call sites are deleted (stage
  2's regression test is updated to assert the check simply doesn't
  exist rather than asserting its behavior).
- `tokenmaxxxer-core:core/hooks/board-gate.sh`: delete `EXTRA_SUBTREE`'s
  role-keyed dict (superseded by stage 3's author-identity R5, which
  never needed role-name lookups to begin with once landed) — a
  separate PR against that repo, same cross-repo caveat as stage 3.
- `docs/handbooks/architecture-methodology.md` and any other handbook
  text still naming `roles/<role>.json` write-scope conventions is
  updated to describe the skill-based equivalent.

## Out of scope

- Any change to record content already written under the old scheme —
  historical records keep their `role:` field forever; this stage
  deletes the *definitions* that produced new ones, not the evidence
  trail of what already happened.
- Re-litigating which two record-kinds `merge_gate` requires (stage
  5's scope, already landed).

## How you'll know it worked

- `grep -rn "ROLES" spawn.py` and `ls roles/ roles/specs/` both show
  nothing (deletion complete).
- Full test suite passes with no reference to a deleted `roles/*.json`
  path (a broken import or missing-file test failure would surface
  immediately).
- **Empty-state check**: a fresh clone of the repo at this stage's
  commit, with no `docs/issue-<n>/reports/<old-role>.md` history to
  read, can spawn a session, have it write a board record, and have
  `merge_gate.required_verification_missing()` evaluate that record —
  all without any code path touching a role name. This is the concrete
  form of the acceptance criterion's "what a fresh install looks like
  with no legacy role names anywhere": no `ROLES` constant, no
  `roles/` directory, every session mounts skills directly, branch
  names carry `<skill>-<lease-disambiguator>`, every record frontmatter
  carries `author:` and `kind:` with no `role:` key, and
  `required_verification_missing()` reads record-kind presence only.
- Every consumer this survey named for `roles/specs/*.spec.json`
  (`need_detector`, `roles_due`, `role_spec_shape`, `quality_bar`) has
  either a passing migrated test or is confirmed absent from the
  codebase — not silently unaccounted for.

## Rollback

Restore the deleted files from the pre-stage-6 commit; because stages
0-5 never made anything depend on `roles/*.json` being *absent* (only
on the new concepts being *present*), a rollback of this stage alone
returns the repo to a state where both old and new mechanisms coexist,
identical to the state right after stage 5 landed.

## Accumulation

This stage is the direct answer to the "if this repeated N more times"
question for shape 5 (`roles/*.json`-style repeated one-line files):
today there are 43 such files (44 counting `roles/architecture.json`
plus its own spec) as the accumulation instance itself; this stage
deletes the entire accumulated set in one commit rather than adding to
it or trimming it file-by-file, which is why it is sequenced as one
final stage instead of N incremental partial deletions (see Rationale).
