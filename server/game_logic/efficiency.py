from dataclasses import dataclass
from typing import List, Tuple, Any
import numpy as np

@dataclass
class Efficiency:
    name: str
    modifiable_by_products: List
    modifiable_by_projects: List
    modifiable_by_resources: List
    points: int = None
    ID: int = None
    max_points: int = 36

    @property
    def number_of_products_modifiers(self):
        return len(self.modifiable_by_products)

    @property
    def number_of_projects_modifiers(self):
        length = len(self.modifiable_by_projects)
        return length if length > 0 else None

    @property
    def number_of_resources_modifiers(self):
        length = len(self.modifiable_by_resources)
        return length if length > 0 else None

    def update_by_product(self, product, purchased_products):
        if product.ID in self.modifiable_by_products:
            achieved_points = int(self.max_points / self.number_of_products_modifiers)
            requirements_for_product = product.requirements
            # Key: length of the requirements for the product
            # Value: number of requirements that need to be purchased to get whole benefits
            requirements_dict = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3}
            number_of_requirements_needed = requirements_dict.get(len(requirements_for_product), 4)
            purchased_requirements = [
                requirement for requirement in requirements_for_product if requirement in purchased_products
            ]
            
            if len(purchased_requirements) >= number_of_requirements_needed:
                self.points += np.round(achieved_points, 0)
            else:
                self.points += np.round(achieved_points / 2, 0)

    def update_by_project(self, project):
        if not self.number_of_projects_modifiers:
            return
        if project.ID in self.modifiable_by_projects:
            achieved_points = int(self.max_points / self.number_of_projects_modifiers)
            self.points += np.round(achieved_points, 0)

    def update_by_resource(self, resource):
        if not self.number_of_projects_modifiers:
            return
        if resource.ID in self.modifiable_by_resources:
            achieved_points = int(self.max_points / self.number_of_resources_modifiers)
            self.points += np.round(achieved_points, 0)
