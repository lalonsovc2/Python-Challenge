import random
from .player import Player
from .data_loader import load_products, load_projects, load_resources, load_efficiencies, load_events, load_legacy
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
        self.RESOURCES = None
        self.EFFICIENCIES = None
        self.EVENTS = None
        self.LEGACY = None
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
            for line in content[1:]:  # Skip day of the month
                board.append(line.split(";")[1:])  # Skip month name
        return np.array(board, dtype=int)

    def cargar_tablero(self):
        events = self.EVENTS  # Asumimos que los eventos ya están cargados
        visible_days = self.board[0]  # Suponiendo que el primer día de la semana se usa para visibilidad

        # Ajustamos la lógica para asegurarnos de que solo los días visibles estén presentes
        events_for_current_month = []
        for i, day in enumerate(visible_days):
            if day != 0:  # Si la casilla está visible
                event = events.get(str(day), None)  # Obtener el evento correspondiente al día
                if event:
                    events_for_current_month.append(event)

        return {
            "month": player.month,
            "visible_days": visible_days,  # Pasamos los días visibles
            "player_position": player.actual_date,
            "events": events_for_current_month  # Pasamos los eventos correspondientes
        }


class Game:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.board = self.load_board()
        self.current_month = 0  # Comienza en enero
        self.current_half = 0  # Primera mitad del mes

    def load_board(self):
        """
        Carga el tablero desde el archivo CSV y organiza los datos por meses y días.
        Devuelve un diccionario donde cada clave es un mes, con los valores divididos en mitades.
        """
        board_path = self.data_dir.joinpath("board.csv")
        board = {}
        with open(board_path) as f:
            content = f.read().splitlines()
            header = content[0].split(";")[1:]  # Ignorar el primer campo (nombre del mes)
            for line in content[1:]:
                row = line.split(";")
                month = row[0]  # Nombre del mes
                days = [int(cell) if cell != "" else 0 for cell in row[1:]]
                board[month] = {
                    "first_half": days[:15],
                    "second_half": days[15:]
                }
        return board

    def get_current_board(self):
        """
        Devuelve la mitad del tablero correspondiente al mes y mitad actuales.
        """
        months = list(self.board.keys())
        month_name = months[self.current_month]
        return self.board[month_name]["first_half" if self.current_half == 0 else "second_half"]

    def switch_half(self):
        """
        Cambia entre la primera y segunda mitad del mes.
        """
        self.current_half = 1 - self.current_half

    def switch_month(self, increment=1):
        """
        Cambia el mes actual. Incrementa o decrementa en base al parámetro.
        """
        self.current_month = (self.current_month + increment) % len(self.board)
        self.current_half = 0  # Reinicia a la primera mitad del mes





context = Context(DATA_DIR)
player = Player(context=context, initial_budget=1000000)
random.seed(0)
np.random.seed(0)

# Funciones para interactuar con Flask y controlar el juego

def iniciar_juego():
    player.first_turn_in_month = True  # El jugador comienza el primer turno
    return {"message": "Juego iniciado", "initial_budget": player.budget}

def comprar(purchase_type, item_id):
    if purchase_type == 'product':
        player.buy_product(item_id)
    elif purchase_type == 'project':
        player.buy_project(item_id)
    elif purchase_type == 'resource':
        player.hire_resource(item_id)
    
    return {"message": f"{purchase_type} comprado exitosamente"}

def lanzar_dados():
    dices, steps = player.throw_dices(5)
    player.actual_date += steps
    field = context.board.reshape(-1)[player.actual_date]
    return {"message": f"Lanzaste los dados: {dices}. Moviendo {steps} pasos. Casilla: {field}"}

def enfrentar_evento():
    current_trimester = np.ceil(player.month / 3)
    possible_events = [
        event_id for event_id, event in context.EVENTS.items() if event.appear_first_in_trimester <= current_trimester
    ]
    random_event_id = random.choice(possible_events)
    event = deepcopy(context.EVENTS.get(random_event_id))
    
    dices, risk_level = player.throw_dices(5)
    event.level = risk_level
    required_efficiencies_ids = event.required_efficiencies
    required_efficiencies = itemgetter(*required_efficiencies_ids)(player.efficiencies)
    max_efficiencies_point = max([eff.points for eff in required_efficiencies])

    if max_efficiencies_point >= event.level:
        player.apply_challenge_result(event.result_success)
        return {"message": f"Evento completado con éxito: {event.description}", "score": player.score, "budget": player.budget}
    else:
        player.apply_challenge_result(event.result_failure)
        return {"message": f"Evento fallido: {event.description}", "score": player.score, "budget": player.budget}

# Flujo del juego - Parte del ciclo principal (este código debe ser llamado desde el servidor Flask)
def juego_ciclo():
    if player.first_turn_in_month:
        # El jugador puede comprar cosas en su primer turno del mes
        wanna_buy = True
        while wanna_buy:
            # Reemplazamos las interacciones por llamadas HTTP
            # Aquí es donde se pueden hacer peticiones a Flask para comprar productos, proyectos, o recursos
            # En lugar de `input()`, usaríamos rutas de Flask, por ejemplo: requests.post('/comprar', json={...})
            wanna_buy = False  # Para que no quede en bucle

    player.first_turn_in_month = False

    player.display_efficiencies()

    # Lanzar los dados (interacción)
    lanzar_dados()  # Aquí llamamos la función que mueve al jugador

    # Verificar si hay un nuevo mes
    old_month = player.month
    if old_month < player.month:
        player.first_turn_in_month = True
        player.pay_salaries()
        player.get_products_from_projects()
        player.get_products_from_resources()

    # Verificar si es fin de semana
    if player.actual_date % 7 in [6, 0]:
        return {"message": "Es fin de semana, no se puede tomar ningún desafío."}

    # Enfrentar evento (interacción)
    enfrentar_evento()
    return {"message": "Ciclo de juego completado"}
