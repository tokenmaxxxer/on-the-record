"""issue #2241 stage 5: `gates/merge_gate.py::required_verification_missing`
and `gates/spawn_on_pr.py::applicable_record_kinds` match on the `kind:`
frontmatter field instead of a role-named file on the board, and the
self-verification guard (a `kind:` match whose `author:` equals the
subject's own `author:` does not count) actually blocks."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import spawn_on_pr  # noqa: E402
import merge_gate  # noqa: E402


class ApplicableRecordKindsTest(unittest.TestCase):
    def test_both_present_different_authors_reports_none_missing(self):
        board = {
            "execution-observation": {"kind": "execution-observation", "author": "execution-observation"},
            "conformance-review": {"kind": "conformance-review", "author": "conformance-review"},
        }
        missing = spawn_on_pr.applicable_record_kinds(board, subject_author="implementation")
        self.assertEqual(missing, [])

    def test_one_missing_reported_by_record_kind_name(self):
        board = {
            "execution-observation": {"kind": "execution-observation", "author": "execution-observation"},
        }
        missing = spawn_on_pr.applicable_record_kinds(board, subject_author="implementation")
        self.assertEqual(missing, ["conformance-review"])

    def test_kind_field_wins_over_filename(self):
        # A skill-axis-named file whose kind: still identifies it correctly.
        board = {"perf-a1b2c3d4": {"kind": "conformance-review", "author": "conformance-review"}}
        missing = spawn_on_pr.applicable_record_kinds(board, subject_author="implementation")
        self.assertEqual(missing, ["execution-observation"])

    def test_self_verification_guard_blocks_same_author_as_subject(self):
        board = {
            "execution-observation": {"kind": "execution-observation", "author": "implementation"},
            "conformance-review": {"kind": "conformance-review", "author": "conformance-review"},
        }
        missing = spawn_on_pr.applicable_record_kinds(board, subject_author="implementation")
        self.assertEqual(missing, ["execution-observation"])

    def test_no_subject_author_skips_the_guard(self):
        board = {"execution-observation": {"kind": "execution-observation", "author": "implementation"}}
        missing = spawn_on_pr.applicable_record_kinds(board, subject_author=None)
        self.assertEqual(missing, ["conformance-review"])

    def test_legacy_record_without_kind_field_falls_back_to_filename(self):
        board = {"execution-observation": {"loop_state": "landed"}}
        missing = spawn_on_pr.applicable_record_kinds(board)
        self.assertEqual(missing, ["conformance-review"])


class ExemptOwnRecordKindTest(unittest.TestCase):
    def test_drops_only_the_supplying_prs_own_kind(self):
        # issue #2380: 형제-예외 대상(PR_TRIGGERED_RECORD_KINDS) 밖의 kind 는
        # 오늘처럼 자기 것 하나만 빠진다 — subject 의 implementation PR 은
        # 여전히 두 관찰자 기록을 모두 요구한다. 형제 쌍 케이스는 아래
        # test_sibling_observer_pair_both_exempt 가 따로 고정한다.
        missing = ["implementation", "execution-observation", "conformance-review"]
        own = merge_gate._exempt_own_record_kind(
            missing, "issue-2204", "issue-2204/implementation")
        self.assertEqual(own, ["execution-observation", "conformance-review"])

    def test_sibling_observer_pair_both_exempt(self):
        # issue #2380 (stage 5 하에서 record-kind 축으로 재키잉): 같은 리뷰
        # 사이클에 나란히 열린 두 관찰자 PR 이 서로의 선행 머지를 요구하는
        # 순환을 깬다 — 자기 kind 가 형제 쌍 안이면 둘 다 빠진다.
        missing = ["execution-observation", "conformance-review"]
        own = merge_gate._exempt_own_record_kind(
            missing, "issue-2204", "issue-2204/execution-observation")
        self.assertEqual(own, [])
        mirror = merge_gate._exempt_own_record_kind(
            missing, "issue-2204", "issue-2204/conformance-review")
        self.assertEqual(mirror, [])

    def test_other_subjects_pr_is_a_no_op(self):
        missing = ["execution-observation", "conformance-review"]
        other = merge_gate._exempt_own_record_kind(
            missing, "issue-2204", "issue-9999/implementation")
        self.assertEqual(other, missing)

    def test_no_pr_context_is_a_no_op(self):
        missing = ["execution-observation", "conformance-review"]
        self.assertEqual(
            merge_gate._exempt_own_record_kind(missing, "issue-2204", None), missing)


class RequiredVerificationMissingIntegrationTest(unittest.TestCase):
    def test_reads_subject_author_from_the_implementation_record(self):
        import spawn

        board = {
            "issue-2204": {
                "implementation": {"role": "implementation", "author": "implementation"},
                "execution-observation": {"kind": "execution-observation", "author": "implementation"},
                "conformance-review": {"kind": "conformance-review", "author": "conformance-review"},
            }
        }
        orig_board = spawn.board
        spawn.board = lambda root: board
        try:
            missing = merge_gate.required_verification_missing(Path("."), "issue-2204")
        finally:
            spawn.board = orig_board
        # execution-observation was self-authored by "implementation" -- does
        # not satisfy the requirement (self-verification guard).
        self.assertEqual(missing, ["execution-observation"])


if __name__ == "__main__":
    unittest.main()
