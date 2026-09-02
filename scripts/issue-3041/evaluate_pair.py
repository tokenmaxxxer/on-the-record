#!/usr/bin/env python3
"""Blind evaluator for one paired run (issue #3041).

The evaluator is a fresh `claude -p` call with no tool access (--tools ""),
so it cannot inspect either workspace, git history, or file paths that
would disclose which document came from which arm. It never produced
either deliverable. Which deliverable is shown as "Document 1" vs
"Document 2" is randomized per call; the mapping back to skills-on /
skills-off is recorded only in this script's own output, never shown to
the evaluator.

Usage:
  python3 scripts/issue-3041/evaluate_pair.py \
      <task_file> <rubric_file> <deliverable_skills_on> <deliverable_skills_off> \
      <out_json_path>
"""
from __future__ import annotations
import json
import random
import re
import subprocess
import sys


def main() -> None:
    task_file, rubric_file, deliv_on, deliv_off, out_path = sys.argv[1:6]
    task_text = open(task_file, encoding="utf-8").read().strip()
    rubric = open(rubric_file, encoding="utf-8").read().strip()
    text_on = open(deliv_on, encoding="utf-8", errors="replace").read()
    text_off = open(deliv_off, encoding="utf-8", errors="replace").read()

    docs = [("skills-on", text_on), ("skills-off", text_off)]
    random.shuffle(docs)
    (label_1, doc1_text), (label_2, doc2_text) = docs

    prompt = f"""You are a blind evaluator. You did not write either document below, and you are not told which system, process, or person produced them.

TASK GIVEN TO BOTH WRITERS:
{task_text}

SCORING RUBRIC (what a strong answer should contain):
{rubric}

--- DOCUMENT 1 ---
{doc1_text}
--- END DOCUMENT 1 ---

--- DOCUMENT 2 ---
{doc2_text}
--- END DOCUMENT 2 ---

Score DOCUMENT 1 and DOCUMENT 2 independently on a 1-10 scale for how well each satisfies the rubric above (structure and content only -- ignore length, tone, or formatting flourishes). Then state which document is better, or "indistinguishable" if the gap is not meaningful.

Respond with ONLY a JSON object, no other text, no markdown fences:
{{"document_1_score": <int 1-10>, "document_2_score": <int 1-10>, "verdict": "document_1" | "document_2" | "indistinguishable", "reasoning": "<2-3 sentences>"}}"""

    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--model", "sonnet",
            "--tools", "",
            "--setting-sources", "project,local",
            "--output-format", "json",
            "--max-budget-usd", "0.5",
        ],
        capture_output=True, text=True, timeout=180,
    )

    response_text = result.stdout
    try:
        outer = json.loads(result.stdout)
        response_text = outer.get("result", result.stdout)
    except json.JSONDecodeError:
        pass

    m = re.search(r"\{.*\}", response_text, re.DOTALL)
    verdict_json = json.loads(m.group(0)) if m else {"error": "unparsed", "raw": response_text}

    out = {
        "task_file": task_file,
        "rubric_file": rubric_file,
        "document_1_actual_arm": label_1,
        "document_2_actual_arm": label_2,
        "evaluator_prompt": prompt,
        "evaluator_verdict": verdict_json,
        "evaluator_process_returncode": result.returncode,
        "evaluator_stderr_tail": result.stderr[-2000:],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != "evaluator_prompt"}, indent=2))


if __name__ == "__main__":
    main()
