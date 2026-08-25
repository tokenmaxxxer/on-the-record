# 브랜치/레코드 네이밍 — 역할 축과 스킬 축 (dual-scheme)

이슈 #2432 (role retirement stage 4). `docs/decisions/2026-08-25-retire-
role-axis-staging.md`가 결정한 role-axis 은퇴 7단계 프로그램 중 이 stage
가 브랜치 이름과 레코드 경로를 역할(role) 축에서 스킬(skill) 축 +
lease-disambiguator 로 옮긴다 — **완전히 대체하는 것이 아니라, 두 스킴이
공존하는 기간을 둔다.**

## 두 스킴

### 옛 스킴 (role axis) — 계속 지원

```
issue-<n>/<role>
docs/issue-<n>/reports/<role>.md
```

`<role>` 은 `spawn.ROLES`(고정 43개 이름) 중 하나. `spawn.py <role>
"<task>" --issue <n>` 이 만들고 오늘까지와 바이트-동일하게 계속 만든다 —
`pipeline.checkout_issue_branch(cwd, issue, role)`.

### 새 스킴 (skill axis + lease disambiguator) — 이 stage 가 추가

```
issue-<n>/<skill>-<lease-disambiguator>
docs/issue-<n>/reports/<skill>-<lease-disambiguator>.md
```

`<skill>` 은 skill-repository 가 해석하는 스킬 이름(고정 enum 없음 —
동결 결정 `single-skill-axis`). `<lease-disambiguator>` 는
`roster.new_lease_disambiguator()`가 세션마다 새로 뽑는 8자리 hex 문자열이다.

스킬 이름 하나만으로는 세션을 유일하게 구분하지 못한다 — 같은 이슈에
같은 스킬을 두 세션이 동시에 물 수 있다(role 은 그 자체로 유일했다:
로스터가 `issue-<n>/<role>` 키를 세션당 하나만 허용했다). 그래서
disambiguator 가 실제 충돌-방지 세그먼트를 맡는다 — 브랜치 이름과
`roster.lease_key(issue, f"{skill}-{disambiguator}")` 둘 다 같은
문자열을 두 번째 세그먼트로 쓴다.

`pipeline.checkout_issue_branch_for_skill(cwd, issue, skill,
disambiguator=None)` 가 이 스킴으로 checkout 한다 — `disambiguator` 를
생략하면 내부에서 새로 뽑는다.

## 공존 기간 (coexistence window)

- **시작**: 이 stage(#2432)가 landing 된 커밋.
- **의도된 끝**: stage 6 (role 삭제) — role-named 브랜치가 하나도 안 남았을 때.
- 그 사이, `board.py`의 발견 walk(`board()`)는 두 스킴을 **모두** 읽어
  합친다 — 어느 쪽 이름으로 만들어진 레코드든 같은 `board()` 리스팅에
  나온다. 새 스킴 레코드는 고정 role enum 에 없으므로, 이름 모양이 아니라
  "reports/ 바로 아래 + frontmatter 블록 있음"으로 판별한다
  (`board._skill_axis_report_names()`).
- 이 stage는 **기존에 열려 있는 PR 의 브랜치 이름을 하나도 바꾸지
  않는다** — 강제 rename/re-point 없음. 자세한 내용은
  `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`.
- 실제 세션 스폰(`spawn.py --skill ...`)은 아직 이 스킴으로 세션을
  띄우지 않는다(stage 0 은 가이던스 해석 JSON만 찍고 세션은 안 띄운다) —
  이 stage는 두 네이밍/발견 함수를 준비해 두는 것이지, 오늘의 기본 스폰
  경로(role positional)를 바꾸지 않는다. role positional 이 여전히 유일한
  실제 세션 스폰 경로다.

## 구현 지점

| 무엇 | 어디 | 스킴 |
|---|---|---|
| 브랜치 checkout (옛) | `pipeline.checkout_issue_branch()` | role |
| 브랜치 checkout (새) | `pipeline.checkout_issue_branch_for_skill()` | skill + disambiguator |
| 공통 checkout 로직 | `pipeline._checkout_named_branch()` | 둘 다 위임 |
| disambiguator 생성 | `roster.new_lease_disambiguator()` | 새 스킴 |
| 보드 발견 (역할 고정 목록) | `board.board()`의 `_sp.ROLES` 루프 | role |
| 보드 발견 (스킬 축 확장) | `board._skill_axis_report_names()` | skill + disambiguator |

파일마다 새 네이밍/발견 함수는 **하나**다 — call site 마다 스킴을
따로 분기하지 않는다(제안서 Accumulation).
