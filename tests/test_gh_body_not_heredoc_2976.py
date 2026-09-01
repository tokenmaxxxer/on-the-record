"""Issue #2976 acceptance test: callers that pass a long body to `gh` use
a file or stdin path rather than a heredoc, so
`heredoc-command-refusal-gate.sh` has nothing to refuse.

A live spawned session hit this gate mid-session (issue #2976's own
report): `gh ... --body "$(cat <<EOF ... EOF)"` is exactly the shape the
gate refuses (issue #1976). No caller in this repo constructs that shape
today -- every production `gh issue|pr create|comment` call already goes
through `subprocess.run([...])` argv lists (spawn.py, relay.py,
gates/check_runner.py), never a shell heredoc. This test locks that state
in mechanically instead of leaving it as an unverified impression, and
catches the moment a future caller reintroduces the heredoc-shaped
`--body`/`--body-file` construction the gate refuses.

  python3 -m pytest tests/ -k gh_body_not_heredoc -q
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories excluded from the scan: docs/tests describe or exercise the
# refused shape on purpose (docs explain the gate, hook tests fabricate
# refused payloads to prove the gate catches them) -- neither is a live
# caller that would actually run the command. `runs/` is the gitignored
# mounted-plugin checkout (`.gitignore` root entry) -- infrastructure this
# PR does not own or ship, not this repo's own source tree.
_EXCLUDED_DIR_PARTS = {".git", "docs", "test", "tests", "runs"}

# Hook scripts that legitimately carry this exact shape in their own
# detection regex/comments, in service of refusing or describing it --
# never running it. Matching here is the evidence the gate/allow-path
# works, not a live caller to fix.
_ALLOWED_MENTIONS = {
    REPO_ROOT / "on-the-record" / "hooks" / "pr-preflight.sh",
    REPO_ROOT / "on-the-record" / "hooks" / "gh-write-allow-gate.sh",
}

# The anti-pattern itself: a `gh ... --body`/`--body-file` argument built
# from a `$(cat <<DELIM ... DELIM)` command substitution -- the shape
# issue #1976's gate refuses. `\s` already spans newlines, so this
# matches across the heredoc's opening line without needing re.DOTALL.
_HEREDOC_BODY = re.compile(r"--body(?:-file)?[\s=]*\"?\$\(\s*cat\s+<<")


def _scanned_files():
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in (".py", ".sh"):
            continue
        if any(part in _EXCLUDED_DIR_PARTS for part in path.relative_to(REPO_ROOT).parts):
            continue
        yield path


class GhBodyNotHeredocTest(unittest.TestCase):
    def test_no_caller_builds_a_heredoc_shaped_gh_body(self):
        offenders = []
        for path in _scanned_files():
            if path in _ALLOWED_MENTIONS:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if _HEREDOC_BODY.search(text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            offenders, [],
            f"caller(s) build a gh --body/--body-file argument from a "
            f"heredoc command substitution: {offenders} -- "
            f"heredoc-command-refusal-gate.sh refuses exactly this shape "
            f"(issue #1976). Use --body-file <path>, or --body-file - "
            f"with the body piped on stdin, instead (issue #2976).")


if __name__ == "__main__":
    unittest.main()
