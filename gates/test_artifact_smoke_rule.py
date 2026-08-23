#!/usr/bin/env python3
"""issue-2073 — `artifact_smoke_rule.check_issue_body` 의 단위테스트.

네트워크·GitHub 없이 도는 것만(`test_acceptance_gate.py` 와 같은 관례).

  python3 gates/test_artifact_smoke_rule.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import artifact_smoke_rule as asr

_DECLARED = """runtime-artifacts:
- dist/bundle.js
- dist/index.html
"""


def t_declared_artifact_with_only_source_unit_check_is_refused():
    """실측 실패 형태(tm-dicequest#44): 재생성 diff/소스 유닛만으로는
    배송되는 바이트가 브라우저에서 죽어도 초록이다."""
    body = _DECLARED + """
## Acceptance
- check: `python3 -m pytest tests/test_sync.py -q` — 재생성 출력이 diff 동등 (provenance: executed-unit)
"""
    bad = asr.check_issue_body(2073, body)
    assert len(bad) == 1, bad
    assert "파싱/실행하는 검사가 하나도 없다" in bad[0], bad
    assert "dist/bundle.js" in bad[0], bad
    # 간접-검사 힌트가 실제로 붙는다.
    assert "tm-dicequest#26/#44" in bad[0], bad


def t_declared_artifact_with_node_check_is_admitted():
    body = _DECLARED + """
## Acceptance
- check: `node --input-type=module --check dist/bundle.js` (provenance: executed-unit)
"""
    assert asr.check_issue_body(2073, body) == []


def t_absent_declaration_is_byte_inert():
    body = """## Acceptance
- check: `python3 -m pytest gates/test_x.py -q` (provenance: executed-unit)
"""
    assert asr.check_issue_body(2073, body) == []


def t_no_acceptance_section_with_declaration_is_refused_fail_closed():
    bad = asr.check_issue_body(2073, _DECLARED)
    assert len(bad) == 1, bad
    assert "`## Acceptance` 절이 없다" in bad[0], bad


def t_empty_declaration_is_refused():
    body = "runtime-artifacts:\n\n## Acceptance\n- check: `node dist/a.js`\n"
    bad = asr.check_issue_body(2073, body)
    assert len(bad) == 1, bad
    assert "하나도 선언하지 않았다" in bad[0], bad


def t_malformed_tag_line_is_refused_not_silently_inert():
    """이슈 #2037 과 같은 형태 결함 — 태그 줄에 내용이 붙으면 조용히
    byte-inert 로 빠지는 대신 크게 거부한다."""
    body = "runtime-artifacts: dist/bundle.js\n\n## Acceptance\n- check: `pytest -q`\n"
    bad = asr.check_issue_body(2073, body)
    assert len(bad) == 1, bad
    assert "잘못된 형태" in bad[0], bad


def t_override_yes_suppresses_refusal():
    body = _DECLARED + """
artifact-smoke-override: yes

## Acceptance
- check: `python3 -m pytest tests/test_sync.py -q` (provenance: executed-unit)
"""
    assert asr.check_issue_body(2073, body) == []


def t_non_allowlisted_verb_naming_the_artifact_does_not_count():
    """산출물 이름을 스치기만 하는 명령(cat/grep/ls)은 파싱도 실행도
    아니다 — 허용목록이 닫혀 있어야 하는 이유."""
    body = _DECLARED + """
## Acceptance
- check: `cat dist/bundle.js` (provenance: executed-unit)
"""
    bad = asr.check_issue_body(2073, body)
    assert len(bad) == 1, bad


def t_allowlisted_verb_on_an_undeclared_path_does_not_count():
    body = _DECLARED + """
## Acceptance
- check: `node --check src/main.js` (provenance: executed-unit)
"""
    bad = asr.check_issue_body(2073, body)
    assert len(bad) == 1, bad


def t_gate_line_counts_the_same_as_check_line():
    body = _DECLARED + """
## Acceptance
- gate: `deno check dist/index.html` (provenance: executed-unit)
"""
    assert asr.check_issue_body(2073, body) == []


def t_fenced_declaration_block_parses():
    body = """runtime-artifacts:
```
dist/bundle.js
```

## Acceptance
- check: `npx playwright test --grep dist/bundle.js`
"""
    assert asr.check_issue_body(2073, body) == []


def t_command_touches_artifact_is_path_exact_or_suffixed():
    declared = ["dist/bundle.js"]
    assert asr.command_touches_artifact("node --check dist/bundle.js", declared) \
        == "dist/bundle.js"
    assert asr.command_touches_artifact("node --check ./dist/bundle.js", declared) \
        == "dist/bundle.js"
    assert asr.command_touches_artifact("node --check other.js", declared) is None
    assert asr.command_touches_artifact("", declared) is None


def t_advisory_line_fires_only_without_a_declaration():
    smelly = ("이 이슈는 browser 로 여는 generated single-file bundle 을 "
              "dist/ 아래에 배송한다.")
    line = asr.advisory_line(2073, smelly)
    assert line is not None and "거부 아님" in line, line
    # 선언이 있으면 안내는 침묵한다(거부 경로가 이미 판정을 맡는다).
    assert asr.advisory_line(2073, _DECLARED + smelly) is None
    # 어휘가 임계값 미만이면 침묵한다.
    assert asr.advisory_line(2073, "게이트 하나를 고친다") is None


def t_design_artifacts_parser_stays_intact_under_the_tag_parameter():
    """이슈 #2073 이 넓힌 계약은 기존 태그의 동작을 바꾸지 않는다 —
    기본 인자가 `design-artifacts` 이고, 새 태그는 자기 태그만 본다."""
    import design_artifacts_gate as dag
    body = "design-artifacts:\n- docs/s.md\n"
    assert dag.parse_declaration(body) == ["docs/s.md"]
    assert dag.parse_declaration(body, "design-artifacts") == ["docs/s.md"]
    assert dag.parse_declaration(body, "runtime-artifacts") is None
    assert dag.parse_declaration("runtime-artifacts:\n- dist/a.js\n",
                                 "runtime-artifacts") == ["dist/a.js"]
    assert dag.malformed_declaration_line("design-artifacts: a.md") == \
        "design-artifacts: a.md"
    assert dag.malformed_declaration_line("design-artifacts: a.md",
                                          "runtime-artifacts") is None


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("t_") and callable(f)]
    _run(tests)
