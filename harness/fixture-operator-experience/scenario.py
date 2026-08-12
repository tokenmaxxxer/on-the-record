"""issue #1006 harness scenario — operator-experience layer.

Follows the `harness/fixture-requirement-digest/scenario.py` pairing
shape: mechanical checks against `gates/operator_experience.py` and the
two seeded conversations (`seed_vague.json`, `seed_precise.json`), no
live Claude Code session. Covers the issue's acceptance wording: vague
ask -> elicitation before delegation; precise ask -> empty state (skips
straight to delegation); plus a static presence check that blocks A-D
actually landed in `directive.sh`, and a behavioral check that block A's
first-contact guidance fires once per workspace, not every turn.

  python3 harness/fixture-operator-experience/scenario.py
  exits 0 and prints all rows PASS, non-zero otherwise.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_DIR.parent.parent

sys.path.insert(0, str(REPO_ROOT / "gates"))
import operator_experience as oe  # noqa: E402

_DIRECTIVE = REPO_ROOT / "on-the-record" / "hooks" / "directive.sh"


def _load_seed(name: str) -> dict:
    return json.loads((HARNESS_DIR / name).read_text(encoding="utf-8"))


def check_1_blocks_a_through_d_present() -> list[str]:
    return oe.directive_has_blocks_a_through_d(REPO_ROOT)


def check_2_vague_seed_needs_elicitation() -> list[str]:
    seed = _load_seed("seed_vague.json")
    text = " ".join(seed["utterances"])
    got = oe.has_testable_acceptance(text)
    if got != (not seed["expect_elicitation"]):
        return [
            f"vague seed: has_testable_acceptance={got}, "
            f"expected {not seed['expect_elicitation']} "
            f"(expect_elicitation={seed['expect_elicitation']})"
        ]
    return []


def check_3_precise_seed_skips_elicitation() -> list[str]:
    seed = _load_seed("seed_precise.json")
    text = " ".join(seed["utterances"])
    got = oe.has_testable_acceptance(text)
    if got != (not seed["expect_elicitation"]):
        return [
            f"precise seed: has_testable_acceptance={got}, "
            f"expected {not seed['expect_elicitation']} "
            f"(expect_elicitation={seed['expect_elicitation']})"
        ]
    return []


def _run_directive(checkout: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    env["ORCHESTRATE_OFF"] = "0"
    env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
    directive = checkout / "on-the-record" / "hooks" / "directive.sh"
    return subprocess.run(
        ["bash", str(directive)],
        cwd=str(checkout),
        env=env,
        capture_output=True,
        text=True,
    )


def check_4_first_contact_fires_once_per_workspace() -> list[str]:
    # Isolated temp checkout (real hooks/, stub spawn.py) so this run
    # never touches the real working tree's .orchestrate-greeted state.
    import shutil
    d = Path(tempfile.mkdtemp())
    problems: list[str] = []
    try:
        (d / "on-the-record" / "hooks").mkdir(parents=True)
        shutil.copytree(
            REPO_ROOT / "on-the-record" / "hooks", d / "on-the-record" / "hooks",
            dirs_exist_ok=True,
        )
        (d / "spawn.py").write_text(
            "import sys\nif __name__ == '__main__':\n    sys.exit(1)\n"
        )
        first = _run_directive(d)
        if "First time in this workspace" not in first.stdout:
            problems.append(
                f"expected first-contact block on first run, stdout: {first.stdout[:300]!r}"
            )
        second = _run_directive(d)
        if "First time in this workspace" in second.stdout:
            problems.append("expected first-contact block to NOT repeat on second run")
        return problems
    finally:
        shutil.rmtree(d, ignore_errors=True)


CHECKS = [
    ("blocks A-D present in directive.sh", check_1_blocks_a_through_d_present),
    ("vague seed needs elicitation (no testable acceptance shape)", check_2_vague_seed_needs_elicitation),
    ("precise seed skips elicitation (empty state)", check_3_precise_seed_skips_elicitation),
    ("first-contact guidance fires once per workspace", check_4_first_contact_fires_once_per_workspace),
]


def run() -> int:
    failures = 0
    for name, fn in CHECKS:
        problems = fn()
        if problems:
            failures += 1
            print(f"FAIL {name}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"PASS {name}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
