"""Real repaired code (issue #3228 site 5), verbatim excerpt from the
current delegation_state.py: a wildcard entry now refuses to match
unless the action's resource is provably a single, non-chained shell
command."""
from __future__ import annotations

import fnmatch

_SHELL_OPERATOR_TOKENS = (";", "|", "&", "`", "$(", "<<")


def _is_provably_single_command(resource: str) -> bool:
    if not resource.isprintable():
        return False
    return not any(token in resource for token in _SHELL_OPERATOR_TOKENS)


def _is_glob_pattern(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[")


def is_covered(action: dict, manifest: "list[dict] | None", repo: "str | None" = None) -> bool:
    entries = manifest or []
    action_resource = action.get("resource") or ""
    action_is_compound = not _is_provably_single_command(action_resource)
    for entry in entries:
        if entry.get("tool") != action.get("tool"):
            continue
        entry_resource = entry.get("resource")
        if not entry_resource:
            continue
        if action_is_compound and _is_glob_pattern(entry_resource):
            continue
        if not fnmatch.fnmatch(action_resource, entry_resource):
            continue
        entry_repo = entry.get("repo") or "*"
        if repo is not None and not fnmatch.fnmatch(repo, entry_repo):
            continue
        return True
    return False
