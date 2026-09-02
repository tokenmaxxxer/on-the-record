"""Reconstructed pre-repair shape (issue #3228 site 7) of
on-the-record/hooks/amendment_channel.py's success check: text came from
a generic string-or-json-dumps coercion, and the URL match used
`.search()` (anywhere in the text) instead of `.fullmatch()`. A real
Bash `tool_response` is a dict; `json.dumps()`-wrapping it means the
success URL is never a bare, unwrapped string, so `.search()` (which
*could* still match a URL-shaped substring buried in JSON punctuation or
inside a failed edit's own error text) was the only thing standing
between "no signal" and "a false positive" -- and 79 hand-written string
fixtures never exercised the dict shape a real payload actually has, so
the gap went unnoticed. No subprocess call in this shape -- DOCUMENTED
MISS: this is a test-fixture/payload-shape defect (candidate (d) in the
issue, not the chosen mechanism), invisible to a subprocess-observation
lint."""
from __future__ import annotations

import json
import re

_ISSUE_URL_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)\b")


def _old_response_text(tool_response: object) -> str:
    if isinstance(tool_response, str):
        return tool_response
    try:
        return json.dumps(tool_response)
    except TypeError:
        return ""


def issue_url_from_response(tool_response: object):
    text = _old_response_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.search(text)
    if not m:
        return None
    return "%s/%s" % (m.group(1), m.group(2)), m.group(3)
