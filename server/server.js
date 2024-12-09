const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const app = express();

const http = require('http');
const { Server } = require('socket.io');

app.use(cors());
app.use(express.json()); // Para manejar solicitudes con cuerpo JSON
app.use(express.static(path.join(__dirname, '../public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'index.html'));
    });

// Ruta para guardar los datos en un archivo JSON
app.post('/saveData', (req, res) => {
    const { email, password } = req.body;

    // Le asignamos una ID única (simplemente incrementamos un contador)
    const newId = Date.now(); // Usamos el timestamp como ID único

    const data = {
        id: newId,  // Asignamos la ID generada
        email,
        password,
        username: '' // Inicializamos el nombre de usuario como vacío, ya que se añadirá más tarde
    };

    const filePath = path.join(__dirname, 'data.json');

    fs.readFile(filePath, 'utf8', (err, fileData) => {
        if (err) {
            return res.status(500).send('Error al leer el archivo.');
        }

        let jsonData = [];
        try {
            jsonData = JSON.parse(fileData || '[]');
        } catch (e) {
            return res.status(500).send('Error al procesar el archivo de datos.');
        }

        jsonData.push(data);

        fs.writeFile(filePath, JSON.stringify(jsonData, null, 2), (err) => {
            if (err) {
                return res.status(500).send('Error al guardar los datos.');
            }
            res.send('Datos guardados correctamente.');
        });
    });
});

// Ruta para guardar el username de un usuario
app.post('/save-username', (req, res) => {
    const { email, username } = req.body;

    const filePath = path.join(__dirname, 'data.json');

    fs.readFile(filePath, 'utf8', (err, fileData) => {
        if (err) {
            return res.status(500).send('Error al leer el archivo.');
        }

        let users = [];
        try {
            users = JSON.parse(fileData || '[]');
        } catch (e) {
            return res.status(500).send('Error al procesar el archivo de datos.');
        }

        const user = users.find(u => u.email === email);

        if (user) {
            user.username = username; // Asignar el nombre de usuario al usuario encontrado
            fs.writeFile(filePath, JSON.stringify(users, null, 2), 'utf8', (err) => {
                if (err) {
                    return res.status(500).send('Error al guardar el archivo.');
                }
                return res.json({ message: 'Nombre de usuario guardado correctamente.', user });
            });
        } else {
            return res.status(404).send('Usuario no encontrado.');
        }
    });
});

// Ruta para verificar si el usuario ya tiene un nombre de usuario
app.post('/check-username', (req, res) => {
    const { email } = req.body;

    const filePath = path.join(__dirname, 'data.json');

    fs.readFile(filePath, 'utf8', (err, fileData) => {
        if (err) {
            return res.status(500).send('Error al leer el archivo.');
        }

        let users = [];
        try {
            users = JSON.parse(fileData || '[]');
        } catch (e) {
            return res.status(500).send('Error al procesar el archivo de datos.');
        }

        const user = users.find(u => u.email === email);

        if (user && user.username) {
            return res.json({ username: user.username });
        } else {
            return res.json({ username: null });
        }
    });
});

// Ruta para guardar el personaje seleccionado por el usuario
app.post('/save-character', (req, res) => {
    const { email, personaje } = req.body;

    // Ruta al archivo data.json
    const filePath = path.join(__dirname, 'data.json');

    // Leer el archivo para obtener los datos existentes
    fs.readFile(filePath, 'utf8', (err, fileData) => {
        if (err) {
            return res.status(500).send('Error al leer el archivo.');
        }

        // Parsear los datos leídos del archivo
        let users = JSON.parse(fileData || '[]');

        // Buscar al usuario por email
        const userIndex = users.findIndex(user => user.email === email);

        // Si el usuario existe, actualizar el personaje
        if (userIndex !== -1) {
            users[userIndex].personaje = personaje;

            // Escribir los datos actualizados en el archivo
            fs.writeFile(filePath, JSON.stringify(users, null, 2), (err) => {
                if (err) {
                    return res.status(500).send('Error al guardar los datos.');
                }

                // Enviar los datos del usuario actualizado como respuesta
                res.json(users[userIndex]);
            });
        } else {
            // Si no se encuentra al usuario, devolver un error 404
            res.status(404).send('Usuario no encontrado.');
        }
    });
});




// Ruta para obtener los datos de un archivo JSON
app.get('/getData', (req, res) => {
    const filePath = path.join(__dirname, 'data.json');

    fs.readFile(filePath, 'utf8', (err, fileData) => {
        if (err) {
            return res.status(500).send('Error al leer el archivo.');
        }

        res.json(JSON.parse(fileData || '[]'));  // Devolvemos los datos del archivo JSON
    });
});


// Configuración del servidor con Socket.io
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: '*',
    }
});

const rooms = {}; // Guardar datos de las salas

io.on('connection', (socket) => {
    console.log('Usuario conectado:', socket.id);

    // Crear sala
    socket.on('createRoom', ({ user }) => {
        const roomId = `room-${Date.now()}`; // Generar ID único
        rooms[roomId] = {
            id: roomId,
            creatorId: socket.id, // Guardamos el ID del creador
            users: [{ id: socket.id, user }],
        };
        socket.join(roomId);
        io.to(roomId).emit('roomUpdate', rooms[roomId]);
        console.log(`Sala creada: ${roomId} por usuario: ${user}`);
    });

    // Unirse a una sala
    socket.on('joinRoom', ({ roomId, user }) => {
        if (rooms[roomId] && rooms[roomId].users.length < 4) {
            rooms[roomId].users.push({ id: socket.id, user });
            socket.join(roomId);
            io.to(roomId).emit('roomUpdate', rooms[roomId]);
            console.log(`Usuario ${user} se unió a la sala: ${roomId}`);
        } else {
            socket.emit('error', 'La sala no existe o está llena.');
        }
    });

    // Salir de una sala
    socket.on('leaveRoom', (roomId) => {
        if (rooms[roomId]) {
            rooms[roomId].users = rooms[roomId].users.filter(u => u.id !== socket.id);
            if (rooms[roomId].users.length === 0) {
                delete rooms[roomId];
            } else {
                io.to(roomId).emit('roomUpdate', rooms[roomId]);
            }
            socket.leave(roomId);
            console.log(`Usuario ${socket.id} salió de la sala: ${roomId}`);
        }
    });

    // Cerrar una sala (solo el creador puede cerrar)
    socket.on('closeRoom', (roomId) => {
        if (rooms[roomId] && rooms[roomId].creatorId === socket.id) {
            io.to(roomId).emit('roomClosed');
            delete rooms[roomId];
            console.log(`Sala cerrada: ${roomId}`);
        } else {
            socket.emit('error', 'Solo el creador puede cerrar la sala.');
        }
    });

    // Iniciar el juego (redirigir a todos al tablero)
    socket.on('startGame', (roomId) => {
        if (rooms[roomId] && rooms[roomId].creatorId === socket.id) {
            io.to(roomId).emit('gameStarted');
            console.log(`Juego iniciado en la sala: ${roomId}`);
        } else {
            socket.emit('error', 'Solo el creador puede iniciar el juego.');
        }
    });

    socket.on('disconnect', () => {
        for (const roomId in rooms) {
            const room = rooms[roomId];
            room.users = room.users.filter(u => u.id !== socket.id);
            if (room.users.length === 0) {
                delete rooms[roomId];
            } else {
                io.to(roomId).emit('roomUpdate', room);
            }
        }
        console.log('Usuario desconectado:', socket.id);
    });
});







// Datos de los personajes 
const personajes = {
  1: {
    right: ['assets/images/characters/personaje1-right1.png', 'assets/images/characters/personaje1-right2.png', 'assets/images/characters/personaje1-right3.png'],
    up: ['assets/images/characters/personaje1-up1.png', 'assets/images/characters/personaje1-up2.png', 'assets/images/characters/personaje1-up3.png'],
    down: ['assets/images/characters/personaje1-down1.png', 'assets/images/characters/personaje1-down2.png', 'assets/images/characters/personaje1-down3.png'],
    idle: 'assets/images/characters/personaje1-idle.png' // Imagen estática cuando el personaje no se mueve
  },
  2: {
    right: ['assets/images/characters/personaje2-right1.png', 'assets/images/characters/personaje2-right2.png', 'assets/images/characters/personaje2-right3.png'],
    up: ['assets/images/characters/personaje2-up1.png', 'assets/images/characters/personaje2-up2.png', 'assets/images/characters/personaje2-up3.png'],
    down: ['assets/images/characters/personaje2-down1.png', 'assets/images/characters/personaje2-down2.png', 'assets/images/characters/personaje2-down3.png'],
    idle: 'assets/images/characters/personaje2-idle.png' // Imagen estática cuando el personaje no se mueve
  },
  3: {
    right: ['assets/images/characters/personaje3-right1.png', 'assets/images/characters/personaje3-right2.png', 'assets/images/characters/personaje3-right3.png'],
    up: ['assets/images/characters/personaje3-up1.png', 'assets/images/characters/personaje3-up2.png', 'assets/images/characters/personaje3-up3.png'],
    down: ['assets/images/characters/personaje3-down1.png', 'assets/images/characters/personaje3-down2.png', 'assets/images/characters/personaje3-down3.png'],
    idle: 'assets/images/characters/personaje3-idle.png' // Imagen estática cuando el personaje no se mueve
  },
  4: {
    right: ['assets/images/characters/personaje4-right1.png', 'assets/images/characters/personaje4-right2.png', 'assets/images/characters/personaje4-right3.png'],
    up: ['assets/images/characters/personaje4-up1.png', 'assets/images/characters/personaje4-up2.png', 'assets/images/characters/personaje4-up3.png'],
    down: ['assets/images/characters/personaje4-down1.png', 'assets/images/characters/personaje4-down2.png', 'assets/images/characters/personaje4-down3.png'],
    idle: 'assets/images/characters/personaje4-idle.png' // Imagen estática cuando el personaje no se mueve
  }
};
  
  // Ruta para obtener los datos del usuario
  app.get('/api/getUsuario', (req, res) => {
    // Leer los usuarios desde el archivo JSON
    const usuarios = JSON.parse(fs.readFileSync('data.json', 'utf-8'));
    
    // Encontrar al usuario actual (supongamos que el ID está pasando como query)
    const usuarioActual = usuarios.find(usuario => usuario.id === parseInt(req.query.id));
    
    if (usuarioActual) {
      // Obtener el personaje asignado al usuario
      const personajeSeleccionado = personajes[usuarioActual.personaje];
      res.json(personajeSeleccionado); // Enviar las imágenes del personaje
    } else {
      res.status(404).json({ error: 'Usuario no encontrado' });
    }
  });

const PORT = 3000; // Asegúrate de usar el puerto correcto

server.listen(PORT, () => {
    console.log(`Servidor ejecutándose en http://localhost:${PORT}`);
});
