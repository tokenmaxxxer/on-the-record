# Consult trace log

One line per `spawn.py consult` call made with no `--issue` (issue-scoped
calls trace to `docs/issue-<n>/reports/consult-log.md` instead) — success
or failure alike. See `on-the-record/commands/consult.md` and
`spawn.py:consult_cmd`. Appended by `spawn.py`, never hand-edited.
- 2026-08-12T07:42:13.693150+00:00 | role=requirements-engineering | issue=none | question='이 저장소에 테스트 프레임워크로 pytest 를 쓰는가?' | outcome='ok: 예, 이 저장소는 pytest를 테스트 프레임워크로 사용한다 (pytest.ini, conftest.py, gates/test_*.py 다수 확인).'
- 2026-08-12T07:47:22.099327+00:00 | role=requirements-engineering | issue=none | question='Assess a proposed requirement: default-on convergence loop — every landed fix verified by executed-live evidence; verification-discovered defects filed as root-cause issues immediately.' | outcome="ok: 합리적이나 무조건 default-on은 위험. '모든 랜딩된 fix'를 execute-live 증거로 검증한다는 범위가 과도하게 넓다 — trivial/문서성 변경까지 강제하면 검증 비용이 변경 자체보다 커지는 accumulation-cost 문제가 생긴다. 대신 (1) 코드/동작 변경이 있는 fix에 한정해 execute-live 검증을 default-o"
