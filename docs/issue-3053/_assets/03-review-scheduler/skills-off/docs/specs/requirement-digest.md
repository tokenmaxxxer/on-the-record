# Requirement Digest

이 레포가 향하는 살아있는 요구사항 목록. 요구 연결 게이트(issue #1017)는
새로 드래프트되는 이슈 본문이 아래 형식의 R-ID를 인용하기를 기대한다.

## R-entry format

각 항목은 반드시 한 줄이다(줄바꿈 없음) — 그 안의 <설명> 과 <출처>는
여러 절로 이루어진 자유 형식 텍스트여도 된다(issue #2077). 정확한
문법(파서 — `spawn.py::requirement_drift` — 가 그대로 받아들이는 형태):

  - R<n>: <설명, 자유 형식> [<status>] (source: <출처, 자유 형식>)

<설명>과 <출처>는 쉼표·세미콜론·마침표를 포함한 여러 절이어도 되고,
<출처>는 `#<issue-number>` 로 국한되지 않는다 — "user directive
2026-08-23, issue #1" 처럼 issue 번호를 포함하지 않는 자유 텍스트도
허용된다. `[<status>]` 는 공백 없는 단일 토큰이어야 한다.

예(한 줄 설명):
  - R1: 사용자가 X 를 할 수 있어야 한다 [enforced] (source: #12)

예(문서화된 자유 형식 — multi-clause, 자유 형식 source):
  - R1: A browser-playable character-growth RPG whose progression systems benchmark Random Dice 2 — deterministic no-gacha Dice-Tree acquisition, in-match merge 1→7 pips with 7-pip Awakening, Supporter-analog companions [live] (source: user directive 2026-08-23, issue #1)

## Entries

- R1: 대학생이 강의자료나 교재를 읽고 이해하지 못할 때, 자신이 정확히 무엇을 이해하지 못하는지 특정하지 못하는 상태(이해격차)를 AI 기반 서비스로 완화한다 — 이 요구는 아직 검증 대상이며, 실재성·미충족 여부가 조사로 확인되기 전까지 확정이 아니다 [proposed] (source: user directive 2026-09-02, issue #1; discovery PR #2 evidences the broad monitoring failure at behavioral/Fact tier — metacomprehension correlation .24-.27 across 94 studies, Kruger-Dunning 12th-vs-62nd percentile — but does NOT evidence the narrow 'cannot articulate which part' clause, which rests on one unverified secondary source and is the first thing a real interview round must test; a ~500-student RCT and a first-person account also show at least one existing AI tutor already serving a slice of this job, which is evidence against 'underserved' in the strong sense)

