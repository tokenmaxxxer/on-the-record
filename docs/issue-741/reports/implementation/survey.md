# Current-state survey — issue #741

## Scope of this survey

이슈 #741 이 조사를 요구하는 대상은 `contract-guard.sh`(merge 시점 broker-attach,
#653)가 "이 PR 이 phase-2 다"를 판정하는 신호다. 판정이 틀리면 문서만 담은
phase-1 PR 이 승인 직후 머지될 때 `Closes #n` 이 잘못 붙어 이슈가 조기
종결된다(2026-08-11, issue-729, PR #739 로 실제 재현).

## Deployed surface today

### `on-the-record/hooks/contract-guard.sh` — merge 시점 broker (issue #653)

`PreToolUse` 훅으로 `gh pr merge` 를 가로챈다. 읽기 전용 `gh pr view <pr> --json
body,number,commits` 한 번(`contract-guard.sh:125`)과 `gh issue view <issue>
--json comments`(`:165-168`) 두 번의 API 호출로 판정한다.

`phase2` 판정 (`:130-176`, issue #577 "round-scoped" 신호):
- PR 자신의 head 브랜치 커밋들 중 최솟값 `committedDate` 를
  `first_commit_at` 로 삼는다(`:135-139`).
- `docs/specs/approvers.md` 에 등재된 계정이 쓴, `"APPROVE issue-<n>/"` 로
  시작하고 접두사 뒤가 비어있지 않은 이슈 코멘트가 있고, 그 코멘트의
  `createdAt` 이 `first_commit_at` 보다 늦으면 `phase2 = True`.
- 이 신호는 순수하게 **시간**만 본다. PR 의 diff 내용은 전혀 보지 않는다.

`phase2 == True` 면(`:177-201`) PR 본문에 `Closes #<issue>`(또는
Fixes/Resolves)가 없거나 다른 이슈를 가리키면, 거부하는 대신 `gh pr edit`
로 트레일러를 붙이거나 고쳐 쓰고 머지를 통과시킨다(broker-attach, issue
#653) — 이게 재현 시나리오 5-6단계에서 `Closes #729` 를 실제로 써넣은
지점이다.

**결함의 정확한 형태**: 이 저장소의 2단계 계약에서 phase-1 PR 과 phase-2
PR 은 **같은 브랜치**(`issue-<n>/<role>`)를 공유한다. 승인은 phase-2 를
"여는" 신호이므로 정의상 phase-1 의 첫 커밋보다 나중에 온다 — 그래서
`createdAt > first_commit_at` 는 phase-1 PR 이 승인된 바로 그 순간에도
항상 참이 된다. 이 신호는 "이번 라운드에 유효한 승인이 있는가"(정책
질문)에는 맞는 답을 주지만 "지금 머지되는 이 PR 이 실제로 phase-2 코드를
담고 있는가"(내용 질문)에는 아무 답도 주지 않는다. 두 질문을 하나의
신호로 뭉뚱그린 것이 조합 결함이다.

`test_contract_guard.py:282-322` 의 round-scoping 매트릭스(issue #577)는
"승인이 자기 자신이 머지하려는 그 PR을 향한 경우"(즉 phase-1 PR 자신이
승인 대상인 경우)를 다루는 케이스가 없다 —
derived:
```
grep -n "^def test_" on-the-record/hooks/test_contract_guard.py
```
아래에 실행한 실제 출력을 인용한다.

### `on-the-record/hooks/pr-preflight.sh` — create/edit 시점 조기경보 (issue #459/#653)

`gh pr create|edit` 를 가로채 `--body`/`--body-file` 내용을 직접 파싱해
같은 부류를 점검한다(`:29-259`). `phase2` 판정(`:114-119`)은
`contract-guard.sh` 와 **다른 신호**를 쓴다: 정확히 `"APPROVE
issue-<n>/<role>"` 와 완전히 같은 문자열 코멘트가 approvers.md 계정에서
왔는지만 보고, `first_commit_at` 비교(라운드 스코프)가 전혀 없다. 즉 그
이슈/롤에 대해 과거 어느 라운드에서든 승인 코멘트가 한 번이라도 존재했으면
이후 그 롤이 새로 여는 phase-1 제안 PR 도 영원히 phase2 로 오판된다 — 이건
#577 결함이 이 두 번째 위치에서는 아직 고쳐지지 않은 채로 남아 있다는
뜻이다(docs/issue-653/reports/architecture/survey.md:19-25 가 "the literal
#577 defect, un-composed" 라고 명시).

이 훅은 머지를 집행하지 않고 `Closes` 를 자동으로 쓰지도 않는다 —
`deny()` 만 한다. 그래서 오판되더라도 #741 이 재현한 "머지 순간 이슈가
자동으로 닫힌다" 결과를 이 훅 혼자서는 만들 수 없다; 만들어내는 건
`contract-guard.sh` 뿐이다.

### `on-the-record/hooks/approval-gate.sh` — write 시점 phase-2 승인 게이트 (issue #608)

세 번째의 독립된 phase 판정 지점. `Write|Edit|MultiEdit` 를 가로채,
**해당 세션의 브랜치 role 이 쓰려는 경로가 phase-2 모양인지**를 먼저
판정한 뒤에만 승인 여부를 확인한다(`:115-120`):
```python
record_path = "docs/issue-%d/reports/%s.md" % (issue, role)
is_record = n == record_path or n.endswith("/" + record_path)
is_src_test = re.search(r"(^|/)(src|tests?)/", n) is not None
if not (is_record or is_src_test):
    sys.exit(0)  # phase-1-legal path
```
이것이 이 저장소에 이미 배포되어 있는, **경로 내용 기반**으로 "이 변경이
phase-2 모양인가"를 정의하는 유일한 기존 코드다. 이슈별 reports 디렉터리
바로 아래의 role 레코드 파일(정확히 그 파일, 하위 디렉터리 아님) 또는
`src/`/`tests?/` 경로 매칭 — 그 외(`proposals/`, `reports/<role>/*.md`,
`decisions/`, `handbooks/`, `approvers.md` 자신)는 전부 phase-1-legal 로
통과시킨다. 지금 쓰고 있는 이 서베이 파일은 role 레코드 파일 자체가 아니라
그 하위 디렉터리 경로라서 `is_record` 에 걸리지 않는다 — 정확히 role
레코드 파일 자체만 걸린다.

## 세 훅의 phase 판정 신호 비교

| 훅 | 시점 | 신호 | 라운드 스코프 | 내용(diff) 검사 |
|---|---|---|---|---|
| `contract-guard.sh` | `gh pr merge` | APPROVE 코멘트 존재 + 시간 | 있음(#577) | 없음 |
| `pr-preflight.sh` | `gh pr create/edit` | APPROVE 코멘트 존재(정확 일치) | 없음(알려진 결함, #653 survey gap #1, 의도적으로 뒤로 미룸) | 없음 |
| `approval-gate.sh` | `Write/Edit/MultiEdit` | 승인 여부만(대상 경로가 이미 phase-2 모양인지는 승인과 무관하게 먼저 검사) | 해당 없음(대상이 이미 phase-2 파일인지가 선행 조건) | **있음** — 대상 경로 자체가 src/\ tests?/\ 나 role 레코드 파일인지 |

`approval-gate.sh` 만 유일하게 "승인 여부"와 "이게 phase-2 모양의 변경인가"를
분리해서, 후자를 대상 **경로**로 판단한다. 이게 #741 이 요구하는 조합과
구조적으로 가장 가깝다 — `contract-guard.sh` 에 없는 것이 바로 이 경로
기반 내용 검사다.

## `docs/proposals/2026-08-10-closes-trailer-broker-attach-implementation.md` 와 issue-653 ADR

`docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`
(status: landed)가 현재의 broker-attach 를 설계했다. ADR 은 "Round-scoping
already exists where it now matters... no new phase-2 detection code is
added"(라인 71-76)라고 명시하며 #577 의 신호를 그대로 재사용하기로
못박았다 — 즉 #741 이 지금 발견한 조합 결함은 #653 설계 당시 시야 밖에
있었다(그 신호 자체가 라운드 안에서도 "이 PR 자신이 승인 대상인 경우"를
구분 못 한다는 걸 아무도 검사하지 않았다). 같은 ADR 은 `pr-preflight.sh`
쪽 하드닝(라운드 스코프 포팅, body-file 레이스 수정)을 "nice to have, out
of scope for this pass" 로 명시적으로 뒤로 미뤘다(라인 68-70) — 근거는
`contract-guard.sh` 가 "the one place that guarantees the trailer,
independent of what any spawning session did or didn't write"(라인
80-82)이므로 `pr-preflight.sh` 는 조기 경보일 뿐 정확성에 대해
load-bearing 하지 않다는 것.

이 판단은 지금도 유효하다: `pr-preflight.sh` 는 머지를 집행하지 않고
`Closes` 를 쓰지도 않으므로, 이 훅이 오판해도 이슈 조기 종결을 스스로
만들어내지 않는다(위 표). 따라서 #741 의 수정 대상은 `contract-guard.sh`
하나로 좁혀진다 — 아래 "범위" 절 참고.

## `docs/specs/approvers.md`

```
- JiwonJung94
- jjongkwann
```
두 계정이 등재되어 있다 — 테스트 픽스처가 이미 쓰는 `alice`/`bob` 같은
가상 계정과는 별개로, 실제 승인 판정에 쓰이는 목록.

## 예상 write set (phase-2, 승인 후)

- `on-the-record/hooks/contract-guard.sh` — `phase2` 판정 뒤에 "이 PR 의
  diff 가 phase-2 모양인가" 내용 검사를 추가. `gh pr view` 호출에 `files`
  필드를 얹어(추가 API 왕복 없음) 얻은 경로 목록을 `approval-gate.sh` 의
  `is_record`/`is_src_test` 패턴과 같은 모양으로 판정.
- `on-the-record/hooks/test_contract_guard.py` — 기존 round-scoping
  매트릭스(`:282-366`)에 "승인이 자기 자신을 향하는 문서만 담은 PR"
  회귀 케이스와 "코드 포함 PR + 승인" 케이스를 추가(§Acceptance 의 두
  체크에 대응). 저장소 루트 test 이동 작업(issue-729)과 겹치지 않는
  기존 on-the-record/hooks/test_*.py 관례 자리.
- 이슈 결정 문서 한 편 — 선택한 신호와 기각한 대안(대안 B: 제안서
  frontmatter write set 대조, 대안 C: PR 본문 phase 선언)의 근거, #476
  위조가능성 판단 기록. 승인 후 issue-741 결정 트리 아래 새로 만든다(지금
  저장소에는 아직 존재하지 않는다).
- phase-2 레코드 한 편 — 계약이 요구하는 implementation 레코드. 승인 후
  이 이슈의 reports 디렉터리 바로 아래(role 레코드 파일 경로)에 새로
  만든다(지금은 아직 존재하지 않는다).

## Scout: ran

외부 선례는 scout-brief.md 참고. 두 단계(웹서치 1라운드, 판단 1회)로 예산
안에서 종료 — 이 저장소 자체의 기존 신호 세 개(위 표)가 이미 결정에
필요한 대부분의 근거를 제공해서, 추가 심화 라운드가 결정을 바꿀 여지가
없었다(포화 판단).
