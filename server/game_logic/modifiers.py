from dataclasses import dataclass
from typing import List, Tuple, Any


@dataclass
class Modifier:
    name: str
    cost: int
    ID: int
    purchased_on: int or None


@dataclass
class Product(Modifier):
    requirements: List


@dataclass
class Project(Modifier):
    delivered_products: List
    start_datum: Any = None
    project_length: int = 3  # standard is 3 months

    def is_finished(self, actual_month):
        if actual_month - self.project_length > self.start_datum:
            return True
        return False


@dataclass
class Resource(Modifier):
    developed_products: List
    monthly_salary: int
