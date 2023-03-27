"""Linkedin location codes"""
from enum import Enum


class Location(Enum):
    """Linkedin location code"""

    AU = 101452733
    BE = 100565514
    BR = 106057199
    CA = 101174742
    DE = 101282230
    FR = 105015875
    NL = 102890719
    PL = 105072130
    UK = 101165590
    US = 103644278

    @classmethod
    def as_list(cls) -> list[str]:
        """Returns a list of location names"""
        return [location.name for location in cls]
