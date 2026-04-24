"""
Modelo de Cumplimiento de Metas por Tienda
============================================
Algoritmos utilizados:
  - KMeans          → Segmentación de tiendas por comportamiento de cumplimiento
  - LinearRegression → Tendencia de cumplimiento (¿mejorando o bajando?)
  - IsolationForest  → Detección de tiendas con comportamiento anómalo
"""

import pandas as pd
import numpy as np
from datetime import date, datetime
from sqlalchemy import text

from sklearn.cluster         import KMeans
from sklearn.preprocessing   import StandardScaler
from sklearn.linear_model    import LinearRegression
from sklearn.ensemble        import IsolationForest


# ─────────────────────────────────────────────────────────────────────────────
# Lectura de datos
# ─────────────────────────────────────────────────────────────────────────────

def _leer_ventas(engine, fecha_desde: str, fecha_hasta: str) -> pd.DataFrame:
    sql = text("""
        SELECT
            CAST(target_location_id AS INTEGER)  AS tienda_id,
            DATE(transaction_date)                AS fecha,
            SUM(quantity * sale_price)            AS ventas_cop,
            SUM(quantity)                         AS ventas_und
        FROM transacciones
        WHERE type = 'venta'
          AND target_location_id ~ '^[0-9]+$'
          AND DATE(transaction_date) BETWEEN :desde AND :hasta
        GROUP BY target_location_id, DATE(transaction_date)
    """)
    return pd.read_sql(sql, engine, params={"desde": fecha_desde, "hasta": fecha_hasta})


def _leer_metas(engine, fecha_desde: str, fecha_hasta: str) -> pd.DataFrame:
    sql = text("""
        SELECT
            mv.tienda_id,
            mv.fecha,
            t.name             AS tienda_nombre,
            t.city             AS ciudad,
            t.region           AS region,
            t.custom_formato   AS formato,
            mv.meta_diaria_cop,
            mv.meta_semanal_cop,
            mv.meta_mensual_cop,
            mv.meta_diaria_und,
            mv.meta_semanal_und,
            mv.meta_mensual_und,
            mv.anio,
            mv.mes,
            mv.semana_iso,
            mv.trimestre,
            mv.es_temporada_alta
        FROM metas_ventas mv
        JOIN tiendas t ON t.id = mv.tienda_id
        WHERE mv.fecha BETWEEN :desde AND :hasta
        ORDER BY mv.tienda_id, mv.fecha
    """)
    return pd.read_sql(sql, engine, params={"desde": fecha_desde, "hasta": fecha_hasta})


# ─────────────────────────────────────────────────────────────────────────────
# ML 1: Clustering KMeans — Tier de cumplimiento
# ─────────────────────────────────────────────────────────────────────────────

def _aplicar_clustering(resumen: pd.DataFrame) -> pd.DataFrame:
    features = resumen[['pct_cumplimiento_cop', 'pct_dias_sobre_meta', 'cumplimiento_prom']].fillna(0)
    scaler   = StandardScaler()
    X        = scaler.fit_transform(features)

    n = min(4, len(resumen))
    km = KMeans(n_clusters=n, random_state=42, n_init=10)
    resumen = resumen.copy()
    resumen['cluster'] = km.fit_predict(X)

    # Ordenar clusters por cumplimiento promedio → etiqueta semántica
    orden = (resumen.groupby('cluster')['pct_cumplimiento_cop']
             .mean().sort_values(ascending=False).index)
    labels = ['Excelente 🏆', 'Bueno ✅', 'Regular ⚠️', 'Crítico 🚨']
    mapa   = {c: labels[i] for i, c in enumerate(orden)}
    resumen['tier'] = resumen['cluster'].map(mapa)
    return resumen, X


# ─────────────────────────────────────────────────────────────────────────────
# ML 2: LinearRegression — Tendencia de cumplimiento
# ─────────────────────────────────────────────────────────────────────────────

def _calcular_tendencias(df: pd.DataFrame) -> pd.DataFrame:
    registros = []
    for tid, grupo in df.groupby('tienda_id'):
        grupo = grupo.sort_values('fecha')
        if len(grupo) < 3:
            continue
        X     = np.arange(len(grupo)).reshape(-1, 1)
        y     = grupo['pct_diario_cop'].fillna(0).values
        lr    = LinearRegression().fit(X, y)
        slope = lr.coef_[0]
        r2    = lr.score(X, y)
        registros.append({
            'tienda_id':  tid,
            'slope':      round(float(slope), 4),
            'r2':         round(float(r2), 4),
            'tendencia':  ('Mejorando ↑' if slope > 0.5
                           else 'Estable →' if slope > -0.5
                           else 'Bajando ↓'),
        })
    return pd.DataFrame(registros)


# ─────────────────────────────────────────────────────────────────────────────
# ML 3: IsolationForest — Tiendas con comportamiento anómalo
# ─────────────────────────────────────────────────────────────────────────────

def _detectar_anomalias(X_scaled: np.ndarray) -> np.ndarray:
    iso    = IsolationForest(contamination=0.15, random_state=42)
    preds  = iso.fit_predict(X_scaled)
    return preds == -1   # True = anómala


# ─────────────────────────────────────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_cumplimiento(engine,
                          fecha_desde: date | None = None,
                          fecha_hasta: date | None = None) -> dict:

    hoy = date.today()
    if fecha_hasta is None:
        fecha_hasta = hoy
    if fecha_desde is None:
        fecha_desde = date(hoy.year, hoy.month, 1)

    fd, fh = str(fecha_desde), str(fecha_hasta)

    # ── Datos ────────────────────────────────────────────────────────────────
    df_metas  = _leer_metas(engine, fd, fh)
    df_ventas = _leer_ventas(engine, fd, fh)

    if df_metas.empty:
        return {"error": "Sin metas para el período indicado"}

    df = df_metas.merge(df_ventas, on=['tienda_id', 'fecha'], how='left')
    df['ventas_cop'] = df['ventas_cop'].fillna(0)
    df['ventas_und'] = df['ventas_und'].fillna(0)

    # Cumplimiento diario (%)
    df['pct_diario_cop'] = (df['ventas_cop'] / df['meta_diaria_cop'] * 100).round(2)
    df['pct_diario_und'] = (df['ventas_und'] / df['meta_diaria_und'] * 100).round(2)

    # ── Resumen por tienda ────────────────────────────────────────────────────
    resumen = (df.groupby(['tienda_id', 'tienda_nombre', 'ciudad', 'region', 'formato'])
               .agg(
                   dias_totales        = ('fecha',          'count'),
                   dias_con_ventas     = ('ventas_cop',     lambda x: (x > 0).sum()),
                   ventas_cop_total    = ('ventas_cop',     'sum'),
                   meta_cop_total      = ('meta_diaria_cop','sum'),
                   ventas_und_total    = ('ventas_und',     'sum'),
                   meta_und_total      = ('meta_diaria_und','sum'),
                   cumplimiento_prom   = ('pct_diario_cop', 'mean'),
                   dias_sobre_meta     = ('pct_diario_cop', lambda x: (x >= 100).sum()),
                   mejor_dia_cop       = ('ventas_cop',     'max'),
                   meta_mensual_cop    = ('meta_mensual_cop','first'),
               )
               .reset_index())

    resumen['pct_cumplimiento_cop'] = (
        resumen['ventas_cop_total'] / resumen['meta_cop_total'] * 100).round(2)
    resumen['pct_cumplimiento_und'] = (
        resumen['ventas_und_total'] / resumen['meta_und_total'] * 100).round(2)
    resumen['pct_dias_sobre_meta']  = (
        resumen['dias_sobre_meta'] / resumen['dias_totales'] * 100).round(1)
    resumen['ticket_promedio']      = (
        resumen['ventas_cop_total'] / resumen['ventas_und_total'].replace(0, np.nan)).round(0)

    # ── ML 1: KMeans ─────────────────────────────────────────────────────────
    resumen, X_scaled = _aplicar_clustering(resumen)

    # ── ML 2: Tendencias ─────────────────────────────────────────────────────
    df_tend = _calcular_tendencias(df)
    if not df_tend.empty:
        resumen = resumen.merge(df_tend, on='tienda_id', how='left')
    else:
        resumen['slope']     = 0.0
        resumen['r2']        = 0.0
        resumen['tendencia'] = 'Sin datos'

    # ── ML 3: Anomalías ───────────────────────────────────────────────────────
    if len(resumen) >= 5:
        resumen['es_anomalia'] = _detectar_anomalias(X_scaled)
    else:
        resumen['es_anomalia'] = False

    # ── Proyección fin de mes ─────────────────────────────────────────────────
    dias_mes            = pd.Timestamp(hoy.year, hoy.month, 1).days_in_month
    dias_transcurridos  = hoy.day
    factor_proy         = dias_mes / max(dias_transcurridos, 1)
    resumen['proyeccion_cop']  = (resumen['ventas_cop_total'] * factor_proy).round(0)
    resumen['pct_proyeccion']  = (
        resumen['proyeccion_cop'] / resumen['meta_mensual_cop'] * 100).round(2)

    # ── Ranking ───────────────────────────────────────────────────────────────
    resumen = resumen.sort_values('pct_cumplimiento_cop', ascending=False).reset_index(drop=True)
    resumen['ranking'] = resumen.index + 1

    # ── Cumplimiento semanal (semana ISO actual) ───────────────────────────────
    semana_hoy = hoy.isocalendar()[1]
    df_sem = (df[df['semana_iso'] == semana_hoy]
              .groupby('tienda_id')
              .agg(ventas_semana=('ventas_cop', 'sum'),
                   meta_semana  =('meta_semanal_cop', 'first'))
              .reset_index())
    df_sem['pct_semanal'] = (df_sem['ventas_semana'] / df_sem['meta_semana'] * 100).round(2)

    # ── Cumplimiento mensual (mes actual) ──────────────────────────────────────
    df_mes = (df[df['mes'] == hoy.month]
              .groupby('tienda_id')
              .agg(ventas_mes=('ventas_cop', 'sum'),
                   meta_mes  =('meta_mensual_cop', 'first'))
              .reset_index())
    df_mes['pct_mensual'] = (df_mes['ventas_mes'] / df_mes['meta_mes'] * 100).round(2)

    # ── Por trimestre ─────────────────────────────────────────────────────────
    df_trim = (df.groupby(['tienda_id', 'trimestre'])
               .agg(ventas_trim=('ventas_cop', 'sum'),
                    meta_trim  =('meta_diaria_cop', 'sum'))
               .reset_index())
    df_trim['pct_trim'] = (df_trim['ventas_trim'] / df_trim['meta_trim'] * 100).round(2)
    trim_pivot = (df_trim.pivot(index='tienda_id', columns='trimestre', values='pct_trim')
                  .add_prefix('trim_q')
                  .reset_index())

    # ── Construir registros de respuesta ──────────────────────────────────────
    tiendas_out = []
    for _, row in resumen.iterrows():
        tid     = int(row['tienda_id'])
        sem_row = df_sem[df_sem['tienda_id'] == tid]
        mes_row = df_mes[df_mes['tienda_id'] == tid]

        tiendas_out.append({
            'ranking':              int(row['ranking']),
            'tienda_id':            tid,
            'tienda_nombre':        row['tienda_nombre'],
            'ciudad':               row['ciudad'],
            'region':               row['region'],
            'formato':              row['formato'],
            'tier':                 row['tier'],
            'tendencia':            row.get('tendencia', '—'),
            'slope':                float(row.get('slope', 0)),
            'es_anomalia':          bool(row['es_anomalia']),
            # Período completo
            'ventas_cop':           round(float(row['ventas_cop_total']), 0),
            'meta_cop':             round(float(row['meta_cop_total']), 0),
            'pct_cumplimiento_cop': float(row['pct_cumplimiento_cop']),
            'pct_cumplimiento_und': float(row['pct_cumplimiento_und']),
            # Semana
            'pct_semanal':          float(sem_row['pct_semanal'].values[0]) if not sem_row.empty else 0.0,
            # Mes
            'pct_mensual':          float(mes_row['pct_mensual'].values[0]) if not mes_row.empty else 0.0,
            # Proyección
            'proyeccion_cop':       float(row['proyeccion_cop']),
            'meta_mensual_cop':     float(row['meta_mensual_cop']),
            'pct_proyeccion':       float(row['pct_proyeccion']),
            # Extras
            'ticket_promedio':      float(row['ticket_promedio']) if pd.notna(row['ticket_promedio']) else 0.0,
            'dias_sobre_meta':      int(row['dias_sobre_meta']),
            'pct_dias_sobre_meta':  float(row['pct_dias_sobre_meta']),
            'mejor_dia_cop':        float(row['mejor_dia_cop']),
        })

    # ── Distribución por tier ─────────────────────────────────────────────────
    tier_dist = resumen['tier'].value_counts().to_dict()

    # ── Top 3 y Bottom 3 ──────────────────────────────────────────────────────
    top3    = tiendas_out[:3]
    bottom3 = tiendas_out[-3:]

    # ── Alertas (proyección < 80%) ────────────────────────────────────────────
    alertas = [t for t in tiendas_out if t['pct_proyeccion'] < 80]

    # ── Resumen ejecutivo ─────────────────────────────────────────────────────
    ejecutivo = {
        'total_tiendas':          len(resumen),
        'cumplimiento_global_cop': round(float(resumen['pct_cumplimiento_cop'].mean()), 2),
        'tiendas_sobre_meta':     int((resumen['pct_cumplimiento_cop'] >= 100).sum()),
        'tiendas_en_riesgo':      len(alertas),
        'tiendas_anomalas':       int(resumen['es_anomalia'].sum()),
        'distribucion_tiers':     tier_dist,
        'total_ventas_cop':       round(float(resumen['ventas_cop_total'].sum()), 0),
        'total_meta_cop':         round(float(resumen['meta_cop_total'].sum()), 0),
        'pct_ventas_vs_meta':     round(
            float(resumen['ventas_cop_total'].sum()) /
            float(resumen['meta_cop_total'].sum()) * 100, 2),
    }

    return {
        'periodo':           {'desde': fd, 'hasta': fh},
        'resumen_ejecutivo': ejecutivo,
        'tiendas':           tiendas_out,
        'top3':              top3,
        'bottom3':           bottom3,
        'alertas':           alertas,
    }
