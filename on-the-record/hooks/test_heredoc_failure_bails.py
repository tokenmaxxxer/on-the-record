"""issue #2962: a hook whose heredoc assignment fails exits at that point
instead of continuing into an unbound-variable error.

Real disk-full heredoc failure is not portably reproducible in a test
sandbox (bash falls back to a pipe for small heredocs on some platforms/
versions, and the failure is inherently disk-state-dependent -- the issue
itself was only observed live on macOS). What is tested instead, on the
three hooks.json registrations that actually use the
`read -r -d '' VAR <<'DELIM'` -> `python3 -c "$VAR"` shape
(stop-gate.sh, skill-verdict-guard.sh, post-landing-obligation-gate.sh):

1. a behavioral proof that the OLD pattern (bare `read` into an
   uninitialized variable under `set -u`) cascades into a second,
   unrelated "unbound variable" error, and the NEW pattern (pre-init +
   explicit bail check) does not -- the exact mechanism the fix relies on,
   independent of what actually caused the heredoc to come back empty;
2. a static check that each of the three real hook files pre-initializes
   its heredoc-read variable immediately before the read, and bails
   (exits) immediately after it if the variable ended up empty, before
   ever reaching `python3 -c "$VAR"`.

    python3 -m pytest on-the-record/hooks/ -k heredoc_failure_bails -q
"""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# (hook file, heredoc-read variable name)
FIXED_HOOKS = [
    ("stop-gate.sh", "CHECK"),
    ("skill-verdict-guard.sh", "CHECK"),
    ("post-landing-obligation-gate.sh", "GUARD"),
]


class HeredocFailureBailsPatternTest(unittest.TestCase):
    def test_old_pattern_cascades_into_unbound_variable_error(self):
        """Demonstrates the defect this issue names: a heredoc-read
        variable that was never assigned (the shell-level effect of a
        failed heredoc temp file) blows up on its next expansion under
        `set -u`, producing a SECOND, unrelated error."""
        res = subprocess.run(
            ["bash", "-c", 'set -u\nunset VAR\nprintf "%s" "$VAR"\n'],
            capture_output=True, text=True, timeout=10,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
        )
        self.assertNotEqual(res.returncode, 0, res)
        self.assertIn("unbound variable", res.stderr, res.stderr)

    def test_new_pattern_bails_cleanly_without_unbound_variable_error(self):
        """The fix: pre-initialize to empty, then explicitly bail before
        the variable is ever used for real work -- no unbound-variable
        cascade, and the exit is deliberate (a chosen nonzero, non-2 code:
        the platform's fail-open channel), not an accidental shell error."""
        res = subprocess.run(
            ["bash", "-c",
             'set -u\nVAR=""\n[ -n "$VAR" ] || exit 1\nprintf "%s" "$VAR"\n'],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(res.returncode, 1, res)
        self.assertNotIn("unbound variable", res.stderr, res.stderr)
        self.assertNotEqual(res.returncode, 2, "must not fail closed")


class HeredocFailureBailsRealHooksTest(unittest.TestCase):
    def test_each_fixed_hook_preinitializes_and_bails(self):
        for filename, varname in FIXED_HOOKS:
            with self.subTest(hook=filename):
                src = (HOOKS_DIR / filename).read_text()

                preinit_re = re.compile(
                    rf'{re.escape(varname)}=""\n'
                    rf"IFS='' read -r -d '' {re.escape(varname)} <<'PY' \|\| true"
                )
                self.assertRegex(
                    src, preinit_re,
                    f"{filename}: expected `{varname}=\"\"` immediately "
                    f"before the heredoc read of {varname}",
                )

                # the closing heredoc delimiter, then (before use) a bail
                # check that exits when the variable is empty.
                bail_re = re.compile(
                    r"\nPY\n\n"
                    rf'\[ -n "\${re.escape(varname)}" \] \|\| \{{[^\n]*exit 1; \}}\n',
                )
                self.assertRegex(
                    src, bail_re,
                    f"{filename}: expected a `[ -n \"${varname}\" ] || "
                    f"{{ ...; exit 1; }}` bail check right after the "
                    f"heredoc, before {varname} is used",
                )

                # the bail must exit before reaching `python3 -c "$VAR"`
                # (the actual invocation, at the end of the file -- take
                # the last occurrence of each in case either string is
                # also mentioned in a comment earlier in the file).
                bail_pos = src.rindex(f'[ -n "${varname}" ]')
                use_pos = src.rindex(f'python3 -c "${varname}"')
                self.assertLess(bail_pos, use_pos)

    def test_each_fixed_hook_still_parses_as_valid_bash(self):
        for filename, _ in FIXED_HOOKS:
            with self.subTest(hook=filename):
                res = subprocess.run(
                    ["bash", "-n", str(HOOKS_DIR / filename)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(res.returncode, 0, res.stderr)

    def test_bail_exit_code_is_never_2_deny(self):
        """must not: do not make any hook fail-closed. The bail's own exit
        code must not be the platform's block/deny code."""
        for filename, varname in FIXED_HOOKS:
            with self.subTest(hook=filename):
                src = (HOOKS_DIR / filename).read_text()
                m = re.search(
                    rf'\[ -n "\${re.escape(varname)}" \] \|\| \{{[^\n]*exit (\d+); \}}',
                    src,
                )
                self.assertIsNotNone(m, f"{filename}: no bail exit code found")
                self.assertNotEqual(m.group(1), "2", f"{filename} must not fail closed")


if __name__ == "__main__":
    unittest.main()
