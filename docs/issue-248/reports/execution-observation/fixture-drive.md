# Issue #248 execution-observation — independent fixture drive

canonical: `gh issue view 248` (read this session) and `gates/flows.py` lines 320-412 (read
this session) — the issue-27 example is quoted verbatim from the issue body.

Reproduces the issue's own example (issue-27: `implementation` has a merged/board-recorded
PR — absent from the open-PR list — while `execution-observation` (#31) and
`conformance-review` (#32) are open with no board record yet) against the shipped,
unmodified `gates/flows.py` at current HEAD (`git log --oneline -1` → bc53410e, read this
session). The fix landed in PR #252 (merge commit 3c27dc94) and remains present unchanged on
`main` (`grep -n "prs_by_subject" gates/flows.py`, read this session, shows the same
subject-grouped dict introduced by that PR).

Driver script (`/tmp/eo_248_drive.py`, run this session via `python3 /tmp/eo_248_drive.py`):

```python
import sys, tempfile, json
from pathlib import Path

sys.path.insert(0, "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-248-execution-observation")
import spawn
sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
import flows

td = tempfile.TemporaryDirectory()
root = Path(td.name)

spawn.ROOT = root
spawn._repo_slug = lambda root: "acme/repo"
spawn._issue_comments = lambda root, n: ([], True)
spawn._roster_load = lambda: {}
flows._issue_list_all = lambda root: ([], True)

rec = root / spawn.BOARD / "issue-27" / "reports"
rec.mkdir(parents=True, exist_ok=True)
(rec / "implementation.md").write_text("---\nloop_state: scope-approved\n---\n", encoding="utf-8")

flows._pr_list_all = lambda root: ([
    {"number": 31, "headRefName": "issue-27/execution-observation",
     "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
    {"number": 32, "headRefName": "issue-27/conformance-review",
     "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
], True)

payload = flows.flows_payload(root)
by_issue = {f["issue"]: f for f in payload["flows"]}
dq = [d for d in payload["decision_queue"] if d["issue"] == 27]

print("flows[27].prs =", by_issue[27]["prs"])
print("decision_queue (issue 27) =", dq)
assert by_issue[27]["prs"] == [31, 32], "flows[].prs not populated as issue #248 requires"
assert {d["pr"] for d in dq}.issubset(set(by_issue[27]["prs"])), "decision_queue/flows[].prs mismatch"
print("PASS: flows[].prs matches decision_queue's PR source, issue #248 fixed on shipped code")
```

canonical: this driver script's own stdout, captured verbatim below (run this session,
`python3 /tmp/eo_248_drive.py`) — not a summary, the actual printed lines.

Output:

```
flows[27].prs = [31, 32]
decision_queue (issue 27) = [{'issue': 27, 'pr': 32, 'phase': 1, 'role': 'conformance-review', 'opened_at': '2026-07-30T00:00:00Z', 'age_hours': 365.0, 'awaiting': 'approve-scope'}, {'issue': 27, 'pr': 31, 'phase': 1, 'role': 'execution-observation', 'opened_at': '2026-07-30T00:00:00Z', 'age_hours': 365.0, 'awaiting': 'approve-scope'}]
PASS: flows[].prs matches decision_queue's PR source, issue #248 fixed on shipped code
```

`flows[27].prs == [31, 32]` — non-empty, and a superset of `decision_queue`'s PR set for the
same issue (`{31, 32}` ⊆ `{31, 32}`) — matching the issue's own acceptance criteria 1 and 2
against the real-world issue-27 scenario the issue report cited as the reproducing case.

## Shipped test suite

canonical: `git diff c0daeab1~1 892cfeea -- tests/test_spawn.py` and the pytest run below
(both read/run this session).

The implementation PR (#252) added two regression tests to `tests/test_spawn.py`'s
`FlowsPayload` class: `test_flows_prs_includes_open_prs_for_roles_with_no_board_record` and
`test_flows_prs_and_decision_queue_share_the_same_pr_set`. Re-ran the full class against the
current shipped code:

```
$ python3 -m pytest tests/test_spawn.py -k "FlowsPayload" -v
...
tests/test_spawn.py::FlowsPayload::test_flows_prs_and_decision_queue_share_the_same_pr_set PASSED
tests/test_spawn.py::FlowsPayload::test_flows_prs_includes_open_prs_for_roles_with_no_board_record PASSED
...
19 passed, 484 deselected in 0.24s
```
