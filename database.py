from dataclasses import dataclass


@dataclass
class Userdata:
    days: int = 0
    days_since_last_check: int = 0
