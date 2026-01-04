from dataclasses import dataclass


@dataclass
class UserProfile:
    age: int
    employment_status: str
    income: int
    location: str