#!/usr/bin/python
import requests
import schedule
import time
import datetime
import openpyxl
import os.path
import sys
from bs4 import BeautifulSoup
from telegram_notifier import TelegramNotifier


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

products = [
    {"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/reino-unido/reino-unido-britannia-kciii-2024-1oz-plata-info", "name": "Britannia 24", "max_price": 25},
    {"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/otros-paises/sudafrica-krugerrand-2024-1oz-plata-info", "name": "Krugerrand", "max_price": 26},
    {"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/canada/canada-maple-leaf-2024-1oz-plata-info", "name": "Maple Leaf", "max_price": 27},
    {"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/australia/australia-canguro-2024-1oz-plata-info", "name": "Canguro", "max_price": 25},
    {"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/china/china-panda-2024-30g-plata-info", "name": "Panda 24", "max_price": 30},
    {"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/otros-paises/malta-cruz-de-malta-2024-1oz-plata-info", "name": "Malta", "max_price": 28}
]

f = open("token.txt", "r")
token = f.read().strip()
f.close()
chat_id = "1333872"
notifier = TelegramNotifier(token=token, chat_id=chat_id, parse_mode="HTML")


def check_price(product):
    response = requests.get(product["url"])
    soup = BeautifulSoup(response.content, "html.parser")

    price_element = soup.find(class_="Price")
    availability_element = soup.find(class_="availability")

    price_text = price_element.get_text()
    price_number = float(price_text.replace("€", "").replace(",", "."))

    availability_text = availability_element.get_text()
    availability_status = availability_text.replace("Debido a la situación actual, ciertos productos pueden sufrir retrasos excepcionales.", " ").replace("\n", "").replace("Estado:", "").strip()
    
    ahora = datetime.datetime.now()
    cadena = ahora.strftime("%d/%m/%Y %H:%M")

    row = (cadena, product["name"], price_number, availability_status)
    sheet.append(row)

    if price_number < product["max_price"] and availability_status.lower() not in ["fuera de stock", "agotado temporalmente"]:
        print(f"{cadena} - La moneda {product['name']} está a {price_number} euros. ¡Es una buena oferta! | {availability_status}")
        notifier.send(f"TEST - La moneda {product['name']} está a <b>{price_number} euros.</b> ¡Es una buena oferta! | {availability_status} | {cadena} | Compralo en: {product['url']}")
    else:
        print(f"{cadena} - {product['name']} está a {price_number} euros. {availability_status}")

    workbook.save('precioplata.xlsx')


def run_check():
    for product in products:
        check_price(product)


for product in products:
    check_price(product)

schedule.every(3).hours.do(run_check)

while True:
    schedule.run_pending()
    time.sleep(2)
