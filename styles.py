STYLE = """
<style>
    /* ── Fuente y fondo general ── */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background-color: #F5F5F5;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #2C2C2C;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 15px;
        padding: 6px 0;
    }

    /* ── Header principal ── */
    .main-header {
        background: linear-gradient(135deg, #5BA033, #3D7A1F);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        color: white !important;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        margin: 4px 0 0 0;
        font-size: 14px;
    }

    /* ── Tarjetas KPI minimalistas ── */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        border-left: 4px solid #5BA033;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }
    .kpi-label {
        font-size: 12px;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #2C2C2C;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 12px;
        color: #AAAAAA;
        margin-top: 4px;
    }
    .kpi-danger  { border-left-color: #E24B4A; }
    .kpi-warning { border-left-color: #EF9F27; }
    .kpi-success { border-left-color: #5BA033; }
    .kpi-info    { border-left-color: #378ADD; }
    .kpi-neutral { border-left-color: #888888; }

    /* ── Sección título ── */
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #3D7A1F;
        border-bottom: 2px solid #5BA033;
        padding-bottom: 6px;
        margin: 1.5rem 0 1rem 0;
    }

    /* ── Tarjeta contenedor ── */
    .content-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }

    /* ── Badge de estado ── */
    .badge-green  { background:#E8F5E0; color:#3D7A1F; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-yellow { background:#FFF8E1; color:#B8860B; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-red    { background:#FFEBEE; color:#C62828; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-blue   { background:#E3F2FD; color:#1565C0; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

    /* ── Ocultar elementos de Streamlit ── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }

    /* ── Dataframe ── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ── Botones ── */
    .stButton > button {
        background-color: #5BA033;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #3D7A1F;
    }
</style>
"""

COLORS = {
    "primary":   "#5BA033",
    "dark":      "#3D7A1F",
    "danger":    "#E24B4A",
    "warning":   "#EF9F27",
    "info":      "#378ADD",
    "neutral":   "#888888",
    "bg":        "#F5F5F5",
    "white":     "#FFFFFF",
    "text":      "#2C2C2C",
}

PLOTLY_TEMPLATE = dict(
    plot_bgcolor  = "#FFFFFF",
    paper_bgcolor = "#FFFFFF",
    font          = dict(family="Segoe UI", color="#2C2C2C"),
    colorway      = ["#5BA033", "#378ADD", "#EF9F27", "#E24B4A", "#888888", "#3D7A1F"],
    xaxis         = dict(gridcolor="#F0F0F0", linecolor="#DDDDDD"),
    yaxis         = dict(gridcolor="#F0F0F0", linecolor="#DDDDDD"),
)

def kpi(label, value, tipo="success", sub=""):
    return f"""
    <div class="kpi-card kpi-{tipo}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
    </div>
    """

def section(title):
    return f'<div class="section-title">{title}</div>'

def header(title, subtitle=""):
    return f"""
    <div class="main-header">
        <h1>{title}</h1>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """
