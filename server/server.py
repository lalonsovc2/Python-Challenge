from pathlib import Path
import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
import time
import json
import os
from datetime import datetime
from game_logic.data_loader import load_efficiencies, load_products, load_projects, load_resources, load_events, load_legacy
from game_logic.efficiency import Efficiency
from game_logic.modifiers import Product, Project, Resource
from game_logic.event import Event
from game_logic.player import Player
from game_logic.game import context, player, lanzar_dados
import numpy as np
from copy import deepcopy
from operator import itemgetter
import random
from livereload import Server


# Configuración inicial
app = Flask(__name__, static_folder='../public')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


# Ruta del archivo JSON
DATA_FILE = "data.json"

# Función para cargar los datos desde el archivo JSON
# Función para limpiar textos mal codificados
def clean_text(text):
    try:
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

# Función para limpiar datos (dict o list)
def clean_data(data):
    if isinstance(data, dict):
        return {clean_text(k): clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, str):
        return clean_text(data)
    else:
        return data

# Cargar datos
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print("Datos cargados (sin limpiar):", data)
        return clean_data(data)  # Limpia los datos al cargarlos

def save_data(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



# Ruta para guardar datos en el archivo JSON
@app.route('/saveData', methods=['POST'])
def save_data_route():
    data = request.json
    new_id = int(datetime.now().timestamp())
    data.update({'id': new_id, 'username': ''})

    users = load_data()
    users.append(data)
    save_data(users)

    return jsonify(message="Datos guardados correctamente.")

# Ruta para guardar el nombre de usuario
@app.route('/save-username', methods=['POST'])
def save_username():
    data = request.json
    email = data.get('email')
    username = data.get('username')

    users = load_data()
    user = next((u for u in users if u['email'] == email), None)
    if user:
        user['username'] = username
        save_data(users)
        return jsonify(message="Nombre de usuario guardado correctamente.", user=user)
    return jsonify(error="Usuario no encontrado."), 404

# Ruta para verificar si el usuario ya tiene un nombre de usuario
@app.route('/check-username', methods=['POST'])
def check_username():
    email = request.json.get('email')

    users = load_data()
    user = next((u for u in users if u['email'] == email), None)
    if user and user.get('username'):
        return jsonify(username=user['username'])
    return jsonify(username=None)

@app.route('/get-user-state', methods=['POST'])
def get_user_state():
    data = request.json
    email = data.get('email')

    # Depuración: Imprimir el email recibido
    print(f"Email recibido: {email}")

    # Cargar los datos del archivo
    users = load_data()  # Cargar usuarios desde el archivo JSON
    user = next((u for u in users if u['email'].lower() == email.lower()), None)


    if user:
        return jsonify({
            "budget": user.get("budget", 1000),  # Presupuesto por defecto si no existe
            "productos_comprados": user.get("productos_comprados", []),
            "proyectos_comprados": user.get("proyectos_comprados", []),
            "recursos_comprados": user.get("recursos_comprados", [])
        })
    print(f"Usuario no encontrado para el email: {email}")
    return jsonify({"error": "Usuario no encontrado."}), 404



@app.route('/update-user-state', methods=['POST'])
def update_user_state():
    data = request.json
    email = data.get('email')
    new_budget = data.get('budget')
    purchased_item = data.get('purchased_item')
    category = data.get('category')  # 'productos', 'proyectos', 'recursos'

    # Cargar los datos actuales desde el archivo JSON
    users = load_data()  # Asegura que carga en UTF-8
    user = next((u for u in users if u['email'] == email), None)

    if user:
        # Actualizar el presupuesto del usuario
        user['budget'] = new_budget

        # Agregar el ítem comprado a la lista correspondiente
        if category == 'productos':
            user.setdefault('productos_comprados', [])
            if purchased_item not in user['productos_comprados']:
                user['productos_comprados'].append(purchased_item)
        elif category == 'proyectos':
            user.setdefault('proyectos_comprados', [])
            if purchased_item not in user['proyectos_comprados']:
                user['proyectos_comprados'].append(purchased_item)
        elif category == 'recursos':
            user.setdefault('recursos_comprados', [])
            if purchased_item not in user['recursos_comprados']:
                user['recursos_comprados'].append(purchased_item)

        # Inicializar eficiencias con valor 0 si no existen
        user.setdefault('eficiencias', {})
        for efficiency_id, efficiency in efficiencies.items():
            efficiency_name = clean_text(efficiency.name)  # Limpieza del nombre de la eficiencia
            user['eficiencias'].setdefault(efficiency_name, 0)

        # Determinar la ganancia de puntos de eficiencia
        puntos_a_sumar = 3  # Por defecto, sumar 3 puntos si no se cumplen los requisitos
        product_data = products.get(purchased_item)

        if product_data:
            requirements = getattr(product_data, 'requirements', [])
            print(f"Requisitos del producto {purchased_item}: {requirements}")
            # Verificar si todos los requisitos se cumplen
            requisitos_cumplidos = all(req in user['productos_comprados'] for req in requirements)
            if requisitos_cumplidos:
                puntos_a_sumar = 6

        # Actualizar las eficiencias correspondientes
        for efficiency_id, efficiency in efficiencies.items():
            # Verificar si el producto comprado es un modificador de la eficiencia
            if purchased_item in efficiency.modifiable_by_products:
                efficiency_name = clean_text(efficiency.name)

                # Debug: Mostrar el proceso de ganancia de puntos
                print(f"Actualizando eficiencia '{efficiency_name}' con {puntos_a_sumar} puntos")

                # Aumentar los puntos en la eficiencia correspondiente del usuario
                user['eficiencias'][efficiency_name] += puntos_a_sumar

        # Guardar los cambios en el archivo JSON
        save_data(clean_data(users))  # Limpia datos antes de guardar

        return jsonify({"message": "Estado del usuario actualizado correctamente."})

    return jsonify({"error": "Usuario no encontrado."}), 404




# Ruta para guardar el personaje seleccionado por el usuario
@app.route('/save-character', methods=['POST'])
def save_character():
    data = request.json
    email = data.get('email')
    personaje = data.get('personaje')

    users = load_data()
    user = next((u for u in users if u['email'] == email), None)
    if user:
        user['personaje'] = personaje
        save_data(users)
        return jsonify(user)
    return jsonify(error="Usuario no encontrado."), 404

# Ruta para obtener todos los datos
@app.route('/getData', methods=['GET'])
def get_data():
    users = load_data()
    return jsonify(users)


#
# Configuración de WebSocket para gestión de salas
rooms = {}

@socketio.on('createRoom')
def create_room(data):
    print("Evento recibido: createRoom", data)
    user = data.get('user')
    room_id = f"room-{int(time.time())}"
    rooms[room_id] = {"id": room_id, "creatorId": request.sid, "users": [{"id": request.sid, "user": user}]}
    join_room(room_id)
    emit('roomUpdate', rooms[room_id], room=room_id)



@socketio.on('joinRoom')
def join_room_event(data):
    room_id = data.get('roomId')
    user_email = data.get('user').get('email')

    # Cargar datos de `data.json`
    with open('data.json', 'r') as file:
        users = json.load(file)

    # Buscar al usuario actual en los datos
    user = next((u for u in users if u['email'] == user_email), None)

    if user and room_id in rooms:
        # Agregar el usuario a la sala
        rooms[room_id]['users'].append({
            "username": user["username"],
            "personaje": user.get("personaje", None)  # Puede no tener personaje
        })
        join_room(room_id)

        # Emitir lista actualizada de jugadores
        emit('updatePlayers', rooms[room_id]['users'], room=room_id)
    else:
        emit('error', 'Usuario no encontrado o sala no existe.', to=request.sid)

@socketio.on('leaveRoom')
def leave_room_event(data):
    room_id = data.get('roomId')
    if room_id in rooms:
        rooms[room_id]['users'] = [u for u in rooms[room_id]['users'] if u['id'] != request.sid]
        if not rooms[room_id]['users']:
            del rooms[room_id]
        else:
            emit('roomUpdate', rooms[room_id], room=room_id)
        leave_room(room_id)

@socketio.on('startGame')
def start_game(data):
    room_id = data.get('roomId')

    if room_id in rooms:
        # Redirigir a todos al tablero
        emit('redirectToBoard', {'roomId': room_id}, room=room_id)

        # Emitir lista de jugadores al tablero
        emit('updatePlayers', rooms[room_id]['users'], room=room_id)
    else:
        emit('error', {'message': 'Sala no encontrada.'}, to=request.sid)



@app.route('/cargar-datos')
def cargar_datos():
    # Rutas de los archivos CSV (ajusta estas rutas según tu estructura de directorios)
    efficiencies_path = 'data/efficiencies.csv'
    products_path = 'data/products.csv'
    projects_path = 'data/projects.csv'
    resources_path = 'data/resources.csv'
    events_path = 'data/events.csv'
    legacy_path = 'data/legacy.csv'

    # Cargar los datos utilizando las funciones definidas en data_loader.py
    efficiencies = load_efficiencies(efficiencies_path)
    products = load_products(products_path)
    projects = load_projects(projects_path)
    resources = load_resources(resources_path)
    events = load_events(events_path)
    legacy = load_legacy(legacy_path)

    # Retornamos un resumen de los datos cargados (puedes modificar esto según tus necesidades)
    return jsonify({
        "efficiencies": list(efficiencies.keys()),  # Solo devolvemos las claves como ejemplo
        "products": list(products.keys()),
        "projects": list(projects.keys()),
        "resources": list(resources.keys()),
        "events": list(events.keys()),
        "legacy": legacy[:5]  # Mostramos solo los primeros 5 para evitar grandes respuestas
    })


# Cargar los datos de eficiencias y otros elementos (productos, proyectos, recursos)
efficiencies = load_efficiencies('data/efficiencies.csv')
products = load_products('data/products.csv')
projects = load_projects('data/projects.csv')
resources = load_resources('data/resources.csv')
events = load_events('data/events.csv')




@app.route('/productos', methods=['GET'])
def obtener_productos():
    productos_resumen = [
        {
            "ID": product.ID,
            "name": product.name,
            "cost": product.cost,
            "requirements": product.requirements,
            "purchased_on": product.purchased_on
        }
        for product in products.values()
    ]
    return jsonify(productos_resumen)

@app.route('/proyectos', methods=['GET'])
def obtener_proyectos():
    proyectos_resumen = [
        {
            "ID": project.ID,
            "name": project.name,
            "cost": project.cost,
            "delivered_products": project.delivered_products,
            "start_datum": project.start_datum,
            "project_length": project.project_length
        }
        for project in projects.values()
    ]
    return jsonify(proyectos_resumen)

@app.route('/recursos', methods=['GET'])
def obtener_recursos():
    recursos_resumen = [
        {
            "ID": resource.ID,
            "name": resource.name,
            "cost": resource.cost,
            "monthly_salary": resource.monthly_salary,
            "developed_products": resource.developed_products,
            "purchased_on": resource.purchased_on
        }
        for resource in resources.values()
    ]
    return jsonify(recursos_resumen)

@app.route('/proyecto/terminado', methods=['POST'])
def verificar_terminacion_proyecto():
    data = request.get_json()
    project_id = data.get('project_id')
    actual_month = data.get('actual_month')

    project = projects.get(project_id)
    if not project:
        return jsonify({"error": "Proyecto no encontrado"}), 404
    
    # Verificar si el proyecto ha terminado
    is_finished = project.is_finished(actual_month)
    return jsonify({
        "project_id": project.ID,
        "is_finished": is_finished
    })






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

context = Context(DATA_DIR)
player = Player(context=context, initial_budget=1000000)
random.seed(0)
np.random.seed(0)

@app.route('/crear_jugador', methods=['POST'])
def crear_jugador():
    data = request.get_json()  # Obtener datos del cuerpo de la solicitud
    initial_budget = data.get('initial_budget', 1000)  # Presupuesto inicial, por defecto es 1000
    player = Player(context=context, initial_budget=initial_budget)  # Crear el jugador
    return jsonify({
        'message': 'Jugador creado con éxito',
        'initial_budget': initial_budget
    })

# Datos del jugador
player = {
    "budget": 100000,
    "score": 0,
    "position": 0
}

@app.route('/comprar_producto', methods=['POST'])
def comprar_producto():
    data = request.get_json()
    product_id = data.get('product_id')
    player.buy_product(product_id)
    return jsonify({'message': f'Producto {product_id} comprado exitosamente'})

@app.route('/comprar_proyecto', methods=['POST'])
def comprar_proyecto():
    data = request.get_json()
    project_id = data.get('project_id')
    player.buy_project(project_id)
    return jsonify({'message': f'Proyecto {project_id} comprado exitosamente'})

@app.route('/contratar_recurso', methods=['POST'])
def contratar_recurso():
    data = request.get_json()
    resource_id = data.get('resource_id')
    player.hire_resource(resource_id)
    return jsonify({'message': f'Recurso {resource_id} contratado exitosamente'})

@app.route('/ver_efficiencias', methods=['GET'])
def ver_efficiencias():
    if not hasattr(player, 'efficiencies') or not player.efficiencies:
        return jsonify({"error": "No se encontraron eficiencias"}), 404
    
    efficiencies = {
        efficiency.name: efficiency.points for efficiency in player.efficiencies.values()
    }
    return jsonify(efficiencies)





@app.route('/iniciar_juego', methods=['POST'])
def iniciar_juego():
    player.first_turn_in_month = True  # El jugador comienza el primer turno
    return jsonify({'message': 'Juego iniciado', 'initial_budget': player.budget})

@app.route('/comprar', methods=['POST'])
def comprar():
    data = request.get_json()
    purchase_type = data.get('purchase_type')  # Tipo de compra: "product", "project", "resource"
    item_id = data.get('item_id')

    # Verificar el presupuesto del jugador
    if player.budget <= 0:
        return jsonify({'error': 'No tienes suficiente presupuesto.'}), 400

    # Identificar el tipo de ítem y validar si está disponible
    if purchase_type == 'product':
        item = context.PRODUCTS.get(item_id)
    elif purchase_type == 'project':
        item = context.PROJECTS.get(item_id)
    elif purchase_type == 'resource':
        item = context.RESOURCES.get(item_id)
    else:
        return jsonify({'error': 'Tipo de compra inválido.'}), 400

    if not item:
        return jsonify({'error': f'{purchase_type.capitalize()} no encontrado.'}), 404

    # Verificar si el ítem ya fue comprado
    if getattr(item, 'purchased_on', 0) > 0:
        return jsonify({'error': f'Este {purchase_type} ya ha sido adquirido.'}), 400

    # Verificar si el jugador tiene presupuesto suficiente
    if player.budget < item.cost:
        return jsonify({'error': 'No tienes suficiente presupuesto para este ítem.'}), 400

    # Procesar la compra
    player.budget -= item.cost
    item.purchased_on = 1  # Marcar como comprado

    # Retornar la respuesta de éxito
    return jsonify({
        'message': f'{purchase_type.capitalize()} comprado exitosamente.',
        'remaining_budget': player.budget,
        'item_id': item_id
    })





# Ruta para lanzar los dados
@app.route('/lanzar_dados', methods=['POST'])
def lanzar_dados():
    dices, steps = player.throw_dices(5)
    player.actual_date += steps
    field = context.board.reshape(-1)[player.actual_date]
    return {"message": f"Lanzaste los dados: {dices}. Moviendo {steps} pasos. Casilla: {field}"}



@app.route('/cargar_tablero', methods=['GET'])
def cargar_tablero_route():
    return jsonify(context.cargar_tablero())


@app.route('/juego_ciclo', methods=['POST'])
def juego_ciclo():
    return juego_ciclo()


@app.route('/routes', methods=['GET'])
def list_routes():
    return jsonify([str(rule) for rule in app.url_map.iter_rules()])




@app.route('/resolve_event', methods=['POST'])
def resolve_event():
    # Cargar datos del jugador
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Obtener datos del frontend
    player_id = request.json['player_id']
    event = request.json['event']  # Recibe el evento completo desde el frontend
    dice_rolls = request.json['dice_rolls']

    # Buscar jugador
    player = next((p for p in data if p['id'] == player_id), None)
    if not player:
        return jsonify({'error': 'Jugador no encontrado'}), 404

    if not event:
        return jsonify({'error': 'Evento no proporcionado'}), 400

    # Sumar dados
    event_efficiency = sum(dice_rolls)

    # Comparar con eficiencias del jugador
    player_efficiencies = player.get('eficiencias', {})
    efficiency_matched = next(
        (clean_text(name) for name, value in player_efficiencies.items() if value >= event_efficiency),
        None
    )

    # Actualizar resultados
    result = {}
    if efficiency_matched:
        # Ganó el evento
        player['budget'] += event['result_success']['money']
        player['points'] = player.get('points', 0) + event['result_success']['points']
        result['success'] = True
        result['efficiency'] = {
            'name': efficiency_matched,
            'value': player_efficiencies[efficiency_matched]
        }
        result['gains'] = event['result_success']
    else:
        # Perdió el evento
        player['budget'] += event['result_failure']['money']
        player['points'] = player.get('points', 0) + event['result_failure']['points']
        result['success'] = False
        result['losses'] = event['result_failure']

    # Guardar cambios en data.json
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(clean_data(data), file, indent=4, ensure_ascii=False)

    return jsonify(result)





@app.route('/penalize_event', methods=['POST'])
def penalize_event():
    # Cargar datos del jugador
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Obtener datos del frontend
    player_id = request.json['player_id']
    event = request.json['event']  # Recibe el evento completo desde el frontend

    # Buscar jugador
    player = next((p for p in data if p['id'] == player_id), None)
    if not player:
        return jsonify({'error': 'Jugador no encontrado'}), 404

    if not event:
        return jsonify({'error': 'Evento no proporcionado'}), 400

    # Aplicar penalización
    player['budget'] += event['result_failure']['money']
    player['points'] = player.get('points', 0) + event['result_failure']['points']

    # Guardar cambios
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(clean_data(data), file, indent=4, ensure_ascii=False)

    return jsonify({
        'success': False,
        'message': 'Has sido penalizado por no resolver el evento.',
        'losses': event['result_failure']
    })


@app.route('/get-eficiencias', methods=['POST'])
def get_eficiencias():
    # Cargar los datos del archivo JSON
    with open('data.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

    # Obtener el email del usuario desde la solicitud
    email = request.json.get('email')

    # Buscar el usuario por email
    user = next((u for u in users if u['email'] == email), None)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    # Retornar las eficiencias del usuario
    return jsonify(user['eficiencias'])



# Configura LiveReload para que use el puerto 35729 (puerto estándar de LiveReload)
def run_livereload():
    server = Server(app.wsgi_app)
    server.watch('../public/styles/*')  # Ruta para los archivos CSS
    server.watch('../public/*.html')   # Ruta para los archivos HTML
    server.serve(port=35730, host='0.0.0.0')  # Puerto para LiveReload

# Ejecuta ambos servicios en paralelo usando Eventlet en el mismo puerto
if __name__ == '__main__':
    eventlet.spawn(run_livereload)  # Ejecutar LiveReload en un hilo separado
    socketio.run(app, debug=True, host='0.0.0.0', port=3000)  # Ejecutar Sock