import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
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
socketio = SocketIO(app)
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

import os
import json

# Ruta del archivo JSON
DATA_FILE = "data.json"

# Función para cargar los datos desde el archivo JSON
def load_data():
    if not os.path.exists(DATA_FILE):  # Si el archivo no existe, devolver una lista vacía
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)  # Leer el archivo JSON y cargar los datos

# Función para guardar los datos en el archivo JSON
def save_data(data):
    print("Guardando los siguientes datos en data.json:", data)  # Ver los datos que se guardan
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# Ruta para servir la página principal
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

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
    category = data.get('category')  # 'producto', 'proyecto', 'recurso'

    # Cargar los datos actuales desde el archivo
    users = load_data()
    user = next((u for u in users if u['email'] == email), None)

    if user:
        # Actualizar el presupuesto
        user['budget'] = new_budget

        # Agregar el ítem comprado a la lista correspondiente
        if category == 'productos':
            if 'productos_comprados' not in user:
                user['productos_comprados'] = []  # Si no existe la lista, crearla
            if purchased_item not in user['productos_comprados']:
                user['productos_comprados'].append(purchased_item)  # Agregar el ítem
        elif category == 'proyectos':
            if 'proyectos_comprados' not in user:
                user['proyectos_comprados'] = []  # Si no existe la lista, crearla
            if purchased_item not in user['proyectos_comprados']:
                user['proyectos_comprados'].append(purchased_item)  # Agregar el ítem
        elif category == 'recursos':
            if 'recursos_comprados' not in user:
                user['recursos_comprados'] = []  # Si no existe la lista, crearla
            if purchased_item not in user['recursos_comprados']:
                user['recursos_comprados'].append(purchased_item)  # Agregar el ítem

        # Guardar los cambios en el archivo
        save_data(users)

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

# Datos de los personajes
personajes = {
    "1": {
        "right": ['assets/images/characters/personaje1-right1.png', 'assets/images/characters/personaje1-right2.png', 'assets/images/characters/personaje1-right3.png'],
        "up": ['assets/images/characters/personaje1-up1.png', 'assets/images/characters/personaje1-up2.png', 'assets/images/characters/personaje1-up3.png'],
        "down": ['assets/images/characters/personaje1-down1.png', 'assets/images/characters/personaje1-down2.png', 'assets/images/characters/personaje1-down3.png'],
        "idle": 'assets/images/characters/personaje1-idle.png'
    },
    # Resto de los personajes...
}

# Ruta para obtener los datos del personaje de un usuario
@app.route('/api/getUsuario', methods=['GET'])
def get_usuario():
    user_id = request.args.get('id')
    users = load_data()
    user = next((u for u in users if str(u['id']) == user_id), None)
    if user and 'personaje' in user:
        personaje_data = personajes.get(str(user['personaje']), {})
        return jsonify(personaje_data)
    return jsonify(error="Usuario no encontrado o sin personaje."), 404

# Configuración de Socket.IO
rooms = {}

@socketio.on('createRoom')
def create_room(data):
    user = data['user']
    room_id = f"room-{int(datetime.now().timestamp())}"
    rooms[room_id] = {"id": room_id, "creatorId": request.sid, "users": [{"id": request.sid, "user": user}]}
    join_room(room_id)
    emit('roomUpdate', rooms[room_id], room=room_id)

@socketio.on('joinRoom')
def join_room_event(data):
    room_id = data['roomId']
    user = data['user']
    if room_id in rooms and len(rooms[room_id]['users']) < 4:
        rooms[room_id]['users'].append({"id": request.sid, "user": user})
        join_room(room_id)
        emit('roomUpdate', rooms[room_id], room=room_id)
    else:
        emit('error', 'La sala no existe o está llena.')

@socketio.on('leaveRoom')
def leave_room_event(room_id):
    if room_id in rooms:
        rooms[room_id]['users'] = [u for u in rooms[room_id]['users'] if u['id'] != request.sid]
        if not rooms[room_id]['users']:
            del rooms[room_id]
        else:
            emit('roomUpdate', rooms[room_id], room=room_id)
        leave_room(room_id)

@socketio.on('startGame')
def start_game(room_id):
    if room_id in rooms and rooms[room_id]['creatorId'] == request.sid:
        emit('gameStarted', room=room_id)

@socketio.on('disconnect')
def disconnect():
    for room_id, room in list(rooms.items()):
        rooms[room_id]['users'] = [u for u in room['users'] if u['id'] != request.sid]
        if not rooms[room_id]['users']:
            del rooms[room_id]
        else:
            emit('roomUpdate', room, room=room_id)




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

@app.route('/eficiencia/<efficiency_id>', methods=['GET'])
def obtener_eficiencia(efficiency_id):
    efficiency = efficiencies.get(efficiency_id)
    if not efficiency:
        return jsonify({"error": "Eficiencia no encontrada"}), 404
    return jsonify({
        "name": efficiency.name,
        "ID": efficiency.ID,
        "points": efficiency.points,
        "modifiable_by_products": efficiency.modifiable_by_products,
        "modifiable_by_projects": efficiency.modifiable_by_projects,
        "modifiable_by_resources": efficiency.modifiable_by_resources,
    })

@app.route('/actualizar-eficiencia', methods=['POST'])
def actualizar_eficiencia():
    data = request.get_json()
    efficiency_id = data.get('efficiency_id')
    product_id = data.get('product_id')
    project_id = data.get('project_id')
    resource_id = data.get('resource_id')
    
    efficiency = efficiencies.get(efficiency_id)
    if not efficiency:
        return jsonify({"error": "Eficiencia no encontrada"}), 404
    
    if product_id:
        product = products.get(product_id)
        if product:
            efficiency.update_by_product(product, purchased_products=products)
    
    if project_id:
        project = projects.get(project_id)
        if project:
            efficiency.update_by_project(project)
    
    if resource_id:
        resource = resources.get(resource_id)
        if resource:
            efficiency.update_by_resource(resource)
    
    return jsonify({
        "efficiency_id": efficiency.ID,
        "updated_points": efficiency.points
    })



@app.route('/eventos', methods=['GET'])
def obtener_eventos():
    eventos_resumen = [
        {
            "ID": event.ID,
            "description": event.description,
            "appear_first_in_trimester": event.appear_first_in_trimester,
            "required_efficiencies": event.required_efficiencies,
            "result_success": event.result_success,
            "result_failure": event.result_failure,
            "level": event.level
        }
        for event in events.values()
    ]
    return jsonify(eventos_resumen)

@app.route('/evento/<event_id>', methods=['GET'])
def obtener_evento(event_id):
    event = events.get(event_id)
    if not event:
        return jsonify({"error": "Evento no encontrado"}), 404
    return jsonify({
        "ID": event.ID,
        "description": event.description,
        "appear_first_in_trimester": event.appear_first_in_trimester,
        "required_efficiencies": event.required_efficiencies,
        "result_success": event.result_success,
        "result_failure": event.result_failure,
        "level": event.level
    })

@app.route('/actualizar-evento', methods=['POST'])
def actualizar_evento():
    data = request.get_json()
    event_id = data.get('event_id')
    efficiency_ids = data.get('efficiency_ids', [])
    
    event = events.get(event_id)
    if not event:
        return jsonify({"error": "Evento no encontrado"}), 404

    # Verificar si se cumplen las eficiencias requeridas
    required_efficiencies_met = all(efficiency_id in efficiencies for efficiency_id in event.required_efficiencies)
    
    # Determinar el resultado
    if required_efficiencies_met:
        result = event.result_success
    else:
        result = event.result_failure

    return jsonify({
        "event_id": event.ID,
        "result": result
    })



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





class GameContext:
    def __init__(self):
        self.PRODUCTS = products
        self.PROJECTS = projects
        self.RESOURCES = resources
        self.EFFICIENCIES = {}
        self.LEGACY = []
        self.board = self.create_board()  # Inicializamos el board aquí

    def create_board(self):
        # Crear una lista representando el tablero
        return np.array([f"Casilla {i}" for i in range(100)])  # Convertir a numpy array desde el principio

    def get_board_as_array(self):
        # En este punto ya es un arreglo numpy, así que no es necesario usar reshape aquí
        return self.board.reshape(-1)  # Esto asegurará que sea un arreglo unidimensional


@app.route('/crear_jugador', methods=['POST'])
def crear_jugador():
    data = request.get_json()  # Obtener datos del cuerpo de la solicitud
    initial_budget = data.get('initial_budget', 1000)  # Presupuesto inicial, por defecto es 1000
    player = Player(context=context, initial_budget=initial_budget)  # Crear el jugador
    return jsonify({
        'message': 'Jugador creado con éxito',
        'initial_budget': initial_budget
    })


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




@app.route('/lanzar_dados', methods=['POST'])
def lanzar_dados():
    dices, steps = player.throw_dices(5)
    player.actual_date += steps

    # Asegúrate de que 'context.board' es un arreglo numpy antes de usar reshape
    if isinstance(context.board, list):
        context.board = np.array(context.board)  # Convertimos la lista a un numpy array

    # Ahora, puedes usar reshape sin problemas si es necesario
    field = context.board.reshape(-1)[player.actual_date]

    # Asegúrate de convertir los objetos numpy.int64 a int
    return jsonify({
        'message': f'Lanzaste los dados: {dices}. Moviendo {steps} pasos. Casilla: {field}',
        'steps': int(steps),  # Convertir a int
        'field': int(field)   # Convertir a int
    })
@app.route('/enfrentar_evento', methods=['POST'])
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
        return jsonify({'message': f'Evento completado con éxito: {event.description}', 'score': player.score, 'budget': player.budget})
    else:
        player.apply_challenge_result(event.result_failure)
        return jsonify({'message': f'Evento fallido: {event.description}', 'score': player.score, 'budget': player.budget})

@app.route('/routes', methods=['GET'])
def list_routes():
    return jsonify([str(rule) for rule in app.url_map.iter_rules()])


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