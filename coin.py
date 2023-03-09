import requests
from bs4 import BeautifulSoup

# Hacer una petición HTTP a la web
url = "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/australia/australia-canguro-2023-1oz-plata-info"
response = requests.get(url)

# Crear un objeto BeautifulSoup con el contenido HTML de la respuesta
soup = BeautifulSoup(response.content, "html.parser")

# Buscar el elemento que contiene el precio del producto
price_element = soup.find(class_="Price")

# Extraer el texto del elemento y convertirlo a un número
price_text = price_element.get_text()
price_number = float(price_text.replace("€", "").replace(",", "."))

# Imprimir el precio del producto
print(f"El precio del Australia Canguro es {price_number} euros.")