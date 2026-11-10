"""
Dashboard: Tipo de cambio USD/PEN
Lee los marts generados por el pipeline (dbt + DuckDB) exportados a Parquet.
"""
import json
from datetime import timedelta
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"
REPO_URL = "https://github.com/JhonyVargas/pipeline-tipo-cambio-peru"  # <- cambia por tu repo

# Paleta (validada para daltonismo): azul = serie principal, naranja = serie secundaria
AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#8a94a6"
TINTA, TINTA_2, GRID = "#1b2433", "#5b6576", "#e9edf2"
SUBE, BAJA = "#eb6834", "#2a78d6"  # sube el dólar = naranja, baja = azul

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

st.set_page_config(page_title="Tipo de Cambio Perú · Data Pipeline", page_icon="💱", layout="wide")

# --------------------------------------------------------------------------- estilos
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stText {{ font-family: 'Inter', sans-serif; }}
#MainMenu, footer, header [data-testid="stToolbar"] {{ visibility: hidden; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1300px; }}

.hero {{
  background: linear-gradient(135deg, #0f1e3d 0%, #18346b 55%, #2a5bb0 100%);
  border-radius: 18px; padding: 28px 34px; color: #fff; margin-bottom: 22px;
  box-shadow: 0 10px 30px rgba(15,30,61,.25); position: relative; overflow: hidden;
}}
.hero:after {{
  content: "S/ $"; position: absolute; right: 30px; top: -10px; font-size: 130px;
  font-weight: 800; opacity: .06; letter-spacing: -6px;
}}
.hero h1 {{ font-size: 30px; font-weight: 800; margin: 0 0 4px 0; color: #fff; }}
.hero p  {{ margin: 0; color: #c9d6ee; font-size: 15px; }}
.badges {{ margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; }}
.badge {{
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.18);
  padding: 4px 12px; border-radius: 999px; font-size: 12.5px; color: #e8eefb;
}}
.badge.ok {{ background: rgba(27,175,122,.22); border-color: rgba(27,175,122,.5); }}

.kpi {{
  background: #fff; border: 1px solid #e6eaf0; border-radius: 14px; padding: 16px 18px;
  box-shadow: 0 2px 8px rgba(20,35,60,.05); height: 100%;
}}
.kpi .lbl {{ font-size: 12.5px; color: {TINTA_2}; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; }}
.kpi .val {{ font-size: 26px; font-weight: 800; color: {TINTA}; margin: 4px 0 2px; white-space: nowrap; }}
.kpi .val.sm {{ font-size: 21px; padding: 4px 0 1px; }}
.kpi .sub {{ font-size: 13px; color: {TINTA_2}; }}
.up   {{ color: #c4501f; font-weight: 700; }}
.down {{ color: #1f62b3; font-weight: 700; }}

.card {{
  background: #fff; border: 1px solid #e6eaf0; border-radius: 14px; padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(20,35,60,.05);
}}
.sec-title {{ font-size: 17px; font-weight: 700; color: {TINTA}; margin: 0 0 2px; }}
.sec-sub {{ font-size: 13px; color: {TINTA_2}; margin: 0 0 6px; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{
  background: #fff; border: 1px solid #e6eaf0; border-radius: 10px; padding: 8px 16px; font-weight: 600;
}}
.stTabs [aria-selected="true"] {{ background: #eaf2fc; border-color: {AZUL}; color: {AZUL}; }}

.flow {{ display: flex; align-items: stretch; gap: 8px; flex-wrap: nowrap; margin: 10px 0 4px; }}
.step {{
  background: #fff; border: 1px solid #e6eaf0; border-radius: 12px; padding: 12px 14px;
  min-width: 0; flex: 1; box-shadow: 0 2px 6px rgba(20,35,60,.05);
}}
.step b {{ display: block; font-size: 14px; color: {TINTA}; }}
.step span {{ font-size: 12.5px; color: {TINTA_2}; }}
.arrow {{ color: {GRIS}; font-size: 20px; font-weight: 700; align-self: center; }}
.footer {{ text-align: center; color: {TINTA_2}; font-size: 12.5px; margin-top: 26px; }}
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- datos
@st.cache_data(ttl=3600)
def cargar():
    con = duckdb.connect()
    q = lambda t: con.execute(f"SELECT * FROM read_parquet('{(DATA / t).as_posix()}.parquet')").df()
    diario, mensual, anual = q("fct_tipo_cambio_diario"), q("fct_tipo_cambio_mensual"), q("fct_tipo_cambio_anual")
    diario["fecha"] = pd.to_datetime(diario["fecha"])
    mensual["periodo"] = pd.to_datetime(mensual["periodo"])
    meta = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))
    return diario, mensual, anual, meta


diario, mensual, anual, meta = cargar()


def fmt_fecha(d) -> str:
    d = pd.Timestamp(d)
    return f"{d.day:02d} {MESES[d.month - 1]} {d.year}"


def layout(fig, alto=420, **kw):
    fig.update_layout(
        height=alto, template="plotly_white", margin=dict(l=10, r=10, t=10, b=10),
        font=dict(family="Inter, sans-serif", color=TINTA, size=13),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        hoverlabel=dict(bgcolor="#fff", bordercolor=GRID, font=dict(color=TINTA, family="Inter")),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(color=TINTA_2)),
        **kw,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=TINTA_2))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=TINTA_2))
    return fig


ult, prev = diario.iloc[-1], diario.iloc[-2]

# --------------------------------------------------------------------------- hero
st.markdown(
    f"""
<div class="hero">
  <h1>💱 Tipo de Cambio USD / PEN</h1>
  <p>Pipeline de ingeniería de datos · API BCRP → DuckDB → dbt → Dashboard, automatizado con GitHub Actions</p>
  <div class="badges">
    <span class="badge ok">● Pipeline activo</span>
    <span class="badge">📅 Último dato: {fmt_fecha(ult.fecha)}</span>
    <span class="badge">🔄 Actualizado: {meta['actualizado_en_utc']} UTC</span>
    <span class="badge">🏦 Fuente: BCRP</span>
    <span class="badge">🗂️ {len(diario):,} días hábiles</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- KPIs
def delta_html(v, sufijo="%"):
    if pd.isna(v):
        return ""
    cls, flecha = ("up", "▲") if v > 0 else ("down", "▼") if v < 0 else ("", "■")
    return f'<span class="{cls}">{flecha} {v:+.2f}{sufijo}</span>'


anio_act = ult.fecha.year
del_anio = diario[diario.anio == anio_act]
ytd = (ult.tc_venta / del_anio.iloc[0].tc_venta - 1) * 100
mes_act = diario[(diario.anio == anio_act) & (diario.mes == ult.fecha.month)]
u52 = diario[diario.fecha >= ult.fecha - timedelta(days=365)]

kpis = [
    ("TC Venta", f"S/ {ult.tc_venta:.3f}", f"{delta_html(ult.var_diaria_pct)} vs día anterior"),
    ("TC Compra", f"S/ {ult.tc_compra:.3f}", f"Spread: {ult.spread * 1000:.1f} milésimas"),
    (f"Promedio {MESES[ult.fecha.month - 1]} {anio_act}", f"S/ {mes_act.tc_venta.mean():.3f}", f"{len(mes_act)} días hábiles"),
    (f"Variación {anio_act} (YTD)", f"{ytd:+.2f}%", "▲ = el sol se deprecia"),
    ("Rango 52 semanas", f"{u52.tc_venta.min():.3f} – {u52.tc_venta.max():.3f}§", "mínimo – máximo (venta)"),
]
for col, (lbl, val, sub) in zip(st.columns(5), kpis):
    cls = "val sm" if val.endswith("§") else "val"
    col.markdown(f'<div class="kpi"><div class="lbl">{lbl}</div><div class="{cls}">{val.rstrip("§")}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

st.write("")

# --------------------------------------------------------------------------- sidebar: conversor
with st.sidebar:
    st.markdown("### 🧮 Conversor")
    st.caption(f"Con el TC interbancario del {fmt_fecha(ult.fecha)}")
    sentido = st.radio("Convertir", ["USD → PEN", "PEN → USD"], horizontal=True, label_visibility="collapsed")
    monto = st.number_input("Monto", min_value=0.0, value=100.0, step=10.0)
    if sentido == "USD → PEN":
        st.metric("Recibes (compra)", f"S/ {monto * ult.tc_compra:,.2f}")
    else:
        st.metric("Recibes (venta)", f"$ {monto / ult.tc_venta:,.2f}")
    st.divider()
    st.markdown("### ℹ️ Sobre el proyecto")
    st.markdown(
        "Solución de **ingeniería de datos** que extrae diariamente el tipo de cambio "
        "interbancario del **BCRP**, lo transforma con **dbt** sobre **DuckDB** y lo publica aquí."
    )
    st.markdown(f"[📂 Ver repositorio en GitHub]({REPO_URL})")

# --------------------------------------------------------------------------- tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Evolución", "📊 Análisis mensual", "📉 Volatilidad", "🗂️ Datos", "⚙️ Pipeline"])

# ---- Evolución
with tab1:
    c1, c2 = st.columns([3, 2])
    rango = c1.segmented_control("Periodo", ["1M", "3M", "6M", "YTD", "1A", "5A", "Todo"], default="1A", label_visibility="collapsed")
    medias = c2.multiselect("Medias móviles", ["Media móvil 7d", "Media móvil 30d"], default=["Media móvil 30d"], label_visibility="collapsed", placeholder="Agregar media móvil")
    dias = {"1M": 31, "3M": 92, "6M": 183, "1A": 365, "5A": 365 * 5}
    if rango == "YTD":
        d = diario[diario.anio == anio_act]
    elif rango in dias:
        d = diario[diario.fecha >= ult.fecha - timedelta(days=dias[rango])]
    else:
        d = diario

    var_p = (d.tc_venta.iloc[-1] / d.tc_venta.iloc[0] - 1) * 100
    st.markdown(
        f'<p class="sec-title">TC interbancario venta (S/ por US$)</p>'
        f'<p class="sec-sub">{fmt_fecha(d.fecha.iloc[0])} – {fmt_fecha(d.fecha.iloc[-1])} · variación en el periodo: {delta_html(var_p)}</p>',
        unsafe_allow_html=True,
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d.fecha, y=d.tc_venta, name="TC venta", mode="lines", line=dict(color=AZUL, width=2),
        fill="tozeroy", fillcolor="rgba(42,120,214,.07)",
        customdata=d[["tc_compra", "var_diaria_pct"]],
        hovertemplate="<b>S/ %{y:.4f}</b> venta<br>S/ %{customdata[0]:.4f} compra<br>Var. diaria: %{customdata[1]:+.2f}%<extra></extra>",
    ))
    estilos = {"Media móvil 7d": ("media_movil_7d", GRIS, "dot"), "Media móvil 30d": ("media_movil_30d", NARANJA, "solid")}
    for m in medias:
        colname, color, dash = estilos[m]
        fig.add_trace(go.Scatter(x=d.fecha, y=d[colname], name=m, mode="lines",
                                 line=dict(color=color, width=2, dash=dash),
                                 hovertemplate=f"{m}: S/ %{{y:.4f}}<extra></extra>"))
    pad = (d.tc_venta.max() - d.tc_venta.min()) * 0.15 or 0.01
    layout(fig, 430, hovermode="x unified", yaxis=dict(range=[d.tc_venta.min() - pad, d.tc_venta.max() + pad], tickformat=".3f"))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ---- Mensual
with tab2:
    anios = sorted(mensual.anio.unique())
    sel = st.select_slider("Rango de años", options=anios, value=(anios[-3], anios[-1]))
    m = mensual[(mensual.anio >= sel[0]) & (mensual.anio <= sel[1])].copy()
    m["etq"] = m.periodo.apply(lambda p: f"{MESES[p.month - 1]} {p.year}")

    st.markdown('<p class="sec-title">Velas mensuales (apertura, máximo, mínimo, cierre)</p>'
                '<p class="sec-sub">Naranja: el dólar subió en el mes · Azul: el dólar bajó</p>', unsafe_allow_html=True)
    fig = go.Figure(go.Candlestick(
        x=m.periodo, open=m.apertura, high=m.maximo, low=m.minimo, close=m.cierre, name="TC venta",
        increasing=dict(line=dict(color=SUBE, width=1.5), fillcolor=SUBE),
        decreasing=dict(line=dict(color=BAJA, width=1.5), fillcolor=BAJA),
    ))
    layout(fig, 380, xaxis_rangeslider_visible=False, showlegend=False, yaxis=dict(tickformat=".3f"))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown('<p class="sec-title">Variación mensual del TC venta (%)</p>'
                '<p class="sec-sub">Cierre del mes vs. cierre del mes anterior</p>', unsafe_allow_html=True)
    fig = go.Figure(go.Bar(
        x=m.periodo, y=m.var_mensual_pct, name="Variación",
        marker=dict(color=[SUBE if v > 0 else BAJA for v in m.var_mensual_pct.fillna(0)], line=dict(color="#fff", width=1)),
        customdata=m[["etq", "promedio_venta"]],
        hovertemplate="<b>%{customdata[0]}</b><br>Variación: %{y:+.2f}%<br>Promedio: S/ %{customdata[1]:.4f}<extra></extra>",
    ))
    layout(fig, 300, showlegend=False, bargap=0.25, yaxis=dict(ticksuffix="%"))
    fig.add_hline(y=0, line=dict(color=GRIS, width=1))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ---- Volatilidad
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p class="sec-title">Volatilidad anual</p>'
                    '<p class="sec-sub">Desviación estándar de la variación diaria (%)</p>', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=anual.anio.astype(str), y=anual.volatilidad_pct, marker=dict(color=AZUL, line=dict(color="#fff", width=1)),
            text=[f"{v:.2f}" for v in anual.volatilidad_pct], textposition="outside", textfont=dict(color=TINTA_2, size=11),
            hovertemplate="<b>%{x}</b><br>Volatilidad: %{y:.3f}%<extra></extra>",
        ))
        layout(fig, 360, showlegend=False, bargap=0.35)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with c2:
        st.markdown('<p class="sec-title">Distribución de variaciones diarias</p>'
                    '<p class="sec-sub">Frecuencia de días según su variación % (todo el histórico)</p>', unsafe_allow_html=True)
        fig = go.Figure(go.Histogram(
            x=diario.var_diaria_pct.dropna(), nbinsx=60, marker=dict(color=AZUL, line=dict(color="#fff", width=1)),
            hovertemplate="Variación: %{x}%<br>Días: %{y}<extra></extra>",
        ))
        layout(fig, 360, showlegend=False, xaxis=dict(range=[-2, 2], ticksuffix="%", title=dict(text="Variación diaria", font=dict(color=TINTA_2, size=12))))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown('<p class="sec-title">Resumen por año</p>', unsafe_allow_html=True)
    st.dataframe(
        anual.sort_values("anio", ascending=False),
        hide_index=True, width="stretch",
        column_config={
            "anio": st.column_config.NumberColumn("Año", format="%d"),
            "dias_habiles": "Días",
            "apertura": st.column_config.NumberColumn("Apertura", format="%.4f"),
            "cierre": st.column_config.NumberColumn("Cierre", format="%.4f"),
            "maximo": st.column_config.NumberColumn("Máximo", format="%.4f"),
            "minimo": st.column_config.NumberColumn("Mínimo", format="%.4f"),
            "promedio_venta": st.column_config.NumberColumn("Promedio", format="%.4f"),
            "volatilidad_pct": st.column_config.NumberColumn("Volatilidad %", format="%.3f"),
            "var_anual_pct": st.column_config.NumberColumn("Var. anual %", format="%+.2f"),
        },
    )

# ---- Datos
with tab4:
    st.markdown('<p class="sec-title">Datos diarios (mart <code>fct_tipo_cambio_diario</code>)</p>', unsafe_allow_html=True)
    tabla = diario.sort_values("fecha", ascending=False)
    st.dataframe(
        tabla, hide_index=True, width="stretch", height=460,
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "anio": None, "mes": None,
            "tc_compra": st.column_config.NumberColumn("Compra", format="%.4f"),
            "tc_venta": st.column_config.NumberColumn("Venta", format="%.4f"),
            "tc_promedio": st.column_config.NumberColumn("Promedio", format="%.4f"),
            "spread": st.column_config.NumberColumn("Spread", format="%.4f"),
            "var_diaria_pct": st.column_config.NumberColumn("Var. diaria %", format="%+.3f"),
            "media_movil_7d": st.column_config.NumberColumn("MM 7d", format="%.4f"),
            "media_movil_30d": st.column_config.NumberColumn("MM 30d", format="%.4f"),
        },
    )
    st.download_button("⬇️ Descargar CSV", tabla.to_csv(index=False).encode("utf-8"), "tipo_cambio_diario.csv", "text/csv")

# ---- Pipeline
with tab5:
    st.markdown('<p class="sec-title">Arquitectura del pipeline</p>'
                '<p class="sec-sub">Se ejecuta automáticamente todos los días con GitHub Actions</p>', unsafe_allow_html=True)
    pasos = [
        ("🏦 API BCRP", "Fuente pública de series estadísticas"),
        ("🐍 Python", "Extract + Load (raw)"),
        ("🦆 DuckDB", "Data warehouse embebido"),
        ("🔧 dbt", "Staging → Marts + 13 tests"),
        ("📦 Parquet", "Export de marts"),
        ("📊 Streamlit", "Dashboard público"),
    ]
    html = '<div class="flow">' + '<div class="arrow">→</div>'.join(
        f'<div class="step"><b>{t}</b><span>{s}</span></div>' for t, s in pasos) + "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
<div class="card">
<p class="sec-title">🔧 Modelos dbt</p>
<ul style="margin:6px 0 0 0; color:#1b2433; font-size:14px; line-height:1.8">
<li><code>stg_tipo_cambio</code> – limpieza y parseo de fechas</li>
<li><code>fct_tipo_cambio_diario</code> – spread, variación, medias móviles</li>
<li><code>fct_tipo_cambio_mensual</code> – OHLC, promedio, volatilidad</li>
<li><code>fct_tipo_cambio_anual</code> – resumen anual</li>
</ul></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
<div class="card">
<p class="sec-title">🤖 Automatización</p>
<ul style="margin:6px 0 0 0; color:#1b2433; font-size:14px; line-height:1.8">
<li>GitHub Actions · cron diario (lun–vie)</li>
<li>Tests de calidad: unicidad, nulos, rangos y reglas de negocio</li>
<li>Commit automático de datos → redeploy en Streamlit Cloud</li>
<li>Última ejecución: <b>{meta['actualizado_en_utc']} UTC</b></li>
</ul></div>""",
            unsafe_allow_html=True,
        )

st.markdown(
    f'<div class="footer">Datos: Banco Central de Reserva del Perú (BCRP) · TC interbancario · '
    f'Proyecto académico de Ingeniería de Datos · <a href="{REPO_URL}">GitHub</a></div>',
    unsafe_allow_html=True,
)
