from __future__ import annotations
import re
import warnings

from importlib.metadata import EntryPoint, EntryPoints, entry_points
from typing import Any, Iterator, TypeVar, cast

from pydantic import BaseModel

from datavalgen.factory import BaseDataModelFactory

# just for static type checking
TPluginClass = TypeVar("TPluginClass", bound=type[object])


def _normalize_distribution_name(name: str) -> str:
    """
    Normalize a distribution name following the common PEP 503 form.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def _entry_point_distribution_name(ep: EntryPoint) -> str:
    """
    Return the entry point's distribution name, or an empty string if unknown.
    """
    dist = getattr(ep, "dist", None)
    if dist is None:
        return ""
    meta = dist.metadata
    return (meta.get("Name") or dist.name or "").strip()


def _group_entry_points(
    group: str,
    distribution: str | None = None,
) -> list[EntryPoint]:
    """
    Return entry points in a group, optionally restricted to one distribution.
    """
    try:
        eps: EntryPoints = entry_points(group=group)
    except TypeError:
        # Older style, above is Python 3.10+
        eps = entry_points().select(group=group)

    if distribution is None:
        return list(eps)

    wanted = _normalize_distribution_name(distribution)
    return [
        ep
        for ep in eps
        if _normalize_distribution_name(_entry_point_distribution_name(ep)) == wanted
    ]


def _load_entry_point(
    group: str,
    name: str,
    distribution: str | None = None,
) -> object:
    """
    Load a single entry point from a given group by name.

    `group` is something like "datavalgen.models" or "datavalgen.factories".
    `name` is the symbolic name ("example", "diabetes", ...).
    """
    eps = _group_entry_points(group, distribution)
    matches = [ep for ep in eps if ep.name == name]
    if not matches:
        available = ", ".join(sorted(ep.name for ep in eps)) or "<none>"
        distribution_label = (
            f" in distribution {distribution!r}" if distribution is not None else ""
        )
        raise LookupError(
            f"Unknown entry-point {name!r} in group {group!r}{distribution_label}.\n"
            f"Available {group!r} entry-point: {available}"
        )

    if len(matches) > 1:
        warnings.warn(
            f"Multiple entry-points found for {group!r}:{name!r}; "
            f"using the first one from distribution "
            f"{getattr(matches[0], 'dist', '<unknown>')}",
            RuntimeWarning,
            # warn at the caller level
            stacklevel=2,
        )

    return matches[0].load()


def _normalize_url_label(label: str) -> str:
    """
    Normalize a Project-URL label according to the well-known URLs spec:
    lowercase, strip punctuation/whitespace.

    See: https://packaging.python.org/en/latest/specifications/well-known-project-urls/#label-normalization
    """
    return "".join(ch for ch in label.lower() if ch.isalnum())


def _iter_plugins(
    group: str,
    base_type: TPluginClass,
    distribution: str | None = None,
) -> Iterator[tuple[str, TPluginClass, str, str]]:
    """
    Generic plugin iterator.

    Yields (name, cls, dist_name, homepage_url) for all entry points in `group`
    whose loaded object is a subclass of `base_type`.
    """
    eps = _group_entry_points(group, distribution)
    for ep in eps:
        obj = ep.load()
        # Only keep proper classes that subclass the expected base_type
        if not isinstance(obj, type) or not issubclass(obj, base_type):
            continue

        dist = getattr(ep, "dist", None)
        if dist is not None:
            meta = dist.metadata
            dist_name = meta.get("Name") or dist.name
        else:
            meta = None
            dist_name = "<unknown>"

        homepage = ""

        if meta is not None:
            # Prefer a well-known "Homepage" Project-URL
            project_urls = meta.get_all("Project-URL") or []
            for item in project_urls:
                label, _, url = item.partition(",")
                if _normalize_url_label(label) == "homepage":
                    homepage = url.strip()
                    break

            # Fallback to legacy Home-page header (setup.py..)
            if not homepage:
                hp = meta.get("Home-page")
                if hp:
                    homepage = hp.strip()

        yield ep.name, cast(TPluginClass, obj), dist_name, homepage


def _get_plugin(
    group: str,
    name: str,
    base_type: TPluginClass,
    distribution: str | None = None,
) -> TPluginClass:
    """
    Generic resolver for a single plugin in `group` with the given `name`.

    Ensures the loaded object is a subclass of `base_type`.
    """
    obj = _load_entry_point(group, name, distribution)

    if not isinstance(obj, type) or not issubclass(obj, base_type):
        typename = getattr(base_type, "__name__", repr(base_type))
        raise TypeError(
            f"Entry point {group!r}:{name!r} did not return a subclass of {typename} "
            f"(got {obj!r})"
        )

    return cast(TPluginClass, obj)


def iter_models(
    distribution: str | None = None,
) -> Iterator[tuple[str, type[BaseModel], str, str]]:
    """
    Yield (name, model_class, dist_name, homepage_url) for all registered
    datavalgen models.

    Models are registered under the entry point group "datavalgen.models".
    `homepage_url` may be "" if none is found.
    """
    return _iter_plugins("datavalgen.models", BaseModel, distribution)


def iter_factories(
    distribution: str | None = None,
) -> Iterator[
    tuple[str, type[BaseDataModelFactory[Any]], str, str]
]:
    """
    Yield (name, factory_class, dist_name, homepage_url) for all registered
    datavalgen factories.

    Factories are registered under the entry point group "datavalgen.factories".
    `homepage_url` may be "" if none is found.
    """
    return _iter_plugins("datavalgen.factories", BaseDataModelFactory, distribution)


def get_model(
    name: str,
    distribution: str | None = None,
) -> type[BaseModel]:
    """
    Resolve a single model by symbolic name (e.g. "example", "diabetes").
    """
    return _get_plugin(
        "datavalgen.models",
        name,
        BaseModel,
        distribution,
    )


def get_factory(
    name: str,
    distribution: str | None = None,
) -> type[BaseDataModelFactory[Any]]:
    """
    Resolve a single factory by symbolic name (e.g. "example", "diabetes").
    """
    return _get_plugin(
        "datavalgen.factories",
        name,
        BaseDataModelFactory,
        distribution,
    )
