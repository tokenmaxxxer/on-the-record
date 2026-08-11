"""Candidate backend A: a flat JSON file. Stubbed, not wired into cli.py."""


def save(path, data):
    import json

    with open(path, "w") as f:
        json.dump(data, f)


def load(path):
    import json

    with open(path) as f:
        return json.load(f)
