"""issue #2962: every hooks.json command registration is classified as
invariant-injecting or observability, and the classification is data a
reader can check (hook_classification.json), not a claim in prose.

    python3 -m pytest on-the-record/hooks/ -k hook_classification -q
"""
from __future__ import annotations

import json
import re
import shlex
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOKS_JSON = HOOKS_DIR / "hooks.json"
CLASSIFICATION_JSON = HOOKS_DIR / "hook_classification.json"
FAIL_OPEN_WRAPPER = HOOKS_DIR / "fail-open-wrapper.sh"

VALID_CLASSES = {"invariant-injecting", "observability"}


def _basename(token: str) -> str:
    return token.rsplit("/", 1)[-1]


def registrations_from_hooks_json() -> list[tuple[str, str, tuple[str, ...], bool]]:
    """(event, script_basename, args, wrapped) for every command registered
    in hooks.json, in file order."""
    data = json.loads(HOOKS_JSON.read_text())
    out: list[tuple[str, str, tuple[str, ...], bool]] = []
    for event, groups in data.get("hooks", {}).items():
        for group in groups:
            for entry in group.get("hooks", []):
                if entry.get("type") != "command":
                    continue
                tokens = shlex.split(entry["command"])
                assert tokens, f"empty command for event {event}"
                if _basename(tokens[0]) == "fail-open-wrapper.sh":
                    wrapped = True
                    script = _basename(tokens[1])
                    args = tuple(tokens[2:])
                else:
                    wrapped = False
                    script = _basename(tokens[0])
                    args = tuple(tokens[1:])
                out.append((event, script, args, wrapped))
    return out


def load_classification() -> list[dict]:
    return json.loads(CLASSIFICATION_JSON.read_text())["registrations"]


class HookClassificationTest(unittest.TestCase):
    def test_every_hooks_json_registration_has_a_classification_entry(self):
        live = registrations_from_hooks_json()
        classified = {
            (r["event"], r["script"], tuple(r["args"]), r["wrapped"])
            for r in load_classification()
        }
        missing = [r for r in live if r not in classified]
        self.assertEqual(
            missing, [],
            f"hooks.json registration(s) with no matching hook_classification.json "
            f"entry: {missing}",
        )

    def test_classification_has_no_orphan_or_duplicate_entries(self):
        live = registrations_from_hooks_json()
        live_set = set(live)
        self.assertEqual(
            len(live), len(live_set),
            "hooks.json itself has a duplicate (event, script, args, wrapped) "
            "registration -- classification cannot be keyed on it",
        )
        entries = load_classification()
        classified_keys = [
            (r["event"], r["script"], tuple(r["args"]), r["wrapped"])
            for r in entries
        ]
        self.assertEqual(
            len(classified_keys), len(set(classified_keys)),
            "hook_classification.json has a duplicate registration entry",
        )
        orphans = [k for k in classified_keys if k not in live_set]
        self.assertEqual(
            orphans, [],
            f"hook_classification.json entries with no matching hooks.json "
            f"registration (stale data): {orphans}",
        )

    def test_every_entry_has_a_valid_class(self):
        entries = load_classification()
        self.assertTrue(entries, "hook_classification.json has no registrations")
        for r in entries:
            self.assertIn(
                r.get("class"), VALID_CLASSES,
                f"{r['event']}/{r['script']}{list(r['args'])}: "
                f"class must be one of {VALID_CLASSES}, got {r.get('class')!r}",
            )

    def test_registration_count_matches_the_issues_own_count(self):
        # issue #2962's own verified-wiring count was 12 registrations, 11
        # wrapped by fail-open-wrapper.sh, 1 (pretooluse-dispatcher.sh)
        # deliberately unwrapped/fail-closed. issue #3073: PR #2872 added
        # gate-registration-post-guard.sh's pre/post pair (both wrapped),
        # raising the live count to 14 (13 wrapped, 1 unwrapped). issue
        # #3129 added amendment-channel.sh (wrapped) and (unrecorded by this
        # comment at the time) amends-landing-apply.sh (wrapped), actually
        # raising it to 16 (15 wrapped, 1 unwrapped) -- this comment's own
        # count had drifted from the live registration count it exists to
        # track, exactly the drift this test catches. issue #3231 added
        # skill-corpus-bootstrap.sh and install-precondition-notices.sh
        # (both wrapped) and classified the orphaned amends-landing-apply.sh
        # entry, landing on 18 (17 wrapped, 1 unwrapped). issue #3229 added
        # delegation-live-check.sh (wrapped), raising it to 19 (18 wrapped,
        # 1 unwrapped) -- this literal is meant to move again the next time
        # a hook is legitimately registered; it exists to catch drift, not
        # to freeze the count at any one issue's number.
        live = registrations_from_hooks_json()
        self.assertEqual(len(live), 19, live)
        self.assertEqual(sum(1 for r in live if r[3]), 18, live)
        self.assertEqual(sum(1 for r in live if not r[3]), 1, live)

    def test_pretooluse_dispatcher_is_classified_but_unwrapped(self):
        entries = {(r["script"], tuple(r["args"])): r for r in load_classification()}
        d = entries.get(("pretooluse-dispatcher.sh", ()))
        self.assertIsNotNone(d, "pretooluse-dispatcher.sh must still be classified")
        self.assertFalse(
            d["wrapped"],
            "pretooluse-dispatcher.sh must stay unwrapped (deliberately "
            "fail-closed) -- issue #2962 must not: do not change its "
            "fail-closed posture in either direction",
        )

    def test_wrapper_notice_case_list_matches_wrapped_invariant_injecting_entries(self):
        """The fail-open-wrapper.sh `case` statement that decides whether to
        print the visible in-band notice must name exactly the WRAPPED
        invariant-injecting hooks from hook_classification.json -- no more,
        no fewer. This is the drift check: two representations of the same
        classification (data file vs. enforcement code) that could silently
        diverge otherwise.
        """
        wrapper_src = FAIL_OPEN_WRAPPER.read_text()
        m = re.search(
            r'case "\$_hook_name" in\s*\n\s*([\w.\-]+(?:\|[\w.\-]+)*)\)',
            wrapper_src,
        )
        self.assertIsNotNone(
            m, "could not find the invariant-injecting case pattern list in "
            "fail-open-wrapper.sh -- did its shape change?",
        )
        wrapper_names = set(m.group(1).split("|"))

        expected = {
            r["script"] for r in load_classification()
            if r["wrapped"] and r["class"] == "invariant-injecting"
        }
        self.assertEqual(wrapper_names, expected)


if __name__ == "__main__":
    unittest.main()
