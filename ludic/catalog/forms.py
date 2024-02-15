from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Literal, get_origin, override

from ludic.attrs import BaseAttrs, FormAttrs, InputAttrs, TextAreaAttrs
from ludic.base import Component
from ludic.html import div, form, input, label, textarea
from ludic.types import AnyElement, ComplexChildren, PrimitiveChild
from ludic.utils import get_element_attrs_annotations

from .utils import attr_to_camel


class ValidationError(Exception):
    reason: str

    def __init__(self, reason: str) -> None:
        self.reason = reason


@dataclass
class FieldMeta:
    """Class to be used as an annotation for attributes.

    Example:
        def validate_email(email: str) -> str:
            if len(email.split("@")) != 2:
                raise ValidationError("Invalid email")
            return email

        class CustomerAttrs(BaseAttrs):
            id: str
            name: Annotated[
                str,
                FieldMeta(label="Email"),
            ]
    """

    label: str
    kind: Literal["input", "textarea"] = "input"
    type: Literal["text", "number", "email", "password", "hidden"] = "text"
    attrs: InputAttrs | TextAreaAttrs | None = None
    validator: Callable[[Any], PrimitiveChild] = str

    def create_field(self, key: str, value: Any) -> AnyElement:
        value = self.validator(value)
        attrs = self.attrs or {}
        attrs["name"] = key

        match self.kind:
            case "input":
                return InputField(value, label=self.label, type=self.type, **attrs)
            case "textarea":
                return TextAreaField(value, label=self.label, **attrs)


class FieldAttrs(BaseAttrs, total=False):
    label: str
    class_div: str


class InputFieldAttrs(FieldAttrs, InputAttrs):
    pass


class TextAreaFieldAttrs(FieldAttrs, TextAreaAttrs):
    pass


class FormField[*Te, Ta: FieldAttrs](Component[*Te, Ta]):
    def get_label_text(self) -> str:
        return self.attrs.get("label", attr_to_camel(str(self.children[0])))


class InputField(FormField[PrimitiveChild, InputFieldAttrs]):
    @override
    def render(self) -> div:
        label_attrs = {}
        input_attrs = self.attrs_for(input)
        if "name" in self.attrs:
            input_attrs["id"] = label_attrs["for_"] = self.attrs["name"]

        return div(
            label(self.get_label_text(), **label_attrs),
            input(value=self.children[0], **input_attrs),
            class_=self.attrs.get("class_div", "form-input"),
        )


class TextAreaField(FormField[PrimitiveChild, TextAreaFieldAttrs]):
    @override
    def render(self) -> div:
        label_attrs = {}
        textarea_attrs = self.attrs_for(textarea)
        if "name" in self.attrs:
            textarea_attrs["id"] = label_attrs["for_"] = self.attrs["name"]

        return div(
            label(self.get_label_text(), **label_attrs),
            textarea(self.children[0], **textarea_attrs),
            class_=self.attrs.get("class_div", "form-textarea"),
        )


class Form(Component[*ComplexChildren, FormAttrs]):
    """A component helper for creating HTML forms."""

    @staticmethod
    def create_fields(element: AnyElement) -> ComplexChildren:
        """Create form fields from the given attributes.

        Example:

            class CustomerAttrs(BaseAttrs):
                id: str
                name: Annotated[
                    str,
                    InputMeta(label="Customer Name"),
                ]

            class Customer(Component[BaseAttrs]):
                def render(self): ...

            customer = Customer(id=1, name="John Doe")
            fields = Form.create_fields(customer)

            form = Form(*fields)

        Args:
            element (AnyElement): The element to create forms from.

        Returns:
            ComplexChildren: list of form fields.
        """
        annotations = get_element_attrs_annotations(element, include_extras=True)
        fields: list[AnyElement] = []

        for name, annotation in annotations.items():
            if get_origin(annotation) is not Annotated:
                continue
            for metadata in annotation.__metadata__:
                if isinstance(metadata, FieldMeta) and name in element.attrs:
                    field = metadata.create_field(name, element.attrs[name])
                    fields.append(field)

        return tuple(fields)

    @override
    def render(self) -> form:
        return form(*self.children, **self.attrs)