# UI 표면 선언 (issue-685)

`gates/ui_evidence_gate.py` 가 읽는다. 대상 레포가 diff 에서 "화면
표면"으로 간주할 경로를 여기에 선언한다 — 선언이 없거나 비어 있으면
게이트는 fail-closed 로 fallback 패턴 목록을 적용한다.

세 가지 상태가 있고 서로 구분된다:

- 파일이 아예 없다 → "선언 없음", fallback 이 적용된다.
- `## Globs` 절이 있지만 비어 있다 → "선언 없음"과 동일 취급, fallback
  이 적용된다.
- `## Globs` 절 아래 리터럴 한 줄 `none` → "이 레포에는 UI 표면이
  없다"는 명시적 선언, fallback 이 꺼진다.
- `## Globs` 절 아래 하나 이상의 glob 패턴(한 줄에 하나) → 그 패턴들만
  사용, fallback 은 쓰이지 않는다.

## Example

형식 예시(참고용 텍스트, 실제 헤딩 아님 — 게이트는 문서 안의 첫
`## Globs` 헤딩만 읽으므로 아래 텍스트는 파싱되지 않는다):

```
GLOBS HEADING:
src/screens/**
src/pages/**
```

## Globs

none
