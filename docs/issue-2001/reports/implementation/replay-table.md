---
subject: issue-2001
role: implementation
phase: 2-replay
---

# Replay-before-ship: `_cross_family_skill_matches()` over today's real sessions

Per the proposal's build-plan replay step and the consult's
precondition ("no hard false-positive data yet"), this replays the new
scorer (`_cross_family_skill_matches`, spawn.py) against 16 real
`tokenmaxxxer/on-the-record` session logs from 2026-08-22 — every distinct
issue+role pair with a session log under `/home/jwjung/.tokenmaxxxer/work/`
dated `20260822`, all in one `gh`-reachable repo.

`derived:`
```
$ find /home/jwjung/.tokenmaxxxer/work -maxdepth 1 -iname "on-the-record-issue-*-*.session.20260822*.log" | sed -E 's#.*/on-the-record-issue-([0-9]+)-([a-z-]+)\.session\..*#\1 \2#' | sort -u -n
1745 implementation
1955 implementation
1958 implementation
1959 test-authoring
1960 implementation
1966 implementation
1969 implementation
1976 implementation
1978 implementation
1981 implementation
1982 implementation
1991 implementation
1992 implementation
1996 knowledge-management
1999 implementation
2001 implementation
```

For each row, the issue's title+body (fetched live via `gh issue view <n>
--json title,body`, mirroring `_spawn_one()`'s own fetch) was fed to
`spawn._cross_family_skill_matches(text, role, spawn._skill_repo_root())`.

`derived:`
```
$ python3 - <<'PYEOF'
import subprocess, json, sys
sys.path.insert(0, ".")
import spawn
pairs = [(1745,"implementation"),(1955,"implementation"),(1958,"implementation"),
         (1959,"test-authoring"),(1960,"implementation"),(1966,"implementation"),
         (1969,"implementation"),(1976,"implementation"),(1978,"implementation"),
         (1981,"implementation"),(1982,"implementation"),(1991,"implementation"),
         (1992,"implementation"),(1996,"knowledge-management"),(1999,"implementation"),
         (2001,"implementation")]
repo_root = spawn._skill_repo_root()
sev = mr = 0
for issue, role in pairs:
    out = subprocess.run(["gh","issue","view",str(issue),"--json","title,body"],
                          capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    text = (data.get("title") or "") + "\n" + (data.get("body") or "")
    names = [d.name for d in spawn._cross_family_skill_matches(text, role, repo_root)]
    if "conformance-review-severity-classification" in names: sev += 1
    if "model-routing" in names: mr += 1
    print(issue, role, names)
print("severity_count", sev, "of", len(pairs))
print("model_routing_count", mr, "of", len(pairs))
PYEOF
1745 implementation ['conformance-review-severity-classification', 'customer-support-research-log']
1955 implementation ['product-discovery-hypothesis-testing', 'conformance-review-severity-classification']
1958 implementation ['conformance-review-severity-classification', 'upstream-defect-report-convention']
1959 test-authoring ['model-routing', 'conformance-review-severity-classification']
1960 implementation ['conformance-review-severity-classification', 'conformance-review-finding-record']
1966 implementation ['conformance-review-severity-classification', 'product-discovery-hypothesis-testing']
1969 implementation ['conformance-review-severity-classification', 'model-routing']
1976 implementation ['conformance-review-severity-classification', 'model-routing']
1978 implementation ['conformance-review-severity-classification', 'pricing-scope-gate']
1981 implementation ['conformance-review-severity-classification', 'product-discovery-hypothesis-testing']
1982 implementation ['usability-eval', 'conformance-review-severity-classification']
1991 implementation ['conformance-review-severity-classification', 'test-authoring-isolation-and-fixture-strategy']
1992 implementation ['secure-coding-authorization-access-control', 'conformance-review-severity-classification']
1996 knowledge-management ['brand-design-icon-system-svg', 'conformance-review-severity-classification']
1999 implementation ['conformance-review-severity-classification', 'model-routing']
2001 implementation ['conformance-review-severity-classification', 'model-routing']
severity_count 16 of 16
model_routing_count 5 of 16
```

| Issue | Role | Would-have-added | Plausibility |
|---|---|---|---|
| 1745 | implementation | conformance-review-severity-classification, customer-support-research-log | No — fast-tier test-failure triage; neither skill's domain (review-severity risk-weighting, support research logs) is present in the task. |
| 1955 | implementation | product-discovery-hypothesis-testing, conformance-review-severity-classification | No — retiring a code path; not product-discovery or review-severity work. |
| 1958 | implementation | conformance-review-severity-classification, upstream-defect-report-convention | No — re-tiering a test config file; not a defect report or review-severity task. |
| 1959 | test-authoring | model-routing, conformance-review-severity-classification | No — splitting a test monolith; model-routing's own trigger is "every non-trivial task" (too broad to be a useful signal) and review-severity is unrelated. |
| 1960 | implementation | conformance-review-severity-classification, conformance-review-finding-record | No — measuring skill-invocation rate; not a conformance review. |
| 1966 | implementation | conformance-review-severity-classification, product-discovery-hypothesis-testing | No — stall-detector heuristic; neither domain applies. |
| 1969 | implementation | conformance-review-severity-classification, model-routing | No — repairing a red test baseline; model-routing's breadth (any non-trivial task) makes it a spurious hit here too. |
| 1976 | implementation | conformance-review-severity-classification, model-routing | No — board-gate refusal UX; same spurious-breadth pattern as above. |
| 1978 | implementation | conformance-review-severity-classification, pricing-scope-gate | No — spawn directive assembly; pricing-scope-gate is unrelated. |
| 1981 | implementation | conformance-review-severity-classification, product-discovery-hypothesis-testing | No — checkpoint-commit directive rule; neither domain applies. |
| 1982 | implementation | usability-eval, conformance-review-severity-classification | No — respawn continuation-preamble heuristic; not a usability study. |
| 1991 | implementation | conformance-review-severity-classification, test-authoring-isolation-and-fixture-strategy | Maybe — test-authoring-isolation-and-fixture-strategy is at least in the right neighborhood (this issue builds a multi-judge reflection scoring rig with test-like structure), though the task itself is not test-authoring work. review-severity remains a no. |
| 1992 | implementation | secure-coding-authorization-access-control, conformance-review-severity-classification | No — outcome-contrast analysis over session history; not an access-control task. |
| 1996 | knowledge-management | brand-design-icon-system-svg, conformance-review-severity-classification | No — skill-repository research wave (kubernetes-workload family); icon-system-svg matches because the issue body happens to mention "icon-system skill" as one of the wave's own past deliverables, a same-repo self-reference rather than genuine cross-family relevance. |
| 1999 | implementation | conformance-review-severity-classification, model-routing | No — judge evidence-extraction bug fix; same spurious-breadth pattern. |
| 2001 | implementation | conformance-review-severity-classification, model-routing | No — this issue itself; same spurious-breadth pattern. |

## Open finding surfaced by this replay

canonical: `severity_count`/`model_routing_count` lines of the derived
replay script output directly above.

`derived:`
```
severity_count 16 of 16
model_routing_count 5 of 16
```

`conformance-review-severity-classification` clears the K=2
min-overlap threshold on every replayed row above, and `model-routing`
on roughly a third of them — neither is a real cross-family relevance
signal. Both stem from trigger sentences carrying generic engineering
vocabulary: conformance-review-severity-classification's frontmatter uses
words like "review", "scope", "explicitly", "finding" — words this
repo's own issue-body convention already contains via its `scope:` line
and `## Request`/`## Rationale` habit — and model-routing's uses "task",
"development", "design", "any domain", consistent with its own
deliberately maximal "Use this skill on EVERY non-trivial task" trigger.
This is exactly the false-positive class the consult flagged as
unmeasured before shipping. Per the proposal's explicit "Out of scope"
section (tuning the threshold/K beyond what this table supports is a
follow-up iteration's job, not decided speculatively here), this replay
does not retune the threshold — it records the miscalibration signal for
that follow-up to act on.
