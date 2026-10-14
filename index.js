let productos = {};
let carrito = [];
let agregandoProducto = false;
let categoriaActual = 'hamburguesas';
const ingredientesPorProducto = {};
const CACHE_VERSION = Date.now();
const API_BASE = ['127.0.0.1', 'localhost'].includes(location.hostname) && location.port === '5500'
    ? `http://${location.hostname}:5000`
    : '';

function solicitarAPI(ruta, opciones = {}) {
    return fetch(`${API_BASE}${ruta}`, { credentials: 'include', ...opciones });
}

const CLAVE_CLIENTE = 'burger-house-cliente';

function obtenerCliente() {
    try {
        const cliente = JSON.parse(localStorage.getItem(CLAVE_CLIENTE) || 'null');
        return cliente && typeof cliente.nombre === 'string' && typeof cliente.telefono === 'string'
            ? cliente
            : null;
    } catch {
        return null;
    }
}

function guardarCliente(cliente) {
    localStorage.setItem(CLAVE_CLIENTE, JSON.stringify(cliente));
}

const CLAVE_PEDIDO_ACTIVO = 'burger-house-pedido-activo';
const INTERVALO_SEGUIMIENTO_MS = 20000;
let temporizadorSeguimiento = null;
let ultimoEstadoPedido = null;

function obtenerPedidoActivo() {
    try {
        const pedido = JSON.parse(localStorage.getItem(CLAVE_PEDIDO_ACTIVO) || 'null');
        if (pedido && Number.isInteger(Number(pedido.id))) {
            return { id: Number(pedido.id), telefono: typeof pedido.telefono === 'string' ? pedido.telefono : '' };
        }
    } catch {
        // almacenamiento no disponible o dato dañado
    }
    return null;
}

function guardarPedidoActivo(id, telefono = '') {
    try {
        localStorage.setItem(CLAVE_PEDIDO_ACTIVO, JSON.stringify({ id: Number(id), telefono }));
    } catch {
        // si no se puede guardar, el seguimiento sigue funcionando mientras la página esté abierta
    }
}

function olvidarPedidoActivo() {
    try {
        localStorage.removeItem(CLAVE_PEDIDO_ACTIVO);
    } catch {
        // nada que hacer
    }
}

function actualizarSaludo(cliente) {
    const nombreCompleto = cliente && typeof cliente.nombre === 'string' ? cliente.nombre.trim() : '';
    document.getElementById('saludo-usuario').textContent = nombreCompleto
        ? `¡Bienvenido, ${nombreCompleto}!`
        : '¡Bienvenido a Burger House!';
}

function escaparHTML(valor) {
    return String(valor).replace(/[&<>"']/g, caracter => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[caracter]);
}

async function obtenerPedido(id, telefono = '') {
    const parametro = new URLSearchParams({ id, telefono });
    const respuesta = await solicitarAPI(`/api/pedidos?${parametro}`);
    const pedido = await respuesta.json();
    if (!respuesta.ok) {
        const error = new Error(pedido.error || 'No se pudo consultar el pedido.');
        error.estado = respuesta.status;
        throw error;
    }
    return pedido;
}
async function cargarMenu() {
    const respuesta = await solicitarAPI('/api/menu');
    if (!respuesta.ok) throw new Error('No se pudo cargar el menú.');
    productos = await respuesta.json();
}

function normalizarTipo(tipo) {
    return tipo.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

const IMAGENES_PRODUCTOS = {
    'hamburguesa clasica': '/imagenes/hamburguesa_clasica_1.png',
    'hamburguesa cheeseburger': '/imagenes/hamburguesa_cheeseburger_2.png',
    'hamburguesa bacon': '/imagenes/bacon_3.png',
    'hamburguesa doble bacon': '/imagenes/doble_bacon_11.png',
    'hamburguesa ranchera': '/imagenes/ranchera_12.png',
    'hamburguesa8': '/imagenes/campesina_13.png',
    'hamburguesa9': '/imagenes/colombiana_14.png',
    'hamburguesa4': '/imagenes/hawaiana_4.png',
    'mexicana': '/imagenes/guacamole_7.png',
    'criolla': '/imagenes/criolla_6.png',
    'hamburguesa5': '/imagenes/cebolla_caramelizada_8.png',
    'hamburguesa10': '/imagenes/tres_quesos_9.png',
    'hamburguesa11': '/imagenes/doble_carne_10.png',
    'llanera': '/imagenes/llanera_15.png',
    'bbq_pulled_pork': '/imagenes/bbq_pulled_pork_16.png',
    'chicken_crispy': '/imagenes/chicken_crispy_17.png',
    'pollo_bbq': '/imagenes/pollo_bbq_19.png',
    'perros': '/imagenes/perros_house.png',
    'bebidas': '/imagenes/bebidas_house.png',
    'sandwich': '/imagenes/sandwich_house.png',
    'acompanamientos': '/imagenes/acompanamientos_house.png',
    'picadas': '/imagenes/picadas_house.png',
    'combos': '/combos/imagen_combo.png',
};

const PRODUCTOS_POR_CATEGORIA = {
    hamburguesas: ['hamburguesa Clasica', 'hamburguesa Cheeseburger', 'hamburguesa Bacon', 'hamburguesa4', 'mexicana', 'criolla', 'hamburguesa5', 'hamburguesa Doble Bacon', 'hamburguesa Ranchera', 'hamburguesa8', 'hamburguesa9', 'llanera', 'bbq_pulled_pork', 'chicken_crispy', 'pollo_bbq', 'hamburguesa10', 'hamburguesa11'],
    perros: ['perros', 'perro_hawaiano', 'perro_bbq', 'perro_ranchero', 'perro_mexicano', 'perro_crispy', 'perro_mixto', 'perro_especial', 'perro_super', 'perro_festival', 'perro_ranchero_bbq', 'perro_pollo', 'perro_tocineta', 'perro_3_carnes', 'perro_brutal'],
    salchipapas: ['salchipapas', 'salchipapas_gratinada', 'salchipapas_cheddar_tocineta', 'salchipapas_pollo', 'salchipapas_carne', 'salchipapas_mixta', 'salchipapas_ranchera', 'salchipapas_criolla', 'salchipapas_costena', 'salchipapas_mexicana', 'salchipapas_hawaiana', 'salchipapas_bbq', 'salchipapas_especial', 'salchipapas_porky', 'salchipapas_festival'],
    bebidas: ['bebidas', 'bebida_coca_600', 'bebida_coca_1_5', 'bebida_zero_600', 'bebida_zero_1_5', 'bebida_sprite_400', 'bebida_pony_malta_1_5', 'bebida_cristal_600', 'bebida_cristal_1l', 'bebida_brisa_1l', 'bebida_manantial_600', 'bebida_manantial_1_5', 'bebida_h2oh_limonata_1_5', 'bebida_hit_mango_500', 'bebida_hit_tropicales_1l'],
    sandwich: ['sandwich_clasico', 'sandwich_mixto', 'sandwich_jamon_queso', 'sandwich_pollo', 'sandwich_pollo_queso', 'sandwich_crispy', 'sandwich_carne', 'sandwich_bbq', 'sandwich_mexicano', 'sandwich_hawaiano', 'sandwich_especial', 'sandwich_ranchero', 'sandwich_bbq_especial', 'sandwich_super_especial', 'sandwich_festival'],
    acompanamientos: ['acompanamientos', 'acomp_papas_mediana', 'acomp_papas_grande', 'acomp_papas_familiar', 'acomp_papas_gratinadas', 'acomp_aros_cebolla', 'acomp_deditos_queso', 'acomp_nuggets', 'acomp_alitas_bbq', 'acomp_alitas_picantes', 'acomp_patacones'],
    combos: ['combos', 'combo_bacon', 'combo_perro', 'combo_salchipapa', 'combo_pareja', 'combo_compartir'],
    picadas: ['picadas', 'picada_imperial', 'picada_fuego_andino', 'picada_dragon', 'picada_brutal', 'picada_tropical', 'picada_trueno', 'picada_escorpion', 'picada_pirata', 'picada_dinamita', 'picada_leon', 'picada_azteca', 'picada_inferno', 'picada_diamante', 'picada_diosa'],
};

function obtenerProductosCategorias(tipoCategoria) {
    const categoria = normalizarTipo(tipoCategoria);
    const base = PRODUCTOS_POR_CATEGORIA[categoria] || [categoria];
    const nuevos = Object.keys(productos).filter(clave => productos[clave].categoria === categoria && !base.includes(clave));
    return [...base, ...nuevos];
}

function obtenerImagenProducto(tipo) {
    const tipoNormalizado = normalizarTipo(tipo);
    const imagenBase = productos[tipo]?.imagen
        || IMAGENES_PRODUCTOS[tipoNormalizado]
        || document.querySelector(`#imagenes-productos img[data-producto="${tipo}"]`)?.getAttribute('src')
        || [...document.querySelectorAll('.tarjeta')].find(item => normalizarTipo(item.dataset.tipo) === tipoNormalizado)?.querySelector('img')?.getAttribute('src')
        || (tipoNormalizado.startsWith('bebida') ? IMAGENES_PRODUCTOS.bebidas : '')
        || '';
    return imagenBase ? encodeURI(imagenBase) : '';
}

function renderListaHamburguesas(tipoCategoria = 'hamburguesas') {
    const contenedor = document.getElementById('lista-hamburguesas');
    if (!contenedor) return;

    const tiposCategoria = obtenerProductosCategorias(tipoCategoria);
    categoriaActual = tipoCategoria;
    contenedor.innerHTML = tiposCategoria.map(tipo => {
        const producto = productos[tipo];
        if (!producto) return '';
        const ingredientes = ingredientesPorProducto[tipo] || producto.ingredientes || [];
        const personalizacion = !(producto.ingredientes && producto.ingredientes.length)
            ? ''
            : `
                <div class="personalizar-producto">
                    <strong>Ingredientes incluidos</strong>
                    <div class="lista-ingredientes">
                ${ingredientes.length ? ingredientes.map(ingrediente => `
                    <div class="ingrediente">
                        <span class="ingrediente-nombre">${escaparHTML(ingrediente)}</span>
                        <button class="btn-quitar-ingrediente btn-quitar-resumen" type="button" data-tipo="${tipo}" data-ingrediente="${escaparHTML(ingrediente)}">Quitar</button>
                    </div>
                `).join('') : '<small>Sin ingredientes incluidos.</small>'}
                    </div>
                    <button class="btn-restaurar-ingredientes btn-restaurar-resumen" type="button" data-tipo="${tipo}">Restaurar ingredientes</button>
                </div>
            `;
        return `
            <article class="producto-lista-item">
                <div class="producto-info">
                    <img src="${escaparHTML(obtenerImagenProducto(tipo))}" alt="${escaparHTML(producto.nombre)}" onerror="this.style.visibility='hidden'">
                    <div>
                        <h3>${escaparHTML(producto.nombre)}</h3>
                        <p class="producto-descripcion">${escaparHTML(producto.descripcion)}</p>
                        <p class="producto-detalle-texto">${escaparHTML(producto.detalle)}</p>
                        ${personalizacion}
                        <p class="producto-precio">Precio: $${producto.precio.toLocaleString('es-CO')}</p>
                        <button class="btn-agregar btn-agregar-lista" type="button" data-tipo="${tipo}">Agregar al carrito</button>
                    </div>
                </div>
            </article>
        `;
    }).join('');

    contenedor.querySelectorAll('.btn-quitar-resumen').forEach(button => {
        button.addEventListener('click', evento => {
            evento.stopPropagation();
            const tipo = button.dataset.tipo;
            const ingredientes = ingredientesPorProducto[tipo] || productos[tipo].ingredientes || [];
            ingredientesPorProducto[tipo] = ingredientes.filter(ingrediente => ingrediente !== button.dataset.ingrediente);
            renderListaHamburguesas(categoriaActual);
        });
    });
    contenedor.querySelectorAll('.btn-restaurar-resumen').forEach(button => {
        button.addEventListener('click', evento => {
            evento.stopPropagation();
            const tipo = button.dataset.tipo;
            const producto = productos[tipo];
            if (producto) {
                ingredientesPorProducto[tipo] = [...producto.ingredientes];
                renderListaHamburguesas(categoriaActual);
            }
        });
    });
    contenedor.querySelectorAll('.btn-agregar-lista').forEach(button => {
        button.addEventListener('click', evento => {
            agregarProductoConSeguridad(button.dataset.tipo, evento.currentTarget);
        });
    });
}

function bloquearBotonTemporamente(boton) {
    if (!(boton instanceof HTMLElement)) return;
    boton.disabled = true;
    window.setTimeout(() => {
        boton.disabled = false;
    }, 250);
}

function agregarProductoConSeguridad(tipo, boton = null) {
    if (agregandoProducto) return;
    agregandoProducto = true;
    if (boton) bloquearBotonTemporamente(boton);
    try {
        agregarAlCarrito(tipo);
    } finally {
        window.setTimeout(() => {
            agregandoProducto = false;
        }, 250);
    }
}

function mostrarMenu() {
    document.getElementById('menu').classList.remove('menu-oculto');
    abrirCarrito();
}

// El botón flotante solo aparece cuando el menú está visible y el carrito está oculto.
function actualizarBotonCarrito() {
    const boton = document.getElementById('abrir-carrito');
    if (!boton) return;
    const menuVisible = !document.getElementById('menu').classList.contains('menu-oculto');
    const carritoOculto = document.getElementById('carrito').classList.contains('oculto');
    const unidades = carrito.reduce((suma, item) => suma + item.cantidad, 0);
    const contador = document.getElementById('contador-carrito');
    if (contador) contador.textContent = unidades;
    boton.setAttribute('aria-label', `Abrir carrito (${unidades} productos)`);
    boton.hidden = !(menuVisible && carritoOculto);
}

function abrirCarrito() {
    document.getElementById('carrito').classList.remove('oculto');
    actualizarBotonCarrito();
}

function cerrarCarrito() {
    document.getElementById('carrito').classList.add('oculto');
    actualizarBotonCarrito();
}

function seleccionarProducto(tipo) {
    const tipoNormalizado = normalizarTipo(tipo);
    const botones = document.querySelectorAll('.btn-seleccion');
    botones.forEach(btn => btn.classList.remove('activo'));
    const botonActivo = document.querySelector(`.btn-seleccion[data-tipo="${tipo}"]`);
    if (botonActivo) botonActivo.classList.add('activo');

    document.querySelectorAll('.tarjeta').forEach(item => {
        const seleccionada = normalizarTipo(item.dataset.tipo) === tipoNormalizado;
        item.classList.toggle('seleccionada', seleccionada);
        item.setAttribute('aria-pressed', String(seleccionada));
    });

    const categoriaProductos = obtenerProductosCategorias(tipoNormalizado);
    const primerProducto = categoriaProductos.find(item => productos[item]);
    const producto = productos[tipoNormalizado] || productos[primerProducto];

    if (!producto) {
        document.getElementById('titulo-producto').textContent = 'Producto no disponible';
        document.getElementById('producto-detalle').textContent = 'No hay productos para esta categoría.';
        renderListaHamburguesas(tipoNormalizado);
        return;
    }

    renderListaHamburguesas(tipoNormalizado);
    document.getElementById('titulo-producto').textContent = botonActivo ? botonActivo.textContent : producto.nombre;

    if (!ingredientesPorProducto[tipoNormalizado]) {
        ingredientesPorProducto[tipoNormalizado] = [...(producto.ingredientes || [])];
    }

    const ingredientes = ingredientesPorProducto[tipoNormalizado];
    const imagen = obtenerImagenProducto(tipoNormalizado);
    const esCategoriaSinPersonalizacion = false;
    document.getElementById('producto-detalle').innerHTML = `
        <div class="producto-info">
            <img src="${escaparHTML(imagen)}" alt="${escaparHTML(producto.nombre)}" onerror="this.style.visibility='hidden'">
            <div>
                <p class="producto-descripcion">${escaparHTML(producto.descripcion)}</p>
                <p class="producto-detalle-texto">${escaparHTML(producto.detalle)}</p>
                ${producto.ingredientes && !esCategoriaSinPersonalizacion ? `
                    <div class="personalizar-producto">
                        <strong>Ingredientes incluidos</strong>
                        <p class="nota-personalizacion">La personalización se aplica solo a la unidad que agregues.</p>
                        <div class="lista-ingredientes">
                            ${producto.ingredientes.map(ingrediente => `
                                <div class="ingrediente ${ingredientes.includes(ingrediente) ? '' : 'ingrediente-quitado'}">
                                    <span class="ingrediente-nombre">${escaparHTML(ingrediente)}</span>
                                    <button class="btn-quitar-ingrediente" type="button" data-ingrediente="${escaparHTML(ingrediente)}" ${ingredientes.includes(ingrediente) ? '' : 'disabled'}>
                                        ${ingredientes.includes(ingrediente) ? 'Quitar' : 'Quitado'}
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <button class="btn-restaurar-ingredientes" type="button">Restaurar ingredientes</button>
                    </div>
                ` : ''}
                <p class="producto-precio">Precio: $${producto.precio.toLocaleString('es-CO')}</p>
                <button class="btn-agregar" type="button">Agregar al carrito</button>
            </div>
        </div>
    `;
    if (!esCategoriaSinPersonalizacion) {
        document.querySelectorAll('.btn-quitar-ingrediente').forEach(button => {
            button.addEventListener('click', () => {
                ingredientesPorProducto[tipoNormalizado] = ingredientes.filter(ingrediente => ingrediente !== button.dataset.ingrediente);
                seleccionarProducto(tipoNormalizado);
            });
        });
    }
    const botonRestaurar = document.querySelector('.btn-restaurar-ingredientes');
    if (botonRestaurar) {
        botonRestaurar.addEventListener('click', () => {
            ingredientesPorProducto[tipoNormalizado] = [...producto.ingredientes];
            seleccionarProducto(tipoNormalizado);
        });
    }
    const botonAgregar = document.querySelector('#producto-detalle .btn-agregar');
    if (botonAgregar) {
        botonAgregar.addEventListener('click', evento => {
            agregarProductoConSeguridad(tipoNormalizado, evento.currentTarget);
        });
    }
}

function agregarAlCarrito(tipo) {
    const producto = productos[tipo];
    const ingredientes = ingredientesPorProducto[tipo] || [];
    const itemExistente = carrito.find(item => item.tipo === tipo && JSON.stringify(item.ingredientes) === JSON.stringify(ingredientes));
    const ingredientesQuitados = (producto.ingredientes || []).filter(ingrediente => !ingredientes.includes(ingrediente));
    const nombre = ingredientesQuitados.length
        ? `${producto.nombre} (sin ${ingredientesQuitados.join(', sin ')})`
        : producto.nombre;

    if (itemExistente) {
        itemExistente.cantidad += 1;
    } else {
        carrito.push({ tipo, id: producto.id, nombre, precio: producto.precio, cantidad: 1, ingredientes });
    }

    renderCarrito();
    abrirCarrito();
}

function renderCarrito() {
    const contenedor = document.getElementById('carrito-items');
    const totalCarrito = document.getElementById('total-carrito');
    actualizarBotonCarrito();

    if (carrito.length === 0) {
        contenedor.innerHTML = '<p class="carrito-vacio">Tu carrito está vacío.</p>';
        totalCarrito.textContent = '$0';
        return;
    }

    contenedor.innerHTML = carrito.map(item => `
        <div class="carrito-item">
            <div>
                <strong>${escaparHTML(item.nombre)}</strong>
                <p>${item.cantidad} x $${item.precio.toLocaleString('es-CO')}</p>
            </div>
                <div class="controles-cantidad" aria-label="Cantidad de ${escaparHTML(item.nombre)}">
                    <button class="btn-cantidad" type="button" data-indice="${carrito.indexOf(item)}" data-cambio="-1" aria-label="Reducir ${escaparHTML(item.nombre)}">-</button>
                <span>${item.cantidad}</span>
                    <button class="btn-cantidad" type="button" data-indice="${carrito.indexOf(item)}" data-cambio="1" aria-label="Aumentar ${escaparHTML(item.nombre)}">+</button>
            </div>
        </div>
    `).join('');

    contenedor.querySelectorAll('.btn-cantidad').forEach(button => {
        button.addEventListener('click', () => ajustarCantidad(Number(button.dataset.indice), Number(button.dataset.cambio)));
    });

    const total = carrito.reduce((sum, item) => sum + item.precio * item.cantidad, 0);
    totalCarrito.textContent = `$${total.toLocaleString('es-CO')}`;
}

function ajustarCantidad(indice, cambio) {
    const item = carrito[indice];
    if (!item) return;

    item.cantidad += cambio;
    if (item.cantidad <= 0) {
        carrito.splice(indice, 1);
    }
    renderCarrito();
}

function pagarPedido() {
    if (carrito.length === 0) {
        mostrarMensaje('Agrega al menos un producto antes de pagar.');
        return;
    }

    renderResumenPedido();
    const cliente = obtenerCliente();
    if (cliente) {
        document.getElementById('cliente-nombre').value = cliente.nombre;
        document.getElementById('cliente-telefono').value = cliente.telefono;
        document.getElementById('cliente-direccion').value = cliente.direccion || '';
    }
    document.getElementById('cliente-dialog').showModal();
}

function renderResumenPedido() {
    const resumen = document.getElementById('resumen-pedido');
    const total = carrito.reduce((suma, item) => suma + item.precio * item.cantidad, 0);

    resumen.innerHTML = `
        <h4>Revisa tu pedido</h4>
        <ul>
            ${carrito.map(item => `<li><span>${item.cantidad} x ${escaparHTML(item.nombre)}</span><strong>$${(item.precio * item.cantidad).toLocaleString('es-CO')}</strong></li>`).join('')}
        </ul>
        <div class="resumen-total"><span>Total</span><strong>$${total.toLocaleString('es-CO')}</strong></div>
    `;
}

async function confirmarPedido(evento) {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    const datos = new FormData(formulario);
    const cliente = {
        nombre: datos.get('nombre').trim(),
        telefono: datos.get('telefono').trim(),
        direccion: datos.get('direccion').trim()
    };
    if (!cliente.nombre || !cliente.direccion || !/^\d{7,15}$/.test(cliente.telefono)) {
        mostrarMensaje('Revisa el nombre, la dirección y el teléfono.');
        return;
    }

    const botonConfirmar = formulario.querySelector('[type="submit"]');
    botonConfirmar.disabled = true;
    try {
        const respuesta = await solicitarAPI('/api/pedidos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cliente_nombre: cliente.nombre,
                cliente_telefono: cliente.telefono,
                cliente_direccion: cliente.direccion,
                productos: carrito.map(item => ({
                    tipo: item.tipo,
                    cantidad: item.cantidad,
                    ingredientes: item.ingredientes
                }))
            })
        });
        const respuestaPedido = await respuesta.json();
        if (!respuesta.ok) throw new Error(respuestaPedido.error || 'No se pudo guardar el pedido.');
        guardarCliente(cliente);
        guardarPedidoActivo(respuestaPedido.id, cliente.telefono);
        actualizarSaludo(cliente);
        document.getElementById('cliente-dialog').close();
        formulario.reset();
        mostrarMensaje(`¡Pedido #${respuestaPedido.id} recibido! Tu número de ficha es el #${respuestaPedido.id}. Puedes consultar su estado abajo.`);
        carrito = [];
        renderCarrito();
        cerrarCarrito();
        document.getElementById('seguimiento-id').value = respuestaPedido.id;
        await consultarEstadoPedido(respuestaPedido.id);
        // Lleva al cliente directo al estado de su pedido.
        const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        document.getElementById('seguimiento-pedido').scrollIntoView({
            behavior: reducirMovimiento ? 'auto' : 'smooth',
            block: 'start'
        });
    } finally {
        botonConfirmar.disabled = false;
    }
}

function normalizarEstado(estado) {
    return (estado || 'pendiente').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function telefonoDelPedido(id, telefono = '') {
    if (telefono) return telefono;
    const activo = obtenerPedidoActivo();
    if (activo && activo.id === Number(id) && activo.telefono) return activo.telefono;
    const cliente = obtenerCliente();
    return cliente ? cliente.telefono : '';
}

async function consultarEstadoPedido(id, silencioso = false, telefono = '') {
    const resultado = document.getElementById('resultado-seguimiento');
    if (!silencioso) resultado.innerHTML = '<p>Consultando pedido...</p>';

    const telefonoPedido = telefonoDelPedido(id, telefono);
    const datos = await obtenerPedido(id, telefonoPedido);
    guardarPedidoActivo(datos.id, telefonoPedido);

    document.getElementById('seguimiento-pedido').classList.remove('oculto');
    const estados = ['pendiente', 'preparando', 'en camino', 'entregado'];
    const estadoActual = normalizarEstado(datos.estado);
    const estadoIndex = estados.indexOf(estadoActual);
    const productosPedido = datos.productos.map(producto => `${producto.nombre} x ${producto.cantidad}`).join(', ');
    const mensajesEstado = {
        pendiente: 'Recibimos tu pedido y está pendiente de preparación.',
        preparando: 'Estamos preparando tu pedido.',
        'en camino': 'Tu pedido va en camino.',
        entregado: 'Tu pedido ya fue entregado.',
        cancelado: 'Este pedido fue cancelado. Comunícate con el restaurante si necesitas ayuda.'
    };

    resultado.innerHTML = `
        <div class="seguimiento-cabecera">
            <strong>Pedido #${datos.id}</strong>
            <span>${escaparHTML(etiquetaEstadoPedido(datos.estado))}</span>
        </div>
        <p class="seguimiento-productos">${escaparHTML(productosPedido)}</p>
        <p class="espera-pedido">${mensajesEstado[estadoActual] || 'Consulta el estado de tu pedido.'}</p>
        <div class="pasos-pedido ${estadoActual === 'cancelado' ? 'pedido-cancelado' : ''}">
            ${estados.map((estado, indice) => `
                <span class="paso-pedido ${indice <= estadoIndex ? 'completado' : ''}">
                    <i></i>${escaparHTML(etiquetaEstadoPedido(estado))}
                </span>
            `).join('')}
        </div>
        <strong class="seguimiento-total">Total: $${datos.total.toLocaleString('es-CO')}</strong>
    `;

    if (ultimoEstadoPedido && ultimoEstadoPedido.id === datos.id && ultimoEstadoPedido.estado !== estadoActual) {
        mostrarMensaje(`Tu pedido #${datos.id} ahora está: ${etiquetaEstadoPedido(datos.estado)}.`);
    }
    ultimoEstadoPedido = { id: datos.id, estado: estadoActual };
    programarSeguimiento(datos.id, estadoActual);
    return datos;
}

function programarSeguimiento(id, estado) {
    window.clearTimeout(temporizadorSeguimiento);
    if (estado === 'entregado' || estado === 'cancelado') return;
    temporizadorSeguimiento = window.setTimeout(() => {
        consultarEstadoPedido(id, true).catch(error => {
            if (error.estado === 404) {
                olvidarPedidoActivo();
                return;
            }
            programarSeguimiento(id, estado);
        });
    }, INTERVALO_SEGUIMIENTO_MS);
}

function etiquetaEstadoPedido(estado) {
    return estado === 'preparando' ? 'En preparación' : estado.replace(/^./, letra => letra.toUpperCase());
}

function mostrarMensaje(texto) {
    const mensaje = document.getElementById('mensaje-pedido');
    mensaje.textContent = texto;
    mensaje.classList.add('visible');
    window.clearTimeout(mostrarMensaje.temporizador);
    mostrarMensaje.temporizador = window.setTimeout(() => mensaje.classList.remove('visible'), 4000);
}

document.getElementById('cerrar-carrito')?.addEventListener('click', cerrarCarrito);
document.getElementById('abrir-carrito')?.addEventListener('click', abrirCarrito);
document.getElementById('btn-pagar').addEventListener('click', () => {
    try {
        pagarPedido();
    } catch (error) {
        mostrarMensaje(error.message);
    }
});
document.getElementById('cliente-form').addEventListener('submit', evento => {
    confirmarPedido(evento).catch(error => mostrarMensaje(error.message));
});
document.getElementById('cliente-telefono').addEventListener('input', evento => {
    evento.currentTarget.value = evento.currentTarget.value.replace(/\D/g, '');
});
document.getElementById('cancelar-pedido').addEventListener('click', () => document.getElementById('cliente-dialog').close());
document.getElementById('seguimiento-form').addEventListener('submit', evento => {
    evento.preventDefault();
    const id = document.getElementById('seguimiento-id').value;
    const telefono = document.getElementById('seguimiento-telefono').value.trim();
    consultarEstadoPedido(id, false, telefono).then(cerrarCarrito).catch(error => {
        document.getElementById('resultado-seguimiento').innerHTML = `<p class="seguimiento-error">${escaparHTML(error.message)}</p>`;
    });
});
let seguimientoYaRevisado = false;
(document.getElementById('btn-ver-menu') || document.querySelector('.contenido button')).addEventListener('click', () => {
    mostrarMenu();
    if (!seguimientoYaRevisado) {
        seguimientoYaRevisado = true;
        recuperarPedidoActivo();
    }
});
const REGEX_NOMBRE_APELLIDO = /^[\p{L}'’.-]{2,}(\s+[\p{L}'’.-]{2,})+$/u;

function mostrarErrorRegistro(texto) {
    let error = document.getElementById('registro-error');
    if (!error) {
        // Si el HTML no trae el aviso de error, se crea dentro del cuadro para que se vea.
        error = document.createElement('p');
        error.id = 'registro-error';
        error.setAttribute('role', 'alert');
        error.style.cssText = 'margin:0;min-height:18px;color:#ff8a80;font-size:13px';
        const acciones = document.querySelector('#registro-form .cliente-acciones');
        acciones.parentNode.insertBefore(error, acciones);
    }
    error.textContent = texto;
}

function abrirRegistro(vacio = false) {
    const cliente = obtenerCliente();
    document.getElementById('registro-nombre').value = !vacio && cliente ? cliente.nombre : '';
    mostrarErrorRegistro('');
    document.getElementById('registro-dialog').showModal();
}

function limpiarSeguimiento() {
    window.clearTimeout(temporizadorSeguimiento);
    ultimoEstadoPedido = null;
    olvidarPedidoActivo();
    document.getElementById('seguimiento-id').value = '';
    document.getElementById('seguimiento-telefono').value = '';
    document.getElementById('resultado-seguimiento').innerHTML = '';
    document.getElementById('seguimiento-pedido').classList.add('oculto');
}

document.getElementById('registro-form').addEventListener('submit', evento => {
    evento.preventDefault();
    const datos = new FormData(evento.currentTarget);
    const nombre = datos.get('nombre').trim().replace(/\s+/g, ' ');
    if (!REGEX_NOMBRE_APELLIDO.test(nombre)) {
        mostrarErrorRegistro('Escribe tu nombre y tu apellido (por ejemplo: Juan Pérez).');
        return;
    }
    mostrarErrorRegistro('');
    const anterior = obtenerCliente();
    const esOtraPersona = anterior && REGEX_NOMBRE_APELLIDO.test(anterior.nombre)
        && anterior.nombre.toLowerCase() !== nombre.toLowerCase();
    if (esOtraPersona) {
        // Otra persona en el mismo dispositivo: no se conservan los datos ni el pedido de la anterior.
        limpiarSeguimiento();
    }
    const cliente = anterior && !esOtraPersona
        ? { ...anterior, nombre }
        : { nombre, telefono: '', direccion: '' };
    guardarCliente(cliente);
    actualizarSaludo(cliente);
    document.getElementById('registro-dialog').close();
});
const botonCambiarNombre = document.getElementById('cambiar-nombre');
if (botonCambiarNombre) botonCambiarNombre.addEventListener('click', () => abrirRegistro());
document.getElementById('registro-dialog').addEventListener('cancel', evento => {
    evento.preventDefault();
});

document.querySelectorAll('.btn-seleccion').forEach(btn => {
    btn.addEventListener('click', () => seleccionarProducto(btn.dataset.tipo));
});
document.querySelectorAll('.tarjeta').forEach(tarjeta => {
    tarjeta.addEventListener('click', () => seleccionarProducto(tarjeta.dataset.tipo));
    tarjeta.addEventListener('keydown', evento => {
        if (evento.key === 'Enter' || evento.key === ' ') {
            evento.preventDefault();
            seleccionarProducto(tarjeta.dataset.tipo);
        }
    });
});

async function iniciarTienda() {
    // Cada vez que se abre o se recarga la página se pide de nuevo el nombre y el apellido.
    abrirRegistro(true);
    try {
        await cargarMenu();
        Object.keys(productos).forEach(tipo => {
            if (productos[tipo].ingredientes) ingredientesPorProducto[tipo] = [...productos[tipo].ingredientes];
        });
        renderListaHamburguesas('hamburguesas');
        seleccionarProducto('hamburguesas');
    } catch (error) {
        mostrarMensaje(error.message);
    }
    renderCarrito();
}

function recuperarPedidoActivo() {
    const pedidoActivo = obtenerPedidoActivo();
    if (!pedidoActivo) return;
    document.getElementById('seguimiento-id').value = pedidoActivo.id;
    document.getElementById('seguimiento-telefono').value = telefonoDelPedido(pedidoActivo.id);
    consultarEstadoPedido(pedidoActivo.id)
        .then(() => {
            // Se quitó el scrollIntoView: bajaba la página hasta el seguimiento al pulsar "Ver Menú".
        })
        .catch(error => {
            if (error.estado === 404) olvidarPedidoActivo();
        });
}

iniciarTienda();