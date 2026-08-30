"""pytest plugin (issue #2326 round 3): bounds any single selected test
item to OTR_LINT_TEST_PER_FILE_TIMEOUT_S seconds via SIGALRM, so one
slow/hanging matched file cannot blow the hook's own combined budget --
the item is abandoned and reported as a failure, and the run continues
to the next item, rather than the file being excluded by name.

SIGALRM only interrupts the process's main thread, so this hook always
invokes pytest with xdist disabled (`-o addopts=""`) when this plugin is
loaded -- see lint-test-on-edit.sh, which measured -n auto's worker
distribution turning this same bound unreliable (one file's abandoned
item still cost ~24s wall-clock under xdist, vs ~3-3.5s single-process).
"""
import os
import signal

import pytest


class _PerItemTimeout(Exception):
    pass


def _handler(signum, frame):
    seconds = _seconds()
    raise _PerItemTimeout(
        "otr-per-file-timeout: exceeded %ss, item abandoned" % seconds
    )


def _seconds():
    try:
        return float(os.environ.get("OTR_LINT_TEST_PER_FILE_TIMEOUT_S", "0"))
    except ValueError:
        return 0.0


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    seconds = _seconds()
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return
    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    except _PerItemTimeout:
        pytest.fail(
            "otr-per-file-timeout: exceeded %ss, item abandoned" % seconds
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
