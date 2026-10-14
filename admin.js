const estados = ['pendiente', 'preparando', 'en camino', 'entregado', 'cancelado'];
const API_BASE = ['127.0.0.1', 'localhost'].includes(location.hostname) && location.port === '5500'
    ? `http://${location.hostname}:5000`
    : '';

function solicitarAPI(ruta, opciones = {}) {
    return fetch(`${API_BASE}${ruta}`, { credentials: 'include', ...opciones });
}

async function obtenerPedidos() {
    const respuesta = await solicitarAPI('/api/pedidos');
    if (!respuesta.ok) {
        const datos = await respuesta.json();
        throw new Error(datos.error || 'No se pudieron consultar los pedidos.');
    }
    return respuesta.json();
}

function escaparHTML(valor) {
    return String(valor).replace(/[&<>"']/g, caracter => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[caracter]);
}

function etiquetaEstado(estado) {
    return estado === 'preparando' ? 'En preparación' : estado.replace(/^./, letra => letra.toUpperCase());
}

function formatearFecha(fecha) {
    return new Date(fecha).toLocaleString('es-CO', {
        dateStyle: 'long',
        timeStyle: 'short'
    });
}

function mostrarMensaje(texto, error = false) {
    const mensaje = document.getElementById('admin-mensaje');
    mensaje.textContent = texto;
    mensaje.className = `admin-mensaje ${error ? 'error' : 'visible'}`;
}

function renderPedidos(pedidos) {
    const lista = document.getElementById('lista-pedidos');
    if (pedidos.length === 0) {
        lista.innerHTML = '<p class="sin-pedidos">Todavía no hay pedidos registrados.</p>';
        return;
    }

    lista.innerHTML = pedidos.map(pedido => `
        <article class="pedido-admin">
            <div class="pedido-admin-top">
                <div><span class="pedido-numero">Pedido #${pedido.id}</span><h2>${escaparHTML(pedido.cliente_nombre)}</h2></div>
                <select class="estado-pedido" data-id="${pedido.id}" aria-label="Estado del pedido ${pedido.id}">
                    ${estados.map(estado => `<option value="${estado}" ${estado === pedido.estado ? 'selected' : ''}>${etiquetaEstado(estado)}</option>`).join('')}
                </select>
            </div>
            <p class="productos-pedido">${pedido.productos.map(producto => `${escaparHTML(producto.nombre)} x ${Number(producto.cantidad)}`).join(', ')}</p>
            <div class="datos-pedido"><span>${escaparHTML(pedido.cliente_telefono)}</span><span>${escaparHTML(pedido.cliente_direccion)}</span><strong>$${Number(pedido.total).toLocaleString('es-CO')}</strong></div>
            <time>${pedido.fecha ? escaparHTML(formatearFecha(pedido.fecha)) : ''}</time>
        </article>
    `).join('');

    lista.querySelectorAll('.estado-pedido').forEach(select => {
        select.addEventListener('change', () => cambiarEstado(select));
    });
}

async function cargarPedidos() {
    renderPedidos(await obtenerPedidos());
}

async function cambiarEstado(select) {
    select.disabled = true;
    try {
        const respuesta = await solicitarAPI(`/api/pedidos/${select.dataset.id}/estado`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estado: select.value })
        });
        const pedido = await respuesta.json();
        if (!respuesta.ok) throw new Error(pedido.error || 'No se pudo actualizar el pedido.');
        mostrarMensaje(`Pedido #${pedido.id} actualizado: ${etiquetaEstado(pedido.estado)}.`);
    } catch (error) {
        mostrarMensaje(error.message, true);
        cargarPedidos().catch(() => {});
    } finally {
        select.disabled = false;
    }
}

document.getElementById('admin-login-form').addEventListener('submit', async evento => {
    evento.preventDefault();
    const error = document.getElementById('admin-login-error');
    const boton = evento.currentTarget.querySelector('[type="submit"]');
    boton.disabled = true;
    error.textContent = '';
    try {
        const respuesta = await solicitarAPI('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: document.getElementById('admin-password').value })
        });
        const datos = await respuesta.json();
        if (!respuesta.ok) throw new Error(datos.error || 'No se pudo iniciar sesión.');
        mostrarPanel();
    } catch (fallo) {
        error.textContent = fallo.message;
    } finally {
        boton.disabled = false;
    }
});

function mostrarPanel() {
    document.getElementById('admin-login').classList.add('oculto');
    document.getElementById('admin-panel').classList.remove('oculto');
    cargarPedidos().catch(error => mostrarMensaje(error.message, true));
}

document.getElementById('admin-logout').addEventListener('click', async () => {
    await solicitarAPI('/api/admin/logout', { method: 'POST' });
    document.getElementById('admin-panel').classList.add('oculto');
    document.getElementById('admin-login').classList.remove('oculto');
    document.getElementById('admin-password').value = '';
});

solicitarAPI('/api/admin/sesion')
    .then(respuesta => respuesta.json())
    .then(datos => {
        if (datos.autenticado) mostrarPanel();
    })
    .catch(() => mostrarMensaje('No se pudo verificar la sesión.', true));

document.getElementById('actualizar-pedidos').addEventListener('click', () => {
    cargarPedidos()
        .then(() => mostrarMensaje('Pedidos actualizados.'))
        .catch(error => mostrarMensaje(error.message, true));
});

// ---------- Pestañas y modificación de precios ----------
let menuAdmin = [];

function sinTildes(texto) {
    return String(texto).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function cambiarVista(vista) {
    ['pedidos', 'precios', 'agregar'].forEach(v => { document.getElementById(`vista-${v}`).hidden = v !== vista; });
    document.querySelectorAll('.admin-tab').forEach(boton => boton.classList.toggle('activo', boton.dataset.vista === vista));
    if (vista === 'precios') cargarPrecios().catch(error => mostrarMensaje(error.message, true));
}

async function cargarPrecios() {
    const respuesta = await solicitarAPI('/api/admin/menu');
    const datos = await respuesta.json();
    if (!respuesta.ok) throw new Error(datos.error || 'No se pudo cargar el menú.');
    menuAdmin = datos;
    renderPrecios();
}

function renderPrecios() {
    const filtro = sinTildes(document.getElementById('precios-buscar').value.trim());
    const productos = menuAdmin.filter(p => sinTildes(p.nombre).includes(filtro));
    document.getElementById('lista-precios').innerHTML = productos.length ? productos.map(p => `
        <div class="precio-fila" data-clave="${escaparHTML(p.clave)}">
            <span class="precio-nombre">${escaparHTML(p.nombre)}</span>
            <input class="precio-input" type="text" inputmode="numeric" maxlength="7" value="${Number(p.precio).toLocaleString('es-CO')}" aria-label="Precio de ${escaparHTML(p.nombre)}">
            <label class="precio-disponible"><input class="disp-input" type="checkbox" ${p.disponible ? 'checked' : ''}> Disponible</label>
            <button class="precio-guardar" type="button">Guardar</button>
            <button class="precio-eliminar" type="button">Eliminar producto</button>
        </div>`).join('') : '<p class="sin-pedidos">No hay productos con ese nombre.</p>';
}

async function guardarProducto(fila) {
    const boton = fila.querySelector('.precio-guardar');
    boton.disabled = true;
    try {
        const respuesta = await solicitarAPI('/api/admin/menu', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                clave: fila.dataset.clave,
                precio: leerPrecio(fila.querySelector('.precio-input').value),
                disponible: fila.querySelector('.disp-input').checked
            })
        });
        const producto = await respuesta.json();
        if (!respuesta.ok) throw new Error(producto.error || 'No se pudo guardar el producto.');
        menuAdmin = menuAdmin.map(p => p.clave === producto.clave ? producto : p);
        mostrarMensaje(`${producto.nombre}: $${producto.precio.toLocaleString('es-CO')}${producto.disponible ? '' : ' (no disponible)'} guardado.`);
    } catch (error) {
        mostrarMensaje(error.message, true);
    } finally {
        boton.disabled = false;
    }
}

document.querySelectorAll('.admin-tab').forEach(boton => boton.addEventListener('click', () => cambiarVista(boton.dataset.vista)));
document.getElementById('precios-buscar').addEventListener('input', renderPrecios);
document.getElementById('lista-precios').addEventListener('click', evento => {
    const boton = evento.target.closest('.precio-guardar');
    if (boton) guardarProducto(boton.closest('.precio-fila'));
    const eliminar = evento.target.closest('.precio-eliminar');
    if (eliminar) eliminarProducto(eliminar.closest('.precio-fila'));
});

// ---------- Agregar comida ----------
const camposIngredientes = document.getElementById('ingredientes-campos');
const inputImagen = document.getElementById('nuevo-imagen');

function envolverIngrediente(input) {
    const envoltorio = document.createElement('div');
    envoltorio.className = 'ingrediente-campo';
    input.replaceWith(envoltorio);
    const quitar = document.createElement('button');
    quitar.type = 'button';
    quitar.className = 'quitar-ingrediente';
    quitar.textContent = '×';
    quitar.setAttribute('aria-label', 'Quitar ingrediente');
    envoltorio.append(input, quitar);
}

function nuevoCampoIngrediente() {
    const input = document.createElement('input');
    input.type = 'text';
    input.maxLength = 40;
    camposIngredientes.insertBefore(input, document.getElementById('mas-ingrediente'));
    envolverIngrediente(input);
    return input;
}

const selectCategoria = document.getElementById('nuevo-categoria');
const etiquetaIngredientes = camposIngredientes.previousElementSibling;
const etiquetaPrecioNuevo = document.querySelector('label[for="nuevo-precio"]');

// Campo "Tamaño (mL)", solo visible para bebidas
const etiquetaTamano = document.createElement('label');
etiquetaTamano.htmlFor = 'nuevo-tamano';
etiquetaTamano.textContent = 'Tamaño (mL)';
const campoTamano = document.createElement('input');
campoTamano.id = 'nuevo-tamano';
campoTamano.type = 'text';
campoTamano.inputMode = 'numeric';
campoTamano.maxLength = 4;
campoTamano.placeholder = 'Ej: 400';
etiquetaPrecioNuevo.before(etiquetaTamano, campoTamano);
campoTamano.addEventListener('input', () => { campoTamano.value = campoTamano.value.replace(/\D/g, ''); });

function esBebida() {
    return selectCategoria.value === 'bebidas';
}

function aplicarCategoria() {
    const bebida = esBebida();
    etiquetaIngredientes.hidden = bebida;
    camposIngredientes.hidden = bebida;
    etiquetaTamano.hidden = !bebida;
    campoTamano.hidden = !bebida;
    campoTamano.required = bebida;
    etiquetaPrecioNuevo.textContent = bebida ? 'Valor' : 'Agregar precio';
    document.getElementById('nuevo-nombre').placeholder = bebida ? 'Ej: Coca-Cola Original' : 'Poner título';
    actualizarIngredientes();
}

selectCategoria.addEventListener('change', aplicarCategoria);

function actualizarIngredientes() {
    const campos = camposIngredientes.querySelectorAll('.ingrediente-campo');
    campos.forEach((campo, i) => {
        const input = campo.querySelector('input');
        input.placeholder = `Ingrediente ${i + 1}`;
        input.required = i === 0 && !esBebida();
        campo.querySelector('.quitar-ingrediente').hidden = campos.length === 1;
    });
}

document.getElementById('mas-ingrediente').addEventListener('click', () => {
    if (camposIngredientes.querySelectorAll('.ingrediente-campo').length >= 15) return;
    const campo = nuevoCampoIngrediente();
    actualizarIngredientes();
    campo.focus();
});

camposIngredientes.addEventListener('click', evento => {
    const quitar = evento.target.closest('.quitar-ingrediente');
    if (!quitar) return;
    quitar.closest('.ingrediente-campo').remove();
    actualizarIngredientes();
});

camposIngredientes.querySelectorAll(':scope > input').forEach(envolverIngrediente);
aplicarCategoria();

function limpiarFormularioAgregar() {
    document.getElementById('form-agregar').reset();
    camposIngredientes.querySelectorAll('.ingrediente-campo').forEach((campo, i) => { if (i >= 4) campo.remove(); });
    while (camposIngredientes.querySelectorAll('.ingrediente-campo').length < 4) nuevoCampoIngrediente();
    actualizarIngredientes();
    document.getElementById('nuevo-preview').hidden = true;
    document.getElementById('nuevo-subir-texto').hidden = false;
    aplicarCategoria();
}

inputImagen.addEventListener('change', () => {
    const archivo = inputImagen.files[0];
    const vista = document.getElementById('nuevo-preview');
    if (!archivo) return limpiarFormularioAgregar();
    vista.src = URL.createObjectURL(archivo);
    vista.hidden = false;
    document.getElementById('nuevo-subir-texto').hidden = true;
});

document.getElementById('form-agregar').addEventListener('submit', async evento => {
    evento.preventDefault();
    const boton = evento.currentTarget.querySelector('[type="submit"]');
    boton.disabled = true;
    const datos = new FormData();
    datos.append('nombre', document.getElementById('nuevo-nombre').value);
    datos.append('categoria', document.getElementById('nuevo-categoria').value);
    datos.append('precio', String(leerPrecio(document.getElementById('nuevo-precio').value)));
    datos.append('imagen', inputImagen.files[0]);
    if (esBebida()) datos.append('tamano', campoTamano.value);
    else camposIngredientes.querySelectorAll('input').forEach(campo => datos.append('ingredientes', campo.value));
    try {
        const respuesta = await solicitarAPI('/api/admin/menu/nuevo', { method: 'POST', body: datos });
        const producto = await respuesta.json();
        if (!respuesta.ok) throw new Error(producto.error || 'No se pudo agregar el producto.');
        mostrarMensaje(`${producto.nombre} se agregó al menú por $${producto.precio.toLocaleString('es-CO')}.`);
        limpiarFormularioAgregar();
    } catch (error) {
        mostrarMensaje(error.message, true);
    } finally {
        boton.disabled = false;
    }
});

// ---------- Precios con separador de miles (28.000 = 28000) ----------
function leerPrecio(texto) {
    return Number(String(texto).replace(/\D/g, ''));
}

function formatearPrecioEnCampo(campo) {
    const valor = leerPrecio(campo.value);
    campo.value = valor ? valor.toLocaleString('es-CO') : '';
}

const campoPrecioNuevo = document.getElementById('nuevo-precio');
campoPrecioNuevo.type = 'text';
campoPrecioNuevo.inputMode = 'numeric';
campoPrecioNuevo.maxLength = 7;
['min', 'max', 'step'].forEach(atributo => campoPrecioNuevo.removeAttribute(atributo));
campoPrecioNuevo.addEventListener('input', () => formatearPrecioEnCampo(campoPrecioNuevo));
document.getElementById('lista-precios').addEventListener('input', evento => {
    if (evento.target.classList.contains('precio-input')) formatearPrecioEnCampo(evento.target);
});

function obtenerDialogoEliminar() {
    let dialogo = document.getElementById('confirmar-eliminar');
    if (dialogo) return dialogo;
    dialogo = document.createElement('dialog');
    dialogo.id = 'confirmar-eliminar';
    dialogo.className = 'confirmar-eliminar';
    dialogo.setAttribute('aria-labelledby', 'confirmar-titulo');
    dialogo.innerHTML = `
        <h3 id="confirmar-titulo">¿Seguro que deseas eliminar <span id="confirmar-nombre"></span>?</h3>
        <p>Si lo eliminas no se podrá recuperar.</p>
        <div class="confirmar-acciones">
            <button type="button" id="confirmar-cancelar" class="confirmar-cancelar">Cancelar</button>
            <button type="button" id="confirmar-aceptar" class="confirmar-aceptar">Sí, eliminar</button>
        </div>`;
    document.body.appendChild(dialogo);
    return dialogo;
}

function confirmarEliminacion(nombre) {
    return new Promise(resolver => {
        const dialogo = obtenerDialogoEliminar();
        dialogo.querySelector('#confirmar-nombre').textContent = `"${nombre}"`;
        const aceptar = dialogo.querySelector('#confirmar-aceptar');
        const cancelar = dialogo.querySelector('#confirmar-cancelar');
        const cerrar = resultado => {
            aceptar.removeEventListener('click', alAceptar);
            cancelar.removeEventListener('click', alCancelar);
            dialogo.removeEventListener('cancel', alCancelar);
            dialogo.close();
            resolver(resultado);
        };
        const alAceptar = () => cerrar(true);
        const alCancelar = evento => { if (evento) evento.preventDefault(); cerrar(false); };
        aceptar.addEventListener('click', alAceptar);
        cancelar.addEventListener('click', alCancelar);
        dialogo.addEventListener('cancel', alCancelar);
        dialogo.showModal();
        cancelar.focus();
    });
}

async function eliminarProducto(fila) {
    const nombre = fila.querySelector('.precio-nombre').textContent;
    try {
        if (!await confirmarEliminacion(nombre)) return;
        const respuesta = await solicitarAPI('/api/admin/menu/eliminar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clave: fila.dataset.clave })
        });
        const datos = await respuesta.json();
        if (!respuesta.ok) throw new Error(datos.error || 'No se pudo eliminar el producto.');
        menuAdmin = menuAdmin.filter(p => p.clave !== datos.clave);
        renderPrecios();
        mostrarMensaje(`${nombre} se eliminó del menú.`);
    } catch (error) {
        mostrarMensaje(error.message, true);
    }
}