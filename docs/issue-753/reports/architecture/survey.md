---
code_under_review:
- spawn.py
- on-the-record/hooks/directive.sh
- docs/issue-700/
- docs/issue-719/proposals/one-writer-claim-and-recut-guard.md
- docs/issue-732/proposals/absorbed-branch-untracked-recut.md
- docs/issue-451/proposals/2026-08-08-follow-loop-stall-bound.md
- docs/issue-451/reports/implementation.md
- docs/issue-484/reports/implementation.md
- docs/issue-699/proposals/consult-and-goal-loop.md
- docs/issue-699/reports/implementation.md
- docs/issue-726/reports/conformance-review.md
type: audit
breaking: false
verdict: pending
loop_state: verdict-issued
---

# Issue #753 — session completion durability audit (architecture, phase-1 survey)

This issue's Acceptance is read-only (`provenance: read`): the deliverable
is the classified findings themselves, not a build. This survey is the
audit's full content; no phase-2 code/record follow-on is proposed beyond
what §"Open findings" recommends as separate future issues.

## What was done

Read-only audit generalizing the 2026-08-11 strand family (#700, #719,
tokenmaxxxer-core#203, #705/#726, #732) plus the watch/re-arm lineage
(#451/#484) and the goal-loop line (#699 R3) into the full space of ways an
on-the-record session breaks off before the goal. Classified each sub-area
MET/PARTIAL/GAP against northpole reqs #1 (finish the goal) and #4
(durability of the record), with file:line evidence, and additionally
recorded a previously-unrecorded concurrent-rulebook-clone race observed
2026-08-11 as a session-durability GAP.

## Why

Issue #753 asks for exactly this generalization, read-only, ranked by
northpole-centrality and observed-failure-frequency, with every PARTIAL/GAP
naming the missing mechanism, its owning repo, and evidence.

## Upstream

docs/issue-753 (this issue). Related upstream records:
`docs/issue-719/proposals/one-writer-claim-and-recut-guard.md`,
`docs/issue-732/proposals/absorbed-branch-untracked-recut.md`,
`docs/issue-451/reports/implementation.md`,
`docs/issue-484/reports/implementation.md`,
`docs/issue-699/reports/implementation.md`,
`docs/issue-726/reports/conformance-review.md`.

## Sub-area classification

### 1. Session-end outcome classes (failed-no-commit / uncommitted-work / progressed-dirty-tree / stall / refused)

**PARTIAL.** The outcome taxonomy and detection exist as real code:
`classify()`'s output feeds the `outcome` variable in `spawn.py`, with an
explicit `uncommitted-work` reclassification in `spawn.py` (function body
guarding `if outcome == "silent-failure" and uncommitted:`) and a
`push-rejected` reclassification immediately after it. The
uncommitted-work case prints actionable recovery guidance ("같은 이슈로
재스폰하면 이 워크스페이스를 이어받아 커밋부터 끝낼 수 있다") in the same
block. This is real, exercised detection — MET as detection.

What remains PARTIAL: the release-before-push race this class used to
produce (#719) has been closed in code — `_release_spawn_claim` now fires
in a `finally` block *after* `ensure_pushed()` returns, with a comment
citing #719 explicitly (`gh` 바이너리 부재 등, so the claim always releases
even if `ensure_pushed()` raises) — but the respawn deadlock for the
absorbed-branch/untracked-only case (#732) is still `status: proposed`
(frontmatter of `docs/issue-732/proposals/absorbed-branch-untracked-recut.md`),
not landed: `git checkout -B` in `spawn.py`'s branch re-cut path still
falls through to a no-op fallback on untracked-path collision, per the
proposal's own citation. A session hitting this path today still stalls
silently forever rather than surfacing as any of the four named outcome
classes.

- Rank: 1 (northpole #1-central — this is the direct "did the goal get
  reached" signal). Observed-failure-frequency: high — multiple distinct
  live field incidents are cited by name across the strand docs (#289,
  #272, #295, #319), plus the two 2026-08-11 live gate refusals cited in
  §3's source, `docs/issue-726/reports/conformance-review.md` (rows 3 and
  4 of its catalog, each citing a named `.events.jsonl` file as the
  reproduction).
- Missing mechanism: land #732's stash-push/pop re-cut fix; note the
  proposal's own warrant-hunt found a second latent gap — leftover stash
  entries are invisible to `clean`'s guard (`spawn.py`, the `clean`
  subcommand's stash-blind status check) — so the fix as proposed does
  not yet close that second vector either.
- Responsible repo: on-the-record (`spawn.py`).

### 2. Watch/re-arm coverage and idle-latency risk (#451/#484 lineage)

**MET.** This is real, exercised, cross-referenced code, not proposal-only:
`_await_bounded` in `spawn.py` derives `limit_s` from `stall_timeout_min`
and enforces a stall bound (issue-451's `docs/issue-451/reports/implementation.md`
confirms this landed); `_watch` and `_watch_all` in `spawn.py` are the
watch loop bodies; `roster_watchdog` plus persisted state via
`_watchdog_state_load`/`_watchdog_state_save` is the re-arm mechanism —
each watchdog pass reads persisted state instead of starting blind,
closing the #484 registration race (`docs/issue-484/reports/implementation.md`:
"Watch attaches before the roster write lands"). Both #451 and #484 cite
these same functions as landed implementation, not aspiration.

- Rank: 3 (northpole-central but already closed; low remaining
  observed-failure-frequency).
- Missing mechanism: none identified.
- Responsible repo: n/a (MET).

### 3. Orchestrator failure behavior — diagnose-and-fix vs. blind-respawn

**PARTIAL.** Not blind respawn: `_respawn_fingerprint` and
`_respawn_or_cap` in `spawn.py` compare fingerprints before respawning to
detect no-progress loops; `RESPAWN_MAX_ATTEMPTS = 2` and
`RESPAWN_ABSOLUTE_MAX = RESPAWN_MAX_ATTEMPTS * 4` cap the retry count,
with a crash-comment fallback ("모든 {cap} 회 자동 재스폰 소진... 사람
개입 필요") when the cap is hit. `next_action` is closed to exactly
`respawn` / `resume-watch` / `manual-review` / `none` (documented as ADR
Decision 3 in a comment block in `spawn.py`): `crashed` → respawn,
`stalled` → `resume-watch` (explicitly *not* auto-respawned, per an
adjacent comment "자동으로 실행하지 않는다"), otherwise (not-in-progress)
→ respawn.

What keeps this PARTIAL rather than MET: the decision closure is a fixed
four-state table keyed on crash/stall/verdict, not an actual diagnosis of
*why* the session broke off. A session that dies from, e.g., the
concurrent-rulebook-clone race in §6 below reads as a bare non-zero `rc` /
crash to this table and gets respawned up to the cap with no
differentiation from a transient network blip — the respawn loop retries
the same failure mode blindly within the cap, even though it is not
literally infinite. This matches the issue's "observed on Mac" framing:
the cap prevents runaway respawn, but nothing in the four-state table
inspects the failure signature to decide whether respawning can possibly
help.

- Rank: 2 (northpole #1-central; failure-frequency currently bounded by
  the cap, but every capped-out session becomes a `manual-review` that a
  human must diagnose from scratch — the diagnosis work the orchestrator
  skipped is not eliminated, just deferred to a human).
- Missing mechanism: failure-signature-aware branching before respawn
  (e.g. distinguish a TOCTOU clone race, a permission denial, and a stall
  as different `next_action` inputs instead of collapsing them all into
  `crashed`).
- Responsible repo: on-the-record (`spawn.py`'s `_respawn_or_cap` /
  `_auto_respawn_check`).

### 4. Resumability — what makes a session resumable vs. losing work

**PARTIAL.** Two real mechanisms exist: (a) the `resume-watch` next-action
in `spawn.py` for a merely-stalled-but-alive session, observation only, no
state loss; (b) the uncommitted-work recovery path (the same block as §1)
— a respawn onto the same branch inherits the prior session's dirty
workspace, so uncommitted work survives a respawn as long as the
workspace itself isn't discarded. Both rely on git-level artifacts
(branch head, working tree) as the durability substrate — there is no
explicit `runId`/checkpoint object; a grep of `spawn.py` for
`checkpoint`/`resume` beyond the `resume-watch` literal turns up nothing
else.

This is durable for the "session died mid-edit, files still on disk" case,
but not for the "session died and the workspace itself needs
reconstruction" case (e.g. §6's clone race, or a re-cut like #732's) —
there, resumability degrades to §1's stall/no-op behavior rather than a
clean recovery.

- Rank: 4 (northpole #1-central but the common case — dirty workspace
  survives — is already handled; the residual gap is narrower).
- Missing mechanism: an explicit resume path for
  workspace-reconstruction failures (clone races, absorbed-branch re-cut)
  that doesn't fall through to silent no-op.
- Responsible repo: on-the-record (`spawn.py`).

### 5. Goal-loop continuation across a dropped session (#699 R3)

**PARTIAL.** #699 R3 is landed as *directive text*, not as enforced state:
`on-the-record/hooks/directive.sh` (line 150) carries the "YOUR GOAL LOOP"
paragraph (decompose → delegate each piece → integrate → continue to
done-or-genuinely-blocked → report the delegation trace), confirmed
shipped by `docs/issue-699/reports/implementation.md` (`loop_state:
landed`). This is prompted behavior a session reads at SessionStart, not a
mechanism the orchestrator enforces or checks after the fact — there is no
gate verifying a session actually followed R3, and no cross-session state
that lets a *new* session (after the old one dropped) discover "the prior
session was mid-goal-loop, resume from step N." Continuation across a
drop relies entirely on §4's git-level durability (the branch/tree state
left behind) plus a human or respawn re-reading the issue from scratch —
there is no goal-loop-specific resumption artifact.

- Rank: 5 (northpole #1-central in principle, but low observed-failure
  frequency so far — #699 is recently landed and no field incident is
  cited yet against R3 specifically; ranked below areas with live
  incident citations).
- Missing mechanism: a goal-loop state artifact (even a simple
  consult-log-style trace, per `_append_consult_trace()` at the consult
  layer in `spawn.py`) surfaced to a respawned session so it can resume
  mid-loop instead of re-deriving the decomposition from the issue text
  alone.
- Responsible repo: on-the-record (`on-the-record/hooks/directive.sh`,
  `spawn.py` goal-loop wiring).

### 6. Concurrent-rulebook-clone race (observed 2026-08-11, not previously recorded)

**GAP.** Confirmed check-then-act (TOCTOU) race, two independent sites in
the same file, no lock/mkdir-exclusivity/retry-on-exists guard found near
either:

- `rulebook_checkout()` in `spawn.py` (function starts at line 207): checks
  `_mkt(d).exists()`, then unconditionally `git clone`s into the same
  path `d = ROOT / "runs" / "rulebooks" / mkt` if absent. Two same-role
  sessions racing this function both see the directory absent, both
  attempt `git clone` into the identical target — `git clone` refuses
  when the target directory exists and is non-empty, matching the
  observed "target exists not empty" symptom exactly.
- `core_root()` in `spawn.py` (function starts at line 3203): identical
  pattern for `runs/rulebooks/tokenmaxxxer-core` — existence check, then
  unconditional clone guarded only by a bare `except OSError: pass`,
  which does not catch or handle a `subprocess`-level clone failure (the
  clone runs via `_run_net`, not a raw filesystem call, so `except
  OSError` would not even catch a `git clone` non-zero exit in the first
  place — the exception guard is effectively a no-op against this
  failure mode).

No `fcntl`/`flock`/`.lock` pattern exists near either call. This was
searched for across `docs/reports/` and every `docs/issue-*/proposals/`
and `docs/issue-*/reports/` file dated 2026-08-11 — unverifiable: no
matching file found; the race as described in the issue prompt has no
prior strand doc anywhere in the tree, confirmed by exhaustive
filename-pattern search rather than a single grep miss.

- Rank: 1 (northpole #1-central — a lost session here never reaches the
  goal at all, it dies before any role logic runs; observed-failure-
  frequency stated directly in the issue prompt as the majority of one
  parallel same-role spawn batch failing this way, the highest
  concentration of any area in this audit).
- Missing mechanism: exclusive-create semantics around the clone (e.g.
  clone into a per-PID temp dir under `runs/rulebooks/` then atomic
  `os.rename` into the final path, or an `flock`-guarded critical section
  around the check-then-clone in both `rulebook_checkout()` and
  `core_root()`) plus a real retry-on-exists path instead of the current
  bare `except OSError: pass`.
- Responsible repo: on-the-record (`spawn.py`, both `rulebook_checkout()`
  and `core_root()`).

## Ranked summary

| Rank | Area | Verdict | Repo |
|---|---|---|---|
| 1 (tie) | Concurrent-rulebook-clone race (§6) | GAP | on-the-record |
| 1 (tie) | Absorbed-branch/untracked re-cut deadlock (§1) | PARTIAL | on-the-record |
| 2 | Orchestrator failure-signature blindness (§3) | PARTIAL | on-the-record |
| 3 | Watch/re-arm (§2) | MET | — |
| 4 | Resumability for workspace-reconstruction failures (§4) | PARTIAL | on-the-record |
| 5 | Goal-loop cross-session continuation (§5) | PARTIAL | on-the-record |

## Open findings

- §6 (clone race) has no prior strand doc despite being directly named in
  the issue prompt as a 2026-08-11 observation — it should get its own
  issue rather than staying only inside this audit, since this record's
  write scope is read-only per issue #753 and cannot itself land a fix.
- §1's #732 fix and its own warrant-hunt-found second gap (leftover
  stash invisible to `clean`'s guard) are both still `status: proposed`,
  unlanded as of this audit.
- §3 and §5 both point at the same underlying shape: session-end handling
  reacts to *that* a session stopped, not *why* — a shared
  failure-signature concept could serve both the respawn-branching gap
  (§3) and the goal-loop-resume gap (§5) rather than being fixed
  independently.

## next steps

File a new issue for §6 (clone race) since it is undocumented and
highest-frequency; prioritize landing #732 given it is the only area with
a written but unlanded fix already in hand.

## resolution path

#732's proposal (`docs/issue-732/proposals/absorbed-branch-untracked-recut.md`)
already specifies the fix for §1 — land it. §6 needs a new proposal in a
new issue since no proposal for it exists yet anywhere in the tree.
