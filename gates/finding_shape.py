"""domain-finding shape checker (issue #1202 requirement 2).

A role session that discovers a domain problem in its own domain records
it as a structured finding file under
`docs/reports/findings/<role>/<date>-<slug>.md` (or the per-issue
variant `docs/issue-<n>/reports/findings/<role>/...`) — never a direct
`gh issue`. The validity-consult that approved this issue's requirement
2 made evidence mandatory: a finding without a playbook citation and
without evidence in the target repo is not a finding, it is an opinion.

Hand-rolled frontmatter/body parsing, same family as
`gates/role_spec_shape.py` (`check(spec) -> list[str]`, empty = pass) —
no new dependency for a shape this simple.

  python3 gates/finding_shape.py docs/reports/findings/<role>/<date>-<slug>.md
  exit 0 pass / 1 fail (prints reasons to stderr)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

_REQUIRED_FRONTMATTER = ("role", "date", "domain_rule", "target_repo")
_REQUIRED_SECTIONS = ("Evidence", "Impact", "Proposed direction")

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """`(frontmatter_dict, body)`. A file with no `---` fence returns an
    empty frontmatter dict and the whole text as body — the caller's
    missing-key checks then fail it, same fail-closed shape
    `record_lint.py`'s parsers use."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2)
    fm: dict[str, str] = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, body


def _section_body(body: str, heading: str) -> str:
    """Text under `## <heading>` up to the next `##` heading or EOF —
    empty string when the heading is absent or has no non-blank content
    under it."""
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", body, re.MULTILINE)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    section = rest[:nxt.start()] if nxt else rest
    return section.strip()


def check_finding(path: str | Path) -> list[str]:
    """Reasons `path` fails the finding shape check. Empty list = pass.

    Rejects: missing/empty `domain_rule` frontmatter (the playbook
    citation), missing/empty `## Evidence` body (the target-repo
    evidence), missing/empty `## Impact`, missing/empty
    `## Proposed direction` — the four fields requirement 2's shape gate
    names as mandatory."""
    p = Path(path)
    if not p.is_file():
        return [f"file does not exist: {p}"]
    text = p.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)

    bad = []
    for key in _REQUIRED_FRONTMATTER:
        if not fm.get(key):
            bad.append(f"missing/empty frontmatter key: {key}")

    for heading in _REQUIRED_SECTIONS:
        if not _section_body(body, heading):
            bad.append(f"missing/empty section: ## {heading}")

    return bad


def session_summary_path(findings_root: Path, role: str, date: str) -> Path:
    """`docs/reports/findings/<role>/<date>-session-summary.md` — where a
    session's findings beyond the rate bound go instead of a new finding
    file (requirement 3), one bare-marker-style line per further
    finding, mirroring the record-tiering directive's "no padding"
    shape already in force for `## What did not work`."""
    return findings_root / role / f"{date}-session-summary.md"


def check_rate_bound(findings_root: Path, role: str, session_id: str,
                      bound: int = 3) -> str | None:
    """`None` when this session is still under `bound` findings filed for
    `role` (the write may proceed); otherwise a reject reason naming the
    summary-line path the session must use instead.

    Counts only finding files already written this session — matched via
    an optional `session:` frontmatter field a role session stamps into
    every finding it writes. Per-session, not cumulative against the
    standing queue: a fresh `session_id` gets a fresh bound (proposal
    §4 — the bound forces depth-over-volume triage within one look, not
    a cap on total queue size)."""
    role_dir = findings_root / role
    if not role_dir.is_dir():
        return None
    count = 0
    for p in role_dir.glob("*.md"):
        if p.name.endswith("-session-summary.md"):
            continue
        fm, _ = _parse_frontmatter(p.read_text(encoding="utf-8"))
        if fm.get("session") == session_id:
            count += 1
    if count >= bound:
        summary = session_summary_path(findings_root, role, "<date>")
        return (f"session bound N={bound} reached for role {role!r} — "
                f"append a summary line to {summary} instead of a new finding file")
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <finding-path>", file=sys.stderr)
        return 2
    bad = check_finding(argv[1])
    if bad:
        for reason in bad:
            print(f"REJECT: {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
