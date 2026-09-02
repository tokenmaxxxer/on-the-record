"""Issue #3050: the sanctioned shape for a correction round that cannot
write into the record it is correcting.

`board-gate.sh`'s write-set isolation (contract v3 s11) resolves ownership
from the writing session's own project root, not from the path being
written -- confirmed live across three write shapes (in-place edit,
revert, append-only) on PR #2872's branch (issue #3050 root-cause comment).
No write shape reaches another session's record. This module does not try
to relax that boundary; it gives the round that follows a shape that does
not need to.

**Decision: two artifacts, not one.** A correcting session can only ever
write its own record (its own `docs/issue-<n>/reports/<skill>.md`), never
the record it is correcting -- so "exactly one artifact survives" was
rejected outright: the only way to leave one artifact would be to edit or
delete the original, and every write shape that reaches it is denied.
The correcting session instead writes its own record and marks, inside
that new file's own frontmatter, which prior record it supersedes. A
reader with only the merged tree -- no PR body, no issue comment -- finds
this by reading the correction's frontmatter, not by cross-referencing
anything external.

The marker is a `supersedes:` frontmatter field (same block the
record-shape directive already mandates `code_under_review:`/
`loop_state:`/`type:`/`breaking:`/`verdict:` in), naming the path it
corrects:

    ---
    supersedes: docs/issue-9101/reports/coding.md  # three fabricated figures
    ...
    ---

`resolve_authoritative()` is the reader-side half: given every record's
raw content (no git, no network, no PR/issue metadata -- content strings
only), it decides which paths are authoritative purely from what is
written in the tree.
"""
from __future__ import annotations

import re

_FRONTMATTER_DELIM = "---"
_SUPERSEDES_RE = re.compile(r"(?m)^supersedes:\s*(\S+)")


def render_supersedes_field(target_path: str, reason: str) -> str:
    """The exact frontmatter line a correcting session's own record adds
    to mark itself as the correction of `target_path`. `reason` travels as
    a YAML comment on the same line -- visible to a plain-text reader of
    the tree, not parsed back out by `parse_supersedes()`."""
    return f"supersedes: {target_path}  # {reason}"


def _frontmatter_block(content: str) -> str | None:
    lines = content.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == _FRONTMATTER_DELIM:
            return "\n".join(lines[1:i])
    return None          # opening delimiter with no close -- not a record


def parse_supersedes(content: str) -> str | None:
    """The path this record's own frontmatter declares it supersedes, or
    None when the record carries no such field (the common case -- most
    records supersede nothing)."""
    fm = _frontmatter_block(content)
    if fm is None:
        return None
    m = _SUPERSEDES_RE.search(fm)
    return m.group(1) if m else None


def resolve_authoritative(records: dict[str, str]) -> dict:
    """Decide, from `records` (path -> full file content) alone, which
    paths are authoritative -- the reader-with-only-the-merged-tree test
    issue #3050's acceptance amendment names.

    Returns a dict with four keys:
      - `authoritative`: sorted paths no other record's `supersedes:`
        names, and that are not part of a `conflicts` entry (see below).
      - `superseded`: {original_path: corrector_path} -- unambiguous
        cases, exactly one record supersedes that original.
      - `broken`: sorted `supersedes:` targets that name a path absent
        from `records` -- a dangling reference the reader cannot verify
        from the tree alone. Left out of both `authoritative` (nothing
        vouches it is current) and `superseded` (nothing in `records`
        confirms it was actually replaced).
      - `conflicts`: {target_path: sorted[corrector_paths]} -- two or
        more records both claim to supersede the same target. This is
        the shape the issue's own second report warns about (a second,
        independent correction producing a third copy): fail-closed, not
        arbitration -- neither the target nor any of its claimed
        correctors is placed in `authoritative`, since content alone
        cannot say which correction is real.
    """
    claims: dict[str, list[str]] = {}
    broken: set[str] = set()
    for path, content in records.items():
        target = parse_supersedes(content)
        if target is None:
            continue
        if target not in records:
            broken.add(target)
            continue
        claims.setdefault(target, []).append(path)

    superseded: dict[str, str] = {}
    conflicts: dict[str, list[str]] = {}
    excluded: set[str] = set()
    for target, correctors in claims.items():
        if len(correctors) > 1:
            conflicts[target] = sorted(correctors)
            excluded.add(target)
            excluded.update(correctors)
        else:
            superseded[target] = correctors[0]

    authoritative = sorted(
        p for p in records
        if p not in superseded and p not in excluded
    )
    return {
        "authoritative": authoritative,
        "superseded": superseded,
        "broken": sorted(broken),
        "conflicts": conflicts,
    }
