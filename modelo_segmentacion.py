import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# Conexión a Go_BD
# ─────────────────────────────────────────
load_dotenv()

def conectar_engine():
    host     = os.getenv("DB_HOST")
    dbname   = os.getenv("DB_NAME")
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port     = os.getenv("DB_PORT", "5432")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require")

# ─────────────────────────────────────────
# 1. Leer datos
# ─────────────────────────────────────────
def leer_datos(engine):
    print("📥 Leyendo datos desde Go_BD...\n")

    df_ventas = pd.read_sql("""
        SELECT
            sku_id,
            target_location_id AS tienda_id,
            SUM(quantity)      AS cantidad_total,
            AVG(quantity)      AS cantidad_promedio,
            AVG(sale_price)    AS precio_promedio,
            COUNT(*)           AS num_transacciones,
            MIN(transaction_date) AS primera_venta,
            MAX(transaction_date) AS ultima_venta
        FROM transacciones
        WHERE type = 'venta'
        GROUP BY sku_id, target_location_id
    """, engine)
    print(f"   ✅ Ventas agrupadas: {len(df_ventas):,} registros")

    df_inventario = pd.read_sql("""
        SELECT
            sku_id,
            location_id AS tienda_id,
            site_qty,
            min_stock,
            max_stock,
            replenishment_lead_time
        FROM inventarios
    """, engine)
    print(f"   ✅ Inventarios: {len(df_inventario):,} registros")

    df_tiendas = pd.read_sql("""
        SELECT
            id::VARCHAR    AS tienda_id,
            city           AS ciudad,
            custom_clima   AS clima,
            custom_zona    AS zona,
            custom_formato AS formato
        FROM tiendas
    """, engine)
    print(f"   ✅ Tiendas: {len(df_tiendas):,} registros\n")

    return df_ventas, df_inventario, df_tiendas

# ─────────────────────────────────────────
# 2. Segmentación de SKUs (ABC)
# ─────────────────────────────────────────
def segmentar_skus(engine, df_ventas):
    print("📦 Segmentando SKUs por volumen de ventas (Análisis ABC)...")

    df_sku = df_ventas.groupby("sku_id").agg(
        cantidad_total    =("cantidad_total",    "sum"),
        cantidad_promedio =("cantidad_promedio",  "mean"),
        precio_promedio   =("precio_promedio",    "mean"),
        num_transacciones =("num_transacciones",  "sum"),
        num_tiendas       =("tienda_id",          "nunique")
    ).reset_index()

    # Calcular participación acumulada
    df_sku = df_sku.sort_values("cantidad_total", ascending=False)
    df_sku["participacion"]  = df_sku["cantidad_total"] / df_sku["cantidad_total"].sum()
    df_sku["acumulado"]      = df_sku["participacion"].cumsum()

    # Clasificación ABC
    df_sku["segmento_abc"] = df_sku["acumulado"].apply(
        lambda x: "A - Alta rotación" if x <= 0.70
        else ("B - Rotación media" if x <= 0.90
        else "C - Baja rotación")
    )

    # Resumen ABC
    resumen = df_sku.groupby("segmento_abc").agg(
        num_skus      =("sku_id",         "count"),
        ventas_totales=("cantidad_total",  "sum")
    ).reset_index()

    print("\n📊 Clasificación ABC de SKUs:")
    print("─" * 55)
    for _, row in resumen.iterrows():
        print(f"  {row['segmento_abc']:25} | "
              f"SKUs: {row['num_skus']:>4} | "
              f"Ventas: {row['ventas_totales']:>8.0f}")
    print("─" * 55)

    # Guardar en Go_BD
    guardar_tabla(engine, df_sku, "segmentacion_skus")
    return df_sku

# ─────────────────────────────────────────
# 3. Segmentación de Tiendas (KMeans)
# ─────────────────────────────────────────
def segmentar_tiendas(engine, df_ventas, df_inventario, df_tiendas):
    print("\n🏪 Segmentando tiendas con KMeans...")

    # Métricas por tienda
    df_metricas = df_ventas.groupby("tienda_id").agg(
        ventas_totales  =("cantidad_total",    "sum"),
        venta_promedio  =("cantidad_promedio",  "mean"),
        precio_promedio =("precio_promedio",    "mean"),
        num_skus        =("sku_id",             "nunique"),
        transacciones   =("num_transacciones",  "sum")
    ).reset_index()

    # Unir con inventario
    df_inv = df_inventario.groupby("tienda_id").agg(
        stock_total =("site_qty",  "sum"),
        stock_prom  =("site_qty",  "mean"),
        lead_time   =("replenishment_lead_time", "mean")
    ).reset_index()

    df_metricas = df_metricas.merge(df_inv, on="tienda_id", how="left")
    df_metricas = df_metricas.merge(df_tiendas, on="tienda_id", how="left")

    # Features para clustering
    features_cluster = [
        "ventas_totales", "venta_promedio", "precio_promedio",
        "num_skus", "transacciones", "stock_total", "lead_time"
    ]

    df_cluster = df_metricas[features_cluster].fillna(0)

    # Escalar datos
    scaler     = StandardScaler()
    X_scaled   = scaler.fit_transform(df_cluster)

    # Encontrar número óptimo de clusters
    mejor_k    = 3
    mejor_score = -1
    for k in range(2, min(6, len(df_metricas))):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        score  = silhouette_score(X_scaled, labels)
        if score > mejor_score:
            mejor_score = score
            mejor_k     = k

    print(f"   Número óptimo de clusters: {mejor_k} (score: {mejor_score:.3f})")

    # Entrenar modelo final
    kmeans = KMeans(n_clusters=mejor_k, random_state=42, n_init=10)
    df_metricas["cluster"] = kmeans.fit_predict(X_scaled)

    # Etiquetar clusters por volumen de ventas
    orden = df_metricas.groupby("cluster")["ventas_totales"].mean().sort_values(ascending=False)
    etiquetas = {
        cluster: f"Tienda Tipo {i+1} - {'Alta' if i==0 else 'Media' if i==1 else 'Baja'} demanda"
        for i, cluster in enumerate(orden.index)
    }
    df_metricas["segmento_tienda"] = df_metricas["cluster"].map(etiquetas)

    # Resumen por cluster
    print("\n📊 Segmentación de Tiendas:")
    print("─" * 65)
    resumen = df_metricas.groupby("segmento_tienda").agg(
        num_tiendas    =("tienda_id",       "count"),
        ventas_prom    =("ventas_totales",   "mean"),
        skus_prom      =("num_skus",         "mean"),
        stock_prom     =("stock_total",      "mean")
    ).reset_index()

    for _, row in resumen.iterrows():
        print(f"  {row['segmento_tienda']:35} | "
              f"Tiendas: {row['num_tiendas']:>2} | "
              f"Ventas prom: {row['ventas_prom']:>7.0f} | "
              f"SKUs prom: {row['skus_prom']:>4.0f}")
    print("─" * 65)

    # Guardar en Go_BD
    guardar_tabla(engine, df_metricas, "segmentacion_tiendas")
    return df_metricas

# ─────────────────────────────────────────
# 4. Guardar tabla en Go_BD
# ─────────────────────────────────────────
def guardar_tabla(engine, df, nombre_tabla):
    df.to_sql(nombre_tabla, engine, if_exists="replace", index=False)
    print(f"   💾 Tabla '{nombre_tabla}' guardada en Go_BD ({len(df):,} registros)")

# ─────────────────────────────────────────
# Ejecutar
# ─────────────────────────────────────────
def main():
    print("\n🚀 Iniciando Segmentación - Go_Retail\n")

    engine                          = conectar_engine()
    df_ventas, df_inventario, df_tiendas = leer_datos(engine)

    df_skus    = segmentar_skus(engine, df_ventas)
    df_tiendas_seg = segmentar_tiendas(engine, df_ventas, df_inventario, df_tiendas)

    print("\n✅ Segmentación completada.")
    print("   Tablas guardadas en Go_BD:")
    print("   → segmentacion_skus")
    print("   → segmentacion_tiendas")

if __name__ == "__main__":
    main()
