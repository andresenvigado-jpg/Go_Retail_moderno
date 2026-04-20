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
            target_location_id      AS tienda_id,
            SUM(quantity)           AS unidades_vendidas,
            AVG(sale_price)         AS precio_venta_prom,
            SUM(quantity*sale_price) AS ingreso_total,
            COUNT(*)                AS num_transacciones
        FROM transacciones
        WHERE type = 'venta'
        AND sale_price > 0
        GROUP BY sku_id, target_location_id
    """, engine)
    print(f"   ✅ Ventas: {len(df_ventas):,} combinaciones SKU-Tienda")

    df_catalogo = pd.read_sql("""
        SELECT
            id::VARCHAR  AS sku_id,
            cost,
            price        AS precio_lista,
            categories   AS categoria,
            brands       AS marca,
            department_name AS departamento,
            size         AS talla,
            seasons      AS temporada
        FROM catalogos
    """, engine)
    print(f"   ✅ Catálogo: {len(df_catalogo):,} productos\n")

    return df_ventas, df_catalogo

# ─────────────────────────────────────────
# 2. Calcular índice de rentabilidad
# ─────────────────────────────────────────
def calcular_rentabilidad(df_ventas, df_catalogo):
    print("🧮 Calculando índice de rentabilidad...")

    df = df_ventas.merge(df_catalogo, on="sku_id", how="left")

    # Margen bruto por unidad
    df["margen_unitario"]    = df["precio_venta_prom"] - df["cost"]
    df["margen_porcentual"]  = np.where(
        df["precio_venta_prom"] > 0,
        (df["margen_unitario"] / df["precio_venta_prom"] * 100).round(2),
        0
    )

    # Rentabilidad total
    df["costo_total"]        = df["unidades_vendidas"] * df["cost"]
    df["rentabilidad_total"] = (df["ingreso_total"] - df["costo_total"]).round(2)

    # Descuento aplicado vs precio lista
    df["descuento_aplicado"] = np.where(
        df["precio_lista"] > 0,
        ((df["precio_lista"] - df["precio_venta_prom"]) / df["precio_lista"] * 100).round(2),
        0
    )

    # Índice de rentabilidad combinado (0-100)
    # Combina margen %, volumen y rentabilidad total normalizada
    df["margen_norm"]        = (df["margen_porcentual"] - df["margen_porcentual"].min()) / \
                               (df["margen_porcentual"].max() - df["margen_porcentual"].min() + 0.01)
    df["rent_norm"]          = (df["rentabilidad_total"] - df["rentabilidad_total"].min()) / \
                               (df["rentabilidad_total"].max() - df["rentabilidad_total"].min() + 0.01)
    df["vol_norm"]           = (df["unidades_vendidas"] - df["unidades_vendidas"].min()) / \
                               (df["unidades_vendidas"].max() - df["unidades_vendidas"].min() + 0.01)

    df["indice_rentabilidad"] = ((df["margen_norm"] * 0.4) +
                                 (df["rent_norm"]   * 0.4) +
                                 (df["vol_norm"]    * 0.2)) * 100
    df["indice_rentabilidad"] = df["indice_rentabilidad"].round(2)

    # Clasificación
    def clasificar(idx):
        if idx >= 70:   return "🟢 Alta rentabilidad"
        elif idx >= 40: return "🟡 Rentabilidad media"
        else:           return "🔴 Baja rentabilidad"

    df["clasificacion"] = df["indice_rentabilidad"].apply(clasificar)

    print(f"   ✅ Rentabilidad calculada para {len(df):,} combinaciones SKU-Tienda\n")

    # Resumen
    resumen = df.groupby("clasificacion").size().reset_index(name="cantidad")
    print("📊 Distribución de rentabilidad:")
    print("─" * 45)
    for _, row in resumen.iterrows():
        print(f"  {row['clasificacion']:30} | {row['cantidad']:>4}")
    print("─" * 45)

    # Top 10 más rentables
    top10 = df.nlargest(10, "indice_rentabilidad")
    print("\n🏆 Top 10 SKUs más rentables:")
    print("─" * 70)
    for _, row in top10.iterrows():
        print(f"  SKU {row['sku_id']:>6} | Tienda {row['tienda_id']:>4} | "
              f"Margen: {row['margen_porcentual']:>6.1f}% | "
              f"Rentabilidad: ${row['rentabilidad_total']:>10,.0f} | "
              f"Índice: {row['indice_rentabilidad']:>5.1f}")
    print("─" * 70)

    return df

# ─────────────────────────────────────────
# 3. Guardar en Go_BD
# ─────────────────────────────────────────
def guardar(engine, df):
    print("\n💾 Guardando en Go_BD...")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rentabilidad_sku (
                id                   SERIAL PRIMARY KEY,
                sku_id               VARCHAR(100),
                tienda_id            VARCHAR(100),
                categoria            VARCHAR(255),
                marca                VARCHAR(255),
                departamento         VARCHAR(255),
                talla                VARCHAR(50),
                temporada            VARCHAR(100),
                unidades_vendidas    NUMERIC(12,2),
                precio_venta_prom    NUMERIC(12,2),
                precio_lista         NUMERIC(12,2),
                costo_total          NUMERIC(12,2),
                ingreso_total        NUMERIC(12,2),
                rentabilidad_total   NUMERIC(12,2),
                margen_unitario      NUMERIC(12,2),
                margen_porcentual    NUMERIC(10,2),
                descuento_aplicado   NUMERIC(10,2),
                indice_rentabilidad  NUMERIC(10,2),
                clasificacion        VARCHAR(50),
                fecha_calculo        TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

    cols = [
        "sku_id","tienda_id","categoria","marca","departamento","talla","temporada",
        "unidades_vendidas","precio_venta_prom","precio_lista","costo_total",
        "ingreso_total","rentabilidad_total","margen_unitario","margen_porcentual",
        "descuento_aplicado","indice_rentabilidad","clasificacion"
    ]
    df[cols].to_sql("rentabilidad_sku", engine, if_exists="replace", index=False)
    print(f"   ✅ {len(df):,} registros guardados en tabla 'rentabilidad_sku'")

def main():
    print("\n🚀 Iniciando Índice de Rentabilidad — Go_Retail\n")
    engine              = conectar_engine()
    df_ventas, df_cat   = leer_datos(engine)
    df                  = calcular_rentabilidad(df_ventas, df_cat)
    guardar(engine, df)
    print("\n✅ Índice de Rentabilidad completado.")

if __name__ == "__main__":
    main()
