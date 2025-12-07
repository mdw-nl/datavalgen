from __future__ import annotations
import warnings

from importlib.metadata import EntryPoints, entry_points
from typing import Iterator, TypeVar, Type

from pydantic import BaseModel

from datavalgen.factory import BaseDataModelFactory

# just for static type checking
TPlugin = TypeVar("TPlugin", bound=type)


def _load_entry_point(group: str, name: str) -> object:
    """
    Load a single entry point from a given group by name.

    `group` is something like "datavalgen.models" or "datavalgen.factories".
    `name` is the symbolic name ("example", "diabetes", ...).
    """
    try:
        eps: EntryPoints = entry_points(group=group)
    except TypeError:
        # Older style, above is Python 3.10+
        eps = entry_points().select(group=group)

    matches = [ep for ep in eps if ep.name == name]
    if not matches:
        available = ", ".join(sorted(ep.name for ep in eps)) or "<none>"
        raise LookupError(
            f"Unknown entry-point {name!r} in group {group!r}.\n"
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
    base_type: Type[TPlugin],
) -> Iterator[tuple[str, Type[TPlugin], str, str]]:
    """
    Generic plugin iterator.

    Yields (name, cls, dist_name, homepage_url) for all entry points in `group`
    whose loaded object is a subclass of `base_type`.
    """
    try:
        eps = entry_points(group=group)
    except TypeError:
        eps = entry_points().select(group=group)  # older style

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

        yield ep.name, obj, dist_name, homepage


def _get_plugin(
    group: str,
    name: str,
    base_type: Type[TPlugin],
) -> Type[TPlugin]:
    """
    Generic resolver for a single plugin in `group` with the given `name`.

    Ensures the loaded object is a subclass of `base_type`.
    """
    obj = _load_entry_point(group, name)

    if not isinstance(obj, type) or not issubclass(obj, base_type):
        typename = getattr(base_type, "__name__", repr(base_type))
        raise TypeError(
            f"Entry point {group!r}:{name!r} did not return a subclass of {typename} "
            f"(got {obj!r})"
        )

    return obj


def iter_models() -> Iterator[tuple[str, Type[BaseModel], str, str]]:
    """
    Yield (name, model_class, dist_name, homepage_url) for all registered
    datavalgen models.

    Models are registered under the entry point group "datavalgen.models".
    `homepage_url` may be "" if none is found.
    """
    return _iter_plugins("datavalgen.models", BaseModel)


def iter_factories() -> Iterator[tuple[str, Type[BaseDataModelFactory], str, str]]:
    """
    Yield (name, factory_class, dist_name, homepage_url) for all registered
    datavalgen factories.

    Factories are registered under the entry point group "datavalgen.factories".
    `homepage_url` may be "" if none is found.
    """
    return _iter_plugins("datavalgen.factories", BaseDataModelFactory)


def get_model(name: str) -> Type[BaseModel]:
    """
    Resolve a single model by symbolic name (e.g. "example", "diabetes").
    """
    return _get_plugin(
        "datavalgen.models",
        name,
        BaseModel,
    )


def get_factory(name: str) -> Type[BaseDataModelFactory]:
    """
    Resolve a single factory by symbolic name (e.g. "example", "diabetes").
    """
    return _get_plugin(
        "datavalgen.factories",
        name,
        BaseDataModelFactory,
    )
