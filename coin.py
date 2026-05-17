import requests
import re
from bs4 import BeautifulSoup


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


# Configuración
name = 'Australia Canguro'
url = "https://www.andorrano-joyeria.com/tienda/monedas-de-plata/australia/australia-canguro-2023-1oz-plata-info"

try:
    # Petición HTTP con timeout y validación
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Buscar el elemento que contiene el precio
    price_element = soup.find(class_="Price")
    if price_element is None:
        raise ValueError("No se encontró el elemento con clase 'Price' en la página")

    price_text = price_element.get_text()
    price_number = parse_precio(price_text)

    print(f"El precio del {name} es {price_number} euros.")

except requests.exceptions.Timeout:
    print(f"Error: Timeout al conectar con {url}")
except requests.exceptions.ConnectionError:
    print(f"Error: No se pudo conectar con {url}")
except requests.exceptions.HTTPError as e:
    print(f"Error HTTP {e.response.status_code} al acceder a {url}")
except ValueError as e:
    print(f"Error en el parseo: {e}")
except Exception as e:
    print(f"Error inesperado: {type(e).__name__}: {e}")
