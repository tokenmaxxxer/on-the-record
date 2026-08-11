---
status: proposed
files:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - docs/issue-741/reports/implementation/survey.md
  - docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md
  - docs/issue-741/reports/implementation/hunt-2026-08-11-execution-provenance-and-phase1-closes-refusal.md
---

## Request

issue #741 의 landed 수정(PR #756, `contract-guard.sh` 의 `is_src_test`/
`is_record` 내용 게이트)이 실환경에서 두 번 반증됐다(이슈 코멘트
2026-08-11T05:55:34Z). 재조사가 답해야 하는 두 가지:

(a) 머지 시점에 실제로 실행된 훅 파일의 절대 경로와 그 내용의 버전을
    실행 중에 기록으로 남기는 수단을 만든다 — 다음 머지부터는 추정이
    아니라 실측으로 확인 가능해야 한다.
(b) 저자가 phase-1 PR 본문에 직접 쓴 `Closes #n` 을 어떻게 다룰지 —
    제거·거부·허용 중 무엇인지, 근거와 함께.

Scout: skip — 순수 버그픽스 조건. (a)는 이 저장소의 다른 훅에 이미 있는
로그·마커 관측성 패턴의 연장이며 외부 제품 카테고리와 비교할 대상이
아니다. (b)는 `gates/ci.py::_phase1_mismatch` 로 이미 설계·구현·테스트가
끝난 로직을 살아있는 실행 경로에 잇는 것뿐, 새 설계 결정이 아니다(근거는
아래 Rationale).

## Constraints

- `contract-guard.sh` 의 기존 phase2/`is_src_test`/`is_record` 판정과
  broker-attach 로직은 결과가 한 비트도 바뀌면 안 된다 — 기존 17개
  유닛테스트가 회귀 기준.
- 로그 기록 자체가 절대 머지 판정을 바꾸거나 새로운 거부 경로가 되면
  안 된다 — 기록 I/O 실패는 항상 무시하고 지나간다(이 파일 헤더가 이미
  선언한 fail-open 철학과 동일).
- `pr-preflight.sh` 쪽 수정은 `check_body`(그리고 그 원본
  `gates/pr_reference.py` 의 `check_body`)의 기존 계약을 바꾸지 않는다 —
  `tests/test_gates.py` 의 `t_pr_reference_phase1_does_not_gate_closing_keywords_itself`
  가 이미 `check_body(126, "Closes #126", "phase1") == []` 를 회귀
  기준으로 핀 처리하고 있다.
- 새 외부 의존성 없음 — 두 훅 모두 zero-install 철학(콘슈머 저장소에
  `gates/` 체크아웃을 가정하지 않음)을 유지, 표준 라이브러리만 사용
  (`hashlib`, `json`, `os`, `datetime`).
- `gates/ci.py`/`gates/pr_reference.py` 자체는 건드리지 않는다 — 그 쪽의
  `_phase1_mismatch` 로직은 이미 옳고, 부족한 건 그것을 부르는 살아있는
  실행 경로일 뿐.
- Claude Code 플러그인 로더의 설치 캐시 갱신 메커니즘 자체(왜/언제
  `${CLAUDE_PLUGIN_ROOT}` 가 오래된 사본을 가리키는가)는 이 저장소가
  제어하지 않는 외부 도구다 — 그걸 고치는 게 아니라 그 불일치를
  실행 중에 관측 가능하게 만드는 것까지가 이 제안의 범위.

## Rationale

**(a) 실행 시점 관측 수단.** Alternative considered and rejected:
`self-update.sh`(SessionStart 훅)가 체크아웃뿐 아니라
`${CLAUDE_PLUGIN_ROOT}` 설치 캐시 자체도 강제로 재설치하도록 확장하는
안. Rejected — 이유 둘: (1) `self-update.sh` 자신의 주석이 이미
"`claude plugin update` 는 버전 문자열만 읽고 영원히 'already latest'
라고 보고한다"고 문서화하고 있다 — 그 명령을 다시 부른다고 캐시가
갱신된다는 보장이 없다(실측으로 확인된 함정을 다시 밟는 것). (2) 플러그인
설치 캐시(`~/.claude/plugins/cache/...`)를 훅 스크립트가 스스로 덮어쓰는
것은 이 저장소가 소유하지 않는 Claude Code 자체의 상태를 훅 실행 중에
변경하는 일이라 블라스트 반경이 크고, 이번 요청의 우선순위("추정으로
결론내지 말고 실측 가능하게 만드는 것이 1순위")와도 어긋난다 — 지금
필요한 건 갱신 메커니즘을 고치는 게 아니라 불일치를 눈에 보이게 만드는
것이다. Chosen instead: `contract-guard.sh` 자신이 매 `gh pr merge`
판정마다 자기 자신의 절대 경로와 sha256 을 로그에 남긴다 — 순수 관측,
부작용 없음.

**(b) `pr-preflight.sh` 에 검사 추가.** 두 대안을 검토하고 모두
rejected. 첫째, "허용"은 계약 위반이다(role-handoff contract v3 s19:
"Merging a phase-1 PR must not auto-close the issue"). 둘째, "check_body
안에서 조용히 제거(본문을 고쳐 씀)"는 rejected — 이 저장소의 두 훅
(`contract-guard.sh`, `pr-preflight.sh`)이 이미 쓰고 있는 설계와
어긋난다: `contract-guard.sh` 의 broker-attach 는 phase-2 인도 PR 에
"빠진 의무"를 채워 넣는 교정적 조작인 반면, `pr-preflight.sh` 는 언제나
deny-before-effect 만 하고 본문을 스스로 고쳐 쓴 적이 없다(이 파일 자신의
헤더: "The only path that exits 2 is a positive, evidence-backed
determination... Denied before the merge/create/edit executes"). 저자가
금지된 키워드를 스스로 쓴 경우를 조용히 지우면 같은 실수를 반복하지
않게 가르치는 대신 숨기는 셈이고, PR 이 아직 존재하지 않는 `gh pr
create` 시점에 거부하는 쪽이 교정 비용도 가장 싸다(이미 파일에 없다,
다시 시도하면 그만) — deny instead of silent strip.

`check_body` 자체를 고쳐서 phase1 분기에 Closes 검사를 넣는 안도 검토
했으나 rejected — `tests/test_gates.py` 의
`t_pr_reference_phase1_does_not_gate_closing_keywords_itself` 가 정확히
반대(phase1+Closes 는 `check_body` 를 통과해야 한다)를 핀 처리하며, 그
주석이 "책임은 `gates/ci.py::_phase1_mismatch` 에 있다"고 명시한다 —
`check_body`(issue #228 소유)와 `_phase1_mismatch`(issue #245/#271 대에
따로 만들어진, 본문·제목·커밋 메시지 세 표면을 보는 별도 함수)는 이미
의도적으로 분리된 책임이다. `check_body` 를 고치면 이 핀 테스트가
깨지고 #228 이 그은 소유 경계를 넘는다. `_phase1_mismatch` 자체는 이미
맞는 로직으로 존재하지만, 그걸 부르던 유일한 실행 경로(`gates/ci.py`
의 `main()`, GitHub Actions 러너)가 issue #460 으로 없어졌고,
issue #512 가 그렇게 죽은 체크들을 하나씩 zero-install 훅으로 이식하는
진행 중인 작업인데(`accumulation-claim-guard.sh`,
`call-shape-guard.sh` 가 이미 그 패턴), `pr-preflight.sh` 는 아직
`_phase1_mismatch` 를 이식하지 않았다(자기 헤더에 `check_body`/
`_plan_from_body` 만 포팅했다고 명시). Chosen instead of both rejected
alternatives: 이 이미 진행 중인 패턴을 그대로 한 항목 더 잇는 것 — 새
아키텍처가 아니라 알려진 구멍을 메우는 것이다.

## What will be done

**contract-guard.sh:**
- bash 래퍼에서 자기 자신의 정규화된 절대 경로를 `self-update.sh` 가 쓰는
  것과 같은 관용구로 계산해(`cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
  -P`) `CG_SELF_PATH` 환경변수로 내보내고, 기존 `CG_PAYLOAD` 와 함께
  파이썬 블록에 전달한다.
- 파이썬 블록에서 `pr_data` 를 성공적으로 읽은 직후(현재
  `if pr_data is None: sys.exit(0)` 바로 다음), `files`/`is_src_test`/
  `role`/`is_record` 계산 블록(현재 phase2 게이트보다 뒤에 있음)을 그
  앞으로 옮겨 phase2 값과 무관하게 항상 계산되게 한다 — 게이트 자체의
  조건문·분기 결과는 그대로 두고 계산 순서만 앞당긴다.
- `phase2`/`is_src_test`/`is_record` 가 모두 계산된 직후, 기존 두 게이트
  (`if not phase2`, `if not (is_src_test or is_record)`) 를 적용하기
  전에 한 번, `CONTRACT_GUARD_PROVENANCE_LOG` 환경변수(기본값
  `~/.claude/on-the-record/hook-provenance.log`)에 JSON 한 줄을
  append 한다: `ts`(UTC ISO8601), `script_path`(`CG_SELF_PATH`),
  `script_sha256`(그 파일을 읽어 `hashlib.sha256` 로 계산), `pr`,
  `repo`(`target_repo_flag` 또는 null), `issue`, `phase2`,
  `is_src_test`, `is_record`, `closes_present_before`(`bool(closes_m)`).
  전체를 `try/except Exception: pass` 로 감싼다(디렉터리 생성 포함) —
  기록 실패가 절대 머지 판정에 영향을 주지 않는다.

**test_contract_guard.py:**
- 새 테스트: `CONTRACT_GUARD_PROVENANCE_LOG` 를 `tmp_path` 아래로
  가리키고 기존 PR #747/#739 모양 픽스처(문서만, 같은 라운드 승인)를
  돌린 뒤, 로그 파일에 줄이 하나 생겼는지, 그 `script_path` 가 실행된
  `contract-guard.sh` 자신의 경로와 일치하는지, `script_sha256` 이
  그 파일을 직접 읽어 계산한 sha256 과 같은지, `phase2=true`,
  `is_src_test=false`, `is_record=false` 가 기록됐는지 단언한다.
- 회귀 테스트: 로그 디렉터리를 쓸 수 없는 경로(예: 존재하지 않는
  상위 경로에 쓰기 권한 없음을 흉내)로 가리켜도 `returncode`/
  `gh pr edit` 호출 여부는 로그를 정상 기록했을 때와 동일함을 단언한다
  (로그 실패가 판정에 영향을 주지 않음의 직접 증거).

**pr-preflight.sh:**
- `bad = check_body(issue, body, phase, plan)` 호출 직후, `phase ==
  "phase1"` 이고 `not bad` 일 때만, 자기 이슈를 가리키는 closing 키워드가
  본문에 있는지 찾는다 — 기존 `_CLOSES_REF`(이 파일 224번째 줄에 이미
  정의됨, 새 정규식 아님)를 그대로 재사용하되, 이 파일의 기존 두 호출부
  (236/241번째 줄)가 쓰는 `.search()`(첫 매치 하나만) 가 아니라
  `.finditer()`(전체 매치를 순회하며 `int(m.group(2)) == issue` 인
  것을 찾음)를 쓴다 — `gates/ci.py::_closes_ref_for_issue`(164-177번째
  줄)와 정확히 같은 의미론. `.search()` 를 그대로 옮기면 본문이 다른
  이슈를 먼저 언급할 때("Fixes #999, ... Closes #743") 첫 매치(#999)에서
  멈춰 뒤쪽의 진짜 `Closes #743` 을 놓친다 — `_closes_ref_for_issue` 자신의
  주석이 이 정확한 회피를 hunt 로 실측 확인했다고 명시하는 이유이자,
  after-proposal 워런트 헌트(stance 0, `docs/issue-741/reports/
  implementation/hunt-2026-08-11-execution-provenance-and-phase1-closes-refusal.md`)
  가 이 제안의 초안 문구("기존 _CLOSES_REF 로... 찾는다")를 그대로
  구현하면 같은 회피를 재도입한다고 확인해 이 문단에 반영한 것. 매치를
  찾으면 `deny()` 로 거부한다(메시지는 `gates/ci.py::_phase1_mismatch`
  가 쓰는 문구와 같은 취지: "phase-1 제안 PR 본문에 closing 키워드(...)가
  있다 — phase-1 머지가 이슈를 자동으로 닫으면 안 된다"). `check_body`
  자신의 코드는 한 줄도 바꾸지 않는다.
- 범위는 본문 표면 하나로 한정한다 — 이 훅이 지금도 커맨드라인에서
  `--body`/`--body-file` 만 추출하고 제목·커밋 메시지는 다루지 않기
  때문(아래 Out of scope).

**test_pr_preflight.py:**
- PR #763 실물 모양의 새 케이스: phase1, 본문이 평문 `#743` 참조와
  `Closes #743` 를 둘 다 담고 있으면 새 검사가 거부해야 한다.
- decoy-참조 케이스(위 hunt finding 을 핀 처리): phase1, 본문이
  `"Fixes #999, unrelated context. Closes #743"` 처럼 자기 이슈가 아닌
  closing 키워드를 먼저 담고 있어도, 뒤쪽의 진짜 `Closes #743` 을
  `.finditer()` 로 찾아내 거부해야 한다 — `.search()` 로 구현했다면
  놓쳤을 케이스를 정확히 겨냥.
- 회귀: 기존 "phase1 plain #459 reference -> allowed"(Closes 없음)는
  그대로 통과.
- 회귀: `check_body(126, "Closes #126", "phase1") == []` 자체는 바뀌지
  않는다 — 새 검사가 `check_body` 밖에 별도로 존재함을 이 케이스로
  고정한다.

## Accumulation

이 변경은 두 개의 반복 패턴에 한 항목씩 더한다.

`pr-preflight.sh` 쪽은 issue #512 포팅 패턴을 그대로 반복한다:
`gates/ci.py::_phase1_mismatch` 로직을 훅의 인라인 파이썬에 복제하고,
`test_pr_preflight.py` 에 같은 순수-파이썬 사본을 또 하나 둔다 —
`accumulation-claim-guard.sh`/`call-shape-guard.sh` 가 이미 쓰고 있는
것과 같은 3중 사본(정본 `gates/`, 훅 인라인 사본, 훅 테스트 사본)
구조다. 이 구조가 N번 더 반복되면(issue #512 가 다룰 다음 죽은 체크마다)
zero-install 훅 디렉터리에 같은 모양의 사본이 하나씩 늘어난다 — 파일
수는 선형으로 늘지만 각 사본은 독립적으로 존재하고 서로를 호출하지
않으므로 결합도는 늘지 않는다. 한 훅(`pr-preflight.sh`) 안에 이런
독립 검사가 세 개를 넘어서면, 그 훅을 `gates/` 위임형(로컬 `gates/`
체크아웃이 있으면 import, 없으면 지금의 인라인 폴백)으로 리팩터링하는
게 다음 단계이지, 이 제안의 메커니즘을 다시 쓰는 게 아니다.

`contract-guard.sh` 쪽은 이미 있는 `gh_json` 헬퍼 + 한 번의 `gh pr edit`
호출에 로그 append 호출 하나를 더한다 — 이 파일 안에서 "판정에 곁들여
부작용을 하나 더 실행한다"는 모양이 N번 더 반복되면(예: 다른 판정
필드도 로그에 남기고 싶어지는 경우), 그때 각 호출부에 반복되는
try/except 상용구를 이 파일 안의 작은 `_log_provenance()` 헬퍼 하나로
묶는 것이 다음 단계다 — 새 파일을 만들거나 zero-install 원칙을 깨지
않는다.

## Out of scope

- Claude Code 플러그인 설치 캐시가 갱신되지 않는 근본 메커니즘을 고치는
  것 — 이 저장소가 제어하지 않는 외부 도구(Claude Code 자체)의 동작.
- `pr-preflight.sh` 의 새 검사를 제목·커밋 메시지 표면까지 넓히는 것
  (`_phase1_surface_mismatch` 가 `gates/ci.py` 안에서는 이미 하고
  있음) — 이 훅이 지금 본문만 다루는 기존 범위를 그대로 유지, 넓히는
  건 별도 이슈.
- 이미 조기 종결된 이슈(#729, #741, #743, #745, #742, #744, #759,
  #760)를 되살리는 보드 복구 작업 — 오케스트레이터의 일이지 이 롤의
  일이 아니다.
- `contract-guard.sh` 와 `pr-preflight.sh` 의 phase 판정 신호 이중화
  통합 — issue #653 ADR 과 지난 라운드 제안서가 이미 범위 밖으로
  명시했고, 이번 재조사도 그 경계를 재검토할 근거를 찾지 못했다.

## How you'll know it worked

- `python3 -m pytest on-the-record/hooks/test_contract_guard.py on-the-record/hooks/test_pr_preflight.py -v` —
  기존 케이스 전부 그린 + 새 provenance-log 테스트(로그 줄의
  `script_path`/`script_sha256` 가 실행 파일과 일치) + 새 PR #763 모양
  거부 테스트가 통과.
- `python3 on-the-record/hooks/test_pr_preflight.py` (기존 순수 파이썬
  러너) 가 새 케이스 포함 전부 PASS 를 출력하고, 기존
  `check_body(126, "Closes #126", "phase1") == []` 케이스도 여전히
  PASS(= `check_body` 자체는 안 바뀜의 실측).
- 랜딩 후 실제 `gh pr merge` 가 한 번 더 일어나면
  `~/.claude/on-the-record/hook-provenance.log` 에 새 줄이 append 된다
  — 그 줄의 `script_path` 가 실제로 어느 `installPath`(플러그인 캐시)를
  가리키는지, `script_sha256` 이 그 시점 main 의
  `on-the-record/hooks/contract-guard.sh` 해시와 같은지를 `sha256sum`
  으로 직접 대조하면, 다음 오배포가 다시 일어나도 이번처럼 캐시
  디렉터리 8개를 손으로 뒤지지 않고 그 자리에서 확인된다 — 이게 (a)가
  요구한 "추정이 아니라 실측"의 인수 기준이다.
