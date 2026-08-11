from fixture_multimod.formatters import format_output


def summarize(items, mode):
    return format_output({"count": len(items)}, mode)


def report(items, mode):
    return format_output({"items": items}, mode)
