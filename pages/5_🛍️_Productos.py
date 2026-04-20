import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import STYLE, COLORS, PLOTLY_TEMPLATE, kpi, section, header

st.set_page_config(page_title="Go Retail — Productos", page_icon="🛍️", layout="wide")
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

st.markdown(header("🛍️ Análisis de Productos", "Segmentación ABC · Market Basket Analysis"), unsafe_allow_html=True)
engine = conectar_engine()

tab1, tab2 = st.tabs(["🗂️ Segmentación ABC", "🛒 Market Basket"])

# ── Tab 1: ABC ──
with tab1:
    st.markdown(section("Segmentación ABC de Productos"), unsafe_allow_html=True)
    try:
        df_abc = pd.read_sql("SELECT * FROM segmentacion_skus", engine)

        abc_a = len(df_abc[df_abc["segmento_abc"] == "A - Alta rotación"])
        abc_b = len(df_abc[df_abc["segmento_abc"] == "B - Rotación media"])
        abc_c = len(df_abc[df_abc["segmento_abc"] == "C - Baja rotación"])

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(kpi("Total SKUs",       len(df_abc), "info"),    unsafe_allow_html=True)
        with c2: st.markdown(kpi("Categoría A",      abc_a,       "success",  "70% de ventas"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Categoría B",      abc_b,       "warning",  "20% de ventas"), unsafe_allow_html=True)
        with c4: st.markdown(kpi("Categoría C",      abc_c,       "danger",   "10% de ventas"), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            resumen = df_abc.groupby("segmento_abc").agg(
                skus          =("sku_id",         "count"),
                ventas_totales=("cantidad_total",  "sum"),
                precio_prom   =("precio_promedio", "mean")
            ).round(1).reset_index()
            fig = px.pie(resumen, names="segmento_abc", values="skus",
                         color_discrete_sequence=[COLORS["primary"], COLORS["warning"], COLORS["danger"]],
                         hole=0.5)
            fig.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0), height=320)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.bar(resumen, x="segmento_abc", y="ventas_totales",
                          color="segmento_abc",
                          color_discrete_sequence=[COLORS["primary"], COLORS["warning"], COLORS["danger"]],
                          labels={"segmento_abc":"Segmento","ventas_totales":"Ventas totales"})
            fig2.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0),
                               height=320, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Tabla detalle con filtro
        st.markdown(section("Detalle de SKUs por Segmento"), unsafe_allow_html=True)
        seg_fil = st.selectbox("Filtrar por segmento", ["Todos"] + df_abc["segmento_abc"].unique().tolist())
        df_fil  = df_abc if seg_fil == "Todos" else df_abc[df_abc["segmento_abc"] == seg_fil]

        df_show = df_fil[["sku_id","segmento_abc","cantidad_total","cantidad_promedio",
                           "precio_promedio","num_tiendas","participacion","acumulado"]].copy()
        df_show["participacion"] = (df_show["participacion"] * 100).round(2).astype(str) + "%"
        df_show["acumulado"]     = (df_show["acumulado"]     * 100).round(2).astype(str) + "%"
        df_show.columns = ["SKU","Segmento","Ventas totales","Venta promedio",
                           "Precio promedio","Tiendas","Participación","Acumulado"]
        st.dataframe(df_show, use_container_width=True, hide_index=True, height=340)

    except Exception:
        st.info("ℹ️ Ejecuta modelo_segmentacion.py para ver la segmentación ABC.")

# ── Tab 2: Market Basket ──
with tab2:
    st.markdown(section("Market Basket Analysis — Productos que se compran juntos"), unsafe_allow_html=True)
    try:
        df_mb = pd.read_sql("SELECT * FROM market_basket ORDER BY lift DESC", engine)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(kpi("Total reglas",       len(df_mb),                     "info"),    unsafe_allow_html=True)
        with c2: st.markdown(kpi("Lift promedio",      f"{df_mb['lift'].mean():.2f}",  "success"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Confianza promedio", f"{df_mb['confianza'].mean()*100:.1f}%", "neutral"), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔗 Reglas de asociación más fuertes**")
            df_show = df_mb[["sku_origen","sku_destino","confianza","lift","soporte"]].head(20).copy()
            df_show["confianza"] = (df_show["confianza"] * 100).round(1).astype(str) + "%"
            df_show["soporte"]   = (df_show["soporte"]   * 100).round(1).astype(str) + "%"
            df_show["lift"]      = df_show["lift"].round(2)
            df_show.columns = ["Si compra SKU","También lleva SKU","Confianza","Lift","Soporte"]
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)

        with col2:
            fig = px.histogram(df_mb, x="lift", nbins=20,
                               color_discrete_sequence=[COLORS["primary"]],
                               labels={"lift":"Lift","count":"Número de reglas"})
            fig.add_vline(x=1, line_dash="dash", line_color=COLORS["danger"],
                         annotation_text="Lift=1 (sin relación)")
            fig.add_vline(x=2, line_dash="dash", line_color=COLORS["warning"],
                         annotation_text="Lift=2 (relación fuerte)")
            fig.update_layout(**PLOTLY_TEMPLATE, margin=dict(l=0,r=0,t=10,b=0), height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Interpretación
        st.markdown(section("¿Cómo interpretar los resultados?"), unsafe_allow_html=True)
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            st.markdown("""
            <div class="content-card">
                <div class="kpi-label">LIFT > 1</div>
                <div style="font-size:14px;color:#2C2C2C;">Existe una relación real entre los productos. No es casual.</div>
            </div>""", unsafe_allow_html=True)
        with col_i2:
            st.markdown("""
            <div class="content-card">
                <div class="kpi-label">LIFT > 2</div>
                <div style="font-size:14px;color:#2C2C2C;">Relación fuerte. Se recomienda abastecer estos productos juntos.</div>
            </div>""", unsafe_allow_html=True)
        with col_i3:
            st.markdown("""
            <div class="content-card">
                <div class="kpi-label">LIFT > 3</div>
                <div style="font-size:14px;color:#2C2C2C;">Relación muy fuerte. Considerar como combo o promoción cruzada.</div>
            </div>""", unsafe_allow_html=True)

    except Exception:
        st.info("ℹ️ Ejecuta modelo_market_basket.py para ver los productos que se compran juntos.")

st.divider()
st.caption("Go Retail v3.0 · Módulo de Productos")
