import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, text
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
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
# 1. Leer datos de inventario
# ─────────────────────────────────────────
def leer_datos(engine):
    print("📥 Leyendo datos desde Go_BD...\n")

    df_inv = pd.read_sql("""
        SELECT
            i.location_id   AS tienda_id,
            i.sku_id,
            i.site_qty,
            i.transit_qty,
            i.reserved_qty,
            i.min_stock,
            i.max_stock,
            i.replenishment_lead_time AS lead_time,
            i.avoid_replenishment
        FROM inventarios i
    """, engine)
    print(f"   ✅ Inventarios: {len(df_inv):,} registros")

    df_ventas = pd.read_sql("""
        SELECT
            sku_id,
            target_location_id AS tienda_id,
            AVG(quantity)      AS venta_diaria_prom,
            SUM(quantity)      AS venta_total,
            COUNT(*)           AS num_transacciones
        FROM transacciones
        WHERE type = 'venta'
        GROUP BY sku_id, target_location_id
    """, engine)
    print(f"   ✅ Ventas: {len(df_ventas):,} registros\n")

    return df_inv, df_ventas

# ─────────────────────────────────────────
# 2. Preparar features
# ─────────────────────────────────────────
def preparar_features(df_inv, df_ventas):
    print("🔧 Preparando features de inventario...")

    df = df_inv.merge(df_ventas, on=["sku_id", "tienda_id"], how="left")
    df["venta_diaria_prom"]  = df["venta_diaria_prom"].fillna(0)
    df["venta_total"]        = df["venta_total"].fillna(0)
    df["num_transacciones"]  = df["num_transacciones"].fillna(0)

    # Indicadores de salud del inventario
    df["cobertura_dias"]     = np.where(
        df["venta_diaria_prom"] > 0,
        df["site_qty"] / df["venta_diaria_prom"],
        999
    ).round(2)

    df["ratio_stock_min"]    = np.where(
        df["min_stock"] > 0,
        df["site_qty"] / df["min_stock"],
        1
    ).round(4)

    df["ratio_stock_max"]    = np.where(
        df["max_stock"] > 0,
        df["site_qty"] / df["max_stock"],
        1
    ).round(4)

    df["stock_disponible"]   = df["site_qty"] - df["reserved_qty"]
    df["stock_total_cadena"] = df["site_qty"] + df["transit_qty"]

    print(f"   ✅ Features preparadas: {len(df.columns)} variables\n")
    return df

# ─────────────────────────────────────────
# 3. Detectar anomalías con Isolation Forest
# ─────────────────────────────────────────
def detectar_anomalias(df):
    print("🤖 Ejecutando Isolation Forest...")

    features = [
        "site_qty", "transit_qty", "reserved_qty",
        "min_stock", "max_stock", "lead_time",
        "venta_diaria_prom", "venta_total",
        "cobertura_dias", "ratio_stock_min",
        "ratio_stock_max", "stock_disponible"
    ]

    features = [f for f in features if f in df.columns]
    X = df[features].fillna(0)

    # Escalar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Modelo Isolation Forest
    modelo = IsolationForest(
        contamination=0.1,  # 10% de registros esperados como anomalías
        random_state=42,
        n_estimators=100
    )

    df["anomalia"]      = modelo.fit_predict(X_scaled)
    df["score_anomalia"] = modelo.score_samples(X_scaled).round(4)

    # -1 = anomalía, 1 = normal
    df["es_anomalia"] = df["anomalia"] == -1

    total_anomalias = df["es_anomalia"].sum()
    print(f"   ✅ Anomalías detectadas: {total_anomalias:,} de {len(df):,} registros ({total_anomalias/len(df)*100:.1f}%)\n")

    return df

# ─────────────────────────────────────────
# 4. Clasificar tipo de anomalía
# ─────────────────────────────────────────
def clasificar_anomalias(df):
    print("🔍 Clasificando tipo de anomalías...")

    def tipo_anomalia(row):
        if not row["es_anomalia"]:
            return "Normal"
        if row["site_qty"] <= row["min_stock"]:
            return "🔴 Quiebre de stock"
        if row["site_qty"] >= row["max_stock"] * 1.5:
            return "🟡 Sobrestock"
        if row["cobertura_dias"] < row["lead_time"]:
            return "🟠 Riesgo de quiebre"
        if row["venta_diaria_prom"] == 0 and row["site_qty"] > 0:
            return "🔵 Sin movimiento"
        return "⚪ Anomalía general"

    df["tipo_anomalia"] = df.apply(tipo_anomalia, axis=1)

    # Resumen por tipo
    resumen = df[df["es_anomalia"]].groupby("tipo_anomalia").size().reset_index(name="cantidad")

    print("\n📊 Resumen de Anomalías Detectadas:")
    print("─" * 45)
    for _, row in resumen.iterrows():
        print(f"  {row['tipo_anomalia']:30} | {row['cantidad']:>4} registros")
    print("─" * 45)

    return df

# ─────────────────────────────────────────
# 5. Mostrar alertas críticas
# ─────────────────────────────────────────
def mostrar_alertas(df):
    criticos = df[df["tipo_anomalia"] == "🔴 Quiebre de stock"].nsmallest(10, "site_qty")
    riesgo   = df[df["tipo_anomalia"] == "🟠 Riesgo de quiebre"].nsmallest(10, "cobertura_dias")

    if not criticos.empty:
        print("\n🚨 TOP Quiebres de Stock:")
        print("─" * 60)
        for _, row in criticos.iterrows():
            print(f"  SKU {row['sku_id']:>6} | Tienda {row['tienda_id']:>4} | "
                  f"Stock: {row['site_qty']:>5.0f} | Min: {row['min_stock']:>5.0f} | "
                  f"Cobertura: {row['cobertura_dias']:>5.1f} días")
        print("─" * 60)

    if not riesgo.empty:
        print("\n⚠️  TOP Riesgos de Quiebre:")
        print("─" * 60)
        for _, row in riesgo.iterrows():
            print(f"  SKU {row['sku_id']:>6} | Tienda {row['tienda_id']:>4} | "
                  f"Stock: {row['site_qty']:>5.0f} | "
                  f"Cobertura: {row['cobertura_dias']:>5.1f} días | "
                  f"Lead time: {row['lead_time']:>2.0f} días")
        print("─" * 60)

# ─────────────────────────────────────────
# 6. Guardar en Go_BD
# ─────────────────────────────────────────
def guardar_anomalias(engine, df):
    print("\n💾 Guardando anomalías en Go_BD...")

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS anomalias_inventario (
                id              SERIAL PRIMARY KEY,
                tienda_id       VARCHAR(100),
                sku_id          VARCHAR(100),
                site_qty        NUMERIC(12,2),
                min_stock       NUMERIC(12,2),
                max_stock       NUMERIC(12,2),
                cobertura_dias  NUMERIC(12,2),
                es_anomalia     BOOLEAN,
                tipo_anomalia   VARCHAR(100),
                score_anomalia  NUMERIC(10,4),
                fecha_generacion TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

    df_save = df[[
        "tienda_id", "sku_id", "site_qty", "min_stock", "max_stock",
        "cobertura_dias", "es_anomalia", "tipo_anomalia", "score_anomalia"
    ]].copy()

    df_save.to_sql("anomalias_inventario", engine, if_exists="replace", index=False)
    print(f"   ✅ {len(df_save):,} registros guardados en tabla 'anomalias_inventario'")

# ─────────────────────────────────────────
# Ejecutar
# ─────────────────────────────────────────
def main():
    print("\n🚀 Iniciando detección de anomalías - Go_Retail\n")

    engine              = conectar_engine()
    df_inv, df_ventas   = leer_datos(engine)
    df                  = preparar_features(df_inv, df_ventas)
    df                  = detectar_anomalias(df)
    df                  = clasificar_anomalias(df)

    mostrar_alertas(df)
    guardar_anomalias(engine, df)

    print("\n✅ Proceso de detección de anomalías completado.")
    print("   Tabla guardada en Go_BD: anomalias_inventario")

if __name__ == "__main__":
    main()


# ─────────────────────────────────────────
# Punto de entrada para la Web API
# ─────────────────────────────────────────
def ejecutar_anomalias(engine) -> "pd.DataFrame":
    """Ejecuta detección de anomalías y retorna DataFrame. No guarda en BD."""
    df_inv, df_ventas = leer_datos(engine)
    df = preparar_features(df_inv, df_ventas)
    df = detectar_anomalias(df)
    df = clasificar_anomalias(df)
    # Solo columnas que existen en AnomaliaORM, sin NaN
    result = df[["sku_id", "tienda_id", "site_qty", "cobertura_dias",
                 "es_anomalia", "tipo_anomalia", "score_anomalia"]].copy()
    result = result.rename(columns={"site_qty": "stock_actual"})
    result["stock_actual"]  = result["stock_actual"].where(result["stock_actual"].notna(), None)
    result["cobertura_dias"] = result["cobertura_dias"].where(result["cobertura_dias"].notna(), None)
    result["score_anomalia"] = result["score_anomalia"].fillna(0)
    return result
