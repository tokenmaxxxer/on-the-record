---
proposal: docs/issue-2920/proposals/resolve-consult-skill-source.md
---

# Hunt record — resolve-consult-skill-source

## after-proposal — stance 1: unresolved-visibility composition regression across consult's verb siblings

Verdict: FINDING — `ideate_cmd`/`draft_cmd`/`review_cmd` (all via `_verb_cmd()`) compute `env["MUSTER_SKILLS_UNRESOLVED"]` through the same `_consult_cmd_and_env()` helper as `consult_cmd()`, but `_verb_cmd()`'s `_append_consult_trace()` call never passes `mounted=`/`unresolved=`, so the durable git-committed trace shows nothing when a verb call's skill selector fails to resolve.
Kind: composition
Seed: consult.py diff — `resolve_skill_family_source()` deleted, replaced by `resolve_consult_skill_source()`; `consult_cmd()` wired `verdict["skills_mounted"]`/`verdict["skills_unresolved"]` and `_append_consult_trace(..., mounted=, unresolved=)`; `_verb_cmd()` only gained a defensive `env: dict = {}` pre-try initializer, its `_append_consult_trace()` call was left untouched (no `mounted=`/`unresolved=` kwargs)
cap_seconds: (not specified by dispatcher)
tier: default
diff_stat_lines: see below
```
$ git diff --stat
 consult.py                                         | 214 ++++++++++++---------
 skills.py                                          | 102 ++++++----
 spawn.py                                           |   2 +-
 test/test_consult_no_rulebook_identity_regression.py |  45 +++--
 test/test_spawn_model_override.py                  |   8 +-
 test/test_spawn_skills_mount.py                    |   2 +-
 6 files changed, 218 insertions(+), 155 deletions(-)
```
started_at: 2026-08-31T04:15:00Z
ended_at: 2026-08-31T04:42:00Z

### Reproduce

Both runs against the working tree's uncommitted diff, `subprocess.run` stubbed to isolate the trace-writing path (`_skill_repo_root` pointed at a temp dir seeded with `work-in-english` + `adversarial-review` only, so `conformance-review` — a retired-role name — is the unresolved selector).

`ideate_cmd` (representative of the `_verb_cmd()` family):
```python
import sys, json, tempfile, subprocess
from pathlib import Path
from unittest import mock
sys.path.insert(0, ".")
import spawn as _sp
import consult

repo_root = Path(tempfile.mkdtemp())
(repo_root / "work-in-english").mkdir(); (repo_root / "work-in-english" / "SKILL.md").write_text("g")
(repo_root / "adversarial-review").mkdir(); (repo_root / "adversarial-review" / "SKILL.md").write_text("g")
cwd = tempfile.mkdtemp()

def fake_run(cmd, cwd=None, input=None, text=None, capture_output=None, timeout=None, env=None):
    fake_run.captured_env = env
    payload = json.dumps({"result": json.dumps({"options": ["a"], "tradeoffs": []})})
    return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

with mock.patch.object(_sp, "_skill_repo_root", return_value=repo_root), \
     mock.patch("subprocess.run", side_effect=fake_run), \
     mock.patch.object(_sp, "_commit_consult_trace", lambda *a, **k: None):
    consult.ideate_cmd("conformance-review", "some question", issue=None, cwd=cwd)

print("MUSTER_SKILLS_UNRESOLVED:", fake_run.captured_env.get("MUSTER_SKILLS_UNRESOLVED"))
print(_sp._consult_trace_path(None, cwd).read_text())
```

`consult_cmd` (sibling, same selector, same helper) for contrast:
```python
import sys, json, tempfile, subprocess
from pathlib import Path
from unittest import mock
sys.path.insert(0, ".")
import spawn as _sp
import consult

repo_root = Path(tempfile.mkdtemp())
(repo_root / "work-in-english").mkdir(); (repo_root / "work-in-english" / "SKILL.md").write_text("g")
(repo_root / "adversarial-review").mkdir(); (repo_root / "adversarial-review" / "SKILL.md").write_text("g")
cwd = tempfile.mkdtemp()

def fake_run(cmd, cwd=None, input=None, text=None, capture_output=None, timeout=None, env=None):
    payload = json.dumps({"result": json.dumps({"answer": "x", "confidence": "low", "caveats": []})})
    return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

with mock.patch.object(_sp, "_skill_repo_root", return_value=repo_root), \
     mock.patch("subprocess.run", side_effect=fake_run), \
     mock.patch.object(_sp, "_commit_consult_trace", lambda *a, **k: None):
    consult.consult_cmd("conformance-review", "some question", issue=None, cwd=cwd)

print(_sp._consult_trace_path(None, cwd).read_text())
```

### Observed
canonical: literal stdout of the two Reproduce scripts, executed in this session against the current uncommitted working tree (2026-08-31T04:39-04:41Z).

`ideate_cmd` run:
```
MUSTER_SKILLS_UNRESOLVED: conformance-review
- 2026-08-31T04:39:55.642797+00:00 | skill=conformance-review | verb=ideate | issue=none | question='some question' | outcome="ok: ['a']"
```

`consult_cmd` run (same selector, same helper, same repo fixture):
```
- 2026-08-31T04:41:07.256319+00:00 | skill=conformance-review | verb=consult | issue=none | question='some question' | outcome='ok: x | evidence=[verified:0 failed:0 unverified-cmd:0 no-evidence:1]' | mounted='work-in-english' | unresolved='conformance-review'
```

`MUSTER_SKILLS_UNRESOLVED` was non-empty (`conformance-review`) in both cases (same `_consult_cmd_and_env()` build), but only `consult_cmd`'s trace line carries `mounted=`/`unresolved=`. `ideate_cmd`'s trace line has no such suffix at all — it reads identically to a fully-resolved, successful call.

### Expected
acceptance: `sed -n '1233,1239p' consult.py` — result:
```
    finally:
        if settings_path:
            with contextlib.suppress(OSError):
                os.unlink(settings_path)
        _sp._append_consult_trace(trace_path, ts, skill, issue, prompt_text, outcome, verb=verb)
        commit_paths = [trace_path] + raw_paths
        _sp._commit_consult_trace(commit_paths, issue, skill, outcome, cwd)
```
vs `consult_cmd`'s `finally` block, `sed -n '1120,1126p' consult.py` — result:
```
        print(_consult_timing_line(skill) +
              f" muster_skills={env.get('MUSTER_SKILLS', '')!r}"
              f" muster_skills_unresolved={env.get('MUSTER_SKILLS_UNRESOLVED', '')!r}",
              file=sys.stderr)
        _sp._append_consult_trace(trace_path, ts, skill, issue, question, outcome,
                              mounted=env.get("MUSTER_SKILLS", ""),
                              unresolved=env.get("MUSTER_SKILLS_UNRESOLVED", ""))
```
`_verb_cmd()` builds and consumes the exact same `env` dict (`_sp._consult_cmd_and_env(...)`, same helper `consult_cmd()` calls) but its `_append_consult_trace()` call passes neither `mounted=` nor `unresolved=`, so `ideate`/`draft`/`review` calls get none of the durable empty-mount visibility this issue's own docstring (consult.py:361-370, "이전엔 이 정보가 트레이스... 전혀 안 남고... 이 두 필드가 그 공백을 닫는다") says it closed — only `consult` got the fix, its three verb siblings did not.
