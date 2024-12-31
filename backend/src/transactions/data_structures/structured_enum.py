from dataclasses import dataclass
from typing import TypeVar, Any, Dict
from pydantic import BaseModel, create_model, Field
from pydantic._internal._model_construction import ModelMetaclass

T = TypeVar("T")

class _StructuredEnumMeta(ModelMetaclass):
    def __new__(mcs, name, bases, namespace, __pydantic_reset_parent_namespace__=None, **kwargs):
        variants = {}
        for key, value in namespace.items():
            if isinstance(value, type) and hasattr(value, "__annotations__"):
                fields = value.__annotations__
                variant_model = create_model(
                    f"{name}_{key}",
                    __base__=StructuredEnum,
                    __module__=namespace.get('__module__'),
                    variant_name=(str, Field(default=key)),
                    **{k: (v, ...) for k, v in fields.items()},
                )
                variant_model.__match_args__ = tuple(fields.keys())
                variants[key] = variant_model

        cls = super().__new__(mcs, name, bases, namespace)
        cls._variants = variants

        for variant_name, variant_class in variants.items():
            setattr(cls, variant_name, variant_class)

        return cls

    def __instancecheck__(cls, instance):
        return any(isinstance(instance, variant) for variant in cls._variants.values())


class StructuredEnum(BaseModel, metaclass=_StructuredEnumMeta):
    variant_name: str = Field()

    def model_dump(self) -> Dict[str, Any]:
        return {self.variant_name: {k: v for k, v in super().model_dump().items() if k != 'variant_name'}}

    def __eq__(self, other):
        if not isinstance(other, BaseModel):
            return False
        return (
            self.variant_name == other.variant_name
            and self.model_dump() == other.model_dump()
        )

    @classmethod
    def model_validate(cls, obj: Any) -> Any:
        if isinstance(obj, dict) and len(obj) == 1:
            variant_name, data = next(iter(obj.items()))
            if variant_name in cls._variants:
                return getattr(cls, variant_name)(**data)
        raise ValueError(f"Invalid data for {cls.__name__}")

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.variant_name}({', '.join(f'{k}={v}' for k, v in self.model_dump().items() if k != self.variant_name)})"