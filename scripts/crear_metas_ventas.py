"""
Script DBA: Creación y carga de tabla metas_ventas
====================================================
Diseño:
  - Una fila por tienda × día calendario
  - Contiene meta diaria, semanal y mensual en valor (COP) y unidades
  - Las metas semanales/mensuales se repiten en cada día del período
    para facilitar JOIN directo con transacciones sin agrupar fechas

Criterios de segmentación por formato de tienda:
  - SUPERSTORE   → metas altas  (tiendas grandes)
  - SUPERMERCADO → metas medias
  - EXPRESS      → metas bajas
  - Sin formato  → metas medias

Factores estacionales por mes:
  - Temporada alta  (ene, feb, jun, jul, oct, nov, dic) → x1.30
  - Temporada media (mar, abr, may, ago, sep)            → x1.00
  - Fin de año      (dic)                                → x1.50
"""

import psycopg2
import os
import random
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

# ─── Conexión ────────────────────────────────────────────────────────────────
def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode="require"
    )

# ─── DDL ─────────────────────────────────────────────────────────────────────
DDL = """
DROP TABLE IF EXISTS metas_ventas;

CREATE TABLE metas_ventas (
    id                  SERIAL          PRIMARY KEY,

    -- Dimensiones
    tienda_id           INTEGER         NOT NULL REFERENCES tiendas(id),
    fecha               DATE            NOT NULL,
    anio                SMALLINT        NOT NULL,
    mes                 SMALLINT        NOT NULL,   -- 1-12
    semana_iso          SMALLINT        NOT NULL,   -- ISO week 1-53
    dia_semana          SMALLINT        NOT NULL,   -- 1=Lun … 7=Dom
    trimestre           SMALLINT        NOT NULL,   -- 1-4
    es_temporada_alta   BOOLEAN         NOT NULL DEFAULT FALSE,

    -- Metas en valor (COP)
    meta_diaria_cop     NUMERIC(15,2)   NOT NULL,
    meta_semanal_cop    NUMERIC(15,2)   NOT NULL,
    meta_mensual_cop    NUMERIC(15,2)   NOT NULL,

    -- Metas en unidades
    meta_diaria_und     INTEGER         NOT NULL,
    meta_semanal_und    INTEGER         NOT NULL,
    meta_mensual_und    INTEGER         NOT NULL,

    -- Auditoría
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_meta_tienda_fecha UNIQUE (tienda_id, fecha)
);

-- Índices para el informe de cumplimiento
CREATE INDEX idx_metas_tienda   ON metas_ventas (tienda_id);
CREATE INDEX idx_metas_fecha    ON metas_ventas (fecha);
CREATE INDEX idx_metas_anio_mes ON metas_ventas (anio, mes);
CREATE INDEX idx_metas_semana   ON metas_ventas (anio, semana_iso);
"""

# ─── Configuración de metas base por formato ─────────────────────────────────
METAS_BASE = {
    # formato            : (meta_dia_cop_min, meta_dia_cop_max, und_dia_min, und_dia_max)
    "GRANDE"             : (4_500_000,  7_000_000, 80, 150),
    "MEDIANO"            : (2_500_000,  4_500_000, 45,  90),
    "PEQUEÑO"            : (1_200_000,  2_500_000, 20,  50),
    "EXPRESS"            : (800_000,    1_800_000, 15,  40),
    "DEFAULT"            : (1_500_000,  3_000_000, 30,  60),
}

FACTOR_ESTACIONAL = {
    1: 1.25,  # Enero      — temporada alta
    2: 1.20,  # Febrero
    3: 1.00,  # Marzo
    4: 0.95,  # Abril
    5: 0.95,  # Mayo
    6: 1.20,  # Junio      — mitad de año
    7: 1.25,  # Julio
    8: 0.95,  # Agosto
    9: 1.00,  # Septiembre
    10: 1.20, # Octubre
    11: 1.30, # Noviembre  — pre-navidad
    12: 1.50, # Diciembre  — temporada máxima
}

TEMPORADA_ALTA_MESES = {1, 2, 6, 7, 10, 11, 12}

# ─── Generar rango de fechas ──────────────────────────────────────────────────
def fechas_rango(inicio: date, fin: date):
    d = inicio
    while d <= fin:
        yield d
        d += timedelta(days=1)

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("\n🏦  DBA — Creación y carga de metas_ventas")
    print(f"    Período: 2025-01-01 → 2026-12-31\n")

    conn = conectar()
    cur  = conn.cursor()
    print("✅  Conexión exitosa a PostgreSQL\n")

    # 1. Crear tabla
    print("📐  Creando tabla metas_ventas...")
    cur.execute(DDL)
    conn.commit()
    print("    Tabla e índices creados.\n")

    # 2. Leer tiendas con su formato
    cur.execute("SELECT id, custom_formato FROM tiendas ORDER BY id")
    tiendas = cur.fetchall()
    print(f"🏪  Tiendas encontradas: {len(tiendas)}")
    for t in tiendas:
        print(f"    → Tienda {int(t[0]):>5}  |  formato: {t[1] or 'DEFAULT'}")

    # 3. Generar registros
    inicio = date(2025, 1, 1)
    fin    = date(2026, 12, 31)
    total  = 0
    batch  = []
    BATCH_SIZE = 500

    print(f"\n📅  Generando metas del {inicio} al {fin}...\n")

    for tienda_id, formato in tiendas:
        fmt_key = (formato or "DEFAULT").upper()
        if fmt_key not in METAS_BASE:
            fmt_key = "DEFAULT"
        cop_min, cop_max, und_min, und_max = METAS_BASE[fmt_key]

        # Meta base fija para esta tienda (con algo de variación entre tiendas)
        factor_tienda = random.uniform(0.85, 1.15)

        for fecha in fechas_rango(inicio, fin):
            mes      = fecha.month
            factor   = FACTOR_ESTACIONAL[mes] * factor_tienda
            es_alta  = mes in TEMPORADA_ALTA_MESES

            # Reducir domingos un 30%
            dia_sem = fecha.isoweekday()  # 1=Lun, 7=Dom
            f_dia   = 0.70 if dia_sem == 7 else 1.0

            # Meta diaria
            meta_dia_cop = round(random.uniform(cop_min, cop_max) * factor * f_dia, 2)
            meta_dia_und = int(random.uniform(und_min, und_max) * factor * f_dia)

            # Meta semanal = meta_dia × 6 días hábiles (± variación)
            meta_sem_cop = round(meta_dia_cop * random.uniform(5.5, 6.5), 2)
            meta_sem_und = int(meta_dia_und * random.uniform(5.5, 6.5))

            # Meta mensual = meta_dia × días hábiles del mes (≈ 24)
            dias_habiles = 24 if mes in {1,3,5,7,8,10,12} else 22
            meta_mes_cop = round(meta_dia_cop * random.uniform(dias_habiles - 1, dias_habiles + 1), 2)
            meta_mes_und = int(meta_dia_und * random.uniform(dias_habiles - 1, dias_habiles + 1))

            iso_cal  = fecha.isocalendar()
            semana   = iso_cal[1]
            trimestre = (mes - 1) // 3 + 1

            batch.append((
                tienda_id, fecha, fecha.year, mes, semana,
                dia_sem, trimestre, es_alta,
                meta_dia_cop, meta_sem_cop, meta_mes_cop,
                meta_dia_und, meta_sem_und, meta_mes_und,
            ))
            total += 1

            if len(batch) >= BATCH_SIZE:
                cur.executemany("""
                    INSERT INTO metas_ventas (
                        tienda_id, fecha, anio, mes, semana_iso,
                        dia_semana, trimestre, es_temporada_alta,
                        meta_diaria_cop, meta_semanal_cop, meta_mensual_cop,
                        meta_diaria_und, meta_semanal_und, meta_mensual_und
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (tienda_id, fecha) DO NOTHING
                """, batch)
                conn.commit()
                batch.clear()
                print(f"    ✓ {total:,} registros insertados...", end="\r")

    # Último batch
    if batch:
        cur.executemany("""
            INSERT INTO metas_ventas (
                tienda_id, fecha, anio, mes, semana_iso,
                dia_semana, trimestre, es_temporada_alta,
                meta_diaria_cop, meta_semanal_cop, meta_mensual_cop,
                meta_diaria_und, meta_semanal_und, meta_mensual_und
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (tienda_id, fecha) DO NOTHING
        """, batch)
        conn.commit()

    print(f"\n\n✅  Carga completada: {total:,} registros insertados")
    print(f"    ({len(tiendas)} tiendas × 731 días = {len(tiendas)*731:,} filas esperadas)\n")

    # 4. Resumen de validación
    cur.execute("""
        SELECT
            anio,
            COUNT(*)                               AS registros,
            COUNT(DISTINCT tienda_id)              AS tiendas,
            ROUND(AVG(meta_diaria_cop))            AS meta_dia_prom,
            ROUND(AVG(meta_mensual_cop))           AS meta_mes_prom
        FROM metas_ventas
        GROUP BY anio
        ORDER BY anio
    """)
    rows = cur.fetchall()
    print("📊  Resumen por año:")
    print(f"    {'Año':<6} {'Registros':>10} {'Tiendas':>8} {'Meta Día Prom':>15} {'Meta Mes Prom':>15}")
    print(f"    {'─'*6} {'─'*10} {'─'*8} {'─'*15} {'─'*15}")
    for r in rows:
        print(f"    {r[0]:<6} {r[1]:>10,} {r[2]:>8} {r[3]:>14,.0f} {r[4]:>14,.0f}")

    cur.close()
    conn.close()
    print("\n🔒  Conexión cerrada.")
    print("─" * 60)
    print("✅  metas_ventas lista para informes de cumplimiento.")

if __name__ == "__main__":
    main()
