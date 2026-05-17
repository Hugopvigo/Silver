# Instalación en VPS con Cron 🪙

Guía paso a paso para montar el script en un servidor y que se ejecute **cada 6 horas** automáticamente.

---

## Requisitos

- Un VPS con **Ubuntu 20.04 o superior** (u otro Linux)
- **Python 3.8+** instalado
- **Git** instalado

---

## Paso 1: Conectarse al VPS

```bash
ssh usuario@tu-vps.com
```

---

## Paso 2: Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Paso 3: Clonar el repositorio

```bash
cd /opt
sudo git clone https://github.com/tuusuario/Silver.git
sudo chown -R $USER:$USER /opt/Silver
cd /opt/Silver
```

---

## Paso 4: Crear entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4 schedule openpyxl telegram-notifier
```

Para saber exactamente qué versiones tienes:
```bash
pip freeze > requirements.txt
```

---

## Paso 5: Configurar el token de Telegram

Crea el archivo con tu token de Telegram:

```bash
nano token.txt
```

Pega tu token dentro (el que te da [@BotFather](https://t.me/BotFather)) y guarda (`Ctrl+O`, `Enter`, `Ctrl+X`).

> ⚠️ **Importante:** Este archivo ya está en `.gitignore`, no se subirá al repo.

---

## Paso 6: Probar que funciona

Ejecuta una vez para ver si todo va bien:

```bash
cd /opt/Silver
source venv/bin/activate
python3 allcoins.py --cron
```

Deberías ver algo como:

```
Catalogo disponible (60 monedas 1oz):
  - Britannia 2026 1 oz
  - Krugerrand 2026 1 oz
  ...

  ✓ Britannia → https://www.andorrano-joyeria.com/...
  ✓ Krugerrand → https://www.andorrano-joyeria.com/...
  ...

--- Ejecutando comprobación: 17/05/2026 12:00 ---
12:00 - Britannia está a 26.50 euros. Disponible
12:00 - Krugerrand está a 27.80 euros. Disponible
...
--- Comprobación finalizada ---

[CRON] Comprobación finalizada. Saliendo...
```

Si ves errores, revisa que el token de Telegram sea correcto y que el VPS tenga conexión a internet.

---

## Paso 7: Configurar Cron (ejecución cada 6 horas)

Abre el crontab del usuario:

```bash
crontab -e
```

(Elige `nano` si te pregunta qué editor usar)

Añade esta línea al final:

```bash
0 */6 * * * cd /opt/Silver && /opt/Silver/venv/bin/python3 allcoins.py --cron >> /opt/Silver/silver.log 2>&1
```

**Explicación de la línea:**
- `0 */6 * * *` → Cada 6 horas, en el minuto 0 (00:00, 06:00, 12:00, 18:00)
- `cd /opt/Silver` → Va a la carpeta del proyecto
- `/opt/Silver/venv/bin/python3 allcoins.py --cron` → Ejecuta el script una vez
- `>> /opt/Silver/silver.log 2>&1` → Guarda toda la salida en un archivo de log

Guarda y cierra (`Ctrl+O`, `Enter`, `Ctrl+X`).

> ⚠️ **Usamos la ruta completa al Python del venv** (`/opt/Silver/venv/bin/python3`) para que cron sepa exactamente qué ejecutar.

---

## Paso 8: Verificar que Cron está activo

```bash
crontab -l
```

Deberías ver tu línea. Para ver los logs:

```bash
tail -f /opt/Silver/silver.log
```

El Excel con los precios se guarda en:

```bash
ls -la /opt/Silver/precioplata.xlsx
```

---

## Comandos útiles

| Qué quieres hacer | Comando |
|-------------------|---------|
| Ver próximas ejecuciones de cron | `crontab -l` |
| Ver el log en tiempo real | `tail -f /opt/Silver/silver.log` |
| Ejecutar una vez manualmente | `cd /opt/Silver && source venv/bin/activate && python3 allcoins.py --cron` |
| Ver el Excel (conteo de líneas) | `cd /opt/Silver && python3 -c "import openpyxl; w=openpyxl.load_workbook('precioplata.xlsx'); print(f'{w.active.max_row} filas')"` |
| Parar cron temporalmente | `crontab -e` y comenta la línea con `#` |
| Descargar el Excel del VPS (local) | `scp usuario@tu-vps.com:/opt/Silver/precioplata.xlsx .` |

---

## Solución de problemas

**"No se encuentra el módulo X"**
Asegúrate de activar el venv: `source /opt/Silver/venv/bin/activate`

**Cron no ejecuta nada**
Revisa los logs del sistema: `grep CRON /var/log/syslog`

**El Excel se ve raro en Google Sheets**
Descárgalo y ábrelo con Excel o LibreOffice. El script lo guarda en formato `.xlsx`.

**Precio muestra "Sin información"**
La web cambió ligeramente — el script ya no encuentra la clase `availability`. Revisa si hay que actualizar el scraping.

**No encuentra el Panda (u otro producto)**
El script busca los productos en el catálogo de la web automáticamente. Si un producto no aparece, lo notifica en el log y usa la URL por defecto del año actual. Revisa `silver.log`.

---

## Seguridad

- El token de Telegram está en `token.txt` → ya está en `.gitignore`
- No compartas `token.txt` ni el Excel si contiene precios sensibles
- Para mayor seguridad, usa variables de entorno (avanzado):
  ```bash
  export TELEGRAM_TOKEN="tu-token"
  ```
  Y modifica el script para usar `os.getenv('TELEGRAM_TOKEN')`

---

## Notas sobre la frecuencia

- El script espera **2 segundos entre producto y producto** para no saturar la web
- Con 6 productos son ~12 segundos por ejecución
- Cada 6 horas son **~48 segundos al día** de tráfico a la web — muy ligero
- Si quieres cambiar la frecuencia, edita el crontab:
  - Cada 4h: `0 */4 * * *`
  - Cada 12h: `0 */12 * * *`
  - Cada día a las 9 de la mañana: `0 9 * * *`
