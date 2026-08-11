from fixture_ambiguous import _build_parser


def test_convert_subcommand_is_registered():
    parser = _build_parser()
    args = parser.parse_args(["convert"])
    assert args.command == "convert"


# The driven session's own conversion behavior (once it settles the
# ambiguity — by asking or by a flagged assumption) is not asserted here:
# this fixture's acceptance for issue #895 type 5 is scored from the
# transcript/final_report (signals #4 and #5), not from a fixed expected
# conversion, since the correct target units are the deliberately
# withheld fact.
