let currentMonthIndex = 0;
let currentHalf = 0;

document.getElementById('prev-month').addEventListener('click', () => {
    fetch('/api/game/switch_month', { method: 'POST', body: JSON.stringify({ increment: -1 }) })
        .then(updateBoard);
});

document.getElementById('next-month').addEventListener('click', () => {
    fetch('/api/game/switch_month', { method: 'POST', body: JSON.stringify({ increment: 1 }) })
        .then(updateBoard);
});

document.getElementById('switch-half').addEventListener('click', () => {
    fetch('/api/game/switch_half', { method: 'POST' })
        .then(updateBoard);
});

function updateBoard() {
    fetch('/api/game/get_current_board')
        .then(response => response.json())
        .then(data => {
            // Renderizar el tablero con los datos de la mitad actual
            renderBoard(data);
        });
}
