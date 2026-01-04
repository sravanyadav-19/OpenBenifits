from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class SchemeCriteria:
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    employment_status_in: Optional[List[str]] = None
    max_income: Optional[int] = None
    location_in: Optional[List[str]] = None


@dataclass
class Scheme:
    id: str
    name: str
    description: str
    official_link: str
    criteria: SchemeCriteria

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def schemes_from_payload(payload: Dict[str, Any]) -> List[Scheme]:
    """
    Convert a JSON payload with a 'schemes' list into Scheme objects.
    """
    schemes_raw = payload.get("schemes", [])
    schemes: List[Scheme] = []

    for item in schemes_raw:
        crit = item.get("criteria", {})
        criteria = SchemeCriteria(
            min_age=crit.get("min_age"),
            max_age=crit.get("max_age"),
            employment_status_in=crit.get("employment_status_in"),
            max_income=crit.get("max_income"),
            location_in=crit.get("location_in"),
        )
        scheme = Scheme(
            id=item["id"],
            name=item["name"],
            description=item.get("description", ""),
            official_link=item.get("official_link", ""),
            criteria=criteria,
        )
        schemes.append(scheme)

    return schemes