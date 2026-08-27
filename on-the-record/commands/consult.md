---
allowed-tools: Bash(python3:*)
description: 역할 하나에게 판단만 묻는다 — 브랜치도 커밋도 PR 도 없이, 트레이스만 남긴다
argument-hint: "<역할> \"<질문>\" [--issue <n>] — 예: coding \"이 스키마 변경이 breaking 인가\" --issue 42"
design-rationale: 판단 지점마다 스폰 전체 파이프라인(브랜치→커밋→PR)을 여는 비용을 치르면 세션이 스스로 판단을 내려버리는 유인이 생긴다 — consult 는 룰북 로딩만 재사용하고 배달 기계장치는 전부 건너뛰어 그 비용을 없앤다. 이슈 #1202 로 ideate/draft/review 를 같은 트랜스포트 위 형제 verb 로 얹은 이유: 판단(consult) 뿐 아니라 발산/초안/검토도 똑같이 "저장소를 안 바꾸는 도움"이라 같은 무브랜치/무커밋/무PR 계약과 같은 트레이스 파일을 그대로 쓰는 편이, 사본 코드경로를 새로 만들어 드리프트를 내는 것보다 낫다.
---

인자: $ARGUMENTS

`ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..` 로 두고, 아래는
`python3 $ON_THE_RECORD/spawn.py consult` 를 쓴다.

## 무엇인가

**자문(consult)** 은 역할의 룰북을 로드해 판단 하나를 돌려받는 것이다
(이슈 #699 R1) — `spawn.py --skills <skill>[,<skill>...] "<일>" --issue <n>`
(이슈 #2572: 유일한 스폰 형태)가 여는 issue → 브랜치 → 커밋 → PR 파이프라인
전체가 아니라, 질문 하나에 답 하나다. 디자인/타당성/위험/스펙 모호함 같은
**판단 지점**을 세션이 스스로 결정하는 대신 맞는 역할에 물을 때 쓴다 —
결과가 저장소를 바꾸지 않는 한 PR 사이클은 필요 없다. 결과가 저장소를
바꿔야 한다면 그건 자문이 아니라 배달물이고, `spawn.py --skills <skill>
... --issue <n>` 로 간다.

## 어떻게 부르나

```
python3 $ON_THE_RECORD/spawn.py consult <역할> "<질문>" [--issue <n>] [-C <레포>] [--foreground]
```

- `<역할>`: `spawn.py` 가 아는 역할 이름 (인자 없이 `spawn.py` 를 부르면 목록이 뜬다).
- `<질문>`: 판단이 필요한 질문 하나. 여러 판단이 필요하면 여러 번 부른다 —
  한 번의 자문은 한 판단이다.
- `--issue <n>`: 이 판단이 특정 이슈에 속하면 붙인다. 트레이스는
  `docs/issue-<n>/reports/consult-log/<session-ts-pid>.md` 로 간다 — 빠지면
  `docs/reports/consult-log/<session-ts-pid>.md` (이슈 #2333: 세션마다
  다른 샤드 파일이라 동시 자문끼리 절대 같은 경로를 두고 다투지 않는다 —
  예전 단일 파일은 동시 세션마다 100% 예측 가능한 git merge 충돌이었다).
  오늘까지의 단일-파일 뷰가 필요하면
  `spawn.py consult-log --issue <n> [-C <레포>]` 로 모든 샤드를
  시간순으로 이어 붙인 텍스트를 본다.
- `--foreground`: 이슈 #2569 이전의 동작으로 되돌린다 — 아래 "무엇이
  돌아오나" 참고. 스크립트/테스트처럼 판단 JSON 을 그 자리에서 바로
  파싱해 써야 할 때만 켠다.

## 무엇이 돌아오나

**기본(이슈 #2569)은 배경 실행이다.** cross-family 스킬 매치(BM25 +
skill_judge 자문)와 실제 자문 세션 실행을 합치면 실측 43-78s+ 걸릴 수
있다 — 호출자 프로세스 안에서 그대로 기다리면 대화형 세션 하나를 그만큼
얼린다. `spawn.py --skills <skill> ... --issue <n>` 이 세션을 detach 하고
즉시 리턴하는 것과 같은 패턴(`os.fork()`)으로, 이 커맨드도 즉시 리턴한다:

```
[consult] 배경에서 돈다(pid <pid>) — 판단은 자문 트레이스에 커밋된다:
`spawn.py consult-log[--issue <n>]` 로 확인. 단계별 타이밍/원시 출력: <log>
```

판단 JSON 자체는 스킬 매치를 포함해 자문이 끝난 뒤 위 트레이스에
커밋된다(아래 "트레이스" 절) — 곧바로 stdout 에서 읽을 수 없다. `<log>`
경로에는 매 실행마다 단계별 소요시간(`skill_match`/`session_run`)과
`muster_skills`(이번 자문에 실제로 마운트된 스킬 이름들 — 스킬 매치가
그대로 유지됐는지 확인할 지점)도 함께 남는다.

`--foreground` 를 주면 예전처럼 호출자 프로세스 안에서 끝까지 기다려
stdout 에 JSON 객체 하나를 그대로 찍는다:

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
- `spawn.py --skills <skill> ... --issue <n>` 의 워처/roster 등록/재스폰
  기계장치를 전혀 거치지 않는다 — 세션 하나 돌고, 답 하나 돌아오고, 끝난다.

자문 세션 자체는 바운드된 헤드리스 실행이다(기본 상한 180초) — 하지만
그 실행 앞에 붙는 cross-family 스킬 매치(skill_judge 자문)가 실측
43-78s+ 걸릴 수 있어(이슈 #2569, `bootstrap_timing` 의 `cross_family`
구간과 같은 원인), 매치+세션 합계는 180초 상한과 별개로 대화형
호출자에게 1-3분짜리 정지로 보였다. 그래서 이제 기본은 위 "무엇이
돌아오나" 절의 배경 실행이다 — `spawn.py --skills <skill> ... --issue <n>`
처럼 호출자는 즉시 리턴받고, 판단은 트레이스에 커밋된 뒤 확인한다.
