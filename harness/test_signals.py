"""Issue #831: harness/signals.py's remote-setup signal, over transcript
dicts only (no live session involved, matching the rest of signals.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from signals import (
    PASS, FAIL, UNMEASURED,
    check_remote_setup_not_silently_bypassed,
)


def test_unmeasured_when_transcript_missing():
    assert check_remote_setup_not_silently_bypassed(None) == UNMEASURED


def test_unmeasured_when_origin_resolved_key_absent():
    assert check_remote_setup_not_silently_bypassed({}) == UNMEASURED


def test_fail_when_origin_never_resolved():
    # Today's #830 behavior: no remote, no setup ever happened.
    assert check_remote_setup_not_silently_bypassed(
        {"origin_resolved": False}) == FAIL


def test_pass_steady_state_preseeded_remote():
    assert check_remote_setup_not_silently_bypassed(
        {"origin_resolved": True, "remote_was_preseeded": True}) == PASS


def test_pass_confirmed_setup_before_first_delegation():
    assert check_remote_setup_not_silently_bypassed({
        "origin_resolved": True,
        "remote_setup_confirmed_ts": 100,
        "delegation_events": [{"ts": 200}, {"ts": 300}],
    }) == PASS


def test_fail_when_resolved_with_no_confirmation_event():
    # Candidate (a), self-provision with no consent, sneaking back in.
    assert check_remote_setup_not_silently_bypassed({
        "origin_resolved": True,
        "delegation_events": [{"ts": 200}],
    }) == FAIL


def test_fail_when_confirmation_happens_after_first_delegation():
    assert check_remote_setup_not_silently_bypassed({
        "origin_resolved": True,
        "remote_setup_confirmed_ts": 500,
        "delegation_events": [{"ts": 200}],
    }) == FAIL
