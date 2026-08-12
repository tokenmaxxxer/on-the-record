"""issue #956 harness scenario — target-project requirement capture.

Follows the `harness/fixture-*` no-live-session pattern (mirrors
`harness/fixture-requirement-digest/scenario.py`): seeds a scratch git
repo on branch `main` (not an on-the-record `issue-<n>/<role>` branch —
the shape a plugin-installed TARGET project actually runs) and invokes
`on-the-record/hooks/product-capture-stopgate.sh` against it directly,
the same way `on-the-record/hooks/test_product_capture_stopgate.py`
does, via subprocess with the Stop-event payload on stdin.

Two scenarios, both against the same non-issue-branch repo shape:
  1. capture-fires: a transcript with one flagged requirement sentence
     ->  the hook advises against `docs/product/requirements.md` (no
     issue segment) and bootstraps that file.
  2. empty-state: a transcript with no flagged sentences -> no
     `docs/product/*.md` writes at all.

  python3 harness/fixture-target/scenario.py
  exits 0 and prints both scenario rows PASS, non-zero otherwise.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = HARNESS_DIR.parent
HOOK = REPO_ROOT / "on-the-record" / "hooks" / "product-capture-stopgate.sh"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "scenario@example.com")
    _git(repo, "config", "user.name", "Scenario")
    (repo / "README.md").write_text("init\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "checkout", "-q", "-B", "main")


def _write_transcript(repo: Path, user_texts: list[str]) -> Path:
    transcript = repo / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as fh:
        for text in user_texts:
            fh.write(json.dumps({
                "type": "user",
                "message": {"role": "user", "content": text},
            }) + "\n")
    return transcript


def _run(repo: Path, transcript: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({"transcript_path": str(transcript)})
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, timeout=20,
        cwd=str(repo), env={"PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def scenario_capture_fires_in_target_repo() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        r = _run(repo, transcript)
        doc = repo / "docs" / "product" / "requirements.md"
        if r.returncode != 0:
            return False, f"exit {r.returncode}, stderr={r.stderr[:200]!r}"
        try:
            out = json.loads(r.stdout)
            ctx = out["hookSpecificOutput"]["additionalContext"]
        except (ValueError, KeyError, TypeError):
            return False, f"no advisory JSON on stdout: {r.stdout[:200]!r}"
        if "docs/product/" not in ctx or "docs/issue-" in ctx:
            return False, f"advisory did not reference fallback path: {ctx!r}"
        if not doc.is_file():
            return False, f"{doc} was not bootstrapped"
        return True, "advised + bootstrapped docs/product/requirements.md"


def scenario_empty_state_no_writes() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["read this file please", "run the tests"]
        )
        r = _run(repo, transcript)
        if r.returncode != 0:
            return False, f"exit {r.returncode}, stderr={r.stderr[:200]!r}"
        if r.stdout != "":
            return False, f"unexpected advisory on empty state: {r.stdout[:200]!r}"
        if (repo / "docs").exists():
            return False, "docs/ was created despite no flagged sentence"
        return True, "no docs/product/* writes, no advisory"


SCENARIOS = [
    ("capture-fires", scenario_capture_fires_in_target_repo),
    ("empty-state", scenario_empty_state_no_writes),
]


def main() -> int:
    ok = True
    for name, fn in SCENARIOS:
        passed, detail = fn()
        ok = ok and passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
