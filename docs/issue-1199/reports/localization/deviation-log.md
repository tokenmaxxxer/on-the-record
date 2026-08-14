# Deviation log (issue-1199, localization)

- 2026-08-13T17:10 filed: pr-preflight retry loop on issue-1199
  (localization) — recurring generic judgment-watcher comments post
  faster than PR-create attempts can reconcile them; commit 3aa83e2
  (branch issue-1199/localization) is pushed and represents the final
  content state for this session; PR-create is deferred to relay, per
  the same-shaped precedent commit 8bf080a on this issue ("stop
  pr-preflight retry loop, final record state for this session").
  reported, not spawned.

- 2026-08-14T01:45 filed: pr-preflight retry loop recurs on issue-1199
  (localization) plugin-ecosystem rework — the same generic
  judgment-watcher comment (issuecomment-5288371026, then
  issuecomment-5288375802) posted again between reconcile and
  PR-create; commit 655ee9783f96ed4ae78dee5248b68f5991789578 (branch
  issue-1199/localization) is pushed and represents the final content
  state for this session; PR-create is deferred to relay, same-shaped
  precedent as the entry above. reported, not spawned.
