// Elements
const loginBtn = document.getElementById('loginBtn');
const loginModal = document.getElementById('loginModal');
const usernameModal = document.getElementById('usernameModal');
const loginForm = document.getElementById('loginForm');
const usernameForm = document.getElementById('usernameForm');
const closeLoginModal = document.getElementById('closeLoginModal');
const closeUsernameModal = document.getElementById('closeUsernameModal');

// Show Login Modal
loginBtn.addEventListener('click', () => {
    loginModal.classList.remove('hidden');
});

// Close Login Modal
closeLoginModal.addEventListener('click', () => {
    loginModal.classList.add('hidden');
});


document.addEventListener('DOMContentLoaded', () => {
    const user = localStorage.getItem('user');
    if (user) {
        // Si el usuario está logueado, redirigimos o mostramos la selección de personajes
        window.location.href = '/character-selection.html'; // Ruta hacia la página de selección de personajes
    }
});

// Login Modal - Verificar si las credenciales coinciden y guardarlas en localStorage
// Login Modal - Verificar si las credenciales coinciden y guardarlas en localStorage
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    fetch('http://localhost:3000/getData')
        .then(response => response.json())
        .then(users => {
            const user = users.find(user => user.email === email && user.password === password);

            if (user) {
                // Si el usuario existe, guardamos los datos en localStorage
                let userData = {
                    ...user,
                    personaje: user.personaje || null // Aseguramos que el personaje esté en el objeto, aunque sea null
                };

                // Guardar el usuario con el personaje (o null) en el localStorage
                localStorage.setItem('user', JSON.stringify(userData));

                if (user.username) {
                    alert(`¡Bienvenido de nuevo, ${user.username}!`);
                    window.location.href = '/dashboard.html'; // Redirige al panel principal
                } else {
                    // Si el usuario no tiene un nombre de usuario, mostramos el modal para ingresar el nombre
                    loginModal.classList.add('hidden');
                    usernameModal.classList.remove('hidden');
                }

                // Enviar los datos al servidor si el personaje aún no está asignado
                if (!user.personaje) {
                    fetch('http://localhost:3000/save-character', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            email: user.email,
                            personaje: null // Enviamos null por ahora, ya que el personaje no está asignado
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Personaje inicial guardado en el servidor', data);
                    })
                    .catch(error => {
                        console.error('Error al guardar el personaje en el servidor:', error);
                    });
                }
            } else {
                alert('Credenciales incorrectas.');
            }
        })
        .catch(error => alert('Error al obtener los datos: ' + error));
});


// Close Username Modal
closeUsernameModal.addEventListener('click', () => {
    usernameModal.classList.add('hidden');
});


// Manejar el envío del nombre de usuario
usernameForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('loginEmail').value; // Obtener el email ingresado

    try {
        // Enviar el nombre de usuario junto con el correo al servidor
        const response = await fetch('http://localhost:3000/save-username', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email, username: username })
        });

        if (response.ok) {
            // Obtener el usuario actualizado desde el servidor
            let updatedUser;
            try {
                updatedUser = await response.json(); // Intenta convertir la respuesta a JSON
            } catch (error) {
                alert('Error al procesar la respuesta del servidor. Por favor, revisa el backend.');
                console.error('Respuesta del servidor:', await response.text()); // Muestra la respuesta en texto plano
                return;
            }
            

            // Actualizar el localStorage con los datos del usuario actualizado
            localStorage.setItem('user', JSON.stringify(updatedUser));

            
            usernameModal.classList.add('hidden');
            window.location.href = '/character-selection.html'; // Cambia según tu ruta
        } else {
            alert('Hubo un error al guardar el nombre de usuario.');
        }
    } catch (error) {
        alert('Error al comunicarse con el servidor: ' + error.message);
    }
});


