#!/usr/bin/env python3
"""Issue-authoring gate — flags an `## Acceptance` bullet that requires an
action the delivering role is categorically forbidden from taking
(issue #2503, #2479 R3).

#2479's original R3 bullet read "file that as a separate follow-up issue
and link it here". No role session can create a GitHub issue — `gh-guard`
refuses it (contract v3 s8/s9: issues are the user's requirement backlog,
user-authored only). The bullet was unsatisfiable by construction: the
delivering session did the honest thing (drafted the body, logged a
deviation, named it for the orchestrator) and the gate still marked the
requirement short.

This gate looks for a file/open/create verb paired with issue/ticket
inside the Acceptance section. It does not flag a bullet that merely
mentions or links an issue number (no verb attached), and it does not
flag a bullet that explicitly reassigns the action to the orchestrator,
the operator, or another non-role account — that is the sanctioned shape
("name the follow-up ... the orchestrator files it").

  python3 gates/forbidden_action_rule.py <issue-number> [--repo <path>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")

# A verb obligating someone to act on an issue/ticket, within a short
# window of the noun — "file that as a ... issue", "open a ticket",
# "create an issue". Deliberately narrow to the "file/create an issue"
# obligation shape named by #2503's Acceptance — a bare mention or link
# of an issue number carries no verb and never matches.
_FORBIDDEN_ACTION = re.compile(
    r"\b(?:file|filing|filed|open|opening|opened|create|creating|created"
    r"|raise|raising|raised)\b(?:(?![.\n]).){0,60}?\b(?:github\s+)?"
    r"(?:issue|ticket)s?\b",
    re.IGNORECASE,
)

# The same obligation is fine when it names someone other than the
# delivering role as the actor — the sanctioned rewrite for the
# follow-up case.
_ROLE_REASSIGNED = re.compile(
    r"orchestrator|\boperator\b|\bhuman\b|non-role|not (?:this|the deliver"
    r"ing) role|not by (?:this|the) (?:role|session)|different account"
    r"|the user files|filed by",
    re.IGNORECASE,
)


def _acceptance_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


def check_issue_body(issue: int, body: str) -> list[str]:
    """Judge from issue body text alone (no network, easy to test).

    No `## Acceptance` section means there is nothing for this gate to
    judge, so it returns an empty list — this gate does not judge
    section presence, only the attribution of an obligation already
    inside the section (`acceptance_gate.py` already owns presence).
    """
    body = body or ""
    section = _acceptance_section(body)
    if section is None:
        return []

    bad = []
    for m in _FORBIDDEN_ACTION.finditer(section):
        window_start = max(0, m.start() - 200)
        window_end = min(len(section), m.end() + 200)
        window = section[window_start:window_end]
        if _ROLE_REASSIGNED.search(window):
            continue
        line_end = section.find("\n", m.end())
        line = section[section.rfind("\n", 0, m.start()) + 1:
                        line_end if line_end != -1 else len(section)]
        bad.append(
            f"issue #{issue}'s 'Acceptance' bullet requires an action the "
            f"delivering role is forbidden from taking ({line.strip()!r}) "
            f"— gh-guard refuses issue creation for every role session "
            f"(contract v3 s8/s9: issues are the user's requirement "
            f"backlog, user-authored only). Rewrite with the sanctioned "
            f"follow-up wording: 'name the follow-up with a drafted body "
            f"in `## Open findings`; the orchestrator files it.'"
        )
    return bad


def _issue_view_body(repo: Path, issue: int) -> str | None:
    r = subprocess.run(["gh", "issue", "view", str(issue), "--json", "body"],
                        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    data = json.loads(r.stdout)
    return data.get("body", "")


def check(repo: Path, issue: int) -> list[str]:
    body = _issue_view_body(repo, issue)
    if body is None:
        return [f"could not read issue #{issue}'s body (`gh issue view` "
                f"failed) — unable to check is not a pass."]
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: forbidden_action_rule.py <issue-number> [--repo <path>]")
        return 1
    try:
        issue = int(sys.argv[1])
    except ValueError:
        print(f"usage: forbidden_action_rule.py <issue-number> [--repo <path>] "
              f"— issue-number must be an integer, got {sys.argv[1]!r}")
        return 1
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    bad = check(repo, issue)
    if not bad:
        print("gate passed")
        return 0
    print("gate blocked:")
    for b in bad:
        print(f"  - {b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
