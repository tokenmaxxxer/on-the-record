"""이슈 #2241 stage 2 (docs/specs/consult-guidance-source.md): consult.py 가
가이던스 콘텐츠를 위해 rulebook/plugin-repo identity 를 읽는 코드 경로를
다시 들이는 회귀를 막는다.

이슈 #1955 phase 2(commit ac4d56a0)가 전이용 role-source-allowlist/rulebook
해석 경로(`rulebook_checkout`, `_role_source_allowlist`, `checkout_version`,
`docs/specs/role-source-allowlist.json`)를 완전히 지웠다 — 가이던스 콘텐츠는
이제 무조건 `resolve_role_source()`(skills.py) 를 거쳐 skill-repository 에서
온다. 이 스테이지는 그 상태를 바꾸지 않고 확인·회귀-가드만 한다(제안서
Constraints: `_ROLE_SKILLS`/`roles/<role>.json` existence-check 는 그대로).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn

_CONSULT_PY = Path(__file__).resolve().parent.parent / "consult.py"

# 이슈 #1955 가 지운, "가이던스 소스가 role 별로 갈릴 수 있다"는 상태 자체를
# 나타내던 식별자들 — 이 이름들 중 하나라도 consult.py 에 다시 나타나면 그
# 전이용 분기가 되살아났다는 신호다.
_FORBIDDEN_TOKENS = (
    "rulebook_checkout",
    "_role_source_allowlist",
    "checkout_version",
    "role-source-allowlist",
    "ROLE_SOURCE_ALLOWLIST",
)


class NoRulebookIdentityInSource(unittest.TestCase):
    def test_consult_py_carries_no_forbidden_rulebook_identifiers(self):
        source = _CONSULT_PY.read_text(encoding="utf-8")
        found = [tok for tok in _FORBIDDEN_TOKENS if tok in source]
        self.assertEqual(found, [],
                          f"consult.py 가 은퇴한 rulebook/allowlist 식별자를 다시 물었다: {found}")


class ReadonlyPluginDirsUnconditionalSkillRepo(unittest.TestCase):
    """`_readonly_plugin_dirs()`(judge 경로가 쓰는 가이던스 조립 함수)가
    `role` 이 `_ROLE_SKILLS` 에 없는 이름이어도(즉 "매핑 안 됨" 이라는 상태가
    없어도) 조건 분기 없이 `resolve_role_source()` 하나로만 가이던스를
    조립하는지 — 소스 파일이 아니라 실제 호출 경로로 확인한다."""

    def setUp(self):
        self._saved_resolve = spawn.resolve_role_source
        self._saved_core = spawn.core_plugin_dirs
        self._calls = []

        def fake_resolve(role, repo_root):
            self._calls.append(role)
            return {"source": "skill-repo", "skill_dirs": [Path("/fake/skill-repo/x")],
                    "skills": ["x"], "skill_sha": "abc1234"}

        spawn.resolve_role_source = fake_resolve
        spawn.core_plugin_dirs = lambda: []

    def tearDown(self):
        spawn.resolve_role_source = self._saved_resolve
        spawn.core_plugin_dirs = self._saved_core

    def test_unmapped_role_still_resolves_through_resolve_role_source(self):
        out = spawn._readonly_plugin_dirs("no-such-role-anywhere", {})
        self.assertEqual(self._calls, ["no-such-role-anywhere"])
        self.assertEqual(out, [Path("/fake/skill-repo/x")])

    def test_mapped_role_takes_the_same_single_path(self):
        role = next(iter(spawn._ROLE_SKILLS))
        out = spawn._readonly_plugin_dirs(role, {})
        self.assertEqual(self._calls, [role])
        self.assertEqual(out, [Path("/fake/skill-repo/x")])


if __name__ == "__main__":
    unittest.main()
