import pandas as pd
import os
from sqlalchemy import create_engine
from prophet import Prophet
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
# 1. Leer transacciones de Go_BD
# ─────────────────────────────────────────
def leer_transacciones(engine):
    print("📥 Leyendo transacciones desde Go_BD...")
    query = """
        SELECT 
            sku_id,
            DATE(transaction_date) AS fecha,
            SUM(quantity)          AS cantidad
        FROM transacciones
        WHERE type = 'venta'
        GROUP BY sku_id, DATE(transaction_date)
        ORDER BY sku_id, fecha
    """
    df = pd.read_sql(query, engine)
    print(f"   ✅ {len(df):,} registros leídos.\n")
    return df

# ─────────────────────────────────────────
# 2. Entrenar Prophet por SKU
# ─────────────────────────────────────────
def entrenar_pronostico(df, dias_pronostico=30, top_skus=10):
    print(f"🤖 Entrenando modelo Prophet (top {top_skus} SKUs más vendidos)...\n")

    # Seleccionar los SKUs con más ventas
    top = (
        df.groupby("sku_id")["cantidad"]
        .sum()
        .nlargest(top_skus)
        .index.tolist()
    )

    resultados = []

    for sku in top:
        df_sku = df[df["sku_id"] == sku][["fecha", "cantidad"]].copy()
        df_sku.columns = ["ds", "y"]
        df_sku["ds"] = pd.to_datetime(df_sku["ds"])

        # Necesitamos al menos 2 puntos para entrenar
        if len(df_sku) < 2:
            continue

        try:
            modelo = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95
            )
            modelo.fit(df_sku)

            # Generar fechas futuras
            futuro = modelo.make_future_dataframe(periods=dias_pronostico)
            pronostico = modelo.predict(futuro)

            # Tomar solo los días futuros
            df_futuro = pronostico[pronostico["ds"] > df_sku["ds"].max()][
                ["ds", "yhat", "yhat_lower", "yhat_upper"]
            ].copy()
            df_futuro["sku_id"] = sku
            df_futuro["yhat"] = df_futuro["yhat"].clip(lower=0).round(2)
            df_futuro["yhat_lower"] = df_futuro["yhat_lower"].clip(lower=0).round(2)
            df_futuro["yhat_upper"] = df_futuro["yhat_upper"].clip(lower=0).round(2)

            resultados.append(df_futuro)
            print(f"   ✅ SKU {sku} → pronóstico generado para {dias_pronostico} días")

        except Exception as e:
            print(f"   ⚠️  SKU {sku} → error: {e}")

    if not resultados:
        print("❌ No se generaron pronósticos.")
        return pd.DataFrame()

    return pd.concat(resultados, ignore_index=True)

# ─────────────────────────────────────────
# 3. Guardar pronósticos en Go_BD
# ─────────────────────────────────────────
def guardar_pronosticos(engine, df_pronostico):
    if df_pronostico.empty:
        print("⚠️  Sin datos para guardar.")
        return

    print("\n💾 Guardando pronósticos en Go_BD...")

    # Crear tabla de pronósticos si no existe
    with engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text("""
            CREATE TABLE IF NOT EXISTS pronosticos (
                id          SERIAL PRIMARY KEY,
                sku_id      VARCHAR(100),
                fecha       DATE,
                demanda_estimada   NUMERIC(12,2),
                demanda_minima     NUMERIC(12,2),
                demanda_maxima     NUMERIC(12,2),
                fecha_generacion   TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

    df_save = df_pronostico.rename(columns={
        "ds":          "fecha",
        "yhat":        "demanda_estimada",
        "yhat_lower":  "demanda_minima",
        "yhat_upper":  "demanda_maxima"
    })[["sku_id", "fecha", "demanda_estimada", "demanda_minima", "demanda_maxima"]]

    df_save.to_sql("pronosticos", engine, if_exists="append", index=False)
    print(f"   ✅ {len(df_save):,} registros de pronóstico guardados en tabla 'pronosticos'.")

# ─────────────────────────────────────────
# 4. Mostrar resumen en consola
# ─────────────────────────────────────────
def mostrar_resumen(df_pronostico):
    if df_pronostico.empty:
        return

    print("\n📊 RESUMEN DE PRONÓSTICOS (próximos 30 días)")
    print("─" * 60)

    resumen = (
        df_pronostico.groupby("sku_id")
        .agg(
            demanda_total=("yhat", "sum"),
            demanda_diaria_prom=("yhat", "mean"),
            demanda_maxima=("yhat_upper", "max")
        )
        .round(2)
        .reset_index()
        .sort_values("demanda_total", ascending=False)
    )

    for _, row in resumen.iterrows():
        print(f"  SKU {row['sku_id']:>6} | "
              f"Total estimado: {row['demanda_total']:>8.1f} | "
              f"Promedio diario: {row['demanda_diaria_prom']:>6.1f} | "
              f"Máximo estimado: {row['demanda_maxima']:>6.1f}")

    print("─" * 60)

# ─────────────────────────────────────────
# Ejecutar
# ─────────────────────────────────────────
def main():
    print("\n🚀 Iniciando modelo de pronóstico de demanda - Go_Retail\n")

    engine          = conectar_engine()
    df_transac      = leer_transacciones(engine)
    df_pronostico   = entrenar_pronostico(df_transac, dias_pronostico=30, top_skus=10)
    guardar_pronosticos(engine, df_pronostico)
    mostrar_resumen(df_pronostico)

    print("\n✅ Proceso completado.")

if __name__ == "__main__":
    main()
