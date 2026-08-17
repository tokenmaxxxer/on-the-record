# Deviation log

2026-08-13T00:00:00Z inline upstream-defect-report(issue-1174): task
brief named an existing rulebook repo target
(tokenmaxxxer/upstream-defect-report-rulebook) that did not yet exist;
created it directly rather than inventing an unenforced docs/playbook/
bucket in the parent repo — see docs/issue-1174/reports/upstream-defect-report.md.

2026-08-17T00:00:00Z filed implementation(issue-1726): warrant-hunter
(dispatched before phase-2 completion) found
gates/test_product_capture_vs_deliverable_guard.py lines 135-159 (test
function t_empty_state_bootstrap_still_works) is an xfail(strict=False)
regression guard whose docstring still frames bootstrap-on-first-flag as
intentional behavior ("(d) regression guard for #566's
bootstrap-on-first-flag: no docs/product/ directory at all -> still
bootstraps and flags") and whose body asserts doc.exists() /
"Requirements" in doc.read_text() — the exact behavior #1726 removed by
design. canonical: gates/test_product_capture_vs_deliverable_guard.py
lines 135-159, read this session. Fixing it needs editing a file
outside issue-1726's frozen write set
(on-the-record/hooks/product-capture-stopgate.sh,
on-the-record/hooks/test_product_capture_stopgate.py), so per
SCOPE-EXCEEDED RULE the frozen write set is finished and this is
reported, not spawned — see docs/issue-1726/reports/implementation.md's
Open findings.
