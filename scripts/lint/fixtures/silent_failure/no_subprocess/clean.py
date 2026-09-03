"""A valid, parseable module with zero subprocess call sites -- used to
exercise the lint's empty-state refusal (scan_targets()/_run_scan()):
pointing the scanner at a target where it finds nothing to check must
report a distinct failure, never a silent "0 findings = pass"."""


def add(a: int, b: int) -> int:
    return a + b
