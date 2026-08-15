"""Live-fire test for patrol_queue.py (issue #914 mechanism b): calls the
module's own checking functions from >= 2 distinct scenarios and asserts
an outcome from each, in-process (patrol_queue.py has no hooks.json
lifecycle-event surface — it's invoked in-process by other gates/CLI,
not piped a stdin payload)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patrol_queue as pq


def test_verify_allows_when_excerpt_present(tmp_path):
    target = tmp_path / "f.py"
    target.write_text("exact text here\n", encoding="utf-8")
    assert pq.verify({"path": "f.py", "excerpt": "exact text here"}, tmp_path) is True


def test_verify_denies_when_excerpt_absent(tmp_path):
    target = tmp_path / "f.py"
    target.write_text("something else\n", encoding="utf-8")
    assert pq.verify({"path": "f.py", "excerpt": "not present"}, tmp_path) is False
