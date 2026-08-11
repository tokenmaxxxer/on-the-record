# Scout brief — issue #741

이 작업은 제품이 아니라 저장소 내부 CI 자동화 규약(broker-attach)이라
외부에 직접 대응하는 제품 카테고리가 없다. 두 각도로 한 라운드만
돌렸다: (1) GitHub 커뮤니티가 "다단계 PR 이 이슈를 조기 종결시키는"
동일 클래스 문제를 어떻게 다루는지, (2) diff 내용으로 "이 PR 이 코드
변경인가 문서뿐인가"를 판별하는 기존 관행.

## Must-be 1 — closing 키워드는 최종/전달 PR 에만 붙인다

GitHub 자체는 "링크된 PR 중 closing 키워드를 가진 PR 이 머지되면 그
즉시" 이슈를 닫는다 — 다단계 작업 도중 하나가 먼저 머지돼도 예외가
없다. 커뮤니티가 이미 여러 차례 네이티브 옵트아웃을 요청했지만
구현되지 않았고, 실제로 쓰이는 유일한 우회는 "중간 PR 에서는 closing
키워드를 아예 빼고, 마지막 PR 에만 붙인다"는 수동 규율이다.
`contract-guard.sh` 의 broker-attach 가 대신하려는 일이 바로 이
"마지막/전달 PR 에만 붙이기" 판정이므로, #741 이 요구하는 것은 이
알려진 문제의 자동화 버전이다 — 새로운 문제가 아니라 잘 알려진 문제의
새로운 인스턴스.

## Must-be 2 — "코드 변경인가"는 self-report 가 아니라 diff 로 판별한다

CI 생태계에서 "이 PR 이 문서뿐인가 코드인가"를 가리는 표준 패턴은 변경된
파일 경로를 glob 으로 매칭하는 것이다(`dorny/paths-filter`,
`check-for-changed-files` 류 GitHub Action 이 전형) — PR 본문 텍스트나
라벨 self-declaration 이 아니라 실제 diff 의 경로 목록을 진실로 삼는다.
이 패턴은 이 저장소 안에서 이미 쓰이는 신호(`approval-gate.sh` 의
`is_record`/`is_src_test` 경로 매칭, survey.md 참고)와 정확히 같은
모양이다 — 외부 관행과 내부 기존 코드가 같은 방향을 가리킨다.

## Adopt / Skip

- **Adopt**: diff 파일 경로 기반 판별(경로 glob/regex 매칭) — 외부
  생태계에서 표준, 내부에도 이미 한 곳(`approval-gate.sh`)에 있다.
- **Skip**: PR 본문/라벨의 self-declaration 을 진실 신호로 쓰는 것 —
  외부에서도 "라벨을 CI 가 강제하지 않으면 사람이 깜빡한다"는 불평이
  따라오고, 이 저장소 자체의 #476 원칙(재실행/독립 신호가 self-report
  보다 우선)과도 맞지 않는다(survey.md, gates 조사 참고).

## Gap line

이 저장소의 현재 상태가 이미 충족하는 must-be: 2(diff 경로 판별 패턴) —
`approval-gate.sh` 에 이미 존재. 아직 충족하지 않는 곳:
`contract-guard.sh` 의 merge 시점 판정에는 이 패턴이 없다 — 시간만
본다. 이 gap 이 제안서의 "What will be done" 대상이다.

## 진행 방식

1 라운드 웹서치(앵글 2개, 병렬 tool call) 후 판단 1회로 종료 — 두 결과
모두 이미 확보한 내부 판단(diff 내용 기반 판별을 쓰고, self-report 는
쓰지 않는다)을 뒤집지 않아 추가 라운드가 결정을 바꾸지 않는다고 판단.

## Sources

- https://github.com/orgs/community/discussions/23476
- https://github.com/orgs/community/discussions/66741
- https://github.com/orgs/community/discussions/17308
- https://github.com/RasaHQ/pr-changed-files-filter
- https://github.com/brettcannon/check-for-changed-files
- https://github.com/marketplace/actions/verify-changed-files
