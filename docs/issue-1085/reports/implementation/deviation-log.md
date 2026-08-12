canonical: core/hooks/board-gate.sh:553, read this session — `deny("writing docs/%s/
requires branch %s (current: %s). ...")` fires unconditionally for any docs/issue-<n>/ write
whose branch != issue-<n>/<role>, no exception path.
2026-08-12T00:00:00Z filed board-gate.sh (core/hooks/board-gate.sh R4) refused a
docs/issue-1062/** write attempted from branch issue-1085/implementation — the approved
proposal (docs/issue-1085/proposals/git-tracked-canonical-path-gate.md) planned to correct
docs/issue-1062/reports/implementation.md's two false citations from this branch in the same
commit as the new gate check; that write is not mechanically possible here. reported, not
spawned.
