from types import SimpleNamespace

from pydantic import BaseModel

from datavalgen.plugins import get_model, iter_models


class ExampleModel(BaseModel):
    value: int


class OtherModel(BaseModel):
    value: int


class _FakeMetadata:
    def __init__(self, name: str):
        self._name = name

    def get(self, key: str) -> str | None:
        if key == "Name":
            return self._name
        return None

    def get_all(self, key: str) -> list[str] | None:
        return None


class _FakeDist:
    def __init__(self, name: str):
        self.name = name
        self.metadata = _FakeMetadata(name)


class _FakeEntryPoint:
    def __init__(self, name: str, obj: object, dist_name: str):
        self.name = name
        self._obj = obj
        self.dist = _FakeDist(dist_name)

    def load(self) -> object:
        return self._obj


def test_get_model_filters_by_distribution(monkeypatch):
    fake_eps = [
        _FakeEntryPoint("example", ExampleModel, "datavalgen-model-example"),
        _FakeEntryPoint("example", OtherModel, "some-bad-dependency"),
    ]
    monkeypatch.setattr(
        "datavalgen.plugins.entry_points",
        lambda *, group: fake_eps,
    )

    model = get_model("example", distribution="datavalgen-model-example")

    assert model is ExampleModel


def test_iter_models_filters_by_distribution(monkeypatch):
    fake_eps = [
        _FakeEntryPoint("example", ExampleModel, "datavalgen-model-example"),
        _FakeEntryPoint("other", OtherModel, "some-bad-dependency"),
    ]
    monkeypatch.setattr(
        "datavalgen.plugins.entry_points",
        lambda *, group: fake_eps,
    )

    rows = list(iter_models(distribution="datavalgen-model-example"))

    assert [(name, dist_name) for name, _obj, dist_name, _homepage in rows] == [
        ("example", "datavalgen-model-example")
    ]


def test_get_model_reports_distribution_scoped_lookup(monkeypatch):
    fake_eps = [
        _FakeEntryPoint("example", OtherModel, "some-bad-dependency"),
    ]
    monkeypatch.setattr(
        "datavalgen.plugins.entry_points",
        lambda *, group: fake_eps,
    )

    try:
        get_model("example", distribution="datavalgen-model-example")
    except LookupError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected LookupError")

    assert "distribution 'datavalgen-model-example'" in message
    assert "Available 'datavalgen.models' entry-point: <none>" in message
