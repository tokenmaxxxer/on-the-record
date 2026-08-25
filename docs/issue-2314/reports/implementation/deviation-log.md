# Deviation log — issue-2314 (implementation role)

canonical: `69a26bc7:gates/stale_revert_guard.py`, `69a26bc7:docs/issue-2314/reports/implementation/2026-08-25-hunt-binary-file-crash-fix.md`, full narrative in `docs/issue-2314/reports/implementation.md` ("What did not work" / "Rationale for deviations")

- 2026-08-25T03:30:00Z | inline | issue asks `_git_show()` to fall back to `""` on decode failure; a before-landing warrant-hunt (stance 0) found that literal fallback silently converts a genuine stale revert into ALLOW for non-UTF-8-but-git-non-binary content — switched the fallback to `errors="surrogateescape"` instead. Location: `gates/stale_revert_guard.py:_git_show()`, commit `69a26bc7`.
- 2026-08-25T03:35:00Z | inline | the `surrogateescape` switch above made `_merge_file()` (writes/reads those same strings via strict-UTF-8 `write_text`/`text=True`) raise `UnicodeEncodeError` on a lone surrogate — hardened its I/O to the same `surrogateescape` round-trip. Outside the issue's two named functions but same file/write set, required for the fix above to actually hold. Location: `gates/stale_revert_guard.py:_merge_file()`, commit `69a26bc7`.
