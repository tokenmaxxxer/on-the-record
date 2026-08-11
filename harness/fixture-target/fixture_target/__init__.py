import argparse

__version__ = "0.1.0"


def _build_parser():
    parser = argparse.ArgumentParser(prog="fixture-target")
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the version and exit",
    )
    return parser


def _resolve_version(args):
    # Seeded defect: reads the wrong module attribute name.
    import fixture_target as _pkg

    if args.version:
        return _pkg.VERSION
    return None


def main():
    parser = _build_parser()
    args = parser.parse_args()
    version = _resolve_version(args)
    if version is not None:
        print(version)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
