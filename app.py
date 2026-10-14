from datetime import datetime
from contextlib import contextmanager
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import unicodedata
from collections import defaultdict, deque
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_from_directory, session

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / 'pedidos.db'
MENU = {
    'hamburguesa Clasica': {
        'id': 1, 'nombre': 'Clásica', 'descripcion': 'Carne de res, queso y vegetales frescos',
        'precio': 18000,
        'detalle': 'Carne de res, queso, lechuga, tomate, cebolla y salsa de la casa.',
        'ingredientes': ['Carne de res', 'Queso', 'Lechuga', 'Tomate', 'Cebolla', 'Salsa de la casa'],
    },
    'hamburguesa Cheeseburger': {
        'id': 2, 'nombre': 'Cheeseburger', 'descripcion': 'Carne de res, doble queso cheddar, cebolla grillada y salsa especial',
        'precio': 21000,
        'detalle': 'Carne de res, doble queso cheddar, cebolla grillada y salsa especial.',
        'ingredientes': ['Carne de res', 'Queso cheddar', 'Cebolla grillada', 'Salsa especial'],
    },
    'hamburguesa Bacon': {
        'id': 3, 'nombre': 'Bacon', 'descripcion': 'Carne de res, queso cheddar, tocineta, lechuga, tomate y BBQ',
        'precio': 24000,
        'detalle': 'Carne de res, queso cheddar, tocineta, lechuga, tomate y BBQ.',
        'ingredientes': ['Carne de res', 'Queso cheddar', 'Tocineta', 'Lechuga', 'Tomate', 'BBQ'],
    },
    'hamburguesa Doble Bacon': {
        'id': 11, 'nombre': 'Doble Bacon', 'descripcion': 'Dos carnes, doble cheddar, doble tocineta, cebolla y BBQ',
        'precio': 32000,
        'detalle': 'Dos carnes, doble cheddar, doble tocineta, cebolla y BBQ.',
        'ingredientes': ['Carne de res', 'Cheddar', 'Tocineta', 'Cebolla', 'BBQ'],
    },
    'hamburguesa Ranchera': {
        'id': 12, 'nombre': 'Ranchera', 'descripcion': 'Carne, queso, chorizo, tocineta, maíz, cebolla y salsa BBQ',
        'precio': 29000,
        'detalle': 'Carne, queso, chorizo, tocineta, maíz, cebolla y salsa BBQ.',
        'ingredientes': ['Carne de res', 'Queso', 'Chorizo', 'Tocineta', 'Maíz', 'Cebolla', 'Salsa BBQ'],
    },
    'hamburguesa8': {
        'id': 13, 'nombre': 'Campesina', 'descripcion': 'Carne, queso, huevo, chorizo, aguacate, tomate y cebolla',
        'precio': 30000,
        'detalle': 'Carne, queso, huevo, chorizo, aguacate, tomate y cebolla.',
        'ingredientes': ['Carne de res', 'Queso', 'Huevo', 'Chorizo', 'Aguacate', 'Tomate', 'Cebolla'],
    },
    'hamburguesa9': {
        'id': 14, 'nombre': 'Colombiana', 'descripcion': 'Carne, queso, tocineta, huevo, maíz, aguacate, ripio de papa y salsa de piña',
        'precio': 32000,
        'detalle': 'Carne, queso, tocineta, huevo, maíz, aguacate, ripio de papa y salsa de piña.',
        'ingredientes': ['Carne de res', 'Queso', 'Tocineta', 'Huevo', 'Maíz', 'Aguacate', 'Ripio de papa', 'Salsa de piña'],
    },
    'hamburguesa4': {
        'id': 4, 'nombre': 'Hawaiana', 'descripcion': 'Carne de res, queso, jamón, piña asada, lechuga y salsa rosada',
        'precio': 23000,
        'detalle': 'Carne de res, queso, jamón, piña asada, lechuga y salsa rosada.',
        'ingredientes': ['Carne de res', 'Queso', 'Jamón', 'Piña asada', 'Lechuga', 'Salsa rosada'],
    },
    'mexicana': {
        'id': 5, 'nombre': 'Mexicana', 'descripcion': 'Carne de res, queso, guacamole, pico de gallo, jalapeños y salsa mexicana',
        'precio': 26000,
        'detalle': 'Carne de res, queso, guacamole, pico de gallo, jalapeños y salsa mexicana.',
        'ingredientes': ['Carne de res', 'Queso', 'Guacamole', 'Pico de gallo', 'Jalapeños', 'Salsa mexicana'],
    },
    'criolla': {
        'id': 6, 'nombre': 'Criolla', 'descripcion': 'Carne de res, queso, huevo frito, cebolla grillada, tomate y salsa de la casa',
        'precio': 25000,
        'detalle': 'Carne de res, queso, huevo frito, cebolla grillada, tomate y salsa de la casa.',
        'ingredientes': ['Carne de res', 'Queso', 'Huevo frito', 'Cebolla grillada', 'Tomate', 'Salsa de la casa'],
    },
    'hamburguesa5': {
        'id': 8, 'nombre': 'Cebolla Caramelizada', 'descripcion': 'Carne de res, queso, cebolla caramelizada, lechuga y salsa BBQ',
        'precio': 24000,
        'detalle': 'Carne de res, queso, cebolla caramelizada, lechuga y salsa BBQ.',
        'ingredientes': ['Carne de res', 'Queso', 'Cebolla caramelizada', 'Lechuga', 'Salsa BBQ'],
    },
    'hamburguesa10': {
        'id': 9, 'nombre': 'Tres Quesos', 'descripcion': 'Carne de res, cheddar, mozzarella, queso crema y salsa de queso',
        'precio': 27000,
        'detalle': 'Carne de res, cheddar, mozzarella, queso crema y salsa de queso.',
        'ingredientes': ['Carne de res', 'Cheddar', 'Mozzarella', 'Queso crema', 'Salsa de queso'],
    },
    'hamburguesa11': {
        'id': 10, 'nombre': 'Doble Carne', 'descripcion': 'Dos carnes de res, doble queso, cebolla, pepinillos y salsa especial',
        'precio': 29000,
        'detalle': 'Dos carnes de res, doble queso, cebolla, pepinillos y salsa especial.',
        'ingredientes': ['Carne de res', 'Queso', 'Cebolla', 'Pepinillos', 'Salsa especial'],
    },
    'llanera': {
        'id': 18, 'nombre': 'Llanera', 'descripcion': 'Carne de res, carne llanera, queso, chimichurri, cebolla y guacamole',
        'precio': 35000,
        'detalle': 'Carne de res, carne llanera, queso, chimichurri, cebolla y guacamole.',
        'ingredientes': ['Carne de res', 'Carne llanera', 'Queso', 'Chimichurri', 'Cebolla', 'Guacamole'],
    },
    'bbq_pulled_pork': {
        'id': 19, 'nombre': 'BBQ Pulled Pork', 'descripcion': 'Carne de cerdo desmechada, queso, cebolla morada, BBQ y ensalada de repollo',
        'precio': 28000,
        'detalle': 'Carne de cerdo desmechada, queso, cebolla morada, BBQ y ensalada de repollo.',
        'ingredientes': ['Carne de cerdo desmechada', 'Queso', 'Cebolla morada', 'BBQ', 'Ensalada de repollo'],
    },
    'chicken_crispy': {
        'id': 20, 'nombre': 'Chicken Crispy', 'descripcion': 'Pollo apanado, queso, lechuga, tomate, pepinillos y salsa de ajo',
        'precio': 24000,
        'detalle': 'Pollo apanado, queso, lechuga, tomate, pepinillos y salsa de ajo.',
        'ingredientes': ['Pollo apanado', 'Queso', 'Lechuga', 'Tomate', 'Pepinillos', 'Salsa de ajo'],
    },
    'pollo_bbq': {
        'id': 21, 'nombre': 'Pollo BBQ', 'descripcion': 'Pollo a la plancha, queso, tocineta, cebolla caramelizada y BBQ',
        'precio': 25000,
        'detalle': 'Pollo a la plancha, queso, tocineta, cebolla caramelizada y BBQ.',
        'ingredientes': ['Pollo a la plancha', 'Queso', 'Tocineta', 'Cebolla caramelizada', 'BBQ'],
    },
}
# ---------------------------------------------------------------------------
# SALCHIPAPAS
# La foto se busca sola en la carpeta /salchipapas: sirve cualquier archivo cuyo
# nombre termine en el número (ej. "La Clásica 1.jpg", "La Tropical 11.PNG").
# (clave, número de foto, nombre, descripción, precio, ingredientes)
# ---------------------------------------------------------------------------
SALCHIPAPAS_DIR = BASE_DIR / 'salchipapas'
SALCHIPAPAS = [
    ('salchipapas', 1, 'Salchipapa Clásica', 'Papa francesa, salchicha, queso y salsas', 12000,
     ['Papa francesa', 'Salchicha', 'Queso', 'Salsas']),
    ('salchipapas_gratinada', 2, 'Salchipapa Gratinada', 'Papa, salchicha, queso gratinado y salsas', 15000,
     ['Papa', 'Salchicha', 'Queso gratinado', 'Salsas']),
    ('salchipapas_cheddar_tocineta', 3, 'Salchipapa Cheddar & Tocineta', 'Papa, salchicha, cheddar, tocineta y salsas', 18000,
     ['Papa', 'Salchicha', 'Cheddar', 'Tocineta', 'Salsas']),
    ('salchipapas_pollo', 4, 'Salchipapa Pollo', 'Papa, salchicha, pollo desmechado, queso y salsas', 20000,
     ['Papa', 'Salchicha', 'Pollo desmechado', 'Queso', 'Salsas']),
    ('salchipapas_carne', 5, 'Salchipapa Carne', 'Papa, salchicha, carne desmechada, queso y salsas', 21000,
     ['Papa', 'Salchicha', 'Carne desmechada', 'Queso', 'Salsas']),
    ('salchipapas_mixta', 6, 'Salchipapa Mixta', 'Papa, salchicha, pollo, carne, queso y salsas', 24000,
     ['Papa', 'Salchicha', 'Pollo', 'Carne', 'Queso', 'Salsas']),
    ('salchipapas_ranchera', 7, 'Salchipapa Ranchera', 'Papa, salchicha, pollo, chorizo, tocineta, queso y lechuga', 25000,
     ['Papa', 'Salchicha', 'Pollo', 'Chorizo', 'Tocineta', 'Queso', 'Lechuga']),
    ('salchipapas_criolla', 8, 'Salchipapa Criolla', 'Papa, salchicha, chorizo, maíz, maduro, queso y lechuga', 25000,
     ['Papa', 'Salchicha', 'Chorizo', 'Maíz', 'Maduro', 'Queso', 'Lechuga']),
    ('salchipapas_costena', 9, 'Salchipapa Costeña', 'Papa, salchicha, chorizo, butifarra, queso costeño, maíz y salsas', 27000,
     ['Papa', 'Salchicha', 'Chorizo', 'Butifarra', 'Queso costeño', 'Maíz', 'Salsas']),
    ('salchipapas_mexicana', 10, 'Salchipapa Mexicana', 'Papa, salchicha, carne, jalapeño, maíz, queso y salsa especial', 28000,
     ['Papa', 'Salchicha', 'Carne', 'Jalapeño', 'Maíz', 'Queso', 'Salsa especial']),
    ('salchipapas_hawaiana', 11, 'Salchipapa Hawaiana', 'Papa, salchicha, pollo, piña, queso, jamón y salsas', 28000,
     ['Papa', 'Salchicha', 'Pollo', 'Piña', 'Queso', 'Jamón', 'Salsas']),
    ('salchipapas_bbq', 12, 'Salchipapa BBQ', 'Papa, salchicha, pollo, tocineta, queso y salsa BBQ', 29000,
     ['Papa', 'Salchicha', 'Pollo', 'Tocineta', 'Queso', 'Salsa BBQ']),
    ('salchipapas_especial', 13, 'Salchipapa Especial', 'Papa, salchicha, pollo, carne, chorizo, queso, maíz y salsas', 32000,
     ['Papa', 'Salchicha', 'Pollo', 'Carne', 'Chorizo', 'Queso', 'Maíz', 'Salsas']),
    ('salchipapas_porky', 14, 'Salchipapa Porky', 'Papa, salchicha, tocineta, chicharrón, costilla, chorizo, queso y maduro', 38000,
     ['Papa', 'Salchicha', 'Tocineta', 'Chicharrón', 'Costilla', 'Chorizo', 'Queso', 'Maduro']),
    ('salchipapas_festival', 15, 'Salchipapa Festival', 'Papa, salchicha, carne, pollo, chorizo, alitas, tocineta, maduro, maíz, queso y salsas', 45000,
     ['Papa', 'Salchicha', 'Carne', 'Pollo', 'Chorizo', 'Alitas', 'Tocineta', 'Maduro', 'Maíz', 'Queso', 'Salsas']),
]


def imagen_salchipapa(numero):
    patron = re.compile(rf'(?:^|\D){numero}\.(?:jpe?g|png|webp)$', re.IGNORECASE)
    if SALCHIPAPAS_DIR.is_dir():
        for archivo in sorted(SALCHIPAPAS_DIR.iterdir()):
            if patron.search(archivo.name):
                return f'/salchipapas/{archivo.name}'
    print(f'[AVISO] No encontré la foto número {numero} en {SALCHIPAPAS_DIR}')
    return ''


for _clave, _numero, _nombre, _descripcion, _precio, _ingredientes in SALCHIPAPAS:
    MENU[_clave] = {
        'id': 100 + _numero,
        'nombre': _nombre,
        'descripcion': _descripcion,
        'precio': _precio,
        'detalle': _descripcion + '.',
        'ingredientes': _ingredientes,
        'imagen': imagen_salchipapa(_numero),
    }

# ---------------------------------------------------------------------------
# BEBIDAS
# Las fotos se buscan por nombre (sin importar .jpg/.png) en /bebidas y /imagenes.
# (clave, nombre, presentación, precio, tipo, nombre de la foto)
# Solo van las bebidas que tienen foto. Para agregar otra: sube su foto a /bebidas y
# añade una línea aquí (y su clave en PRODUCTOS_POR_CATEGORIA.bebidas de index.js).
# ---------------------------------------------------------------------------
CARPETAS_BEBIDAS = ['bebidas', 'imagenes']
BEBIDAS = [
    ('bebidas', 'Coca-Cola Original', '400 ml', 4000, 'Gaseosa', 'cocacola400ml'),
    ('bebida_coca_600', 'Coca-Cola Original', '600 ml', 5000, 'Gaseosa', 'coca_cola600ml'),
    ('bebida_coca_1_5', 'Coca-Cola Original', '1.5 L', 8000, 'Gaseosa', 'cocacola1_5L'),
    ('bebida_zero_600', 'Coca-Cola Zero', '600 ml', 5000, 'Gaseosa sin azúcar', 'cocacola_zero600'),
    ('bebida_zero_1_5', 'Coca-Cola Zero', '1.5 L', 8000, 'Gaseosa sin azúcar', 'cocacola_zero1_5'),
    ('bebida_sprite_400', 'Sprite', '400 ml', 3500, 'Gaseosa lima limón', 'sprite400ml'),
    ('bebida_pony_malta_1_5', 'Pony Malta', '1.5 L', 7500, 'Bebida de malta', 'ponymalta1_5'),
    ('bebida_cristal_600', 'Agua Cristal', '600 ml', 3000, 'Agua sin gas', 'aguacristal600ml'),
    ('bebida_cristal_1l', 'Agua Cristal', '1 L', 3500, 'Agua sin gas', 'aguacristal_1l'),
    ('bebida_brisa_1l', 'Agua Brisa', '1 L', 3500, 'Agua sin gas', 'aguabrisa1l'),
    ('bebida_manantial_600', 'Agua Manantial', '600 ml', 4000, 'Agua sin gas', 'aguamanantial600ml'),
    ('bebida_manantial_1_5', 'Agua Manantial', '1.5 L', 7000, 'Agua sin gas', 'aguamanantial1_5l'),
    ('bebida_h2oh_limonata_1_5', 'H2OH! Limonata', '1.5 L', 6000, 'Bebida sabor limón', 'h2ohlimonata'),
    ('bebida_hit_mango_500', 'Hit Mango', '500 ml', 4000, 'Bebida de mango', 'hitdemango500ml'),
    ('bebida_hit_tropicales_1l', 'Hit Frutas Tropicales', '1 L', 6000, 'Bebida de frutas tropicales', 'hittropical1l'),
    # Hit Mango 1 L: tienes la foto (hitmango1l) pero no estaba en la lista de precios.
    # Cuando tengas el precio, quita el "#" y pon el valor:
    # ('bebida_hit_mango_1l', 'Hit Mango', '1 L', 0, 'Bebida de mango', 'hitmango1l'),
]


def _clave_archivo(texto):
    # "Coca Cola 1.5L", "cocacola1_5L" y "Cocacola-1.5l" dan la misma clave: cocacola15l
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', texto.lower())


def imagen_bebida(nombre_foto):
    if not nombre_foto:
        return ''
    buscada = _clave_archivo(nombre_foto)
    for carpeta in CARPETAS_BEBIDAS:
        base = BASE_DIR / carpeta
        if base.is_dir():
            for archivo in sorted(base.iterdir()):
                if archivo.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp') and _clave_archivo(archivo.stem) == buscada:
                    return f'/{carpeta}/{archivo.name}'
    print(f'[AVISO] No encontré la foto "{nombre_foto}" en {", ".join(CARPETAS_BEBIDAS)}')
    return ''


for _n, (_clave, _nombre, _tam, _precio, _tipo, _foto) in enumerate(BEBIDAS, start=1):
    MENU[_clave] = {
        'id': 200 + _n,
        'nombre': f'{_nombre} {_tam}',
        'descripcion': f'{_tipo}, presentación de {_tam}',
        'precio': _precio,
        'detalle': f'{_nombre} de {_tam}. Se sirve bien fría.',
        'imagen': imagen_bebida(_foto),
    }

# ---------------------------------------------------------------------------
# SANDWICH
# Las fotos se buscan por nombre (sin importar tildes, mayúsculas ni guiones)
# en la carpeta /sandwich.
# (clave, nombre, descripción, precio, ingredientes, nombre de la foto)
# ---------------------------------------------------------------------------
CARPETAS_SANDWICH = ['sandwich', 'sandwiches']
SANDWICHES = [
    ('sandwich_clasico', 'Sándwich Clásico', 'Jamón, queso, lechuga, tomate y salsas', 8000,
     ['Jamón', 'Queso', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_Clásico'),
    ('sandwich_mixto', 'Sándwich Mixto', 'Jamón, queso, tomate, lechuga y salsas', 10000,
     ['Jamón', 'Queso', 'Tomate', 'Lechuga', 'Salsas'], 'Sándwich_Mixto'),
    ('sandwich_jamon_queso', 'Sándwich de Jamón y Queso', 'Jamón, queso, lechuga, tomate y salsas', 9000,
     ['Jamón', 'Queso', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_de_Jamón_y_Queso'),
    ('sandwich_pollo', 'Sándwich de Pollo', 'Pechuga de pollo, queso, lechuga, tomate y salsas', 10000,
     ['Pechuga de pollo', 'Queso', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_de_Pollo'),
    ('sandwich_pollo_queso', 'Sándwich de Queso y Pollo', 'Pollo a la parrilla, queso derretido, lechuga y salsas', 12000,
     ['Pollo a la parrilla', 'Queso derretido', 'Lechuga', 'Salsas'], 'Sándwich_de_Pollo_y_Queso'),
    ('sandwich_crispy', 'Sándwich Crispy', 'Pollo crispy, lechuga, tomate, queso y salsas', 12000,
     ['Pollo crispy', 'Lechuga', 'Tomate', 'Queso', 'Salsas'], 'Sándwich_Crispy'),
    ('sandwich_carne', 'Sándwich de Carne', 'Carne de res, queso, lechuga, tomate, cebolla y salsas', 12000,
     ['Carne de res', 'Queso', 'Lechuga', 'Tomate', 'Cebolla', 'Salsas'], 'Sándwich_de_Carne'),
    ('sandwich_bbq', 'Sándwich BBQ', 'Carne de res, queso, tocineta, lechuga, tomate y salsas', 12000,
     ['Carne de res', 'Queso', 'Tocineta', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_BBQ'),
    ('sandwich_mexicano', 'Sándwich Mexicano', 'Carne de res, maíz, frijoles, queso, lechuga, tomate y salsas', 12000,
     ['Carne de res', 'Maíz', 'Frijoles', 'Queso', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_Mexicano'),
    ('sandwich_hawaiano', 'Sándwich Hawaiano', 'Jamón, queso, piña, tomate, lechuga y salsas', 11000,
     ['Jamón', 'Queso', 'Piña', 'Tomate', 'Lechuga', 'Salsas'], 'Sándwich_Hawaiano'),
    ('sandwich_especial', 'Sándwich Especial', 'Jamón, queso, pollo, tocineta, lechuga, tomate y salsas', 13000,
     ['Jamón', 'Queso', 'Pollo', 'Tocineta', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_Especial'),
    ('sandwich_ranchero', 'Sándwich Ranchero', 'Carne de res, huevo, tocineta, queso, lechuga, tomate y salsas', 13000,
     ['Carne de res', 'Huevo', 'Tocineta', 'Queso', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_Ranchero'),
    ('sandwich_bbq_especial', 'Sándwich BBQ Especial', 'Carne de res, pollo, tocineta, queso, salsa BBQ, lechuga, tomate y salsas', 16000,
     ['Carne de res', 'Pollo', 'Tocineta', 'Queso', 'Salsa BBQ', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_BBQ_Especial'),
    ('sandwich_super_especial', 'Sándwich Super Especial', 'Carne de res, pollo, jamón, tocineta, huevo, queso, lechuga, tomate y salsas', 15000,
     ['Carne de res', 'Pollo', 'Jamón', 'Tocineta', 'Huevo', 'Queso', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_Super_Especial'),
    ('sandwich_festival', 'Sándwich Festival', 'Carne de res, pollo, jamón, tocineta, queso, huevo, lechuga, tomate y salsas', 18000,
     ['Carne de res', 'Pollo', 'Jamón', 'Tocineta', 'Queso', 'Huevo', 'Lechuga', 'Tomate', 'Salsas'], 'Sándwich_Festival'),
]


def imagen_sandwich(nombre_foto):
    # Busca en /sandwich y, por si la carpeta quedó con el nombre en plural, en /sandwiches también.
    buscada = _clave_archivo(nombre_foto)
    for carpeta in CARPETAS_SANDWICH:
        base = BASE_DIR / carpeta
        if base.is_dir():
            for archivo in sorted(base.iterdir()):
                if archivo.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp') and _clave_archivo(archivo.stem) == buscada:
                    return f'/{carpeta}/{archivo.name}'
    print(f'[AVISO] No encontré la foto "{nombre_foto}" en {" ni ".join(CARPETAS_SANDWICH)}')
    return ''


for _n, (_clave, _nombre, _descripcion, _precio, _ingredientes, _foto) in enumerate(SANDWICHES, start=1):
    MENU[_clave] = {
        'id': 300 + _n,
        'nombre': _nombre,
        'descripcion': _descripcion,
        'precio': _precio,
        'detalle': _descripcion + '.',
        'ingredientes': _ingredientes,
        'imagen': imagen_sandwich(_foto),
    }

# ---------------------------------------------------------------------------
# PICADAS
# Las fotos se buscan en la carpeta /picadas: sirve cualquier archivo cuyo nombre
# contenga la palabra clave (sin importar tildes, mayúsculas ni guiones).
# (clave, nombre, descripción, precio, ingredientes, palabra clave de la foto)
# La primera usa la clave 'picadas' porque es la que activa la categoría en el menú.
# ---------------------------------------------------------------------------
CARPETAS_PICADAS = ['picadas']
PICADAS = [
    ('picadas', 'Picada Volcán', 'Carne, pollo, chorizo, papa criolla, queso y salsas', 25000,
     ['Carne', 'Pollo', 'Chorizo', 'Papa criolla', 'Queso', 'Salsas'], 'volcan'),
    ('picada_imperial', 'Picada Imperial', 'Carne, pollo, tocineta, chorizo, salchicha y papa', 30000,
     ['Carne', 'Pollo', 'Tocineta', 'Chorizo', 'Salchicha', 'Papa'], 'imperial'),
    ('picada_fuego_andino', 'Picada Fuego Andino', 'Carne, chorizo, maíz, papa, queso y salsa BBQ', 28000,
     ['Carne', 'Chorizo', 'Maíz', 'Papa', 'Queso', 'Salsa BBQ'], 'fuegoandino'),
    ('picada_dragon', 'Picada Dragón', 'Carne, pollo crispy, chorizo, tocineta y papa', 32000,
     ['Carne', 'Pollo crispy', 'Chorizo', 'Tocineta', 'Papa'], 'dragon'),
    ('picada_brutal', 'Picada Brutal', 'Carne, pollo, chorizo, salchicha, jamón, tocineta y papa', 35000,
     ['Carne', 'Pollo', 'Chorizo', 'Salchicha', 'Jamón', 'Tocineta', 'Papa'], 'brutal'),
    ('picada_tropical', 'Picada Tropical', 'Pollo, carne, piña, maíz, queso, papa y salsas', 27000,
     ['Pollo', 'Carne', 'Piña', 'Maíz', 'Queso', 'Papa', 'Salsas'], 'tropical'),
    ('picada_trueno', 'Picada Trueno', 'Carne, pollo, chorizo, salchicha, queso y papa ripio', 30000,
     ['Carne', 'Pollo', 'Chorizo', 'Salchicha', 'Queso', 'Papa ripio'], 'trueno'),
    ('picada_escorpion', 'Picada Escorpión', 'Carne, chorizo picante, tocineta, jalapeño, queso y papa', 32000,
     ['Carne', 'Chorizo picante', 'Tocineta', 'Jalapeño', 'Queso', 'Papa'], 'escorpion'),
    ('picada_pirata', 'Picada Pirata', 'Carne, pollo, salchicha, chorizo, maíz y papa', 35000,
     ['Carne', 'Pollo', 'Salchicha', 'Chorizo', 'Maíz', 'Papa'], 'pirata'),
    ('picada_dinamita', 'Picada Dinamita', 'Carne, pollo crispy, tocineta, queso cheddar y papa', 42000,
     ['Carne', 'Pollo crispy', 'Tocineta', 'Queso cheddar', 'Papa'], 'dinamita'),
    ('picada_leon', 'Picada León', 'Doble carne, pollo, chorizo, queso, papa y salsas', 52000,
     ['Doble carne', 'Pollo', 'Chorizo', 'Queso', 'Papa', 'Salsas'], 'leon'),
    ('picada_azteca', 'Picada Azteca', 'Carne, pollo, jalapeño, guacamole, maíz, queso y papa', 58000,
     ['Carne', 'Pollo', 'Jalapeño', 'Guacamole', 'Maíz', 'Queso', 'Papa'], 'azteca'),
    ('picada_inferno', 'Picada Inferno', 'Carne, chorizo, tocineta, jalapeño, queso y salsa picante', 68000,
     ['Carne', 'Chorizo', 'Tocineta', 'Jalapeño', 'Queso', 'Salsa picante'], ('inferno', 'infierno')),
    ('picada_diamante', 'Picada Diamante', 'Carne, pollo, chorizo, camarón, queso, papa y salsas', 75000,
     ['Carne', 'Pollo', 'Chorizo', 'Camarón', 'Queso', 'Papa', 'Salsas'], 'diamante'),
    ('picada_diosa', 'Picada Diosa', 'Carne, pollo, chorizo, tocineta, salchicha, queso, papa y guacamole', 85000,
     ['Carne', 'Pollo', 'Chorizo', 'Tocineta', 'Salchicha', 'Queso', 'Papa', 'Guacamole'], 'diosa'),
]


def imagen_picada(palabras):
    # Basta con que el nombre del archivo CONTENGA la palabra clave (ej. "diosa" sirve para
    # "Picada_Diosa.jpg", "PIcada_La_diosa.jpg" o "diosa 2.png"). Ignora tildes y mayúsculas.
    if isinstance(palabras, str):
        palabras = (palabras,)
    claves = [_clave_archivo(p) for p in palabras]
    for carpeta in CARPETAS_PICADAS:
        base = BASE_DIR / carpeta
        if base.is_dir():
            for archivo in sorted(base.iterdir()):
                if archivo.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                    nombre = _clave_archivo(archivo.stem)
                    if any(clave in nombre for clave in claves):
                        return f'/{carpeta}/{archivo.name}'
    print(f'[AVISO] No encontré la foto de {palabras} en {", ".join(CARPETAS_PICADAS)}')
    return ''


for _n, (_clave, _nombre, _descripcion, _precio, _ingredientes, _foto) in enumerate(PICADAS, start=1):
    MENU[_clave] = {
        'id': 400 + _n,
        'nombre': _nombre,
        'descripcion': _descripcion,
        'precio': _precio,
        'detalle': _descripcion + '.',
        'ingredientes': _ingredientes,
        'imagen': imagen_picada(_foto),
    }

# ---------------------------------------------------------------------------
# PERROS CALIENTES
# Las fotos se buscan en la carpeta /perros por nombre de archivo (sin importar
# tildes, mayúsculas ni guiones): Perro_clasico.jpg, Perro_BBQ.jpg, etc.
# (clave, nombre, descripción, precio, ingredientes, nombre de la foto)
# El primero usa la clave 'perros' porque es la que activa la categoría en el menú.
# ---------------------------------------------------------------------------
CARPETAS_PERROS = ['perros']
PERROS = [
    ('perros', 'Perro Clásico', 'Salchicha, papa ripio, queso, salsas', 10000,
     ['Salchicha', 'Papa ripio', 'Queso', 'Salsas'], 'Perro_clasico'),
    ('perro_hawaiano', 'Perro Hawaiano', 'Salchicha, jamón, piña, queso, papa ripio, salsas', 13000,
     ['Salchicha', 'Jamón', 'Piña', 'Queso', 'Papa ripio', 'Salsas'], 'Perro_hawaiano'),
    ('perro_bbq', 'Perro BBQ', 'Salchicha, tocineta, queso, salsa BBQ, papa ripio', 14000,
     ['Salchicha', 'Tocineta', 'Queso', 'Salsa BBQ', 'Papa ripio'], 'Perro_BBQ'),
    ('perro_ranchero', 'Perro Ranchero', 'Salchicha ranchera, chorizo, queso, cebolla, papa ripio, salsas', 15000,
     ['Salchicha ranchera', 'Chorizo', 'Queso', 'Cebolla', 'Papa ripio', 'Salsas'], 'Perro_ranchero'),
    ('perro_mexicano', 'Perro Mexicano', 'Salchicha, carne molida, jalapeño, guacamole, queso, salsas', 16000,
     ['Salchicha', 'Carne molida', 'Jalapeño', 'Guacamole', 'Queso', 'Salsas'], 'Perro_mexicano'),
    ('perro_crispy', 'Perro Crispy', 'Salchicha, pollo crispy, queso, papa ripio, salsa de ajo', 16000,
     ['Salchicha', 'Pollo crispy', 'Queso', 'Papa ripio', 'Salsa de ajo'], 'Perro_crispy'),
    ('perro_mixto', 'Perro Mixto', 'Salchicha, pollo, jamón, queso, papa ripio, salsas', 15000,
     ['Salchicha', 'Pollo', 'Jamón', 'Queso', 'Papa ripio', 'Salsas'], 'Perro_mixto'),
    ('perro_especial', 'Perro Especial', 'Salchicha, tocineta, jamón, pollo, queso, papa ripio, salsas', 18000,
     ['Salchicha', 'Tocineta', 'Jamón', 'Pollo', 'Queso', 'Papa ripio', 'Salsas'], 'Perro_especial'),
    ('perro_super', 'Perro Súper', 'Doble salchicha, carne, tocineta, queso, papa ripio, salsas', 20000,
     ['Doble salchicha', 'Carne', 'Tocineta', 'Queso', 'Papa ripio', 'Salsas'], 'Perro_super'),
    ('perro_festival', 'Perro Festival', 'Salchicha, chorizo, pollo, maíz, tocineta, queso, papa ripio, salsas', 19000,
     ['Salchicha', 'Chorizo', 'Pollo', 'Maíz', 'Tocineta', 'Queso', 'Papa ripio', 'Salsas'], 'Perro_festival'),
    ('perro_ranchero_bbq', 'Perro Ranchero BBQ', 'Salchicha ranchera, tocineta, cebolla caramelizada, queso, BBQ', 16000,
     ['Salchicha ranchera', 'Tocineta', 'Cebolla caramelizada', 'Queso', 'BBQ'], 'Perro_ranchero_BBQ'),
    ('perro_pollo', 'Perro Pollo', 'Salchicha, pollo desmechado, queso, papa ripio, salsa de ajo', 14000,
     ['Salchicha', 'Pollo desmechado', 'Queso', 'Papa ripio', 'Salsa de ajo'], 'Perro_de_pollo'),
    ('perro_tocineta', 'Perro Tocineta', 'Salchicha, doble tocineta, queso cheddar, papa ripio, salsas', 15000,
     ['Salchicha', 'Doble tocineta', 'Queso cheddar', 'Papa ripio', 'Salsas'], 'Perro_tocineta'),
    ('perro_3_carnes', 'Perro 3 Carnes', 'Salchicha, carne, pollo, chorizo, queso, papa ripio, salsas', 18000,
     ['Salchicha', 'Carne', 'Pollo', 'Chorizo', 'Queso', 'Papa ripio', 'Salsas'], 'Perro_3_carnes'),
    ('perro_brutal', 'Perro Brutal', 'Doble salchicha, carne, pollo, chorizo, tocineta, jamón, queso, papa ripio y salsas', 22000,
     ['Doble salchicha', 'Carne', 'Pollo', 'Chorizo', 'Tocineta', 'Jamón', 'Queso', 'Papa ripio', 'Salsas'], 'Perro_brutal'),
]


def imagen_perro(nombre_foto):
    buscada = _clave_archivo(nombre_foto)
    for carpeta in CARPETAS_PERROS:
        base = BASE_DIR / carpeta
        if base.is_dir():
            for archivo in sorted(base.iterdir()):
                if archivo.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp') and _clave_archivo(archivo.stem) == buscada:
                    return f'/{carpeta}/{archivo.name}'
    print(f'[AVISO] No encontré la foto "{nombre_foto}" en {", ".join(CARPETAS_PERROS)}')
    return ''


for _n, (_clave, _nombre, _descripcion, _precio, _ingredientes, _foto) in enumerate(PERROS, start=1):
    MENU[_clave] = {
        'id': 500 + _n,
        'nombre': _nombre,
        'descripcion': _descripcion,
        'precio': _precio,
        'detalle': _descripcion + '.',
        'ingredientes': _ingredientes,
        'imagen': imagen_perro(_foto),
    }

# ---------------------------------------------------------------------------
# ACOMPAÑAMIENTOS
# Las fotos se buscan en la carpeta /acompanamientos: basta con que el nombre del
# archivo contenga la palabra clave (sin importar tildes, mayúsculas ni guiones).
# (clave, nombre, descripción, precio, ingredientes o None, palabra clave de la foto)
# El primero usa la clave 'acompanamientos' porque es la que activa la categoría en el menú.
# ---------------------------------------------------------------------------
ACOMPANAMIENTOS = [
    ('acompanamientos', 'Papas a la francesa pequeña', 'Papas a la francesa, porción de 100 g', 5000, None, 'pequena'),
    ('acomp_papas_mediana', 'Papas a la francesa mediana', 'Papas a la francesa, porción de 150 g', 8000, None, 'mediana'),
    ('acomp_papas_grande', 'Papas a la francesa grande', 'Papas a la francesa, porción de 250 g', 12000, None, 'grande'),
    ('acomp_papas_familiar', 'Papas a la francesa familiar', 'Papas a la francesa, porción de 400 g', 18000, None, 'familiar'),
    ('acomp_papas_gratinadas', 'Papas gratinadas', 'Papas gratinadas con queso y tocineta', 12000, ['Papas', 'Queso', 'Tocineta'], 'gratinadas'),
    ('acomp_aros_cebolla', 'Aros de cebolla', 'Aros de cebolla, 8 unidades', 8000, None, 'aros'),
    ('acomp_deditos_queso', 'Deditos de queso', 'Deditos de queso, 6 unidades', 9000, None, 'deditos'),
    ('acomp_nuggets', 'Nuggets de pollo', 'Nuggets de pollo, 6 unidades', 10000, None, 'nuggets'),
    ('acomp_alitas_bbq', 'Alitas BBQ', 'Alitas con salsa BBQ, 6 unidades', 16000, None, 'alitas'),
    ('acomp_alitas_picantes', 'Alitas Picantes', 'Alitas picantes, 6 unidades', 16000, None, 'alitas'),
    ('acomp_patacones', 'Patacones con hogao', 'Patacones con hogao, porción', 7000, None, 'patacon'),
]


def _carpetas_acompanamientos():
    # Cualquier carpeta cuyo nombre empiece por "acompan" (acompanamientos, acompañamientos, ...)
    return [d for d in sorted(BASE_DIR.iterdir()) if d.is_dir() and _clave_archivo(d.name).startswith('acompan')]


_FOTOS_ACOMPANAMIENTOS = []
for _carpeta in _carpetas_acompanamientos():
    # rglob: también encuentra las fotos si quedaron dentro de una subcarpeta
    for _archivo in sorted(_carpeta.rglob('*')):
        if _archivo.is_file() and _archivo.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
            _FOTOS_ACOMPANAMIENTOS.append((_clave_archivo(_archivo.stem), '/' + _archivo.relative_to(BASE_DIR).as_posix()))
if not _FOTOS_ACOMPANAMIENTOS:
    print('[AVISO] No encontré fotos de acompañamientos: crea la carpeta "acompanamientos" junto a app.py y copia ahí las fotos.')


def imagen_acompanamiento(palabra):
    # Basta con que el nombre del archivo CONTENGA la palabra clave (ej. "mediana"
    # sirve para "Papas_a_la_francesa_mediana_150g.png" o "papas mediana (1).png").
    for clave, ruta in _FOTOS_ACOMPANAMIENTOS:
        if palabra in clave:
            return ruta
    print(f'[AVISO] No encontré la foto del acompañamiento "{palabra}"')
    return ''


for _n, (_clave, _nombre, _descripcion, _precio, _ingredientes, _foto) in enumerate(ACOMPANAMIENTOS, start=1):
    MENU[_clave] = {
        'id': 600 + _n,
        'nombre': _nombre,
        'descripcion': _descripcion,
        'precio': _precio,
        'detalle': _descripcion + '.',
        'imagen': imagen_acompanamiento(_foto),
    }
    if _ingredientes:
        MENU[_clave]['ingredientes'] = _ingredientes

print(f'[INFO] Acompañamientos: {sum(1 for _c in ACOMPANAMIENTOS if MENU[_c[0]]["imagen"])} de {len(ACOMPANAMIENTOS)} con foto ({len(_FOTOS_ACOMPANAMIENTOS)} archivos leídos)')

# ---------------------------------------------------------------------------
# COMBOS
# Cada combo se arma con productos que ya existen en el menú: el precio es la suma de
# sus partes menos un descuento, así que si cambias el precio de un producto el combo
# se actualiza solo.
# (clave, nombre, [(clave del producto, cantidad, texto para mostrar)], descuento, palabra clave de la foto)
# El primero usa la clave 'combos' porque es la que activa la categoría en el menú.
# Fotos: carpeta /combos; basta con que el nombre del archivo contenga la palabra clave
# (por ejemplo combo_clasico.png o "Combo Clásico.jpg" para la palabra "clasico").
# ---------------------------------------------------------------------------
COMBOS = [
    ('combos', 'Combo Clásico',
     [('hamburguesa Clasica', 1, 'Hamburguesa Clásica'), ('acomp_papas_mediana', 1, 'papas medianas'),
      ('bebidas', 1, 'Coca-Cola 400 ml')], 2000, 'clasico'),
    ('combo_bacon', 'Combo Bacon',
     [('hamburguesa Bacon', 1, 'Hamburguesa Bacon'), ('acomp_papas_grande', 1, 'papas grandes'),
      ('bebida_coca_600', 1, 'Coca-Cola 600 ml')], 2000, 'bacon'),
    ('combo_perro', 'Combo Perro Especial',
     [('perro_especial', 1, 'Perro Especial'), ('acompanamientos', 1, 'papas pequeñas'),
      ('bebidas', 1, 'Coca-Cola 400 ml')], 2000, 'perro'),
    ('combo_salchipapa', 'Combo Salchipapa',
     [('salchipapas_mixta', 1, 'Salchipapa Mixta'), ('bebida_coca_600', 1, 'Coca-Cola 600 ml')], 2000, 'salchipapa'),
    ('combo_pareja', 'Combo Pareja',
     [('hamburguesa Clasica', 2, 'Hamburguesa Clásica'), ('acomp_papas_grande', 1, 'papas grandes'),
      ('bebidas', 2, 'Coca-Cola 400 ml')], 3000, 'pareja'),
    ('combo_compartir', 'Combo Compartir',
     [('picadas', 1, 'Picada Volcán'), ('acomp_alitas_bbq', 1, 'alitas BBQ'),
      ('bebida_coca_1_5', 1, 'Coca-Cola 1.5 L')], 3000, 'compartir'),
]


def _pesos(valor):
    return '$' + f'{valor:,}'.replace(',', '.')


_FOTOS_COMBOS = []
for _carpeta in sorted(BASE_DIR.iterdir()):
    if _carpeta.is_dir() and _clave_archivo(_carpeta.name).startswith('combo'):
        for _archivo in sorted(_carpeta.rglob('*')):
            if _archivo.is_file() and _archivo.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                _FOTOS_COMBOS.append((_clave_archivo(_archivo.stem), '/' + _archivo.relative_to(BASE_DIR).as_posix()))


def imagen_categoria_combos():
    # Imagen de la tarjeta "Combos" del menú: cualquier archivo de /combos cuyo nombre contenga
    # "imagen" y "combo" (imagen_combo.png, "imagen combo.png", ...).
    for clave, ruta in _FOTOS_COMBOS:
        if 'imagencombo' in clave:
            return ruta
    return '/imagenes/combos_house.png'


def imagen_combo(palabra):
    for clave, ruta in _FOTOS_COMBOS:
        if palabra in clave:
            return ruta
    return ''


for _n, (_clave, _nombre, _partes, _descuento, _foto) in enumerate(COMBOS, start=1):
    _suma = 0
    for _clave_producto, _cantidad, _texto in _partes:
        if _clave_producto not in MENU:
            raise KeyError(f'El combo "{_nombre}" usa un producto que no existe: {_clave_producto}')
        _suma += MENU[_clave_producto]['precio'] * _cantidad
    _incluye = ' + '.join(f'{c} x {t}' if c > 1 else t for _, c, t in _partes)
    MENU[_clave] = {
        'id': 700 + _n,
        'nombre': _nombre,
        'descripcion': _incluye,
        'precio': _suma - _descuento,
        'detalle': f'Ahorras {_pesos(_descuento)} frente a pedirlo por separado.',
        'imagen': imagen_combo(_foto),
    }

print(f'[INFO] Combos: {len(COMBOS)} creados, {sum(1 for _c in COMBOS if MENU[_c[0]]["imagen"])} con foto')

ESTADOS_PEDIDO = {'pendiente', 'preparando', 'en camino', 'entregado', 'cancelado'}

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path='')
app.secret_key = os.environ.get('BURGER_SECRET_KEY') or secrets.token_hex(32)
# Contraseña del panel de administración.
# En el servidor real define la variable de entorno BURGER_ADMIN_PASSWORD con una contraseña larga;
# la de abajo es solo para pruebas en tu computador.
DEFAULT_ADMIN_PASSWORD = 'cambiar-esta-clave'


def contrasena_admin():
    return os.environ.get('BURGER_ADMIN_PASSWORD') or DEFAULT_ADMIN_PASSWORD


if contrasena_admin() == DEFAULT_ADMIN_PASSWORD:
    print('[AVISO] El panel de administración usa la contraseña de prueba. Antes de publicar, define BURGER_ADMIN_PASSWORD.')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('BURGER_HTTPS') == '1',
)
# Límite de intentos fallidos (en memoria): frena a quien prueba contraseñas
# o teléfonos sin parar. Se reinicia al reiniciar el servidor.
INTENTOS_FALLIDOS = defaultdict(deque)
MAX_INTENTOS_LOGIN = 5
MAX_INTENTOS_CONSULTA = 10
VENTANA_INTENTOS_SEGUNDOS = 300


def _limpiar_intentos(clave):
    intentos = INTENTOS_FALLIDOS[clave]
    limite = time.monotonic() - VENTANA_INTENTOS_SEGUNDOS
    while intentos and intentos[0] < limite:
        intentos.popleft()
    if not intentos:
        INTENTOS_FALLIDOS.pop(clave, None)
    return intentos


def demasiados_intentos(clave, maximo):
    return len(_limpiar_intentos(clave)) >= maximo


def registrar_intento_fallido(clave):
    _limpiar_intentos(clave)
    INTENTOS_FALLIDOS[clave].append(time.monotonic())


def olvidar_intentos(clave):
    INTENTOS_FALLIDOS.pop(clave, None)


app.config['TEMPLATES_AUTO_RELOAD'] = True  # los cambios en templates/ se ven sin reiniciar el servidor
ORIGENES_DESARROLLO = {'http://127.0.0.1:5500', 'http://localhost:5500'}


EXTENSIONES_IMAGEN = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg')
EXTENSIONES_PRIVADAS = ('.py', '.pyc', '.db', '.sqlite', '.cfg', '.env', '.md')
CARPETAS_PRIVADAS = {'.venv', 'venv', '.git', '__pycache__', 'comprobantes', 'templates'}


@app.before_request
def bloquear_archivos_privados():
    # La carpeta del proyecto es pública (static_folder=BASE_DIR): sin esto
    # cualquiera podría descargar /pedidos.db o /app.py (que contiene la clave del admin).
    ruta = request.path.lower().rstrip('. /')
    partes = set(Path(ruta.lstrip('/')).parts)
    if ruta.endswith(EXTENSIONES_PRIVADAS) or partes & CARPETAS_PRIVADAS:
        abort(404)


@app.after_request
def permitir_live_server_local(respuesta):
    origen = request.headers.get('Origin')
    if origen in ORIGENES_DESARROLLO:
        respuesta.headers['Access-Control-Allow-Origin'] = origen
        respuesta.headers['Access-Control-Allow-Credentials'] = 'true'
        respuesta.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        respuesta.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, OPTIONS'
        respuesta.headers['Vary'] = 'Origin'

    if request.path.lower().endswith(EXTENSIONES_IMAGEN) and respuesta.status_code in (200, 304):
        respuesta.headers['Cache-Control'] = 'public, max-age=86400'
    else:
        respuesta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        respuesta.headers['Pragma'] = 'no-cache'
        respuesta.headers['Expires'] = '0'
    return respuesta


def admin_configurado():
    return bool(contrasena_admin())


def admin_requerido():
    return session.get('admin_autenticado') is True


def error_json(mensaje, estado):
    return jsonify({'error': mensaje}), estado


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def initialize_database():
    with get_connection() as connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_nombre TEXT NOT NULL,
                cliente_telefono TEXT NOT NULL,
                cliente_direccion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                fecha TEXT NOT NULL,
                total INTEGER NOT NULL,
                productos TEXT NOT NULL,
                comprobante TEXT,
                pago_estado TEXT NOT NULL DEFAULT 'pendiente'
            )
        ''')
        columns = {row['name'] for row in connection.execute('PRAGMA table_info(pedidos)').fetchall()}
        if 'comprobante' not in columns:
            connection.execute('ALTER TABLE pedidos ADD COLUMN comprobante TEXT')
        if 'pago_estado' not in columns:
            connection.execute("ALTER TABLE pedidos ADD COLUMN pago_estado TEXT NOT NULL DEFAULT 'pendiente'")
        connection.commit()


def sincronizar_menu():
    """Guarda precio y disponibilidad en SQLite y los aplica sobre MENU."""
    with get_connection() as connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS precios_menu (
                clave TEXT PRIMARY KEY,
                precio INTEGER NOT NULL,
                disponible INTEGER NOT NULL DEFAULT 1
            )
        ''')
        columnas = {c['name'] for c in connection.execute('PRAGMA table_info(precios_menu)')}
        if 'eliminado' not in columnas:
            connection.execute('ALTER TABLE precios_menu ADD COLUMN eliminado INTEGER NOT NULL DEFAULT 0')
        guardados = {fila['clave']: fila for fila in connection.execute('SELECT * FROM precios_menu')}
        for clave, producto in MENU.items():
            fila = guardados.get(clave)
            if fila is None:
                connection.execute('INSERT INTO precios_menu (clave, precio, disponible) VALUES (?, ?, 1)',
                                   (clave, producto['precio']))
                producto['disponible'] = True
            else:
                producto['precio'] = fila['precio']
                producto['disponible'] = bool(fila['disponible'])
                producto['eliminado'] = bool(fila['eliminado'])
        connection.commit()


CATEGORIAS_MENU = ('combos', 'hamburguesas', 'perros', 'salchipapas', 'bebidas', 'sandwich', 'acompanamientos', 'picadas')
CARPETA_NUEVOS = BASE_DIR / 'productos_nuevos'
FIRMAS_IMAGEN = {'.jpg': b'\xff\xd8\xff', '.jpeg': b'\xff\xd8\xff', '.png': b'\x89PNG', '.webp': b'RIFF'}
MAX_IMAGEN = 3 * 1024 * 1024


def construir_producto(id_, nombre, categoria, ingredientes, imagen, precio, tamano=None):
    if categoria == 'bebidas' and tamano:
        # Las bebidas no llevan ingredientes: solo nombre, tamaño (mL) y precio.
        return {
            'id': id_, 'nombre': f'{nombre} {tamano} ml', 'descripcion': f'Bebida, presentación de {tamano} ml',
            'precio': precio, 'detalle': f'{nombre} de {tamano} ml. Se sirve bien fría.', 'imagen': imagen,
            'categoria': categoria, 'disponible': True, 'agregado': True,
        }
    descripcion = ', '.join(ingredientes)
    return {
        'id': id_, 'nombre': nombre, 'descripcion': descripcion, 'precio': precio,
        'detalle': descripcion + '.', 'ingredientes': ingredientes, 'imagen': imagen,
        'categoria': categoria, 'disponible': True, 'agregado': True,
    }


def cargar_productos_nuevos():
    """Carga en MENU los productos agregados desde el panel de administración."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS productos_nuevos (
                clave TEXT PRIMARY KEY,
                id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                ingredientes TEXT NOT NULL,
                imagen TEXT NOT NULL,
                precio INTEGER NOT NULL
            )
        """)
        columnas = {c['name'] for c in connection.execute('PRAGMA table_info(productos_nuevos)')}
        if 'tamano' not in columnas:
            connection.execute('ALTER TABLE productos_nuevos ADD COLUMN tamano INTEGER')
            connection.commit()
        for f in connection.execute('SELECT * FROM productos_nuevos ORDER BY id'):
            MENU[f['clave']] = construir_producto(
                f['id'], f['nombre'], f['categoria'], json.loads(f['ingredientes']), f['imagen'], f['precio'], f['tamano'])


def serialize_order(row):
    order = dict(row)
    order['productos'] = json.loads(order['productos'])
    return order


def serialize_public_order(order):
    return {
        'id': order['id'],
        'estado': order['estado'],
        'fecha': order['fecha'],
        'total': order['total'],
        'productos': order['productos'],
    }


def validar_pedido(data):
    if not isinstance(data, dict):
        return None, 'Los datos del pedido no son válidos.'

    nombre = data.get('cliente_nombre')
    telefono = data.get('cliente_telefono')
    direccion = data.get('cliente_direccion')
    items = data.get('productos')
    if not all(isinstance(value, str) for value in (nombre, telefono, direccion)):
        return None, 'Completa nombre, teléfono y dirección.'

    nombre, telefono, direccion = nombre.strip(), telefono.strip(), direccion.strip()
    if not 2 <= len(nombre) <= 80:
        return None, 'El nombre debe tener entre 2 y 80 caracteres.'
    if not re.fullmatch(r'\d{7,15}', telefono):
        return None, 'El teléfono debe tener entre 7 y 15 números.'
    if not 5 <= len(direccion) <= 200:
        return None, 'La dirección debe tener entre 5 y 200 caracteres.'
    if not isinstance(items, list) or not 1 <= len(items) <= 30:
        return None, 'El pedido debe incluir entre 1 y 30 productos.'

    productos = []
    total = 0
    for item in items:
        if not isinstance(item, dict):
            return None, 'Hay un producto con datos no válidos.'
        tipo = item.get('tipo')
        cantidad = item.get('cantidad')
        if (
            not isinstance(tipo, str)
            or tipo not in MENU
            or isinstance(cantidad, bool)
            or not isinstance(cantidad, int)
            or not 1 <= cantidad <= 99
        ):
            return None, 'Hay un producto o una cantidad no válida.'

        producto = MENU[tipo]
        if producto.get('eliminado') or not producto.get('disponible', True):
            return None, f"{producto['nombre']} no está disponible por ahora."
        ingredientes = item.get('ingredientes', producto.get('ingredientes', []))
        ingredientes_disponibles = producto.get('ingredientes', [])
        if (
            not isinstance(ingredientes, list)
            or any(not isinstance(value, str) or value not in ingredientes_disponibles for value in ingredientes)
            or len(set(ingredientes)) != len(ingredientes)
        ):
            return None, 'La personalización de un producto no es válida.'

        nombre_producto = producto['nombre']
        quitados = [value for value in ingredientes_disponibles if value not in ingredientes]
        if quitados:
            nombre_producto += f" (sin {', sin '.join(quitados)})"
        productos.append({
            'tipo': tipo,
            'nombre': nombre_producto,
            'cantidad': cantidad,
            'precio': producto['precio'],
            'ingredientes': ingredientes,
        })
        total += producto['precio'] * cantidad

    return {
        'cliente_nombre': nombre,
        'cliente_telefono': telefono,
        'cliente_direccion': direccion,
        'productos': productos,
        'total': total,
    }, None


TEMPLATES_DIR = BASE_DIR / 'templates'


def cache_buster():
    return int(datetime.now().timestamp() * 1000)


@app.get('/')
def home():
    return render_template('index.html', cache_buster=cache_buster(), imagen_combos=imagen_categoria_combos())


@app.get('/admin')
def admin():
    return render_template('admin.html', cache_buster=cache_buster())


@app.get('/api/pedidos')
def list_orders():
    # Sin "ficha" (id) en la URL: es el panel de administración, que necesita sesión.
    order_id = request.args.get('id', type=int)
    if order_id is None:
        if not admin_requerido():
            return error_json('Debes iniciar sesión como administrador.', 401)
        with get_connection() as connection:
            rows = connection.execute('SELECT * FROM pedidos ORDER BY id DESC').fetchall()
        return jsonify([serialize_order(row) for row in rows])

    # Con "ficha" (id): consulta pública. Hay que indicar también el teléfono con el
    # que se hizo el pedido, y solo se devuelven datos no sensibles
    # (ver serialize_public_order): nada de nombre, teléfono ni dirección.
    clave = f'consulta:{request.remote_addr}'
    if demasiados_intentos(clave, MAX_INTENTOS_CONSULTA):
        return error_json('Demasiados intentos. Espera unos minutos e inténtalo de nuevo.', 429)
    telefono = request.args.get('telefono', '', type=str).strip()
    with get_connection() as connection:
        row = connection.execute('SELECT * FROM pedidos WHERE id = ?', (order_id,)).fetchone()
    # Mismo mensaje si el pedido no existe o el teléfono no coincide, para no
    # revelar qué números de ficha existen.
    if not row or not hmac.compare_digest(telefono, row['cliente_telefono']):
        registrar_intento_fallido(clave)
        return error_json('No encontramos un pedido con ese número de ficha y teléfono.', 404)
    return jsonify(serialize_public_order(serialize_order(row)))


@app.get('/api/menu')
def get_menu():
    return jsonify({clave: p for clave, p in MENU.items() if p.get('disponible', True) and not p.get('eliminado')})


def producto_admin(clave):
    p = MENU[clave]
    return {'clave': clave, 'nombre': p['nombre'], 'precio': p['precio'], 'disponible': p.get('disponible', True),
            'eliminable': True}


@app.get('/api/admin/menu')
def admin_listar_menu():
    if not admin_requerido():
        return error_json('Debes iniciar sesión como administrador.', 401)
    return jsonify([producto_admin(clave) for clave in MENU if not MENU[clave].get('eliminado')])


@app.post('/api/admin/menu/nuevo')
def admin_agregar_producto():
    if not admin_requerido():
        return error_json('Debes iniciar sesión como administrador.', 401)
    nombre = (request.form.get('nombre') or '').strip()
    categoria = request.form.get('categoria', '')
    ingredientes = [i.strip() for i in request.form.getlist('ingredientes') if i.strip()]
    tamano = request.form.get('tamano', type=int)
    precio = request.form.get('precio', type=int)
    archivo = request.files.get('imagen')
    if not 2 <= len(nombre) <= 60:
        return error_json('El título debe tener entre 2 y 60 caracteres.', 400)
    if categoria not in CATEGORIAS_MENU:
        return error_json('Elige una categoría válida.', 400)
    if categoria == 'bebidas':
        ingredientes = []
        if tamano is None or not 50 <= tamano <= 5000:
            return error_json('El tamaño debe ser un número de mL entre 50 y 5000.', 400)
    else:
        tamano = None
        if not 1 <= len(ingredientes) <= 15 or any(len(i) > 40 for i in ingredientes):
            return error_json('Agrega entre 1 y 15 ingredientes (máximo 40 letras cada uno).', 400)
        if len({i.lower() for i in ingredientes}) != len(ingredientes):
            return error_json('Hay ingredientes repetidos.', 400)
    if precio is None or not 1000 <= precio <= 500000:
        return error_json('El precio debe ser un número entero entre $1.000 y $500.000.', 400)
    extension = Path(archivo.filename or '').suffix.lower() if archivo else ''
    contenido = archivo.read(MAX_IMAGEN + 1) if archivo else b''
    if extension not in FIRMAS_IMAGEN or not contenido.startswith(FIRMAS_IMAGEN[extension]):
        return error_json('Sube una imagen JPG, PNG o WEBP.', 400)
    if len(contenido) > MAX_IMAGEN:
        return error_json('La imagen no puede pesar más de 3 MB.', 400)

    texto = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode()
    base = 'nuevo_' + (re.sub(r'[^a-z0-9]+', '_', texto.lower()).strip('_') or 'producto')
    clave, contador = base, 2
    while clave in MENU:
        clave, contador = f'{base}_{contador}', contador + 1
    nuevo_id = max((p['id'] for p in MENU.values() if isinstance(p.get('id'), int)), default=0) + 1
    CARPETA_NUEVOS.mkdir(exist_ok=True)
    nombre_archivo = f'{clave}_{secrets.token_hex(4)}{extension}'
    (CARPETA_NUEVOS / nombre_archivo).write_bytes(contenido)
    imagen = f'/productos_nuevos/{nombre_archivo}'
    with get_connection() as connection:
        connection.execute(
            'INSERT INTO productos_nuevos (clave, id, nombre, categoria, ingredientes, imagen, precio, tamano) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (clave, nuevo_id, nombre, categoria, json.dumps(ingredientes, ensure_ascii=False), imagen, precio, tamano))
        connection.execute('INSERT INTO precios_menu (clave, precio, disponible) VALUES (?, ?, 1)', (clave, precio))
        connection.commit()
    MENU[clave] = construir_producto(nuevo_id, nombre, categoria, ingredientes, imagen, precio, tamano)
    return jsonify(producto_admin(clave)), 201


@app.post('/api/admin/menu/eliminar')
def admin_eliminar_producto():
    if not admin_requerido():
        return error_json('Debes iniciar sesión como administrador.', 401)
    clave = (request.get_json(silent=True) or {}).get('clave')
    if not isinstance(clave, str) or clave not in MENU:
        return error_json('Producto no encontrado.', 404)
    with get_connection() as connection:
        fila = connection.execute('SELECT imagen FROM productos_nuevos WHERE clave = ?', (clave,)).fetchone()
        if fila is None:
            connection.execute('UPDATE precios_menu SET eliminado = 1 WHERE clave = ?', (clave,))
            connection.commit()
            MENU[clave]['eliminado'] = True
            return jsonify({'clave': clave, 'eliminado': True})
        connection.execute('DELETE FROM productos_nuevos WHERE clave = ?', (clave,))
        connection.execute('DELETE FROM precios_menu WHERE clave = ?', (clave,))
        connection.commit()
    MENU.pop(clave, None)
    (CARPETA_NUEVOS / Path(fila['imagen']).name).unlink(missing_ok=True)
    return jsonify({'clave': clave, 'eliminado': True})


@app.patch('/api/admin/menu')
def admin_actualizar_producto():
    if not admin_requerido():
        return error_json('Debes iniciar sesión como administrador.', 401)
    datos = request.get_json(silent=True) or {}
    clave = datos.get('clave')
    if not isinstance(clave, str) or clave not in MENU or MENU[clave].get('eliminado'):
        return error_json('Producto no encontrado.', 404)
    precio = datos.get('precio', MENU[clave]['precio'])
    disponible = datos.get('disponible', MENU[clave].get('disponible', True))
    if isinstance(precio, bool) or not isinstance(precio, int) or not 1000 <= precio <= 500000:
        return error_json('El precio debe ser un número entero entre $1.000 y $500.000.', 400)
    if not isinstance(disponible, bool):
        return error_json('La disponibilidad no es válida.', 400)
    with get_connection() as connection:
        connection.execute('UPDATE precios_menu SET precio = ?, disponible = ? WHERE clave = ?',
                           (precio, int(disponible), clave))
        connection.commit()
    MENU[clave]['precio'] = precio
    MENU[clave]['disponible'] = disponible
    return jsonify(producto_admin(clave))


@app.post('/api/admin/login')
def admin_login():
    if not admin_configurado():
        return error_json('Configura BURGER_ADMIN_PASSWORD en el servidor.', 503)
    clave = f'login:{request.remote_addr}'
    if demasiados_intentos(clave, MAX_INTENTOS_LOGIN):
        return error_json('Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.', 429)
    data = request.get_json(silent=True) or {}
    password = data.get('password') if isinstance(data, dict) else None
    expected_password = contrasena_admin()
    if not isinstance(password, str) or not hmac.compare_digest(password, expected_password):
        registrar_intento_fallido(clave)
        return error_json('Contraseña incorrecta.', 401)
    olvidar_intentos(clave)
    session.clear()
    session['admin_autenticado'] = True
    return jsonify({'autenticado': True})


@app.get('/api/admin/sesion')
def admin_session():
    return jsonify({'autenticado': admin_requerido()})


@app.post('/api/admin/logout')
def admin_logout():
    session.clear()
    return jsonify({'autenticado': False})


@app.post('/api/pedidos')
def create_order():
    data = request.get_json(silent=True) or {}
    pedido, error = validar_pedido(data)
    if error:
        return error_json(error, 400)

    fecha = datetime.now().astimezone().isoformat(timespec='seconds')
    with get_connection() as connection:
        cursor = connection.execute(
            '''INSERT INTO pedidos
               (cliente_nombre, cliente_telefono, cliente_direccion, estado, fecha, total, productos)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                pedido['cliente_nombre'],
                pedido['cliente_telefono'],
                pedido['cliente_direccion'],
                'pendiente',
                fecha,
                pedido['total'],
                json.dumps(pedido['productos'], ensure_ascii=False),
            ),
        )
        connection.commit()
        row = connection.execute('SELECT * FROM pedidos WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return jsonify(serialize_order(row)), 201


@app.patch('/api/pedidos/<int:order_id>/estado')
def update_order_status(order_id):
    if not admin_requerido():
        return error_json('Debes iniciar sesión como administrador.', 401)
    data = request.get_json(silent=True) or {}
    new_status = data.get('estado', '').strip() if isinstance(data, dict) else ''
    if new_status not in ESTADOS_PEDIDO:
        return error_json('Estado de pedido no válido.', 400)

    with get_connection() as connection:
        cursor = connection.execute(
            'UPDATE pedidos SET estado = ? WHERE id = ?',
            (new_status, order_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Pedido no encontrado.'}), 404
        row = connection.execute('SELECT * FROM pedidos WHERE id = ?', (order_id,)).fetchone()
    return jsonify(serialize_order(row))


initialize_database()
cargar_productos_nuevos()
sincronizar_menu()

if __name__ == '__main__':
    app.run(debug=False)