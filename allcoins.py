#!/usr/bin/python
import requests
import schedule
import time
import datetime
import openpyxl
import os.path
from bs4 import BeautifulSoup
from telegram_notifier import TelegramNotifier


# Verificar si el archivo ya existe   
filename = f'precioplata.xlsx'
if os.path.isfile(filename):
    workbook = openpyxl.load_workbook(filename)
    sheet = workbook.active
else:
  # Crear un libro de Excel
  workbook = openpyxl.Workbook()
  # Seleccionar la hoja activa
  sheet = workbook.active
  # Escribir encabezados de las columnas
  sheet['A1'] = 'Fecha y hora'
  sheet['B1'] = 'Moneda'
  sheet['C1'] = 'Precio'
  sheet['D1'] = 'Stock'

# Crear una lista de diccionarios con las urls, los nombres y los precios máximos de los productos que quieres analizar
products = [
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/otros-paises/germania-2023-1oz-plata-info", "name": "Germania", "max_price": 36},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/estados-unidos/estados-unidos-american-eagle-2023-1oz-plata-info", "name": "American Eagle", "max_price": 33},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/china/china-panda-2023-30-00g-plata-info", "name": "Panda", "max_price": 31},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/australia/australia-wedge-tailed-2023-1oz-plata-info", "name": "Wedge Tailed", "max_price": 30},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/australia/australia-koala-2023-1oz-plata-info", "name": "Koala", "max_price": 28},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/otros-paises/sudafrica-krugerrand-2023-1oz-plata-info", "name": "Krugerrand", "max_price": 26},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/reino-unido/reino-unido-britannia-2023-1oz-plata-info", "name": "Britannia", "max_price": 25},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/austria/austria-filarmonica-2023-1oz-plata-info", "name": "Filarmonica", "max_price": 24}
]

# Definir una función que reciba un diccionario como argumento y extraiga el precio de la url usando beautifulsoup
def check_price(product):
 
  # Hacer una petición HTTP a la url del producto
  response = requests.get(product["url"])

  # Crear un objeto BeautifulSoup con el contenido HTML de la respuesta
  soup = BeautifulSoup(response.content, "html.parser")
     
  # Buscar el elemento que contiene el precio y el stock del producto usando un selector CSS
  price_element = soup.find(class_="Price")
  stock_element = soup.find(class_="stock")

  # Extraer el texto del elemento y convertirlo a un número
  price_text = price_element.get_text()
  price_number = float(price_text.replace("€", "").replace(",", "."))

  # Extraer el texto de stock
  stock_text = stock_element.get_text()
  stock_status = stock_text.replace("Debido a la situación actual, ciertos productos pueden sufrir retrasos excepcionales.", " ").replace("\n", "").replace("Estado:", "")

  # Obtener fecha y hora actual
  ahora = datetime.datetime.now()
  # Formatear la fecha y la hora como una cadena
  cadena = ahora.strftime("%d/%m/%Y %H:%M") 

  # Comparar el precio extraído con el precio máximo de la lista y si es menor, imprimir un mensaje con el nombre y el precio del producto
  if price_number < product["max_price"]:     
    # Configurar el chat_id y el token del bot
    f = open("token.txt", "r")
    Token = f.read()
    chat_id = "1333872" # Tu chat_id
    token = Token # Tu token del bot
    notifier = TelegramNotifier(token=token, chat_id=chat_id, parse_mode="HTML")
    # Enviar un mensaje al chat_id cuando se cumpla una condición    
    print(cadena, f"La moneda {product['name']} está a {price_number} euros. ¡Es una buena oferta! | {stock_status}")
    row = (cadena, f"{product['name']}", f"{price_number} ", f"{stock_status}")
    sheet.append(row)
    notifier.send(f"La moneda {product['name']} está a <b>{price_number} euros.</b> ¡Es una buena oferta! | {stock_status} | {cadena} | Compralo en: {product['url']}")
  elif price_number > product["max_price"]:
    print(cadena, f"{product['name']} está a {price_number} euros y es caro. {stock_status}")      
    row = (cadena, f"{product['name']}", f"{price_number}", f"{stock_status}")
    sheet.append(row)
    # Guardar el archivo de Excel
    workbook.save('precioplata.xlsx')
# Usar un bucle for para iterar sobre la lista de productos y llamar a la función para cada uno
for product in products:
  check_price(product)    
  # Programar la función para que se ejecute cada dos horas
  schedule.every(3).hours.do(check_price,product)
# Ejecutar un bucle infinito que comprueba si hay tareas pendientes
while True:
  schedule.run_pending()
  time.sleep(2)  