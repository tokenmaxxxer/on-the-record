---
issue: 2695
role: requirements-quality+technical-writing-minimalism-scoping-37ef6c94
author: requirements-quality+technical-writing-minimalism-scoping-37ef6c94
skills: requirements-quality (skill-repository(297e350)), technical-writing-minimalism-scoping (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/commands/run.md
    sha: same-commit
  - path: docs/specs/enforcement-boundary.md
    sha: same-commit
---

# issue-2695 — requirements-quality+technical-writing-minimalism-scoping-37ef6c94 record

## What was done

Edited `on-the-record/commands/run.md` (the orchestrator directive) to
retire the two dead-machinery mandatory steps #2695 names:

- Removed the four-name classification step (old step 2: feasibility /
  product / ux-design / coding, keyed off a `리드 역할` table the text
  explicitly forbade extending) and replaced it with a non-enumerating
  step: state in one line whether anything is still unresolved
  (investigation / requirements / UX judgment needed) before filing, or
  state readiness to implement directly — no fixed name/category is
  selected from.
- Removed the remediation-queue step (old step 3) entirely, with no
  replacement text in run.md — the mechanism it depended on is
  confirmed structurally dead (see Why).
- Renumbered every downstream cross-reference in the same file to
  match the compacted step list below.
  derived: `grep -n '^[0-9]\. \*\*' on-the-record/commands/run.md` — result:
  ```
  22:1. **요구사항 → 이슈.**
  89:2. **이슈를 등록하기 전에, 지금 확정 짓지 못한 것이 있는지 말한다.**
  99:3. **누구를 깨울지.**
  105:4. **띄운다 — 반드시 백그라운드로.**
  124:5. **PR 을 설명한다.**
  313:6. **사용자의 결정을 중계한다.**
  ```
  derived: `git diff --stat -- on-the-record/commands/run.md` — result: `1 file changed, 26 insertions(+), 40 deletions(-)`

Acceptance check 1 (four-name classification is gone from run.md, and
the replacement names no fixed identity set):
acceptance: `grep -nE 'feasibility|ux-design|리드 역할' on-the-record/commands/run.md` — result: no output, exit 1 (0 occurrences).
provenance: executed-live

Acceptance check 2 (remediation-queue step is gone; queue shown unable
to produce a line): the step's only value source is `routed_to`, set
unconditionally in `on-the-record/hooks/delegated-judgment-gate.sh`:
```
# issue #2559: this used to route `target_path` to whichever role's
# write_scope glob-matched it. write_scope is gone — no role owns a path
# subset anymore, so there is no ownership signal left to route on.
routed_to = None
```
acceptance: `python3 gates/remediation_spawn.py --issue <n> -C .` run against 5 real board issues (2695, 2690, 2688, 2686, 2682) — result: empty stdout, exit 0, on every issue.
provenance: executed-live
canonical: shell output of the 5 executed `remediation_spawn.py` invocations, this session — empty stdout every time, so "the command prints nothing" is the acceptance criterion's own predicted empty state, not a single-issue fluke.

Acceptance check 3 (an orchestrator following the edited directive
reaches a spawn that produces a PR): ran the edited step 4 verbatim —
`python3 spawn.py lint --issue 2503 -C .` (result: `이슈 #2503 lint: 위반
없음`, exit 0), then, exactly as the edited step 4 instructs, backgrounded
`python3 spawn.py --skills requirements-quality "<task>" --issue 2503 -C .`.
acceptance: `python3 spawn.py --skills requirements-quality "acceptance-format.md 규칙 추가 + authoring-time 체크 구현 (issue #2503)" --issue 2503 -C .`
canonical: spawn.py's own live stdout — `[requirements-quality-112361d7] 워처 자동 무장: pid 2587174`, `스폰은 리턴했지만 세션은 계속 돈다 — 상태는 spawn.py ps, 이어보려면 spawn.py watch --issue 2503 --session requirements-quality-112361d7`, session `requirements-quality-112361d7` armed and running against real issue #2503 at edit time. This record is updated with the session's terminal outcome (PR link or refusal) before `loop_state` moves to a terminal value — see Open findings.
provenance: executed-live

skill-verdict: requirements-quality — not-applicable: the deliverable is retiring dead procedural steps in an internal orchestrator directive, not reviewing or authoring a requirement/user story against EARS/Connextra/QUS.
skill-verdict: technical-writing-minimalism-scoping — applied: invoked; used rule 5 (dedicated cut-search pass) to decide the four-name table and its `리드 역할` column are pure subtraction (dead identities, no replacement needed for #2572's `--skills`-only spawn form to keep working), rule 9 (cut content that doesn't change reader action) to decide the remediation-queue step gets no replacement text (structurally dead, nothing left for a reader to act on), and rule 6 (delete purely definitional content, keep only what has a task attached) to keep the step-2 replacement text short and action-only (one line, no table).

Also updated `docs/specs/enforcement-boundary.md`'s `remediation_spawn.py`
row (a warrant-hunter finding — see Open findings) so it stops claiming a
`run.md`-instructed reachability path that this same change removed.

## Why

**Step 2 (classification):** none of the four names (`feasibility`,
`product`, `ux-design`, `coding`) is a mountable skill, so the
classification's output could never be handed to `--skills`, the sole
spawn form since #2572 (`ls -d ~/.claude/skills/{feasibility,product,ux-design,coding}`,
executed live in #2139's 2026-08-29 evidence comment — all four absent;
reused per this task's instruction not to redo #2139's derivations). The
issue's `must not` forbids swapping the table for a different fixed list
of names, so the replacement step preserves only the underlying
discipline (declare what's unresolved before filing) as free prose,
naming no role identity or category.

**Step 3 (remediation queue):** `gates/remediation_spawn.py:77` reads
`fields.get("routed_to", "")`, and the only producer of that field is
the `routed_to = None` line quoted above
(`on-the-record/hooks/delegated-judgment-gate.sh`), landed by #2559
with its own comment explaining the capability (per-role `write_scope`
ownership) is gone. Since the step can never produce the
`<역할>\t<태스크>` line its own branching depends on, it is
unfollowable-as-written and is removed outright rather than softened
into an optional check (the issue's `must not` forbids that fix shape
too). Per #2695's non-goals, `gates/remediation_spawn.py` and
`delegated-judgment-gate.sh`'s escalate branch are untouched — only the
directive text describing them, and the one spec row whose reachability
claim depended on that text, are retired.

## What did not work

- Ran `python3 gates/spec_index.py --update` after editing
  `docs/specs/enforcement-boundary.md` (per the standing obligation that
  a `docs/specs/*` edit regenerates `docs/specs/reconciled-index.md` in
  the same commit) — it raised, both before and after this diff:
  ```
  File "gates/spec_index.py", line 71, in update
      new_hash = _sha256(target)
  FileNotFoundError: [Errno 2] No such file or directory: '.../roles/specs/brand-design.spec.json'
  ```
  derived: `git stash && python3 gates/spec_index.py --update; git stash pop` — the identical `FileNotFoundError` reproduces on the clean pre-edit tree, so the generator is broken independent of this change; `docs/specs/reconciled-index.md` is left unregenerated for that pre-existing reason, not skipped.

## Upstream basis

- `on-the-record/commands/run.md`, `docs/specs/enforcement-boundary.md`, this record, and the warrant-hunt record (this commit) — sha: same-commit
- #2139 evidence comment, 2026-08-29 (`gh issue view 2139 --comments`) — derivations for both dead-step rows (skill-absence check, `routed_to = None` quote) reused verbatim per the task's instruction not to redo them.

## Open findings

- A warrant-hunter dispatched before landing (stance: assume the
  gate/mechanism just touched is bypassable) found that removing the
  remediation-queue step orphaned a claim in
  `docs/specs/enforcement-boundary.md` line 98 (pre-fix text) that
  `remediation_spawn.py` is "reachable zero-install via run.md's own
  instructed step" — no longer true once that step was removed.
  canonical: hunter's own finding write-up, appended in this same
  commit under this role's reports subtree (filename dated
  2026-08-29, prefixed `hunt-run-md-dead-steps`) — resolution path:
  fixed in this same commit by rewriting the `enforcement-boundary.md`
  row (see What was done / Why) to state the reachability path was
  retired by #2695 and the module is now manual-invocation-only,
  without touching the module or the gate's escalate branch (#2695
  non-goals).
- The step-4 spawn demonstration (session `requirements-quality-112361d7`,
  real issue #2503) reached a real PR. canonical:
  `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2503-requirements-quality-112361d7.watcher.log`
  — `pr-opened: https://github.com/tokenmaxxxer/on-the-record/pull/2696`,
  then `session-end: progressed` (the session hit its own
  record-claim-guard refusals writing its record after the PR was
  already open, same gate class this record itself hit while being
  written — it did not re-open a second PR or need to). canonical:
  `gh pr view 2696` — `title: issue-2503: acceptance-format
  role-forbidden-action rule + authoring gate`, `state: OPEN`,
  `additions: 305`, `Closes #2503`. Resolution: confirmed — acceptance
  check 3 is satisfied by this real, running-repo PR, not a simulated
  or dry-run spawn.

## Next steps

None — all three acceptance checks are executed-live and cited above;
`loop_state` moves to `landed` with this edit.
