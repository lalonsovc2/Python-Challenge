document.addEventListener("DOMContentLoaded", () => {
    const boardContainer = document.getElementById("board-container");
    const budgetElement = document.getElementById("budget");
    const scoreElement = document.getElementById("score");
    const eventList = document.getElementById("event-list");

    let player = {
        budget: 100000,
        score: 0,
        position: 0,
        products: [],
        projects: [],
        resources: []
    };

    let currentMonth = 'enero';
    let currentHalf = 1;

    const months = {
        enero: generateMonthBoard(),
        febrero: generateMonthBoard(),
        // Agregar más meses según sea necesario
    };

    function generateMonthBoard() {
        const board = [];
        for (let i = 0; i < 30; i++) {
            const dayOfWeek = (i % 7) + 1; // 1: Monday, 7: Sunday
            board.push({
                day: i + 1,
                type: (dayOfWeek === 6 || dayOfWeek === 7) ? 'weekend' : 'normal',
                event: null
            });
        }
        return board;
    }

    function assignEvents() {
        const events = [
            // Aquí se deben agregar los eventos del archivo CSV
            { id: 1, description: "Evento 1", required_efficiencies: [5, 6, 9], result_success: { budgetChange: 100, scoreChange: 50 }, result_failure: { budgetChange: -100, scoreChange: -50 } },
            { id: 2, description: "Evento 2", required_efficiencies: [9, 12, 4], result_success: { budgetChange: 200, scoreChange: 100 }, result_failure: { budgetChange: -200, scoreChange: -100 } },
            // Agregar más eventos según sea necesario
        ];

        for (const month in months) {
            const monthBoard = months[month];
            let eventIndex = 0;
            for (let i = 0; i < monthBoard.length; i++) {
                if (monthBoard[i].type === 'normal' && eventIndex < events.length) {
                    monthBoard[i].event = events[eventIndex];
                    eventIndex++;
                }
            }
        }
    }

    function renderBoard() {
        boardContainer.innerHTML = '';
        const monthBoard = months[currentMonth];
        const start = (currentHalf - 1) * 15;
        const end = currentHalf * 15;
        for (let i = start; i < end; i++) {
            const cell = document.createElement("div");
            cell.classList.add("board-cell");
            cell.textContent = `Día ${monthBoard[i].day}`;
            if (monthBoard[i].event) {
                cell.classList.add("event-cell");
                cell.title = monthBoard[i].event.description;
            }
            boardContainer.appendChild(cell);
        }
        const nextButton = document.createElement("div");
        nextButton.classList.add("board-cell");
        nextButton.textContent = '→';
        nextButton.onclick = () => {
            if (currentHalf === 1) {
                currentHalf = 2;
            } else {
                currentHalf = 1;
                // Cambiar al siguiente mes
                // Implementar lógica para cambiar al siguiente mes
            }
            renderBoard();
        };
        boardContainer.appendChild(nextButton);
    }

    window.showMonth = function(month) {
        currentMonth = month;
        currentHalf = 1;
        renderBoard();
    };

    window.rollDice = async function() {
        const response = await fetch('/lanzar_dados', { method: 'POST' });
        const data = await response.json();
        alert(data.message);
        player.position += data.steps;
        player.position = player.position % 30; // Asegurarse de que la posición esté dentro del mes
        updateBoard();
    };

    window.handleEvent = async function() {
        const response = await fetch('/enfrentar_evento', { method: 'POST' });
        const data = await response.json();
        const eventItem = document.createElement("li");
        eventItem.textContent = data.message;
        eventList.appendChild(eventItem);
        player.budget += data.budgetChange;
        player.score += data.scoreChange;
        updateBoard();
    };

    function updateBoard() {
        const cells = document.querySelectorAll(".board-cell");
        cells.forEach(cell => cell.classList.remove("player-position"));
        cells[player.position % 15].classList.add("player-position");
        budgetElement.textContent = player.budget;
        scoreElement.textContent = player.score;
    }

    assignEvents();
    renderBoard();
});