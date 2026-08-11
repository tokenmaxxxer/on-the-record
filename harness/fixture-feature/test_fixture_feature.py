from fixture_feature import greet


def test_greet_returns_text_message():
    assert greet("Ada") == "Hello, Ada!"


# Requirement (issue #895 type 2) asks for a test covering both the
# default "text" format and a new "json" format for the greet command.
# The json-format test is deliberately absent: writing it is part of the
# requirement the driven session must satisfy.
