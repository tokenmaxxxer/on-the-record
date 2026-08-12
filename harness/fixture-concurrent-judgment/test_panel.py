"""issue #973 — end-to-end fixture for `panel_cmd()` (spawn.py).

Seeded stand-ins only: no real `claude -p` process is spawned (matches the
proposal's adopted fixture shape — none of `harness/fixture-*/`'s tests
shell out to `claude -p`). `run_session` is the dependency-injection point
`panel_cmd()` exposes at the transport boundary; the degraded-path test
also stubs `spawn.consult_cmd()` so the fallback path stays offline too.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import spawn  # noqa: E402


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
    monkeypatch.setattr(spawn, "ROOT", tmp_path)
    return tmp_path


def _seeded_live_session(role, peer_role, question, cwd):
    """Stands in for a live judge session: one position, one rebuttal,
    then a verdict — the shape a real session's `SendMessage` exchange
    plus final JSON would produce."""
    return {
        "turns": [
            f"{role}: my position on {question!r} is X.",
            f"{role}: rebutting {peer_role}'s point — still X, refined.",
        ],
        "verdict": {"answer": f"{role} says X", "confidence": "high", "caveats": []},
    }


def test_panel_live_exchange_records_position_rebuttal_and_verdict(fake_root):
    result = spawn.panel_cmd("qa", "review", "should we ship it?", issue=973,
                              cwd=str(fake_root), run_session=_seeded_live_session)

    assert result["degraded"] is False
    record_path = Path(result["record_path"])
    assert record_path == fake_root / "docs" / "issue-973" / "reports" / "panel" / "should-we-ship-it.md"
    text = record_path.read_text(encoding="utf-8")

    assert "| position |" in text
    assert "| rebuttal |" in text
    assert "| verdict |" in text
    assert "role=qa" in text
    assert "role=review" in text


def _unavailable_session(role, peer_role, question, cwd):
    raise spawn._PanelMessagingUnavailable(f"{role}: seeded unavailable")


def test_panel_degrades_to_sequential_consult_when_messaging_unavailable(fake_root, monkeypatch):
    calls = []

    def fake_consult(role, question, issue=None, cwd=None):
        calls.append(role)
        return {"answer": f"{role} sequential answer", "confidence": "medium", "caveats": []}

    monkeypatch.setattr(spawn, "consult_cmd", fake_consult)

    result = spawn.panel_cmd("qa", "review", "should we ship it?", issue=973,
                              cwd=str(fake_root), run_session=_unavailable_session)

    assert result["degraded"] is True
    assert "seeded unavailable" in result["reason"]
    assert calls == ["qa", "review"]

    text = Path(result["record_path"]).read_text(encoding="utf-8")
    assert "degraded" in text
    assert "sequential-consult" in text
    assert "seeded unavailable" in text
