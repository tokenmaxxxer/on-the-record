---
allowed-tools: Bash(python3:*), Bash(git:*), Bash(gh:*), Read, Write
description: 컨슈머 세션에서 on-the-record 플러그인 자체의 결함을 upstream 에 issue 로 보고한다 — PR 은 절대 아니다
argument-hint: "\"<결함 관측 서술>\" — 예: \"watcher registry 가 재기동 후 살아있는 pid 를 DEAD 로 표시한다\""
design-rationale: 컨슈머 세션에는 upstream 결함을 보고할 채널이 없어 관측이 대화 로그에서 죽는다 (issue #1131). draft→dedup→미리보기→확인 순서로 만든 이유는 자동 제출을 금지하는 req#3 을 지키면서도 사용자가 매번 초안을 손으로 쓰지 않게 하기 위함이고, issue-only 인 이유는 fix 는 upstream 자체의 issue→role 플로우 몫이라 컨슈머가 PR 을 열 권한/근거가 없기 때문이다 (req#4).
---

인자: $ARGUMENTS

`ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..`, upstream 저장소는
`tokenmaxxxer/on-the-record` 로 둔다.

## 무엇인가 (issue #1131)

컨슈머 세션(target 레포에 on-the-record 가 설치된 세션)이 플러그인
자체의 결함을 관측했을 때, 그 관측을 upstream(on-the-record 본체) 에
issue 로 보고하는 채널이다. `roles/upstream-defect-report.json` 이 이
채널의 스펙 홈이고, `docs/specs/upstream-defect-channel.md` 가 EARS
요구사항 명세다. **issue 로만 보고한다 — PR 경로는 없다** (req#4,
UDC-4). hooks/command 요소만 쓰고 CI 를 만들지 않는다 (req#7).

## 단계

1. **초안 조립 (UDC-1).** `$ARGUMENTS` 의 결함 서술로부터 다음 세
   섹션을 담은 초안을 만든다:
   - `Plugin version`: 현재 설치된 on-the-record 플러그인의 커밋 sha
     (`git -C "$CLAUDE_PLUGIN_ROOT/.." rev-parse HEAD`).
   - `Reproduction`: 관측 당시 실행한 명령/조건 — 아는 만큼 기입한다,
     지어내지 않는다.
   - `Observation context`: 언제/어느 세션/어느 role 에서 관측했는지.

2. **중복 체크 (UDC-2).** 초안을 사용자에게 보이기 전에
   `gh issue list --repo tokenmaxxxer/on-the-record --state open --search
   "<초안 제목 핵심어>"` 로 열린 upstream issue 를 찾는다. 유사한
   issue 가 있으면 그 번호와 제목을 초안과 함께 보여준다 — 사용자가
   그래도 새로 낼지, 기존 issue 를 참조만 할지 고른다.

3. **미리보기 + 확인 (UDC-3).** 조립된 초안 전문을 사용자에게 그대로
   보여주고 확인을 받는다. **확인 전에는 upstream 에 어떤 쓰기 호출도
   하지 않는다** — `gh issue create` 를 포함해 어떤 네트워크 filing
   호출도 이 단계 이전에는 일어나지 않는다.

4. **filing (확인 후에만).**
   - upstream 에 도달 가능하면: `gh issue create --repo
     tokenmaxxxer/on-the-record --title "<제목>" --body "$(cat <<'EOF'
     <초안 본문>
     EOF
     )"` 로 issue 를 연다. 필요하면 `gh-write-allow-gate.sh` 가 이미
     허용하는 다섯 verb 중 `gh issue create` 를 그대로 쓴다 — 새
     wrapper 를 만들지 않는다.
   - upstream 이 도달 불가능하면 (권한/네트워크 실패, UDC-5): 초안을
     컨슈머 레포의 `docs/reports/upstream-findings/<날짜>-<슬러그>.md` 로
     저장하고, 그 fallback 이 일어났다고 사용자에게 보고한다.

5. **PR 경로는 존재하지 않는다 (UDC-4).** 이 커맨드는 `gh pr create`,
   `gh api ... /pulls`, GraphQL `createPullRequest`, `GH_REPO` 환경변수로
   구동되는 `gh pr create`, 또는 `hub`/`curl` 로 GitHub API 를 직접
   때리는 어떤 PR 생성 호출도 절대 만들지 않는다.
   `on-the-record/hooks/upstream-defect-scope-guard.sh` 가 이 경로에서
   그런 호출을 구조적으로 차단한다 — 이 문서에 규칙을 적는 것만으로
   끝내지 않는다.

## 무엇을 하지 않나

- upstream 에 자동으로, 확인 없이 파일링하지 않는다 (req#3).
- upstream 에 PR 을 열지 않는다, 열 것을 제안하지 않는다 (req#4).
- CI/GitHub Actions 를 만들지 않는다 — hooks/command 요소만 쓴다
  (req#7).
