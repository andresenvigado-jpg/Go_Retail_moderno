import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import STYLE, COLORS, PLOTLY_TEMPLATE, kpi, section, header

st.set_page_config(page_title="Go Retail — Demanda", page_icon="📈", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)
load_dotenv()

@st.cache_resource
def conectar_engine():
    host     = os.getenv("DB_HOST")
    dbname   = os.getenv("DB_NAME")
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port     = os.getenv("DB_PORT", "5432")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require")

st.markdown(header("📈 Análisis de Demanda", "Pronósticos Prophet · Predicciones LightGBM por tienda"), unsafe_allow_html=True)
engine = conectar_engine()

# ── Pronóstico Prophet ──
st.markdown(section("🔮 Pronóstico de Demanda — Próximos 30 días (Prophet)"), unsafe_allow_html=True)

try:
    df_pron = pd.read_sql("SELECT * FROM pronosticos ORDER BY fecha", engine)
    df_pron["fecha"] = pd.to_datetime(df_pron["fecha"])

    top_skus = df_pron.groupby("sku_id")["demanda_estimada"].sum().nlargest(10).index.tolist()

    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        skus_sel = st.multiselect("Selecciona SKUs a visualizar", top_skus, default=top_skus[:5])
    with col_f2:
        vista = st.selectbox("Vista", ["Línea", "Área", "Barras"])

    df_top = df_pron[df_pron["sku_id"].isin(skus_sel)]

    if vista == "Línea":
        fig = px.line(df_top, x="fecha", y="demanda_estimada", color="sku_id",
                      labels={"fecha": "Fecha", "demanda_estimada": "Unidades estimadas", "sku_id": "SKU"})
    elif vista == "Área":
        fig = px.area(df_top, x="fecha", y="demanda_estimada", color="sku_id",
                      labels={"fecha": "Fecha", "demanda_estimada": "Unidades estimadas", "sku_id": "SKU"})
    else:
        fig = px.bar(df_top, x="fecha", y="demanda_estimada", color="sku_id",
                     labels={"fecha": "Fecha", "demanda_estimada": "Unidades estimadas", "sku_id": "SKU"})

    fig.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0, r=0, t=10, b=0), height=340)
    st.plotly_chart(fig, use_container_width=True)

    # KPIs Prophet
    resumen_pron = df_pron.groupby("sku_id").agg(
        demanda_total  =("demanda_estimada", "sum"),
        demanda_diaria =("demanda_estimada", "mean"),
        demanda_max    =("demanda_maxima",   "max")
    ).round(1).reset_index().sort_values("demanda_total", ascending=False).head(10)

    st.markdown(section("Tabla de Pronósticos por SKU"), unsafe_allow_html=True)
    resumen_pron.columns = ["SKU", "Demanda total 30d", "Promedio diario", "Máximo estimado"]
    st.dataframe(resumen_pron, use_container_width=True, hide_index=True, height=320)

except Exception:
    st.info("ℹ️ Ejecuta modelo_pronostico.py para ver los pronósticos de demanda.")

st.divider()

# ── LightGBM ──
st.markdown(section("🤖 Predicciones LightGBM — Por SKU y Tienda"), unsafe_allow_html=True)

try:
    df_lgbm = pd.read_sql("""
        SELECT sku_id, tienda_id,
               AVG(cantidad_real)     AS real_prom,
               AVG(cantidad_predicha) AS pred_prom,
               COUNT(*)               AS registros
        FROM predicciones_lgbm
        GROUP BY sku_id, tienda_id
        ORDER BY real_prom DESC
        LIMIT 200
    """, engine)

    c1, c2, c3 = st.columns(3)
    mae = abs(df_lgbm["real_prom"] - df_lgbm["pred_prom"]).mean()
    with c1: st.markdown(kpi("Combinaciones SKU-Tienda", len(df_lgbm), "info"), unsafe_allow_html=True)
    with c2: st.markdown(kpi("Error promedio (MAE)", f"{mae:.2f} und", "success"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("Venta real promedio", f"{df_lgbm['real_prom'].mean():.1f} und", "neutral"), unsafe_allow_html=True)

    col_l1, col_l2 = st.columns(2)

    with col_l1:
        fig_comp = px.scatter(df_lgbm, x="real_prom", y="pred_prom",
                              color_discrete_sequence=[COLORS["primary"]],
                              labels={"real_prom": "Venta real promedio", "pred_prom": "Predicción promedio"},
                              title="Real vs Predicción")
        fig_comp.add_shape(type="line", x0=0, y0=0,
                           x1=df_lgbm["real_prom"].max(),
                           y1=df_lgbm["real_prom"].max(),
                           line=dict(color=COLORS["danger"], dash="dash"))
        fig_comp.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0, r=0, t=40, b=0), height=320)
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_l2:
        df_tienda = df_lgbm.groupby("tienda_id").agg(
            real_prom=("real_prom", "mean"),
            pred_prom=("pred_prom", "mean")
        ).reset_index().sort_values("real_prom", ascending=False).head(15)
        fig_t = px.bar(df_tienda, x="tienda_id", y=["real_prom", "pred_prom"],
                       barmode="group",
                       color_discrete_sequence=[COLORS["primary"], COLORS["info"]],
                       labels={"tienda_id": "Tienda", "value": "Unidades", "variable": ""},
                       title="Real vs Predicción por Tienda")
        fig_t.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0, r=0, t=40, b=0), height=320)
        st.plotly_chart(fig_t, use_container_width=True)

except Exception:
    st.info("ℹ️ Ejecuta modelo_lightgbm.py para ver las predicciones por tienda.")

st.divider()
st.caption("Go Retail v3.0 · Módulo de Demanda")
