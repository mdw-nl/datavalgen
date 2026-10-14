from typing import Annotated

import pandas as pd
import pytest
from pydantic import BaseModel, Field

from datavalgen.cli import generate
from datavalgen.factory import BaseDataModelFactory


class _Model(BaseModel):
    name: str
    age: Annotated[int, Field(ge=0, le=120)]
    score: float


class _Factory(BaseDataModelFactory[_Model]):
    __model__ = _Model


def test_seed_random_makes_batches_reproducible():
    _Factory.seed_random(42)
    first = _Factory.batch_dataframe(20)
    _Factory.seed_random(42)
    second = _Factory.batch_dataframe(20)
    pd.testing.assert_frame_equal(first, second)


def test_different_seeds_give_different_batches():
    _Factory.seed_random(1)
    first = _Factory.batch_dataframe(20)
    _Factory.seed_random(2)
    second = _Factory.batch_dataframe(20)
    assert not first.equals(second)


@pytest.mark.parametrize("seed_args", [["--seed", "7"], ["-s", "7"]])
def test_generate_cli_seed_is_applied(tmp_path, monkeypatch, seed_args):
    monkeypatch.setattr(generate, "get_factory", lambda *a, **k: _Factory)
    out_a = tmp_path / "a.csv"
    out_b = tmp_path / "b.csv"
    generate.main(["-f", "x", "-n", "15", "-o", str(out_a), *seed_args])
    generate.main(["-f", "x", "-n", "15", "-o", str(out_b), *seed_args])
    assert out_a.read_text() == out_b.read_text()


def test_generate_cli_without_seed_is_not_forced_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(generate, "get_factory", lambda *a, **k: _Factory)
    out_a = tmp_path / "a.csv"
    out_b = tmp_path / "b.csv"
    generate.main(["-f", "x", "-n", "200", "-o", str(out_a)])
    generate.main(["-f", "x", "-n", "200", "-o", str(out_b)])
    assert out_a.read_text() != out_b.read_text()
