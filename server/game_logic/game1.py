import random

from player import Player
from data_loader import load_products, load_projects, load_resources, load_efficiencies, load_events, load_legacy
from pathlib import Path
import numpy as np
import math
from copy import deepcopy
from operator import itemgetter
import logging
logging.basicConfig(level=logging.INFO)

DATA_DIR = Path().parent.resolve().parent.resolve().joinpath("data")


class Context:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.PRODUCTS = None
        self.PROJECTS = None
        self. RESOURCES = None
        self. EFFICIENCIES = None
        self.EVENTS = None
        self. LEGACY = None
        self.load_data()
        self.board = self.load_bord()

    def load_data(self):
        data_dir = self.data_dir
        products_path = data_dir.joinpath("products.csv")
        projects_path = data_dir.joinpath("projects.csv")
        resources_path = data_dir.joinpath("resources.csv")
        efficiencies_path = data_dir.joinpath("efficiencies.csv")
        events_path = data_dir.joinpath("events.csv")
        legacy_path = data_dir.joinpath("legacy.csv")

        self.PRODUCTS = load_products(products_path)
        self.PROJECTS = load_projects(projects_path)
        self.RESOURCES = load_resources(resources_path)
        self.EFFICIENCIES = load_efficiencies(efficiencies_path)
        self.EVENTS = load_events(events_path)
        self.LEGACY = load_legacy(legacy_path)

    def load_bord(self):
        board_path = self.data_dir.joinpath("board.csv")
        board = []
        with open(board_path) as f:
            content = f.read().splitlines()
            for line in content[1:]: # skip day of month
                board.append(line.split(";")[1:])  # skip month name
        return np.array(board, dtype=int)


context = Context(DATA_DIR)
player = Player(context=context, initial_budget=1000000)
random.seed(0)
np.random.seed(0)

while player.month <= 13:

    if player.first_turn_in_month:

    #----- buy ------
        print("You are on the first turn of the month. You can buy the modifiers you like")
        wanna_buy = True
        while wanna_buy:
            purchase = input("What would you like to buy? (product, project, resource, nothing)")
            purchase = purchase.lower()
            if purchase == "nothing":
                wanna_buy = False
            elif purchase == "product":
                product_id = input("Which product would you like to buy?")
                # TODO make this dummy proof (only integers are allowed)
                player.buy_product(str(product_id))
            elif purchase == "project":
                project_id = input("Which project would you like to buy?")
                player.buy_project(str(project_id))
            elif purchase == "resource":
                resource_id = input("Which resource would you like to hire?")
                player.hire_resource(str(resource_id))
            else:
                print("Please select product, project, resource or nothing")
                continue
    else:
        print("You are not in the first turn of the month. You can't buy anything but you have to face challenges")

    player.first_turn_in_month = False

    player.display_efficiencies()
    # throw dice and move
    throw = input(f"Ready to throw the dices? Click anything")
    old_month = player.month
    dices, steps = player.throw_dices(5)
    player.actual_date += steps
    field = context.board.reshape(-1)[player.actual_date]
    print(f"You threw the dices: {dices}, moving forward {steps} steps.")
    print(f"You are actually on {player.actual_date % 30}-{player.month} and "
          f"have to throw {field} dices to get the level risk of your event")

    # check if a new month has begun
    if old_month < player.month:
        player.first_turn_in_month = True
        player.pay_salaries()
        player.get_products_from_projects()
        player.get_products_from_resources()
        print(f"A new month has begun. You have paid {player.salaries_to_pay} dollars on salaries")

    # check if saturday or sunday
    if player.actual_date % 7 in [6, 0]:
        print("Today is weekend, it is not allowed to take any challenges")
        continue

    # take random event
    current_trimester = np.ceil(player.month / 3)
    possible_events = [
        event_id for event_id, event in context.EVENTS.items() if event.appear_first_in_trimester <= current_trimester
    ]
    random_event_id = random.choice(possible_events)
    event = deepcopy(context.EVENTS.get(random_event_id))
    take_event = input(f"Press a key to get a random event")
    print("Taking random event")
    print(event.description)

    throw = input(f"Ready to know which level of risk your event has? Press any key")
    dices, risk_level = player.throw_dices(field)
    print(f"you threw the dices: {dices} ")
    event.level = risk_level
    print(f"With risk level of {event.level}")

    # Evaluate if won or loose challenge
    required_efficiencies_ids = event.required_efficiencies
    required_efficiencies = itemgetter(*required_efficiencies_ids)(player.efficiencies)
    max_efficiencies_point = max([eff.points for eff in required_efficiencies])

    print(f"You can manage this event with following efficiencies and your points on them")
    for efficiency in required_efficiencies:
        print(f"{efficiency.name}: {efficiency.points}")

    if max_efficiencies_point >= event.level:
        print(f"Congrats! You have managed this event successfully "
              f"winning {event.result_success[0]} points and {event.result_success[1]} dollars.")
        player.apply_challenge_result(event.result_success)
    else:
        print(f"Ups! Your efficiencies weren`t sufficient for this event. "
              f"You have lost {event.result_failure[0]} points and {event.result_failure[1]} dollars.")
        player.apply_challenge_result(event.result_failure)

    print(f"Your actual score is: {player.score} and budget is {player.budget}")


