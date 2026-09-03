"""Real pre-repair shape (issue #3228 site 7), verbatim from
on-the-record/hooks/amendment_channel.py and hook_input.py at commit
f699f5c6^ (the parent of f699f5c6 "issue-3129: round-7 fix -- real Bash
tool_response shape + fixture blind spot", `git show f699f5c6^:...`) --
replacing a round-2 reconstruction that implemented a DIFFERENT,
already-fixed bug (round 5's `.search()` vs `.fullmatch()`, fixed two
rounds before this one) rather than the one issue #3228 actually cites.

Round 5 had already switched to `.fullmatch()` (the positive
success check the `history_after` fixture also uses) by this point; the
defect issue #3228 names -- "a success check that never matched the real
payload shape passed all seventy-nine of its tests, because every
fixture was hand-written in a shape the real system never produces" --
is `_issue_url_from_response` reading its text through
`hook_input.tool_response_text()`, which `json.dumps()`-wraps a real
Bash `tool_response` dict whole. A real `tool_response` is
`{"stdout": ..., "stderr": ..., ...}`, so the JSON-wrapped text
(`'{"stdout": "https://...", ...}'`) can never `fullmatch` the bare URL
pattern -- the positive check `fullmatch` was supposed to make strict
instead silently never fired for a single real `gh issue edit` call,
success or failure, while all 79 hand-built *string* `tool_response`
fixtures (never a dict) passed. PR #3205 captured the real payload shape
live and found this; round 7 (`f699f5c6`) fixed it by reading through
`_response_stdout_text()` (the `history_after` fixture) instead. No
subprocess call in this shape -- DOCUMENTED MISS: this is a test-fixture/
payload-shape defect (candidate (d) in the issue, not the chosen
mechanism), invisible to a subprocess-observation lint."""
from __future__ import annotations

import json
import re

_ISSUE_URL_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)\b")


def _old_tool_response_text(raw: object) -> str:
    """Verbatim from hook_input.py's `tool_response_text` at f699f5c6^:
    a dict `tool_response` (a real Bash payload's actual shape) is
    `json.dumps()`-wrapped whole, not read through its own `stdout`
    field."""
    if isinstance(raw, str):
        return raw
    if raw is None:
        return ""
    try:
        return json.dumps(raw)
    except (TypeError, ValueError):
        return ""


def issue_url_from_response(tool_response: object):
    text = _old_tool_response_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.fullmatch(text.strip())
    if not m:
        return None
    return "%s/%s" % (m.group(1), m.group(2)), m.group(3)
