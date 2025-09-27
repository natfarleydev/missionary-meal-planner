"""Pydantic models that describe the Streamlit session state."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Mapping, Optional

from pydantic import BaseModel, Field

DEFAULT_COMPANIONSHIP_COUNT = 4
DEFAULT_MISSIONARIES_PER_COMPANIONSHIP = 2
LOCAL_STORAGE_KEY = "missionaryMealPlanner.appState"


def _default_missionaries() -> List["Missionary"]:
    """Return the default missionary collection for a companionship."""

    return [Missionary() for _ in range(DEFAULT_MISSIONARIES_PER_COMPANIONSHIP)]


class Missionary(BaseModel):
    """Represents a single missionary entry in the planner."""

    title: str = "Elder"
    name: str = ""
    photo: Optional[str] = None


class Companionship(BaseModel):
    """Container for missionaries and their associated contact details."""

    missionaries: List[Missionary] = Field(default_factory=_default_missionaries)
    phone_number: str = ""
    schedule: List[str] = Field(default_factory=list)


class AppState(BaseModel):
    """Top-level representation of the Streamlit session state."""

    num_companionships: int = DEFAULT_COMPANIONSHIP_COUNT
    companionships_data: List[Companionship] = Field(default_factory=list)
    missionary_counts: Dict[int, int] = Field(default_factory=dict)
    dates: Dict[str, date] = Field(default_factory=dict)
    generated_pdf: Optional[bytes] = None

    @classmethod
    def create_default(cls) -> "AppState":
        """Create an application state instance populated with default data."""

        companionships = [Companionship() for _ in range(DEFAULT_COMPANIONSHIP_COUNT)]
        return cls(companionships_data=companionships)

    def to_session_state(self) -> Dict[str, Any]:
        """Convert the model into a structure suitable for ``st.session_state``."""

        payload = self.model_dump()
        payload["companionships_data"] = [item.model_dump() for item in self.companionships_data]
        return payload

    @classmethod
    def from_session_state(cls, session_state: Mapping[str, Any]) -> "AppState":
        """Build an ``AppState`` instance from an existing ``st.session_state`` mapping."""

        payload: Dict[str, Any] = {
            "num_companionships": session_state.get("num_companionships", DEFAULT_COMPANIONSHIP_COUNT),
            "companionships_data": session_state.get("companionships_data", []),
            "missionary_counts": session_state.get("missionary_counts", {}),
            "dates": session_state.get("dates", {}),
            "generated_pdf": session_state.get("generated_pdf"),
        }
        return cls.model_validate(payload)

    def to_storage_payload(self) -> Dict[str, Any]:
        """Serialize the state into a JSON-compatible dictionary for localStorage."""

        storage_copy = self.model_copy(update={"generated_pdf": None}, deep=True)
        payload = storage_copy.model_dump()
        payload["dates"] = {
            key: value.isoformat() if isinstance(value, date) else value
            for key, value in payload["dates"].items()
        }
        payload["missionary_counts"] = {
            str(key): value for key, value in payload["missionary_counts"].items()
        }
        payload["companionships_data"] = [item.model_dump() for item in storage_copy.companionships_data]
        return payload


def create_companionship(missionary_count: int) -> Companionship:
    """Create a blank companionship with a specific number of missionaries."""

    missionaries = [Missionary() for _ in range(missionary_count)]
    return Companionship(missionaries=missionaries)

