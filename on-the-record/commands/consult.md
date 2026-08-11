---
allowed-tools: Bash(python3:*)
description: 역할 하나에게 판단만 묻는다 — 브랜치도 커밋도 PR 도 없이, 트레이스만 남긴다
argument-hint: "<역할> \"<질문>\" [--issue <n>] — 예: coding \"이 스키마 변경이 breaking 인가\" --issue 42"
---

인자: $ARGUMENTS

`ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..` 로 두고, 아래는
`python3 $ON_THE_RECORD/spawn.py consult` 를 쓴다.

## 무엇인가

**자문(consult)** 은 역할의 룰북을 로드해 판단 하나를 돌려받는 것이다
(이슈 #699 R1) — `spawn.py <역할> "<일>" --issue <n>` 이 여는
issue → 브랜치 → 커밋 → PR 파이프라인 전체가 아니라, 질문 하나에 답 하나다.
디자인/타당성/위험/스펙 모호함 같은 **판단 지점**을 세션이 스스로 결정하는
대신 맞는 역할에 물을 때 쓴다 — 결과가 저장소를 바꾸지 않는 한 PR 사이클은
필요 없다. 결과가 저장소를 바꿔야 한다면 그건 자문이 아니라 배달물이고,
`spawn.py <역할> ... --issue <n>` 로 간다.

## 어떻게 부르나

```
python3 $ON_THE_RECORD/spawn.py consult <역할> "<질문>" [--issue <n>] [-C <레포>]
```

- `<역할>`: `spawn.py` 가 아는 역할 이름 (인자 없이 `spawn.py` 를 부르면 목록이 뜬다).
- `<질문>`: 판단이 필요한 질문 하나. 여러 판단이 필요하면 여러 번 부른다 —
  한 번의 자문은 한 판단이다.
- `--issue <n>`: 이 판단이 특정 이슈에 속하면 붙인다. 트레이스 파일이
  `docs/issue-<n>/reports/consult-log.md` 로 간다 — 빠지면
  `docs/reports/consult-log.md`.

## 무엇이 돌아오나

stdout 에 JSON 객체 하나:

```json
{"answer": "...", "confidence": "low|medium|high", "caveats": ["..."]}
```

## 트레이스 (예외 없음)

성공이든 실패든(타임아웃, 파싱 실패, 세션 크래시) **매번** 한 줄이
트레이스 파일에 append 된다 — "traceless consult 없음"은 운영자 결정이다.
실패해도 자문을 다시 시도하기 전에, 트레이스 파일을 읽어 이전 시도가
무엇으로 실패했는지 확인하라.

## 무엇을 하지 않나

- 브랜치를 만들지 않는다, 커밋하지 않는다, PR 을 열지 않는다.
- 보드(`docs/issue-<n>/reports/<역할>.md`)에 아무것도 쓰지 않는다 — 자문은
  배달 기록이 아니다.
- `spawn.py <역할> ... --issue <n>` 의 워처/roster 등록/재스폰 기계장치를
  전혀 거치지 않는다 — 세션 하나 돌고, 답 하나 돌아오고, 끝난다.

바운드된 헤드리스 실행이라 오래 걸리지 않는다(기본 상한 180초) — 결과를
기다려도 된다, `spawn.py <역할> ... --issue <n>` 처럼 백그라운드로 돌릴
필요 없다.
