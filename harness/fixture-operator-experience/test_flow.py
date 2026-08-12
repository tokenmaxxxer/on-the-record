"""pytest wrapper around `scenario.py`'s mechanical checks (issue #1006).

Mirrors `fixture-requirement-digest`'s pairing: `scenario.py` is the
runnable CLI check (`python3 harness/fixture-operator-experience/
scenario.py`), this file lets the same checks run under pytest.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenario  # noqa: E402


def test_blocks_a_through_d_present():
    assert scenario.check_1_blocks_a_through_d_present() == []


def test_vague_seed_needs_elicitation():
    assert scenario.check_2_vague_seed_needs_elicitation() == []


def test_precise_seed_skips_elicitation():
    assert scenario.check_3_precise_seed_skips_elicitation() == []


def test_first_contact_fires_once_per_workspace():
    assert scenario.check_4_first_contact_fires_once_per_workspace() == []
