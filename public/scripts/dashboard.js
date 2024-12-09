// Función para cerrar los elementos de hover
function closeHover(hoverId) {
    const hoverElement = document.getElementById(hoverId);
    hoverElement.style.display = 'none';
}

// Función para iniciar el juego
function startGame() {
    // Redirigir a la página de juego
    window.location.href = 'crear-sala.html';
}

// Aquí podrías obtener el personaje seleccionado de localStorage o del servidor
document.addEventListener('DOMContentLoaded', () => {
    const selectedCharacter = JSON.parse(localStorage.getItem('selectedCharacter')); // Suponiendo que lo guardas en localStorage
    if (selectedCharacter) {
        document.getElementById('selectedCharacterImage').src = selectedCharacter.imageb; // Cambia la ruta de la imagen  
        document.getElementById('characterName').textContent = selectedCharacter.name;
        document.getElementById('level').textContent = `Nivel: ${selectedCharacter.level}`;
        document.getElementById('trophies').textContent = `Copas: ${selectedCharacter.trophies}`;
    }
});

function cerrarSesion() {
    // Eliminar los datos del usuario del localStorage
    localStorage.removeItem('user');

    // Redirigir al usuario a la página de inicio de sesión
    window.location.href = '/login.html'; // Cambia la URL a donde quieras redirigir
}
