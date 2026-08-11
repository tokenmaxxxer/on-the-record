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

## Scout: ran (1라운드, 위 표 참고)

외부 선례는 scout-brief.md 참고. 두 단계(웹서치 1라운드, 판단 1회)로 예산
안에서 종료 — 이 저장소 자체의 기존 신호 세 개(위 표)가 이미 결정에
필요한 대부분의 근거를 제공해서, 추가 심화 라운드가 결정을 바꿀 여지가
없었다(포화 판단).

---

# Round 2 (2026-08-11, 재조사 — 실환경 반증 2건)

위 라운드가 승인·구현·랜딩된 뒤(PR #756, `contract-guard.sh` 에
`is_src_test`/`is_record` 내용 게이트 추가, 유닛테스트 17개 통과), 실환경에서
두 건이 반증됐다. 이슈 코멘트 원문:
canonical: `gh issue view 741 --comments` (2026-08-11T05:55:34Z 코멘트)
두 사례 모두 이 코멘트에 기록돼 있다.

## 사례 2 근본 원인 (PR #768, issue-759 phase-1): 로직이 아니라 배포 캐시가 오래됐다

canonical: `git log -1 --format="%H %ai %s" -- on-the-record/hooks/contract-guard.sh`
(main, 커밋 `978d112`, `2026-08-11 14:23:29 +0900` = `05:23:29Z`) 및
`gh pr view 756 --json mergedAt` (`2026-08-11T05:28:21Z`, 이 내용 게이트를
main 에 실제로 얹은 머지).

PR #768 은 그보다 늦은 `2026-08-11T05:52:52Z` 에 머지됐다 —
canonical: `gh pr view 768 --json mergedAt`. 즉 **main 의 git 이력만 보면
내용 게이트는 PR #768 머지 24분 전에 이미 존재했다.** 그런데도 파일
목록(issue-759 의 proposals·reports/implementation 아래 문서 4개뿐,
`src/`·`tests?/` 없음)으로 게이트 조건을 재현하면 `is_src_test=False`,
`is_record=False` — 로직대로면 부착 전에 종료해야 했는데 부착됐다
(이슈 코멘트 원문, 위 canonical).

이 모순을 풀려면 "main 의 git 이력"과 "머지 순간 실제로 실행된 훅 파일"이
같은 것이 아니라는 사실이 필요하다. 이 세션이 실측한 것:

canonical:
```
$ python3 -c "
import json
d = json.load(open('/Users/jk/.claude/plugins/installed_plugins.json'))
for e in d['plugins']['on-the-record@tokenmaxxxer']:
    print(e)
"
{'scope': 'local', 'projectPath': '/Users/jk/workspace/10_WORK/tokenmaxxxer/on-the-record', 'installPath': '/Users/jk/.claude/plugins/cache/tokenmaxxxer/on-the-record/0a983531a9fe', 'version': '0a983531a9fe', 'installedAt': '2026-08-01T03:59:21.648Z', 'lastUpdated': '2026-08-11T04:06:29.067Z', 'gitCommitSha': '0a983531a9fe41d5059d3925cca2820bb7624ece'}
```
- `on-the-record/hooks/hooks.json` 이 `contract-guard.sh` 를
  `${CLAUDE_PLUGIN_ROOT}/hooks/contract-guard.sh` 로 등록한다(해당 줄:
  `"command": "${CLAUDE_PLUGIN_ROOT}/hooks/contract-guard.sh"`, 실행
  matcher `Bash` 블록) — 이 값은 오케스트레이터 자신의 프로젝트 경로
  (`/Users/jk/workspace/10_WORK/tokenmaxxxer/on-the-record`, on-the-record
  저장소 자체 checkout, 각 롤의 `~/.tokenmaxxxer/work/
  on-the-record-issue-*-implementation` 워크트리와는 별개)에 대해 위
  `installed_plugins.json` 항목이 가리키는 `installPath` 로 Claude Code
  플러그인 로더가 해석한다.
- 그 `installPath`(`.../cache/tokenmaxxxer/on-the-record/0a983531a9fe`)의
  `hooks/contract-guard.sh` 를 실측하면 —
canonical:
```
$ grep -c "is_src_test" /Users/jk/.claude/plugins/cache/tokenmaxxxer/on-the-record/0a983531a9fe/hooks/contract-guard.sh
0
$ diff /Users/jk/.claude/plugins/cache/tokenmaxxxer/on-the-record/0a983531a9fe/hooks/contract-guard.sh /Users/jk/workspace/10_WORK/tokenmaxxxer/on-the-record/on-the-record/hooks/contract-guard.sh | head -5
125c125
< pr_data = gh_json("pr", "view", pr, "--json", "body,number,commits")
---
> pr_data = gh_json("pr", "view", pr, "--json", "body,number,commits,files")
```
  — 내용 게이트가 통째로 빠져 있다. `gh pr view` 호출조차 `files` 필드를
  안 받는다.
- 이 설치본의 `gitCommitSha`(`0a983531a9fe41d5059d3925cca2820bb7624ece`)가
  실제로 main 이력에서 어디인지 —
canonical:
```
$ git -C /Users/jk/workspace/10_WORK/tokenmaxxxer/on-the-record log -1 --format="%H %ai %s" 0a983531a9fe41d5059d3925cca2820bb7624ece
0a983531a9fe41d5059d3925cca2820bb7624ece 2026-08-11 13:00:05 +0900 Merge pull request #728 from tokenmaxxxer/issue-726/conformance-review
$ git -C /Users/jk/workspace/10_WORK/tokenmaxxxer/on-the-record log 0a983531a9fe41d5059d3925cca2820bb7624ece..main --oneline -- on-the-record/hooks/contract-guard.sh
978d112 fix(issue-741): content-based phase-2 gate for contract-guard.sh
```
  설치본은 `2026-08-11 04:00:05Z` 커밋에서 멈춰 있다 — 내용 게이트 커밋
  (`05:23:29Z`)보다 83분 이르다. `lastUpdated: 2026-08-11T04:06:29.067Z`
  가 설치 시각과 정확히 일치한다.
- 8개 캐시 디렉터리 전부를 스캔해도 —
derived: `for d in /Users/jk/.claude/plugins/cache/tokenmaxxxer/on-the-record/*/; do grep -c is_src_test "${d}hooks/contract-guard.sh" 2>/dev/null; done`
```
0a983531a9fe   mtime=2026-08-11T13:06:26 has_is_src_test=0
0fa8a2c621e5   mtime=2026-08-08T10:37:13 has_is_src_test=0
18a5f9d88cd1   mtime=2026-08-10T16:28:54 has_is_src_test=0
23b3b6354cc7   mtime=2026-08-10T21:42:01 has_is_src_test=0
be71072db26b   mtime=2026-08-10T12:31:23 has_is_src_test=0
d95b7d4148a1   mtime=2026-08-09T12:39:44 has_is_src_test=0
e21cdf07fc24   mtime=2026-08-11T12:04:07 has_is_src_test=0
fbbae5b892df   mtime=2026-08-11T11:51:02 has_is_src_test=0
```
  이 세션이 시작된 지금(2026-08-11 오후, 여러 후속 머지가 이미 main 에
  더 얹힌 시점)까지도 캐시 8개 중 내용 게이트를 가진 사본은 0개다.

`on-the-record/hooks/self-update.sh` 의 자체 주석이 정확히 이 함정을 이미
문서화하고 있다: "`claude plugin update` 가 버전 문자열만 읽고 영원히
'already latest' 라고 보고한다" — 그리고 그 스크립트 자신이 `git pull`
하는 대상은 이 "설치 캐시"(installPath)가 아니라 별도의
"체크아웃"(spawn.py 를 찾아가는 대상, 위 예시에서
`/Users/jk/workspace/10_WORK/tokenmaxxxer/on-the-record` 자체)이다 —
canonical: `git -C /Users/jk/workspace/10_WORK/tokenmaxxxer/on-the-record log -1` 는
main 최신(`f9d2ded`, 이 저장소 `on-the-record/hooks/contract-guard.sh` 에
`is_src_test` 존재 확인됨)과 일치한다. 즉 **체크아웃은 최신인데 설치
캐시는 오래됐다** — self-update.sh 는 체크아웃만 갱신하고 설치 캐시는
갱신하지 않으므로 이 두 값이 갈라져도 아무것도 알아채지 못한다.

결론: 사례 2 는 `contract-guard.sh` 의 판정 로직 결함이 아니다(유닛테스트
17개가 이미 이를 확인, 위 라운드 참고). 원인은 머지를 실제로 집행한
프로세스가 어느 훅 사본을 실행했는지가 git 이력과 별개로 결정된다는
배포 계층의 사실이며, 지금까지는 그것을 실행 중에 기록할 수단이 전혀 없어
사후에 캐시 디렉터리 8개와 `installed_plugins.json` 을 손으로 대조해야만
알 수 있었다.

## 사례 1 근본 원인 (PR #763, issue-743 phase-1): 저자가 쓴 Closes 를 걸러낼 살아있는 체크가 없다

canonical: `gh pr view 763 --json body`
PR #763 본문은 `"...\n\n#743\n\nCloses #743"` 로 끝난다 — 저자가 평문
참조와 `Closes` 를 모두 직접 썼다(broker-attach 관여 없음, 병합 자체가
GitHub 네이티브 키워드 종결로 이슈를 닫았다).

canonical: `gh pr view 763 --json createdAt` / `gh issue view 743 --json comments`
PR 생성 시각은 `2026-08-11T05:40:57Z`, `APPROVE issue-743/implementation`
코멘트는 그보다 늦은 `05:42:18Z` — 즉 `gh pr create` 실행 시점에는 아직
승인이 없었다. `pr-preflight.sh` 의 phase 판정(정확한 문자열 일치 +
approvers.md)은 이 시점에 `phase2=False` 를 정확히 냈을 것이다 — 잘못된
phase 판정이 아니라, **phase1 로 정확히 판정된 뒤에도 저자가 쓴 Closes 를
걸러내지 못했다**는 뜻이다.

canonical: `on-the-record/hooks/pr-preflight.sh` 246-251번째 줄
```
    refs = {int(n) for n in _PLAIN_REF.findall(body)}
    if issue not in refs:
        return [f"PR 본문에 '#{issue}' 참조가 없다 — phase-1 제안 PR도 자기 "
                f"이슈를 본문에서 가리켜야 한다(Closes/Fixes/Resolves는 금지: "
                f"phase-1 머지가 이슈를 자동으로 닫으면 안 된다)."]
    return []
```
`check_body` 의 phase1 분기는 평문 `#issue` 참조가 있는지만 본다. deny
메시지 문구는 "Closes/Fixes/Resolves는 금지"라고 주장하지만, 그 문구가
반환되는 유일한 경로는 "평문 참조가 아예 없을 때"이지 "Closes 가 있을
때"가 아니다 — `#743` 과 `Closes #743` 이 본문에 함께 있으면 `refs`
집합에 743 이 들어 있으므로 `return []`(통과)한다. 이 코드는 이 훅이
`gates/pr_reference.py` 의 `check_body` 를 그대로 포팅한 것이라고 자기
헤더에 명시하는데(`on-the-record/hooks/pr-preflight.sh` 7번째 줄), 원본도
동일하다 — canonical: `gates/pr_reference.py` 58-63번째 줄(동일한 5줄,
동일한 조건문).

이건 우연한 이식 누락이 아니라 **의도적으로 남겨둔 경계**다 —
canonical: `tests/test_gates.py` 713-717번째 줄
```
def t_pr_reference_phase1_does_not_gate_closing_keywords_itself():
    # check_body 의 phase1 분기는 그 자체로 closing 키워드를 차단하지
    # 않는다 — 그 책임은 gates/ci.py 의 _phase1_mismatch 에 있다(코드
    # 확인, proposal 참조). phase1 은 #126 참조 존재 여부만 본다.
    assert pr_reference.check_body(126, "Closes #126", "phase1") == []
```
이 테스트가 `check_body(126, "Closes #126", "phase1") == []`(통과, 거부
아님)를 핀 처리하며, "책임은 `_phase1_mismatch` 에 있다"고 명시적으로
위임한다.

canonical: `gates/ci.py` 319-342번째 줄(`_phase1_mismatch`/
`_phase1_surface_mismatch` 정의) 및 440번째 줄(`main()` 안에서의 유일한
호출부)
`_phase1_mismatch`/`_phase1_surface_mismatch` 는 실제로 존재하고, 정확히
같은 `_CLOSES_REF` 정규식으로 본문(과 제목·커밋 메시지)을 검사해 phase1
PR 에 closing 키워드가 있으면 거부 사유를 반환한다 — `check_body` 가
일부러 안 하는 바로 그 검사다. 문제는 이 함수를 호출하는 코드가
`gates/ci.py` 의 `main()` 하나뿐이라는 것이다 —
canonical: `grep -rn "_phase1_mismatch\|_phase1_surface_mismatch" --include="*.py" --include="*.sh" .` 결과
(위 두 정의/호출 외 다른 호출부 0건).

`gates/ci.py` 의 `main()` 은 예전에 GitHub Actions 러너가 매 PR 마다
자동으로 실행했지만, 그 러너는 issue #460 으로 없어졌다 —
canonical: `on-the-record/hooks/accumulation-claim-guard.sh` 3-4번째 줄,
`on-the-record/hooks/call-shape-guard.sh` 3-4번째 줄 ("ported per issue
#512 — gates/ci.py's runner disappeared with GitHub Actions retirement,
#460"). issue #512 는 그 러너가 사라지며 잃은 개별 체크들을 하나씩
zero-install `PreToolUse` 훅으로 포팅하는 진행 중인 이니셔티브다
(`on-the-record/hooks/accumulation-claim-guard.sh` 가
`check_accumulation_claim` 을, `on-the-record/hooks/call-shape-guard.sh`
가 `subprocess_call_shape_divergence`/`sibling_mention_check` 를 포팅한
사례가 이미 있음). `pr-preflight.sh` 는 자기 헤더(6-9번째 줄)에 "ports
gates/pr_reference.py::check_body and gates/flows.py::_plan_from_body
inline" 이라고만 적혀 있고 `_phase1_mismatch`/`_phase1_surface_mismatch`
는 언급되지 않는다 — 이 포팅 이니셔티브가 아직 닿지 않은 항목이다.

결론: **이 저장소 전체에서 "phase-1 PR 본문에 Closes 금지"를 실시간으로
(`gh pr create`/`gh pr edit` 시점에) 집행하는 살아있는 코드는 현재
없다.** `check_body` 는 설계상 안 하고, `_phase1_mismatch` 는 하지만
아무도 부르지 않는다.

### 이전 라운드 판단의 정정

이전 라운드 서베이(위, "`docs/proposals/2026-08-10-closes-trailer-broker-attach-implementation.md`
와 issue-653 ADR" 절)는 "`pr-preflight.sh` 가 오판해도 머지를 집행하지도
`Closes` 를 쓰지도 않으므로 이슈 조기 종결을 스스로 만들어내지 않는다"고
결론지었다 — 이 결론은 그 절이 다루던 문제(라운드 스코프 오판이 phase1
PR 에 불필요한 `Closes` 요구를 강제하는 것)에 대해서는 지금도 맞다.
하지만 사례 1 은 **다른 메커니즘**이다: `phase` 판정 자체는 맞았고
(phase1), `pr-preflight.sh` 가 "쓰지" 않은 게 아니라 저자가 이미 쓴
것을 막지 못했다 — 저자의 `gh pr create` 명령 자체가 GitHub 에
`Closes #743` 를 담은 본문을 전달했고, 그 명령을 막았어야 할 `check_body`
가 막지 않았다. `gh pr merge` 는 그 본문을 그대로 읽어 네이티브 키워드
종결을 수행했을 뿐, broker-attach 관여가 전혀 없었다(사례 2 와 무관한
별도 경로).

## Scout: skip (조건 — 순수 버그픽스)

두 사례 모두 "이미 문서화된, 그러나 실행되지 않는" 규칙을 실행 경로에
복원/추가하는 작업이다: (a) 배포 캐시 최신성을 실행 중에 기록하는 것은
이 저장소의 다른 훅에 이미 있는 관측성 패턴(로그·마커 파일)의 연장이고
외부 제품 카테고리 비교 대상이 없다, (b) `pr-preflight.sh` 에 저자가 쓴
Closes 를 거부하는 검사를 추가하는 것은 이미 `gates/ci.py` 의
`_phase1_mismatch` 로 설계·구현·테스트까지 끝나 있는 로직을 이식하는
것뿐, 새 설계 결정이 아니다. 스카우트-디렉티브의 "순수 버그픽스" 스킵
조건에 해당한다.
