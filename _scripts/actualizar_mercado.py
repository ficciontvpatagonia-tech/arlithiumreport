#!/usr/bin/env python3
"""
actualizar_mercado.py — Cotizaciones reales para AR Lithium Report.
Fuente: Yahoo Finance (gratuito, sin API key). Genera SITIO/data/mercado.json
con precio, variación % diaria y cierres de 7 días para los sparklines.
Uso: python3 SCRIPTS/actualizar_mercado.py   (desde la raíz del proyecto)
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent  # raíz del repo
SALIDA = RAIZ / "data" / "mercado.json"

# symbol Yahoo -> (etiqueta corta, descripción, moneda para formato)
INSTRUMENTOS = [
    ("LTH=F",     "LiOH CIF CJK",  "Lithium hydroxide (Fastmarkets) · COMEX", "USD/kg"),
    ("LIT",       "LIT ETF",       "Global X Lithium & Battery Tech · NYSE",  "USD"),
    ("ALB",       "ALB",           "Albemarle · NYSE",                        "USD"),
    ("SQM",       "SQM",           "SQM · NYSE",                              "USD"),
    ("LAR",       "LAR",           "Lithium Argentina · NYSE",                "USD"),
    ("PLS.AX",    "PLS",           "Pilbara Minerals · ASX",                  "AUD"),
    ("002460.SZ", "GANFENG",       "Ganfeng Lithium · SZSE",                  "CNY"),
    ("RIO",       "RIO",           "Rio Tinto (Arcadium) · NYSE",             "USD"),
]

def traer(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=7d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    res = d["chart"]["result"][0]
    meta = res["meta"]
    quote = (res.get("indicators", {}).get("quote") or [{}])[0]
    closes = [c for c in (quote.get("close") or []) if c is not None]
    precio = meta.get("regularMarketPrice")
    if precio is None:
        raise ValueError("sin precio")
    # la última barra diaria ya refleja el precio actual (o el cierre de hoy);
    # la variación diaria es contra la barra anterior = cierre de ayer
    previo = closes[-2] if len(closes) > 1 else None
    var = ((precio - previo) / previo * 100) if previo else 0.0
    return precio, var, closes[-8:]

def formatear(precio, moneda):
    simbolo = {"USD": "$", "AUD": "A$", "CNY": "¥", "USD/kg": "$"}[moneda]
    if precio >= 1000:
        txt = f"{precio:,.0f}"
    elif precio >= 100:
        txt = f"{precio:,.2f}"
    else:
        txt = f"{precio:.2f}"
    sufijo = "/kg" if moneda == "USD/kg" else ""
    return f"{simbolo}{txt}{sufijo}"

def main():
    datos = []
    for symbol, corto, descripcion, moneda in INSTRUMENTOS:
        try:
            precio, var, cierres = traer(symbol)
            datos.append({
                "symbol": symbol,
                "corto": corto,
                "descripcion": descripcion,
                "precio": formatear(precio, moneda),
                "variacion": round(var, 2),
                "cierres": [round(c, 4) for c in cierres],
            })
            print(f"  {corto:10s} {formatear(precio, moneda):>12s}  {var:+.2f}%")
        except Exception as e:
            print(f"  {corto}: ERROR {e} — se omite")
        time.sleep(1)
    if len(datos) < 5:
        raise SystemExit("Muy pocos instrumentos respondieron; no se sobrescribe el JSON.")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    contenido = json.dumps({
        "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fuente": "Yahoo Finance",
        "instrumentos": datos,
    }, ensure_ascii=False, indent=1)
    SALIDA.write_text(contenido)
    # variante .js para que la página funcione también abierta como archivo local (sin fetch)
    (SALIDA.parent / "mercado.js").write_text("window.MERCADO = " + contenido + ";")
    print(f"OK → {SALIDA} (+ mercado.js)")

if __name__ == "__main__":
    main()
