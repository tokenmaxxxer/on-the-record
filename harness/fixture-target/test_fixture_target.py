import argparse

from fixture_target import _resolve_version


def test_resolve_version_returns_version_string_when_flag_set():
    args = argparse.Namespace(version=True)
    assert _resolve_version(args) == "0.1.0"


def test_resolve_version_returns_none_when_flag_unset():
    args = argparse.Namespace(version=False)
    assert _resolve_version(args) is None
