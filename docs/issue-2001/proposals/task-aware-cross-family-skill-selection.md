---
status: proposed
files:
  - spawn.py
  - test/test_spawn_cross_family_skill_selection.py
  - docs/issue-2001/reports/implementation/replay-table.md
---

## Request

Task-aware skill selection at spawn, step 1 (add-only, per the consult
recorded inline in the issue body: 2026-08-22, requirements-engineering
— add-only first, K=1-2, family set intact, replay-before-ship;
noise/drop deferred). Keep each role's fixed `_ROLE_SKILLS` family set as
the safety floor and ADD, on top of it, top-K (K=2) cross-family skills
whose `SKILL.md` "Use when ..." trigger sentence lexically matches the
spawn task/issue text — deterministic keyword scoring, no network, no
new dependency. When no cross-family skill clears the threshold, the
directive and mount list must be byte-identical to today's output.
Before shipping, replay the scorer against today's 12+ real session logs
and record a would-have-added table with a one-line plausibility
judgment per session. Explicit non-goal: dropping family skills — a
separate later iteration.

## Constraints

- Confined to `spawn.py`, `scripts/`, `test/`/`tests/`, `docs/` per the
  issue's stated scope.
- Family set (`_ROLE_SKILLS`, spawn.py:5068-5112) is never reduced —
  add-only, per the consult and the issue's explicit non-goal.
- No network calls, no new third-party dependency — deterministic
  keyword scoring only.
- No-match path must be byte-identical to today: when zero cross-family
  skills clear the threshold, neither the directive text nor the
  `--plugin-dir` mount list may differ by even one byte from a build
  with this feature absent (spawn.py:8002-8015 directive block,
  spawn.py:8047-8048 mount-list assembly).
- K is capped at 2 (`up to K=2` per acceptance).
- Acceptance test must run live, serial, `-o addopts=''` — no reliance
  on a mocked scorer that never touches real `SKILL.md` frontmatter
  parsing.

## Rationale

Per `docs/issue-2001/reports/implementation/survey.md`, `_skill_trigger_line()`
(spawn.py:7845-7871) already extracts each skill's "Use ..." sentence
from `SKILL.md` frontmatter and this exact text is already rendered
in-line for family skills at spawn.py:8007-8010 — so the new cross-family
line can reuse the identical extraction and rendering shape instead of
inventing a second one. No lexical scorer exists anywhere in the repo
(survey, "No existing lexical scorer" section) — the matcher itself is
net-new. Two shapes were considered for it:

1. **Full-text TF-IDF / embedding similarity** between task text and
   each candidate skill's trigger sentence. Rejected: pulls in either a
   new dependency (scikit-learn, embeddings) or a from-scratch TF-IDF
   implementation, both disproportionate to a same-repo, deterministic,
   no-network requirement; embeddings would also violate the no-network
   constraint outright if backed by an API, and a local embedding model
   is a new dependency either way. The issue explicitly asks for
   "deterministic keyword scoring," not similarity search.
2. **Deterministic keyword-overlap scoring**: tokenize the task text and
   each candidate skill's trigger sentence (lowercase, split on
   non-alphanumeric, drop a small stopword list), score by count of
   distinct shared tokens (ties broken by skill name for determinism),
   keep skills whose score clears a fixed threshold, take the top K=2.
   Chosen: zero new dependencies, deterministic (same input always
   produces the same output — required for the byte-identical no-match
   assertion to be meaningful and stable across runs), and directly
   testable with the existing `DirectiveAssemblyBase` fixture pattern
   (survey, "Test fixture pattern to extend" section) without mocking
   anything scorer-internal.

For candidate discovery, `resolved_skill_dirs()`'s use of
`repo_root.iterdir()` (spawn.py:4905) already enumerates every skill
directory in the skill-repository checkout — reused as the candidate
pool (all names not already in the role's own `_ROLE_SKILLS[role]`
list), rather than adding a second directory-listing path.

## What will be done

- Add `_tokenize(text)` and `_cross_family_skill_matches(task_text,
  role, repo_root, k=2)` to spawn.py (near `_skill_trigger_line`,
  spawn.py:7871+):
  - Tokenize `task_text` and, for each candidate skill directory in
    `repo_root.iterdir()` whose name is not in `_ROLE_SKILLS.get(role,
    [])`, tokenize its `_skill_trigger_line()` result (skip candidates
    with no trigger line — no sentence to match against).
  - Score by count of distinct shared tokens (case-insensitive,
    non-alphanumeric split, small fixed stopword list: "a", "the",
    "use", "when", "or", "and", "is", "an" — trimmed so generic words
    like "Use when" itself never drive a match).
  - Keep scores >= a fixed minimum-overlap threshold (2 distinct shared
    content tokens, chosen conservatively so a single generic shared
    word like "code" cannot alone trigger a match); sort by (score
    desc, name asc) for determinism; take top `k`.
  - Return `[]` when nothing clears the threshold — this is the
    byte-identical no-match path.
- Wire the result into `_spawn_one()` at spawn.py:8002-8015: when
  `role_source["source"] == "skill-repo"` and the role has task text
  (the `task` param `_spawn_one()` already receives), compute cross-
  family matches once, append their dirs to the list rendered in the
  existing skill-listing paragraph (same `name — trigger-line` shape,
  same fallback-to-bare-name empty-state as today) and to
  `all_skill_dirs` at spawn.py:8047-8048 so they are actually mounted
  via `--plugin-dir`, not just named in the directive.
- Add one short clause to the existing family-skill paragraph noting
  which of the listed skills were cross-family additions (so the
  directive stays legible about why an unfamiliar skill name appears),
  worded to add nothing when the added list is empty (preserving byte-
  identity).
- Tests in `test/test_spawn_cross_family_skill_selection.py`, extending
  `DirectiveAssemblyBase` from `tests/test_spawn_directive_assembly.py`
  per the survey's fixture-extension plan:
  - Unit tests for `_tokenize` and `_cross_family_skill_matches`
    (matching case, sub-threshold case, tie-breaking, K=2 cap with 3+
    candidates clearing threshold).
  - Live acceptance test (serial, `-o addopts=''`, matching the
    acceptance line verbatim): build a temp skill-repository root with
    the role's family skills plus a cross-family skill whose `SKILL.md`
    "Use when ..." sentence lexically matches a fixture task string;
    run `spawn._spawn_one()`; assert the mount list gains exactly that
    skill (and no more when only one clears K=2) and the directive
    names it. Second case: same setup, non-matching fixture task; assert
    the delivered directive and `all_skill_dirs` mount list are byte-
    identical to a baseline run built from `role_source["skill_dirs"]`
    alone (no cross-family logic invoked).
- Before landing: write a standalone replay script (or a `--replay-only`
  path added to the same test file, whichever keeps `spawn.py` free of
  a permanent CLI subcommand for a one-time analysis) that, for each of
  today's 12+ real spawned sessions (roster/ledger entries with a
  distinct issue+role, per the survey's "Replay-before-ship" section),
  refetches the issue text via `gh issue view <n>` (mirroring
  spawn.py:7961-7963's own fetch) and runs
  `_cross_family_skill_matches()` against it. Record the results as
  `docs/issue-2001/reports/implementation/replay-table.md`: one row per
  session — issue, role, would-have-added skill(s) (or none), and a
  one-line human plausibility judgment (does the added skill actually
  look relevant to that task, yes/no/maybe) — the consult's explicit
  precondition ("no hard false-positive data yet") for shipping.

## Out of scope

- Dropping or reordering any role's existing `_ROLE_SKILLS` family
  entries — add-only per the issue's explicit non-goal; false-negative
  safeguards for a future drop iteration are not designed here.
- `--skills` (operator-supplied CSV mounting, spawn.py:7889-7901) is
  untouched — it is additive with family mounts already and orthogonal
  to this task-aware cross-family addition.
- Any similarity/embedding-based scoring, or a scorer configurable by
  role — the issue asks for one deterministic keyword scorer, not a
  pluggable ranking framework.
- Persisting task text into roster entries for future replay
  convenience — this proposal's one-time replay reads issue text live
  via `gh issue view` instead, since no stored task-text field exists
  today (survey) and adding one is a separate concern from selection
  logic.
- Tuning the overlap threshold or K beyond what the replay table
  supports; if the replay table's plausibility judgments suggest the
  fixed threshold is miscalibrated, that is phase-2/follow-up work, not
  decided speculatively here.

## Accumulation

The replay script calls `gh issue view <n>` once per today's 12+ session
rows — a fixed, one-time batch for this ship-gate replay, not a
per-spawn accumulating cost: it does not run again after this proposal
lands, and the live `_spawn_one()` path it mirrors already makes exactly
one `gh issue view` call per spawn today (spawn.py:7961-7963), unchanged
by this proposal. If a future iteration needs a second full replay
(e.g. after a threshold retune), it reuses this same one-off script
rather than adding a new call site — no inline `gh`/subprocess call
accumulates inside `spawn.py` itself, and the per-spawn hot path gains
zero additional `gh` calls (cross-family scoring runs entirely off the
issue text `_spawn_one()` already fetched).

## How you'll know it worked

- `pytest test/test_spawn_cross_family_skill_selection.py -o addopts=''`
  passes serially, live (no mocked scorer), asserting both acceptance
  cases verbatim: matching-task mount-list gain (exactly the matched
  skill, up to K=2) plus directive mention, and non-matching-task
  byte-identical directive/mount list versus today.
- Existing `tests/test_spawn_directive_assembly.py` and
  `test/test_spawn_skills_mount.py` /
  `test/test_spawn_role_skill_resolution.py` continue to pass unchanged
  — the empty-cross-family-match path must not perturb any existing
  assertion.
- `docs/issue-2001/reports/implementation/replay-table.md` exists,
  covers 12+ real session logs, and each row carries a would-have-added
  entry plus a one-line plausibility judgment.
