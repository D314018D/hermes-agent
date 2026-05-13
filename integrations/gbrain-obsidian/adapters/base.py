from abc import ABC, abstractmethod
from typing import Any, Dict

from core.schemas import RawInputEvent


class BaseInputAdapter(ABC):
    """Convert a platform payload into a RawInputEvent without routing decisions."""

    source = "unknown"
    source_type = "unknown"

    @abstractmethod
    def can_handle(self, payload: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def to_raw_event(self, payload: Dict[str, Any]) -> RawInputEvent:
        raise NotImplementedError
