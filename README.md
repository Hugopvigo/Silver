<div align="center">

# 🪙 Silver

### *Precios de la plata en tiempo real*

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-blue?style=for-the-badge)

---

*Script que obtiene los precios de monedas de plata,*
*los exporta a Google Sheets y envía alertas por Telegram.*

</div>

---

## ✨ Características

| | |
|---|---|
| 🪙 | **Múltiples monedas** — precio de plata en diversas divisas |
| 📊 | **Google Sheets** — exporta automáticamente a una hoja de cálculo |
| 🔔 | **Alertas Telegram** — notificación cuando cambia el precio |
| ⏰ | **Automático** — ejecución programada cada 6 horas |
| 🔄 | **Reintentos** — manejo robusto de errores de red |

---

## 🚀 Instalación

### Requisitos

- Python 3.8+
- Cuenta de Google Sheets API
- Bot de Telegram (optional)

### Pasos

```bash
# 1. Clonar
git clone https://github.com/Hugopvigo/Silver.git
cd Silver

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar
cp .env.example .env
# Editar .env con tus credenciales

# 4. Ejecutar
python allcoins.py
```

### Despliegue en VPS (cron)

```bash
# Editar crontab
crontab -e

# Añadir (cada 6 horas):
0 */6 * * * cd /home/user/Silver && python3 allcoins.py >> salida.log 2>&1
```

Ver [Install.md](Install.md) para guía completa.

---

## 📁 Estructura

```
Silver/
├── allcoins.py         ← Script principal
├── coin.py             ← Lógica de parsing de precios
├── GoogleSheet.py      ← Exportación a Google Sheets
├── precioplata.xlsx    ← Datos de referencia
└── Install.md          ← Guía de instalación en VPS
```

---

## 🛠️ Uso

```bash
# Ejecución directa
python3 allcoins.py

# Con logs
nohup python3 allcoins.py > salida.log 2>&1 &

# Ver logs
tail -f salida.log
```

---

## 📝 License

**CC BY-NC-SA 4.0** — Consulta [LICENSE](LICENSE) para más detalles.
