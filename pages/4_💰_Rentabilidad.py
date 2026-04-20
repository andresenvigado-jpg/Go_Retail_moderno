import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import STYLE, COLORS, PLOTLY_TEMPLATE, kpi, section, header

st.set_page_config(page_title="Go Retail — Rentabilidad", page_icon="💰", layout="wide")
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

st.markdown(header("💰 Rentabilidad y Rotación", "Índice de margen real · Velocidad de movimiento de productos"), unsafe_allow_html=True)
engine = conectar_engine()

tab1, tab2 = st.tabs(["💰 Índice de Rentabilidad", "🔄 Velocidad de Rotación"])

# ── Tab 1: Rentabilidad ──
with tab1:
    st.markdown(section("Índice de Rentabilidad por SKU y Tienda"), unsafe_allow_html=True)
    try:
        df_r = pd.read_sql("SELECT * FROM rentabilidad_sku ORDER BY indice_rentabilidad DESC", engine)

        alta  = len(df_r[df_r["clasificacion"] == "🟢 Alta rentabilidad"])
        media = len(df_r[df_r["clasificacion"] == "🟡 Rentabilidad media"])
        baja  = len(df_r[df_r["clasificacion"] == "🔴 Baja rentabilidad"])
        margen_prom       = df_r["margen_porcentual"].mean()
        rentabilidad_total = df_r["rentabilidad_total"].sum()

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.markdown(kpi("Alta rentabilidad",   alta,                              "success"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Rentabilidad media",  media,                             "warning"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Baja rentabilidad",   baja,                              "danger"),  unsafe_allow_html=True)
        with c4: st.markdown(kpi("Margen promedio",     f"{margen_prom:.1f}%",             "info"),    unsafe_allow_html=True)
        with c5: st.markdown(kpi("Rentabilidad total",  f"${rentabilidad_total:,.0f} COP", "success"), unsafe_allow_html=True)

        # Filtros
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            cats = ["Todas"] + sorted(df_r["categoria"].dropna().unique().tolist())
            cat_sel = st.selectbox("Categoría", cats)
        with col_f2:
            marcas = ["Todas"] + sorted(df_r["marca"].dropna().unique().tolist())
            marca_sel = st.selectbox("Marca", marcas)
        with col_f3:
            clases = ["Todas"] + df_r["clasificacion"].unique().tolist()
            clase_sel = st.selectbox("Clasificación", clases)

        df_fil = df_r.copy()
        if cat_sel   != "Todas": df_fil = df_fil[df_fil["categoria"]     == cat_sel]
        if marca_sel != "Todas": df_fil = df_fil[df_fil["marca"]         == marca_sel]
        if clase_sel != "Todas": df_fil = df_fil[df_fil["clasificacion"] == clase_sel]

        col1, col2 = st.columns(2)
        with col1:
            df_show = df_fil[["sku_id","tienda_id","categoria","margen_porcentual",
                               "rentabilidad_total","indice_rentabilidad","clasificacion"]].head(20)
            df_show.columns = ["SKU","Tienda","Categoría","Margen %","Rentabilidad COP","Índice","Clasificación"]
            df_show["Margen %"]        = df_show["Margen %"].round(1)
            df_show["Rentabilidad COP"]= df_show["Rentabilidad COP"].round(0)
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=380)

        with col2:
            df_cat = df_fil.groupby("categoria").agg(
                margen_prom      =("margen_porcentual",  "mean"),
                rentabilidad_sum =("rentabilidad_total", "sum"),
                skus             =("sku_id",             "nunique")
            ).round(1).reset_index().sort_values("margen_prom", ascending=False)
            fig = px.bar(df_cat, x="categoria", y="margen_prom",
                         color="margen_prom",
                         color_continuous_scale=["#FFEBEE","#EF9F27","#5BA033"],
                         labels={"categoria":"Categoría","margen_prom":"Margen promedio %"})
            fig.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0),
                              height=380, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        # Scatter margen vs volumen
        st.markdown(section("Margen vs Volumen de Ventas"), unsafe_allow_html=True)
        fig_s = px.scatter(df_fil, x="unidades_vendidas", y="margen_porcentual",
                           color="clasificacion", size="rentabilidad_total",
                           color_discrete_sequence=[COLORS["primary"], COLORS["warning"], COLORS["danger"]],
                           labels={"unidades_vendidas":"Unidades vendidas",
                                   "margen_porcentual":"Margen %",
                                   "clasificacion":"Clasificación"},
                           hover_data=["sku_id","tienda_id","categoria"])
        fig_s.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0), height=320)
        st.plotly_chart(fig_s, use_container_width=True)

    except Exception:
        st.info("ℹ️ Ejecuta modelo_rentabilidad.py para ver el índice de rentabilidad.")

# ── Tab 2: Rotación ──
with tab2:
    st.markdown(section("Velocidad de Rotación de Productos"), unsafe_allow_html=True)
    try:
        df_rot = pd.read_sql("SELECT * FROM rotacion_sku ORDER BY indice_velocidad DESC", engine)

        alta_rot  = len(df_rot[df_rot["clasificacion_rotacion"] == "🚀 Alta rotación"])
        media_rot = len(df_rot[df_rot["clasificacion_rotacion"] == "🔄 Rotación media"])
        lenta_rot = len(df_rot[df_rot["clasificacion_rotacion"] == "🐢 Rotación lenta"])
        sin_mov   = len(df_rot[df_rot["clasificacion_rotacion"] == "❄️  Sin movimiento"])

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(kpi("Alta rotación",   alta_rot,  "success"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Rotación media",  media_rot, "info"),    unsafe_allow_html=True)
        with c3: st.markdown(kpi("Rotación lenta",  lenta_rot, "warning"), unsafe_allow_html=True)
        with c4: st.markdown(kpi("Sin movimiento",  sin_mov,   "danger"),  unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            df_show = df_rot[["sku_id","tienda_id","categoria","tasa_rotacion_anual",
                               "dsi","frecuencia_venta","indice_velocidad","clasificacion_rotacion"]].head(20)
            df_show.columns = ["SKU","Tienda","Categoría","Rotación anual","DSI días","Frecuencia %","Índice","Clasificación"]
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=380)

        with col2:
            df_cat_v = df_rot.groupby("categoria").agg(
                velocidad_prom=("indice_velocidad",   "mean"),
                dsi_prom      =("dsi",                "mean"),
                skus          =("sku_id",             "nunique")
            ).round(1).reset_index().sort_values("velocidad_prom", ascending=False)
            fig = px.bar(df_cat_v, x="categoria", y="velocidad_prom",
                         color="velocidad_prom",
                         color_continuous_scale=["#FFEBEE","#EF9F27","#5BA033"],
                         labels={"categoria":"Categoría","velocidad_prom":"Índice velocidad promedio"})
            fig.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0),
                              height=380, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        # DSI por categoría
        st.markdown(section("Días de Inventario (DSI) por Categoría"), unsafe_allow_html=True)
        fig_dsi = px.box(df_rot, x="categoria", y="dsi", color="categoria",
                         color_discrete_sequence=[COLORS["primary"], COLORS["warning"],
                                                   COLORS["danger"], COLORS["info"],
                                                   COLORS["neutral"], COLORS["dark"]],
                         labels={"categoria":"Categoría","dsi":"Días de inventario (DSI)"})
        fig_dsi.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0),
                              height=300, showlegend=False)
        st.plotly_chart(fig_dsi, use_container_width=True)

    except Exception:
        st.info("ℹ️ Ejecuta modelo_rotacion.py para ver la velocidad de rotación.")

st.divider()
st.caption("Go Retail v3.0 · Módulo de Rentabilidad")
