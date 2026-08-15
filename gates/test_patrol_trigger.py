"""Live-fire test for patrol_trigger.py (issue #914 mechanism b): calls
should_fire from >= 2 distinct scenarios and asserts an allow and a deny
outcome, in-process (patrol_trigger.py has no hooks.json lifecycle-event
surface — it's a callable meant to be chained onto the merge-command
seam, not a stdin-piped hook)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patrol_trigger as pt
import patrol_queue as pq


def test_should_fire_allows_genuine_change():
    assert pt.should_fire({"changed_files": ["src/app.py"]}) is True


def test_should_fire_denies_patrol_artifact_only_1360_class():
    assert pt.should_fire({"changed_files": [pq.QUEUE_REL_PATH]}) is False
