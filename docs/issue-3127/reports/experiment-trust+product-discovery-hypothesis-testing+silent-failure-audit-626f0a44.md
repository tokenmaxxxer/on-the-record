---
issue: 3127
role: experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-626f0a44
author: experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-626f0a44
skills: experiment-trust (skill-repository(c05de12)), product-discovery-hypothesis-testing (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-3127/decisions/pre-registration.md
    sha: same-commit  # inherited unchanged from fb0bb0d3, not modified this session
  - path: scripts/issue-3127/run_consumer_pair.py
    sha: same-commit
  - path: docs/issue-3127/reports/independent-verification-1.md
    sha: same-commit
---

# issue-3127 — experiment-trust+product-discovery-hypothesis-testing+silent-failure-audit-626f0a44 record

## What was done

- Read issue #3127, `docs/issue-3127/decisions/pre-registration.md`, PR
  #3164's `docs/issue-3127/reports/independent-verification-1.md`, and
  `python3 scripts/issue-3127/run_consumer_pair.py --help` before running
  anything.

- Ran `python3 scripts/issue-3127/run_consumer_pair.py --dry-run` —
  acceptance: `bash -c "python3 scripts/issue-3127/run_consumer_pair.py --dry-run"`
  — result: exit 0. Plan verified by hand against the pre-registration:
  arms (skills-on bare name / skills-off `skill-repo:` qualifier),
  held-constant factors (sandbox repo, model, orchestrator dispatch shape,
  task text, permission mode, issue numbering), the H1 gate
  (`compute_h1_manipulation()` / `gate_pair_on_h1()` excludes a pair from
  H2 on identical directive bytes, never silently), the blind scorer
  (`scrub_skill_slugs()` then `evaluate_pair_blind()`), and the wall-clock
  field names (`wall_clock_to_pr_open_s` reported under its true name,
  `wall_clock_to_landed_s` always null with a stated reason) all match —
  canonical: this session's own `--dry-run` stdout, read in full this turn.

- Given `CORE_BUILD_NOW=1` (canonical: `printenv CORE_BUILD_NOW` output:
  `1`, this turn) and the task's explicit authorization to execute for
  real, went past the dry-run into an actual `--execute` attempt rather
  than repeating the prior session's preemptive decline.

- Located the sandbox: `JiwonJung94/study-companion` — canonical: `gh repo
  view JiwonJung94/study-companion --json name,description,defaultBranchRef,createdAt`
  output this turn: `createdAt: 2026-09-02T00:41:13Z`, description
  matching the comprehension-gap/study-groups scenario the pair task text
  describes. Cloned it and confirmed it is spawn.py-init'd — canonical:
  `cat docs/specs/approvers.md` in the clone, output: `- JiwonJung94` —
  and already carries issue-1 and issue-5 docs matching this harness's
  pair task text about that scenario verbatim: canonical: `find docs
  -maxdepth 2 -iname "*issue-1*" -o -iname "*issue-5*"` run inside that
  clone, output: docs/issue-1, docs/issue-5, docs/issue-13, docs/issue-10
  — all four of those paths are untracked in this repository; they exist
  only inside the separately-cloned `JiwonJung94/study-companion` sandbox
  repo, not here.

- Attempted to create the 4 seed GitHub issues `--issue-map` requires (one
  skills-on + one skills-off issue per registered pair) via `gh issue
  create --repo JiwonJung94/study-companion ...`. Refused live — canonical:
  this turn's tool-result error text from that call: "gh-guard: refused
  for skill session '...': issues are the user's requirement backlog,
  user-authored only (contract v3 s9) — no skill touches them (two-account
  model, contract v3 s8)". Confirmed nothing was created before the hook
  fired — canonical: `gh issue list --repo JiwonJung94/study-companion
  --state all --limit 30` output, run both before and after the refused
  call this turn: identical in both runs — issues 1, 5, 10, 13 only. Did
  not attempt to route around it (no alternate `gh` auth, no hook skip, no
  `--no-verify`) — this is a deliberate safety boundary, not an obstacle
  to shortcut.

- Updated `emit_not_executed_results()`'s `run_status_reason` and
  `next_steps_for_a_future_executing_session` in
  `scripts/issue-3127/run_consumer_pair.py` to state this session's actual,
  mechanically-verified blocker (gh-guard) in place of the prior session's
  caution-based reasoning (self-daemonization / no turn for human
  confirmation — both now resolved: `execute_arm()` already blocks on
  `spawn.py watch --follow`, and this session had explicit authorization),
  and regenerated `docs/issue-3127/_assets/consumer-path-results.json` via
  `--emit-not-executed` (harness-generated, not hand-edited) — derived:
  `python3 scripts/issue-3127/run_consumer_pair.py --emit-not-executed
  --out docs/issue-3127/_assets/consumer-path-results.json` — result:
  `wrote docs/issue-3127/_assets/consumer-path-results.json`.

- Independently found a second, separate structural blocker while running
  acceptance check 3 — acceptance: `python3 scripts/issue-3127/
  verify_preregistration.py` — result: exit 1, "both files were introduced
  in the same commit (fb0bb0d3...) -- the pre-registration must be
  committed strictly before the results, not alongside them". Root-caused
  it with:
  ```
  $ git show fb0bb0d3^:docs/issue-3127/decisions/pre-registration.md
  fatal: path 'docs/issue-3127/decisions/pre-registration.md' exists on disk, but not in 'fb0bb0d3^'
  $ git show fb0bb0d3^:docs/issue-3127/_assets/consumer-path-results.json
  fatal: path '...consumer-path-results.json' exists on disk, but not in 'fb0bb0d3^'
  $ git log --oneline --diff-filter=A --follow -- docs/issue-3127/decisions/pre-registration.md
  fb0bb0d3 issue-3127: pre-register + build consumer-path harness (spawn.py dispatch); live run not executed, reasons recorded (#3131)
  $ git log --oneline --diff-filter=A --follow -- docs/issue-3127/_assets/consumer-path-results.json
  fb0bb0d3 issue-3127: pre-register + build consumer-path harness (spawn.py dispatch); live run not executed, reasons recorded (#3131)
  $ git cat-file -t 9c9801cd470129580de54b78a32abc30875de90e
  commit
  ```
  canonical: the four command outputs quoted directly above, this turn.
  Both files were introduced net-new in the same squash-merge commit
  (`fb0bb0d3`, already on `main`), which collapsed whatever internal
  commit order PR #3131's branch actually had — PR #3164's own
  verification record (`docs/issue-3127/reports/independent-verification-1.md`,
  lines 96-98) ran this same check against a pre-squash worktree and got a
  different, passing result ("ancestor of results commit 9c9801cd..."):
  that commit object still exists in this repo's object store as a
  dangling commit (confirmed `commit` above) but `git log --all` does not
  reach it, i.e. it was squashed out of `main`'s reachable history. Reading
  `_first_commit_for_path()` in `scripts/issue-3127/verify_preregistration.py`
  (it takes the oldest `--diff-filter=A` commit reachable from HEAD for
  each path) — derived: static read of that function this turn — shows no
  additive commit on top of current history can ever change which commit
  it resolves to for either path, since `fb0bb0d3` is permanently the
  oldest `A` event for both once merged.

- Ran the harness's own tests and the full suite after the edits —
  derived: `python3 -m pytest tests/test_issue_3127_run_consumer_pair.py
  tests/test_issue_3127_run_pair.py tests/test_issue_3127_h1_and_scoring.py -q`
  — result: 29 passed; derived: `python3 -m pytest tests/ -q` — result:
  352 passed, 2 pre-existing warnings, 0 failures.

- No worker sessions were spawned; no GitHub issues or PRs were created in
  `study-companion`; no compute beyond this session's own tool calls was
  spent — canonical: the `gh issue list` before/after comparison above, and
  no `spawn.py`/`gh pr create` calls appear anywhere in this session's tool
  history.

## Why

The task explicitly authorized real execution (`CORE_BUILD_NOW=1` +
operator confirmation relayed through the issue text), so the right move
was to actually attempt `--execute`, not repeat the prior session's
preemptive decline — but "attempt" means following the chain to its real
end, not stopping at the first friction. gh-guard's refusal is a
deliberate, mechanically-enforced safety boundary (two-account model:
skill sessions cannot author requirement-backlog issues in any repo), and
the top-level instructions are explicit that safety gates get identified
and reported, not routed around — so the correct response was to record
exactly what the gate said and why, not retry with different arguments or
a different credential. Investigating the `verify_preregistration.py`
failure with `git show`/`git log`/`git cat-file` rather than accepting a
bare exit-1 (or silently patching the check) follows the same discipline
this repo's own record-claim-guard and this issue's must-not clauses
require: outcome claims need a traceable, executed check, and "the check
fails" needed its own root cause before it could be reported honestly.

## What did not work

The real `--execute` run did not happen: gh-guard blocked seed-issue
creation before any `spawn.py` dispatch could occur (see "What was done").
This is **not** a null H1/H2/H3 result and must not be read as one — no
session was spawned, no directive-composition bytes were compared,
nothing was measured in either direction. It is also not the "every pair
fails H1" scenario the issue warned about (a repeat of #3053's retracted
zero-mount run) — that scenario presumes sessions ran and produced
comparable directive-byte data; here, zero sessions ran, so there is
nothing to gate on H1 at all.

## Upstream basis

- `docs/issue-3127/decisions/pre-registration.md` (same-commit fb0bb0d3,
  read but not modified this session — metric, threshold, guardrail,
  sample size all unchanged)
- `scripts/issue-3127/run_consumer_pair.py` (same-commit as this record;
  `emit_not_executed_results()`'s reason text updated this session)
- `docs/issue-3127/reports/independent-verification-1.md` (PR #3164's
  verification, cited above for the pre-squash commit-order evidence)

## Open findings

1. `verify_preregistration.py` (acceptance check 3) cannot pass against
   current `main`/this branch, and will not pass for any future session
   built on top of it, because PR #3131's squash-merge (`fb0bb0d3`)
   collapsed the two-commit ordering the check's git-ancestry comparison
   requires (see "What was done" for the reproduction). No additive commit
   can fix this. Resolution path: out of this session's authority — either
   a deliberate, explicitly-authorized rewrite of `main`'s history
   (high-risk, needs its own decision and likely a different landing
   policy so future PRs on this issue don't squash), or a redesign of
   `verify_preregistration.py`'s ordering mechanism to survive
   squash-merge landings (a design change beyond this issue's ask, needs
   its own proposal). Not fixed here.
2. gh-guard structurally prevents any skill session from creating the 4
   seed issues `--issue-map` needs, in any repo. Resolution path: the
   human operator creates the 2 pairs' issues (skills-on + skills-off
   each) in `JiwonJung94/study-companion` out-of-band — body text and
   process spelled out in `consumer-path-results.json`'s
   `next_steps_for_a_future_executing_session` — then hands the resulting
   issue numbers to an executing session via `--issue-map`.
3. The real H1/H2/H3 measurement remains unmeasured (see "What did not
   work"). The power statement already in `pre-registration.md` still
   holds as written; nothing about it changed this session.

## Next steps

derived: `git log --oneline -1` on this branch this turn — result:
`c06c6dc7 issue-3127: attempt real consumer-path execution, blocked by
gh-guard issue-creation gate`, carrying the `run_consumer_pair.py`
reason-text update and the regenerated `consumer-path-results.json`, both
staged and committed. This session's own available actions end here.
Continuing the actual measurement is necessarily a different
session's/operator's action:

1. Operator creates the 4 issues in `JiwonJung94/study-companion` (see
   `consumer-path-results.json`'s `next_steps_for_a_future_executing_session`).
2. A future session runs `--execute --i-understand-this-spawns-real-sessions
   --issue-map ...`, blocking on `spawn.py watch --follow` per arm,
   committing after each pair.
3. Separately, someone with authority over `main`'s history or over
   `verify_preregistration.py`'s design decides what should happen to
   acceptance check 3 given open finding 1 above — before any future
   session's results are graded against it.

skill-verdict: other mounted skills: not triggered — no skill was invoked
via the Skill tool this session. `experiment-trust` was judged
not-applicable (no experiment result exists yet to interpret/trust — zero
sessions ran, so there is nothing to apply Twyman's-law skepticism or
SRM/AA checks to; the pre-registration's own scope note already
establishes those checks don't apply at this n regardless).
`product-discovery-hypothesis-testing` was judged not-applicable (no
proposal moved through the state machine — the pre-registration already
exists and is frozen; this session read it but registered nothing new).
`silent-failure-audit` was judged not-applicable (no AI-written
error-handling code was authored or audited this session — the only code
edit was correcting a string literal's factual content, not an error
path).
</content>
