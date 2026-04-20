import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import STYLE, COLORS, PLOTLY_TEMPLATE, kpi, section, header

st.set_page_config(page_title="Go Retail — Tiendas", page_icon="🏪", layout="wide")
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

st.markdown(header("🏪 Análisis de Tiendas", "Segmentación K-Means · Eficiencia de Reposición"), unsafe_allow_html=True)
engine = conectar_engine()

tab1, tab2 = st.tabs(["📊 Segmentación", "🔄 Eficiencia de Reposición"])

# ── Tab 1: Segmentación ──
with tab1:
    st.markdown(section("Segmentación de Tiendas — K-Means"), unsafe_allow_html=True)
    try:
        df_t = pd.read_sql("SELECT * FROM segmentacion_tiendas", engine)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(kpi("Total tiendas",     len(df_t),                           "info"),    unsafe_allow_html=True)
        with c2: st.markdown(kpi("Venta promedio",    f"{df_t['ventas_totales'].mean():.0f} und", "success"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("SKUs prom/tienda",  f"{df_t['num_skus'].mean():.0f}",    "neutral"), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_t.sort_values("ventas_totales", ascending=True),
                         x="ventas_totales", y="tienda_id", color="segmento_tienda",
                         orientation="h",
                         color_discrete_sequence=[COLORS["danger"], COLORS["warning"],
                                                   COLORS["primary"], COLORS["neutral"]],
                         labels={"ventas_totales":"Ventas totales","tienda_id":"Tienda","segmento_tienda":"Segmento"})
            fig.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0), height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            resumen_seg = df_t.groupby("segmento_tienda").agg(
                tiendas      =("tienda_id",      "count"),
                ventas_prom  =("ventas_totales", "mean"),
                skus_prom    =("num_skus",       "mean")
            ).round(1).reset_index()
            resumen_seg.columns = ["Segmento","Tiendas","Ventas prom","SKUs prom"]
            st.dataframe(resumen_seg, use_container_width=True, hide_index=True, height=200)

            if "ciudad" in df_t.columns:
                df_ciudad = df_t.groupby("ciudad").agg(
                    ventas=("ventas_totales","sum"), tiendas=("tienda_id","count")
                ).reset_index().sort_values("ventas", ascending=False)
                fig2 = px.bar(df_ciudad, x="ciudad", y="ventas",
                              color="ventas", color_continuous_scale=["#C8E6B0","#5BA033","#3D7A1F"],
                              labels={"ciudad":"Ciudad","ventas":"Ventas totales"})
                fig2.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0),
                                   height=200, coloraxis_showscale=False)
                st.plotly_chart(fig2, use_container_width=True)

    except Exception:
        st.info("ℹ️ Ejecuta modelo_segmentacion.py para ver la segmentación de tiendas.")

# ── Tab 2: Eficiencia ──
with tab2:
    st.markdown(section("Eficiencia de Reposición por Tienda"), unsafe_allow_html=True)
    try:
        df_ef = pd.read_sql("SELECT * FROM eficiencia_reposicion ORDER BY indice_eficiencia DESC", engine)

        alta  = len(df_ef[df_ef["clasificacion_eficiencia"] == "🟢 Alta eficiencia"])
        media = len(df_ef[df_ef["clasificacion_eficiencia"] == "🟡 Eficiencia media"])
        baja  = len(df_ef[df_ef["clasificacion_eficiencia"] == "🔴 Baja eficiencia"])
        cob   = df_ef["cobertura_reposicion"].mean()

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(kpi("Alta eficiencia",    alta,          "success"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Eficiencia media",   media,         "warning"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Baja eficiencia",    baja,          "danger"),  unsafe_allow_html=True)
        with c4: st.markdown(kpi("Cobertura promedio", f"{cob:.1f}%", "info"),    unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            df_show = df_ef[["nombre_tienda","ciudad","cobertura_reposicion",
                              "tasa_devolucion","indice_eficiencia","clasificacion_eficiencia"]]
            df_show.columns = ["Tienda","Ciudad","Cobertura %","Devolución %","Índice","Clasificación"]
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)

        with col2:
            df_ciudad = df_ef.groupby("ciudad").agg(
                eficiencia_prom=("indice_eficiencia","mean"),
                tiendas        =("tienda_id","count")
            ).round(1).reset_index().sort_values("eficiencia_prom", ascending=False)
            fig = px.bar(df_ciudad, x="ciudad", y="eficiencia_prom",
                         color="eficiencia_prom",
                         color_continuous_scale=["#E24B4A","#EF9F27","#5BA033"],
                         labels={"ciudad":"Ciudad","eficiencia_prom":"Índice eficiencia"})
            fig.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0),
                              height=400, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    except Exception:
        st.info("ℹ️ Ejecuta modelo_eficiencia_reposicion.py para ver la eficiencia de reposición.")

st.divider()
st.caption("Go Retail v3.0 · Módulo de Tiendas")
