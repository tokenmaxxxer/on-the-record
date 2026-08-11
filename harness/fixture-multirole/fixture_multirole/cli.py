import argparse


def _build_parser():
    parser = argparse.ArgumentParser(prog="fixture-multirole")
    subparsers = parser.add_subparsers(dest="command")

    save_p = subparsers.add_parser("save")
    save_p.add_argument("path")
    save_p.add_argument("value")

    load_p = subparsers.add_parser("load")
    load_p.add_argument("path")

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if args.command in ("save", "load"):
        # Requirement (issue #895 type 6): pick storage_a or storage_b,
        # wire it in here, record the choice and rejected alternative's
        # reason, and verify it works. Neither backend is wired yet.
        raise SystemExit(f"{args.command} is not wired to a storage backend yet")
    parser.print_help()


if __name__ == "__main__":
    main()
