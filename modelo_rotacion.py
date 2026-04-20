import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

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
            target_location_id          AS tienda_id,
            SUM(quantity)               AS unidades_vendidas,
            AVG(quantity)               AS venta_diaria_prom,
            STDDEV(quantity)            AS desviacion_venta,
            COUNT(DISTINCT DATE(transaction_date)) AS dias_con_venta,
            MIN(transaction_date)       AS primera_venta,
            MAX(transaction_date)       AS ultima_venta
        FROM transacciones
        WHERE type = 'venta'
        GROUP BY sku_id, target_location_id
    """, engine)
    print(f"   ✅ Ventas: {len(df_ventas):,} combinaciones SKU-Tienda")

    df_inv = pd.read_sql("""
        SELECT
            sku_id,
            location_id             AS tienda_id,
            site_qty,
            min_stock,
            max_stock,
            replenishment_lead_time AS lead_time
        FROM inventarios
    """, engine)
    print(f"   ✅ Inventarios: {len(df_inv):,} registros")

    df_cat = pd.read_sql("""
        SELECT
            id::VARCHAR AS sku_id,
            categories  AS categoria,
            brands      AS marca,
            size        AS talla,
            seasons     AS temporada,
            cost,
            price
        FROM catalogos
    """, engine)
    print(f"   ✅ Catálogo: {len(df_cat):,} productos\n")

    return df_ventas, df_inv, df_cat

# ─────────────────────────────────────────
# 2. Calcular velocidad de rotación
# ─────────────────────────────────────────
def calcular_rotacion(df_ventas, df_inv, df_cat):
    print("🧮 Calculando velocidad de rotación...")

    df = df_ventas.merge(df_inv, on=["sku_id","tienda_id"], how="left")
    df = df.merge(df_cat, on="sku_id", how="left")

    df["desviacion_venta"]  = df["desviacion_venta"].fillna(0)
    df["site_qty"]          = df["site_qty"].fillna(0)
    df["lead_time"]         = df["lead_time"].fillna(3)

    # Días de cobertura con stock actual
    df["dias_cobertura"] = np.where(
        df["venta_diaria_prom"] > 0,
        (df["site_qty"] / df["venta_diaria_prom"]).round(1),
        999
    )

    # Período total analizado
    df["primera_venta"] = pd.to_datetime(df["primera_venta"])
    df["ultima_venta"]  = pd.to_datetime(df["ultima_venta"])
    df["dias_periodo"]  = (df["ultima_venta"] - df["primera_venta"]).dt.days.clip(lower=1)

    # Tasa de rotación anual
    # Ventas anualizadas / Stock promedio
    df["ventas_anualizadas"]  = df["unidades_vendidas"] * (365 / df["dias_periodo"])
    df["stock_promedio"]      = ((df["site_qty"] + df["min_stock"]) / 2).clip(lower=0.1)
    df["tasa_rotacion_anual"] = (df["ventas_anualizadas"] / df["stock_promedio"]).round(2)

    # Días de inventario (DSI - Days Sales of Inventory)
    df["dsi"] = np.where(
        df["venta_diaria_prom"] > 0,
        (df["site_qty"] / df["venta_diaria_prom"]).round(1),
        999
    )

    # Frecuencia de venta (% de días que tuvo venta)
    df["frecuencia_venta"] = (df["dias_con_venta"] / df["dias_periodo"] * 100).round(2)

    # Índice de velocidad (0-100)
    df["rot_norm"]  = (df["tasa_rotacion_anual"] - df["tasa_rotacion_anual"].min()) / \
                      (df["tasa_rotacion_anual"].max() - df["tasa_rotacion_anual"].min() + 0.01)
    df["freq_norm"] = df["frecuencia_venta"] / 100
    df["dsi_norm"]  = 1 - (df["dsi"].clip(upper=365) / 365)

    df["indice_velocidad"] = ((df["rot_norm"]  * 0.4) +
                              (df["freq_norm"] * 0.3) +
                              (df["dsi_norm"]  * 0.3)) * 100
    df["indice_velocidad"] = df["indice_velocidad"].round(2)

    # Clasificación
    def clasificar(idx):
        if idx >= 70:   return "🚀 Alta rotación"
        elif idx >= 40: return "🔄 Rotación media"
        elif idx >= 15: return "🐢 Rotación lenta"
        else:           return "❄️  Sin movimiento"

    df["clasificacion_rotacion"] = df["indice_velocidad"].apply(clasificar)

    print(f"   ✅ Rotación calculada para {len(df):,} combinaciones\n")

    resumen = df.groupby("clasificacion_rotacion").size().reset_index(name="cantidad")
    print("📊 Distribución de velocidad de rotación:")
    print("─" * 45)
    for _, row in resumen.iterrows():
        print(f"  {row['clasificacion_rotacion']:25} | {row['cantidad']:>4}")
    print("─" * 45)

    top10 = df.nlargest(10, "indice_velocidad")
    print("\n🏆 Top 10 SKUs de mayor rotación:")
    print("─" * 75)
    for _, row in top10.iterrows():
        print(f"  SKU {row['sku_id']:>6} | Tienda {row['tienda_id']:>4} | "
              f"Rotación anual: {row['tasa_rotacion_anual']:>6.1f}x | "
              f"DSI: {row['dsi']:>5.1f} días | "
              f"Índice: {row['indice_velocidad']:>5.1f}")
    print("─" * 75)

    return df

# ─────────────────────────────────────────
# 3. Guardar en Go_BD
# ─────────────────────────────────────────
def guardar(engine, df):
    print("\n💾 Guardando en Go_BD...")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rotacion_sku (
                id                      SERIAL PRIMARY KEY,
                sku_id                  VARCHAR(100),
                tienda_id               VARCHAR(100),
                categoria               VARCHAR(255),
                marca                   VARCHAR(255),
                talla                   VARCHAR(50),
                temporada               VARCHAR(100),
                unidades_vendidas       NUMERIC(12,2),
                venta_diaria_prom       NUMERIC(12,4),
                dias_con_venta          INTEGER,
                dias_periodo            INTEGER,
                site_qty                NUMERIC(12,2),
                dias_cobertura          NUMERIC(10,2),
                tasa_rotacion_anual     NUMERIC(10,2),
                dsi                     NUMERIC(10,2),
                frecuencia_venta        NUMERIC(10,2),
                indice_velocidad        NUMERIC(10,2),
                clasificacion_rotacion  VARCHAR(50),
                fecha_calculo           TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

    cols = [
        "sku_id","tienda_id","categoria","marca","talla","temporada",
        "unidades_vendidas","venta_diaria_prom","dias_con_venta","dias_periodo",
        "site_qty","dias_cobertura","tasa_rotacion_anual","dsi",
        "frecuencia_venta","indice_velocidad","clasificacion_rotacion"
    ]
    df[cols].to_sql("rotacion_sku", engine, if_exists="replace", index=False)
    print(f"   ✅ {len(df):,} registros guardados en tabla 'rotacion_sku'")

def main():
    print("\n🚀 Iniciando Velocidad de Rotación — Go_Retail\n")
    engine                  = conectar_engine()
    df_ventas, df_inv, df_cat = leer_datos(engine)
    df                      = calcular_rotacion(df_ventas, df_inv, df_cat)
    guardar(engine, df)
    print("\n✅ Velocidad de Rotación completada.")

if __name__ == "__main__":
    main()
