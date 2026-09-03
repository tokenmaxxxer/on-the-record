"""Real repaired code (issue #3228 site 6), verbatim excerpt from the
current scripts/consumer-path/verify_manipulation.py: evidence now comes
from two launcher-owned artifacts (a manifest plus its sha256 sidecar,
and a transport record the dispatching process itself wrote before
Popen()) -- nothing the spawned process opens can produce or alter
either one. Still no subprocess call here (fails closed on file
read/JSON/hash checks, not on a subprocess observation), so this stays
outside the chosen mechanism's scope just as the pre-repair shape was --
the repair here was architectural (whose process wrote which file), not
a subprocess-timeout/returncode fix, which is exactly why this
mechanism cannot claim credit for catching it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class VerificationFailure(Exception):
    pass


def load_manifest(manifest_path: Path) -> "tuple[dict, bytes]":
    if not manifest_path.is_file():
        raise VerificationFailure(f"manifest not found at {manifest_path} -- pair excluded")
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    return manifest, raw


def verify_manifest_integrity(manifest_path: Path, raw: bytes) -> None:
    sidecar_path = Path(str(manifest_path) + ".sha256")
    if not sidecar_path.is_file():
        raise VerificationFailure(
            f"manifest hash sidecar not found at {sidecar_path} -- pair excluded")
    recorded = sidecar_path.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(raw).hexdigest()
    if recorded != actual:
        raise VerificationFailure(
            f"manifest hash mismatch at {manifest_path}: sidecar records "
            f"{recorded!r}, recomputed {actual!r} -- pair excluded")
