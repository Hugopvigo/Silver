<div align="center">

# 🪙 Silver

### *Vigilante de primas sobre la plata*

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-blue?style=for-the-badge)

---

*Scrapea monedas de plata de 1 oz en andorrano-joyeria.com, calcula su prima*
*sobre el precio spot y avisa por Telegram cuando hay ganga. Con resumen*
*diario para saber que está vivo.*

</div>

---

## ✨ Características

| | |
|---|---|
| 📈 | **Umbral dinámico** — prima % sobre el spot XAG (gold-api.com + BCE), no precios fijos |
| 🪙 | **Una línea por serie** — de cada moneda vigila la variante más barata (año actual vs "años varios") |
| ⚡ | **Alertas instantáneas** — Telegram en cuanto una serie baja del umbral de prima |
| 📊 | **Resumen diario** — latido con spot, todas las series, sus primas y errores del día |
| 💾 | **Histórico CSV** — `historico.csv` con fecha, precio, spot y prima |
| 🔄 | **Reintentos** — backoff exponencial ante fallos de red; los errores nunca matan el digest |

---

## 🚀 Instalación

```bash
# 1. Clonar
git clone https://github.com/Hugopvigo/Silver.git
cd Silver

# 2. Entorno virtual
python3 -m venv .venv
.venv/bin/pip install requests beautifulsoup4 pyyaml

# 3. Configurar
#    - token.txt: token del bot de Telegram
#    - config.yaml: chat_id, hora del resumen y series vigiladas
```

### Despliegue en VPS (systemd timer)

```bash
sudo cp deploy/silver.service deploy/silver.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now silver.timer

# Ver el estado
systemctl list-timers silver.timer
journalctl -u silver -f
```

---

## ⚙️ Configuración (`config.yaml`)

```yaml
digest_hour: 10          # hora (Europe/Madrid) del resumen diario
timezone: Europe/Madrid
chat_id: "1333872"
token_file: token.txt
series:
  - {name: Britannia,   keyword: britannia,   max_premium: 0.05}
  - {name: Krugerrand,  keyword: krugerrand,  max_premium: 0.05}
  # keyword = fragmento inicial del slug en la URL de la tienda
  # max_premium = prima máxima sobre spot antes de avisar (0.05 = 5%)
```

---

## 🔔 Ejemplo de resumen diario

```
📊 Silver diario — 23/08
Spot plata: 59,07 €/oz

• Britannia: 77,07 € (+30.5%) [años varios]
• Krugerrand: 79,88 € (+35.2%) [2026]
• Panda 30g: 83,47 € (+41.3%) [2026]
...

✅ 6/6 series | errores: 0
```

---

## 📁 Estructura

```
Silver/
├── allcoins.py      ← Script principal (corre y sale; lo dispara systemd)
├── config.yaml      ← Series, umbrales y Telegram
├── token.txt        ← Token del bot (no versionado)
├── historico.csv    ← Histórico de precios (se genera solo)
└── docs/superpowers/specs/  ← Diseño de la v2
```

`precioplata.xlsx`, `GoogleSheet.py` y `coin.py` son legado de la v1.

---

## 📝 License

**CC BY-NC-SA 4.0** — Consulta [LICENSE](LICENSE) para más detalles.
