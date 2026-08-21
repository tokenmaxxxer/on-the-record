"""Equivalence-test harness for the 6 role-name-convention consumers (issue #1792).

Golden baseline for `issue-N/<role>`: pins today's parse/emit behavior of
each consumer on unmodified main, so every phase-5 migration sub-issue can
prove it changes nothing behaviorally. No convention/parser change lives
here; regexes below are literal reproductions of the hook-embedded copies
(hooks are heredoc'd shell+Python and not importable) with their
file:line provenance noted per the survey
(docs/issue-1792/reports/implementation/survey.md).
"""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "gates"))

import spawn  # noqa: E402
import flows  # noqa: E402

CONSUMERS = [
    "branch_names",
    "approve_grammar",
    "approval_gate",
    "board_records",
    "watch_roster",
    "rsb_status_board",
]


def test_consumer_count():
    assert len(CONSUMERS) == 6


# --- consumer 1: branch names -----------------------------------------------

# approval-gate.sh:106 / pr-preflight.sh:106 / contract-guard.sh:185
_HOOK_BRANCH_RE = re.compile(r"^issue-(\d+)/([\w-]+)$")
# gates/flows.py:32
_FLOWS_BRANCH_RE = flows._BRANCH_RE
# spawn.py:3115
_HEAD_REF_SUBJECT_RE = spawn._HEAD_REF_SUBJECT_RE
# spawn.py:4513
_LEGACY_WORKSPACE_KEY_RE = spawn._LEGACY_WORKSPACE_KEY_RE


class BranchNamesEquivalenceTest(unittest.TestCase):
    GOLDEN_MATCH = [
        # (branch, issue, role) — real repo branch (git rev-parse --abbrev-ref HEAD)
        ("issue-1792/implementation", "1792", "implementation"),
        ("issue-1/product-discovery", "1", "product-discovery"),
    ]
    GOLDEN_DIVERGENT = [
        # charset divergence the survey found: [\w-]+ (hooks) accepts these,
        # [a-z0-9-]+ (flows.py) rejects them (uppercase, underscore — digits
        # alone are accepted by both charsets, so not divergent)
        "issue-1/UPPERCASE",
        "issue-1/role_with_underscore",
    ]
    GOLDEN_NO_MATCH = [
        "issue-1",
        "not-a-branch",
        "issue-abc/implementation",
    ]

    def test_hook_trio_match_and_extract(self):
        for branch, issue, role in self.GOLDEN_MATCH:
            m = _HOOK_BRANCH_RE.match(branch)
            self.assertIsNotNone(m, branch)
            self.assertEqual(m.group(1), issue)
            self.assertEqual(m.group(2), role)

    def test_flows_match_and_extract(self):
        for branch, issue, role in self.GOLDEN_MATCH:
            m = _FLOWS_BRANCH_RE.match(branch)
            self.assertIsNotNone(m, branch)
            self.assertEqual(m.group(1), f"issue-{issue}")
            self.assertEqual(m.group(2), role)

    def test_charset_divergence_hooks_accept_flows_reject(self):
        for branch in self.GOLDEN_DIVERGENT:
            self.assertIsNotNone(_HOOK_BRANCH_RE.match(branch), branch)
            self.assertIsNone(_FLOWS_BRANCH_RE.match(branch), branch)

    def test_no_match_both(self):
        for branch in self.GOLDEN_NO_MATCH:
            self.assertIsNone(_HOOK_BRANCH_RE.match(branch), branch)
            self.assertIsNone(_FLOWS_BRANCH_RE.match(branch), branch)

    def test_head_ref_subject_re(self):
        m = _HEAD_REF_SUBJECT_RE.match("issue-1792/implementation")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "1792")
        self.assertIsNone(_HEAD_REF_SUBJECT_RE.match("not-a-branch"))

    def test_legacy_workspace_key_re(self):
        self.assertIsNotNone(_LEGACY_WORKSPACE_KEY_RE.match("issue-1792/implementation"))
        self.assertIsNone(_LEGACY_WORKSPACE_KEY_RE.match("issue-1792/a/b"))


# --- consumer 2: APPROVE token grammar --------------------------------------

# approval-gate.sh:176 / pr-preflight.sh:154
_CITE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+) VIA DELEGATION (\S+)$")


def _needle_exact(issue: int, role: str) -> str:
    """approval-gate.sh:166 / pr-preflight.sh:137"""
    return "APPROVE issue-%d/%s" % (issue, role)


def _needle_prefix(issue: int) -> str:
    """gates/ci.py / contract-guard.sh"""
    return "APPROVE issue-%d/" % issue


class ApproveGrammarEquivalenceTest(unittest.TestCase):
    # real recorded sample: docs/issue-983/reports/implementation.md:79
    REAL_APPROVED_983 = "APPROVE issue-983/implementation"
    # gates/test_delegation_metrics.py fixture comments
    REAL_APPROVED_707 = "APPROVE issue-707/implementation"
    REAL_DELEGATION_707 = "APPROVE issue-707/implementation VIA DELEGATION issue-707/implementation"
    # docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md:45-46
    # real near-miss cases: wrong subject / role-swapped
    REAL_NEAR_MISS_1 = "APPROVE issue-23/implementation"
    REAL_NEAR_MISS_2 = "APPROVE issue-227/rsb"

    def test_exact_match_semantics(self):
        self.assertEqual(_needle_exact(983, "implementation"), self.REAL_APPROVED_983)
        self.assertEqual(_needle_exact(707, "implementation"), self.REAL_APPROVED_707)
        self.assertNotEqual(_needle_exact(1792, "implementation"), self.REAL_NEAR_MISS_1)

    def test_prefix_match_semantics(self):
        prefix = _needle_prefix(983)
        self.assertTrue(self.REAL_APPROVED_983.startswith(prefix))
        self.assertFalse(self.REAL_NEAR_MISS_1.startswith(_needle_prefix(1792)))

    def test_delegation_citation_regex(self):
        m = _CITE_RE.match(self.REAL_DELEGATION_707)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "707")
        self.assertEqual(m.group(2), "implementation")
        self.assertEqual(m.group(3), "issue-707/implementation")
        self.assertIsNone(_CITE_RE.match(self.REAL_APPROVED_707))

    # issue #1818: field-present path equivalence — a structured approval
    # record (write-through cache of the needle scan itself) must yield
    # the same role set the comment-scan-only path derives on its own.
    def test_approved_roles_record_present_matches_scan_only(self):
        import tempfile
        import ci  # noqa: PLC0415 — local import mirrors flows import style above
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orig_approvers, orig_comments = spawn._approvers, spawn._issue_comments
            spawn._approvers = lambda repo: {"approver1"}
            spawn._issue_comments = lambda repo, issue: (
                [{"login": "approver1", "body": "APPROVE issue-9101/implementation"}], True)
            try:
                roles_scan_only = ci._approved_roles_on_issue(root, 9101)
                # second call: record now exists (write-through from the
                # first call) — comment scan still runs unmodified.
                roles_record_present = ci._approved_roles_on_issue(root, 9101)
            finally:
                spawn._approvers, spawn._issue_comments = orig_approvers, orig_comments
            self.assertEqual(roles_scan_only, {"implementation"})
            self.assertEqual(roles_record_present, roles_scan_only)

    def test_approved_roles_record_absent_matches_legacy_scan(self):
        import tempfile
        import ci  # noqa: PLC0415
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orig_approvers, orig_comments = spawn._approvers, spawn._issue_comments
            spawn._approvers = lambda repo: {"approver1"}
            spawn._issue_comments = lambda repo, issue: (
                [{"login": "approver1", "body": "APPROVE issue-9102/implementation"},
                 {"login": "not-an-approver", "body": "APPROVE issue-9102/review"}], True)
            try:
                self.assertFalse(spawn._approval_record_path(root, 9102).exists())
                roles = ci._approved_roles_on_issue(root, 9102)
            finally:
                spawn._approvers, spawn._issue_comments = orig_approvers, orig_comments
            self.assertEqual(roles, {"implementation"})

    def test_two_semantics_diverge_on_near_miss(self):
        # exact match rejects a role-swapped near-miss; prefix match (any
        # role) accepts it as long as the issue number matches — this is
        # the deliberate divergence the survey confirmed (section 2).
        exact_needle = _needle_exact(227, "implementation")
        self.assertNotEqual(self.REAL_NEAR_MISS_2, exact_needle)
        self.assertTrue(self.REAL_NEAR_MISS_2.startswith(_needle_prefix(227)))


# --- consumer 3: approval-gate hook -----------------------------------------

class ApprovalGateEquivalenceTest(unittest.TestCase):
    HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "approval-gate.sh"

    def test_hook_file_exists_and_has_expected_shape(self):
        self.assertTrue(self.HOOK_PATH.is_file())
        text = self.HOOK_PATH.read_text(encoding="utf-8")
        self.assertIn('re.match(r"^issue-(\\d+)/([\\w-]+)$", branch)', text)
        self.assertIn('needle = "APPROVE issue-%d/%s" % (issue, role)', text)
        self.assertIn(
            're.compile(r"^APPROVE issue-(\\d+)/([\\w-]+) VIA DELEGATION (\\S+)$")',
            text,
        )

    def test_branch_role_gate_logic_matches_survey(self):
        # lines 111-112: if role != branch_role: sys.exit(0) (fails open)
        text = self.HOOK_PATH.read_text(encoding="utf-8")
        self.assertIn("if role != branch_role:", text)

    def test_hook_reads_approval_record_path(self):
        # issue #1821: dual-reads the #1818 structured approval record
        # before the gh needle scan.
        text = self.HOOK_PATH.read_text(encoding="utf-8")
        self.assertIn('"gh-read-cache", "issue-%d-approvals.json" % issue', text)
        self.assertIn("if isinstance(record, dict) and role in record:", text)

    def test_hook_has_distinct_sidecar_vs_branch_mismatch_deny(self):
        # issue #1821: a NEW comparison, distinct from the existing,
        # untouched `if role != branch_role:` fallback-path check above —
        # this one compares the sidecar's own role/issue against an
        # independently branch-parsed role/issue once the sidecar has
        # already resolved.
        text = self.HOOK_PATH.read_text(encoding="utf-8")
        self.assertIn("if cross_issue != issue or cross_role != branch_role:", text)
        self.assertIn("disagrees with the", text)


# --- consumer 4: board records (zero role-name-parse-site consumer) --------

class BoardRecordsEquivalenceTest(unittest.TestCase):
    def test_board_matches_only_known_roles(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subj = root / "docs" / "issue-9001" / "reports"
            subj.mkdir(parents=True)
            known_role = spawn.ROLES[0]
            (subj / f"{known_role}.md").write_text("---\nloop_state: x\n---\n", encoding="utf-8")
            (subj / "not-a-real-role.md").write_text("---\n---\n", encoding="utf-8")
            result = spawn.board(root)
            self.assertIn("issue-9001", result)
            self.assertIn(known_role, result["issue-9001"])
            self.assertNotIn("not-a-real-role", result["issue-9001"])

    def test_roles_is_a_fixed_tuple_not_a_parse_site(self):
        self.assertIsInstance(spawn.ROLES, tuple)
        self.assertIn("implementation", spawn.ROLES)


# --- consumer 5: watch/roster ------------------------------------------------

class WatchRosterEquivalenceTest(unittest.TestCase):
    def test_live_roster_matches_key_split(self):
        matches = [("repo/issue-1792/implementation", {"work": "w"})]
        roster = {"issue-1792/implementation": {"pid": 999999999, "work": "w"}}
        orig = spawn._roster_load
        spawn._roster_load = lambda: roster
        try:
            alive_orig = spawn._alive
            spawn._alive = lambda pid: False
            try:
                result = spawn._live_roster_matches(matches, 1792)
                self.assertEqual(result, [])
            finally:
                spawn._alive = alive_orig
        finally:
            spawn._roster_load = orig

    def test_roster_fallback_entry_key_shape(self):
        roster = {"issue-1792/implementation": {"pid": 1, "work": "/w", "log": "/l"}}
        orig_load = spawn._roster_load
        orig_alive = spawn._alive
        orig_repo = spawn._repo_identity
        spawn._roster_load = lambda: roster
        spawn._alive = lambda pid: True
        spawn._repo_identity = lambda work: "repo"
        try:
            key, entry = spawn._roster_fallback_entry(1792, "implementation", None)
            self.assertEqual(key, "repo/issue-1792/implementation")
            self.assertEqual(entry, {"work": "/w", "log": "/l"})
        finally:
            spawn._roster_load = orig_load
            spawn._alive = orig_alive
            spawn._repo_identity = orig_repo

    def test_lookup_workspace_entry_suffix_match(self):
        idx = {"repoA/issue-1792/implementation": {"work": "/w"}}
        key, entry = spawn._lookup_workspace_entry(idx, 1792, "implementation", repo=None)
        self.assertEqual(key, "repoA/issue-1792/implementation")
        self.assertEqual(entry, {"work": "/w"})

    # issue #1803: field-present path equivalence — an explicit `role`
    # field on the entry must yield the same role the legacy key-split
    # would have derived from the same key.
    def test_live_roster_matches_field_read_matches_key_split(self):
        matches_field = [("repo/issue-1792/implementation",
                           {"work": "w", "role": "implementation"})]
        matches_split = [("repo/issue-1792/implementation", {"work": "w"})]
        roster = {"issue-1792/implementation": {"pid": 999999999, "work": "w"}}
        orig = spawn._roster_load
        spawn._roster_load = lambda: roster
        try:
            alive_orig = spawn._alive
            spawn._alive = lambda pid: False
            try:
                result_field = spawn._live_roster_matches(matches_field, 1792)
                result_split = spawn._live_roster_matches(matches_split, 1792)
                self.assertEqual(result_field, result_split)
            finally:
                spawn._alive = alive_orig
        finally:
            spawn._roster_load = orig

    def test_roster_fallback_entry_field_read_matches_key_split(self):
        roster_field = {"issue-1792/implementation":
                         {"pid": 1, "work": "/w", "log": "/l", "role": "implementation"}}
        roster_split = {"issue-1792/implementation": {"pid": 1, "work": "/w", "log": "/l"}}
        orig_load = spawn._roster_load
        orig_alive = spawn._alive
        orig_repo = spawn._repo_identity
        spawn._alive = lambda pid: True
        spawn._repo_identity = lambda work: "repo"
        try:
            spawn._roster_load = lambda: roster_field
            key_field, entry_field = spawn._roster_fallback_entry(1792, None, None)
            spawn._roster_load = lambda: roster_split
            key_split, entry_split = spawn._roster_fallback_entry(1792, None, None)
            self.assertEqual(key_field, key_split)
            self.assertEqual(entry_field, entry_split)
        finally:
            spawn._roster_load = orig_load
            spawn._alive = orig_alive
            spawn._repo_identity = orig_repo

    def test_lookup_workspace_entry_ambiguous_exit_field_read_matches_key_split(self):
        matches_field = [("repoA/issue-1792/implementation",
                           {"work": "/wa", "role": "implementation"}),
                          ("repoB/issue-1792/review",
                           {"work": "/wb", "role": "review"})]
        matches_split = [("repoA/issue-1792/implementation", {"work": "/wa"}),
                          ("repoB/issue-1792/review", {"work": "/wb"})]
        with self.assertRaises(SystemExit) as ctx_field:
            spawn._ambiguous_watch_exit(1792, matches_field, None)
        with self.assertRaises(SystemExit) as ctx_split:
            spawn._ambiguous_watch_exit(1792, matches_split, None)
        self.assertEqual(str(ctx_field.exception), str(ctx_split.exception))


# --- consumer 6: rsb status board -------------------------------------------

class RsbStatusBoardEquivalenceTest(unittest.TestCase):
    def test_branch_re_extracts_subject_and_role(self):
        m = flows._BRANCH_RE.match("issue-1792/implementation")
        self.assertIsNotNone(m)
        self.assertEqual((m.group(1), m.group(2)), ("issue-1792", "implementation"))

    def test_pr_approved_needle_shape(self):
        comments = [{"body": "APPROVE issue-1792/implementation", "login": "approver1"}]
        approved = flows._pr_approved(
            {"reviews": []}, comments, {"approver1"}, "issue-1792", "implementation"
        )
        self.assertTrue(approved)

    def test_pr_approved_rejects_role_mismatch(self):
        comments = [{"body": "APPROVE issue-1792/product-discovery", "login": "approver1"}]
        approved = flows._pr_approved(
            {"reviews": []}, comments, {"approver1"}, "issue-1792", "implementation"
        )
        self.assertFalse(approved)

    def test_plan_from_body_parses_role_checklist(self):
        body = (
            "## 실행 계획\n"
            "- [ ] step 1 implementation\n"
            "- [x] step 2 conformance-review ‖ defect-verification\n"
        )
        plan = flows._plan_from_body(body)
        self.assertEqual(
            plan,
            [
                {"step": 1, "roles": ["implementation"], "done": False},
                {"step": 2, "roles": ["conformance-review", "defect-verification"], "done": True},
            ],
        )


# --- issue #1814: explicit-carrier dual-read/fallback equivalence ----------
# Golden baseline for the branch-role field migration: additions only, per
# the frozen migration order's zero-convention-bugs constraint. Proves the
# 4 sites' carrier-absent fallback path stays byte-identical to today's
# regex-only behavior, and that the carrier-present path (when read)
# resolves to the same role a fallback parse of a matching branch would.

class BranchRoleFieldDualReadEquivalenceTest(unittest.TestCase):
    HOOK_PATHS = {
        "approval_gate": REPO_ROOT / "on-the-record" / "hooks" / "approval-gate.sh",
        "pr_preflight": REPO_ROOT / "on-the-record" / "hooks" / "pr-preflight.sh",
        "contract_guard": REPO_ROOT / "on-the-record" / "hooks" / "contract-guard.sh",
    }

    def test_hooks_retain_original_fallback_regex_verbatim(self):
        # the exact fallback line each hook fell back to before #1814 must
        # still be present, unchanged, in every hook's source.
        for path in self.HOOK_PATHS.values():
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                're.match(r"^issue-(\\d+)/([\\w-]+)$"', text,
                msg=f"{path} lost its branch-regex fallback",
            )

    def test_hooks_read_role_json_sidecar_before_falling_back(self):
        for path in self.HOOK_PATHS.values():
            text = path.read_text(encoding="utf-8")
            self.assertIn(".on-the-record", text)
            self.assertIn("role.json", text)

    def test_flows_role_from_pr_prefers_trailer_over_branch_group(self):
        m = flows._BRANCH_RE.match("issue-1792/implementation")
        self.assertIsNotNone(m)
        pr_with_trailer = {"body": "Part of #1792.\n\nrole: product-discovery"}
        self.assertEqual(
            flows._role_from_pr(pr_with_trailer, m), "product-discovery"
        )

    def test_flows_role_from_pr_falls_back_to_branch_group_when_absent(self):
        # carrier-absent case: identical to pre-#1814 pr_by_branch role.
        m = flows._BRANCH_RE.match("issue-1792/implementation")
        self.assertIsNotNone(m)
        pr_without_trailer = {"body": "Part of #1792.\n\nno role line here."}
        self.assertEqual(flows._role_from_pr(pr_without_trailer, m), m.group(2))
        pr_no_body = {"body": None}
        self.assertEqual(flows._role_from_pr(pr_no_body, m), m.group(2))


if __name__ == "__main__":
    unittest.main()
