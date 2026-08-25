#!/usr/bin/env python3
"""spawn.py 의 순수 함수들 — 세션을 띄우지 않고 검사한다."""
import argparse
import contextlib
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn
import shape_contracts



def _event(type_, **kw):
    """Build a stream-json event fixture and validate its shape against
    what spawn.py's parser reads (issue #335) before returning it."""
    event = {"type": type_, **kw}
    shape_contracts.assert_claude_stream_event_shape(event)
    return event


@contextlib.contextmanager
def isolated_role_model_config():
    """Patch spawn.ROLE_MODEL_CONFIG to a private per-test temp path.

    The real path (ROOT / "role_model.txt") is a single fixed file shared
    by every pytest-xdist worker process; tests that read/write it directly
    race each other (torn writes, UnicodeDecodeError from another test's
    in-flight non-UTF-8 fixture) whenever two of them land in different
    workers at the same time. Isolating each test to its own tmp path
    removes the shared mutable state instead of just narrowing the race.
    """
    tmp_dir = tempfile.mkdtemp(prefix="role_model_config_")
    try:
        with mock.patch.object(spawn, "ROLE_MODEL_CONFIG", Path(tmp_dir) / "role_model.txt"):
            yield
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


