"""Reconstructed pre-repair shape (issue #3228 site 6) of the evidence
scripts/issue-3127/run_consumer_pair.py's original design read to decide
whether a spawned session invoked a skill: a `Skill: <name>` line the
SPAWNED process's own Bash tool_use output could contain -- see
scripts/consumer-path/verify_manipulation.py's module docstring
("issue #3127's PR #3180 already demonstrated this live for the
previous design's own signal"). No subprocess call in this shape --
DOCUMENTED MISS: this is a trust/evidence-provenance defect (who could
have written this data), not an observation the chosen mechanism
(subprocess timeout/returncode) reasons about at all -- no syntactic
AST pattern distinguishes "evidence the process under test could forge"
from "evidence only a trusted launcher could have written"; that
distinction lives in which process opened which file, not in this
file's text."""
from __future__ import annotations

import re

_SKILL_LINE_RE = re.compile(r"^Skill:\s*(\S+)\s*$", re.MULTILINE)


def skill_was_invoked(spawned_process_log: str, expected_skill: str) -> bool:
    """`spawned_process_log` is text the SPAWNED session's own Bash
    output stream produced -- nothing stops that same process from
    printing this line itself whether or not it actually invoked the
    skill."""
    m = _SKILL_LINE_RE.search(spawned_process_log)
    return bool(m and m.group(1) == expected_skill)
