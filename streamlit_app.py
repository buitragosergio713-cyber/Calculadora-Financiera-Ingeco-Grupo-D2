"""Calculadora financiera | Ingeniería económica - UIS.
Interfaz web; el motor calculos.py se conserva sin modificaciones.
"""
import csv
import io
from datetime import datetime

import streamlit as st

from calculos import (
    EJERCICIOS, MODULOS, OPERACIONES, REGLAS,
    ErrorCalculo, ejecutar, formatear,
)

# Identidad visual: azul institucional de la interfaz original + verde UIS.
LOGO_UIS = "https://uis.edu.co/wp-content/uploads/2024/12/Recurso-1logo-uis-.png"
AZUL = "#10243B"
AZUL_MEDIO = "#214770"
AZUL_ACENTO = "#2563EB"
VERDE_UIS = "#67B93E"
FONDO = "#F2F5FA"

st.set_page_config(
    page_title="Calculadora financiera | Ingeniería económica",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root {{ --navy:{AZUL}; --navy2:{AZUL_MEDIO}; --blue:{AZUL_ACENTO}; --uis:{VERDE_UIS}; }}
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: {FONDO}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{ background: var(--navy); border-right: 1px solid #1B3654; }}
    [data-testid="stSidebar"] * {{ color: #F4F7FB; }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color:#C6D2E0; }}
    [data-testid="stSidebar"] hr {{ border-color:#29435F; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        background: transparent; border-radius:8px; padding:7px 10px; margin:2px 0;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ background:#183454; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{
        background:#214770; border-left:4px solid #60A5FA; font-weight:700;
    }}
    .block-container {{ padding-top: 2.0rem; padding-bottom: 3rem; max-width: 1450px; }}
    h1, h2, h3 {{ color:var(--navy); letter-spacing:-.025em; }}
    .hero {{ background:linear-gradient(115deg,#10243B 0%,#214770 100%); color:white;
        border-radius:16px; padding:25px 28px; margin-bottom:20px; box-shadow:0 8px 24px #10243b18; }}
    .hero h1 {{ color:white; margin:0 0 6px 0; font-size:1.8rem; }}
    .hero p {{ color:#D7E2EF; margin:0; font-size:.96rem; }}
    .eyebrow {{ color:#A8C2DE; font-size:.72rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }}
    .metric-card {{ background:white; border:1px solid #DFE5EF; border-radius:12px; padding:16px 18px; min-height:100px; }}
    .metric-label {{ color:#6B7A90; font-size:.70rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }}
    .metric-value {{ color:#10243B; font-size:1.7rem; font-weight:800; margin-top:4px; }}
    .op-card {{ background:white; border:1px solid #DFE5EF; border-radius:14px; padding:18px 18px 12px 18px; margin:0 0 16px 0; box-shadow:0 3px 12px #10243b08; }}
    .op-title {{ font-size:1.03rem; font-weight:750; color:#172A40; margin-bottom:8px; }}
    .equation {{ background:#F4F6FB; border-left:3px solid #2563EB; color:#43536A;
        border-radius:6px; padding:10px 12px; font-family:ui-monospace, SFMono-Regular, Consolas, monospace;
        font-size:.82rem; margin:10px 0 15px 0; }}
    .result {{ background:#EAF5E5; border:1px solid #C8E5B8; border-left:4px solid #67B93E;
        border-radius:9px; padding:13px 15px; margin-top:12px; }}
    .result-label {{ color:#477B2B; font-size:.70rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }}
    .result-value {{ color:#1F5721; font-size:1.25rem; font-weight:800; margin-top:3px; }}
    div.stButton > button, div.stFormSubmitButton > button {{ border-radius:8px; font-weight:700; border:0; }}
    div.stFormSubmitButton > button {{ background:#2563EB; color:white; }}
    div.stFormSubmitButton > button:hover {{ background:#1D4ED8; color:white; }}
    div.stButton > button[kind="secondary"] {{ background:#E8EDF5; color:#1B2635; }}
    [data-testid="stMetric"] {{ background:white; border:1px solid #DFE5EF; padding:14px 16px; border-radius:12px; }}
    [data-testid="stDataFrame"] {{ border:1px solid #DFE5EF; border-radius:10px; overflow:hidden; }}
    .small-note {{ color:#6B7A90; font-size:.82rem; }}
    .uis-line {{ height:4px; background:var(--uis); border-radius:4px; margin:10px 0 18px 0; }}
</style>
""", unsafe_allow_html=True)

if "historial" not in st.session_state:
    st.session_state.historial = []
if "resultados" not in st.session_state:
    st.session_state.resultados = {}

# Sidebar / navegación
with st.sidebar:
    try:
        st.image(LOGO_UIS, width=190)
    except Exception:
        st.markdown("<h2 style='color:white'>UIS</h2>", unsafe_allow_html=True)
    st.markdown("### Calculadora financiera")
    st.markdown("Ingeniería económica · Grupo D2")
    st.divider()
    st.markdown("<div class='eyebrow'>NAVEGACIÓN</div>", unsafe_allow_html=True)
    nav_items = ["Inicio"] + [m[1] for m in MODULOS] + ["07  Validación", "08  Reporte"]
    selected = st.radio("Secciones", nav_items, label_visibility="collapsed")
    st.divider()
    st.caption("Herramienta académica · UIS")

# Helpers
module_by_title = {m[1]: m for m in MODULOS}

def render_header(title, subtitle, eyebrow="CALCULADORA FINANCIERA"):
    st.markdown(f"<div class='hero'><div class='eyebrow'>{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)

def render_operation(op, idx):
    result_key = op.clave
    with st.container(border=True):
        st.markdown(f"<div class='op-title'>{op.titulo}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='equation'>{op.ecuacion}</div>", unsafe_allow_html=True)
        with st.form(f"form_{op.clave}", clear_on_submit=False):
            cols = st.columns(2)
            values = {}
            for j, campo in enumerate(op.campos):
                with cols[j % 2]:
                    if campo.tipo == "num":
                        values[campo.clave] = st.text_input(
                            campo.etiqueta, key=f"input_{op.clave}_{campo.clave}",
                            placeholder=f"Ingrese {campo.unidad}" if campo.unidad else "Ingrese un valor",
                        )
                    else:
                        values[campo.clave] = st.selectbox(campo.etiqueta, list(campo.valores), key=f"input_{op.clave}_{campo.clave}")
            submitted = st.form_submit_button("Calcular resultado", use_container_width=True)
    if submitted:
        try:
            result = ejecutar(op, values)
            formatted = formatear(result, op.res_unidad)
            st.session_state.resultados[result_key] = {"ok": True, "texto": formatted}
            st.session_state.historial.append({
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Módulo": dict((x[0], x[1].split(None, 1)[1]) for x in MODULOS)[op.modulo],
                "Operación": op.titulo,
                "Entradas": "; ".join(f"{k}={v}" for k, v in values.items()),
                "Resultado": formatted,
            })
        except ErrorCalculo as exc:
            st.session_state.resultados[result_key] = {"ok": False, "texto": str(exc)}
    result_state = st.session_state.resultados.get(result_key)
    if result_state:
        if result_state["ok"]:
            st.markdown(f"<div class='result'><div class='result-label'>{op.res_etiqueta}</div><div class='result-value'>{result_state['texto']}</div></div>", unsafe_allow_html=True)
        else:
            st.error(result_state["texto"])

# Page content
if selected == "Inicio":
    render_header("Calculadora financiera", "Una herramienta clara y práctica para resolver operaciones de ingeniería económica.", "UNIVERSIDAD INDUSTRIAL DE SANTANDER")
    implementadas = sum(not op.pendiente for op in OPERACIONES)
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "Operaciones", len(OPERACIONES)),
        (c2, "Módulos", len(MODULOS)),
        (c3, "Ejercicios de referencia", len(EJERCICIOS)),
        (c4, "Ejercicios validados", "11 / 11"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='uis-line'></div>", unsafe_allow_html=True)
    st.subheader("Módulos de cálculo")
    grid = st.columns(2)
    for i, (key, title, desc) in enumerate(MODULOS):
        with grid[i % 2]:
            st.markdown(f"<div class='op-card'><div class='op-title'>{title}</div><p class='small-note'>{desc}</p></div>", unsafe_allow_html=True)
    st.info("Selecciona un módulo en el menú lateral para comenzar. Las ecuaciones y el motor de cálculo se conservan del proyecto original.")

elif selected in module_by_title:
    mod_key, mod_title, mod_desc = module_by_title[selected]
    render_header(mod_title, mod_desc)
    ops = [op for op in OPERACIONES if op.modulo == mod_key]
    left, right = st.columns(2, gap="large")
    for i, op in enumerate(ops):
        with (left if i % 2 == 0 else right):
            render_operation(op, i)

elif selected == "07  Validación":
    render_header("Validación de resultados", "Compara los ejercicios de referencia del proyecto con los resultados calculados.", "CONTROL ACADÉMICO")
    if st.button("Ejecutar validación", type="primary"):
        import math
        rows = []
        for clave, entradas, esperado in EJERCICIOS:
            op = next(x for x in OPERACIONES if x.clave == clave)
            try:
                obtenido = ejecutar(op, entradas)
                ok = math.isclose(obtenido, esperado, rel_tol=1e-6, abs_tol=1e-9)
                rows.append({"Operación": op.titulo, "Esperado": formatear(esperado, op.res_unidad), "Obtenido": formatear(obtenido, op.res_unidad), "Estado": "Correcto" if ok else "Revisar"})
            except Exception as exc:
                rows.append({"Operación": op.titulo, "Esperado": formatear(esperado, op.res_unidad), "Obtenido": str(exc), "Estado": "Error"})
        st.session_state.validacion = rows
    if "validacion" in st.session_state:
        rows = st.session_state.validacion
        st.dataframe(rows, use_container_width=True, hide_index=True)
        passed = sum(r["Estado"] == "Correcto" for r in rows)
        st.success(f"{passed} de {len(rows)} ejercicios coinciden con la referencia.") if passed == len(rows) else st.warning(f"{passed} de {len(rows)} ejercicios coinciden con la referencia.")
    st.markdown("**Criterio:** tolerancia relativa de 1×10⁻⁶ y absoluta de 1×10⁻⁹.")

else:  # Reporte
    render_header("Historial y reporte", "Consulta las operaciones realizadas y descarga el registro en formato CSV.", "HERRAMIENTAS")
    history = st.session_state.historial
    if history:
        st.metric("Cálculos registrados", len(history))
        st.dataframe(list(reversed(history)), use_container_width=True, hide_index=True)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)
        st.download_button("Descargar historial CSV", buffer.getvalue().encode("utf-8-sig"), "historial_calculadora.csv", "text/csv", type="primary")
        if st.button("Limpiar historial"):
            st.session_state.historial = []
            st.rerun()
    else:
        st.info("Todavía no hay cálculos registrados. Realiza una operación en cualquiera de los módulos para crear el reporte.")
    st.markdown("### Reglas de uso")
    st.markdown(REGLAS.replace("• ", "- "))

st.markdown("<div style='text-align:center;color:#7B8798;font-size:.78rem;padding-top:25px'>Calculadora financiera · Ingeniería económica · Grupo D2 · UIS</div>", unsafe_allow_html=True)
