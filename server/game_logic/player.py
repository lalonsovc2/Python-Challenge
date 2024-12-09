from copy import deepcopy
import numpy as np
import random
from typing import Tuple
import logging


class Player:
    def __init__(self, context=None, initial_budget=0):
        self.context = context
        self.efficiencies = deepcopy(self.context.EFFICIENCIES)  # standard efficiencies beginning with 0 points
        self.products = dict()
        self.projects = dict()
        self.resources = dict()
        self.budget = initial_budget
        self.score = 0
        self.salaries_to_pay = 0
        self.actual_date = 0  # day stacked (360)
        self._get_legacy()
        self.first_turn_in_month = True

    @property
    def month(self):
        return (self.actual_date // 30) + 1

    @property
    def current_projects(self):
        return [key for key, value in self.projects.items() if value.is_finished(self.month)]

    def _get_legacy(self):
        legacy_list = self.context.LEGACY
        
        # Verificamos si legacy_list tiene elementos
        if legacy_list:
            legacy_choice = random.choice(legacy_list)
            
            # Aseguramos que legacy_choice sea iterable (por ejemplo, una lista o un conjunto)
            if isinstance(legacy_choice, list):
                
                for item in legacy_choice:
                    self._add_product(item)
                    print(f"You have inherited: {self.context.PRODUCTS.get(item).name}")
            else:
                # Si legacy_choice no es iterable, lo tratamos como un solo elemento
                self._add_product(legacy_choice)
                print(f"You have inherited: {self.context.PRODUCTS.get(legacy_choice).name}")
        else:
            print("No legacy items available to inherit.")

    def budget_enough_for_buying(self, modifier):
        if self.budget < modifier.cost:
            print(f"You dont have enough budget to buy: {modifier.name}")
            return False

        return True

    def _add_product(self, product_id):
        product = self.context.PRODUCTS.get(product_id, None)
        name = product.name
        if product_id in self.products.keys():
            print(f"Product {name} is already available")
            return
        purchased_product = deepcopy(product)
        purchased_product.purchased_on = self.month
        self.products[product_id] = purchased_product
        for efficiency in self.efficiencies.values():
            efficiency.update_by_product(product, self.products)

    def check_number_of_purchases(self, modifier_type):
        purchased_modifiers = None

        if modifier_type == "product":
            purchased_modifiers = {
                key: value for key, value in self.products.items() if value.purchased_on == self.month
            }
            if len(purchased_modifiers) >= 5:
                return False  # Number of purchases this month has been reached
            else:
                return True
        elif modifier_type == "project":
            purchased_modifiers = {
                key: value for key, value in self.projects.items() if value.purchased_on == self.month
            }
        elif modifier_type == "resource":
            purchased_modifiers = {
                key: value for key, value in self.resources.items() if value.purchased_on == self.month
            }
        else:
            pass
        if len(purchased_modifiers) >= 1:
            return False
        return True

    def buy_product(self, product_id):
        if not self.check_number_of_purchases("product"):
            print("You have already purchased 5 products this month, you are not allowed to buy more")
            return
        product = self.context.PRODUCTS.get(product_id, None)

        if self.budget_enough_for_buying(product):
            self._add_product(product_id)
            # Todo: print some message if the requirements for the product are not bought
            self.budget -= product.cost

    def buy_project(self, project_id):
        if len(self.current_projects) >= 3:
            print("You are note allowed to run more than 3 projects in parallel")
            return
        if not self.check_number_of_purchases("project"):
            print("You have already bought 1 project this month, you are not allowed to buy more")
            return
        project = self.context.PROJECTS.get(project_id, None)
        name = project.name
        if project_id in self.projects.keys():
            print(f"Project {name} is already available")
            return
        if self.budget_enough_for_buying(project):
            bought_project = deepcopy(project)
            bought_project.purchased_on = self.month
            bought_project.start_datum = self.month + 1
            # Todo: check datum --> do you still have time to get the products
            self.projects[project_id] = bought_project
            self.budget -= project.cost

    def hire_resource(self, resource_id):
        if not self.check_number_of_purchases("resource"):
            print("You have already hired 1 resource this month, you are not allowed to buy more")
            return
        resource = self.context.RESOURCES.get(resource_id, None)
        name = resource.name
        if resource_id in self.resources.keys():
            print(f"Resource {name} is already available")
            return
        if not self.budget_enough_for_buying(resource):
            return

        hired_resource = deepcopy(resource)
        hired_resource.purchased_on = self.month
        self.resources[resource_id] = hired_resource
        self.salaries_to_pay += hired_resource.monthly_salary
        self.budget -= resource.cost

    def pay_salaries(self):
        self.budget -= self.salaries_to_pay
        # TODO: charge salaries after hiring (not in the first month)

    def get_products_from_projects(self):
        for project_id, project in self.projects.items():
            time_passed = self.month - project.start_datum
            if time_passed == project.project_length:
                delivered_products_ids = project.delivered_products
                for product_id in delivered_products_ids:
                    self._add_product(product_id)  # add products and its efficiencies

                for efficiency in self.efficiencies.values():
                    efficiency.update_by_project(project)  # add points to efficiency corresponding to the project

    def get_products_from_resources(self):
        last_month = self.month - 1
        purchased_resources_last_month = [
            resource for resource in self.resources.values() if resource.purchased_on == last_month
        ]
        for resource in purchased_resources_last_month:
            for product_id in resource.developed_products:
                self._add_product(product_id)

            for efficiency in self.efficiencies.values():
                efficiency.update_by_resource(resource)

    def throw_dices(self, number):
        dices = np.random.randint(1, 6, size=number)
        return dices, dices.sum()

    def check_efficiencies(self):
        pass

    def apply_challenge_result(self, result: Tuple):
        points, money = result
        self.score += points
        self.budget += money

    def display_modifier(self, list_modifiers):
        for modifier in list_modifiers:
            print(f"{modifier.ID}: {modifier.name}")
            print(f"Purchased on: {modifier.purchased_on} for: {modifier.cost} dollars.")
            print("--------------------------------------------------------------------")

    def display_efficiencies(self):
        print(f"Actual value of efficiencies")
        for efficiency in self.efficiencies.values():
            print(f"{efficiency.name}: {efficiency.points}")
