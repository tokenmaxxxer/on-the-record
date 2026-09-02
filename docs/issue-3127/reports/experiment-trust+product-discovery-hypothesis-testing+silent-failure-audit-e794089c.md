---
issue: 3127
role: experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c
author: experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c
skills: experiment-trust (skill-repository(c05de12)), product-discovery-hypothesis-testing (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: terminal
code_under_review: scripts/issue-3127/run_consumer_pair.py
type: fix
breaking: false
verdict: not measured -- manipulation check (H1) could not be established for either registered pair; two real skills-on sessions genuinely dispatched and landed phase-1 PRs (sandbox #23, #24), but both skills-off arms failed to dispatch at all on a real, reproducible cross-family skill-source tier conflict (issue #2055's own fail-closed safety check), distinct from and additional to a policy-skill-stub defect this session found and fixed
upstream:
  - path: docs/issue-3127/decisions/pre-registration.md
    sha: same-commit
  - path: scripts/issue-3127/run_consumer_pair.py
    sha: same-commit
---

# issue-3127 — experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-e794089c record

## What was done

canonical: this session's own live command transcript below — each numbered
step names the exact command it derives from.

Ran the real consumer-path measurement against the pre-provisioned sandbox
`JiwonJung94/study-companion`, using the orchestrator-supplied issue map
(`01-study-groups`: skills-on=19/skills-off=20; `02-onboarding-experiment`:
skills-on=21/skills-off=22).

1. derived: `python3 scripts/issue-3127/run_consumer_pair.py --dry-run --repo /home/jwjung/study-companion --issue-map "01-study-groups:19:20,02-onboarding-experiment:21:22"` — exit 0, plan text matched `docs/issue-3127/decisions/pre-registration.md`'s arms/held-constant factors/H1 gate/blind scorer/`wall_clock_to_pr_open_s` naming.
   derived: `for i in 19 20 21 22; do python3 spawn.py lint --issue $i -C /home/jwjung/study-companion; done` — each printed `이슈 #N lint: 위반 없음`.

2. First real `--execute --i-understand-this-spawns-real-sessions` attempt on
   pair `01-study-groups` found the skills-off arm's dispatch failing:
   derived: background task `bne9bitb2` output —
   `"dispatch_stderr": "...--skills: 모르는 스킬 work-in-english -- 쓸 수 있는 이름: product-discovery-hypothesis-preregistration\n"`.
   Root cause read from source: `skills.py:440` (`_STATIC_POLICY_SKILLS =
   {'work-in-english'}`) and `skills.py:445-452`
   (`resolve_static_policy_source()` resolves it unconditionally from
   whatever skill-repo root is in effect); `scripts/issue-3127/
   run_consumer_pair.py`'s pre-existing `build_stub_skill_repo()` only ever
   wrote the one named target skill. Fixed by extending
   `build_stub_skill_repo()` to also stub every name in
   `skills._STATIC_POLICY_SKILLS`; added
   `BuildStubSkillRepoTest::test_also_stubs_static_policy_skills`.
   derived: `python3 -m pytest tests/test_issue_3127_run_consumer_pair.py tests/test_issue_3127_h1_and_scoring.py -q` — result: `25 passed in 0.89s`.
   Committed as a checkpoint (commit `1deb6198`) before further real dispatch.

3. Re-attempted the skills-off arm for issue 20 directly via `execute_arm()`
   (not through `main()`, to avoid re-dispatching the already-real
   skills-on arm on issue 19 a second time):
   derived: background task `b1uw8n1gz` output —
   `"dispatch_stderr": "...cross-family 후보 스킬 product-discovery-hypothesis-preregistration 가 둘 이상의 소스에서 겹친다 -- skill-repo(/tmp/issue-3127-skills-off-sy3hif8s/...), local-user(/home/jwjung/.claude/skills/product-discovery-hypothesis-preregistration) (이슈 #2055: ...)\n"`.
   Root cause read from source: `pipeline.py:1423-1490`
   (`_cross_family_candidate_corpus()`, called from
   `directive_assembly.py:756` on every dispatch, independent of the
   `--skills` argument's own source qualifier) fails closed
   (`sys.exit`) whenever a skill name resolves to *different* content
   across more than one tier — confirmed via
   derived: `cat ~/.claude/skills/product-discovery-hypothesis-preregistration/SKILL.md | head -20` — a full, real skill body (not this harness's frontmatter-only stub) genuinely present on this machine.
   Confirmed identically reproducing for pair `02-onboarding-experiment`'s
   skills-off arm:
   derived: background task `bipqng43a` output — same `cross-family 후보 스킬` `sys.exit` text for issue 22.

4. Ran pair `02-onboarding-experiment`'s skills-on arm (issue 21) for real,
   same reasoning as (3):
   derived: background task `b2bckbxrz` output —
   `"dispatch_returncode": 0, "wall_clock_to_pr_open_s": 364.089...`.

Net real outcome, canonical: `gh pr view 23 --repo JiwonJung94/study-companion`
and `gh pr view 24 --repo JiwonJung94/study-companion` (both state OPEN,
titles naming issues 19 and 21 respectively) plus
derived: `grep "issue-19-product-discovery\|21" runs/ledger.jsonl` (cost-entries:
issue 19 `cost_usd: 0.743878, turns: 23, duration_s: 274.8`; issue 21
`cost_usd: 0.8055754, turns: 29, duration_s: 278.3`) — both skills-on arms
genuinely dispatched, ran a full session, and opened real phase-1 proposal
PRs against the sandbox. Both skills-off arms (issues 20, 22) never
dispatched at all (same evidence as steps 2-3 above).

`docs/issue-3127/_assets/consumer-path-results.json` (acceptance check 2)
was hand-assembled (`/tmp/finalize_results.py`, not committed — a one-off
glue script, not a repo feature) from these real, independently-verified
artifacts rather than produced end-to-end by `main()`, because no pair
ever reached a state where both arms completed for `run_pair()`'s own
gating logic to run over. Every figure in that file traces to one of the
`derived:`/canonical citations above.

derived: `python3 scripts/issue-3127/verify_preregistration.py` — result: exit 1, `"both files were introduced in the same commit (fb0bb0d349cfe27837b03c7ed9e3bc470887c9c8) -- the pre-registration must be committed strictly before the results, not alongside them..."` — reproducing PR #3166's independently-found defect exactly (squash-merge `fb0bb0d3` collapsed the two-commit ancestry the check depends on). Per this session's own spawning instructions this gates landing, not execution, is out of scope (a separate session is redesigning the check), and does not block this PR.

## Why

The policy-skill-stub fix (step 2 above) is the minimal, targeted change
needed to let the skills-off arm's dispatch reach past an unrelated
resolution failure at all — without it, no skills-off arm could ever
start, for any reason, defeating the measurement outright. It was applied
and tested the same way the file's own prior repair rounds fix comparable
defects (frontmatter-only stub, same shape as the existing target-skill
stub) — see the `derived: pytest ...` citation in "What was done" step 2.

The cross-family tier-conflict (step 3) was deliberately **not** patched.
Weakening `pipeline.py`'s issue-#2055 fail-closed check to tolerate a
qualified source silently overriding a name that also exists elsewhere
would remove a real safety property shared by every session on this
machine, to serve one harness's manipulation design — the same class of
out-of-scope call PR #3166 made for `verify_preregistration.py`'s
squash-merge defect (canonical: `gh pr view 3166 --repo tokenmaxxxer/on-the-record`,
read this session). The one considered alternative — temporarily moving
`~/.claude/skills/product-discovery-hypothesis-preregistration` aside for
the width of one dispatch call — was rejected: it mutates global,
machine-shared state with no scoping to this harness, risking any other
concurrently-running session that reads the same path
(canonical: `ps aux | grep -iE "claude|spawn.py"`, run this session,
showed no live process using that specific skill at decision time, but
the machine runs many concurrent sessions per
`ls /home/jwjung/.tokenmaxxxer/work/`), purely to force an experimental
condition to succeed.

`experiment-trust` invoked this session (Skill tool). Step 1's scope gate
applies the pre-registration's own scope note (canonical:
`docs/issue-3127/decisions/pre-registration.md`'s "Scope note" section,
read this session) — this is an offline, pre-assigned n=2 paired
comparison, not an online controlled experiment with random assignment,
so the platform-validation and SRM chi-square steps do not apply; nothing
new to add there. The operative discipline this session was Twyman's-law
skepticism applied to the raw observation that the (aborted) skills-off
workspace and the completed skills-on workspace reported byte-identical
`directive_composition_bytes` — derived:
`python3 -c "import sys; sys.path.insert(0,'scripts/issue-3127'); import run_consumer_pair as rcp; from pathlib import Path; print(rcp.collect_directive_bytes(Path('/home/jwjung/.tokenmaxxxer/work/study-companion-issue-19-product-discovery-hypothesis-preregistration-f8df81f9')))"`
— result: `13026`, matching the aborted issue-20 workspace's own count
exactly. Taking that at face value could have been misread as an H1
zero-mount data point; tracing it forward instead
(derived: `grep -o '"skill":"[a-z-]*"' <issue-19 session log> | sort -u`
— result included `"skill":"product-discovery-hypothesis-preregistration"`
as a tool-call reference, i.e. the skill is delivered via the Skill
tool's on-demand invocation, not a pre-written per-skill directive file)
surfaced a construct-validity gap in H1's own operationalization instead,
recorded in the results JSON's `construct_validity_note_on_h1_metric`
rather than reported as a pass.

`silent-failure-audit` invoked this session (Skill tool), applied to the
harness code touched this session: `build_stub_skill_repo()`'s new
policy-skill loop introduces no new fallible operation (a `set` iteration
+ `Path.mkdir`/`write_text`, same shape as the pre-existing target-skill
stub it extends — canonical: the diff in commit `1deb6198`, read this
session before committing). `execute_arm()`'s pre-existing dispatch/watch
failure paths (not modified this session — canonical:
`scripts/issue-3127/run_consumer_pair.py:595-677`, read this session)
classify as Handled: `lint-failed`/`dispatch-failed`/`watch-timed-out`/
`watch-failed` each return an explicit status dict carrying the real
`stderr`/`returncode`, propagated to the caller and into the results
JSON verbatim — this session's own two real defect findings above came
directly from reading those propagated `dispatch_stderr` fields, which is
itself the evidence that they are not silently absorbed. No
Silently-Absorbed sites found in the code path exercised this session.

`product-discovery-hypothesis-testing` mounted, not invoked: its trigger
is moving a spec through product-cycle's `docs/proposals/` state machine
(scoping an idea, registering a metric/threshold in a proposal's
frontmatter, applying a registered rule to reach a go/kill/pivot call).
This session's pre-registration already exists at `docs/issue-3127/
decisions/pre-registration.md` under a different, already-registered
process (`product-discovery-hypothesis-preregistration` — the skill this
issue *measures*, not one of this session's own mounted skills), and no
`docs/proposals/` file was scoped, registered, or advanced this session —
not applicable.

## What did not work

- The very first `--execute` attempt (before the checkpoint commit) was
  killed 2 seconds after launch because it was started via detached
  `nohup ... & disown` instead of the Bash tool's tracked
  `run_in_background`, losing harness-level completion tracking.
  derived: `kill 794555; ps aux | grep -i run_consumer_pair | grep -v grep`
  — no output (no live process).
  derived: `gh pr list --repo JiwonJung94/study-companion --state all --limit 10`
  — no stray PR for issue 19 or issue 20 in that window. An inert
  `.spawn-claim` file for issue 19 under workspace hash `6f70d776`
  survived (canonical:
  `cat /home/jwjung/.tokenmaxxxer/work/study-companion-issue-19-product-discovery-hypothesis-preregistration-6f70d776.spawn-claim`
  — `{"pid": 794820, ...}`, and `ps -p 794820` returned nothing, confirming
  dead), never the workspace the real run used. All subsequent dispatches
  used the Bash tool's `run_in_background` + `TaskOutput(block=true)`
  instead.
- `execute_arm()`'s own `watch` step reported `watch-failed` /
  `"기록 없음 — 아직 스폰된 적이 없다"` for BOTH real skills-on sessions
  (issues 19, 21), even though both genuinely ran to completion and
  opened real PRs. derived: background task `bne9bitb2` output —
  `"watch_returncode": 1, "watch_stderr": "...기록 없음...\n"` alongside
  `"dispatch_returncode": 0` and `"wall_clock_to_pr_open_s": 340.36...`;
  cross-checked against canonical: `gh pr view 23 --repo JiwonJung94/study-companion`
  (state OPEN, real body) and the `runs/ledger.jsonl` cost-entry for
  issue 19 cited in "What was done". This looks like a distinct
  `spawn.py watch`/roster-lookup race (`events.py:_watch()`/
  `_lookup_roster_entry()`, read this session), separate from H1 and out
  of this session's scope to fix; recorded per-arm in the results JSON as
  `harness_watch_defect_note`, with the real outcome cross-checked and
  reported alongside the harness's own (incorrect) status rather than
  silently trusting either the harness or the workaround.

## Upstream basis

- `docs/issue-3127/decisions/pre-registration.md` (sha: same-commit;
  already landed on this branch pre-`fb0bb0d3`, read but not modified
  this session) — the metric, threshold, decision rule, and H1/H2/H3
  hypotheses this run was executed against.
- `scripts/issue-3127/run_consumer_pair.py` (sha: same-commit; modified
  this session, commit `1deb6198` for the policy-skill-stub fix) — the
  harness invoked for the real dry-run and both real dispatch attempts.
- PR #3166 (canonical: `gh pr view 3166 --repo tokenmaxxxer/on-the-record`,
  read this session; prior session, not on this branch) — the gh-guard
  seed-issue-creation blocker and the `verify_preregistration.py`
  squash-merge defect this session independently reproduced (see "What
  was done").

## Open findings

1. **Cross-family skill-source tier conflict blocks the skills-off arm's
   dispatch** for any skill that is also mirrored (with diverging
   content) under `~/.claude/skills` on the execution machine —
   `pipeline.py::_cross_family_candidate_corpus()`, called unconditionally
   from `directive_assembly.py` on every dispatch, independent of the
   `--skills` argument's own source qualifier (canonical: `pipeline.py:
   1423-1490`, `directive_assembly.py:756`, read this session; live
   reproduction cited in "What was done" step 3). Not fixed here (see
   "Why"). Resolution path: either scope
   `_cross_family_candidate_corpus()` to respect an explicit source
   qualifier the way the primary `--skills` resolution already does (a
   `pipeline.py`/`skills.py` change, needs its own review since it is
   shared, safety-relevant code), or provision a sandbox execution
   environment where the target skill under test is not also present
   under `~/.claude/skills`.
2. **`compute_h1_manipulation()`'s directive-bytes proxy has a
   construct-validity gap** for skills delivered via the runtime Skill
   tool (live evidence cited in "Why" above: both real skills-on
   workspaces contain only the 8 session-universal baseline policy files
   in `.on-the-record/directive/`, byte-identical regardless of which
   skill was mounted) — not fixed here; recorded in the results JSON's
   `construct_validity_note_on_h1_metric` for whoever next revisits H1's
   operationalization.
3. **`spawn.py watch`'s roster-lookup reports `watch-failed`/"no record"
   for sessions that genuinely completed** (derived: `gh pr view 23
   --repo JiwonJung94/study-companion` and `gh pr view 24 --repo
   JiwonJung94/study-companion`, both state OPEN — full evidence chain in
   "What did not work") — not diagnosed to a root cause or fixed here;
   flagged per-arm in the results JSON.
4. `verify_preregistration.py`'s squash-merge git-ancestry defect (PR
   #3166's finding, reproduced identically here — see "What was done")
   — explicitly out of scope per this session's spawning instructions; a
   separate session is redesigning that check.

## Next steps

None from this session — `loop_state: terminal`. The four open findings
above are handed off, not owned by this record.

skill-verdict: experiment-trust — applied: invoked; Step 1 scope-gate
cross-check and Step 5 Twyman's-law forward-trace in "Why", surfacing the
H1 construct-validity finding (Open findings item 2)
skill-verdict: silent-failure-audit — applied: invoked; classified
`build_stub_skill_repo()`'s new code and `execute_arm()`'s existing
dispatch/watch failure paths as Handled in "Why"
skill-verdict: product-discovery-hypothesis-testing — not-applicable: no
`docs/proposals/` file was scoped, registered, or advanced this session
(see "Why")
