# Deviation log — issue-2190 (implementation role)

- 2026-08-24T00:00:00Z | filed | while verifying this issue's fix against the real `record-fields-gate.sh` and `record-claim-guard.sh` mechanics, this session hit a refusal when its own `Write` to this record cited its own path in a backtick-quoted reference — tracing it turned up a bug in `on-the-record/hooks/record-claim-guard.sh`'s call site for `record_lint.git_tracked_path_reference_check`, reproduced below:

```
$ python3 -c "
import re
text = open('on-the-record/hooks/record-claim-guard.sh').read()
m = re.search(r'git_tracked_path_reference_check\([^)]*\)', text)
print(m.group(0))
m2 = re.search(r'def git_tracked_path_reference_check\([^)]*\)', open('gates/record_lint.py').read())
print(m2.group(0))
"
git_tracked_path_reference_check(
        record_lint.Path(root)
def git_tracked_path_reference_check(root: Path, text: str,
                                      record_rel: str | None = None)
```
canonical: python3 -c "..." execution above, this session, this turn.

The hook's call site omits the third `record_rel` argument, so the function's own self-citation exemption for the record currently being written can never activate — any record whose own body backtick-cites its own repo-relative path is refused as an uncommitted path on its very first write, for every role, every time. Worked around by rewording this record's own prose to avoid backtick-citing its own path, rather than fixing the hook: `on-the-record/hooks/*.sh` is outside issue #2190's frozen write set, and a role session does not open an issue or spawn a peer role on its own initiative mid-task. Reported here rather than filed as a new issue/spawn, per the role-session variant of the deviation loop; the user should decide whether to open a follow-up issue.
