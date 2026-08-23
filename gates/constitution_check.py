"""issue #2104 — constitution check: mechanical layer only.

Two documented drift incidents (2026-08-21, 2x in one day) had the
orchestrator adopt consult recommendations that contradicted frozen
program principles; the check lived only in operator memory. This
module makes the *mechanical* part structural:

1. `scope_intersection()` — which frozen decisions does a recommendation
   touch? Keyword match (case-insensitive substring on the recommendation
   text) plus glob match (fnmatch on any path the recommendation names /
   the adoption would touch).
2. `check_recommendation()` — non-intersecting recommendations SKIP with
   a logged reason (no ceremony where none is owed); intersecting ones
   REQUIRE an explicit recorded disposition.
3. `check_disposition()` — the disposition contract: an issue that cites
   a consult-trace whose scope intersects a frozen decision must contain
   either `reaffirms <decision-id>` or `escalated-to-operator: <link or
   quote>`. Missing disposition => named-conflict failure (the failure
   names the frozen decision, so the orchestrator knows what to escalate).

Deliberately NOT here: the semantic judgment of whether the
recommendation actually contradicts the principle. That stays with the
orchestrator (a fresh-context principle-check pass, per the issue); this
gate only guarantees a disposition EXISTS and blocks silent adoption.
"""
from __future__ import annotations

import re
import sys
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from frozen_decisions import Decision, frozen_decisions  # noqa: E402

REAFFIRM_RE = re.compile(r"reaffirms\s+(\S+)", re.IGNORECASE)
ESCALATED_RE = re.compile(r"escalated-to-operator:\s*(\S.*)", re.IGNORECASE)


def _glob_hit(path: str, pattern: str) -> bool:
    p = path.strip().lstrip("./")
    if fnmatch(p, pattern):
        return True
    # `roles/**` should also match `roles/foo.json` and bare `roles`
    if pattern.endswith("/**"):
        base = pattern[:-3]
        return p == base or p.startswith(base + "/")
    return False


def scope_intersection(recommendation_text: str, touched_paths: list[str] | None = None,
                       registry: list[Decision] | None = None) -> list[tuple[Decision, str]]:
    """Frozen decisions whose scope intersects the recommendation.
    Returns (decision, why) pairs; `why` names the matched keyword or
    glob so the refusal is self-explaining."""
    frozen = registry if registry is not None else frozen_decisions()
    text = recommendation_text.lower()
    hits: list[tuple[Decision, str]] = []
    for dec in frozen:
        if dec.status != "frozen":
            continue
        why = None
        for kw in dec.keywords:
            if kw.lower() in text:
                why = f"keyword {kw!r}"
                break
        if why is None:
            for pattern in dec.globs:
                hit = next((p for p in (touched_paths or []) if _glob_hit(p, pattern)), None)
                if hit:
                    why = f"glob {pattern!r} matches {hit!r}"
                    break
        if why is not None:
            hits.append((dec, why))
    return hits


def check_recommendation(recommendation_text: str, touched_paths: list[str] | None = None,
                         registry: list[Decision] | None = None) -> dict:
    """Mechanical constitution check for a consult recommendation.

    Returns:
      {"status": "skip", "reason": "..."}                       — no frozen scope touched
      {"status": "needs-disposition", "conflicts": [...],
       "detail": "..."}                                          — disposition required
    Never returns an adoption verdict — that judgment is the
    orchestrator's, made against the frozen decision text."""
    hits = scope_intersection(recommendation_text, touched_paths, registry)
    if not hits:
        n = len(registry) if registry is not None else len(frozen_decisions())
        return {"status": "skip",
                "reason": f"intersects none of {n} frozen decision scope(s) "
                          "(keywords and globs both miss)"}
    return {
        "status": "needs-disposition",
        "conflicts": [d.decision_id for d, _ in hits],
        "detail": "; ".join(f"{d.decision_id}: {why}" for d, why in hits),
    }


def check_disposition(issue_text: str, decision_ids: list[str]) -> dict:
    """Disposition contract for an issue citing a scope-intersecting
    consult. PASS iff, for every intersecting decision, the issue text
    contains `reaffirms <decision-id>` OR contains a single
    `escalated-to-operator: <link/quote>` record (escalation covers all
    conflicts at once — the operator saw the whole recommendation).

    Returns {"ok": bool, "missing": [ids], "detail": str}. On failure the
    detail NAMES the conflicting decision(s) — never a bare refusal."""
    escalated = ESCALATED_RE.search(issue_text)
    if escalated:
        return {"ok": True, "missing": [],
                "detail": f"escalated-to-operator: {escalated.group(1).strip()[:200]}"}
    reaffirmed = {m.group(1).strip().rstrip(".,;:") for m in REAFFIRM_RE.finditer(issue_text)}
    missing = [d for d in decision_ids if d not in reaffirmed]
    if missing:
        return {"ok": False, "missing": missing,
                "detail": ("conflict with frozen decision(s) " + ", ".join(missing)
                           + " — issue must carry `reaffirms <decision-id>` or "
                             "`escalated-to-operator: <link/quote>`; silent adoption is blocked")}
    return {"ok": True, "missing": [],
            "detail": "reaffirms " + ", ".join(decision_ids)}


def main(argv: list[str]) -> int:
    """CLI: constitution_check.py <recommendation-file> [touched-path ...]
    Prints PASS/SKIP or the named conflict; exit 1 on needs-disposition."""
    if len(argv) < 2:
        print("usage: constitution_check.py <recommendation-file> [touched-path ...]",
              file=sys.stderr)
        return 2
    text = Path(argv[1]).read_text(encoding="utf-8")
    result = check_recommendation(text, list(argv[2:]))
    if result["status"] == "skip":
        print(f"SKIP: {result['reason']}")
        return 0
    print(f"NEEDS-DISPOSITION: {result['detail']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
