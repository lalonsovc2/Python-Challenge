const socket = io('http://localhost:3000'); // Ajusta según el puerto
const user = JSON.parse(localStorage.getItem('user'));
if (!user) window.location.href = '/login.html';

const roomUsersDiv = document.getElementById('roomUsers');
const roomIdInput = document.getElementById('roomIdInput');
const currentRoomId = document.getElementById('currentRoomId');
const userCount = document.getElementById('userCount');
const closeRoomButton = document.getElementById('closeRoom');
const startGameButton = document.getElementById('startGame');
const roomInfo = document.getElementById('roomInfo');
const joinRoomHover = document.getElementById('joinRoomHover');
const submitRoomIdButton = document.getElementById('submitRoomId');

// Mostrar hover para unirse a sala
document.getElementById('joinRoom').addEventListener('click', () => {
    joinRoomHover.style.display = 'block';  // Mostrar el hover para ingresar ID de sala
});

// Crear sala
document.getElementById('createRoom').addEventListener('click', () => {
    socket.emit('createRoom', { user });
    roomInfo.style.display = 'block';  // Mostrar la info de la sala
    joinRoomHover.style.display = 'none';  // Ocultar hover de unirse
});

// Unirse a sala con ID ingresada
submitRoomIdButton.addEventListener('click', () => {
    const roomId = roomIdInput.value.trim();
    if (roomId) {
        socket.emit('joinRoom', { roomId, user });
        roomInfo.style.display = 'block';  // Mostrar la info de la sala
        joinRoomHover.style.display = 'none';  // Ocultar hover de unirse
    }
});

// Cerrar sala
closeRoomButton.addEventListener('click', () => {
    const roomId = currentRoomId.textContent;
    if (roomId !== '-') socket.emit('closeRoom', roomId);
});

// Iniciar juego
startGameButton.addEventListener('click', () => {
    const roomId = currentRoomId.textContent;
    if (roomId !== '-') socket.emit('startGame', roomId);
});

/// Mostrar la sala centrada y destacada
socket.on('roomUpdate', (room) => {
    const roomInfo = document.getElementById('roomInfo');
    currentRoomId.textContent = room.id;
    userCount.textContent = room.users.length;

    // Actualizar usuarios en la sala
    roomUsersDiv.innerHTML = room.users.map(u =>
        `<div class="user-slot">
            <img src="${u.user.personaje ? `/images/personaje${u.user.personaje}.png` : '/images/default.png'}" alt="${u.user.username}">
            <p>${u.user.username}</p>
        </div>`).join('');

    // Mostrar sala destacada
    roomInfo.style.display = 'block';

    // Ocultar botones si no es el creador
    if (room.creatorId !== socket.id) {
        closeRoomButton.style.display = 'none';
        startGameButton.style.display = 'none';
    } else {
        closeRoomButton.style.display = 'inline-block';
        startGameButton.style.display = 'inline-block';
    }
});

// Notificar cierre de sala
socket.on('roomClosed', () => {
    alert('La sala ha sido cerrada.');
    currentRoomId.textContent = '-';
    userCount.textContent = '0';
    roomUsersDiv.innerHTML = '';
    roomInfo.style.display = 'none';  // Ocultar la info de la sala
});

// Redirigir al tablero
socket.on('gameStarted', () => {
    window.location.href = '/tablero.html';
});


socket.on('joinRoomError', (message) => {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message || 'La ID de la sala no es correcta o la sala está llena.';
    errorMessage.style.display = 'block';

    // Ocultar el mensaje después de 3 segundos
    setTimeout(() => {
        errorMessage.style.display = 'none';
        roomIdInput.value = ''; // Limpiar el campo de texto para intentarlo de nuevo
    }, 3000);
});