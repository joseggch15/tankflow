# TankFlow Pipeline 🛢️

Pipeline en Python para replicar los cálculos del XLSX de análisis de tanques
(Main Tank + Virtual Tanks LFO 171-TK-03/04/05) a partir de CSVs.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución (CLI)

Desde la raíz del proyecto:

```bash
python -m tankflow.pipeline /ruta/historical_tank_volumes.csv \
  --transactions-csv /ruta/delivery_transaction.csv \
  --config tankflow/config/settings.yaml \
  --date-start "12/01/2026 00:00" \
  --date-end   "19/01/2026 23:59"
```

El pipeline genera:
- `outputs/tankflow_output.xlsx` (si export_xlsx=true)
- `outputs/tankflow_output_*.csv` (si export_csv=true)

## Qué calcula

- Time2 = MOD(Time, 1) (fracción del día)
- Minute, Hour, Date
- delta por tanque: Volume(t) - Volume(t-1)
- gains por virtual tank: IF(delta > threshold, delta, 0)
- conciliación: mt_delta_vt = delta_main - sum(gains_virtuals)
- pivots: Sum(Volume) por Hour×Tank
- detección de eventos de delivery por umbral y SUMIF(delta>0) dentro de ventana

## Tests

```bash
pytest -q
```
