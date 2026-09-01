"""Issue #2976 acceptance tests for `spawn.resolve_task_text()`: a task
body reaching `spawn.py --skills` only as a CLI argument has to survive
shell quoting whole -- a single `->` inside it is enough to make zsh fail
with a parse error (observed live). `--task-stdin` opens a second,
explicit channel without retiring the positional `<task>` form (#2572
fixed `--skills <skill> "<task>"` as the sole spawn form).

  python3 -m pytest tests/ -k task_from_stdin -q
  python3 -m pytest tests/ -k task_input_conflict_refused -q
  python3 -m pytest tests/ -k task_body_survives_shell_metacharacters -q
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class TaskFromStdinTest(unittest.TestCase):
    def test_task_from_stdin_used_when_no_positional(self):
        stream = io.StringIO("a long task body")
        result = spawn.resolve_task_text(None, True, stdin=stream)
        self.assertEqual(result, "a long task body")

    def test_positional_form_unchanged_as_default(self):
        # #2572 kept `--skills <skill> "<task>"` as the sole spawn form --
        # the positional path must stay byte-identical when --task-stdin
        # is not given, not merely "still work".
        result = spawn.resolve_task_text("a task", False)
        self.assertEqual(result, "a task")

    def test_stdin_flag_off_ignores_stdin_even_if_readable(self):
        stream = io.StringIO("should never be read")
        result = spawn.resolve_task_text("positional wins", False, stdin=stream)
        self.assertEqual(result, "positional wins")
        self.assertEqual(stream.tell(), 0)

    def test_neither_input_supplied_returns_falsy_for_caller_usage_error(self):
        # Decision-table 4th column (positional x stdin, both false): the
        # existing "usage: spawn.py --skills ..." exit lives in main(),
        # one level above resolve_task_text() -- this only pins that the
        # helper itself passes the falsy value through unchanged rather
        # than raising, so that caller-level check still fires.
        self.assertFalse(spawn.resolve_task_text(None, False))


class TaskInputConflictRefusedTest(unittest.TestCase):
    def test_task_input_conflict_refused_names_both(self):
        stream = io.StringIO("stdin body")
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolve_task_text("positional body", True, stdin=stream)
        message = str(ctx.exception.code)
        self.assertIn("positional body", message)
        self.assertIn("--task-stdin", message)

    def test_conflict_is_refused_not_resolved_by_precedence(self):
        # Neither input silently wins -- the call never returns.
        stream = io.StringIO("stdin body")
        with self.assertRaises(SystemExit):
            spawn.resolve_task_text("positional body", True, stdin=stream)


class TaskBodySurvivesShellMetacharactersTest(unittest.TestCase):
    def test_task_body_survives_shell_metacharacters(self):
        body = ("step one -> step two\n"
                 "quoted \"value\" and 'single'\n"
                 "third line")
        stream = io.StringIO(body)
        result = spawn.resolve_task_text(None, True, stdin=stream)
        self.assertEqual(result, body)

    def test_empty_body_boundary_survives_as_empty_string(self):
        # BVA boundary of the metacharacter-body partition: the shortest
        # possible stdin payload, zero characters.
        result = spawn.resolve_task_text(None, True, stdin=io.StringIO(""))
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
