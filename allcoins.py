#!/usr/bin/python3
"""Silver v2: vigila monedas de plata 1oz en andorrano-joyeria.com,
calcula la prima sobre el spot y notifica ofertas por Telegram.

Ejecucion: `allcoins.py` hace una pasada y sale (lo dispara un systemd timer).
"""
import csv
import datetime
import os
import re
import sys
import time

import requests
import yaml
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL_BASE = 'https://www.andorrano-joyeria.com'
URL_CATEGORIA = f'{URL_BASE}/tienda/monedas-de-plata/'
TELEGRAM_API = 'https://api.telegram.org'


def cargar_config():
    with open(os.path.join(BASE_DIR, 'config.yaml')) as f:
        return yaml.safe_load(f)


def crear_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    })
    retry = Retry(total=3, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def parse_precio(texto):
    limpio = re.sub(r'[^\d,]', '', texto.strip())
    if not limpio:
        raise ValueError(f"sin precio en '{texto}'")
    if ',' in limpio:
        limpio = limpio.replace('.', '').replace(',', '.')
    return float(limpio)


def obtener_spot_eur(session):
    try:
        r = session.get('https://api.gold-api.com/price/XAG', timeout=15)
        r.raise_for_status()
        usd_oz = float(r.json()['price'])
        r = session.get('https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR',
                        timeout=15)
        r.raise_for_status()
        cambio = float(r.json()['rates']['EUR'])
        return round(usd_oz * cambio, 2)
    except Exception as e:
        print(f"[ERROR] Spot indisponible: {type(e).__name__}: {e}")
        return None


def variante_de_slug(slug, keyword):
    """Devuelve la etiqueta de variante ('2026' o 'años varios') si el slug
    corresponde a la serie (keyword), o None si es otro producto."""
    kw = keyword.replace(' ', '-')
    prefijo = kw + '-'
    if not slug.startswith(prefijo):
        return None
    resto = slug[len(prefijo):]
    primero = resto.split('-')[0]
    if primero.isdigit() and len(primero) == 4:
        return primero
    if primero in ('1oz', 'plata', '30g'):
        return 'años varios'
    return None


def obtener_candidatos(session, series, errores):
    """Scrapea el catalogo y devuelve {keyword: [{url, variante}]}."""
    try:
        r = session.get(URL_CATEGORIA, timeout=20)
        r.raise_for_status()
    except Exception as e:
        errores.append(f"catálogo inaccesible: {type(e).__name__}: {e}")
        return {}
    soup = BeautifulSoup(r.content, 'html.parser')
    candidatos = {s['keyword']: [] for s in series}
    for enlace in soup.find_all('a', href=True):
        href = enlace['href']
        if not href.endswith('-info') or not href.startswith('/tienda/monedas-de-plata/'):
            continue
        slug = href.rstrip('-info').rsplit('/', 1)[-1]
        # Excluir tallas/pesos que no son 1 oz ni 30 g
        if any(f in slug for f in ('1-4', '1-2', '1-10', '1-20', '1kg', '150g')):
            continue
        if '1oz' not in slug and '30g' not in slug:
            continue
        for s in series:
            variante = variante_de_slug(slug, s['keyword'])
            if variante:
                candidatos[s['keyword']].append({
                    'url': URL_BASE + href,
                    'variante': variante,
                })
                break
    return candidatos


def obtener_precio(session, url, errores):
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        el = soup.select_one('.PricesalesPrice')
        if el is None:
            raise ValueError("selector .PricesalesPrice no encontrado")
        return parse_precio(el.get_text())
    except Exception as e:
        errores.append(f"{url.rsplit('/', 1)[-1]}: {type(e).__name__}: {e}")
        return None


def enviar_telegram(token, chat_id, texto):
    try:
        r = requests.post(
            f'{TELEGRAM_API}/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': texto},
            timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Telegram: {type(e).__name__}: {e}")


def guardar_csv(filas):
    path = os.path.join(BASE_DIR, 'historico.csv')
    nuevo = not os.path.isfile(path)
    with open(path, 'a', newline='') as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(['fecha_hora', 'serie', 'variante', 'precio_eur',
                        'spot_eur', 'prima_pct'])
        w.writerows(filas)


def main():
    config = cargar_config()
    tz = ZoneInfo(config.get('timezone', 'Europe/Madrid'))
    ahora = datetime.datetime.now(tz)
    token = open(os.path.join(BASE_DIR, config['token_file'])).read().strip()
    chat_id = str(config['chat_id'])
    errores = []

    session = crear_session()
    spot = obtener_spot_eur(session)

    series = config['series']
    resultados = []
    filas_csv = []
    ofertas = []

    if spot is None:
        errores.append('spot indisponible (gold-api/frankfurter)')
    else:
        candidatos = obtener_candidatos(session, series, errores)
        for s in series:
            nombre = s['name']
            opciones = candidatos.get(s['keyword'], [])
            if not opciones:
                errores.append(f"{nombre}: sin variantes en catálogo")
                continue
            precios = []
            for op in opciones:
                precio = obtener_precio(session, op['url'], errores)
                if precio is not None:
                    precios.append((precio, op))
                time.sleep(2)
            if not precios:
                errores.append(f"{nombre}: ninguna variante con precio legible")
                continue
            precio, op = min(precios, key=lambda x: x[0])
            prima_pct = round((precio / spot - 1) * 100, 1)
            resultados.append({'serie': nombre, 'variante': op['variante'],
                               'precio': precio, 'prima': prima_pct})
            filas_csv.append([ahora.strftime('%Y-%m-%d %H:%M'), nombre,
                              op['variante'], precio, spot, prima_pct])
            if prima_pct <= s['max_premium'] * 100:
                ofertas.append((nombre, op, precio, prima_pct))

    for nombre, op, precio, prima in ofertas:
        enviar_telegram(token, chat_id,
                        f"⚡ Oferta: {nombre} ({op['variante']}) a {precio} € "
                        f"({prima}% sobre spot de {spot} €/oz)\n{op['url']}")

    if filas_csv:
        guardar_csv(filas_csv)

    if ahora.hour == int(config.get('digest_hour', 10)):
        lineas = [f"📊 Silver diario — {ahora.strftime('%d/%m')}"]
        lineas.append(f"Spot plata: {'%.2f €/oz' % spot if spot else 'NO DISPONIBLE'}\n")
        for r_ in resultados:
            marca = ''
            if any(o[0] == r_['serie'] for o in ofertas):
                marca = ' ⚡'
            lineas.append(f"• {r_['serie']}: {r_['precio']} € "
                          f"({r_['prima']:+.1f}%) [{r_['variante']}]{marca}")
        faltantes = [s['name'] for s in series
                     if s['name'] not in [r_['serie'] for r_ in resultados]]
        for f_ in faltantes:
            lineas.append(f"• {f_}: ❌ sin datos")
        lineas.append(f"\n✅ {len(resultados)}/{len(series)} series | errores: {len(errores)}")
        for e in errores[:5]:
            lineas.append(f"  ❌ {e}")
        enviar_telegram(token, chat_id, '\n'.join(lineas))

    print(f"[OK] {ahora}: {len(resultados)} series, spot={spot}, errores={len(errores)}")


if __name__ == '__main__':
    main()
