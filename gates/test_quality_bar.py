"""issue #1156: gates/quality_bar.py classifier tests — the five acceptance
scenarios named in docs/issue-1156/proposals/per-role-quality-bars.md's
"How you'll know it worked" section, plus the reject-cap escalation and
bar_scoped_roles helper."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import quality_bar


def test_no_bar_scoped_change_passes_through():
    assert quality_bar.classify(False, None, None, None) == (quality_bar.NO_BAR_SCOPED, None)


def test_bar_scoped_no_record_is_bar_not_met():
    status, reason = quality_bar.classify(True, None, None, None)
    assert status == quality_bar.BAR_NOT_MET
    assert reason == "no bar-met record"


def test_bar_scoped_bar_met_record_from_different_role_is_bar_met():
    status, reason = quality_bar.classify(True, "bar-met", "acct-reviewer", "acct-producer")
    assert status == quality_bar.BAR_MET
    assert reason is None


def test_bar_scoped_bar_met_record_authored_by_producer_itself_is_bar_not_met():
    status, reason = quality_bar.classify(True, "bar-met", "acct-same", "acct-same")
    assert status == quality_bar.BAR_NOT_MET
    assert "same account" in reason


def test_same_account_wins_even_if_claude_role_differed_at_authoring_time():
    # anti-circularity is account-resolved, not CLAUDE_ROLE-string-resolved
    # (proposal §4 same-operator bypass finding) — this test asserts the
    # classifier's own contract: callers must never pass a bare CLAUDE_ROLE
    # value as either account argument.
    status, reason = quality_bar.classify(True, "bar-met", "acct-same", "acct-same",
                                           consecutive_bar_not_met_count=0)
    assert status == quality_bar.BAR_NOT_MET


def test_third_consecutive_bar_not_met_escalates():
    status1, _ = quality_bar.classify(True, "bar-not-met", "acct-a", "acct-b",
                                       consecutive_bar_not_met_count=0)
    status2, _ = quality_bar.classify(True, "bar-not-met", "acct-a", "acct-b",
                                       consecutive_bar_not_met_count=1)
    status3, reason3 = quality_bar.classify(True, "bar-not-met", "acct-a", "acct-b",
                                             consecutive_bar_not_met_count=2)
    assert status1 == quality_bar.BAR_NOT_MET
    assert status2 == quality_bar.BAR_NOT_MET
    assert status3 == quality_bar.ESCALATE
    assert reason3 == "bar-not-met verdict recorded"


def test_escalate_persists_beyond_the_cap():
    status, _ = quality_bar.classify(True, "bar-not-met", "acct-a", "acct-b",
                                      consecutive_bar_not_met_count=5)
    assert status == quality_bar.ESCALATE


def test_bar_scoped_roles_matches_glob_patterns():
    patterns = {
        "ux-engineering": ["**/*.tsx", "**/*.jsx"],
        "secure-coding": ["**/auth/**"],
    }
    scoped = quality_bar.bar_scoped_roles(
        ["src/components/Button.tsx", "src/server.py"], patterns
    )
    assert scoped == frozenset({"ux-engineering"})


def test_bar_scoped_roles_empty_when_no_pattern_matches():
    patterns = {"secure-coding": ["**/auth/**"]}
    scoped = quality_bar.bar_scoped_roles(["src/server.py"], patterns)
    assert scoped == frozenset()


def test_bar_scoped_roles_ignores_role_with_no_patterns():
    patterns = {"some-role": []}
    scoped = quality_bar.bar_scoped_roles(["anything.py"], patterns)
    assert scoped == frozenset()


# issue #1160 step 3 machinery: mission_bar_scoped / verified_by_account /
# bar-verdict linkage anti-circularity.

def test_mission_bar_scoped_matches_deliverable_glob():
    assert quality_bar.mission_bar_scoped(
        ["design-tokens/colors.json"], ["design-tokens/*.json"]
    ) is True


def test_mission_bar_scoped_false_when_no_deliverable_touched():
    assert quality_bar.mission_bar_scoped(
        ["src/server.py"], ["design-tokens/*.json"]
    ) is False


def test_mission_bar_scoped_false_when_no_patterns():
    assert quality_bar.mission_bar_scoped(["anything.json"], []) is False


def test_verified_by_account_resolves_leading_role_token():
    spec = {"verified_by": "ux-engineering — brand-design never grades its own mission_deliverables"}
    resolved = quality_bar.verified_by_account(spec, lambda role: f"acct-{role}")
    assert resolved == "acct-ux-engineering"


def test_verified_by_account_none_when_field_absent():
    assert quality_bar.verified_by_account({}, lambda role: f"acct-{role}") is None


def test_bar_verdict_linkage_anti_circular_when_verified_by_resolves_to_producer():
    # producer role (e.g. brand-design) and the resolved verified_by
    # account collide onto the same account -> classify must still refuse
    # (proving mission_bar_scoped/verified_by_account feed classify's
    # existing anti-circularity rather than bypassing it).
    spec = {"verified_by": "brand-design — self-referential for this test"}
    resolved_verifier_account = quality_bar.verified_by_account(
        spec, lambda role: "acct-same"
    )
    bar_scoped = quality_bar.mission_bar_scoped(
        ["design-tokens/colors.json"], ["design-tokens/*.json"]
    )
    status, reason = quality_bar.classify(
        bar_scoped, "bar-met", resolved_verifier_account, "acct-same"
    )
    assert status == quality_bar.BAR_NOT_MET
    assert "same account" in reason


def test_bar_verdict_linkage_bar_met_when_verifier_differs_from_producer():
    spec = {"verified_by": "ux-engineering — differing verifier"}
    resolved_verifier_account = quality_bar.verified_by_account(
        spec, lambda role: "acct-ux-engineering"
    )
    bar_scoped = quality_bar.mission_bar_scoped(
        ["design-tokens/colors.json"], ["design-tokens/*.json"]
    )
    status, reason = quality_bar.classify(
        bar_scoped, "bar-met", resolved_verifier_account, "acct-brand-design"
    )
    assert status == quality_bar.BAR_MET
    assert reason is None
