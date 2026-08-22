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


