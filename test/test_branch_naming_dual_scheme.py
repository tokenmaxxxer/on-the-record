"""Issue #2432 (role retirement stage 4): branch/record naming moves to the
skill axis + a lease disambiguator, alongside the existing role-axis naming
— not instead of it. Per docs/issue-2241/proposals/2026-08-25-stage-4-
branch-record-naming-cutover.md, `board.py`/`pipeline.py` read BOTH
`issue-<n>/<role>` and `issue-<n>/<skill>-<lease-disambiguator>` for a
stated coexistence window; old-scheme branches are never force-renamed.

These tests prove:
 - `pipeline.checkout_issue_branch_for_skill()` produces the new-scheme
   branch name and behaves like the existing `checkout_issue_branch()`
   otherwise (real git, local bare-repo origin — same harness shape as
   test_branch_role_field.py's `PrBodyTrailerWriteShapeTest`).
 - `pipeline.checkout_issue_branch()` (old scheme) stays byte-identical.
 - `board.board()`'s discovery walk surfaces a record under either
   naming scheme, and both appear together in one `board()` listing —
   the acceptance criterion this test file is named for.

Run: python3 -m pytest test/test_branch_naming_dual_scheme.py -q
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import spawn


def _init_bare_origin_and_clone(tmp: Path) -> Path:
    origin = tmp / "origin.git"
    work = tmp / "work"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    # bare 저장소가 아직 커밋이 없어도 HEAD symref 를 미리 main 으로 잡아둔다
    # — 안 그러면 아래 `remote set-head -a` 가 원격 HEAD 를 못 정한다(로컬
    # git 의 init.defaultBranch 설정과 무관하게 결정론적으로).
    subprocess.run(["git", "-C", str(origin), "symbolic-ref", "HEAD",
                    "refs/heads/main"], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"],
                    check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "t"], check=True)
    # 빈 bare 저장소는 기본 브랜치가 없다 — main 에 최초 커밋을 하나 만들고
    # push 해야 `_sp._base()`가 딛고 설 origin/HEAD 가 생긴다.
    subprocess.run(["git", "-C", str(work), "checkout", "-q", "-b", "main"], check=True)
    (work / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "seed"], check=True)
    subprocess.run(["git", "-C", str(work), "push", "-q", "-u", "origin", "main"],
                    check=True)
    subprocess.run(["git", "-C", str(work), "remote", "set-head", "origin", "-a"],
                    check=True)
    return work


def _git_current_branch(work: Path) -> str:
    r = subprocess.run(["git", "-C", str(work), "symbolic-ref", "--short", "HEAD"],
                        capture_output=True, text=True, check=True)
    return r.stdout.strip()


class CheckoutNamingSchemeTest(unittest.TestCase):
    def test_old_scheme_branch_shape_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = _init_bare_origin_and_clone(Path(tmp))
            br = spawn.checkout_issue_branch(str(work), 2432, "implementation")
            self.assertEqual(br, "issue-2432/implementation")
            self.assertEqual(_git_current_branch(work), br)

    def test_new_scheme_branch_shape_carries_skill_and_disambiguator(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = _init_bare_origin_and_clone(Path(tmp))
            br = spawn.checkout_issue_branch_for_skill(
                str(work), 2432, "implementation-blueprint", "a1b2c3d4")
            self.assertEqual(br, "issue-2432/implementation-blueprint-a1b2c3d4")
            self.assertEqual(_git_current_branch(work), br)

    def test_new_scheme_mints_a_disambiguator_when_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = _init_bare_origin_and_clone(Path(tmp))
            br = spawn.checkout_issue_branch_for_skill(
                str(work), 2432, "implementation-blueprint")
            self.assertRegex(br, r"^issue-2432/implementation-blueprint-[0-9a-f]{8}$")

    def test_new_scheme_disambiguator_feeds_lease_key_same_segment(self):
        # 제안서: "roster.py의 lease key가 <lease-disambiguator> 세그먼트를
        # 공급한다" — 브랜치 이름의 두 번째 세그먼트와 lease_key()의 두 번째
        # 세그먼트가 같은 문자열이어야, 그 disambiguator가 실제로 로스터
        # 충돌-방지 키로도 쓰인다.
        disambiguator = spawn.new_lease_disambiguator()
        with tempfile.TemporaryDirectory() as tmp:
            work = _init_bare_origin_and_clone(Path(tmp))
            br = spawn.checkout_issue_branch_for_skill(
                str(work), 2432, "implementation-blueprint", disambiguator)
        key = spawn.lease_key(2432, f"implementation-blueprint-{disambiguator}")
        self.assertEqual(br, f"issue-2432/implementation-blueprint-{disambiguator}")
        self.assertEqual(key, f"issue-2432/implementation-blueprint-{disambiguator}")
        self.assertEqual(br, key)


class DualSchemeBoardDiscoveryTest(unittest.TestCase):
    """board.py's discovery walk: a record under either naming scheme is
    board-visible, and both appear together in one board() listing."""

    def _write_record(self, root: Path, issue: int, name: str) -> Path:
        rep = root / "docs" / f"issue-{issue}" / "reports"
        rep.mkdir(parents=True, exist_ok=True)
        p = rep / f"{name}.md"
        p.write_text("---\nloop_state: in-progress\n---\nbody\n", encoding="utf-8")
        return p

    def test_old_scheme_role_record_stays_board_visible_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_record(root, 2432, "implementation")
            b = spawn.board(root)
            self.assertIn("implementation", b["issue-2432"])
            self.assertEqual(b["issue-2432"]["implementation"]["loop_state"],
                              "in-progress")

    def test_new_scheme_skill_record_is_board_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_record(root, 2432, "implementation-blueprint-a1b2c3d4")
            b = spawn.board(root)
            self.assertIn("implementation-blueprint-a1b2c3d4", b["issue-2432"])

    def test_both_schemes_appear_together_in_one_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_record(root, 2432, "implementation")
            self._write_record(root, 2432, "implementation-blueprint-a1b2c3d4")
            b = spawn.board(root)
            roles = b["issue-2432"]
            self.assertEqual(set(roles),
                              {"implementation", "implementation-blueprint-a1b2c3d4"})
            for name in roles:
                self.assertEqual(roles[name]["loop_state"], "in-progress")

    def test_non_record_md_file_in_reports_is_not_swept_in(self):
        # frontmatter 블록이 없는 잡파일은 새 스킬 축 레코드로 오인되면
        # 안 된다 — 이름 모양이 아니라 frontmatter 유무로 판별하는지 확인.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rep = root / "docs" / "issue-2432" / "reports"
            rep.mkdir(parents=True)
            (rep / "implementation.md").write_text(
                "---\nloop_state: in-progress\n---\nbody\n", encoding="utf-8")
            (rep / "notes.md").write_text("just some notes, no frontmatter\n",
                                           encoding="utf-8")
            b = spawn.board(root)
            self.assertEqual(set(b["issue-2432"]), {"implementation"})

    def test_nested_reports_subdir_not_swept_in(self):
        # docs/issue-<n>/reports/<role>/<file>.md 같은 중첩 구조(예:
        # architecture 역할의 survey.md/scout-brief.md)는 reports/ 바로
        # 아래가 아니므로 스킬 축 레코드로 잡히면 안 된다.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rep = root / "docs" / "issue-2432" / "reports"
            nested = rep / "architecture"
            nested.mkdir(parents=True)
            (rep / "architecture.md").write_text(
                "---\nloop_state: in-progress\n---\nbody\n", encoding="utf-8")
            (nested / "survey.md").write_text(
                "---\nloop_state: in-progress\n---\nnested\n", encoding="utf-8")
            b = spawn.board(root)
            self.assertEqual(set(b["issue-2432"]), {"architecture"})


if __name__ == "__main__":
    unittest.main()
