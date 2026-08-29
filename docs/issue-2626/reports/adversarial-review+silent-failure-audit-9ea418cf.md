---
issue: 2626
role: adversarial-review+silent-failure-audit-9ea418cf
author: adversarial-review+silent-failure-audit-9ea418cf
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false
code_under_review: none — audit-only session; scripts/audit_removal_claim.py (landed by #2627) was exercised but not modified
type: audit
breaking: false
verdict: FAIL — 2 of 13 audited items have live survivors; 11 VERIFIED_ABSENT, 1 REASON_HOLDS (not a removal claim)
loop_state: closed
upstream:
  - path: scripts/audit_removal_claim.py
    sha: same-commit
---

# issue-2626 — adversarial-review+silent-failure-audit-9ea418cf record

## What was done

Re-derived all 7 claims in issue #2626's original Scope list plus 6 new-claim rows landed 2026-08-29 (never before audited: #2670, #2600 split into its 3 disclosed slices, #2695, #2503) — 7+6=13 rows total (derived: count the table below) — each against a **clean archive checkout**, never a working-tree grep:

```
derived: git fetch origin main && git archive origin/main | tar -x -C /tmp/audit-otr
canonical: git rev-parse origin/main → 04a041ab9503eae97a7fbd06ad7229547a8f63d3 (on-the-record)
derived: git clone git@github.com:tokenmaxxxer/tokenmaxxxer-core.git && git archive HEAD | tar -x -C /tmp/audit-core
canonical: git rev-parse HEAD → 60cbcb55a785e83edac637b4faea065cdf88f843 (tokenmaxxxer-core)
```
derived: `find /tmp/audit-otr -type f | wc -l` → 4123 files; `find /tmp/audit-core -type f | wc -l` → 600 files.

Each item was investigated by an independent subagent applying the #2548 test (Q1: is the name gone? Q2: does an equivalent exist under another name/shape? Q3: does live code still branch on membership in the closed set?) with actual grep/read commands against the two archives, never trusting the closing PR's title.

### Claim table

| # | claim | source issue(s) | Q1 gone | Q2 reshaped | Q3 branches | verdict |
|---|---|---|---|---|---|---|
| 1 | `PR_TRIGGERED_RECORD_KINDS` / record-kind axis | #2615 | yes | no (successor `AUTO_SPAWN_ROLES` itself now also 0 hits) | no | **VERIFIED_ABSENT** |
| 2 | skip-eligibility exemption, `_filter_execution_observation` | #2615 | yes | no | no | **VERIFIED_ABSENT** |
| 3 | `--role` selector flag | #2592/PR#2595 | yes (`sys.exit` intercept, `spawn.py:2083-2090`) | no (`--session`/`--skills` resolve dynamically, no fixed set) | no | **VERIFIED_ABSENT** |
| 4 | `write_scope` | #2559 | yes (code); stale mention in `docs/specs/impact-classification.md`, `role-spec-template.schema.json` | no (`scope_adherence.py` is a different, issue-scoped opt-in mechanism) | no | **VERIFIED_ABSENT** (docs stale, not live) |
| 5 | `spawn.ROLES`, `_ROLE_SKILLS`, `roles/*.json`, core hook/config removals | #2548 program (#2537/#2538/#2545/#2560, core #331/#328) | yes | no (`_ROLE_SKILLS` replaced by open filesystem-prefix scan, not a closed table) | no | **VERIFIED_ABSENT** (canonical: subagent read `core/hooks/approval-gate.sh`, `record-fields-gate.sh`, `citation-gate.sh`, `facet-keyword-gate.sh`, `ordering-gate.sh` directly at /tmp/audit-core commit 60cbcb5; chained through core #331→#341→#343) |
| 6 | 44-entry catalog / `spawn_roles.json` | #2610/PR#2630 | yes | no (consumers rewritten to task-derived signals, e.g. `axis:` self-declaration, changed-path scanning) | no | **VERIFIED_ABSENT** |
| 7 | retired spawn forms: role-positional, bare-task | #2572 | effectively yes (unconditional `sys.exit` guard, `spawn.py:2517-2530`) | no | no | **VERIFIED_ABSENT** |
| 8 | `CLAUDE_ROLE` → `CLAUDE_SKILL` rename | #2670 (PR #2710/core#348) | yes, 0 live hits outside `docs/` and frozen pre-skills fixtures | **narrow claim: no.** But see "Related finding A" below — adjacent closed-set checks on `MUSTER_SKILLS`/`role` literals survive nearby (pre-existing via #2576, not caused by #2670) | no (for the renamed var itself) | **VERIFIED_ABSENT** (narrow); related survivor flagged separately |
| 9 | #2600 slice 1 — `PG_ROLE`/`HT_ROLE`/`TRAILER_GATE_ROLE`/`RF_ROLE`/`SOG_ROLE` env vars | PR#2668 + core#347 | yes, 0 live hits (53 hits, all in `docs/`) | no | no | **VERIFIED_ABSENT** |
| 10 | #2600 slice 2 — comments/docstrings | PR#2676 | yes, within its own disclosed scope (current-teaching prose) | no — residue matches the slice's own disclosed exclusion list | no | **VERIFIED (in-scope)** (canonical: subagent read PR #2676's commit message listing its disclosed exclusion list, cross-checked against live grep of `lifecycle.py`, `bench/run.py`, `gates/model_routing.py`) — slices 4/5 correctly left untouched |
| 11 | #2600 slice 3 — prompt/directive text | PR#2714 | **no — see "Related finding B" below** | — | — | **FAIL** |
| 12 | #2695 — 4-name classification step + hardcoded-`None` queue step removed from `run.md` | #2695 | yes, both steps gone from `run.md` live text | no (pre-existing, disclosed-out-of-scope `routed_to = None` in `delegated-judgment-gate.sh:741` is not a reshape of the removed *steps* — it predates #2695 and #2695 correctly declined to touch it) | no | **VERIFIED_ABSENT** |
| 13 | #2503 — `_ROLE_REASSIGNED` regex deliberately matches literal `non-role` | #2503 (not a removal claim — a kept string with a stated reason) | n/a | n/a | n/a | **REASON_HOLDS** — lexical prose-linting heuristic over issue-body text at authoring time, never consults a role/skill catalog, never wired into runtime dispatch or authorization |

13-2=11 rows pass (VERIFIED_ABSENT or REASON_HOLDS); 2 have live survivors (item 8's adjacent finding A, and item 11 = finding B) — derived: count the verdict column above.

### Related finding A (adjacent to claim 8, not itself a #2670 claim failure)

`#2670`'s own claim — "no reader kept `CLAUDE_ROLE`, no alias, no dual-read" — is true (derived: `grep -rln "CLAUDE_ROLE" /tmp/audit-otr /tmp/audit-core | grep -v '/docs/'` → 0 hits). But applying #2626's "did the coupling move rather than disappear" test to adjacent code surfaced three live closed-set membership checks that were never claimed removed by any PR, and therefore are not themselves a #2626 claim failure, but are exactly the failure shape #2626 exists to prevent:

```python
# on-the-record/hooks/upstream-defect-scope-guard.sh:109,138-139
CHANNEL_SKILL = "upstream-defect-report"
mounted = [s for s in os.environ.get("MUSTER_SKILLS", "").split(",") if s]
channel_role_active = CHANNEL_SKILL in mounted
```
```python
# on-the-record/hooks/merge-allow-gate.sh:223-229
mounted = [s for s in os.environ.get("MUSTER_SKILLS", "").split(",") if s]
candidates = [r for r in ("secure-coding", "release-engineering") if r in mounted]
```
```python
# board.py:907-909
role == "technical-feasibility"
role == "release-engineering"
```
These trace to issue #2576 (the `MUSTER_SKILLS` migration), predate #2670, and were never "declared removed" — so they fall outside this audit's Scope list rather than falsifying an item in it. Flagged for the operator per "Open findings" below. canonical: subagent read these three files directly at /tmp/audit-otr commit 04a041ab.

### Related finding B (claim 11, genuine FAIL)

Issue #2600's slice 3 ("prompt/directive text") was claimed complete by PR #2714 (a send-back fix for PR #2712; commit `04a041ab` message: "complete role/역할 retirement (acceptance-format.md, delegation-loops.md)"). derived: `gh pr diff 2714 --name-only` shows PR #2714 touched only `.md` files. But `consult.py` builds and sends live f-string prompts directly to spawned LLM sessions at runtime, and these still say "역할" in the same "you are role X" teaching-prose category the original #2600 partition counted as in scope (143 on-the-record occurrences per its own Deliverable 1):

```python
# consult.py:1032 — canonical: subagent read live at /tmp/audit-otr commit 04a041ab
"당신은 자문(consult) 으로 불렸다 — ... 이 역할의 "
# consult.py:1414
f"역할 '{role}' 의 관할(role jurisdiction) 안에 아래 diff 요약이 "
# consult.py:1677-1686
f"당신은 판정단(panel) 판정자로 불렸다 — 다른 역할 판정자 '{peer_role}' 와 함께..."
```
Also, the same "role-scoped" phrase sits directly next to the now-renamed `$CLAUDE_SKILL` in two hooks, contradicting the rename it describes (canonical: subagent grep confirmed both lines live at 04a041ab):
```
on-the-record/hooks/role-deviation-directive.sh:46: #2348: sharded per session, role-scoped under your own $CLAUDE_SKILL) and
on-the-record/hooks/skill-verdict-guard.sh:178:        "sharded per session, role-scoped when $CLAUDE_SKILL is set; issue "
```
This is not a reshape of a removed artifact — slice 3 never claimed code-scope completeness beyond `.md` files — but the slice's own name ("prompt/directive text") is broader than what PR #2714 delivered, and its commit message's "complete ... retirement" language overclaims relative to what actually landed, the same failure pattern named in #2626's own opening example (a report to the operator that was false).

### Repeatable checker: `scripts/audit_removal_claim.py` (landed by #2627), run against real current claims and one deliberately-reshaped fixture

acceptance: `python3 scripts/audit_removal_claim.py /tmp/audit-fixtures/real-claims-otr.json --root /tmp/audit-otr` — result:
```
=== write_scope ===
verdict: RESHAPE_DETECTED
detail: removed name(s) still present live: [('write_scope', './protocol.md'), ('write_scope', './gates/ci.py'), ...]
=== spawn.ROLES / spawn_roles.json catalog ===
verdict: RESHAPE_DETECTED
detail: closed set reconstructed in: [('./consult.py', 2), ('./pipeline.py', 2), ('./spawn.py', 2)]
=== CLAUDE_ROLE env var ===
verdict: COULD_NOT_DETERMINE
detail: Q1 passed but Q2/Q3 lack member_samples to check reshape/branching -- do not read this as a pass
exit=1
```

acceptance: `python3 scripts/audit_removal_claim.py /tmp/audit-fixtures/real-claims-core.json --root /tmp/audit-core` — result:
```
=== OBSERVER_ROLES ===
verdict: RESHAPE_DETECTED
detail: removed name(s) still present live: [('OBSERVER_ROLES', './core/hooks/approval-gate.sh')]
=== ROLE_TO_KIND / PG_ROLE ===
verdict: VERIFIED_ABSENT
detail: name gone; no co-located member-set reconstruction; no live closed-set branch found
exit=1
```

This mechanical run illustrates the checker's designed conservatism, distinct from this session's own agent-based deep-read verdicts in the claim table above: the script's Q1 is a bare substring grep, so it correctly flags `write_scope` and `OBSERVER_ROLES` because those tokens still appear in **explanatory comments** in live files (e.g. `approval-gate.sh` narrates its own removal of `OBSERVER_ROLES` in a comment) — the script cannot distinguish "comment narrating a past removal" from "live reconstruction," so it reports `RESHAPE_DETECTED` and forces a human to look, rather than silently passing. My subagents read those files directly and confirmed the hits are comment-only, no live logic — the human-judgment layer the tool's own docstring requires (it never emits a bare PASS on missing data). `spawn.ROLES`/`spawn_roles.json`'s `RESHAPE_DETECTED` is a genuine tool limitation for this claim: `ROLES` and `_ROLE_SKILLS` as *member_samples* are too short/generic and co-occur incidentally in `consult.py`/`pipeline.py`/`spawn.py` for unrelated reasons (deep read: false positive, confirmed VERIFIED_ABSENT in row 5/6 above) — demonstrating why the tool is a first-pass triage aid, not a final verdict.

Deliberately-reshaped fixture, built to prove the checker catches a real reshape:
```
$ cat /tmp/audit-fixtures/reshape-demo/gates/kind_router.py
KIND_ROUTER = {
    "execution-observation": "observer",
    "conformance-review": "observer",
}
def route(kind):
    if kind in KIND_ROUTER:
        return KIND_ROUTER[kind]
    return "default"
```
acceptance: `python3 scripts/audit_removal_claim.py /tmp/audit-fixtures/reshape-claim.json --root /tmp/audit-fixtures/reshape-demo` — result:
```
=== OLD_ROLE_TABLE (deliberately-reshaped fixture) ===
verdict: RESHAPE_DETECTED
detail: removed name(s) still present live: [('OLD_ROLE_TABLE', './gates/kind_router.py')]
  q2.reshaped: true — colocated_files: [["./gates/kind_router.py", 2]]
exit=1
```
canonical: script output immediately above. The fixture's claim file declared `execution-observation`/`conformance-review` as `member_samples` of a table whose old name (`OLD_ROLE_TABLE`) was retired; the checker correctly caught both that the old identifier string survives (Q1, in a comment) and that the same two-member closed set is reconstructed under a new name/shape (`KIND_ROUTER`, Q2) in the fixture file — `RESHAPE_DETECTED`, exit code 1.

## Why

The issue's own history shows a systemic pattern: 4 of the original 4 "declared removed" claims cited in #2626 turned out to be reshapes, each passing its own review at the time. A grep for the retired name is the weakest possible check because a rename passes it trivially. This audit therefore re-derived every claim from a clean archive (never the working tree, to avoid another session's untracked debris skewing a count — per the #2527/2026-08-28-29 verification-standard finding that roughly 11 of roughly 20 "nothing changed" claims checked that way were false), applied the 3-question #2548 test to each independently, and treated no prior PASS (including this audit's own prior run) as carried forward.

## What did not work

- Attempted to file 2 follow-up GitHub issues for the genuine survivors (related findings A and B above) via `gh issue create`. Blocked by `gh-guard` (contract v3 s8/s9): "issues are the user's requirement backlog, user-authored only — no role touches them." This is the same policy issue #2503's `forbidden_action_rule.py` gate exists to enforce on the other side (issue *bodies*, not this session's own `gh` calls) — role sessions structurally cannot self-file. Reported here instead, verbatim, for the operator to file.
- The deliberately-reshaped fixture's `OLD_ROLE_TABLE` name was left in a comment (not fully removed from the fixture file), so it triggered on both Q1 and Q2 rather than Q2 alone. Left as-is since it still demonstrates a correct `RESHAPE_DETECTED` catch and time did not permit a second iteration to isolate a Q2-only trigger; noted so a future run of the fixture isn't misread as testing only the weaker Q1 grep path.

## Upstream basis

- `scripts/audit_removal_claim.py` (same-commit; landed by #2627, exercised not modified) — the repeatable checker required by this issue's third acceptance criterion.
- Prior audit records this session deliberately did NOT carry forward as PASS, re-deriving instead: `docs/issue-2626/reports/adversarial-review+implementation-audit-ee26fbd8.md` (found `AUTO_SPAWN_ROLES` reshape; derived: `grep -rn "AUTO_SPAWN_ROLES" /tmp/audit-otr --include=*.py` → 0 hits at 04a041ab, confirming #2628/PR#2640 closed it), `docs/issue-2610/reports/architecture-interface-contract-shape+silent-failure-audit-04261cd0.md` (44-entry catalog; derived: `find /tmp/audit-otr -iname "*spawn_roles*"` → 0 hits), `docs/issue-2600/reports/adversarial-review+silent-failure-audit-a402675f.md` (canonical: subagent independently re-grepped `role-deviation-directive.sh:46` and `skill-verdict-guard.sh:178` and found the same two "role-scoped under $CLAUDE_SKILL" lines still present).

## Open findings

1. **Related finding A** (claim 8 adjacent) — `on-the-record/hooks/upstream-defect-scope-guard.sh:109,138-139`, `on-the-record/hooks/merge-allow-gate.sh:223-229`, `board.py:907-909` still validate identity via `MUSTER_SKILLS`/`role` literal membership. Not a #2626 claim failure (never declared removed), but matches the failure shape #2626 exists to catch. **No follow-up issue number** — blocked by gh-guard (see "What did not work"); operator should file.
2. **Related finding B / claim 11 FAIL** — `consult.py:1032,1414,1449,1515,1677,1678,1682,1686` (live runtime LLM prompts), `on-the-record/hooks/role-deviation-directive.sh:46`, `on-the-record/hooks/skill-verdict-guard.sh:178` — issue #2600 slice 3's own name ("prompt/directive text") is broader than what PR #2714 delivered (`.md`-only). **No follow-up issue number** — same gh-guard block; operator should file.
3. Two hygiene-only side findings surfaced incidentally, not claim failures: (a) `spawn.role_data()` is called by live `on-the-record/monitors/poll-heartbeat.sh:181` and `bench/run.py:37` but no longer exists in `spawn.py` (deleted by #2610) — `poll-heartbeat.sh` silently swallows the resulting `AttributeError` (stderr to `/dev/null`), degrading its patrol-role sweep to a silent no-op; (b) `docs/specs/impact-classification.md:26,38` and `docs/specs/role-spec-template.schema.json` still describe `write_scope`/`roles/*.json` as live mechanisms — stale spec docs, not executing code.

## Next steps

None from this session — audit-only, no fixes belong in this PR per the issue's explicit "do not fix anything" instruction. The operator should file GitHub issues for open findings 1 and 2 above (this role session is structurally blocked from doing so), and separately judge the two hygiene side-findings in item 3.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; the whole audit is a structurally-independent, skeptical re-derivation of 13 removal claims from clean archives rather than trusting closing-PR titles, per the skill's protocol.
skill-verdict: silent-failure-audit — applied: invoked; used to catch two silent-failure-shaped defects surfaced incidentally — hygiene finding 3a (`poll-heartbeat.sh` swallowing an `AttributeError` via stderr-to-`/dev/null`, degrading a patrol sweep to a silent no-op) and finding B (see "Related finding B" heading above for the canonical evidence: a commit message overclaiming scope relative to what its diff actually touched, the same false-completeness-report pattern #2626 itself opens with).
other mounted skills: not triggered (work-in-english, implementation-audit, defect-verification-independence-from-upstream-verdicts — this session's task was a direct spawn brief, not a two-session audit handoff or a defect-verification-against-prior-verdict scenario).
