# Current-state survey — issue #2211 conformance-review

## Target artifact and spec

Target: commit `94fbd4df`, the head of `issue-2211/implementation`
(PR #2228, open).
canonical: `git show 94fbd4df --stat` (read directly, this session) —
touches `pipeline.py`, `spawn.py`, `tests/test_spawn_pipeline.py`,
`tests/test_directive_diet_2135.py`, and adds a record at
`git show 94fbd4df:docs/issue-2211/reports/implementation.md`.

Spec: issue #2211 body, `## Fix` and `## Acceptance` sections.
canonical: `gh issue view 2211` (read directly, this session)

Board condition per role spec: an implementation commit landed on the
role's branch and no conformance-review record exists yet for that sha.
canonical: `roles/specs/conformance-review.spec.json` (read directly) —
condition holds: `94fbd4df` is the current tip of `issue-2211/implementation`
per the `git show --stat` citation above, and this session's own working
tree carries only the issue-2135 pre-seeded skeleton at
docs/issue-2211/reports/conformance-review.md (unfilled placeholder
sections, no requirement/verdict content) — not a record for `94fbd4df`.

## Scout skip record

Skip condition: the spec leaves no design decision open in the
scout-directive's product/exemplar sense.
canonical: `gh issue view 2211` (read directly) — `## Fix`/`## Acceptance`
is a closed checklist against one already-open PR touching four files;
there is no product/exemplar field to compare against external
best-in-class systems. The one open call this role does make — sample
vs. full enumeration of the touched surface — is resolved under
"Sampling scope" below via the sampling-derivation skill's own
procedure, not web scouting.

## Sampling scope

Population: the four files named in the `git show --stat` citation
above, plus the requirement list below. Chosen scope: full enumeration,
zero sampling — every touched file and every extracted requirement gets
inspected in phase 2. Per sampling-derivation rule 5 (exempt the
highest-impact tier from sampling), this population is treated as one
highest-impact tier in its entirety: an env-var injection wired into
every future role spawn is infrastructure-wide blast radius, not a
lower-tier partial-check candidate.

## Board / approval state

canonical: `gh pr list --head issue-2211/conformance-review --state all`
(executed this session) — empty result, no PR yet for this role's
branch.
canonical: `gh issue view 2211 --json comments` (executed this session)
— one existing comment, an automated `[watch]` PR-opened notice for
PR #2228; no `APPROVE issue-2211/conformance-review` string from either
approvers.md account (`jiwonjung94`, `jjongkwann`).
canonical: this session's own PreToolUse denial when a Bash read named
a path under docs/issue-2211/reports/implementation/ (a different
role's phase-2-only material), verbatim: "neither the PR for
issue-2211/conformance-review nor issue #2211 carries an approval from
a listed human approver (jiwonjung94, jjongkwann)..." — live evidence
that phase 2 is not yet open for this role.

## Requirement list (from issue #2211 `## Fix`/`## Acceptance`, split
per requirement-extraction rule 1 — the bundled "plugin-root, core-root,
skill-registry, and workspace paths" clause split into one line per
path — and dimension-tagged per rule 6)

canonical: `gh issue view 2211` (read directly — `## Fix`/`## Acceptance`
is the source for every item below)

1. (functional) The spawned session's environment unconditionally
   carries a workspace-root path variable.
2. (functional) The spawned session's environment unconditionally
   carries a plugin-root path variable (the on-the-record checkout
   root).
3. (functional/regression) The spawned session's environment carries a
   core-root path variable, pre-existing per issue #182: this
   requirement is that the change leaves it in place, not that it is
   new.
4. (functional, conditional on a skill-repository being resolved for
   the spawn) The environment carries a skill-registry path variable
   when that resolution succeeds.
5. (edge-case) When no skill-repository is resolved, the skill-registry
   variable stays absent from the env dict rather than present as an
   empty string.
6. (verification-method, process) Requirement 1-4's check runs as a
   live spawn with an in-session env readback, not only a unit-test
   assertion against a function's returned dict.
7. (functional) A re-measured engineering-class session's log carries
   zero `find /` or `find /home` invocations for paths now exported.
8. (verification-method, process) Requirement 7's check runs by
   producing an actual new session log and grepping it, not by
   inference from the code alone.
9. (unverifiable-as-written, requirement-extraction rule 2) The phrase
   "engineering-class session" names no defined term anywhere in this
   repository or the mounted core plugin.
   canonical: `git grep -rni "engineering-class"` against this repo
   (executed this session, zero hits) and an equivalent grep against
   the mounted core plugin's own tree (executed this session, zero
   hits) — the issue states no acceptance threshold for which task or
   role qualifies. Phase 2 can only judge whether the implementer's own
   chosen stand-in is a reasonable one, and must say so explicitly.
10. (scope-boundary/regression) Spawns unrelated to the four new/changed
    keys carry an env dict with no other key added, changed, or removed.
11. (process) The record carries executed acceptance evidence — real
    command and output — rather than narrated claims, per issue #2137's
    verify-at-landing convention already binding via the core
    session-protocol this session was itself spawned under.
12. (scope-boundary, negative requirement) No new discovery mechanism or
    cache is introduced; the fix is limited to exporting values the
    spawner already resolves.
13. (functional) A short directive note/section is added telling
    sessions the new variables exist, paired with the export.
14. (scope-boundary) The fix reuses an already-resolved value rather
    than adding a second resolution call for the same lookup.

## Verification method per requirement (per
verification-method-selection skill; phase 2 executes these, not phase
1)

- R1-R4: Inspection of the env-dict assignment lines in `pipeline.py`
  against `94fbd4df`, plus Test — reuse and independently re-run the
  implementation's own new unit tests rather than trust only a pasted
  summary (verification-method-selection rule 4; finding-record norm:
  verdict from the artifact, not the builder's account).
- R5: Test — reuse and independently re-run the empty-state unit test.
- R6: Demonstration — the requirement names the check method itself (a
  live spawn), so a unit test cannot stand in; phase 2 independently
  re-runs a live `claude -p` spawn and env readback rather than accept
  a prior transcript at face value.
- R7-R8: Demonstration — phase 2 independently re-runs a live spawn
  mirroring the implementer's own "engineering-class" stand-in and greps
  its own new log.
- R9: Analysis-only — no invented threshold; judge the implementer's
  stand-in for reasonableness against the issue's own text.
- R10: Inspection of the pre-change vs. post-change env-dict
  construction in `pipeline.py`, plus Test — independently re-run the
  pre-existing tests this diff leaves untouched.
- R11: Inspection of the record's frontmatter and its evidence section.
- R12: Inspection of the touched-file list for a new discovery/caching
  module.
- R13: Inspection of `directive_section_files()`'s always-on set, plus
  Test — reuse the new directive-file-shape unit test.
- R14: Inspection of the call site that resolves the skill-registry
  root, checking it is called once and threaded through rather than
  re-resolved a second time.

## Facts gathered this session, not yet verdicted

- `ROOT = Path(__file__).resolve().parent` at spawn.py:43 is spawn.py's
  own containing directory — the same directory this session's working
  tree root already resolves to.
  canonical: `git show 94fbd4df:spawn.py` line 43 (read directly, this
  session)
- `_workspace_base()` at lifecycle.py:561 resolves `MUSTER_WORK_DIR` or
  else `Path.home() / ".tokenmaxxxer" / "work"` — a prefix of this
  session's own workspace path.
  canonical: `git show 94fbd4df:lifecycle.py` lines 561-566 (read
  directly, this session)
- A repo-wide grep for the two new variable names outside the new test
  files returns zero prior occurrences — new names, not a rename or a
  reused name with different prior meaning.
  canonical: `git grep -rn "MUSTER_WORKSPACE_ROOT\|MUSTER_SKILL_REGISTRY_ROOT" -- '*.py' '*.md'`
  (executed this session, excluding the new test files)
- `ON_THE_RECORD` as a name has one prior convention elsewhere in this
  repo, `ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..`, in three files under
  `on-the-record/commands/`.
  canonical: `git grep -n "ON_THE_RECORD" -- on-the-record/commands/run.md on-the-record/commands/consult.md on-the-record/commands/report-upstream.md`
  (executed this session) — same name, same directory-root meaning, no
  collision with a differently-scoped prior use.
- The pre-change `CLAUDE_PLUGIN_ROOT_CORE` injection block in
  `pipeline.py` sits immediately before the diff's insertion point, and
  the diff hunk itself (already read this session) inserts three new
  lines after that block without altering any of its existing lines.
  canonical: `git diff 94fbd4df^..94fbd4df -- pipeline.py` (read
  directly, this session)
- This session's own ambient environment carries `CLAUDE_PLUGIN_ROOT_CORE`
  and an older `MUSTER_SKILL_REPO`/`MUSTER_SKILLS` pair, but no
  `ON_THE_RECORD` or `MUSTER_WORKSPACE_ROOT` key.
  canonical: `env | grep -iE 'MUSTER|ON_THE_RECORD|CLAUDE_PLUGIN'`
  (executed this session) — expected, not a defect: this
  conformance-review session was spawned off `main`, which does not
  carry `94fbd4df` (still on the open `issue-2211/implementation`
  branch); R1/R2/R4's live-spawn check needs a spawn built from that
  branch's own code, as the implementer's own record describes doing.
- The session log the issue body's own `provenance:` line names is no
  longer present in this session's workspace-root directory.
  canonical: `find ~/.tokenmaxxxer -maxdepth 1 -iname "on-the-record-issue-2201-implementation.session.2026*"`
  (executed this session, zero results — log rotation) — this role
  cannot independently re-derive the original 126-second measurement
  from that specific log; phase 2 will rely on the issue's own citation
  for that historical number and instead independently re-run R7/R8's
  *re-measurement* live.
- PR #2228's body carries a `Closes #2211` trailer, not a plain
  reference.
  canonical: `gh pr view 2228 --json state,body -q '.state,.body'`
  (executed this session) — result: `OPEN`, body ends with `Closes
  #2211`. This differs from the issue-2156 precedent (a plain-reference
  gap); no trailer gap exists here to flag as an Open Finding.

## Notable surface for phase 2 (candidate observations, not verdicted
here)

- The implementation record names two items outside R1-R14: a companion
  `tokenmaxxxer-core` change for a `directive.sh` index-line entry, and
  a same-branch-vs-`main`-worktree test comparison it says shows the
  same set of pre-existing failures on both sides.
  canonical: `git show 94fbd4df:docs/issue-2211/reports/implementation.md`
  (read directly, this session), its own "Open findings" section — phase
  2 should independently re-run that comparison (a stated, reproducible
  command) rather than accept it unchecked, and record the `directive.sh`
  item as a resolution-path-bearing observation outside the R1-R14 set,
  mirroring the issue-2156 precedent for out-of-band process gaps.
  canonical: `git show 96f9e98d:docs/issue-2156/reports/conformance-review/survey.md`
  (read directly, this session), its "Notable surface for phase 2"
  section.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split the bundled acceptance clause into R1-R4, flag R9's undefined term under rule 2, and dimension-tag R1-R14 above.
skill-verdict: conformance-review-sampling-derivation — applied: invoked; used to derive the full-enumeration, single-tier scope under "Sampling scope" above per rule 5.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used to assign Inspection/Test/Demonstration/Analysis per requirement above, reusing existing tests per rule 4 instead of deriving parallel manual checks.
other mounted skills: not triggered — traceability-and-evidence, verdict-assignment, finding-record, and severity-classification are phase-2 concerns; this session's writes stop at the phase-1 survey/proposal boundary, enforced live by approval-gate.sh (see "Board / approval state" above).
