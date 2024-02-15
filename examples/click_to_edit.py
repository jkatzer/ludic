from typing import Annotated, Self

from starlette.datastructures import FormData

from ludic.base import BaseAttrs
from ludic.catalog.buttons import ButtonDanger, ButtonPrimary
from ludic.catalog.forms import FieldMeta, Form
from ludic.catalog.lists import Pairs
from ludic.html import div
from ludic.web.endpoints import Endpoint
from ludic.web.exceptions import NotFoundError

from examples import Body, Header, Page, app


class ContactAttrs(BaseAttrs):
    id: str
    first_name: Annotated[str, FieldMeta(label="First Name")]
    last_name: Annotated[str, FieldMeta(label="Last Name")]
    email: Annotated[str, FieldMeta(label="Email", type="email")]


contacts = {
    "1": ContactAttrs(
        id="1",
        first_name="John",
        last_name="Doe",
        email="qN6Z8@example.com",
    )
}


@app.endpoint("/")
class Index(Endpoint):
    @classmethod
    async def get(cls) -> Self:
        return cls()

    def render(self) -> Page:
        return Page(
            Header("Click To Edit"),
            Body(*(Contact(**contact) for contact in contacts.values())),
        )


@app.endpoint("/contacts/{id}")
class Contact(Endpoint[ContactAttrs]):
    @classmethod
    async def get(cls, id: str) -> Self:
        contact = contacts.get(id)
        if contact is None:
            raise NotFoundError("Contact not found")

        return cls(**contact)

    @classmethod
    async def put(cls, id: str, data: FormData) -> Self:
        contact = contacts.get(id)
        if contact is None:
            raise NotFoundError("Contact not found")

        contact["first_name"] = str(data["first_name"])
        contact["last_name"] = str(data["last_name"])
        contact["email"] = str(data["email"])

        return cls(**contact)

    def render(self) -> div:
        return div(
            Pairs(items=self.attrs.items()),
            ButtonPrimary(
                "Click To Edit",
                hx_get=self.url_for(ContactForm),
            ),
            hx_target="this",
            hx_swap="outerHTML",
        )


@app.endpoint("/contacts/{id}/form")
class ContactForm(Endpoint[ContactAttrs]):
    @classmethod
    async def get(cls, id: str) -> Self:
        contact = contacts.get(id)

        if contact is None:
            raise NotFoundError("Contact not found")

        return cls(**contact)

    def render(self) -> Form:
        return Form(
            *Form.create_fields(self),
            ButtonPrimary("Submit"),
            ButtonDanger("Cancel", hx_get=self.url_for(Contact)),
            hx_put=self.url_for(Contact),
            hx_target="this",
        )