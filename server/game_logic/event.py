from dataclasses import dataclass
from typing import List, Tuple, Any
from .efficiency import Efficiency


@dataclass
class Event:
    description: str
    appear_first_in_trimester: int
    required_efficiencies: List
    result_success: Tuple
    result_failure: Tuple
    ID: int = None
    level: int = None

