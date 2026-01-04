from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..models.scheme import Scheme, schemes_from_payload


class RulesService:
    """
    Loads and exposes scheme rules from a JSON file.
    """

    def __init__(self, rules_path: Path):
        self._rules_path = Path(rules_path)
        self._schemes: List[Scheme] = []
        self.reload()

    def reload(self) -> None:
        with self._rules_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        self._schemes = schemes_from_payload(payload)

    @property
    def schemes(self) -> List[Scheme]:
        return self._schemes

    def as_dict(self) -> list[dict]:
        return [s.to_dict() for s in self._schemes]