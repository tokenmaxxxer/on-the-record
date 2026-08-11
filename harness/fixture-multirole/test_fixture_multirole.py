from fixture_multirole import storage_a, storage_b


def test_storage_a_round_trips(tmp_path):
    path = tmp_path / "a.json"
    storage_a.save(str(path), {"x": 1})
    assert storage_a.load(str(path)) == {"x": 1}


def test_storage_b_round_trips(tmp_path):
    path = tmp_path / "b.sqlite"
    storage_b.save(str(path), {"x": 1})
    assert storage_b.load(str(path)) == {"x": 1}


# Requirement (issue #895 type 6): once a backend is chosen and wired into
# cli.py's save/load commands, that wiring should be covered by a new
# test — deliberately absent here, since which backend gets tested
# depends on the decision the driven session records.
