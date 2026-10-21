<meta property="og:title" content="SILVER">
<meta property="og:description" content="Un vigilante de primas sobre las monedas de plata de 1 onza.">
<meta property="og:image" content="https://raw.githubusercontent.com/Hugopvigo/Silver/main/og.png">


<p align="center">
  <img src="cabecera.png" alt="Silver — vigilante de primas sobre las monedas de plata" width="100%">
</p>

<p align="center">
  <b>Un vigilante de primas sobre las monedas de plata de 1 onza.</b><br>
  Raspa el catálogo de la tienda, compara cada serie con el spot y avisa por Telegram cuando entra en el umbral.
</p>

<p align="center">
  <img alt="python" src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&labelColor=1a1a1e">
  <img alt="telegram" src="https://img.shields.io/badge/Telegram-bot-26A5E4?style=flat-square&labelColor=1a1a1e">
  <img alt="licencia" src="https://img.shields.io/badge/licencia-CC%20BY--NC--SA%204.0-8E8E93?style=flat-square&labelColor=1a1a1e">
  <img alt="despliegue" src="https://img.shields.io/badge/VPS-systemd%20timer-8E8E93?style=flat-square&labelColor=1a1a1e">
</p>

---

## Qué es esto

Un script de Python que **vigila la prima de las monedas de plata** (1 onza y
las de 30 g) de una tienda online y **avisa por Telegram** cuando alguna cae
por debajo del umbral que tú pongas.

Una pasada y sale: lo lanza un `systemd timer` cada hora.

Lo que hace, en orden:

1. **Lee el spot de la plata**: precio XAG en dólares por onza de
   `api.gold-api.com`, convertido a euros con el tipo de cambio que da
   `api.frankfurter.dev` (USD → EUR).
2. **Raspa el catálogo** `andorrano-joyeria.com/tienda/monedas-de-plata/`: se
   queda con los enlaces de producto que son de 1 onza o de 30 g, descartando
   el resto de tamaños (1/4, 1/2, 1/10, 1/20, 1 kg, 150 g).
3. **Calcula la prima** de cada serie: `(precio / spot − 1) × 100`.
4. **Avisa** por Telegram de cada serie cuya prima esté en o por debajo del
   umbral, con el precio, la prima y el enlace al producto.
5. **Guarda el histórico** en `historico.csv` y, una vez al día, manda el
   **resumen** con el spot, todas las series, sus primas y los errores de la
   pasada.

De cada serie se queda con la **variante más barata** (el año en curso o el
lote «años varios»).

## Series vigiladas

Las define `config.yaml`. Por defecto son ocho:

| Serie | `keyword` | Umbral |
|---|---|---|
| Britannia | `britannia` | 5 % |
| Krugerrand | `krugerrand` | 5 % |
| Maple Leaf | `maple-leaf` | 5 % |
| Canguro | `canguro` | 5 % |
| Panda 30 g | `panda` | 5 % |
| Filarmónica | `filarmonica` | 5 % |
| American Eagle | `american-eagle` | 5 % |
| Libertad | `libertad-de-mexico` | 5 % |

El `keyword` es el inicio del *slug* del producto en la URL; el script deduce
la variante del resto del *slug* (`britannia-2026-1oz-plata` → «2026»,
`britannia-1oz-plata` → «años varios»).

## Instalación

```bash
git clone https://github.com/Hugopvigo/silver.git
cd silver

python3 -m venv .venv
.venv/bin/pip install requests beautifulsoup4 pyyaml
```

Después, dos cosas:

- **`token.txt`**: el token del bot de Telegram, el que da
  [@BotFather](https://t.me/BotFather). Va en un fichero de texto en la raíz
  del repo y está en `.gitignore`: no se versiona.
- **`config.yaml`**: `chat_id` (el chat donde recibes los avisos), la hora del
  resumen diario, la zona horaria y las series con su umbral.

```yaml
digest_hour: 10          # hora (Europe/Madrid) del resumen diario
timezone: Europe/Madrid
chat_id: "<id del chat>"
token_file: token.txt
series:
  - {name: Britannia, keyword: britannia, max_premium: 0.05}
  # max_premium: prima máxima sobre spot antes de avisar (0.05 = 5 %)
```

### Probarlo

```bash
.venv/bin/python allcoins.py
```

Imprime una línea de resumen por consola y manda a Telegram lo que toque.

### Dejarlo corriendo (systemd timer)

```bash
sudo cp deploy/silver.service deploy/silver.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now silver.timer

systemctl list-timers silver.timer
journalctl -u silver -f
```

El `timer` dispara el `service` **cada hora**, con un retraso aleatorio de
hasta 5 minutos; `Persistent=true` hace que se recupere si el servidor estaba
apagado. Antes de activarlo, ajusta en `deploy/silver.service` el usuario y
las rutas (`User`, `WorkingDirectory`, `ExecStart`).

## Los mensajes de Telegram

Aviso de oferta, en cuanto una serie baja del umbral:

```
⚡ Oferta: Britannia (2026) a 71.5 € (4.2% sobre spot de 68.6 €/oz)
https://www.andorrano-joyeria.com/tienda/monedas-de-plata/...
```

Resumen diario, a la hora de `digest_hour`:

```
📊 Silver diario — 23/08
Spot plata: 59.07 €/oz

• Britannia: 77.07 € (+30.5%) [años varios]
• Krugerrand: 79.88 € (+35.2%) [2026]
• Panda 30g: 83.47 € (+41.3%) [2026]
...

✅ 8/8 series | errores: 0
```

Las series sin datos en esa pasada salen con `❌ sin datos`, y debajo se
listan hasta cinco errores de la ejecución.

## Detalles de cómo funciona

- **Precios**: se leen del selector `.PricesalesPrice` de la ficha de cada
  producto; el formato europeo (`1.234,56 €`) se convierte a número.
- **Reintentos**: las peticiones `GET` se reintentan hasta 3 veces con
  espera creciente ante `429` y errores de servidor `5xx`.
- **Ritmo**: 2 segundos entre producto y producto, para no cargar la web.
- **Errores**: uno de una serie no tumba la pasada; se anotan y se listan en el
  resumen.
- **Histórico**: `historico.csv` (se genera solo) con las columnas
  `fecha_hora, serie, variante, precio_eur, spot_eur, prima_pct`.

## Estructura

```
silver/
├── allcoins.py        script principal: una pasada y sale
├── config.yaml        series, umbrales y datos de Telegram
├── token.txt          token del bot (no versionado)
├── historico.csv      histórico de precios (se genera solo)
├── deploy/
│   ├── silver.service unidad systemd (oneshot)
│   └── silver.timer   timer horario
├── cabecera.png        cabecera del README
├── Install.md         guía de instalación de la v1 (legado)
├── coin.py            prueba de precio de una moneda (legado)
├── GoogleSheet.py     ejemplo de subida a Google Sheets (legado)
├── precioplata.xlsx   libro de precios de la v1 (legado)
└── exit.txt           log de la v1 (legado)
```

## Licencia

El material de este repositorio está bajo **CC BY-NC-SA 4.0** (Creative Commons
Atribución-NoComercial-CompartirIgual 4.0): puedes compartirlo y adaptarlo
para fines no comerciales, citando la fuente y manteniendo la misma licencia.
Ver [LICENSE](LICENSE).
