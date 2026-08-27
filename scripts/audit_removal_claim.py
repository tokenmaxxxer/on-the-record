#!/usr/bin/env python3
"""Repeatable removal-claim checker (issue #2626).

The #2548 test, mechanized: a claimed removal is not "the old name is gone"
but "nothing reconstructs the removed structure under another name and
nothing still branches on membership in the closed set." A grep for the old
identifier answers only the first, weakest question and a rename passes it
trivially -- three of four prior "removals" in this system were exactly that.

A claim is a JSON object:
{
  "name": "human label",
  "removed_names": ["OldConstantOrFuncName", ...],   # Q1: must be gone
  "member_samples": ["memberA", "memberB", "memberC"],  # >=2 known elements
                                                          # of the closed set
                                                          # the old name held
  "min_coloc": 2                                        # how many of
                                                          # member_samples
                                                          # co-located in one
                                                          # file counts as
                                                          # "reconstructed"
}

Q1 (name gone): grep for each removed_name.
Q2 (reshaped): grep for each member_sample; if >= min_coloc of them appear
   in the same non-doc, non-test file, that file is reconstructing the same
   closed set under a new container (dict, tuple, glob'd directory listing,
   JSON, whatever) -- regardless of what it's called.
Q3 (still branches): grep for membership-test shapes ("in (...)", "==", a
   dict literal, dispatch keyed by name) touching >=1 member_sample outside
   docs/tests.

Every verdict is one of VERIFIED_ABSENT, RESHAPE_DETECTED, or
COULD_NOT_DETERMINE (never a bare pass/fail on missing data -- reporting
uncertainty as success is the same defect this tool exists to catch).
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DOC_TEST_EXCLUDE = re.compile(r"(^|/)(docs|test|tests)/")


def _grep(root: Path, pattern: str) -> list[str]:
    try:
        out = subprocess.run(
            ["grep", "-rln", "-E", pattern, "."],
            cwd=root, capture_output=True, text=True, timeout=30,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [l for l in out.splitlines() if l]


def _grep_files_containing_all(root: Path, needles: list[str], min_count: int) -> list[tuple[str, int]]:
    """Files where at least min_count of `needles` co-occur (grep -l per
    needle, then intersect counts) -- the mechanical stand-in for "the same
    closed set reconstructed under a new name/shape"."""
    counts: dict[str, int] = {}
    for needle in needles:
        for f in _grep(root, re.escape(needle)):
            counts[f] = counts.get(f, 0) + 1
    return sorted((f, c) for f, c in counts.items() if c >= min_count)


def check_claim(root: Path, claim: dict) -> dict:
    name = claim["name"]
    removed_names = claim.get("removed_names", [])
    member_samples = claim.get("member_samples", [])
    min_coloc = claim.get("min_coloc", max(2, len(member_samples) - 1))

    result = {"name": name, "q1": {}, "q2": {}, "q3": {}, "verdict": None, "detail": ""}

    # Q1 -- is the name gone (excluding docs/, test/, tests/ -- historical
    # records and this tool's own fixtures are expected to mention it)?
    q1_hits = []
    for rn in removed_names:
        hits = [f for f in _grep(root, re.escape(rn)) if not DOC_TEST_EXCLUDE.search(f)]
        q1_hits.extend((rn, f) for f in hits)
    result["q1"] = {"checked": removed_names, "live_hits": q1_hits, "gone": len(q1_hits) == 0}

    if not removed_names:
        result["verdict"] = "COULD_NOT_DETERMINE"
        result["detail"] = "no removed_names supplied -- Q1 cannot run"
        return result

    # Q2 -- reconstructed under another name/shape? Only checkable if we
    # were given known members of the old closed set.
    if not member_samples or len(member_samples) < 2:
        result["q2"] = {"checked": False, "reason": "fewer than 2 member_samples supplied"}
        q2_determinable = False
    else:
        coloc = _grep_files_containing_all(root, member_samples, min_coloc)
        coloc = [(f, c) for f, c in coloc if not DOC_TEST_EXCLUDE.search(f)]
        result["q2"] = {
            "checked": True, "member_samples": member_samples, "min_coloc": min_coloc,
            "colocated_files": coloc, "reshaped": len(coloc) > 0,
        }
        q2_determinable = True

    # Q3 -- still branches on membership? Look for comparison/dispatch shapes
    # touching a member sample outside docs/tests.
    if not member_samples:
        result["q3"] = {"checked": False, "reason": "no member_samples supplied"}
        q3_determinable = False
    else:
        branch_hits = []
        for m in member_samples:
            pattern = rf'(==\s*["\']{ re.escape(m) }["\']|["\']{ re.escape(m) }["\']\s*in\s|\bin\s*[\[({{][^)\]}}]*["\']{ re.escape(m) }["\'])'
            hits = [f for f in _grep(root, pattern) if not DOC_TEST_EXCLUDE.search(f)]
            branch_hits.extend((m, f) for f in hits)
        result["q3"] = {"checked": True, "branch_hits": branch_hits, "still_branches": len(branch_hits) > 0}
        q3_determinable = True

    if not result["q1"]["gone"]:
        result["verdict"] = "RESHAPE_DETECTED"
        result["detail"] = f"removed name(s) still present live: {q1_hits}"
    elif q2_determinable and result["q2"]["reshaped"]:
        result["verdict"] = "RESHAPE_DETECTED"
        result["detail"] = f"closed set reconstructed in: {result['q2']['colocated_files']}"
    elif q3_determinable and result["q3"]["still_branches"]:
        result["verdict"] = "RESHAPE_DETECTED"
        result["detail"] = f"live closed-set branching found: {result['q3']['branch_hits']}"
    elif not q2_determinable or not q3_determinable:
        result["verdict"] = "COULD_NOT_DETERMINE"
        result["detail"] = "Q1 passed but Q2/Q3 lack member_samples to check reshape/branching -- do not read this as a pass"
    else:
        result["verdict"] = "VERIFIED_ABSENT"
        result["detail"] = "name gone; no co-located member-set reconstruction; no live closed-set branch found"

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("claims_file", help="JSON file: a claim object or a list of claim objects")
    ap.add_argument("--root", default=".", help="repo root to check (default: cwd)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    data = json.loads(Path(args.claims_file).read_text(encoding="utf-8"))
    claims = data if isinstance(data, list) else [data]

    exit_code = 0
    for claim in claims:
        r = check_claim(root, claim)
        print(f"=== {r['name']} ===")
        print(f"verdict: {r['verdict']}")
        print(f"detail: {r['detail']}")
        print(json.dumps(r, indent=2, default=str))
        if r["verdict"] != "VERIFIED_ABSENT":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
