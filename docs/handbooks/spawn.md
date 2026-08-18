# spawn.py — self-hosted hook wiring

이슈 #508. `spawn.py` 가 자기 자신(on-the-record 레포)을 대상으로 역할
세션을 띄울 때, 컨슈머 설치 경로에서 나가는 `on-the-record/hooks/hooks.json`
을 그 세션에도 켠다.

## 왜 필요했나

`on-the-record/hooks/hooks.json` 은 마켓플레이스로 설치한 컨슈머 세션에는
`--plugin-dir` 을 통해 켜지지만, on-the-record 자신의 레포에는 체크인된
`.claude/settings.json` 이 없어 이 저장소를 대상으로 한 역할 세션에서는
계속 inert 였다 — preflight/가드/stop-gate 전부 안 붙는 채로 이 저장소
자신의 커밋이 돌아갔다는 뜻이다.

## 왜 체크인된 `.claude/settings.json` 이 아니라 spawn-time 병합인가

`spawn.py:require_no_repo_config()` 는 스폰 **대상** 레포가 자기
`.claude/settings.json`/`.claude/hooks`/등을 들고 있으면 멈춘다 —
그 파일의 훅은 스폰이 선언한 `sandbox.filesystem` 경계를 받지 않고 전체
사용자 권한으로 돈다(2026-07-27 실측 사고). on-the-record 는 자기 자신을
대상으로 스폰할 때마다 정확히 이 "대상 레포가 자기 설정을 들고 있다" 케이스가
되므로, 체크인된 파일로 풀면 그 정지를 매번 트립시키고 매번 신뢰 고정이
필요해진다. 대신 `role_settings()` 가 이미 만드는 `--settings` 임시 파일에
직접 병합해 넣는다 — `require_no_repo_config` 가 보는 파일시스템 표면을
전혀 건드리지 않는다.

## 동작

- `spawn.self_hosted_hooks(cwd)`: `<cwd>/on-the-record/hooks/hooks.json`
  이 존재하면 그 `"hooks"` 값을 읽고, `${CLAUDE_PLUGIN_ROOT}` 를
  `<cwd>/on-the-record` 로 치환해 돌려준다. 없으면 `None`.
  (컨슈머 설치 경로에서는 Claude CLI 가 `--plugin-dir` 로 이 변수를
  채우지만, 여기서는 그 경로로 로드하지 않으므로 spawn.py 가 직접 치환한다.)
- `spawn.role_settings(role, cwd=None)`: `cwd` 가 self-hosted 대상으로
  판정되면(위 함수가 `None` 이 아닌 값을 돌려주면) 반환하는 설정 dict 에
  `"hooks"` 키를 추가로 얹는다. 다른 모든 대상 레포에는 아무 변화 없음
  (additive, opt-in by target detection).
- 두 호출부(`main()` 의 `--dry-run` 경로, `_spawn_one()`) 모두 `cwd` 를
  넘긴다.

## 정합성 보장

`gates/test_hooks_parity.py` 가 `on-the-record/hooks/hooks.json` 의 모든
(event, matcher, script) 삼중항이 `self_hosted_hooks()` 출력에 그대로
있는지 매 실행마다 대조한다 — 손으로 유지하는 두 번째 목록이 아니라
hooks.json 자체를 읽어 낸다. 같은 파일이 실제 git 저장소에서 `git commit`
시도를 살려/거부하는 live-fire red/green 페어도 돈다.

```
python3 gates/test_hooks_parity.py
```

# spawn.py judge — read-only budgeted role judgment over a merge diff

이슈 #1587. `consult`/`ideate`/`draft`/`review`의 형제 verb지만 세션 조립이
읽기 전용으로 구조적으로 격리된다는 점에서 다르다 — 프롬프트 문장으로
"쓰지 마라"고 지시하는 게 아니라 `--plugin-dir`/`permissions` 자체가
Write/Edit 를 세션에 넣지 않는다.

```
python3 spawn.py judge <역할> --merge <sha> [-C <대상 레포>]
```

## 파이프라인

1. **prefilter** (하이쿠급 1콜): diff 가 이 역할의 관할에 걸리는지만
   판단한다. 미스면 judge 본세션을 아예 안 부른다 — 가장 큰 비용 절감
   지점.
2. **judge** (역할 모델, `--max-turns 6`): 역할 룰북이 로드된 읽기 전용
   세션이 diff 를 보고 위반 findings 를 낸다.
3. **validator** (하이쿠급 1콜): findings 를 확인/반박한다. 반박된 것은
   큐에 닿지 않는다.
4. **verify**: `gates/patrol_queue.py`의 `verify()`가 인용된 경로/발췌를
   작업 트리에서 실제로 다시 읽어 확인한다 — `run_scan()`이 이미 밟는
   scan → verify → budget → enqueue 파이프라인의 그 단계. validator(모델의
   자기평가)만으로는 환각된 path/excerpt 를 잡아내지 못하므로, 이 단계를
   건너뛰지 않는다(2026-08-15 warrant-hunt finding).
5. **enqueue**: verify 를 통과한 finding만 `enqueue()`로
   `.on-the-record/findings/queue.jsonl`에 `lane="diff"`로 들어간다.

## 읽기 전용 구성

- `spawn._readonly_plugin_dirs(role, spec)`: 역할 룰북은 그대로 싣고,
  core 플러그인 중 배달-지향(`freelunch`/`scout`/`warrant`)만 뺀다.
- `spawn._readonly_settings(role, cwd)`: `permissions.allow`를
  Read/Grep/Glob + `git show`/`git diff`/`git log`(cwd 앵커)로만 한정하고,
  Write/Edit/`gh `는 `permissions.deny`로도 명시적으로 막는다.
- `_judge_cmd_and_env()`는 `--permission-mode bypassPermissions`를 주지
  않는다 — headless 세션은 허용 목록 밖 도구를 답할 사람 없이 그냥
  거부한다(`role_settings()`가 서술하는 실측 동작을 안전장치로 쓴다).

## 예산

- `JUDGE_TIMEOUT = 120`(초) — prefilter/judge/validator 호출마다 각각.
- `JUDGE_MAX_ROLES_PER_MERGE = 3` — 같은 merge sha 에 대해 실행할 수
  있는 judge 역할 수 상한. `runs/patrol-judge-log.md` 트레이스
  로그에서 `merge=<sha>`를 세어 판정하며, **로그가 없거나(회전/최초
  실행) 손상돼 있으면 0으로 fail(허용)** 한다 — 로그 부재가 판정을
  막지 않는다(PR #1590 binding review note).

## 트레이스

모든 실행(성공/실패/캡초과/prefilter-미스 가리지 않고)이
`runs/patrol-judge-log.md`에 한 줄 남는다 — consult-log의
`finally`-블록 관례와 같다. `runs/`는 git-ignored라 커밋 없이도
대상 트리를 더럽히지 않는다(이슈 #1730).

## 의존성

`tokenmaxxxer-core#216`(scope-gate 읽기전용 세션 수정)이 아직 안 걸린
환경에서는, 망가진 proposal 이 있는 레포를 대상으로 한 통합 테스트가
연기된다 — #216 이 머지된 뒤에는 도달 가능해지지만 이 변경 자체의
frozen write set 밖이라 이 이슈에서는 다루지 않는다(§Out of scope).
