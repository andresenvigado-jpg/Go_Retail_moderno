import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
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
# 1. Leer y combinar datos
# ─────────────────────────────────────────
def leer_datos(engine):
    print("📥 Leyendo datos desde Go_BD...\n")

    # Transacciones de ventas
    df_ventas = pd.read_sql("""
        SELECT
            t.sku_id,
            t.target_location_id    AS tienda_id,
            DATE(t.transaction_date) AS fecha,
            SUM(t.quantity)          AS cantidad,
            AVG(t.sale_price)        AS precio_promedio
        FROM transacciones t
        WHERE t.type = 'venta'
        GROUP BY t.sku_id, t.target_location_id, DATE(t.transaction_date)
        ORDER BY fecha
    """, engine)
    print(f"   ✅ Ventas: {len(df_ventas):,} registros")

    # Tiendas con sus características
    df_tiendas = pd.read_sql("""
        SELECT
            id::VARCHAR       AS tienda_id,
            custom_clima      AS clima,
            custom_zona       AS zona,
            custom_formato    AS formato,
            city              AS ciudad,
            default_replenishment_lead_time AS lead_time
        FROM tiendas
    """, engine)
    print(f"   ✅ Tiendas: {len(df_tiendas):,} registros")

    # Catálogo con características de producto
    df_catalogo = pd.read_sql("""
        SELECT
            id::VARCHAR       AS sku_id,
            categories        AS categoria,
            brands            AS marca,
            seasons           AS temporada,
            size              AS talla,
            price,
            cost,
            custom_tipolinea  AS tipo_linea
        FROM catalogos
    """, engine)
    print(f"   ✅ Catálogo: {len(df_catalogo):,} registros\n")

    return df_ventas, df_tiendas, df_catalogo

# ─────────────────────────────────────────
# 2. Preparar features para LightGBM
# ─────────────────────────────────────────
def preparar_features(df_ventas, df_tiendas, df_catalogo):
    print("🔧 Preparando features...")

    # Unir ventas con tiendas y catálogo
    df = df_ventas.merge(df_tiendas, on="tienda_id", how="left")
    df = df.merge(df_catalogo, on="sku_id", how="left")

    # Features de fecha
    df["fecha"]     = pd.to_datetime(df["fecha"])
    df["dia_semana"] = df["fecha"].dt.dayofweek
    df["mes"]        = df["fecha"].dt.month
    df["semana"]     = df["fecha"].dt.isocalendar().week.astype(int)
    df["es_fin_semana"] = (df["dia_semana"] >= 5).astype(int)

    # Features de temporada alta
    df["temporada_alta"] = df["mes"].isin([1, 2, 6, 7, 10, 11, 12]).astype(int)

    # Margen del producto
    df["margen"] = ((df["price"] - df["cost"]) / df["price"]).round(4)

    # Codificar variables categóricas
    categoricas = ["clima", "zona", "formato", "ciudad", "categoria",
                   "marca", "temporada", "talla", "tipo_linea"]

    le = LabelEncoder()
    for col in categoricas:
        if col in df.columns:
            df[col] = df[col].fillna("desconocido")
            df[col] = le.fit_transform(df[col].astype(str))

    df = df.dropna(subset=["cantidad"])
    print(f"   ✅ Dataset final: {len(df):,} registros con {len(df.columns)} variables\n")

    return df

# ─────────────────────────────────────────
# 3. Entrenar modelo LightGBM
# ─────────────────────────────────────────
def entrenar_lightgbm(df):
    print("🤖 Entrenando modelo LightGBM...")

    features = [
        "dia_semana", "mes", "semana", "es_fin_semana", "temporada_alta",
        "clima", "zona", "formato", "ciudad", "lead_time",
        "categoria", "marca", "temporada", "talla", "tipo_linea",
        "price", "cost", "margen", "precio_promedio"
    ]

    # Filtrar features disponibles
    features = [f for f in features if f in df.columns]
    target   = "cantidad"

    X = df[features]
    y = df[target]

    # Dividir en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Configurar y entrenar modelo
    params = {
        "objective":      "regression",
        "metric":         "mae",
        "learning_rate":  0.05,
        "num_leaves":     31,
        "min_data_in_leaf": 5,
        "verbose":        -1
    }

    train_data = lgb.Dataset(X_train, label=y_train)
    test_data  = lgb.Dataset(X_test,  label=y_test, reference=train_data)

    modelo = lgb.train(
        params,
        train_data,
        num_boost_round=200,
        valid_sets=[test_data],
        callbacks=[lgb.early_stopping(20), lgb.log_evaluation(50)]
    )

    # Evaluar modelo
    y_pred = modelo.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)

    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"\n📈 Resultados del modelo:")
    print(f"   MAE  (error promedio):  {mae:.2f} unidades")
    print(f"   RMSE (error cuadrático): {rmse:.2f} unidades\n")

    return modelo, features, mae, rmse

# ─────────────────────────────────────────
# 4. Importancia de variables
# ─────────────────────────────────────────
def mostrar_importancia(modelo, features):
    print("🔍 Variables más influyentes en la demanda:")
    print("─" * 50)

    importancia = pd.DataFrame({
        "variable":    features,
        "importancia": modelo.feature_importance(importance_type="gain")
    }).sort_values("importancia", ascending=False).head(10)

    for _, row in importancia.iterrows():
        barra = "█" * int(row["importancia"] / importancia["importancia"].max() * 20)
        print(f"  {row['variable']:>20} | {barra}")

    print("─" * 50)

# ─────────────────────────────────────────
# 5. Guardar predicciones en Go_BD
# ─────────────────────────────────────────
def guardar_predicciones(engine, df, modelo, features):
    print("\n💾 Generando y guardando predicciones en Go_BD...")

    with engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text("""
            CREATE TABLE IF NOT EXISTS predicciones_lgbm (
                id                  SERIAL PRIMARY KEY,
                sku_id              VARCHAR(100),
                tienda_id           VARCHAR(100),
                fecha               DATE,
                cantidad_real       NUMERIC(12,2),
                cantidad_predicha   NUMERIC(12,2),
                fecha_generacion    TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

    df_pred = df[["sku_id", "tienda_id", "fecha", "cantidad"]].copy()
    df_pred["cantidad_predicha"] = np.clip(
        modelo.predict(df[features]), 0, None
    ).round(2)
    df_pred = df_pred.rename(columns={"cantidad": "cantidad_real"})

    df_pred.to_sql("predicciones_lgbm", engine, if_exists="append", index=False)
    print(f"   ✅ {len(df_pred):,} predicciones guardadas en tabla 'predicciones_lgbm'")

# ─────────────────────────────────────────
# Ejecutar
# ─────────────────────────────────────────
def main():
    print("\n🚀 Iniciando modelo LightGBM - Go_Retail\n")

    engine                      = conectar_engine()
    df_ventas, df_tiendas, df_catalogo = leer_datos(engine)
    df                          = preparar_features(df_ventas, df_tiendas, df_catalogo)
    modelo, features, mae, rmse = entrenar_lightgbm(df)

    mostrar_importancia(modelo, features)
    guardar_predicciones(engine, df, modelo, features)

    print("\n✅ Proceso LightGBM completado.")
    print(f"   Precisión del modelo: error promedio de {mae:.1f} unidades por predicción")

if __name__ == "__main__":
    main()


# ─────────────────────────────────────────
# Punto de entrada para la Web API
# ─────────────────────────────────────────
def ejecutar_lightgbm(engine) -> "pd.DataFrame":
    """
    Ejecuta LightGBM y retorna DataFrame con predicciones.
    No guarda en BD — lo hace el repositorio.
    """
    df_ventas, df_tiendas, df_catalogo = leer_datos(engine)
    df = preparar_features(df_ventas, df_tiendas, df_catalogo)
    modelo, features, _, _ = entrenar_lightgbm(df)

    df_pred = df[["sku_id", "tienda_id", "cantidad"]].copy()
    df_pred["cantidad_predicha"] = np.clip(
        modelo.predict(df[features]), 0, None
    ).round(2)
    return df_pred.rename(columns={"cantidad": "cantidad_real"})[
        ["sku_id", "tienda_id", "cantidad_real", "cantidad_predicha"]
    ]
