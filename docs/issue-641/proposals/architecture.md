---
status: proposed
files:
  - docs/issue-641/reports/architecture/survey.md
  - docs/issue-641/proposals/architecture.md
---

# Proposal — issue #641: review-is-role-work boundary (architecture, phase 1)

Phase 1 only: boundary design and detectability verdict, no code. Grounded in
`docs/issue-641/reports/architecture/survey.md`.

**Scout skip record**: scouting skipped this phase. Reason: this is an internal
orchestration-protocol boundary with no external product category to benchmark against —
the issue's own requirement fixes the design space to reusing this repo's already-shipped
machinery (`conformance-review`, the axis panel, `open_decision_item`, `delegated-judgment-gate.sh`),
not selecting among external patterns. Same skip class as `docs/issue-609/proposals/architecture.md`'s
precedent (extending an already-scouted internal mechanism, not surveying a new field).

## 1. The run.md contract addition

**Where**: `on-the-record/commands/run.md` step 6 ("PR 을 설명한다"), immediately after the
2단계 머지 sub-bullet (current line ~109) and before "모든 승인/머지 요청은 최소한..." (line
110). This is the exact point where the instruction to summarize a diff is stated — the
boundary has to sit right next to the instruction it bounds, or it will be read as an
unrelated aside (the failure mode the issue root-caused: nothing near the summarize
instruction currently forbids sliding into review).

**New subsection, `**경계 — 요약과 리뷰는 다른 일이다 (이슈-641).**`**:

- 오케스트레이터가 위에서 하는 일은 **결정 지원 요약**이다: 무엇이 바뀌었는지, 왜
  바뀌었는지, 어떻게 검증됐다고 역할이 기록했는지를 사람의 승인/머지 결정을 위해
  자연어로 옮기는 것. 이것은 정당한 오케스트레이터 업무다.
- **산출물에 대한 리뷰/피드백 — 지적 사항, 문제점, 수정 요구 — 을 만들어내는 것은
  오케스트레이터의 산문이 아니라 역할의 산출물이다.** 명세 대비 정합성 검토가
  필요하면 `conformance-review` 역할을 스폰해 그 역할의 기록
  (`docs/issue-<n>/reports/conformance-review.md`)을 받아 relay 한다. 방법론적 판단
  (유지보수 복잡도/외부 부담/공격 표면/성능/정합성 등)이 걸린 리뷰가 필요하면, 새로
  발명하지 않고 이미 배선된 축 패널(`_JUDGMENT_AXES`, 각 축의 소유 역할,
  `open_decision_item` 트리아지)을 통해 관련 역할(들)을 스폰하고 **그들이 기록한
  판정**을 relay 한다.
- **테스트**: 지금 쓰려는 문장이 "역할의 기록/PR에 이미 있는 내용을 사람이 읽기 쉽게
  옮기는 것"인가, 아니면 "역할의 기록에 없는 새 지적/판정을 오케스트레이터가 만들어
  내는 것"인가. 후자면 절차 위반이다 — 관련 역할을 먼저 스폰해서 그 역할이 지적하게
  하라.
- 이 경계는 위 1단계/2단계 요약 의무(무엇을/왜/어떻게 검증됐는가)를 없애지 않는다 —
  그 요약은 여전히 오케스트레이터의 몫이고, 리뷰 생성과는 별개의, 구조적으로 구분되는
  축이다 (114-116행의 flow/stage/next가 네 항목을 대신하지 않는 것과 같은 모양).

**Spec-index**: this text edit lands in phase 2 (the actual run.md diff); `docs/specs/reconciled-index.md`
regeneration (`python3 gates/spec_index.py --update`) is phase-2 work, tracked here as an
open item so it is not silently dropped when phase 2 executes.

## 2. Detectability verdict

**Verdict: partially detectable, advisory only — extend `delegated-judgment-gate.sh`,
fail-open, narrow trigger vocabulary.**

**What's detectable**: the hook is already a PreToolUse/Bash hook that inspects
orchestrator-issued `gh` commands before they run (survey, "shipped machinery" section). A
sixth-ish firing condition, symmetric to #597's addition, can add a case arm for
`gh pr comment` / `gh issue comment` in an orchestrator session and inspect the comment
body text before it posts.

**What's not detectable, honestly stated**: whether prose is "genuinely relayed from a
role's record" vs. "authored fresh by the orchestrator" cannot be determined from the
comment text alone — the hook has no access to session provenance (which agent produced
which sentence). It can only check a *proxy*: does the comment contain review-verdict-
shaped language, and if so, does it also cite a role-record path
(`docs/issue-<n>/reports/(conformance-review|<owning-role>).md`) or that role's own PR? A
comment that paraphrases a real role finding without including the citation string still
counts as "no citation found" under this proxy — a false positive that isn't gameable in
the adversarial sense but that the design has to accept as a cost.

**Trigger vocabulary — kept deliberately narrow to avoid the #320 collision (survey,
"constraint" section)**: match on `conformance-review`'s own produces-vocabulary used as a
verdict (`Present|Surface|Absent|Incorrect|Unverifiable`, or the axis panel's
`supports|contradicts|no-opinion`) OR explicit Korean review-verdict markers (`리뷰 결과`,
`검토 결과`, `지적 사항`, `수정 필요`) — never on `#320`'s mandated problem/cost/possible/
remaining framing words (문제/비용/가능) alone, which run.md already requires in every
PR/board summary and would false-positive on every compliant turn.

**Gaming-resistance stated plainly**: this is lexical matching, not semantic
understanding. An orchestrator that phrases a self-authored critique to avoid the trigger
vocabulary (e.g. avoiding `Absent`/`Incorrect`/`지적 사항` while still delivering the same
critique in other words) is not caught. This is the same class of limit `claim_scan.py`
already accepts for its own claim-word list (survey) — stated as a known gap, not solved
here, matching this repo's existing posture of accepting narrow-but-honest lexical checks
over unbuilt semantic ones.

**False-positive posture**: fail-open, comment-only, same as `delegated-judgment-gate.sh`'s
existing six firing conditions — the hook never blocks `gh pr comment`; on a lexical hit
with no citation, it posts its own audit comment flagging the gap for the operator to see,
exactly like its existing audit-trail behavior for other firing conditions. This keeps a
false positive cheap (an extra comment, correctable by the operator) rather than blocking,
given the proxy's known imprecision above.

## Open items (phase 2 scope, not decided here)

- Exact case-arm code for `gh pr comment`/`gh issue comment` detection inside
  `delegated-judgment-gate.sh`'s existing heredoc, plus its own test file
  (`on-the-record/hooks/test_delegated_judgment_gate.py` already covers the other five
  conditions — a sixth belongs there).
- `docs/specs/reconciled-index.md` regeneration once run.md's phase-2 diff lands.
- Whether the citation format should be a strict path regex or accept a bare PR link —
  left to implementation given the shape is a text-matching heuristic either way.
