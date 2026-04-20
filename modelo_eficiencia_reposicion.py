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

    df_trans = pd.read_sql("""
        SELECT
            target_location_id          AS tienda_id,
            sku_id,
            type,
            quantity,
            DATE(transaction_date)      AS fecha
        FROM transacciones
    """, engine)
    print(f"   ✅ Transacciones: {len(df_trans):,} registros")

    df_inv = pd.read_sql("""
        SELECT
            location_id             AS tienda_id,
            sku_id,
            site_qty,
            min_stock,
            replenishment_lead_time AS lead_time,
            avoid_replenishment
        FROM inventarios
    """, engine)
    print(f"   ✅ Inventarios: {len(df_inv):,} registros")

    df_tiendas = pd.read_sql("""
        SELECT
            id::VARCHAR    AS tienda_id,
            name           AS nombre_tienda,
            city           AS ciudad,
            custom_zona    AS zona,
            custom_clima   AS clima,
            custom_formato AS formato
        FROM tiendas
    """, engine)
    print(f"   ✅ Tiendas: {len(df_tiendas):,} registros\n")

    return df_trans, df_inv, df_tiendas

# ─────────────────────────────────────────
# 2. Calcular eficiencia de reposición
# ─────────────────────────────────────────
def calcular_eficiencia(df_trans, df_inv, df_tiendas):
    print("🧮 Calculando eficiencia de reposición por tienda...")

    # Métricas por tienda
    ventas = df_trans[df_trans["type"] == "venta"].groupby("tienda_id").agg(
        total_ventas      =("quantity", "sum"),
        dias_con_venta    =("fecha",    "nunique"),
        skus_vendidos     =("sku_id",   "nunique"),
        transac_ventas    =("quantity", "count")
    ).reset_index()

    reposiciones = df_trans[df_trans["type"] == "reposicion"].groupby("tienda_id").agg(
        total_repuesto    =("quantity", "sum"),
        num_reposiciones  =("quantity", "count"),
        skus_repuestos    =("sku_id",   "nunique")
    ).reset_index()

    devoluciones = df_trans[df_trans["type"] == "devolucion"].groupby("tienda_id").agg(
        total_devuelto    =("quantity", "sum"),
        num_devoluciones  =("quantity", "count")
    ).reset_index()

    traslados = df_trans[df_trans["type"] == "traslado"].groupby("tienda_id").agg(
        total_trasladado  =("quantity", "sum"),
        num_traslados     =("quantity", "count")
    ).reset_index()

    # Inventario por tienda
    inv_tienda = df_inv.groupby("tienda_id").agg(
        stock_total       =("site_qty",   "sum"),
        skus_activos      =("sku_id",     "count"),
        lead_time_prom    =("lead_time",  "mean"),
        skus_sin_repos    =("avoid_replenishment", "sum")
    ).reset_index()

    # Combinar todo
    df = df_tiendas.merge(ventas,       on="tienda_id", how="left")
    df = df.merge(reposiciones,         on="tienda_id", how="left")
    df = df.merge(devoluciones,         on="tienda_id", how="left")
    df = df.merge(traslados,            on="tienda_id", how="left")
    df = df.merge(inv_tienda,           on="tienda_id", how="left")

    df = df.fillna(0)

    # ─── Indicadores de eficiencia ───

    # 1. Cobertura de reposición: qué % de lo vendido fue repuesto
    df["cobertura_reposicion"] = np.where(
        df["total_ventas"] > 0,
        (df["total_repuesto"] / df["total_ventas"] * 100).clip(upper=150).round(2),
        0
    )

    # 2. Tasa de devolución: % de lo vendido que fue devuelto
    df["tasa_devolucion"] = np.where(
        df["total_ventas"] > 0,
        (df["total_devuelto"] / df["total_ventas"] * 100).round(2),
        0
    )

    # 3. Frecuencia de reposición: reposiciones por mes
    df["repos_por_mes"] = (df["num_reposiciones"] / 12).round(2)

    # 4. Eficiencia de cobertura de SKUs: % de SKUs vendidos que también fueron repuestos
    df["eficiencia_skus"] = np.where(
        df["skus_vendidos"] > 0,
        (df["skus_repuestos"] / df["skus_vendidos"] * 100).clip(upper=100).round(2),
        0
    )

    # 5. Índice de eficiencia global (0-100)
    # Cobertura óptima es cercana al 100% (ni mucho ni poco)
    df["cobertura_norm"] = (100 - abs(df["cobertura_reposicion"] - 100)).clip(lower=0) / 100
    df["devol_norm"]     = (1 - df["tasa_devolucion"].clip(upper=30) / 30)
    df["skus_norm"]      = df["eficiencia_skus"] / 100

    df["indice_eficiencia"] = ((df["cobertura_norm"] * 0.5) +
                               (df["devol_norm"]     * 0.3) +
                               (df["skus_norm"]      * 0.2)) * 100
    df["indice_eficiencia"] = df["indice_eficiencia"].round(2)

    # Clasificación
    def clasificar(idx):
        if idx >= 70:   return "🟢 Alta eficiencia"
        elif idx >= 45: return "🟡 Eficiencia media"
        else:           return "🔴 Baja eficiencia"

    df["clasificacion_eficiencia"] = df["indice_eficiencia"].apply(clasificar)

    print(f"   ✅ Eficiencia calculada para {len(df):,} tiendas\n")

    resumen = df.groupby("clasificacion_eficiencia").size().reset_index(name="cantidad")
    print("📊 Distribución de eficiencia de reposición:")
    print("─" * 45)
    for _, row in resumen.iterrows():
        print(f"  {row['clasificacion_eficiencia']:25} | {row['cantidad']:>4} tiendas")
    print("─" * 45)

    print("\n🏆 Ranking de tiendas por eficiencia de reposición:")
    print("─" * 80)
    for _, row in df.sort_values("indice_eficiencia", ascending=False).iterrows():
        print(f"  {row['nombre_tienda']:12} | {row['ciudad']:12} | "
              f"Cobertura: {row['cobertura_reposicion']:>6.1f}% | "
              f"Devolución: {row['tasa_devolucion']:>5.1f}% | "
              f"Índice: {row['indice_eficiencia']:>5.1f} | "
              f"{row['clasificacion_eficiencia']}")
    print("─" * 80)

    return df

# ─────────────────────────────────────────
# 3. Guardar en Go_BD
# ─────────────────────────────────────────
def guardar(engine, df):
    print("\n💾 Guardando en Go_BD...")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eficiencia_reposicion (
                id                      SERIAL PRIMARY KEY,
                tienda_id               VARCHAR(100),
                nombre_tienda           VARCHAR(255),
                ciudad                  VARCHAR(100),
                zona                    VARCHAR(100),
                clima                   VARCHAR(100),
                formato                 VARCHAR(100),
                total_ventas            NUMERIC(12,2),
                total_repuesto          NUMERIC(12,2),
                total_devuelto          NUMERIC(12,2),
                num_reposiciones        INTEGER,
                skus_vendidos           INTEGER,
                skus_repuestos          INTEGER,
                stock_total             NUMERIC(12,2),
                lead_time_prom          NUMERIC(10,2),
                cobertura_reposicion    NUMERIC(10,2),
                tasa_devolucion         NUMERIC(10,2),
                repos_por_mes           NUMERIC(10,2),
                eficiencia_skus         NUMERIC(10,2),
                indice_eficiencia       NUMERIC(10,2),
                clasificacion_eficiencia VARCHAR(50),
                fecha_calculo           TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

    cols = [
        "tienda_id","nombre_tienda","ciudad","zona","clima","formato",
        "total_ventas","total_repuesto","total_devuelto","num_reposiciones",
        "skus_vendidos","skus_repuestos","stock_total","lead_time_prom",
        "cobertura_reposicion","tasa_devolucion","repos_por_mes",
        "eficiencia_skus","indice_eficiencia","clasificacion_eficiencia"
    ]
    df[cols].to_sql("eficiencia_reposicion", engine, if_exists="replace", index=False)
    print(f"   ✅ {len(df):,} tiendas guardadas en tabla 'eficiencia_reposicion'")

def main():
    print("\n🚀 Iniciando Eficiencia de Reposición — Go_Retail\n")
    engine                      = conectar_engine()
    df_trans, df_inv, df_tiendas = leer_datos(engine)
    df                          = calcular_eficiencia(df_trans, df_inv, df_tiendas)
    guardar(engine, df)
    print("\n✅ Eficiencia de Reposición completada.")

if __name__ == "__main__":
    main()
