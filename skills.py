"""Skill-resolution machinery (skill repo discovery, --skills resolution,
role -> skill-source mapping, roster provenance fields), extracted from
spawn.py (issue #2105, extraction 7/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py/
watchdog.py/events.py/consult.py, extractions 1-6): every cross-function
reference here resolves at call time through `_sp` — the spawn module
object, injected by spawn.py right after it imports this module (guarded so
only the canonical spawn/__main__ module binds it), so
`mock.patch.object(spawn, "<name>")` patches stay visible to the moved
code. Cluster-internal cross-function calls also go through `_sp`.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

def _core_candidates() -> list[tuple[str, Path]]:
    """core_root() 가 순서대로 보는 로컬 오버라이드 후보 (라벨, 경로).
    관리 클론(runs/rulebooks/tokenmaxxxer-core)은 이 목록 밖 — 둘 다
    없을 때만 core_root() 가 그리로 떨어지는 별도 단계라 후보가 아니다.
    """
    return [
        ("TOKENMAXXXER_CORE", os.environ.get("TOKENMAXXXER_CORE")),
        ("TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core",
         "$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core"),
    ]


def _skill_repo_valid(d: Path) -> bool:
    """`d` 를 `resolved_skill_dirs()` 가 이미 쓰는 것과 같은 바로 그 기준으로
    "실제 체크아웃"으로 본다: non-dot 서브디렉터리가 하나라도 있는
    디렉터리(요구사항 2 — env/sibling/managed 세 경로 모두 같은 바)."""
    if not d.is_dir():
        return False
    return any(p.is_dir() and not p.name.startswith(".") for p in d.iterdir())


def _skill_repo_managed_root() -> Path | None:
    """관리 클론(이슈 #1789): env 도 형제 체크아웃도 없을 때 on-the-record 가
    직접 `https://github.com/tokenmaxxxer/skill-repository` 를 관리 영역에
    받아 쓴다 — `core_root()` 가 이미 쓰는 다섯 단계
    (로컬 오버라이드 확인은 호출자 쪽에서 이미 끝남 → 관리 디렉터리 유효성
    확인 → 신선하면 재사용 → 아니면 pull-or-clone → 재확인) 를 그대로
    따른다. 네트워크가 죽었을 때 기존 관리 클론이 있으면 그걸 그대로 쓴다
    (오프라인 재사용, 요구사항 1).

    저장소 최상위가 아니라 그 안의 `skills/` 서브디렉터리를 돌려준다 —
    env(`MUSTER_SKILL_REPO`)와 sibling(`$TOKENMAXXXER_RULEBOOKS/
    skill-repository`) 두 경로 모두 실측상 이미 `skills/` 를 직접 가리키고
    있고(레포 최상위에는 skills 외에도 docs/scripts/install.sh 가 있다),
    `resolved_skill_dirs()` 는 그 셋을 구분 없이 같은 root 로 받는다 —
    요구사항 2 의 "env-pointed checkout 과 동일한 스킬 해석"이 성립하려면
    관리 클론도 같은 `skills/` 레벨을 돌려줘야 한다."""
    d = _sp.ROOT / "runs" / "rulebooks" / "skill-repository"
    d.parent.mkdir(parents=True, exist_ok=True)
    with _sp._locked_rulebook_dir(d):
        skills_dir = d / "skills"
        if _sp._skill_repo_valid(skills_dir):
            if not _sp._pull_is_fresh(d):
                _sp._run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                         "[skill-repo] pull")
                _sp._mark_pulled(d)
            return skills_dir
        try:
            print("[skill-repo] skill-repository 를 받는 중", file=sys.stderr)
            _sp._run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/skill-repository.git",
                     str(d)], "[skill-repo] clone", timeout=_sp.CLONE_TIMEOUT)
            _sp._mark_pulled(d)
        except OSError:
            pass
        if _sp._skill_repo_valid(skills_dir):
            return skills_dir
    return None


def _skill_repo_root() -> Path | None:
    """`--skills` 가 마운트할 skill-repository 체크아웃 루트. 순서:
    `MUSTER_SKILL_REPO` env > 형제 클론 (`$TOKENMAXXXER_RULEBOOKS/
    skill-repository`) > 관리 클론(이슈 #1789 — skill-repository가 공개된
    뒤로는 on-the-record 소유 클론이 다른 관리 체크아웃과 같은 fallback을
    쓸 수 있다). 셋 다 없으면 `None`."""
    env_value = os.environ.get("MUSTER_SKILL_REPO")
    if env_value:
        p = Path(os.path.expanduser(os.path.expandvars(env_value)))
        if p.is_dir():
            return p
    sibling = os.path.expandvars("$TOKENMAXXXER_RULEBOOKS/skill-repository")
    if "$" not in sibling:
        p = Path(os.path.expanduser(sibling))
        if p.is_dir():
            return p
    return _sp._skill_repo_managed_root()


def resolved_skill_dirs(skills_csv: str | None,
                         repo_root: Path | None) -> list[Path]:
    """`--skills a,b,c` 를 skill-repository 체크아웃 안의 디렉터리 목록으로
    푼다. `skills_csv` 가 비면 빈 목록(마운트 없음, byte-identical 경로).
    이름 하나라도 `<repo_root>/<name>` 으로 해석되지 않으면 워크스페이스/
    브랜치를 건드리기 전에 fail-closed(이슈 #1742 요구사항 2)."""
    names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not names:
        return []
    if repo_root is None:
        sys.exit("--skills: skill-repository 체크아웃을 못 찾았다 — "
                  "MUSTER_SKILL_REPO 나 $TOKENMAXXXER_RULEBOOKS/skill-repository 를 확인하고, "
                  "관리 클론도 시도했지만(네트워크나 기존 클론 없음) 실패했다")
    available = sorted(p.name for p in repo_root.iterdir()
                        if p.is_dir() and not p.name.startswith("."))
    unknown = [n for n in names if n not in available]
    if unknown:
        sys.exit(f"--skills: 모르는 스킬 {', '.join(unknown)} "
                  f"— 쓸 수 있는 이름: {', '.join(available)}")
    return [repo_root / n for n in names]


def _installed_plugin_skill_dirs() -> dict[str, list[tuple[str, Path, str]]]:
    """`~/.claude/plugins/installed_plugins.json` (실제 shape:
    `{"plugins": {"<name>@<marketplace>": [{"installPath":...,
    "version"|"gitCommitSha":...}, ...]}}`, `_installed()` 와 같은 파일)을
    읽어 설치된 각 플러그인의 `skills/<name>/` 서브디렉터리를 이름별로
    인덱싱한다: name -> [(qualifier "<name>@<marketplace>", 디렉터리,
    version-or-sha 문자열), ...]. 파일이 없거나 못 읽으면 빈 매핑(이슈
    #1774 요구사항 4: 이 함수는 `--skills` 가 실제로 이름을 낼 때만
    불린다)."""
    p = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(p.read_text())
    except (OSError, ValueError):
        return {}
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return {}
    index: dict[str, list[tuple[str, Path, str]]] = {}
    for qualifier, entries in plugins.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            if not isinstance(e, dict):
                continue
            install_path = e.get("installPath")
            if not install_path:
                continue
            skills_root = Path(install_path) / "skills"
            if not skills_root.is_dir():
                continue
            version = e.get("version") or e.get("gitCommitSha") or "?"
            for skill_dir in skills_root.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                    index.setdefault(skill_dir.name, []).append(
                        (str(qualifier), skill_dir, str(version)))
    return index


def _local_skill_dirs(root: Path) -> dict[str, Path]:
    """`root` 바로 아래의 디렉터리들을 이름 -> 경로로 나열한다(이슈 #1774
    tiers 3/4 공용 — 호출자가 어느 root 를 넘기는지로만 tier 가 갈린다).
    `root` 가 없으면 빈 매핑."""
    if not root.is_dir():
        return {}
    return {p.name: p for p in root.iterdir()
            if p.is_dir() and not p.name.startswith(".")}


def _skill_content_hash(skill_dir: Path) -> str:
    """tier 3/4 소스 정체성(이슈 #1774): 저장소 sha 도 플러그인 버전도 없는
    로컬 디렉터리라, `SKILL.md` 내용의 sha256 을 그 대신 쓴다(proposal
    Rationale: 이 저장소의 스킬 정의 관례가 이미 `SKILL.md` 를 정식 정의
    파일로 취급한다). `SKILL.md` 가 없으면 빈 바이트의 해시."""
    try:
        data = (skill_dir / "SKILL.md").read_bytes()
    except OSError:
        data = b""
    return hashlib.sha256(data).hexdigest()


def _describe_skill_match(m: dict) -> str:
    """에러 메시지/태스크 문구에 쓸, 소스 하나를 사람이 읽는 한 줄로."""
    if m["source"] == "skill-repo":
        return f"skill-repository({m['sha']})"
    if m["source"] == "plugin":
        return f"plugin {m['plugin']}@{m['version']}"
    if m["source"] == "local-user":
        return f"~/.claude/skills ({m['path']})"
    if m["source"] == "local-repo":
        return f".claude/skills ({m['path']})"
    return m["source"]


def resolved_skill_sources(skills_csv: str | None, repo_root: Path | None,
                            home: Path | None = None,
                            target_repo_root: Path | None = None) -> list[dict]:
    """이슈 #1774: `--skills a,b,c` 를 네 소스(skill-repository, 설치된
    플러그인, `~/.claude/skills`, 타깃 저장소 `.claude/skills`)에 걸쳐
    푼다. `skills_csv` 가 비면 빈 목록(마운트 없음, byte-identical 경로 —
    이 경우 네 소스 중 어느 것도 읽지 않는다, 요구사항 4).

    이름 하나가 소스 하나에서만 잡히면 그 소스로 확정. 소스 두 개 이상에서
    잡히면(같은 tier 안의 플러그인-대-플러그인 충돌 포함) 워크스페이스/
    브랜치를 건드리기 전에 fail-closed, 잡힌 소스를 전부 이름 붙여
    보고한다 — 어느 tier 도 다른 tier 를 조용히 가리지 않는다(이슈 #1774
    SCOPE EXTENSION). 어디서도 안 잡히면 오늘과 같은 fail-closed.

    각 소스가 가리키는 디렉터리에 `hooks/` 서브디렉터리가 있으면 —
    스킬 마운트는 가이던스 전용이라는 원칙 위반 — 역시 워크스페이스/
    브랜치 전에 fail-closed(네 소스 모두 동일 규칙).

    반환값은 이름당 dict 하나: 최소 `name`/`source`/`dir` 를 들고, 소스별
    정체성 필드(`sha`|`plugin`+`version`|`path`+`content_sha256`)가
    추가된다."""
    names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not names:
        return []
    home = home or Path.home()
    plugin_index = _sp._installed_plugin_skill_dirs()
    tier3 = _sp._local_skill_dirs(home / ".claude" / "skills")
    tier4 = (_sp._local_skill_dirs(target_repo_root / ".claude" / "skills")
             if target_repo_root is not None else {})
    results = []
    for name in names:
        matches: list[dict] = []
        if repo_root is not None and repo_root.is_dir():
            cand = repo_root / name
            if cand.is_dir() and not name.startswith("."):
                matches.append({"source": "skill-repo", "dir": cand,
                                 "sha": _sp.skill_repo_sha(repo_root)})
        for qualifier, plugin_skill_dir, version in plugin_index.get(name, []):
            matches.append({"source": "plugin", "dir": plugin_skill_dir,
                             "plugin": qualifier, "version": version})
        if name in tier3:
            d = tier3[name]
            matches.append({"source": "local-user", "dir": d, "path": str(d),
                             "content_sha256": _sp._skill_content_hash(d)})
        if name in tier4:
            d = tier4[name]
            matches.append({"source": "local-repo", "dir": d, "path": str(d),
                             "content_sha256": _sp._skill_content_hash(d)})
        if not matches:
            sys.exit(
                f"--skills: 모르는 스킬 {name} — skill-repository, 설치된 "
                f"플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills "
                f"어디에도 없다")
        if len(matches) > 1:
            sys.exit(
                f"--skills: {name} 가 둘 이상의 소스에서 겹친다 — "
                f"{', '.join(_sp._describe_skill_match(m) for m in matches)} "
                f"(precedence 는 검색 순서일 뿐 충돌을 가리지 않는다)")
        m = matches[0]
        if (m["dir"] / "hooks").is_dir():
            sys.exit(
                f"--skills: {name} ({_sp._describe_skill_match(m)}) 가 hooks/ "
                f"를 들고 있다 — 스킬 마운트는 가이던스 전용이다(집행은 "
                f"core 훅뿐)")
        m["name"] = name
        results.append(m)
    return results


def skill_repo_sha(repo_root: Path) -> str:
    """`repo_root` 체크아웃이 물고 있는 커밋(짧은 sha). `rulebook_version()`
    과 같은 shape — git 실패는 조용히 "?" 로 대체."""
    p = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--short=7", "HEAD"],
                        capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "?"


# 이슈 #1955: 전이용 역할-소스 허용목록(#1758)/rulebook 해석 경로 은퇴 —
# 매핑은 더 이상 대상 저장소의 선택적 파일이 아니라 여기 고정된다. 43개
# 역할 전부가 예전 docs/specs 아래 허용목록 파일과 값이 같다(그 파일이
# 이미 모든 역할을 매핑하고 있었다 — 이 상수는 그 내용을 그대로 옮긴 것).
_ROLE_SKILLS = {
    'accessibility': ['accessibility-aria-and-contrast-rules'],
    'api-design': ['api-design-error-design', 'api-design-http-semantics', 'api-design-payload-design', 'api-design-resource-modeling', 'api-design-tool-landscape', 'api-design-versioning-evolution'],
    'architecture': ['architecture-coupling-classification', 'architecture-decomposition-strategy', 'architecture-dependency-direction', 'architecture-interface-contract-shape', 'architecture-module-boundary-definition'],
    'brand-design': ['brand-design-brand-consistency-governance', 'brand-design-brand-identity-strategy', 'brand-design-color-visibility', 'brand-design-logo-clear-space-size', 'brand-design-typography-pairing'],
    'capacity-planning': ['capacity-planning-cost-attribution-at-trigger', 'capacity-planning-demand-shape-and-forecast-method', 'capacity-planning-expansion-trigger-threshold-sizing', 'capacity-planning-headroom-band-and-degradation-risk', 'capacity-planning-safety-buffer-sizing-by-criticality'],
    'conformance-review': ['conformance-review-requirement-extraction', 'conformance-review-sampling-derivation', 'conformance-review-traceability-and-evidence', 'conformance-review-verdict-assignment', 'conformance-review-verification-method-selection', 'conformance-review-finding-record', 'conformance-review-severity-classification'],
    'content-design': ['content-design-operational-playbook'],
    'customer-support': ['customer-support-escalation-path', 'customer-support-five-whys-recurring-scope', 'customer-support-kcs-article-authoring', 'customer-support-research-log', 'customer-support-sla-tier-priority', 'customer-support-subtraction-comprehensibility'],
    'data-engineering': ['data-engineering-data-quality', 'data-engineering-failure-handling', 'data-engineering-pipeline-design'],
    'data-modeling': ['data-modeling-datavault', 'data-modeling-inmon', 'data-modeling-kimball', 'data-modeling-structure'],
    'defect-verification': ['defect-verification-evidence-artifact-completeness', 'defect-verification-independence-from-upstream-verdicts', 'defect-verification-reproduction-evidence-quality', 'defect-verification-severity-band-assignment', 'verify-finding-record', 'verify-severity-classification'],
    'devrel': ['devrel-channel-convention', 'devrel-content-comprehensibility', 'devrel-program-subtraction'],
    'finance-unit-economics': ['finance-unit-economics-cac-payback', 'finance-unit-economics-evidence-chain', 'finance-unit-economics-ltv-cac-band', 'finance-unit-economics-ltv-churn-assumption', 'finance-unit-economics-proposal-shape', 'finance-unit-economics-sensitivity-scenario'],
    'growth-analytics': ['growth-analytics-experiment-trust', 'growth-analytics-funnel-stage-attribution', 'growth-analytics-metric-selection', 'growth-analytics-reporting-reduction', 'growth-analytics-segmentation'],
    # 이슈 #2208: work-in-english 는 태스크별 트리거가 아니라 이 저장소의
    # 모든 코딩 작업(코드/커밋/PR/문서)에 적용되는 언어 정책 스킬 — 실측
    # 판단 로그(docs/issue-2073, issue-2093 의 consult-log.md, 둘 다
    # role=implementation) 상 실제로 마운트된 건 언제나 implementation
    # 역할이었다. cross-family 후보 풀에서는 `_STATIC_POLICY_SKILLS`(아래)
    # 로 전 역할에서 조용히 빠진다 — 여기 family 목록에 있는 건 마운트
    # 경로(resolve_role_source)만을 위한 것.
    'implementation': ['implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'implementation-blueprint', 'work-in-english'],
    'incident-response': ['incident-response-action-item-quality', 'incident-response-blameless-language-editing', 'incident-response-rca-method-selection', 'incident-response-severity-classification-scoping', 'incident-response-timeline-construction', 'incident-response-tool-landscape'],
    'interaction-design': ['interaction-design-form-control-and-layout'],
    'issue-retrospective': ['issue-retrospective-timeline-comprehensibility-and-subtraction-rules'],
    'knowledge-management': ['knowledge-management-curation-pruning', 'knowledge-management-structure-findability', 'knowledge-management-taxonomy-tagging', 'knowledge-management-supersession-lifecycle', 'knowledge-management-pattern-extraction'],
    'legal-compliance': ['legal-compliance-consent-ux', 'legal-compliance-cross-border-transfer', 'legal-compliance-lawful-basis-selection', 'legal-compliance-license-compatibility', 'legal-compliance-research-log', 'legal-compliance-retention-minimization', 'legal-compliance-vendor-dpa'],
    'localization': ['localization-locale-convention-formatting', 'localization-pluralization-and-grammar', 'localization-rtl-and-script-support', 'localization-string-externalization', 'localization-text-expansion-and-layout'],
    'market-analysis': ['market-analysis-competitor-mapping', 'market-analysis-evidence-rigor', 'market-analysis-five-forces', 'market-analysis-jtbd-fit', 'market-analysis-mece-proposal'],
    'marketing': ['marketing-channel-selection', 'marketing-message-persuasion', 'marketing-positioning-differentiation', 'marketing-scope-pruning', 'marketing-segment-targeting'],
    'ml-engineering': ['ml-engineering-evaluation-discipline', 'ml-engineering-ml-test-score-scoring', 'ml-engineering-model-provenance-versioning', 'ml-engineering-rollout-promotion-rollback', 'ml-engineering-serving-pattern-selection', 'ml-engineering-slo-definition-tradeoffs'],
    'observability': ['observability-cardinality-budget', 'observability-explorability', 'observability-methodology-selection', 'observability-phase-trace', 'observability-signal-golden', 'observability-signal-red', 'observability-signal-use'],
    'partnerships-bd': ['partnerships-bd-deal-structure-selection', 'partnerships-bd-exclusivity-and-scope-terms', 'partnerships-bd-governance-cadence-and-kpi', 'partnerships-bd-negotiation-positioning', 'partnerships-bd-term-sheet-comprehensibility-and-convention'],
    'performance-engineering': ['performance-engineering-operational-playbook'],
    'pr-communications': ['pr-communications-message-planning-and-evaluation-rules'],
    'pricing': ['pricing-design-rigor', 'pricing-method-family', 'pricing-scope-gate', 'pricing-tier-structure', 'pricing-verdict-report'],
    'product-discovery': ['product-discovery-guardrail-metric-status', 'product-discovery-hypothesis-preregistration', 'product-discovery-jtbd-problem-framing', 'product-discovery-opportunity-solution-tree-branching', 'product-discovery-rice-ice-prioritization', 'product-discovery-assumption-mapping', 'product-discovery-guardrail-metrics', 'product-discovery-hypothesis-testing', 'product-discovery-one-pager', 'product-discovery-opportunity-solution-tree'],
    'refactoring-legacy': ['refactoring-legacy-characterization-test-scope', 'refactoring-legacy-refactoring-step-decomposition', 'refactoring-legacy-seam-selection', 'refactoring-legacy-strangler-fig-migration', 'refactoring-legacy-verification-cadence'],
    'release-engineering': ['release-engineering-branching-release-strategy', 'release-engineering-changelog-entry-categorization', 'release-engineering-deployment-rollout-strategy', 'release-engineering-release-cadence-and-toil', 'release-engineering-rollback-and-recovery', 'release-engineering-semver-bump-selection', 'release-engineering-error-budget-policy', 'release-engineering-postmortem', 'release-engineering-readiness-checklist', 'release-engineering-rollout-plan'],
    'requirements-engineering': ['requirements-engineering-rules'],
    'risk-management': ['risk-management-aggregation-consolidation', 'risk-management-appetite-tolerance-threshold', 'risk-management-likelihood-impact-scale', 'risk-management-monitoring-review-cadence', 'risk-management-response-strategy-selection'],
    'sales': ['sales-objection-handling', 'sales-pitch-scoping-and-messaging-handoff', 'sales-qualification-and-discovery'],
    'secure-coding': ['secure-coding-authorization-access-control', 'secure-coding-cryptography-secrets-management', 'secure-coding-dependency-supply-chain-security', 'secure-coding-input-validation-injection-defense', 'secure-coding-session-authentication'],
    'security-threat-model': ['security-threat-model-threat-modeling-decision-rules'],
    'technical-feasibility': ['technical-feasibility-build-vs-buy-dependency-health', 'technical-feasibility-license-and-regulatory-risk', 'technical-feasibility-reversibility-and-spike-scoping', 'technical-feasibility-threat-model-disposition', 'technical-feasibility-verdict-and-timebox-selection', 'technical-feasibility-build-vs-buy', 'technical-feasibility-license-scan', 'technical-feasibility-reversibility-tag', 'technical-feasibility-spike-report', 'technical-feasibility-stride-table'],
    'technical-writing': ['technical-writing-doc-type-selection', 'technical-writing-minimalism-scoping', 'technical-writing-persuasion-trust', 'technical-writing-structure-comprehension', 'technical-writing-style-guide-compliance', 'technical-writing-tool-landscape'],
    'test-authoring': ['test-authoring-isolation-and-fixture-strategy'],
    'upstream-defect-report': ['upstream-defect-report-subtraction', 'upstream-defect-report-comprehensibility', 'upstream-defect-report-convention'],
    'user-discovery': ['user-discovery-evidence-strength-tagging', 'user-discovery-follow-up-ladder-depth', 'user-discovery-question-design-past-behavior', 'user-discovery-saturation-stopping-rule', 'user-discovery-switch-timeline-causal-forces', 'user-discovery-verdict-prevalence-reporting'],
    'ux-engineering': ['ux-engineering-color-visibility', 'ux-engineering-control-selection', 'ux-engineering-layout-grouping', 'ux-engineering-navigation-depth', 'ux-engineering-research-log', 'ux-engineering-surface-contrast'],
}

# 이슈 #2208: POLICY 스킬 — 특정 task family 를 겨냥한 트리거가 아니라
# 세션 전체에 걸쳐 적용되는 규칙(언어 정책, 모델 라우팅 등)이라 cross-family
# 후보 풀에서 경쟁할 이유가 없다. 여기 이름은 역할과 무관하게(`_ROLE_SKILLS`
# 에 실제로 매핑돼 있든 아니든) `_cross_family_candidate_corpus()` 가 항상
# 걸러낸다 — declared-phrase self-inflation(work-in-english 의 예시 문구가
# 코드와 무관한 태스크에 verbatim 매치되는 문제, 골드 케이스
# `work-in-english-declared-phrase-self-inflation-fp`)처럼 판정 없이 BM25만
# 으로 마운트되는 경로를 원천 차단한다. 감사 결과(이슈 #2208 report) 이
# 모양의 다른 스킬은 model-routing 뿐이었으나, model-routing 은 현재
# 어떤 역할에도 정적으로 매핑돼 있지 않고(family 목록 없음) 실측 로그에서
# 반복적으로 옳게 골라지고 있어 이번 변경 범위에서는 제외했다 — 리포트의
# 감사 섹션 참고.
_STATIC_POLICY_SKILLS = {'work-in-english'}


def resolve_role_source(role: str, repo_root: Path | None) -> dict:
    """`role` 을 skill-repository 가이던스로 무조건 해석한다(이슈 #1955:
    전이용 역할-소스 허용목록/rulebook 해석 경로 은퇴, #1758 이 얼린 phase 5
    제약 이행 — 매핑 없는 역할이라는 상태 자체가 더 이상 없다).

    이름을 `resolved_skill_dirs()` 로 푼다(모르는 이름은 이미 거기서
    워크스페이스/브랜치 전에 fail-closed). 풀린 디렉터리 중 하나라도
    `hooks/` 서브디렉터리를 들고 있으면 — skill-repository 는 가이던스
    전용이라는 얼어붙은 프로그램 원칙 위반 — 역시 워크스페이스/브랜치 전에
    fail-closed. {"source": "skill-repo", "skill_dirs": [...],
    "skills": [이름...], "skill_sha": <첫 디렉터리의 부모 저장소 sha>} 를
    돌려준다."""
    names = _sp._ROLE_SKILLS.get(role, [])
    skill_dirs = _sp.resolved_skill_dirs(",".join(names), repo_root)
    hooked = [d for d in skill_dirs if (d / "hooks").is_dir()]
    if hooked:
        sys.exit(
            f"resolve_role_source: 역할 {role!r} 이 매핑한 스킬 중 "
            f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
            f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": _sp.skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}


def _skill_source_roster_row(m: dict) -> dict:
    """이슈 #1774 요구사항 3: 마운트된 스킬 한 줄의 로스터/기록용 row —
    소스별로 정체성 필드 shape 가 다르다(proposal `## What will be done`
    item 6)."""
    if m["source"] == "skill-repo":
        return {"name": m["name"], "source": "skill-repo", "sha": m["sha"]}
    if m["source"] == "plugin":
        return {"name": m["name"], "source": "plugin",
                "plugin": m["plugin"], "version": m["version"]}
    return {"name": m["name"], "source": m["source"], "path": m["path"],
            "content_sha256": m["content_sha256"]}


def _skill_roster_fields(skill_sources: list[dict], skill_sha: str | None) -> dict:
    """`--skills` 로 마운트된 스킬들의 로스터/기록 필드. `skills_detail` 은
    쓰였을 때 항상 붙어 소스별 identity(요구사항 3)를 나른다. 오늘의 flat
    `skills`/`skills_sha` shape 는 전부 skill-repo 매치일 때만 additive 로
    같이 붙는다(empty-state 요구: skill-repo-only 조합은 오늘 shape 유지) —
    안 쓰면(빈 목록) 키 자체가 없다."""
    if not skill_sources:
        return {}
    fields = {"skills_detail": [_sp._skill_source_roster_row(m) for m in skill_sources]}
    if all(m["source"] == "skill-repo" for m in skill_sources):
        fields["skills"] = [m["name"] for m in skill_sources]
        fields["skills_sha"] = skill_sha
    return fields


def _role_source_roster_fields(role_source: dict) -> dict:
    """이슈 #1758 요구사항 3 계승, 이슈 #1955 로 단순화: 로스터 엔트리마다
    항상 붙는 resolution 필드. source 는 이제 언제나 skill-repo(rulebook
    해석 경로는 은퇴했다) — resolution_source/resolution_skills/
    resolution_skill_sha 를 채운다."""
    return {"resolution_source": "skill-repo",
            "resolution_skills": role_source["skills"],
            "resolution_skill_sha": role_source["skill_sha"]}
