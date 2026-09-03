"""Real repaired code (issue #3228 site 7), verbatim excerpt from the
current on-the-record/hooks/amendment_channel.py: `_response_stdout_text`
reads a real Bash `tool_response` dict's own `stdout` field directly
(never json.dumps()-wrapped), and the URL check is a positive
`.fullmatch()` against the stripped text, not a `.search()` that could
match a URL-shaped substring anywhere."""
from __future__ import annotations

import re
from typing import NamedTuple, Optional

_ISSUE_URL_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)\b")


def _response_stdout_text(tool_response: object) -> str:
    if isinstance(tool_response, dict):
        stdout = tool_response.get("stdout")
        return stdout if isinstance(stdout, str) else ""
    if isinstance(tool_response, str):
        return tool_response
    return ""


class _IssueUrl(NamedTuple):
    repo: str
    issue: str


def issue_url_from_response(tool_response: object) -> Optional[_IssueUrl]:
    text = _response_stdout_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.fullmatch(text.strip())
    if not m:
        return None
    owner, repo, issue = m.group(1), m.group(2), m.group(3)
    return _IssueUrl("%s/%s" % (owner, repo), issue)
