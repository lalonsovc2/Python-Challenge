from .modifiers import Product, Project, Resource
from .efficiency import Efficiency
from .event import Event


def load_efficiencies(path):
    efficiencies_dict = dict()
    with open(path) as f:
        content = f.read().splitlines()
        for line in content:
            parts = line.split("%%%")
            name_and_products = parts[0].split(";")
            idx, name = name_and_products[0:2]
            modifiers_products = name_and_products[2:]
            modifiers_products = [idx for idx in modifiers_products if len(idx) != 0]

            modifiers_projects = parts[1].split(";")
            modifiers_projects = [idx for idx in modifiers_projects if len(idx) != 0]

            modifiers_resources = parts[2].split(";")
            modifiers_resources = [idx for idx in modifiers_resources if len(idx) != 0]

            efficiencies_dict[idx] = Efficiency(
                name=name, ID=idx, points=0, modifiable_by_products=modifiers_products,
                modifiable_by_projects=modifiers_projects, modifiable_by_resources=modifiers_resources
            )
    return efficiencies_dict


def load_products(path):
    products_dict = dict()
    with open(path) as f:
        content = f.read().splitlines()
        for line in content:
            line_content = line.split(";")
            idx, name, cost = line_content[0:3]
            requirements = line_content[3:]
            requirements = [idx for idx in requirements if len(idx) != 0]

            products_dict[idx] = Product(
                name=name, cost=int(cost), ID=idx, requirements=requirements, purchased_on=None
            )
    return products_dict


def load_projects(path):
    projects_dict = dict()
    with open(path) as f:
        content = f.read().splitlines()
        for line in content:
            line_content = line.split(";")
            idx, name, cost = line_content[0:3]
            delivered_products = line_content[3:]
            delivered_products = [idx for idx in delivered_products if len(idx) != 0]

            projects_dict[idx] = Project(
                name=name, cost=int(cost), ID=idx, delivered_products=delivered_products, start_datum=0,
                purchased_on=None
            )
    return projects_dict


def load_resources(path):
    resources_dict = dict()
    with open(path) as f:
        content = f.read().splitlines()
        for line in content:
            line_content = line.split(";")
            idx, name, cost, monthly_salary = line_content[0:4]
            developed_products = line_content[4:]
            developed_products = [idx for idx in developed_products if len(idx) != 0]

            resources_dict[idx] = Resource(
                name=name, cost=int(cost), ID=idx, developed_products=developed_products,
                monthly_salary=int(monthly_salary), purchased_on=None
            )
    return resources_dict


def load_events(path):
    events_dict = dict()
    with open(path) as f:
        content = f.read().splitlines()
        for line in content:
            line_content = line.split(";")
            idx, trimester, description = line_content[0:3]
            trimester = int(trimester[-1])  #In data writen as "Q1"
            required_efficiencies = line_content[3:6]
            result_success = line_content[6:8] or (0, 0)
            result_success = tuple(map(lambda x: int(x), result_success))
            result_failure = line_content[8:10] or (0, 0)
            result_failure = tuple(map(lambda x: -int(x), result_failure))

            events_dict[idx] = Event(
                description=description, appear_first_in_trimester=trimester, ID=idx,
                required_efficiencies=required_efficiencies,
                result_success=result_success, result_failure=result_failure, level=0
            )
    return events_dict


def load_legacy(path):
    legacy_list = []
    with open(path) as f:
        content = f.read().splitlines()
        for line in content:
            legacy_list.append(line.split(";"))
    return legacy_list
