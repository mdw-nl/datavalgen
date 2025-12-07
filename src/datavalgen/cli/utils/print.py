from typing import Iterable, Tuple

from datavalgen.plugins import iter_models, iter_factories

# (name, cls, dist_name, homepage)
PluginRow = Tuple[str, object, str, str]


def _print_plugin_list(kind: str, rows: Iterable[PluginRow]) -> None:
    """
    Prints a table of plugins of given kind ("model" or "factory").
    """
    rows = list(rows)
    if not rows:
        print(f"No datavalgen {kind}s found.")
        return

    # Compute column widths
    name_label = kind
    pkg_label = "package"

    name_w = max(len(name_label), max(len(name) for name, *_ in rows))
    dist_w = max(len(pkg_label), max(len(dist) for _, _, dist, _ in rows))

    print(f"List of datavalgen {kind}s installed:")
    print(f"  {name_label:<{name_w}} | {pkg_label:<{dist_w}} | homepage")
    print(f"  {'-' * name_w} | {'-' * dist_w} | {'-' * 8}")

    for name, _obj, dist, homepage in sorted(rows, key=lambda r: r[0]):
        print(f"  {name:<{name_w}} | {dist:<{dist_w}} | {homepage or ''}")


def print_factory_list() -> None:
    """
    Prints a table of registered datavalgen factories.
    """
    _print_plugin_list("factory", iter_factories())


def print_model_list() -> None:
    """
    Prints a table of registered datavalgen models.
    """
    _print_plugin_list("model", iter_models())
