Subject: issue-1554

- 2026-08-15T00:00:00Z inline gates/test_closure_sweep.py::test_sweep_gh_call_count_is_constant_in_board_size updated (whitelist gh repo view + bump expected call count 2->3, clear repo-slug cache per iteration) because issue_state_index_all now probes the repo slug once to attempt an ETag-conditional list before falling back — still O(1) in board size, contract preserved, only the constant shifted.
