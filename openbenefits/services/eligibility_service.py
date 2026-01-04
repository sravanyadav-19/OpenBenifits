from typing import List

from ..models.scheme import Scheme
from ..models.user_profile import UserProfile


def is_eligible(user: UserProfile, scheme: Scheme) -> bool:
    c = scheme.criteria

    if c.min_age is not None and user.age < c.min_age:
        return False
    if c.max_age is not None and user.age > c.max_age:
        return False
    if c.employment_status_in is not None and user.employment_status not in c.employment_status_in:
        return False
    if c.max_income is not None and user.income > c.max_income:
        return False
    if c.location_in is not None and user.location not in c.location_in:
        return False

    return True


def find_eligible_schemes(user: UserProfile, schemes: List[Scheme]) -> List[Scheme]:
    return [s for s in schemes if is_eligible(user, s)]