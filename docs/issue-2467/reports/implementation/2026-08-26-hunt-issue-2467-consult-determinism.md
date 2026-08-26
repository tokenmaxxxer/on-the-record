---
proposal: docs/issue-2467/reports/implementation.md
---

# Hunt record — issue-2467-consult-determinism

## after-proposal — stance 1: silent failure in the record's evidentiary claim

Verdict: FINDING — the record's determinism evidence is not verifiable/reproducible.
Kind: silent-failure
Seed: docs/issue-2467/reports/implementation.md (new, ~197 lines); git diff origin/main..HEAD touches only two consult-log entries plus this record (0 lines of consult.py/spawn.py changed)
cap_seconds: not specified by dispatcher
tier: default
diff_stat_lines: 201 (2+2+197 per `git diff origin/main..HEAD --stat`)
started_at: 2026-08-26T00:20:00Z
ended_at: 2026-08-26T00:55:00Z

canonical: docs/issue-2467/reports/implementation.md lines 33-35 ("Full
commands and raw output are pasted verbatim under 'What did not work' →
'Determinism check — executed evidence' below") and lines 86-140 (the two
`acceptance:` blocks citing `.scratch2467/determinism_check.py` /
`determinism_check2.py`), as read directly from the working tree this turn.

acceptance: `git diff origin/main..HEAD --stat` — result:
```
 .../consult-log/20260826T000850748395-193999.md    |   2 +
 .../consult-log/20260826T000943632184-196116.md    |   2 +
 docs/issue-2467/reports/implementation.md          | 197 +++++++++++++++++++++
 3 files changed, 201 insertions(+)
```
canonical: above `git diff` output — no `.scratch2467/*` file is part of what is being landed.

acceptance: `find . -iname "*scratch2467*"` — result:
```
(no output)
```
canonical: above `find` output — the scripts the record's acceptance blocks invoke are absent from the working tree entirely, not just unstaged.

acceptance: `PYTHONPATH=. python3 .scratch2467/determinism_check.py` — result:
```
python3: can't open file '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2467-implementation/.scratch2467/determinism_check.py': [Errno 2] No such file or directory
```
canonical: above transcript, this turn — re-running the record's own cited acceptance command verbatim fails with FileNotFoundError.

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2467-implementation
git diff origin/main..HEAD --stat
find . -iname "*scratch2467*"
PYTHONPATH=. python3 .scratch2467/determinism_check.py
```

### Observed
canonical: `PYTHONPATH=. python3 .scratch2467/determinism_check.py` — result: FileNotFoundError, transcript above, this turn.

docs/issue-2467/reports/implementation.md lines 79-140 (the "Determinism
check — executed evidence" section) rests its central, delivery-defining
claim — the judge call is non-deterministic, therefore no cache is added —
on two `acceptance:` blocks that run `.scratch2467/determinism_check.py` /
`determinism_check2.py`. Only the invocation line and captured stdout are
pasted; the script source itself is neither committed nor quoted anywhere in
the record. The three transcripts above show the scripts are absent from the
diff being landed and from the working tree, so the actual construction of
"byte-identical arguments" (which exact candidates/role/task-text were
given, whether call 1 and call 2 shared identical environment/session
assembly) is not inspectable by any reader now, despite the record's line
33-35 claim that "Full commands and raw output are pasted verbatim."

canonical: `grep -rl "\.scratch" docs/issue-*/reports/*.md` (run this turn)
— docs/issue-1730/reports/implementation.md lines 70-76 (`cat
.scratch_check1.py` shown immediately before `python3 .scratch_check1.py` is
run). The only other record in the repo citing a `.scratch*` acceptance
script embeds the script's source in the record itself before executing it,
so its acceptance evidence outlives the scratch file's later deletion.
issue-2467's record does not follow that pattern.

### Expected
Either the acceptance scripts should have been committed (e.g. under
`docs/issue-2467/` alongside the record) or their source pasted into the
record the way `docs/issue-1730/reports/implementation.md` does — so the
record's own "pasted verbatim" claim is true of the evidence that decided
this issue's outcome.
