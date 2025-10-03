"""Pydantic models that describe the Streamlit session state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Mapping

from utils import flatten_to_json_pointers, unflatten_from_json_pointers

DEFAULT_COMPANIONSHIP_COUNT = 4
DEFAULT_MISSIONARIES_PER_COMPANIONSHIP = 2


def _default_missionaries() -> list[Missionary]:
    """Return the default missionary collection for a companionship."""

    return [Missionary() for _ in range(DEFAULT_MISSIONARIES_PER_COMPANIONSHIP)]


class Missionary(BaseModel):
    """Represents a single missionary entry in the planner."""

    title: str = "Elder"
    name: str = ""
    photo: str | None = None


class Companionship(BaseModel):
    """Container for missionaries and their associated contact details."""

    missionaries: list[Missionary] = Field(default_factory=_default_missionaries)
    phone_number: str = ""
    schedule: list[str] = Field(default_factory=list)


class AppState(BaseModel):
    """Top-level representation of the Streamlit session state."""

    num_companionships: int = DEFAULT_COMPANIONSHIP_COUNT
    companionships_data: list[Companionship] = Field(default_factory=list)
    missionary_counts: list[int] = Field(default_factory=lambda: [2 for _ in range(4)])
    generated_pdf: str = ""

    @classmethod
    def create_default(cls) -> AppState:
        """Create an application state instance populated with default data."""

        companionships = [Companionship() for _ in range(DEFAULT_COMPANIONSHIP_COUNT)]
        return cls(companionships_data=companionships)

    def to_session_state(self) -> dict[str, Any]:
        """Convert the model into a structure suitable for ``st.session_state``."""

        return flatten_to_json_pointers(self.model_dump(exclude_none=False))

    @classmethod
    def from_session_state(cls, session_state: Mapping[str, Any]) -> AppState:
        """Build an ``AppState`` instance from an existing ``st.session_state`` mapping."""

        payload: dict[str, Any] = unflatten_from_json_pointers(session_state)
        return cls.model_validate(payload)


def create_companionship(missionary_count: int) -> Companionship:
    """Create a blank companionship with a specific number of missionaries."""

    missionaries = [Missionary() for _ in range(missionary_count)]
    return Companionship(missionaries=missionaries)
