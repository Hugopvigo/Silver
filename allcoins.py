import requests
import schedule
import time
import datetime
from bs4 import BeautifulSoup
from telegram_notifier import TelegramNotifier
  
# Obtener fecha y hora actual
ahora = datetime.datetime.now()
# Formatear la fecha y la hora como una cadena
cadena = ahora.strftime("%d/%m/%Y %H:%M:%S")
print(cadena)  
# Crear una lista de diccionarios con las urls, los nombres y los precios máximos de los productos que quieres analizar
products = [
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/otros-paises/germania-2023-1oz-plata-info", "name": "Germania", "max_price": 37},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/estados-unidos/estados-unidos-american-eagle-2023-1oz-plata-info", "name": "American Eagle", "max_price": 33},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/china/china-panda-2023-30-00g-plata-info", "name": "Panda", "max_price": 31},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/australia/australia-wedge-tailed-2023-1oz-plata-info", "name": "Wedge Tailed", "max_price": 30},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/australia/australia-koala-2023-1oz-plata-info", "name": "Koala", "max_price": 28},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/otros-paises/sudafrica-krugerrand-2023-1oz-plata-info", "name": "Krugerrand", "max_price": 26},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/reino-unido/reino-unido-britannia-2023-1oz-plata-info", "name": "Britannia", "max_price": 25},
{"url": "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/austria/austria-filarmonica-2023-1oz-plata-info", "name": "Filarmonica", "max_price": 28}
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
  stock_status = stock_text.replace("Debido a la situación actual, ciertos productos pueden sufrir retrasos excepcionales.", " ").replace("\n", "")
  
# Comparar el precio extraído con el precio máximo del diccionario y si es menor, imprimir un mensaje con el nombre y el precio del producto
  if price_number < product["max_price"]:
# Configurar el chat_id y el token del bot
    chat_id = "1333872" # Tu chat_id
    token = "6074866123:AAGacC5qvmV5IYOCEoJ8PZ2SBirmFyzd1rQ" # Tu token del bot
    notifier = TelegramNotifier(token=token, chat_id=chat_id, parse_mode="HTML")
# Enviar un mensaje al chat_id cuando se cumpla una condición    
    print(f"El {product['name']} está a {price_number} euros. ¡Es una buena oferta! | {stock_status}")
    notifier.send(f"El {product['name']} está a <b>{price_number} euros.</b> | {stock_status} | {cadena} | Compralo en: {product['url']}")
  elif price_number > product["max_price"]:
    print(f"{product['name']} está caro. {stock_status}")      
# Usar un bucle for para iterar sobre la lista de diccionarios y llamar a la función para cada uno
for product in products:
  check_price(product)    
# Programar la función para que se ejecute cada dos horas
  schedule.every().hour.do(check_price,product)
 # Ejecutar un bucle infinito que comprueba si hay tareas pendientes
while True:
  schedule.run_pending()
  time.sleep(1)