"""Reconstructed pre-repair shape (issue #3228 site 5) of
delegation_state.py's is_covered(). No subprocess call anywhere -- this
is string/glob matching (fnmatch), a DOCUMENTED MISS for the chosen
subprocess-observation mechanism. The defect: a wildcard manifest entry
could not tell whether `action_resource` was a single command or a
shell-chained one (no way to observe that distinction was ever added),
so it silently matched either way -- "cannot tell" read as "matches"
instead of "does not match"."""
from __future__ import annotations

import fnmatch


def is_covered(action: dict, manifest: "list[dict] | None", repo: "str | None" = None) -> bool:
    entries = manifest or []
    action_resource = action.get("resource") or ""
    for entry in entries:
        if entry.get("tool") != action.get("tool"):
            continue
        entry_resource = entry.get("resource")
        if not entry_resource:
            continue
        if not fnmatch.fnmatch(action_resource, entry_resource):
            continue
        entry_repo = entry.get("repo") or "*"
        if repo is not None and not fnmatch.fnmatch(repo, entry_repo):
            continue
        return True
    return False
