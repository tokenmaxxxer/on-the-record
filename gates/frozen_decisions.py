"""issue #2104 — machine-readable frozen-decision registry.

docs/decisions/*.md carry YAML front-matter; this module parses it with
no third-party dependency (the shape is deliberately restricted: scalar
keys plus a `scope:` mapping of two string lists). The registry is what
`gates/constitution_check.py` loads to decide whether a consult
recommendation intersects a frozen principle.

Front-matter contract (see docs/decisions/README.md):

    ---
    id: single-skill-axis          # stable slug; defaults to filename stem
    status: frozen                 # frozen | active | superseded
    scope:                         # REQUIRED (non-empty) when status: frozen
      globs:
        - "roles/**"
      keywords:
        - "role manifest"
    ---

`status` values outside {frozen, active, superseded} are lint errors.
Legacy keys (kind/date/subject/legacy-status/origin/...) pass through
untouched — the lint only constrains what it names.

    python3 -m gates.frozen_decisions          # lint the repo registry
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

VALID_STATUS = ("frozen", "active", "superseded")
DECISIONS_DIR = Path(__file__).resolve().parent.parent / "docs" / "decisions"


@dataclass
class Decision:
    decision_id: str
    status: str
    path: Path
    globs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    # AND-groups: a group hits when EVERY term in it appears in the text.
    # Guards against paraphrase drift that exact phrases miss (issue #2104
    # review: 'enforcement hooks beside skills' slipped past all 6 phrases).
    keyword_groups: list[list[str]] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @property
    def has_scope(self) -> bool:
        return bool(self.globs or self.keywords or self.keyword_groups)


def parse_front_matter(text: str) -> dict | None:
    """Return the front-matter mapping, or None when the document has no
    `---` block at the very top. Restricted-YAML: `key: value` scalars,
    plus one level of nested mappings whose values are `- item` lists.
    Raises ValueError on a malformed block (unterminated, bad line)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    out: dict = {}
    current_map: dict | None = None
    current_list: list | None = None
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return out
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped.startswith("- "):
            if current_list is None:
                raise ValueError(f"line {i}: list item outside a list key: {stripped!r}")
            current_list.append(_unquote(stripped[2:].strip()))
            continue
        if ":" not in stripped:
            raise ValueError(f"line {i}: not a `key: value` line: {stripped!r}")
        key, _, value = stripped.partition(":")
        key, value = key.strip(), _unquote(value.strip())
        if indent == 0:
            current_map = None
            current_list = None
            if value == "":
                current_map = {}
                out[key] = current_map
            else:
                out[key] = value
        else:
            if current_map is None:
                raise ValueError(f"line {i}: indented key with no parent mapping: {stripped!r}")
            if value == "":
                current_list = []
                current_map[key] = current_list
            else:
                current_list = None
                current_map[key] = value
    raise ValueError("unterminated front-matter block (no closing ---)")


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def dump_front_matter(meta: dict) -> str:
    """Inverse of parse_front_matter for the restricted shape — used by
    the round-trip test, so authored front-matter provably re-parses."""
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k2, v2 in value.items():
                if isinstance(v2, list):
                    lines.append(f"  {k2}:")
                    lines.extend(f'    - "{item}"' for item in v2)
                else:
                    lines.append(f"  {k2}: {v2}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def load_decision(path: Path) -> Decision:
    meta = parse_front_matter(path.read_text(encoding="utf-8"))
    if meta is None:
        raise ValueError(f"{path.name}: missing front-matter block")
    status = str(meta.get("status", "")).strip()
    scope = meta.get("scope") or {}
    if not isinstance(scope, dict):
        raise ValueError(f"{path.name}: `scope:` must be a mapping")
    globs = scope.get("globs") or []
    keywords = scope.get("keywords") or []
    # Restricted-YAML front matter has no nested lists, so each group is one
    # string of `+`-joined terms: - "hook + skill" => all terms must appear.
    raw_groups = scope.get("keyword-groups") or []
    if not isinstance(globs, list) or not isinstance(keywords, list):
        raise ValueError(f"{path.name}: scope.globs / scope.keywords must be lists")
    if not isinstance(raw_groups, list) or not all(isinstance(g, str) for g in raw_groups):
        raise ValueError(f"{path.name}: scope.keyword-groups must be a list of"
                         " '+'-joined term strings")
    keyword_groups = [[t.strip() for t in g.split("+") if t.strip()] for g in raw_groups]
    if not all(keyword_groups) or (raw_groups and not keyword_groups):
        raise ValueError(f"{path.name}: scope.keyword-groups entries need at least one term")
    return Decision(
        decision_id=str(meta.get("id", path.stem)),
        status=status,
        path=path,
        globs=[str(g) for g in globs],
        keywords=[str(k) for k in keywords],
        keyword_groups=keyword_groups,
        raw=meta,
    )


def load_registry(decisions_dir: Path | None = None) -> list[Decision]:
    d = decisions_dir or DECISIONS_DIR
    return [load_decision(p) for p in sorted(d.glob("*.md")) if p.name != "README.md"]


def frozen_decisions(decisions_dir: Path | None = None) -> list[Decision]:
    return [d for d in load_registry(decisions_dir) if d.status == "frozen"]


def lint_registry(decisions_dir: Path | None = None) -> list[str]:
    """Every decision file parses; status is in-vocabulary; frozen ones
    carry a non-empty scope; ids are unique. Returns error strings."""
    d = decisions_dir or DECISIONS_DIR
    errors: list[str] = []
    seen: dict[str, str] = {}
    for p in sorted(d.glob("*.md")):
        if p.name == "README.md":
            continue
        try:
            dec = load_decision(p)
        except ValueError as e:
            errors.append(str(e))
            continue
        if dec.status not in VALID_STATUS:
            errors.append(f"{p.name}: status {dec.status!r} not in {'/'.join(VALID_STATUS)}")
        if dec.status == "frozen" and not dec.has_scope:
            errors.append(f"{p.name}: status frozen but scope is empty "
                          "(frozen decisions need globs or keywords to be enforceable)")
        if dec.decision_id in seen:
            errors.append(f"{p.name}: duplicate id {dec.decision_id!r} (also {seen[dec.decision_id]})")
        else:
            seen[dec.decision_id] = p.name
    return errors


def main(argv: list[str]) -> int:
    d = Path(argv[1]) if len(argv) > 1 else DECISIONS_DIR
    errors = lint_registry(d)
    for e in errors:
        print(f"frozen-decisions lint: {e}", file=sys.stderr)
    if not errors:
        frozen = frozen_decisions(d)
        print(f"ok: {len(load_registry(d))} decision(s), {len(frozen)} frozen "
              f"({', '.join(x.decision_id for x in frozen)})")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
