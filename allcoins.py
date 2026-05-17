#!/usr/bin/python
import requests
import schedule
import time
import datetime
import openpyxl
import os.path
import sys
import re
from bs4 import BeautifulSoup
from telegram_notifier import TelegramNotifier
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def parse_precio(texto: str) -> float:
    """Convierte formato europeo '1.234,56 €' a float 1234.56 de forma robusta."""
    limpio = re.sub(r'[^\d,\-]', '', texto.strip())
    if not limpio:
        raise ValueError(f"No se pudo extraer precio de: '{texto}'")

    # Detectar formato europeo (coma como separador decimal)
    if ',' in limpio:
        # Si también hay punto, el punto es separador de miles
        if '.' in limpio:
            limpio = limpio.replace('.', '').replace(',', '.')
        else:
            limpio = limpio.replace(',', '.')

    return float(limpio)


def sanitizar_stock(texto: str) -> str:
    """Limpia el texto de stock eliminando textos redundantes."""
    return (texto
            .replace("Debido a la situación actual, ciertos productos pueden sufrir retrasos excepcionales.", " ")
            .replace("\n", "")
            .replace("Estado:", "")
            .strip())


filename = 'precioplata.xlsx'
if os.path.isfile(filename):
    workbook = openpyxl.load_workbook(filename)
    sheet = workbook.active
else:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet['A1'] = 'Fecha y hora'
    sheet['B1'] = 'Moneda'
    sheet['C1'] = 'Precio'
    sheet['D1'] = 'Stock'

URL_BASE = 'https://www.andorrano-joyeria.com'
URL_CATEGORIA = f'{URL_BASE}/tienda/monedas-de-plata/'

# Productos que queremos rastrear (keyword → precio maximo)
# El script busca estos keywords en los nombres de la web
PRODUCTOS_DESEADOS = [
    {"keyword": "britannia", "name": "Britannia", "max_price": 25},
    {"keyword": "krugerrand", "name": "Krugerrand", "max_price": 26},
    {"keyword": "maple leaf", "name": "Maple Leaf", "max_price": 27},
    {"keyword": "canguro", "name": "Canguro", "max_price": 25},
    {"keyword": "panda", "name": "Panda", "max_price": 30},
    {"keyword": "malta", "name": "Malta", "max_price": 28},
]


def obtener_productos():
    """
    Scrapea la categoria de monedas de plata y devuelve los productos
    de 1 onza del anyo actual listos para checkear.

    Filtra para quedarse solo con productos de 1 onza o 30g
    (excluye 1/4, 1/2, 150g, 1kg, etc. y monedas de "varios anyos")
    del anyo en curso o posterior.
    """
    anyo = datetime.date.today().year
    anyo_corto = str(anyo)[-2:]
    productos_encontrados = []

    try:
        response = session.get(URL_CATEGORIA, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] No se pudo obtener el listado de productos: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Buscar todos los enlaces a productos (href contiene "-info")
    for enlace in soup.find_all('a', href=True):
        href = enlace['href']

        # Solo nos interesan enlaces a productos individuales
        if not href.endswith('-info'):
            continue
        if not href.startswith('/tienda/monedas-de-plata/'):
            continue

        # El nombre esta en el <a> dentro del <h3>
        nombre_tag = enlace.find_parent('li')
        if nombre_tag:
            h3 = nombre_tag.find('h3')
            if h3 and h3.find('a'):
                nombre_completo = h3.find('a').get_text(strip=True)
            else:
                continue
        else:
            continue

        # Normalizar nombre para busqueda
        nombre_lower = nombre_completo.lower()

        # Filtrar: solo 1 oz o 30g (nada de 1/4, 1/2, 150g, 1kg, etc.)
        if any(f in nombre_lower for f in ['1/4', '1/2', '1/10', '1/20', '1 kg', '1kg']):
            continue
        if '150 g' in nombre_lower or '150g' in nombre_lower:
            continue
        if '1 oz' not in nombre_lower and '1 onza' not in nombre_lower and '30 g' not in nombre_lower and '30g' not in nombre_lower:
            continue

        # Preferir el anyo actual frente a "varios anyos" o anyos anteriores
        if 'varios' in nombre_lower and len([c for c in nombre_lower if c.isdigit()]) <= 1:
            continue

        url_completa = URL_BASE + href

        # Extraer nombre limpio (quitar "Moneda de Plata " y " 1 oz")
        nombre_limpio = (nombre_completo
                         .replace('Moneda de Plata ', '')
                         .replace('Medalla de Plata ', '')
                         .strip())

        productos_encontrados.append({
            'url': url_completa,
            'name': nombre_limpio,
        })

    return productos_encontrados


def emparejar_productos():
    """
    Busca en la web los productos que queremos y los empareja
    con su max_price. Si no encuentra alguno, avisa pero no rompe.
    """
    catalogo = obtener_productos()
    if catalogo is None:
        print("[AVISO] No se pudo descargar el catalogo. Usando URLs por defecto.")
        return None

    if not catalogo:
        print("[AVISO] El catalogo esta vacio. Usando URLs por defecto.")
        return None

    print(f"\nCatalogo disponible ({len(catalogo)} monedas 1oz):")
    for p in catalogo:
        print(f"  - {p['name']}")
    print()

    productos_finales = []
    for deseado in PRODUCTOS_DESEADOS:
        keyword = deseado['keyword'].lower()
        # Buscar coincidencia en el catalogo
        coincidencia = None
        for p in catalogo:
            if keyword in p['name'].lower():
                coincidencia = p
                break

        if coincidencia:
            productos_finales.append({
                'url': coincidencia['url'],
                'name': deseado['name'],
                'max_price': deseado['max_price'],
            })
            print(f"  ✓ {deseado['name']} → {coincidencia['url']}")
        else:
            print(f"  ✗ {deseado['name']} — NO ENCONTRADO en el catalogo")

    return productos_finales


f = open("token.txt", "r")
token = f.read().strip()
f.close()
chat_id = "1333872"
notifier = TelegramNotifier(token=token, chat_id=chat_id, parse_mode="HTML")

# Sesión HTTP con User-Agent realista (simula un navegador normal)
# para que la web no bloquee las peticiones automáticas.
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
})

# Reintentos automáticos: si falla la conexión, timeout o da error 5xx,
# reintenta hasta 3 veces con espera progresiva (1s, 2s, 4s).
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


# Obtener productos de la web (con fallback a URLs por defecto)
products = emparejar_productos()
if not products:
    # Fallback: URLs generadas con el anyo actual
    anyo = datetime.date.today().year
    anyo_corto = str(anyo)[-2:]
    print("[FALLBACK] Usando URLs generadas con el anyo actual.")
    products = [
        {"url": f"{URL_BASE}/tienda/monedas-de-plata/reino-unido/reino-unido-britannia-kciii-{anyo}-1oz-plata-info", "name": f"Britannia {anyo_corto}", "max_price": 25},
        {"url": f"{URL_BASE}/tienda/monedas-de-plata/otros-paises/sudafrica-krugerrand-{anyo}-1oz-plata-info", "name": "Krugerrand", "max_price": 26},
        {"url": f"{URL_BASE}/tienda/monedas-de-plata/canada/canada-maple-leaf-{anyo}-1oz-plata-info", "name": "Maple Leaf", "max_price": 27},
        {"url": f"{URL_BASE}/tienda/monedas-de-plata/australia/australia-canguro-{anyo}-1oz-plata-info", "name": "Canguro", "max_price": 25},
        {"url": f"{URL_BASE}/tienda/monedas-de-plata/china/china-panda-{anyo}-30g-plata-info", "name": f"Panda {anyo_corto}", "max_price": 30},
        {"url": f"{URL_BASE}/tienda/monedas-de-plata/otros-paises/malta-cruz-de-malta-{anyo}-1oz-plata-info", "name": "Malta", "max_price": 28}
    ]


def check_price(product):
    ahora = datetime.datetime.now()
    cadena = ahora.strftime("%d/%m/%Y %H:%M")

    try:
        # Petición HTTP con timeout y validación
        response = session.get(product["url"], timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Extraer precio
        price_element = soup.find(class_="Price")
        if price_element is None:
            raise ValueError("No se encontró el elemento con clase 'Price'")

        price_text = price_element.get_text()
        price_number = parse_precio(price_text)

        # Extraer stock
        availability_element = soup.find(class_="availability")
        if availability_element is not None:
            availability_text = availability_element.get_text()
            availability_status = sanitizar_stock(availability_text)
        else:
            availability_status = "Sin información"

        # Guardar en Excel
        row = (cadena, product["name"], price_number, availability_status)
        sheet.append(row)

        # Notificar si es una buena oferta
        if (price_number < product["max_price"]
                and availability_status.lower() not in ["fuera de stock", "agotado temporalmente"]):
            print(f"{cadena} - La moneda {product['name']} está a {price_number} euros. ¡Es una buena oferta! | {availability_status}")
            notifier.send(
                f"TEST - La moneda {product['name']} está a <b>{price_number} euros.</b> "
                f"¡Es una buena oferta! | {availability_status} | {cadena} | "
                f"Compralo en: {product['url']}"
            )
        else:
            print(f"{cadena} - {product['name']} está a {price_number} euros. {availability_status}")

        workbook.save('precioplata.xlsx')

    except requests.exceptions.Timeout:
        print(f"{cadena} - Error: Timeout al consultar {product['name']}")
    except requests.exceptions.ConnectionError:
        print(f"{cadena} - Error: No se pudo conectar al consultar {product['name']}")
    except requests.exceptions.HTTPError as e:
        print(f"{cadena} - Error HTTP {e.response.status_code} al consultar {product['name']}")
    except ValueError as e:
        print(f"{cadena} - Error en datos de {product['name']}: {e}")
    except Exception as e:
        print(f"{cadena} - Error inesperado con {product['name']}: {type(e).__name__}: {e}")


def run_check():
    print(f"\n--- Ejecutando comprobación: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} ---")
    for product in products:
        check_price(product)
        time.sleep(2)  # Pequeña pausa entre productos para no saturar la web
    print("--- Comprobación finalizada ---\n")


# --- MODO DE EJECUCIÓN ---
# Sin argumentos: bucle infinito con scheduler cada 3h
# Con --cron: ejecuta una vez y sale (para usar con cron del sistema)

if '--cron' in sys.argv:
    # Ejecutar una vez y salir
    run_check()
    print("[CRON] Comprobación finalizada. Saliendo...")
else:
    # Ejecutar una vez al inicio
    run_check()

    # Programar cada 3 horas
    schedule.every(3).hours.do(run_check)

    # Bucle principal
    print("[SCHEDULER] Bucle infinito iniciado. Ctrl+C para salir.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[SCHEDULER] Detenido por el usuario.")
