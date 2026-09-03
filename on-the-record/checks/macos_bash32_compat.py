#!/usr/bin/env python3
"""issue #2924: the standing check for macOS/bash-3.2 platform divergence.

No check anywhere in this repo ran on macOS or on bash 3.2 (Linux bash 5.x
tolerates unset-array expansion and ships `flock`/`stat -c`/GNU `sed`;
Linux has `/proc`), so every prior check passed green while the macOS path
was degraded or dead -- that is how #2919's two failures (unguarded
`flock`, a bash-3.2 unbound-array expansion) shipped with a full green
suite. This is a purely static, dependency-free lint over the population
`git ls-files '*.sh' '*.py'` bounded to live code (`docs/` and test paths
excluded, matching the population #2919/#2924 already enumerated) --
cheap enough to run on every `pytest` invocation and quiet on a clean
pass, per the issue's must-not ("so slow or noisy it gets disabled").

Two rule families:

1. `check_sh_file()` -- GNU-only constructs with no portable fallback:
   - `flock` invoked anywhere in the file without a `command -v flock`
     guard present in the same file (the exact #2919 shape: util-linux's
     `flock` is absent on macOS by default).
   - `stat -c` on a line that does not also carry a `stat -f` BSD
     fallback on the SAME line (the portable idiom already used by
     `on-the-record/hooks/decision-queue-stopgate.sh`).
   - `sed -i`, `date -d`, `readlink -f`, `grep -P` -- zero live sites as
     of this check's authoring; any live sh file using one is flagged
     with no fallback-recognition (no precedent for what "portable" looks
     like for these yet).
   - `"${arr[@]}"` (or `${arr[@]}"` etc.) expanded on a line, in a file
     that also sets `-u`/`-o nounset`, without the bash-3.2-safe
     `${arr[@]+"${arr[@]}"}` guard marker (`[@]+`) present on that same
     line -- the exact #2919 shape: bash 3.2 treats even a genuinely
     empty/unset array as unbound under `set -u` when expanded plainly.

2. `check_py_file()` (via `KNOWN_PROC_SITES`) -- a `/proc/` reference in a
   live .py file outside the already-reviewed set (roster.py, watchdog.py
   -- see docs/issue-2924/reports/) is flagged: a new `/proc` dependency
   must be either made portable or given a runtime-visible degradation
   notice (not just a docstring) before it is added to the reviewed set.
   This is enumeration + an allowlist, not a portability check -- Python's
   `/proc` guards are deliberately NOT weakened on Linux (must-not: parity
   by removing the stronger guard is not parity).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_TEST_PATH_RE = re.compile(
    r"(^|/)(test|tests)/|(^|/)test_[^/]*\.py$|_test\.py$"
)

# issue #2924: roster.py (`_watcher_looks_real`, `_session_looks_real`) and
# watchdog.py (`_proc_start_time`) are the reviewed, runtime-visible /proc
# identity sites (docs/issue-2924/reports/silent-failure-audit+
# refactoring-legacy-seam-selection-140f0858.md). board.py's /proc mention
# is prose about a mechanism that does not exist yet, not a live call.
# `monitor_ownership.py` (issue #3293) reads /proc for the start-tick half
# of a monitor's owner token. Where there is no /proc the token degrades
# to `<pid>.nostat` and every stop attempt is refused with that named
# reason rather than signalling a pid it cannot prove identity for --
# a runtime-visible degradation, not a silent one. Stage 3 owes macOS a
# working stop path built on something other than the start tick.
KNOWN_PROC_SITES = {"roster.py", "watchdog.py", "monitor_ownership.py"}

_FLOCK_INVOKE_RE = re.compile(r"(^|[^\w#])flock(\s|$)")
_FLOCK_GUARD_RE = re.compile(r"command\s+-v\s+flock")
_STAT_C_RE = re.compile(r"\bstat\s+-c\b")
_STAT_F_RE = re.compile(r"\bstat\s+-f\b")
_ARRAY_BARE_RE = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\[@\]\}")
_ARRAY_GUARD_MARK = "[@]+"
_SET_U_RE = re.compile(
    r"^\s*set\s+-[a-zA-Z]*u[a-zA-Z]*\b|^\s*set\s+-o\s+nounset\b", re.MULTILINE
)
_GNU_ONLY_BARE = {
    "sed -i": re.compile(r"\bsed\s+-i\b"),
    "date -d": re.compile(r"\bdate\s+-d\b"),
    "readlink -f": re.compile(r"\breadlink\s+-f\b"),
    "grep -P": re.compile(r"\bgrep\s+(-\w*P\w*|--perl-regexp)\b"),
}
# Only a `/proc/` immediately inside a string literal counts as a real
# dependency -- a backtick-quoted `` `/proc/<pid>` `` mention in Korean
# prose/docstring (e.g. board.py's documented-but-not-yet-built mechanism)
# is not a live call and must not be flagged as one.
_PROC_RE = re.compile(r"[\"']/proc/")


def is_live(path: str) -> bool:
    if path.startswith("docs/"):
        return False
    return not _TEST_PATH_RE.search(path)


def list_population(repo_root: Path = REPO_ROOT) -> tuple[list[str], list[str]]:
    out = subprocess.run(
        ["git", "ls-files", "*.sh", "*.py"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout
    files = [p for p in out.splitlines() if p]
    live = [p for p in files if is_live(p)]
    sh = sorted(p for p in live if p.endswith(".sh"))
    py = sorted(p for p in live if p.endswith(".py"))
    return sh, py


def _code_lines(content: str) -> list[tuple[int, str]]:
    out = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.append((i, line))
    return out


def check_sh_file(path: str, content: str) -> list[str]:
    violations: list[str] = []
    lines = _code_lines(content)
    has_flock_guard = bool(_FLOCK_GUARD_RE.search(content))
    has_set_u = bool(_SET_U_RE.search(content))
    for lineno, line in lines:
        if _FLOCK_INVOKE_RE.search(line) and not has_flock_guard:
            violations.append(
                f"{path}:{lineno}: `flock` used without a `command -v flock` "
                "guard anywhere in the file -- absent on macOS by default "
                "(issue #2919 shape)"
            )
        if _STAT_C_RE.search(line) and not _STAT_F_RE.search(line):
            violations.append(
                f"{path}:{lineno}: `stat -c` with no `stat -f` BSD fallback "
                "on the same line -- BSD/macOS stat has no -c"
            )
        if (
            _ARRAY_BARE_RE.search(line)
            and _ARRAY_GUARD_MARK not in line
            and has_set_u
        ):
            violations.append(
                f'{path}:{lineno}: "${{arr[@]}}" expanded under set -u/-o '
                'nounset without the ${arr[@]+"${arr[@]}"} bash-3.2-safe '
                "guard -- an empty/unset array is unbound under bash 3.2 "
                "(issue #2919 shape)"
            )
    for label, rx in _GNU_ONLY_BARE.items():
        for lineno, line in lines:
            if rx.search(line):
                violations.append(
                    f"{path}:{lineno}: GNU-only `{label}` with no recognized "
                    "portable fallback on this line"
                )
    return violations


def check_py_file(path: str, content: str) -> list[str]:
    hits = []
    for lineno, line in _code_lines(content):
        if _PROC_RE.search(line):
            hits.append(f"{path}:{lineno}")
    return hits


def run(repo_root: Path | None = None, verbose: bool = False) -> tuple[bool, str]:
    root = repo_root or REPO_ROOT
    sh_files, py_files = list_population(root)

    violations: list[str] = []
    for rel in sh_files:
        content = (root / rel).read_text(encoding="utf-8", errors="replace")
        violations.extend(check_sh_file(rel, content))

    proc_hits: list[str] = []
    for rel in py_files:
        content = (root / rel).read_text(encoding="utf-8", errors="replace")
        hits = check_py_file(rel, content)
        proc_hits.extend(hits)
        if hits and Path(rel).name not in KNOWN_PROC_SITES:
            violations.append(
                f"{rel}: new /proc dependency outside the reviewed set "
                f"{sorted(KNOWN_PROC_SITES)} -- must be made portable or "
                "given a runtime-visible degradation notice, then added "
                "to KNOWN_PROC_SITES"
            )

    proc_files = sorted({h.split(":")[0] for h in proc_hits})
    lines = [
        f"[macos-bash32-compat] population: {len(sh_files)} live .sh, "
        f"{len(py_files)} live .py (git ls-files '*.sh' '*.py' minus docs/ "
        "and test/tests paths)",
        f"[macos-bash32-compat] /proc dependency sites: {len(proc_hits)} "
        f"occurrence(s) in {len(proc_files)} file(s): "
        f"{', '.join(proc_files) if proc_files else 'none'}",
    ]

    ok = not violations
    if ok and not verbose:
        return True, ""
    if not ok:
        lines.append(f"[macos-bash32-compat] FAIL -- {len(violations)} violation(s):")
        lines.extend(f"  {v}" for v in violations)
    else:
        lines.append("[macos-bash32-compat] PASS")
    return ok, "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    verbose = "--verbose" in argv or "-v" in argv
    ok, report = run(verbose=verbose)
    if report:
        print(report, file=sys.stderr if not ok else sys.stdout)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
