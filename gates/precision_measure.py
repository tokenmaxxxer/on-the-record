"""issue #1614 requirement 3 — sweep-lane precision measurement, one
command instead of a bespoke session.

Protocol (frozen from the issue #1614 measurement, 2026-08-16):
  population = every verified sweep-lane record_lint finding (per-rule
  disabled rules already excluded by `patrol_queue.run_scan`'s own
  `SWEEP_DISABLED_RULES` filter — this tool measures precision on the
  ENABLED-rule population only, consistent with what the sweep lane
  actually enqueues).
  sample = stratified random, proportional by rule, floor 5 per rule
  present, target n=100 (or the full population when smaller), seeded.
  judged (TP/FP) by a human/LLM reviewer against the Tricorder
  effective-FP criterion ("would the record's owner take positive
  action?") — this module does not itself judge (no LLM call in any
  `gates/` module, same convention `patrol_queue.py` already holds); it
  builds the sample, then reads back a judgments file mapping each
  sample's `id` to `"TP"`/`"FP"`.
  report = per-rule + overall precision with a one-sided 90% Wilson
  lower bound, finite-population-corrected, plus the pre-registered
  pass/kill rule from #1614: overall point >=90% AND Wilson LB >=85%;
  per-rule kill <70%.

  python3 -m gates.precision_measure sample <repo-root> \
      [--n 100] [--seed 20260816] [--out samples.json]
  python3 -m gates.precision_measure report <samples.json> \
      [--judgments judgments.json]
"""
from __future__ import annotations
import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import patrol_queue  # noqa: E402


def _population(repo_root: Path) -> list[dict]:
    """The verified sweep-lane finding population, one entry per
    finding, each carrying its rule id (already-disabled rules never
    appear — `scan_record_lint`'s output, filtered the same way
    `run_scan` filters it for the sweep lane)."""
    raw = patrol_queue.scan_record_lint(repo_root)
    kept = []
    for f in raw:
        rid = patrol_queue._finding_rule_id(f)
        if rid in patrol_queue.SWEEP_DISABLED_RULES:
            continue
        probe = {"path": f["path"], "excerpt": f["excerpt"]}
        if not patrol_queue.verify(probe, repo_root):
            continue
        kept.append({
            "rule": rid or "unknown",
            "path": f["path"],
            "excerpt": f["excerpt"],
            "violation": f["context_lines"][0] if f.get("context_lines") else "",
        })
    return kept


def stratified_sample(population: list[dict], n: int = 100,
                       floor: int = 5, seed: int = 20260816) -> list[dict]:
    """Stratified random sample, proportional allocation by rule with a
    per-rule floor, seeded for reproducibility. Returns <= n items (the
    whole population when the population is <= n)."""
    if not population:
        return []
    by_rule: dict[str, list[dict]] = {}
    for item in population:
        by_rule.setdefault(item["rule"], []).append(item)

    total = len(population)
    if total <= n:
        target_n = total
    else:
        target_n = n

    rng = random.Random(seed)
    alloc: dict[str, int] = {}
    for rule, items in by_rule.items():
        proportional = round(target_n * len(items) / total)
        alloc[rule] = min(max(floor, proportional), len(items))

    # Floor allocation can push the sum over target_n when many rules are
    # tiny — trim the largest allocations first until the sum fits, never
    # trimming a rule below its floor unless its whole population is
    # smaller than the floor already (nothing left to trim there).
    def _sum():
        return sum(alloc.values())

    while _sum() > target_n:
        trimmable = [r for r in alloc if alloc[r] > min(floor, len(by_rule[r]))]
        if not trimmable:
            break
        trimmable.sort(key=lambda r: alloc[r], reverse=True)
        alloc[trimmable[0]] -= 1

    sample = []
    for rule, items in by_rule.items():
        k = alloc.get(rule, 0)
        pool = list(items)
        rng.shuffle(pool)
        sample.extend(pool[:k])

    for i, item in enumerate(sample):
        item["id"] = f"s{i:04d}"
    return sample


def wilson_lower_bound(successes: int, n: int, confidence: float = 0.90,
                        population: int | None = None) -> float:
    """One-sided Wilson score lower bound, optionally finite-population
    corrected (Isserlis/standard fpc factor sqrt((N-n)/(N-1)) applied to
    the interval half-width around the Wilson center)."""
    if n == 0:
        return 0.0
    z = _z_one_sided(confidence)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) / n) + (z * z / (4 * n * n)))) / denom
    if population is not None and population > n:
        fpc = math.sqrt((population - n) / (population - 1)) if population > 1 else 1.0
        half *= fpc
    return max(0.0, center - half)


def _z_one_sided(confidence: float) -> float:
    # One-sided z for the common confidence levels this protocol uses;
    # avoids a scipy dependency for a single lookup.
    table = {0.90: 1.2815515655, 0.95: 1.6448536269, 0.80: 0.8416212336}
    if confidence in table:
        return table[confidence]
    raise ValueError(f"unsupported confidence level: {confidence!r}")


def build_report(sample: list[dict], judgments: dict[str, str],
                  population_size: int) -> dict:
    """Per-rule + overall precision with Wilson LB, judged against the
    pre-registered #1614 pass rule (overall point>=90% and LB>=85%;
    per-rule kill <70%)."""
    if not sample:
        return {
            "status": "no-findings",
            "message": ("no findings — precision undefined, promotion "
                        "not applicable"),
        }

    by_rule: dict[str, list[dict]] = {}
    for item in sample:
        by_rule.setdefault(item["rule"], []).append(item)

    rule_reports = {}
    overall_tp = 0
    overall_n = 0
    for rule, items in sorted(by_rule.items()):
        n = len(items)
        tp = sum(1 for it in items
                  if judgments.get(it["id"], "").upper() == "TP")
        overall_tp += tp
        overall_n += n
        precision = tp / n if n else 0.0
        lb = wilson_lower_bound(tp, n)
        rule_reports[rule] = {
            "sampled": n,
            "tp": tp,
            "precision": precision,
            "wilson_lb_90": lb,
            "kill": precision < 0.70,
        }

    overall_precision = overall_tp / overall_n if overall_n else 0.0
    overall_lb = wilson_lower_bound(overall_tp, overall_n,
                                     population=population_size)
    any_kill = any(r["kill"] for r in rule_reports.values())
    passed = (overall_precision >= 0.90 and overall_lb >= 0.85
              and not any_kill)

    return {
        "status": "measured",
        "population": population_size,
        "sampled": overall_n,
        "overall": {
            "tp": overall_tp,
            "precision": overall_precision,
            "wilson_lb_90": overall_lb,
        },
        "per_rule": rule_reports,
        "pass_rule": "overall point>=90% AND wilson_lb_90>=85% AND no per-rule kill(<70%)",
        "promote": passed,
    }


def format_report(report: dict) -> str:
    if report["status"] == "no-findings":
        return report["message"]
    lines = [
        f"population={report['population']} sampled={report['sampled']}",
        "",
        "| rule | sampled | TP | precision | wilson_lb_90 |",
        "|---|---|---|---|---|",
    ]
    for rule, r in sorted(report["per_rule"].items()):
        kill = " (KILL <70%)" if r["kill"] else ""
        lines.append(
            f"| issue-{rule} | {r['sampled']} | {r['tp']} | "
            f"{r['precision']:.1%} | {r['wilson_lb_90']:.1%}{kill} |")
    o = report["overall"]
    lines.append(
        f"| overall | {report['sampled']} | {o['tp']} | "
        f"{o['precision']:.1%} | {o['wilson_lb_90']:.1%} |")
    lines.append("")
    lines.append(f"pass rule: {report['pass_rule']}")
    lines.append(f"promote: {'YES' if report['promote'] else 'NO'}")
    return "\n".join(lines)


def cmd_sample(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="precision_measure sample")
    ap.add_argument("repo_root")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--floor", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--out", default="-")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    population = _population(root)
    sample = stratified_sample(population, n=args.n, floor=args.floor,
                                seed=args.seed)
    payload = {
        "population_size": len(population),
        "n": args.n,
        "floor": args.floor,
        "seed": args.seed,
        "sample": [
            {"id": it["id"], "rule": it["rule"], "path": it["path"],
             "excerpt": it["excerpt"], "violation": it["violation"],
             "verdict": None}
            for it in sample
        ],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {len(sample)} sample items "
              f"(population {len(population)}) to {args.out}")
    return 0


def cmd_report(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="precision_measure report")
    ap.add_argument("samples_file")
    ap.add_argument("--judgments")
    args = ap.parse_args(argv)

    payload = json.loads(Path(args.samples_file).read_text(encoding="utf-8"))
    sample = payload["sample"]

    judgments: dict[str, str] = {}
    if args.judgments:
        judgments = json.loads(Path(args.judgments).read_text(encoding="utf-8"))
    else:
        for it in sample:
            if it.get("verdict"):
                judgments[it["id"]] = it["verdict"]

    report = build_report(sample, judgments, payload["population_size"])
    print(format_report(report))
    return 0 if report["status"] == "no-findings" or report.get("promote") is not None else 1


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("sample", "report"):
        print(__doc__)
        return 2
    if argv[0] == "sample":
        return cmd_sample(argv[1:])
    return cmd_report(argv[1:])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
