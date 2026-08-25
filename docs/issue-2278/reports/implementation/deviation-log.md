# Deviation log — issue-2278 (implementation role)

- 2026-08-25T01:38:00Z | inline | before-landing `warrant-hunter` dispatch (stance 0, "find the bypass") on the check_runner classifier-default-inversion diff found `_looks_like_path` had no fallback for bare, extensionless conventional filenames (`LICENSE`, `Makefile`, `Dockerfile`, ...) or dotfiles (`.gitignore`, ...) — these silently downgraded to `judgment` instead of staying `file-existence` and genuinely FAILing when absent, undermining the issue's own "genuine missing path-shaped artifacts still FAIL" requirement.
acceptance: docs/issue-2278/reports/implementation/2026-08-25-hunt-check-runner-classifier-default-inversion.md "Stance 0" section — result:
```
classified as: judgment (before fix)
mechanical results (LICENSE never created in td): []   # never checked at all
```
acceptance: git diff gates/check_runner.py (commit b4b15c98) — result:
```
first pass: _looks_like_path(token) = "/" in token or known .-delimited extension only
gap: bare filenames (LICENSE, Makefile, ...) and dotfiles (.gitignore, ...) have neither -> wrongly classified judgment
fixed: same commit b4b15c98, inline, within the frozen write set (gates/check_runner.py + gates/test_check_runner.py), mechanical, one-off — added _BARE_PATH_NAMES allowlist + leading-"." check to _looks_like_path
```
