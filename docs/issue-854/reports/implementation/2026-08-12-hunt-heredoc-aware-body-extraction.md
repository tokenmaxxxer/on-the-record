---
proposal: docs/issue-854/proposals/2026-08-12-heredoc-aware-body-extraction.md
---

# Hunt record — heredoc-aware-body-extraction

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `<<-EOF` (dash form) with a tab-indented terminator line makes `_HEREDOC_BODY_RE` fail to match at all, so extraction falls through to the old quote-balance regex, which truncates the body before a genuine `Closes #854` — the exact bug this fix claims to close, reintroduced via one specific real, valid heredoc form.
Kind: silent-failure
Seed: on-the-record/hooks/pr-preflight.sh `_HEREDOC_BODY_RE` (staged fix), docs/issue-854/proposals/2026-08-12-heredoc-aware-body-extraction.md
cap_seconds: 180
tier: size:diff-over-200
diff_stat_lines: 515 insertions / 11 deletions across 4 files
started_at: 2026-08-11T15:11:12Z
ended_at: 2026-08-11T15:12:34Z

### Reproduce

`_HEREDOC_BODY_RE`'s terminator-line group is `r"\n\2[ \t]*\n?\)\""` — it only tolerates trailing whitespace *after* the delimiter word on the terminator line, never leading whitespace *before* it. But `cat <<-EOF` (the dash form the same regex explicitly tries to accept, via the `<<-?` in its own pattern) is bash's own syntax for "the terminator line may be tab-indented" — real, working, unmodified bash:

```bash
cat <<-EOF
## Summary

Addresses #854 - phase 1.

- decided not "무리" (impractical) to do X

Closes #854
	EOF
```
(the last line is a real tab followed by `EOF`) prints the body verbatim including the trailing `Closes #854` line — confirmed by running exactly that heredoc in this shell.

End-to-end drive of the actual deployed hook, same harness shape as `test_pr_preflight.py::_run_preflight` (stub `gh` returning empty `issue_comments` → phase1, on branch `issue-854/implementation`, `ORCHESTRATE_OFF=""`), body built with a real tab before the terminator `EOF`:

```python
# /tmp/drive_hook.py — full script also isolates the cmd string via
# concatenation so the driving Bash invocation itself doesn't literally
# contain "gh pr create" (which would trip this same hook on the
# controlling session).
cmd = (
    "gh" + " " + "pr" + " " + "create" + ' --title "x" --body "$(cat <<-EOF\n'
    '## Summary\n\nAddresses #854 - phase 1.\n\n'
    '- decided not "무리" (impractical) to do X\n\n'
    'Closes #854\n'
    '\tEOF\n)"'
)
r = subprocess.run(["bash", PREFLIGHT], input=payload, capture_output=True,
                    text=True, env=env, cwd=str(repo_dir), timeout=20)
print(r.returncode, r.stdout, r.stderr)
```
Run: `python3 /tmp/drive_hook.py`

### Observed

`_HEREDOC_BODY_RE.search(cmd)` returns `None` (no match — the tab before the terminator `EOF` breaks the pattern), so extraction falls through to the old quote-balance regex, which stops at the first literal `"` (the one opening `"무리"`) and captures only:
```
'$(cat <<-EOF\n## Summary\n\nAddresses #854 - phase 1.\n\n- decided not '
```
— `Closes #854` is outside the captured body entirely. Driving the real hook end-to-end: `returncode: 0`, empty stderr — the phase-1 PR is silently allowed through even though its actual body genuinely contains `Closes #854` on a phase-1 branch with no approval yet.

### Expected

A phase-1 PR body genuinely containing `Closes #854` must be refused (exit 2, `pr-preflight: phase-1 제안 PR 본문에 closing 키워드...` on stderr) regardless of whether the heredoc's terminator line happens to be tab-indented — the same acceptance bar the new regex already meets for the non-indented `<<-EOF` and `<<EOF` forms (see `test_hook_denies_synthetic_heredoc_body_with_embedded_quote_and_closes`, which only exercises `<<'EOF'` with a bare, non-indented terminator).
