const openModalBtn = document.getElementById("openModalBtn");
const mainContainer = document.getElementById("main-container");
const closeModalBtn = document.getElementById("closeModalBtn");
const itemsContainer = document.getElementById("items-container");
const buyButton = document.getElementById("buyButton");
const itemTitle = document.getElementById("item-title");
const itemRequirements = document.getElementById("item-requirements");
const budgetAvailable = document.getElementById("budgetAvailable");

let selectedItem = null;
let availableBudget = 1000; // Presupuesto inicial


// Abrir el modal
// Abrir el modal
openModalBtn.addEventListener("click", () => {
    mainContainer.style.display = "flex";
    openModalBtn.style.display = "none";

    // Obtener los datos del usuario logueado desde localStorage
    const userData = JSON.parse(localStorage.getItem('user')); // Parsear el objeto almacenado
    const email = userData?.email; // Extraer solo el email

    // Verificar que el email esté presente antes de sincronizar la tienda
    if (!email) {
        console.error("No se encontró el email del usuario.");
        return;  // Detener el proceso si no se encuentra el email
    }

    console.log("Email enviado al servidor:", email);  // Verificar el email enviado

    // Re-sincronizar la tienda con el email del usuario logueado
    inicializarTienda(email);  // Pasar el email del usuario logueado dinámicamente
});


function setActive(button) {
    // Elimina la clase 'active' de todos los botones
    const buttons = document.querySelectorAll('.categories button');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Añade la clase 'active' al botón clickeado
    button.classList.add('active');
  }

  // Definir la función showCategory
  function showCategory(category) {
      console.log('Mostrando categoría:', category);
     
  }



// Cerrar el modal
closeModalBtn.addEventListener("click", () => {
    mainContainer.style.display = "none";
    openModalBtn.style.display = "inline-block";
});

function cargarDatos(itemsComprados, categoriaPorDefecto = 'productos') {
    const productosComprados = Array.isArray(itemsComprados.productos_comprados) ? itemsComprados.productos_comprados : [];
    const proyectosComprados = Array.isArray(itemsComprados.proyectos_comprados) ? itemsComprados.proyectos_comprados : [];
    const recursosComprados = Array.isArray(itemsComprados.recursos_comprados) ? itemsComprados.recursos_comprados : [];

    Promise.all([
        fetch("/productos").then(res => res.json()),
        fetch("/proyectos").then(res => res.json()),
        fetch("/recursos").then(res => res.json())
    ])
    .then(([productos, proyectos, recursos]) => {
        window.productos = productos;
        window.proyectos = proyectos;
        window.recursos = recursos;

        // Marcar ítems adquiridos
        productos.forEach(item => {
            if (productosComprados.includes(item.ID.toString())) {
                item.purchased_on = 1;  // Marcar como adquirido
            }
        });
        proyectos.forEach(item => {
            if (proyectosComprados.includes(item.ID.toString())) {
                item.purchased_on = 1;  // Marcar como adquirido
            }
        });
        recursos.forEach(item => {
            if (recursosComprados.includes(item.ID.toString())) {
                item.purchased_on = 1;  // Marcar como adquirido
            }
        });

        // Renderizar la categoría por defecto y mostrar el primer ítem
        showCategory(categoriaPorDefecto);

        // Marcar el botón correspondiente como activo
        const categoryButton = document.querySelector(`.categories button[data-category="${categoriaPorDefecto}"]`);
        setActive(categoryButton);  // Esto marcará el botón correspondiente como activo
    })
    .catch(error => console.error("Error al cargar datos:", error));
}


// Función para seleccionar el primer ítem de la categoría por defecto y mostrar sus detalles
function selectDefaultItem(categoria, productos, proyectos, recursos) {
    let selectedItem = null;
    if (categoria === 'productos' && productos.length > 0) {
        selectedItem = productos[0];  // Selecciona el primer producto
        showItemDetails(selectedItem, 'productos'); // Muestra detalles del primer producto
    } else if (categoria === 'proyectos' && proyectos.length > 0) {
        selectedItem = proyectos[0];  // Selecciona el primer proyecto
        showItemDetails(selectedItem, 'proyectos'); // Muestra detalles del primer proyecto
    } else if (categoria === 'recursos' && recursos.length > 0) {
        selectedItem = recursos[0];  // Selecciona el primer recurso
        showItemDetails(selectedItem, 'recursos'); // Muestra detalles del primer recurso
    }

    if (selectedItem) {
        console.log("Ítem seleccionado por defecto:", selectedItem);
        // Aquí puedes agregar lógica adicional si necesitas hacer algo más con el ítem seleccionado
    }
}








function renderCategory(categoryId, data, itemsComprados = []) {
if (!Array.isArray(data)) {
console.error("Data no es un arreglo válido:", data);  // Agregar mensaje de error si `data` no es un arreglo
return;  // Detener ejecución si `data` no es un arreglo
}

const itemsWrapper = document.querySelector(".items-wrapper");
const itemsContainer = document.querySelector("#items-container");

// Limpiar el contenido anterior
itemsContainer.innerHTML = "";  

const existingIcon = itemsWrapper.querySelector(".category-icon");
if (existingIcon) {
    existingIcon.remove();
}

// Crear el ícono centralizado para la categoría
const categoryIcon = document.createElement("img");
categoryIcon.classList.add("category-icon");
categoryIcon.style.margin = "-60px -100px";  // Para centrar la imagen horizontalmente
categoryIcon.style.position = "absolute"; 

// Determinar el ícono según la categoría
switch (categoryId) {
    case "productos":
        categoryIcon.src = "/images/productsTitle.png";
        categoryIcon.alt = "Icono de productos";
        break;
    case "proyectos":
        categoryIcon.src = "/images/projectsTitle.png";
        categoryIcon.alt = "Icono de proyectos";
        break;
    case "recursos":
        categoryIcon.src = "/images/resourceTitle.png";
        categoryIcon.alt = "Icono de recursos";
        break;
    default:
        categoryIcon.src = "/icons/default.png";  // Ícono genérico para categorías no definidas
        categoryIcon.alt = "Error image";
}

itemsWrapper.insertBefore(categoryIcon, itemsContainer);



data.forEach(item => {
const container = document.createElement("div");
container.classList.add("item-container");



const div = document.createElement("div");
div.classList.add("item");
div.dataset.id = item.ID;

// Asignar el tipo de ítem (producto, proyecto, recurso)
item.type = categoryId;

// Determinar si el ítem está comprado
const isPurchased = itemsComprados.includes(item.ID.toString()) || item.purchased_on;
if (isPurchased) {
    div.classList.add("item-acquired");
}

// Ruta de la imagen
const imagePath = `/images/${categoryId.charAt(0).toUpperCase() + categoryId.slice(1)}/${categoryId}_${item.ID}.png`;

div.innerHTML = `
    <img src="${imagePath}" alt="${item.name}">
    <p class="item-name">${item.name}</p>
`;

div.addEventListener("click", () => showItemDetails(item, categoryId));
container.appendChild(div);

// Mostrar precio o "Adquirido"
const price = document.createElement("p");
        price.classList.add("item-price");

        if (isPurchased) {
            price.classList.add("acquired");
            // Si está adquirido, mostrar un ícono o imagen
            const checkImage = document.createElement("img");
            checkImage.src = "/images/check.png"; // Cambia por la ruta de tu imagen
            checkImage.alt = "Adquirido"; // Texto alternativo para accesibilidad
            checkImage.style.width = "14px"; // Tamaño opcional
            checkImage.style.height = "10px"; // Tamaño opcional
            price.appendChild(checkImage);
        } else {
            // Mostrar el precio
            price.textContent = `$${item.cost}`;
        }
container.appendChild(price);

itemsContainer.appendChild(container);
});
}










function showItemDetails(item, categoryId) {
    selectedItem = item;  // Guardar el ítem seleccionado

    // Mostrar título y detalles
    document.getElementById("item-name").textContent = item.name;
    document.getElementById("item-cost").textContent = item.purchased_on && item.purchased_on > 0 ? "Adquirido" : `$${item.cost}`;

    // Mostrar imagen principal
    const imagePath = `/images/${categoryId.charAt(0).toUpperCase() + categoryId.slice(1)}/${categoryId}_${item.ID}.png`;
    const imageElement = document.createElement("img");
    imageElement.src = imagePath;
    imageElement.alt = item.name;
    imageElement.style.width = "58%";
    imageElement.style.height = "auto";
    imageElement.style.marginTop = "70px";
    imageElement.style.marginLeft = "80px";


    // Limpiar imágenes previas
    const detailsContainer = document.getElementById("selected-item");
    detailsContainer.querySelectorAll("img").forEach(img => img.remove());
    detailsContainer.insertBefore(imageElement, detailsContainer.firstChild);

    // Agregar un ícono por categoría en la parte superior
    const categoryIconContainer = document.createElement("img");
    categoryIconContainer.style.width = "219.48px";  // Ajusta el tamaño del ícono
    categoryIconContainer.style.height = "93.32px";
    categoryIconContainer.style.position = "absolute";
    categoryIconContainer.style.marginLeft = "83px";
    categoryIconContainer.style.marginTop = "-35px";

    if (categoryId === "productos") {
        categoryIconContainer.src = "/images/productDetails.png";  // Ruta del ícono de productos
        categoryIconContainer.alt = "Producto";
    } else if (categoryId === "proyectos") {
        categoryIconContainer.src = "/images/projectsDetails.png";  // Ruta del ícono de proyectos
        categoryIconContainer.alt = "Proyecto";
    } else if (categoryId === "recursos") {
        categoryIconContainer.src = "/images/recursosDetails.png";  // Ruta del ícono de recursos
        categoryIconContainer.alt = "Recurso";
    }

    // Limpiar íconos previos
    const existingIcon = detailsContainer.querySelector(".category-icon");
    if (existingIcon) {
        existingIcon.remove();  // Eliminar el ícono previo si existe
    }

    // Añadir el ícono al contenedor de detalles
    categoryIconContainer.classList.add("category-icon");
    detailsContainer.insertBefore(categoryIconContainer, detailsContainer.firstChild);  // Insertar antes de la imagen principal

    // Mostrar imágenes de requerimientos, solo si item.requirements existe
    itemRequirements.innerHTML = ""; // Limpiar anteriores
    if (item.requirements && Array.isArray(item.requirements)) {  // Verificar si 'requirements' existe y es un array
        item.requirements.slice(0, 3).forEach(reqId => {
            const reqItem = window.productos.find(p => p.ID === reqId);
            if (reqItem) {
                const img = document.createElement("img");
                img.src = `/images/Productos/Productos_${reqId}.png`;
                img.alt = reqItem.name;
                itemRequirements.appendChild(img);
            }
        });
    } else {
        // Si el ítem no tiene requisitos, podemos mostrar un mensaje o simplemente no hacer nada
        console.log("Este ítem no tiene requisitos o 'requirements' no está definido.");
    }

    // Mostrar botón de compra si no está adquirido
    buyButton.style.display = item.purchased_on && item.purchased_on > 0 ? "none" : "block";
}






function buyItem() {
    if (selectedItem) {
        if (availableBudget >= selectedItem.cost) {
            // Actualizar presupuesto localmente
            availableBudget -= selectedItem.cost;
            budgetAvailable.textContent = `$${availableBudget}`;
            selectedItem.purchased_on = 1;

            // Actualizar visualmente el ítem en la UI
            const itemElement = document.querySelector(`.item[data-id="${selectedItem.ID}"]`);
            itemElement.classList.add("item-acquired");
            const priceElement = itemElement.parentElement.querySelector(".item-price");
            priceElement.textContent = "Adquirido";
            const userData = JSON.parse(localStorage.getItem('user')); // Parsear el objeto almacenado
            const email = userData?.email;
            // Verificar la categoría antes de enviar la solicitud
            console.log("Categoría del ítem seleccionado:", selectedItem.type);  // Verifica el valor de 'type'

            // Enviar la compra al backend para actualizar el estado
            fetch('/update-user-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,  // Cambiar según el usuario logueado
                    budget: availableBudget,
                    purchased_item: selectedItem.ID,
                    category: selectedItem.type  // Aquí se pasa 'producto', 'proyecto' o 'recurso'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert("Error al actualizar el estado del usuario.");
                } else {
                    alert(`${selectedItem.name} comprado exitosamente!`);
                }
            })
            .catch(error => console.error("Error al actualizar estado del usuario:", error));
        } else {
            alert("No tienes suficiente presupuesto para comprar este ítem.");
        }
    }
}





function cargarEstadoUsuario(email) {
    fetch('/get-user-state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            console.error("Error:", data.error);
        } else {
            availableBudget = data.budget; // Presupuesto inicial
            budgetAvailable.textContent = `$${availableBudget}`;

            // Marcar ítems comprados
            data.productos_comprados.forEach(itemId => {
                const itemElement = document.querySelector(`.item[data-id="${itemId}"]`);
                if (itemElement) {
                    itemElement.classList.add("item-acquired");
                    const priceElement = itemElement.parentElement.querySelector(".item-price");
                    priceElement.textContent = "Adquirido";
                }
            });
        }
    })
    .catch(error => console.error("Error al cargar estado del usuario:", error));
}



function showCategory(categoria) {
    let items = [];
    let categoryId = '';

    // Dependiendo de la categoría, selecciona los ítems
    if (categoria === 'productos') {
        items = window.productos;
        categoryId = 'productos';
    } else if (categoria === 'proyectos') {
        items = window.proyectos;
        categoryId = 'proyectos';
    } else if (categoria === 'recursos') {
        items = window.recursos;
        categoryId = 'recursos';
    }

    // Renderizar la categoría (esto lo haces con tu función de renderizado)
    renderCategory(categoria, items, []); // Si tienes productos comprados, puedes pasarlos como el tercer parámetro.

    // Seleccionar el primer ítem y mostrar sus detalles
    if (items.length > 0) {
        const selectedItem = items[0];  // Seleccionar el primer ítem
        showItemDetails(selectedItem, categoryId); // Mostrar detalles del primer ítem
    }
}

function inicializarTienda(email) {
    fetch('/get-user-state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })  // Usar el email dinámico desde localStorage
    })
    .then(res => res.json())
    .then(data => {
        // Verificar la respuesta del servidor
        console.log("Datos recibidos del servidor:", data);  // Verifica si los datos se están recibiendo correctamente

        if (data.error) {
            console.error("Error:", data.error);
        } else {
            // Verificar que los datos recibidos estén correctamente estructurados
            if (!Array.isArray(data.productos_comprados) || !Array.isArray(data.proyectos_comprados) || !Array.isArray(data.recursos_comprados)) {
                console.error("Los datos de 'productos_comprados', 'proyectos_comprados' o 'recursos_comprados' no son válidos.");
            }

            // Actualizar el presupuesto y la tienda
            availableBudget = data.budget;
            budgetAvailable.textContent = `$${availableBudget}`;

            cargarDatos(data);  // Pasa los datos correctos a la función cargarDatos
        }
    })
    .catch(error => console.error("Error al inicializar la tienda:", error));
}


