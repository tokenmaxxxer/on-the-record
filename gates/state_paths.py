#!/usr/bin/env python3
"""issue #2240: single accessor for orchestrator-scoped cross-tick state.

Every file the system writes under `runs/` is either target-repo state
(belongs with the repo being worked on) or orchestrator cross-tick memory
("did I already report this PR", "did I already try spawning this role")
that must outlive any single workspace and must never land inside a
consumer's working tree. The latter category was previously composed
ad hoc as `root / "runs" / "<name>.json"`, where `root` is whatever repo
a caller happens to be operating on — the target repo's own checkout, or
an ephemeral per-role clone that gets discarded at session end. Storage
location and meaning disagreed: orchestrator memory kept vanishing
because it was never written to the same place twice, and — worse — for
any repo that is not this orchestrator's own install, it was written
straight into that repo's tracked working tree.

`orchestrator_state_path()` anchors to `MUSTER_STATE_ROOT` when set (the
same override spawn.py's/watchdog.py's/events.py's own `STATE_ROOT`
constants honor) else this install's own `<repo-root>/runs` — never the
`root` a caller passes in. Callers that need orchestrator-scoped storage
should call this instead of composing `root / "runs" / ...` themselves; a
bare `root / "runs"` for one of these files is a scoping bug, not a style
choice.
"""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")


def orchestrator_state_path(filename: str) -> Path:
    """Location for orchestrator-scoped cross-tick state named `filename`.

    Anchored to `STATE_ROOT` (module-level, evaluated at import time —
    tests that need isolation monkeypatch this constant directly, the
    same convention spawn.py's/watchdog.py's own `STATE_ROOT` already use,
    since a post-import env var change is not retroactively seen)."""
    return STATE_ROOT / filename
