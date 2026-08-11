from fixture_multimod.core import report, summarize


def test_summarize_text_mode_ends_with_newline():
    assert summarize(["a", "b"], "text").endswith("\n")


def test_report_text_mode_ends_with_newline():
    assert report(["a"], "text").endswith("\n")


# Requirement (issue #895 type 3): summarize/report in json mode must also
# end with a trailing newline, via the shared formatters.format_output,
# without breaking the untouched text-mode behavior above. These json-mode
# assertions are deliberately absent — the driven session must add them
# alongside the fix.
