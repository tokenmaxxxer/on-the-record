# spawn.py CLI — role path and skill path

이슈 #2241 stage 0. `spawn.py`는 이제 두 가지 호출 모양을 받는다. 하나는
기존 role 경로, 하나는 이번 스테이지가 additive 로 얹는 skill 경로다. 두
경로는 서로 독립이다 — `--skill` 을 쓰지 않으면 이전과 완전히 같다.

## role 경로 (기존, 안 바뀜)

```
spawn.py <역할> "<맡길 일>" [-C <경로>] [--issue <n>] [--skills a,b,c] [...]
```

`<역할>` 은 `ROLES`(43개) 중 하나거나 `init`/`ps`/`watchdog`/`drive` 같은
내장 verb 다. 이슈/브랜치/워크스페이스/스폰 클레임/TTL 리스, board 기록
쓰기 범위 — 전부 이 경로가 오늘까지 하던 그대로다. 이번 스테이지는 이
경로의 어떤 분기도, 어떤 헬퍼도 건드리지 않았다.

## skill 경로 (신규, 이 스테이지가 추가)

```
spawn.py --skill <스킬명>[,<스킬명>...] "<맡길 일>" --issue <n>
```

`--skill` 이 주어지면 `spawn.py` 는 **세션을 띄우지 않는다.** role→skill
표(`_ROLE_SKILLS`)를 거치지 않고 이름 그대로를
`skills.resolve_skill_source()` 로 skill-repository 체크아웃에서 직접
해석해, 그 결과만 JSON 으로 stdout 에 찍고 종료한다:

```json
{
  "task": "<맡길 일>",
  "issue": 2241,
  "source": "skill-repo",
  "skills": ["<스킬명>", ...],
  "skill_sha": "<skill-repository 짧은 sha>"
}
```

이름을 알 수 없거나 해석된 디렉터리가 `hooks/` 를 들고 있으면(가이던스
전용 원칙 위반) 워크스페이스/브랜치를 만들기 전에 fail-closed 로
종료한다 — `resolved_skill_dirs()`/`resolve_skill_source()` 가 이미
role 경로에서 쓰는 것과 같은 검사다.

**동시성/write-scope/observer 검증에 아직 영향 없음.** 이 경로는 스폰
클레임도, TTL 리스도, board write-scope 도, `merge_gate` 의 observer
레코드 요구도 건드리지 않는다 — 그 세 가지 개념(리스, author identity,
record-kind)은 이슈 #2241 stage 1/3/5 에서 따로 들어온다. 지금 이
경로가 하는 일은 "스킬 이름 → 가이던스 해석" 뿐이다.

### positional 인자에 관한 참고

`spawn.py` 의 positional 은 `<role> <task>` 순서로 고정돼 있다.
`--skill` 을 쓰면 `<역할>` 자리가 없으므로, 커맨드라인에 남는 단일
positional("<맡길 일>")은 argparse 규칙상 첫 번째 positional
슬롯(`a.role`)에 묶인다 — `spawn.py` 는 `--skill` 이 있을 때 이
슬롯을 태스크 문구로 읽는다. 사용자가 신경 쓸 내부 구현 디테일이며,
위 사용법 그대로 쓰면 그대로 동작한다.

## 동등성

역할과 스킬이 오늘 1:1 로 매핑되는 쌍(예: `implementation` ↔
`implementation-blueprint` 등 `_ROLE_SKILLS["implementation"]` 의
원소들)에 대해, role 경로가 해석하는 스킬 목록과 skill 경로가 같은
이름들로 해석하는 결과는 동일하다 —
`test/test_spawn_skill_invocation.py` 가 이 동등성과, role 이 없는
스킬(순수 skill 경로 전용 이름)의 해석 둘 다를 검증한다.
