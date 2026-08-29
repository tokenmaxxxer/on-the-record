---
proposal: docs/issue-2695/proposals/requirements-quality+technical-writing-minimalism-scoping-37ef6c94.md
---

# Hunt record — run-md-dead-steps

## before-landing — stance: assume the gate/mechanism just touched is bypassable — find the bypass

canonical: `git diff -- on-the-record/commands/run.md`, `on-the-record/commands/run.md` (post-change file, `grep -n "번 스텝" ...` and `grep -n "^[0-9]\+\. \*\*" ...` output), `docs/specs/enforcement-boundary.md` line 98, `gates/remediation_spawn.py` source

Verdict: FINDING — deleting the "먼저 remediation 대기열을 확인한다(issue #587)" step from run.md orphans `gates/remediation_spawn.py`: no instructed call site remains anywhere in run.md, silently bypassing the only reachability path `docs/specs/enforcement-boundary.md` documents for that gate.
Kind: silent-failure
Seed: `git diff -- on-the-record/commands/run.md` (removed 4-name classification step + removed the whole remediation-queue-check step, renumbered 1-7 to 1-6)
cap_seconds: 120
tier: size:21-200
diff_stat_lines: ~21 changed lines (per dispatcher context)
started_at: 2026-08-29T00:00:00Z
ended_at: 2026-08-29T00:05:00Z

### Reproduce
```
cd on-the-record-issue-2695-...
grep -n "remediation" on-the-record/commands/run.md   # -> no output at all, exit 1
grep -n "remediation_spawn" docs/specs/enforcement-boundary.md
# -> line 98: "`remediation_spawn.py` | contract | new (issue #587):
#    `pending_remediation_tasks` is reachable zero-install via `run.md`'s
#    own instructed step (`python3 $ON_THE_RECORD/gates/remediation_spawn.py
#    --issue <n> -C <repo>`), run directly by every consumer's orchestrator
#    session — not wired into a `PreToolUse`/`Stop` hook or `gates/ci.py`"
```

### Observed
`grep -n "remediation" on-the-record/commands/run.md` returns nothing (exit
code 1) — the post-diff run.md contains zero mentions of remediation,
`remediation_spawn.py`, or issue #587's queue check. Meanwhile
`docs/specs/enforcement-boundary.md:98` still reads (unchanged by this
diff): "`remediation_spawn.py` ... `pending_remediation_tasks` is reachable
zero-install via `run.md`'s own instructed step ... run directly by every
consumer's orchestrator session — not wired into a `PreToolUse`/`Stop` hook
or `gates/ci.py`". The spec's claimed reachability path no longer exists in
the file it points to.

### Expected
Either run.md keeps an instructed call to `gates/remediation_spawn.py`
(folded into the new step numbering, e.g. into step 3 "누구를 깨울지"), so the
gate stays reachable the way `docs/specs/enforcement-boundary.md` describes,
or that spec row is updated to stop claiming a `run.md`-instructed
reachability path that no longer exists. As shipped, an orchestrator
following the new run.md verbatim will never invoke `remediation_spawn.py`,
so any pending remediation task recorded under issue #587 goes unsurfaced
with no error, no lint failure, and no visible sign the check was skipped —
free "판단" (step 3, "기계가 평가하는 라우팅 표는 없다... 당신이 판단해") silently
takes over the ground the removed mandatory step used to cover.

Separately checked (no findings): all `번 스텝` cross-references left in
run.md after the renumbering (lines 221, 240, 260, 283, 300, 302, 309-310,
409, 426, 428, 430, 438, 545) resolve correctly against
`grep -n "^[0-9]\+\. \*\*" on-the-record/commands/run.md`'s new 1-6 list
(5=PR 설명, 6=결정 중계/큐, 3=라우팅 판단/근거, 1=이슈 등록, 2=판단) — none
dangle. `gates/patrol_wiring.py` and `on-the-record/UNENFORCED-CLAUSES.md`
reference run.md only in prose, not by step number, so the renumbering does
not break them. The new step-2 text stays prose (no table, no fixed name
list) and explicitly disclaims re-fixing role identities, citing #2572's
unified `--skills` — it does not reintroduce the forbidden fixed list in
different words.
