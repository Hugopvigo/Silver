# Silver v2 — Diseño

Fecha: 2026-08-23
Estado: aprobado por Hugo

## Contexto

Silver vigila el precio de monedas de plata de 1 oz en andorrano-joyeria.com y avisa
por Telegram cuando hay buena oferta. El bot murió en silencio el 12-01-2025: la web
migró a VirtueMart, cambió el HTML (`class="Price"` → `class="PricesalesPrice"`) y el
proceso `nohup` crasheó sin que nadie se enterara. Además los umbrales fijos de 2023
(25–30 €) están muy por debajo del mercado actual (~79 €/moneda), así que aunque
estuviera vivo jamás notificaría.

## Objetivos

1. Detectar ofertas con un criterio que se adapte al mercado: prima % sobre spot.
2. Que sea imposible que muera en silencio: resumen diario a Telegram como latido.
3. Despliegue simple y observable en VPS 7 (Oracle Ampere).

## No objetivos

- Ampliar tiendas fuente.
- Dashboard web o histórico consultable fuera del CSV.
- Contenedor Docker (se descarta por innecesario para un script oneshot).

## Arquitectura

Script Python único (`allcoins.py`) ejecutado en modo *corre-y-sale* (`--cron`)
por un `systemd.timer` cada hora en VPS 7. Sin bucle infinito ni `schedule`.

### Flujo de cada ejecución

1. Obtener spot XAG/USD (`api.gold-api.com/price/XAG`, JSON sin key) y convertir a EUR
   con `frankfurter.app` (BCE, sin key). Si falla → error registrado, no hay checks.
2. Scrapear catálogo `/tienda/monedas-de-plata/`; para cada serie vigilada, recoger las
   variantes existentes (año actual, "años varios") filtrando 1 oz / 30 g.
3. Extraer precio de cada página candidata (`div.PricesalesPrice`).
4. Por serie quedarse con la **variante más barata**; calcular prima % sobre spot.
5. Si prima ≤ umbral de la serie → notificación inmediata de oferta por Telegram.
6. Añadir líneas al `historico.csv`.
7. Si la hora local (Europe/Madrid) es la del digest → enviar resumen diario.

### Resumen diario (latido)

Hora fija configurable (10:00 Europe/Madrid). Formato:

```
📊 Silver diario — 23/08
Spot plata: 78,20 €/oz

• Britannia: 77,50 € (+0,9%) [años varios]
• Krugerrand: 81,00 € (+3,6%) [2026]
...
✅ 6 series vigiladas | errores: 0
```

Si el bot está caído, el mensaje no llega → se sabe al día siguiente. Los errores del
día (spot caído, web caída, selector roto) se listan en el digest siguiente; nunca
matan la ejecución.

### Configuración — `config.yaml`

Series vigiladas (keyword, prima máxima), chat ID, ruta del token y hora del digest.
Añadir una serie = editar una línea.

```yaml
digest_hour: 10
timezone: Europe/Madrid
chat_id: "1333872"
token_file: token.txt
series:
  - {name: Britannia,   keyword: britannia,   max_premium: 0.05}
  - {name: Krugerrand,  keyword: krugerrand,  max_premium: 0.05}
  - {name: Maple Leaf,  keyword: maple leaf,  max_premium: 0.05}
  - {name: Canguro,     keyword: canguro,     max_premium: 0.05}
  - {name: Panda 30g,   keyword: panda,       max_premium: 0.05}
  - {name: Filarmonica, keyword: filarmonica, max_premium: 0.05}
```

### Telegram

Llamada directa a `api.telegram.org/sendMessage` con `requests`. Se elimina la
dependencia de `telegram_notifier`.

## Datos

- `historico.csv`: `fecha_hora,serie,variante,precio_eur,spot_eur,prima_pct`.
- `precioplata.xlsx` se conserva como archivo histórico, deja de escribirse.

## Despliegue (VPS 7)

- Directorio: `~/dev/Silver` (checkout git existente).
- venv propio con `requests`, `beautifulsoup4`, `pyyaml`.
- `silver.service` (Type=oneshot) + `silver.timer` (OnCalendar=hourly).
- Logs en journald (`journalctl -u silver`).
- Zona horaria del cálculo del digest: Europe/Madrid vía `zoneinfo`.

## Manejo de errores

- Timeout / conexión: reintento HTTP ya existente (Retry ×3); si persiste, se registra.
- Spot indisponible: no se evalúan ofertas esa vuelta; el digest lo refleja.
- Selector roto (web cambia): error por producto, registrado; digest sigue llegando
  con las series que sí funcionaron → fallo visible en <24 h.
