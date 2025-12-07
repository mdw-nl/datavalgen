from typing import Any, Callable, Generic, TypeVar
from pydantic import BaseModel
from dataclasses import asdict, is_dataclass
from polyfactory.factories.pydantic_factory import ModelFactory
import pandas as pd
from pydantic.fields import FieldInfo


# just for static type-checking. TModel is a type parameter that must be a
# subclass of BaseModel
TModel = TypeVar("TModel", bound=BaseModel)


# class for users to subclass to create their own factories
class BaseDataModelFactory(ModelFactory[TModel], Generic[TModel]):

    __is_base_factory__ = True

    # FIXME: this is a hacky util function to deal with constraints set in the
    #        model (lt, gt) more easily as we write generators for different fields
    #        But it makes bad assumptions about implementation details of pydantic
    @classmethod
    def get_field_constraint(cls, field: str, constraint: str) -> Any:
        """
        Helper method to get a constraint value from a field in the model

        :param field: The field name to get the constraint from
        :param constraint: The constraint name to get the value of (e.g. "lt")

        :return: The constraint value (e.g. date(1969, 7, 20))
        """
        # https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.FieldInfo
        field_info: FieldInfo = cls.__model__.__pydantic_fields__[field]

        if constraint not in field_info.metadata_lookup:
            raise ValueError(
                f"Field {field!r} has no {constraint!r} constraint "
                f"(available: {sorted(field_info.metadata_lookup.keys())})"
            )

        # map from constraint string to constraint type seems to be found in
        # field_info.metadata_lookup
        constraint_type: Callable[[Any], Any] | None = field_info.metadata_lookup[
            constraint
        ]
        # return first instance of that constraint type
        constraint_object: Any | None = next(
            (c for c in field_info.metadata if isinstance(c, constraint_type)), None
        )

        if constraint_object is None:
            raise ValueError(
                f"Could not find a {constraint!r} constraint instance for field {field!r}"
            )

        if not is_dataclass(constraint_object):
            raise TypeError(
                f"Constraint object for {field!r}.{constraint!r} is not a dataclass: "
                f"{constraint_object!r}"
            )

        # we hackily assume constraints are dataclasses with a single field
        # https://github.com/annotated-types/annotated-types/blob/main/annotated_types/__init__.py
        return next(iter(asdict(constraint_object).values()))

    @classmethod
    def batch_dataframe(cls, n: int) -> pd.DataFrame:
        """
        Generate a batch of n instances and return them as a pandas DataFrame
        """
        instances: list[TModel] = cls.batch(n)
        # with 'mode="json" enums take on their value (e.g. 'Yes' not YesNo.yes)
        rows: list[dict[str, Any]] = [
            i.model_dump(by_alias=True, mode="json") for i in instances
        ]
        return pd.DataFrame(rows)
