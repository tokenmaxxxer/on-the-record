canonical: docs/issue-2201/reports/implementation/2026-08-24-hunt-bootstrap-cross-family-returned-pr-gate.md
(commit 6dcf38a7b9f5d5d99b8f2a43cc2e240b643214e1), this session's own
before-landing warrant-hunt and its repro script output — the
`returned_pr_gate` daemon thread the first cut of this issue's fix
dispatched is killed by `sys.exit()` before it can finish in the real
bounded `--issue` CLI path (fork-then-fast-return, issue #114/#1154),
so the fix's own stated non-blocking-not-dropped guarantee did not
actually hold there.
2026-08-24T22:33:00Z inline spawn.py (~line 2846-2861, commit
f45266081b371b249da44730183916e8b3077bcc's original shape, fixed on top
same session): added `_returned_pr_gate_thread.join(timeout=10.0)`
immediately before the bounded parent's one `return 0`, restoring the
surfacing/ledger side effect the fire-and-forget conversion had put at
risk; verified both directions via `tests/test_spawn_gate_wiring.py`'s
new ReturnedPRGateIsNonBlocking.test_bounded_fork_parent_join_still_captures_a_slow_lookup
test (added same commit). This same pre-fork/daemon-thread-dies shape likely
recurs for issue #2195's `auto_sweep` dispatch — recorded as Open
finding 1 in docs/issue-2201/reports/implementation.md rather than
filed as a separate issue, since fixing it there is outside this
issue's named scope.
